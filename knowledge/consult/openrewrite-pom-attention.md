# OpenRewrite로 pom.xml 변경 시 유의사항

## 1. 개요

OpenRewrite를 이용해 `pom.xml`의 dependency와 version을 변경할 때는 단순히 yml 규칙이 맞는지만 보면 안 된다.

`mvn rewrite:dryRun` 또는 `mvn rewrite:run`을 실행하는 순간 Maven이 먼저 `pom.xml`을 읽고 dependency를 해석한다. 따라서 중간 상태의 `pom.xml`이 깨져 있으면 OpenRewrite 실행 전 단계에서 오류가 발생할 수 있다.

이번 POC에서도 첫 번째 `egovframe-coordinates.yml` 실행 후 일부 dependency는 4.3 좌표로 변경되었으나, 일부 dependency는 3.x 좌표로 남아 있었다. 이 상태에서 version property가 4.3.0으로 변경되면서 Maven은 존재하지 않는 `egovframework.rte:*:4.3.0` artifact를 조회하게 되었고, 그 결과 두 번째 yml 실행 시 Dependency Resolution 오류가 발생하였다.

즉 이번 오류는 OpenRewrite Recipe 자체의 오류가 아니라, 첫 번째 Recipe 수행 후 생성된 중간 상태의 `pom.xml`을 Maven이 다시 해석하면서 발생한 오류였다.

---

## 2. 주요 유의점

### 유의점 1. 공통 Version Property 변경 시 참조 Dependency를 함께 확인해야 한다

`pom.xml`에서 여러 dependency가 하나의 version property를 공유하는 경우가 있다.

예:

```xml
<egovframework.rte.version>3.1.0</egovframework.rte.version>
```

이 값을 먼저 `4.3.0`으로 변경하면, 같은 property를 사용하는 모든 dependency가 4.3.0으로 해석된다.

문제 예:

```xml
<groupId>egovframework.rte</groupId>
<artifactId>egovframework.rte.fdl.security</artifactId>
<version>${egovframework.rte.version}</version>
```

version property가 4.3.0으로 바뀌면 Maven은 다음 좌표를 찾는다.

```text
egovframework.rte:egovframework.rte.fdl.security:4.3.0
```

하지만 이 좌표가 Maven 저장소에 없으면 오류가 발생한다.

따라서 version property 변경과 groupId/artifactId 변경은 함께 고려해야 한다.

---

### 유의점 2. 일부 Dependency만 변경되면 pom.xml이 중간 상태로 깨질 수 있다

OpenRewrite yml에서 일부 dependency만 변경되고 나머지가 누락되면 `pom.xml`이 다음과 같은 중간 상태가 된다.

```text
일부 dependency = 4.3 좌표
일부 dependency = 3.x 좌표
version property = 4.3.0
```

이 경우 Maven은 아직 3.x groupId로 남아 있는 dependency를 4.3.0 버전으로 찾게 된다.

이 조합은 존재하지 않을 수 있으므로 다음 yml 실행 시 오류가 발생한다.

중간 상태의 `pom.xml`은 다음 Recipe 실행뿐 아니라 Maven Build 자체도 실패할 수 있다.

---

### 유의점 3. 다음 yml 실행 시 Maven은 변경된 pom.xml을 다시 읽는다

OpenRewrite yml을 여러 개로 나누어 실행할 경우, 첫 번째 yml 실행 후 변경된 `pom.xml`을 기준으로 두 번째 yml이 실행된다.

즉 실행 순서는 다음과 같다.

```text
1번 yml 명령 수행
↓
pom.xml 변경
↓
2번 yml 명령 수행
↓
Maven이 변경된 pom.xml을 다시 읽음
↓
Dependency Resolution 수행
↓
이상 없으면 OpenRewrite 실행
↓
이상 있으면 Maven 오류 발생
```

따라서 각 yml 실행 후에는 `pom.xml`이 Maven 기준으로 정상 해석 가능한 상태인지 확인해야 한다.

---

### 유의점 4. 사용하지 않는 Dependency도 pom.xml에 있으면 Maven은 해석한다

소스에서 사용하지 않는 라이브러리라도 `pom.xml`에 dependency로 남아 있으면 Maven은 다운로드를 시도한다.

따라서 사용하지 않는 dependency라고 해서 그냥 남겨두면 안 된다.

처리 방법은 둘 중 하나다.

```text
1. 4.3 기준 좌표로 함께 변경한다.
2. 실제 미사용이면 pom.xml에서 제거 또는 주석 처리한다.
```

---

### 유의점 5. yml에 없는 Dependency는 변경되지 않는다

OpenRewrite는 yml에 작성된 규칙만 수행한다.

예를 들어 yml에 다음 규칙이 없으면 해당 dependency는 변경되지 않는다.

```text
egovframework.rte.fdl.security
egovframework.rte.fdl.excel
```

Rule이 없으면 OpenRewrite는 해당 dependency를 변경하지 않는다.

따라서 yml 작성 시 `pom.xml`의 dependency 목록과 yml의 변경 대상인 `oldGroupId`, `oldArtifactId`를 반드시 비교해야 한다.

---

### 유의점 6. dryRun은 실제 변경이 아니다

`dryRun`은 실제 `pom.xml`을 변경하지 않는다.

변경 예상 결과만 `target/rewrite/rewrite.patch`에 생성한다.

