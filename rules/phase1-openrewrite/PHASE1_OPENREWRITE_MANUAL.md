# Phase1 OpenRewrite 전환 매뉴얼

## 1. 목적

이 문서는 `rules/phase1-openrewrite`에 정의된 OpenRewrite 레시피를 사용해
eGovFrame 3.1 기반 프로젝트를 eGovFrame 4.3 기준으로 1차 자동 전환하는 방법을 정리한다.

Phase 1의 목표는 다음과 같다.

- `pom.xml`의 비교적 안전한 dependency 좌표 및 버전 변경
- Java 소스의 패키지명 및 타입명 변경
- XML 설정의 문자열 기반 클래스명 변경
- 대규모 구조 변경이 필요한 항목은 제외하고, 자동화 가능한 범위만 우선 적용

이 단계는 "전체 마이그레이션 완료"가 아니라 "보수적인 1차 자동 변환"이다.

## 2. 현재 실행 구조

현재 진입점은 다음 두 파일이다.

- OpenRewrite 설정 파일: [rewrite.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/rewrite.yml)
- Maven 플러그인 설정: [pom.xml](/C:/project/egov-migration-tool/pom.xml)

실제 실행 시 Maven은 `pom.xml`에서 아래 설정을 사용한다.

- `configLocation`: `${project.basedir}/rules/phase1-openrewrite/rewrite.yml`
- `activeRecipes`: `egov.migration.phase1.FullMigration`

즉, `rewrite.yml` 하나만 로드하면 그 안에서 Phase 1 전체 레시피를 모두 해석하는 구조다.

## 3. 레시피 구성

`rewrite.yml`의 최상위 진입 레시피는 `egov.migration.phase1.FullMigration`이다.

이 레시피는 아래 3개 composite recipe를 순차적으로 포함한다.

1. `egov.migration.phase1.PomDependencyMigration`
2. `egov.migration.phase1.JavaMigration`
3. `egov.migration.phase1.XmlMigration`

각 영역의 역할은 다음과 같다.

### 3.1 POM 변환

대상:

- eGovFrame RTE 좌표 변경
- Spring 버전 업그레이드
- 로깅 관련 라이브러리 버전 업그레이드
- Jackson 1.x -> 2.x 좌표 전환
- MyBatis / MyBatis-Spring 버전 정리
- Oracle JDBC 좌표 정리
- JSTL / standard 의존성 정리
- 일부 공통 라이브러리 버전 업그레이드

### 3.2 Java 변환

대상:

- `egovframework.rte.*` -> `org.egovframe.rte.*`
- Jackson 1.x 패키지 및 타입 -> Jackson 2.x
- `MappingJacksonHttpMessageConverter` -> `MappingJackson2HttpMessageConverter`

### 3.3 XML 변환

대상:

- XML 내부 문자열 기반 `egovframework.rte` 패키지명 변경
- XML 내부 `MappingJacksonHttpMessageConverter` 문자열 변경

## 4. 사전 준비

실행 전 아래 사항을 확인한다.

1. 대상 프로젝트는 Git 등으로 백업 또는 브랜치 분리되어 있어야 한다.
2. JDK 버전은 최소 Java 17 기준으로 맞추는 것을 권장한다.
3. Maven 실행 환경이 준비되어 있어야 한다.
4. 대상 프로젝트는 변환 전 빌드 상태와 핵심 기능 동작 상태를 가능한 한 기록해둔다.

권장 사전 작업:

- 변환 전 `mvn -q -DskipTests package` 또는 프로젝트 표준 빌드 수행
- 주요 `pom.xml`, Spring XML, DAO 계층 구조 확인
- iBatis, DBCP 1.x, Log4j 1.x 사용 여부 사전 파악

## 5. 실행 방법

프로젝트 루트에서 아래 순서로 진행한다.

### 5.1 Dry Run

먼저 변경 예정 사항만 확인한다.

```bash
mvn rewrite:dryRun
```

확인 포인트:

- 어떤 파일이 변경 대상인지
- 의존성 좌표 변경이 기대와 맞는지
- Java import/type 치환 범위가 과도하지 않은지
- XML 텍스트 치환 결과가 안전한지

### 5.2 실제 반영

Dry Run 결과를 검토한 뒤 실제 반영한다.

```bash
mvn rewrite:run
```

### 5.3 후속 검증

반영 후에는 반드시 빌드와 기본 동작 검증을 수행한다.

예시:

```bash
mvn clean package
```

가능하면 아래도 함께 확인한다.

- 애플리케이션 기동
- Spring context 로딩
- 주요 화면 진입
- DAO / 트랜잭션 / JSON 직렬화 관련 기능

## 6. 자동 변환 범위

현재 Phase 1에서 자동 변환되는 대표 항목은 다음과 같다.

### 6.1 eGovFrame 좌표 변경

- `egovframework.rte:*` 일부 핵심 모듈
- `org.egovframe.rte:*` 4.3.0 기준으로 변경

대표 예:

- `egovframework.rte:egovframework.rte.fdl.cmmn`
- `egovframework.rte:egovframework.rte.psl.dataaccess`
- `egovframework.rte:egovframework.rte.ptl.mvc`

### 6.2 Jackson 전환

POM:

- `org.codehaus.jackson:jackson-core-asl` -> `com.fasterxml.jackson.core:jackson-core`
- `org.codehaus.jackson:jackson-mapper-asl` -> `com.fasterxml.jackson.core:jackson-databind`

