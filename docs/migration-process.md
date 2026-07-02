# Migration Process

전자정부프레임워크 3.x에서 4.3으로 전환할 때의 표준 수행절차를 정리한 문서다.

이 문서는 특히 Phase1, Phase2의 실제 실행 순서와 입력물, 산출물, 검증 포인트를 명확히 하는 데 목적이 있다.

---

## 전체 흐름

```text
1. AS-IS 분석
2. TO-BE 조사
3. 전환 규칙 수립
4. Phase1 수행
5. Phase2 수행
6. Phase3 보정
7. 컴파일 검증
8. 규칙 보강
```

---

## 사전 준비

### 입력물

* 전환 대상 원본 소스
* `pom.xml` 및 모듈 구조
* SQL Map, Spring XML, DAO 소스
* 기존 전환 사례 또는 검토 메모

### 확인 사항

* 전환 대상이 eGovFrame 3.x 기반인지 확인
* iBatis / MyBatis 혼재 여부 확인
* 공통 DAO 래퍼 존재 여부 확인
* 빌드 가능 상태의 기준 브랜치 또는 기준 소스 확보

---

## Phase1 수행절차

Phase1은 전후 매핑이 명확한 저위험 구조 변환 단계다. OpenRewrite를 중심으로 수행한다.

### 목적

* 패키지, 의존성, 타입명 등 정형 치환을 우선 처리한다
* Phase2에서 구조 변환에 집중할 수 있도록 선행 정리를 수행한다

### 주요 대상

* `egovframework.rte.* -> org.egovframe.rte.*`
* pom 의존성 좌표 및 버전 정리
* Jackson 1.x -> 2.x
* `ojdbc14 -> ojdbc8`
* 기타 저위험 import / package 치환

### 수행 순서

1. 전환 대상 소스 백업 또는 작업 사본 준비
2. OpenRewrite 규칙 적용
3. `pom.xml` 및 import 변경 결과 검토
4. 대량 치환 후 잔존 패턴 스캔
5. `validate` / `compile` 등 후속 검증 수행
6. patch 백업과 최종 적용 소스 기준본 정리

### 입력물

* 원본 프로젝트
* `rules/phase1-openrewrite/`

### 산출물

```text
converted/phase1/
output/rewrite-patches/
```

설명:

* `converted/phase1/<project>/`
  Phase1 `runNoFork`와 후속 검증까지 끝난 최종 적용 소스 기준본
* `output/rewrite-patches/`
  dry run / run 수행 시 생성된 patch 백업본

### 검증 포인트

* `egovframework.rte.*` 잔존 여부
* pom 의존성 좌표 누락 여부
* 대량 치환으로 인한 오탐 여부

---

## Phase2 수행절차

Phase2는 Python 프로그램이 주도하는 규칙 기반 구조 변환 단계다. DAO, SQL Map, Spring XML처럼 단순 치환으로 끝나지 않는 항목을 다룬다.

실행 예시, 입력/출력 경로, `run_phase2` 옵션은 [PHASE2_TOOLS_GUIDE.md](/C:/project/egov-migration-tool/tools/PHASE2_TOOLS_GUIDE.md)를 함께 참고한다.

### 목적

* iBatis 기반 구조를 MyBatis 기준 구조로 전환한다
* 후속 수동 검토가 필요한 대상을 자동으로 분류한다
* Phase3에서 다룰 예외 항목을 명확히 남긴다

### 적용 도구

* `tools/conversion/run_phase2.py`
* `tools/analysis/analyze_dao.py`
* `tools/analysis/classify_sqlmapclient_targets.py`
* `tools/conversion/transform_dao.py`
* `tools/conversion/transform_sqlmap.py`
* `tools/conversion/transform_spring_xml.py`
* `tools/conversion/postcheck.py`

### 기본 수행 순서

1. Phase1 최종 적용 소스와 작업 디렉터리 준비
2. 필요 시 분석 JSON 생성
3. Phase2 변환 실행
4. 변환 보고서 검토
5. 잔존 경고와 수동 검토 대상 확인
6. 필요 시 OpenRewrite 후처리 또는 규칙 보완

