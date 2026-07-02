# Phase1 OpenRewrite Manual

## 1. 목적

이 문서는 `rules/phase1-openrewrite` 하위 레시피를 사용해 eGovFrame 3.x 기반 프로젝트를 eGovFrame 4.3 기준으로 1차 자동 전환하는 방법을 정리한다.

현재까지 실제 검증이 끝난 범위는 `pom.xml`의 eGovFrame RTE 좌표 전환이다.

검증 완료 범위:

- JDK 8 환경에서 OpenRewrite Maven Plugin 실행
- 로컬 Nexus 연동 환경에서 `dryRunNoFork` / `runNoFork` 수행
- `samples/asis/hello-egov-board/pom.xml` 대상 좌표 전환
- 전환 후 `validate`, `dependency:tree` 성공

## 2. 현재 권장 실행 방식

현재 기준에서 가장 안정적인 실행 방식은 다음과 같다.

1. JDK 8로 Maven 실행
2. 로컬 Nexus를 통해 의존성 해석
3. `dryRunNoFork`로 변경 예정 확인
4. `runNoFork`로 실제 반영
5. `validate`, `dependency:tree`로 후속 검증

중요:

- `rewrite:dryRun`, `rewrite:run`은 Maven lifecycle을 더 깊게 타므로 환경에 따라 불필요한 컴파일 오류가 먼저 드러날 수 있다.
- 현재 샘플 검증은 `dryRunNoFork`, `runNoFork` 기준으로 통과했다.
- `AS-IS pom.xml`을 손으로 수정하는 방식보다 실행 환경을 맞추는 방식이 우선이다.

## 3. 사전 준비

### 3.1 JDK

- OpenRewrite 실행용 JDK는 우선 `JDK 8`을 권장한다.
- `JAVA_HOME`은 `bin`이 아닌 JDK 홈 디렉터리를 가리켜야 한다.

예시:

```powershell
$env:JAVA_HOME="C:\Program Files\Java\jdk1.8.0_491"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
java -version
mvn -version
```

### 3.2 저장소

- Maven Central 직접 접근 대신 로컬 Nexus 사용을 권장한다.
- 폐쇄망 또는 준폐쇄망에서는 Nexus가 사실상 필수에 가깝다.

### 3.3 대상 프로젝트

- 대상 프로젝트는 `mvn validate` 또는 `dependency:tree` 수준의 기본 해석이 가능해야 한다.
- `pom.xml` 백업 또는 Git 브랜치 분리는 필수다.

## 4. 검증 완료된 POM 전환 레시피

현재 실사용 기준 POM 전환 진입점은 아래 파일이다.

- [egovframe-coordinates.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/pom/egovframe-coordinates.yml)

이 파일은 단일 실행형으로 정리되어 있으며 아래 하위 레시피를 내부에 포함한다.

- `egov.migration.phase1.pom.EgovframeCoordinates`
- `egov.migration.phase1.pom.EgovframeCoordinatesPrepare43Property`
- `egov.migration.phase1.pom.EgovframeCoordinatesSwitchStableModules`

즉, `configLocation`을 이 파일 하나로 지정해도 바로 실행 가능하다.

## 5. 실제 검증 명령

대상 샘플 프로젝트:

- [samples/asis/hello-egov-board/pom.xml](/C:/project/egov-migration-tool/samples/asis/hello-egov-board/pom.xml)

### 5.1 Dry Run

```powershell
mvn -f samples/asis/hello-egov-board/pom.xml org.openrewrite.maven:rewrite-maven-plugin:6.11.0:dryRunNoFork -Drewrite.configLocation=../../../rules/phase1-openrewrite/pom/egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

확인 포인트:

- `target/rewrite/rewrite.patch` 생성 여부
- 신규 프로퍼티 추가 여부
- 대상 eGovFrame 의존성만 전환되는지 여부

### 5.2 실제 반영

```powershell
mvn -f samples/asis/hello-egov-board/pom.xml org.openrewrite.maven:rewrite-maven-plugin:6.11.0:runNoFork -Drewrite.configLocation=../../../rules/phase1-openrewrite/pom/egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

### 5.3 후속 검증

```powershell
mvn -f samples/asis/hello-egov-board/pom.xml validate
```

```powershell
mvn -f samples/asis/hello-egov-board/pom.xml dependency:tree
```

## 6. 이번 검증에서 실제 반영된 변경

샘플 프로젝트 기준으로 아래 변경이 정상 반영되었다.

- 신규 프로퍼티 추가
  - `<org.egovframe.rte.version>4.3.0</org.egovframe.rte.version>`
- 기존 프로퍼티 유지
  - `<egovframework.rte.version>3.1.0</egovframework.rte.version>`
- 아래 6개 의존성만 `org.egovframe.rte`로 전환
  - `ptl.mvc`
  - `psl.dataaccess`
  - `fdl.idgnr`
  - `fdl.property`
  - `fdl.security`
  - `fdl.excel`