Java:

- `org.codehaus.jackson.map.ObjectMapper` -> `com.fasterxml.jackson.databind.ObjectMapper`
- `org.codehaus.jackson.JsonNode` -> `com.fasterxml.jackson.databind.JsonNode`
- `org.codehaus.jackson.type.TypeReference` -> `com.fasterxml.jackson.core.type.TypeReference`

XML/Java 보조 전환:

- `MappingJacksonHttpMessageConverter` -> `MappingJackson2HttpMessageConverter`

### 6.3 버전 업그레이드

대표 대상:

- Spring 5.3.37
- SLF4J 1.7.36
- Log4j2 2.17.1
- MyBatis 3.5.16
- MyBatis-Spring 2.1.2
- `ojdbc8` 19.22.0.0

## 7. 자동 변환에서 제외한 항목

아래 항목은 의도적으로 Phase 1 자동 변환에서 제외했다.

### 7.1 DAO 구현 구조 변경

예:

- `EgovAbstractDAO` -> `EgovAbstractMapper`
- `EgovComAbstractDAO` 기반 커스텀 DAO

제외 이유:

- iBatis / MyBatis 혼재 여부 확인 필요
- 상속 구조와 공통 래퍼 클래스 존재 가능
- 메서드 시그니처 및 호출 방식 수동 점검 필요

### 7.2 XML 기반 MyBatis 전환

예:

- `SqlMapClientFactoryBean` -> `SqlSessionFactoryBean`

제외 이유:

- bean wiring 구조 변경 가능
- `configLocation`, mapper 설정 구조 재설계 필요

### 7.3 DBCP1 -> DBCP2 구조 변경

예:

- `org.apache.commons.dbcp.BasicDataSource`
- `org.apache.commons.dbcp2.BasicDataSource`

제외 이유:

- XML bean property 호환성 점검 필요
- 풀 설정 속성명이 달라질 수 있음

### 7.4 Log4j 1.x API -> SLF4J 코드 전환

제외 이유:

- 필드 선언, 초기화, 호출 패턴 변경 필요
- 단순 import 치환만으로 끝나지 않음

## 8. 실행 후 반드시 점검할 항목

### 8.1 POM 관련

- `dependencyManagement`까지 기대대로 바뀌었는지
- 사내 저장소 또는 폐쇄망 저장소에서 새 좌표를 해석 가능한지
- JSTL 변경 후 JSP 컴파일에 문제가 없는지
- `systemPath` 기반 JDBC jar 참조가 남아 있지 않은지

### 8.2 Java 관련

- Jackson 2.x 전환 후 컴파일 오류가 없는지
- deprecated API 또는 패키지 이동으로 인한 추가 수정이 필요한지
- 커스텀 DAO 상속 구조가 그대로 남아 있는지

### 8.3 XML 관련

- Spring bean class 문자열 치환 결과가 실제 클래스와 맞는지
- 메시지 컨버터 bean 설정이 런타임에서 정상 로딩되는지
- 단순 문자열 치환이 의도치 않은 텍스트까지 바꾸지 않았는지

## 9. 운영 시 주의사항

1. `rewrite.yml`이 현재 단일 진입점이다. Phase 1 전체 적용은 이 파일을 기준으로 실행한다.
2. `01.pom-dependency-migration.yml`, `02.java-migration.yml`, `03.xml-migration.yml`과 `pom/java/xml` 하위 YAML들은 설계 참고용으로 볼 수 있지만, 현재 실제 실행은 `rewrite.yml` 중심이다.
3. 레시피 버전을 변경할 때는 `rewrite.yml` 내부 정의를 기준으로 일관되게 수정해야 한다.
4. 자동 변환 후에는 반드시 빌드와 런타임 검증을 수행해야 한다.
5. Phase 1 결과만으로 eGovFrame 4.3 완전 호환을 보장하지 않는다.

## 10. 권장 작업 순서

실무에서는 아래 순서를 권장한다.

1. 대상 프로젝트 백업 또는 브랜치 생성
2. 변환 전 빌드 및 주요 기능 체크
3. `mvn rewrite:dryRun` 실행
4. 결과 검토
5. `mvn rewrite:run` 실행
6. 컴파일 오류 수정
7. XML / DAO / datasource / logging 수동 보완
8. 통합 테스트 및 주요 기능 검증

## 11. 추가 보완 후보

향후 문서 또는 레시피 측면에서 보완할 수 있는 항목은 다음과 같다.

- `pom.xml` 주석 인코딩 정리
- `rewrite_mapping_sample.md` 한글 깨짐 복구
- 자동 변환 대상/제외 대상을 표 형식으로 재정리
- 샘플 프로젝트 기준 Before/After 예시 추가
- `dryRun` 결과 해석 예시 추가

## 12. 관련 파일

- 진입점 레시피: [rewrite.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/rewrite.yml)
- Maven 설정: [pom.xml](/C:/project/egov-migration-tool/pom.xml)
- POM 분리 설계안: [01.pom-dependency-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/01.pom-dependency-migration.yml)
- Java 분리 설계안: [02.java-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/02.java-migration.yml)
- XML 분리 설계안: [03.xml-migration.yml](/C:/project/egov-migration-tool/rules/phase1-openrewrite/03.xml-migration.yml)