### 세부 단계

#### 1. 대상 탐지와 분류

`discover`와 `classify` 단계에서 아래를 확인한다.

* iBatis 전용 프로젝트인지
* MyBatis 혼재 프로젝트인지
* 공통 DAO 래퍼가 있는지
* `sqlMapClient` 관련 설정이 어디에 있는지

#### 2. DAO 변환

주요 확인 항목:

* `EgovAbstractDAO` 상속 여부
* 공통 DAO 래퍼 상속 구조
* `list`, `select`, `insert`, `update`, `delete` 호출 패턴
* `SqlMapClientTemplate` 사용 여부

대표 예:

```java
extends EgovAbstractDAO
```

→

```java
extends EgovAbstractMapper
```

#### 3. SQL Map 변환

주요 확인 항목:

* `#var#`, `$var$`
* `<dynamic>`, `<isNotEmpty>`, `<isEqual>`, `<iterate>`
* `parameterClass`, `resultClass`
* mapper namespace 및 statement id 구조

대표 예:

```xml
#id#
```

→

```xml
#{id}
```

#### 4. Spring XML 변환

주요 확인 항목:

* `SqlMapClientFactoryBean`
* `configLocation`
* `mapperLocations`
* DAO / mapper / Spring bean 참조 관계

대표 예:

```xml
org.springframework.orm.ibatis.SqlMapClientFactoryBean
```

→

```xml
org.mybatis.spring.SqlSessionFactoryBean
```

#### 5. 후처리와 보고서 생성

변환 후 아래 항목을 자동 점검한다.

* `EgovAbstractDAO`, `SqlMapClientTemplate` 잔존 여부
* iBatis XML 잔존 패턴 여부
* mapper / DAO 연결 불일치 여부
* 수동 검토 필요 파일 분류

### 권장 실행 예시

```bash
python -m tools.conversion.run_phase2 ^
  --source-root converted/phase1/hello-egov-board ^
  --working-root converted/phase2/hello-egov-board ^
  --report-root output/reports/hello-egov-board ^
  --copy-source
```

분석 JSON이 있으면 함께 연결한다.

```bash
python -m tools.conversion.run_phase2 ^
  --source-root converted/phase1/hello-egov-board ^
  --working-root converted/phase2/hello-egov-board ^
  --report-root output/reports/hello-egov-board ^
  --dao-analysis-json output/reports/dao-pattern-analysis.json ^
  --sqlmapclient-targets-json output/reports/sqlmapclient-usage-targets.json ^
  --copy-source
```

### 입력물

* 기본 입력: Phase1 최종 적용 소스 (`converted/phase1/<project>/`)
* 선택 입력: DAO 분석 JSON
* 선택 입력: sqlMapClient 분류 JSON

### 산출물

```text
converted/phase2/
output/reports/
  ├── phase2-discovery.json
  ├── phase2-report.json
  └── phase2-report.md
```

### 검증 포인트

* `EgovAbstractDAO` 잔존 여부
* `SqlMapClientFactoryBean` 잔존 여부
* iBatis XML 문법 잔존 여부
* 변환 후 수동 검토 파일 수
* 자동 변환 결과와 프로젝트 구조 간 불일치 여부

---

## Phase2 이후 처리

Phase2 결과는 곧바로 완료로 보지 않고, 아래 흐름으로 후속 처리한다.

1. `phase2-report.md` 검토
2. 수동 검토 파일 우선순위 지정
3. 필요 시 Phase3 보정 수행
4. 빌드 및 컴파일 검증 수행
5. 발견된 패턴을 규칙으로 환류

---

## 컴파일 검증과 규칙 환류

### 컴파일 검증

```bash
mvn clean compile
```

확인 항목:

* import 오류
* dependency 오류
* API 변경 오류
* mapper wiring 오류

### 규칙 환류

다음 경우에는 규칙을 보강한다.

* 반복적으로 발생하는 import 오류
* 특정 DAO 패턴에서 공통적으로 실패하는 변환
* 특정 SQL Map 문법이 동일하게 누락되는 경우
* Spring XML wiring 구조가 유사하게 반복되는 경우
