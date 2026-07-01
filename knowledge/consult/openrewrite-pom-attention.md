# OpenRewrite로 pom.xml 변경 시 유의사항 (최종)

## 1. 개요

OpenRewrite를 이용해 `pom.xml`의 dependency와 version을 변경할 때는
단순히 yml 규칙만 확인해서는 안 된다.

`mvn rewrite:dryRun` 또는 `mvn rewrite:run`을 실행하면 OpenRewrite보다
먼저 Maven이 `pom.xml`을 읽고 Dependency Resolution을 수행한다. 따라서
중간 상태의 `pom.xml`이 정상적으로 해석되지 않으면 OpenRewrite 실행 전에
Maven 오류가 발생할 수 있다.

이번 POC에서도 첫 번째 `egovframe-coordinates.yml` 실행 후 일부
dependency만 4.3 좌표로 변경되고 일부는 3.x 좌표로 남아 있었다. 이후
version property가 4.3.0으로 변경되면서 Maven은 존재하지 않는
`egovframework.rte:*:4.3.0` artifact를 조회하였고, 다음 Recipe 실행 시
Dependency Resolution 오류가 발생하였다.

즉 이번 오류는 OpenRewrite Recipe의 문제가 아니라, 변경된 `pom.xml`을
Maven이 다시 해석하는 과정에서 발생한 오류였다.

------------------------------------------------------------------------

## 2. 주요 유의점

### 유의점 1. 공통 Version Property 변경 시 참조 Dependency를 함께 확인해야 한다

하나의 version property를 여러 dependency가 공유하는 경우가 많다.

version만 먼저 변경하면 아직 3.x 좌표로 남아 있는 dependency까지 모두 새
버전으로 해석된다.

따라서 version property 변경과 dependency 좌표(groupId/artifactId)
변경은 반드시 함께 검토해야 한다.

------------------------------------------------------------------------

### 유의점 2. 일부 Dependency만 변경되면 pom.xml이 중간 상태가 될 수 있다

다음과 같은 상태는 위험하다.

-   일부 dependency = 4.3 좌표
-   일부 dependency = 3.x 좌표
-   version property = 4.3.0

이 상태에서는 Maven이 존재하지 않는 Artifact를 조회할 수 있으며 다음
Recipe 실행뿐 아니라 Maven Build도 실패할 수 있다.

------------------------------------------------------------------------

### 유의점 3. 다음 yml 실행 시 Maven은 변경된 pom.xml을 다시 읽는다

여러 yml을 순차 실행하면 매번 변경된 pom.xml을 기준으로 Dependency
Resolution을 수행한다.

따라서 각 yml 실행 후에는 pom.xml이 Maven 기준으로 정상 해석 가능한지
반드시 확인한다.

------------------------------------------------------------------------

### 유의점 4. 사용하지 않는 Dependency도 Maven은 해석한다

pom.xml에 존재하는 dependency는 실제 소스 사용 여부와 관계없이 Maven이
해석한다.

오류가 발생했다고 모두 같은 방법으로 처리하면 안 되며 다음 기준으로
판단한다.

1.  실제 미사용 dependency
    -   제거 또는 주석 처리
2.  실제 사용 중이며 4.3 대응 좌표가 있는 경우
    -   yml에 변환 Rule 추가
3.  실제 사용 중이나 자동 변환이 어려운 경우
    -   개발자가 수동 전환

실제 사용 중인 dependency는 주석 처리 대상이 아니라 **전환 대상**이다.

------------------------------------------------------------------------

### 유의점 5. yml에 없는 Dependency는 변경되지 않는다

OpenRewrite는 yml에 정의된 Rule만 수행한다.

따라서 yml 작성 시 pom.xml과 비교하여 누락된 dependency가 없는지 반드시
확인한다.

또한 Rule을 추가하기 전에 실제 Java/XML/JSP/Properties에서 사용하는
dependency인지 먼저 확인한다.

------------------------------------------------------------------------

### 유의점 6. dryRun은 실제 변경이 아니다

dryRun은 patch만 생성하며 pom.xml은 변경하지 않는다.

실제 변경은 run에서 수행한다.

------------------------------------------------------------------------

### 유의점 7. rewrite.patch는 덮어쓴다

dryRun을 실행할 때마다 rewrite.patch는 새로 생성된다.

필요 시 별도 파일로 백업한다.

------------------------------------------------------------------------

### 유의점 8. oldVersion 사용 시 현재 pom.xml 상태를 확인한다

oldVersion을 사용하는 경우 현재 pom.xml과 일치해야 Rule이 적용된다.