```bat
mvn rewrite:dryRun -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

실제 변경은 `run`을 실행해야 한다.

```bat
mvn rewrite:run -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

---

### 유의점 7. rewrite.patch는 dryRun마다 덮어써진다

`target/rewrite/rewrite.patch` 파일은 dryRun을 실행할 때마다 새로 생성된다.

따라서 여러 yml을 연속으로 dryRun하면 마지막 yml의 결과만 남는다.

필요하면 patch를 별도 이름으로 복사해둔다.

```bat
copy target\rewrite\rewrite.patch target\rewrite\egovframe-coordinates.patch
```

---

### 유의점 8. oldVersion 사용 시 현재 pom.xml 버전과 일치하는지 확인한다

`ChangeDependencyGroupIdAndArtifactId`에서 `oldVersion`을 사용하는 경우 현재 `pom.xml`의 version과 일치해야 Rule이 적용된다.

예를 들어 yml에 다음 조건이 있다고 하자.

```yaml
oldVersion: "3.1.0"
```

그런데 현재 `pom.xml`이 이미 다음 상태라면 Rule이 적용되지 않을 수 있다.

```text
version = 4.3.0
```

따라서 `oldVersion`은 필요한 경우에만 사용하고, 현재 `pom.xml` 상태와 일치하는지 확인해야 한다.

특히 version이 property 형태인 경우에는 더 주의해야 한다.

예:

```xml
<version>${egovframework.rte.version}</version>
```

---

### 유의점 9. Maven 오류와 OpenRewrite 오류를 구분해야 한다

OpenRewrite 실행 중 발생하는 오류는 크게 두 가지로 구분된다.

Maven 오류 예:

```text
Could not resolve dependencies
```

이 경우는 `pom.xml`의 dependency를 Maven이 해석하지 못한 것이다.

OpenRewrite 오류 예:

```text
Recipe validation failed
```

이 경우는 yml 문법, Recipe 이름, Recipe 옵션 등에 문제가 있을 가능성이 높다.

오류를 분석할 때는 먼저 Maven 오류인지 OpenRewrite 오류인지 구분해야 한다.

---

### 유의점 10. 하나의 Version Property를 참조하는 Dependency를 모두 확인해야 한다

하나의 Version Property를 여러 dependency가 함께 사용하는 경우가 많다.

예:

```xml
<version>${egovframework.rte.version}</version>
```

이 property를 사용하는 dependency가 여러 개라면, 일부만 변경해서는 안 된다.

예를 들어 8개의 dependency가 같은 property를 사용하는데 6개만 4.3 좌표로 변경되고 2개가 3.x 좌표로 남으면 다음과 같은 문제가 생긴다.

```text
3.x groupId + 4.3.0 version
```

이 조합은 존재하지 않는 artifact를 만들 수 있으므로 Maven Dependency Resolution 오류가 발생할 수 있다.

---

## 3. 기본 실행 명령어

### 3.1 프로젝트 폴더 이동

```bat
cd C:\dev\workspace\egov-migration-poc-main\source\cf-egovboard-war\hello-egov-board
```

### 3.2 recipe 이름 확인

```bat
findstr /n "name:" *.yml
```

### 3.3 dryRun 실행

```bat
mvn rewrite:dryRun -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

### 3.4 dryRun 결과 확인

```bat
notepad target\rewrite\rewrite.patch
```

### 3.5 실제 적용

```bat
mvn rewrite:run -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

### 3.6 pom.xml 변경 결과 확인

```bat
findstr /n "egovframework.rte org.egovframe.rte 3.1.0 4.3.0" pom.xml
```

### 3.7 Maven 빌드 확인

```bat
mvn clean package
```

---

## 4. 오류 발생 시 확인할 명령어

### 4.1 Dependency 오류 확인

오류 예:

```text
Could not resolve dependencies
egovframework.rte:egovframework.rte.fdl.security:4.3.0
```

확인 명령어:

```bat
findstr /n "egovframework.rte org.egovframe.rte 3.1.0 4.3.0" pom.xml
```

이 명령으로 3.x groupId와 4.3 version이 섞여 있는지 확인한다.

---

## 5. 권장 실행 절차

```text
1. pom.xml 백업
2. yml의 oldGroupId/oldArtifactId 목록 확인
3. pom.xml에 해당 old dependency가 모두 있는지 확인
4. 같은 version property를 공유하는 dependency 누락 여부 확인
5. dryRun 실행
6. rewrite.patch 확인
7. run 실행
8. findstr로 변경 결과 확인
9. mvn clean package 실행
10. 다음 yml 진행
```

---

## 6. 핵심 결론

OpenRewrite 실행 오류처럼 보여도 실제 원인은 Maven dependency resolution 오류일 수 있다.

특히 version property를 먼저 변경하면, 아직 변경되지 않은 dependency까지 새 version으로 해석되어 존재하지 않는 artifact를 찾게 된다.

따라서 `pom.xml` 변경 시 가장 중요한 원칙은 다음과 같다.

```text
version property 변경과 dependency 좌표 변경은 반드시 함께 검토한다.
각 yml 실행 후 pom.xml이 Maven 기준으로 정상 해석 가능한 상태인지 확인한다.
사용하지 않는 dependency도 pom.xml에 있으면 Maven은 해석하므로 제거하거나 함께 변환한다.
```