이 방식의 장점은 기존 3.x 프로퍼티를 그대로 남겨 두고, 검증된 모듈만 4.3 전용 프로퍼티를 참조하게 만든다는 점이다.

## 7. WARNING 해석 기준

실행 중 발생하는 WARNING은 크게 두 종류로 본다.

### 7.1 허용 가능한 WARNING

- `These recipes would make changes ...`
- `Changes have been made ...`
- `Patch file available ...`
- `Please review and commit the results.`

이 경고들은 OpenRewrite가 정상 동작했다는 뜻이다.

### 7.2 별도 관리가 필요한 WARNING

- `maven-surefire-plugin version missing`
- `${artifactId}`, `${version}` deprecated

이 경고들은 현재 전환 실패 원인은 아니지만, 원본 POM 품질 이슈로 따로 정리해 둘 필요가 있다.

## 8. 레시피 사용 현황

### 8.1 현재 직접 사용하는 레시피/진입점

- [rules/phase1-openrewrite/pom/egovframe-coordinates.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/pom/egovframe-coordinates.yml)
  - 현재 검증 완료된 단일 실행형 POM 전환 진입점
- [rules/phase1-openrewrite/rewrite.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/rewrite.yml)
  - 루트 `pom.xml` 기준 전체 통합 진입점

### 8.2 분할 실행용으로 유지하는 레시피

- [egovframe-coordinates-rename.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/pom/egovframe-coordinates-rename.yml)
  - 1단계만 따로 실행할 때 사용 가능
- [egovframe-coordinates-version-upgrade.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/pom/egovframe-coordinates-version-upgrade.yml)
  - 2단계만 따로 실행할 때 사용 가능

### 8.3 현재 직접 실행 경로에서는 사용하지 않는 레시피

아래 파일들은 현재 실사용 명령 흐름에서 직접 사용되지 않는다.

- [01.pom-dependency-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/01.pom-dependency-migration.yml)
- [02.java-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/02.java-migration.yml)
- [03.xml-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/03.xml-migration.yml)

이 파일들은 현재 기준으로는 “설계 참조용” 성격이 강하다.

이유:

- 실제 실행은 `rewrite.yml` 내부 정의 또는 `pom/egovframe-coordinates.yml` 단일 실행형 기준으로 이뤄지고 있다.
- `01/02/03` 파일만 단독 `configLocation`으로 주면 하위 레시피 해석 문제가 생길 수 있다.
- 따라서 당장은 삭제보다 “참조용 유지”가 안전하다.

## 9. 정리 권장안

현재 기준 추천 정리는 다음과 같다.

1. `pom/egovframe-coordinates.yml`을 POM 전환 표준 진입점으로 고정
2. `rewrite.yml`은 전체 통합 진입점으로 유지
3. `01/02/03`은 참조용 파일로 간주하고 문서에만 역할 명시
4. Java/XML 단계 검증이 끝나기 전까지는 섣불리 삭제하지 않음

## 10. 다음 작업

다음 우선순위는 아래 둘 중 하나다.

1. 현재 성공한 POM 전환 절차를 표준 운영 절차로 고정
2. Java/XML 레시피를 같은 방식으로 샘플 검증

권장 순서:

1. 현재 `pom.xml` 상태 백업 또는 커밋
2. Java 레시피 검증
3. XML 레시피 검증
4. 검증 완료 후 미사용 레시피 재정리

## 11. 진입점 역할 구분

현재 문서 기준으로 혼동하기 쉬운 두 파일의 역할은 아래와 같다.

### 11.1 `pom/egovframe-coordinates.yml`

이 파일은 현재 실제 운영에 가장 가까운 POM 전환 표준 진입점이다.

특징:

* 단일 실행형
* `configLocation`으로 직접 지정 가능
* 샘플 프로젝트에서 `dryRunNoFork`, `runNoFork`, `validate`, `dependency:tree`까지 검증 완료

즉, POM 전환만 수행할 때는 이 파일을 우선 사용한다.

### 11.2 `rewrite.yml`

이 파일은 전체 Phase1 통합 진입점이다.

특징:

* POM, Java, XML 레시피를 한 번에 묶는 용도
* 루트 `pom.xml`과 연결되는 통합 진입점
* 현재는 보관 및 통합 설계 관점에서 유지

주의:

* Java/XML 레시피는 아직 POM 단계와 동일한 수준으로 끝까지 검증되지 않았다
* 따라서 현재 운영 기준에서는 `rewrite.yml`을 “전체 자동 전환 완료 진입점”으로 보기보다 “통합용 진입점”으로 이해하는 것이 맞다

## 12. 현재 운영 기준 요약

현재 시점의 보수적 운영 기준은 아래와 같다.

1. JDK 8 사용
2. 로컬 Nexus mirror 사용
3. POM 전환은 `pom/egovframe-coordinates.yml` 기준으로 수행
4. 명령은 `dryRunNoFork -> runNoFork -> validate -> dependency:tree` 순서 사용
5. `01/02/03` 파일은 직접 실행용보다 참조용으로 간주