특히 property를 사용하는 경우 더욱 주의한다.

------------------------------------------------------------------------

### 유의점 9. Maven 오류와 OpenRewrite 오류를 구분한다

-   Maven 오류 : Dependency Resolution 실패
-   OpenRewrite 오류 : Recipe, yml, 설정 오류

먼저 어떤 종류의 오류인지 구분해야 한다.

------------------------------------------------------------------------

### 유의점 10. 하나의 Version Property를 사용하는 Dependency를 모두 확인한다

같은 version property를 사용하는 dependency는 일부만 변경하면 안 된다.

3.x groupId와 4.3 version이 섞이면 Dependency Resolution 오류가 발생할
수 있다.

------------------------------------------------------------------------

### 유의점 11. POC 진행을 위한 주석 처리와 최종 전환은 구분해야 한다

이번 POC에서는 `egovframework.rte.fdl.security`,
`egovframework.rte.fdl.excel` dependency가 yml 변환 대상에 포함되어 있지
않아 version property가 4.3.0으로 변경된 이후 Maven이 존재하지 않는
좌표를 조회하면서 Dependency Resolution 오류가 발생하였다.

POC에서는 다음 yml을 계속 검증하기 위해 해당 dependency를 `pom.xml`에서
**임시로 주석 처리**하였다.

그러나 이는 OpenRewrite를 계속 실행하기 위한 **임시 조치**일 뿐 최종
해결 방법은 아니다.

처리 기준은 다음과 같다.

``` text
1. 실제 미사용 Dependency
   → pom.xml에서 제거 또는 주석 처리

2. 실제 사용 중이며 4.3 대응 Dependency가 존재
   → yml에 변환 Rule을 추가하여 자동 변환

3. 실제 사용 중이나 자동 변환이 어려움
   → 개발자가 수동 전환 대상으로 분류
```

따라서 POC에서 발생한 Maven 오류를 해결하기 위해 `pom.xml`을 주석 처리할
수는 있지만, 실제 프로젝트에서는 해당 Dependency의 사용 여부를 먼저
확인한 후 자동 변환 대상인지, 수동 전환 대상인지를 판단해야 한다.

------------------------------------------------------------------------

## 3. 기본 실행 명령어

### 3.1 프로젝트 폴더 이동

``` bat
cd C:\dev\workspace\egov-migration-poc-main\source\cf-egovboard-war\hello-egov-board
```

### 3.2 recipe 이름 확인

``` bat
findstr /n "name:" *.yml
```

### 3.3 dryRun 실행

``` bat
mvn rewrite:dryRun -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

### 3.4 dryRun 결과 확인

``` bat
notepad target\rewrite\rewrite.patch
```

### 3.5 실제 적용

``` bat
mvn rewrite:run -Drewrite.configLocation=egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

### 3.6 pom.xml 변경 결과 확인

``` bat
findstr /n "egovframework.rte org.egovframe.rte 3.1.0 4.3.0" pom.xml
```

### 3.7 Maven 빌드 확인

``` bat
mvn clean package
```

------------------------------------------------------------------------

## 4. 오류 발생 시 확인할 명령어

### 4.1 Dependency 오류 확인

오류 예:

``` text
Could not resolve dependencies
egovframework.rte:egovframework.rte.fdl.security:4.3.0
```

확인 명령어:

``` bat
findstr /n "egovframework.rte org.egovframe.rte 3.1.0 4.3.0" pom.xml
```

이 명령으로 3.x groupId와 4.3 version이 섞여 있는지 확인한다.

------------------------------------------------------------------------

## 5. 권장 실행 절차

1.  pom.xml 백업
2.  yml의 oldGroupId/oldArtifactId 확인
3.  pom.xml에 대상 dependency 존재 여부 확인
4.  실제 Java/XML/JSP/Properties 사용 여부 확인
5.  누락 dependency를 자동 변환(yml) 또는 수동 전환 대상으로 분류
6.  dryRun 실행
7.  rewrite.patch 확인
8.  run 실행
9.  변경 결과 확인
10. mvn clean package 실행
11. 다음 yml 진행

------------------------------------------------------------------------

## 6. 핵심 결론

OpenRewrite는 반복적이고 기계적인 변경을 자동화하는 도구이다.

자동 변환이 가능한 항목은 yml Rule로 처리하고, 자동 변환이 어려운
Dependency나 API 변경은 개발자가 수동 전환 대상으로 관리하는 것이
바람직하다.

실제 사용 중인 Dependency는 주석 처리 대상이 아니라 전환 대상이며,
미사용 Dependency만 제거 또는 주석 처리한다.
