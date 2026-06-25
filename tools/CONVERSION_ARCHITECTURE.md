# Phase 2 Conversion Architecture

## 목표

Phase 2 변환 프로그램은 단순 문자열 치환기가 아니라 아래 순서로 동작하는 오케스트레이터로 설계한다.

1. 프로젝트 스캔
2. 구조/위험도 분류
3. 규칙 기반 변환
4. 잔존 패턴 검증
5. 리포트 생성

## 설계 원칙

* 원본 프로젝트는 직접 수정하지 않는다.
* 작업 대상은 `converted/phase2/`로 복사한 워킹 트리다.
* 확실한 규칙만 자동 수정한다.
* 애매한 항목은 `warnings` 또는 `manual_review`로 남긴다.
* 중간 데이터는 JSON으로 저장한다.

## 주요 모듈

### `discover.py`

역할:

* 파일 목록 수집
* Java / XML / SQL Map / JSP / properties 분류
* 아래 패턴 탐지
  * `EgovAbstractDAO`
  * `EgovComAbstractDAO`
  * `SqlMapClientFactoryBean`
  * `SqlMapClientTemplate`
  * `#...#`
  * `<dynamic>`, `<isNotEmpty>`, `<iterate>`

출력:

* `phase2-discovery.json`

### `classify.py`

역할:

* 스캔 결과를 바탕으로 프로젝트 성격 분류
* 필요 시 `tools/analysis/analyze_dao.py`의 JSON 결과를 병합
* 예:
  * `ibatis_only`
  * `mybatis_only`
  * `mixed`
  * `dao_wrapper_present`
  * `manual_review_required`

출력:

* discovery 결과에 classification 추가
* DAO 분석 JSON이 있으면 분류 신뢰도를 보강

### `transform_sqlmap.py`

역할:

* iBatis SQL Map -> MyBatis Mapper 전환의 MVP 규칙 수행

우선 구현 후보:

* `#id#` -> `#{id}`
* `<sqlMap>` -> `<mapper>`
* 대표 동적 태그 탐지 및 경고 추가

주의:

* 모든 dynamic SQL을 자동 완전 변환하지 않는다.
* 애매한 태그는 우선 경고만 남긴다.

### `transform_dao.py`

역할:

* DAO Java 소스 변환
* DAO 후보를 아래 3가지 결과로 구분해서 리포트
  * `공통 DAO 래퍼 클래스`
  * `공통 기반 클래스 상속 DAO`
  * `iBatis 직접 사용 DAO`

우선 구현 후보:

* `extends EgovAbstractDAO`
* `extends EgovComAbstractDAO`
* 관련 import 정리 후보 탐지

주의:

* method-level rewrite는 바로 자동 반영하지 않는다.
* DAO 래퍼 존재 시 프로젝트 공통 규칙부터 검토한다.

DAO 분류 기준:

* `공통 DAO 래퍼 클래스`
  * 예: `EgovComAbstractDAO.java`
  * 여러 DAO가 공통으로 상속하는 기반 클래스다.
  * 이 클래스를 어떻게 전환하느냐에 따라 하위 DAO 전체에 영향이 간다.
  * 따라서 개별 DAO보다 먼저 전환 전략을 확정해야 한다.
* `공통 기반 클래스 상속 DAO`
  * 예: `UserManageDAO extends EgovComAbstractDAO`
  * 개별 DAO가 공통 래퍼에 의존하는 구조다.
  * 공통 래퍼가 안정적으로 전환되면 이 계열 DAO는 후속 수정량이 작아질 수 있다.
* `iBatis 직접 사용 DAO`
  * 예: DAO 내부에서 `SqlMapClient`, `SqlMapClientTemplate`, `setSuperSqlMapClient(...)` 등을 직접 사용하는 경우
  * 공통 래퍼 전환만으로 끝나지 않을 수 있다.
  * 개별 DAO 내부 코드까지 별도 점검해야 하는 우선 검토 대상이다.

공통 DAO 래퍼 1차 전환 규칙:

* 샘플 기준 `EgovComAbstractDAO`는 하위 DAO 호환을 위한 브리지 래퍼로 우선 유지한다.
* 클래스명은 당장 바꾸지 않고 내부 구현만 `EgovAbstractMapper` 기반으로 전환한다.
* 우선 자동 변환 범위는 아래와 같다.
  * `import egovframework.rte.psl.dataaccess.EgovAbstractDAO`
    → `import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper`
  * `extends EgovAbstractDAO`
    → `extends EgovAbstractMapper`
  * `SqlMapClient`, `@Resource`, `setSuperSqlMapClient(...)` 제거
* 이렇게 하면 하위 DAO의 `extends EgovComAbstractDAO` 선언은 우선 유지할 수 있다.
* 실제 프로젝트에서는 공통 래퍼 내부에 추가 메서드가 있을 수 있으므로, 본 규칙은 샘플 기반 기본 전략으로 보고 프로젝트 소스 확보 후 재검토한다.

직접 `EgovAbstractDAO` 상속 DAO 1차 전환 규칙:

* 공통 래퍼를 거치지 않고 `extends EgovAbstractDAO`를 직접 사용하는 DAO는 더 단순한 규칙으로 먼저 전환한다.
* 우선 자동 변환 범위는 아래와 같다.
  * `import egovframework.rte.psl.dataaccess.EgovAbstractDAO`
    → `import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper`
  * `extends EgovAbstractDAO`
    → `extends EgovAbstractMapper`
* 이 규칙은 base class/import 전환까지만 자동 처리한다.
* DAO 내부에 `SqlMapClient`, `SqlMapClientTemplate` 등 iBatis 직접 사용 흔적이 남아 있으면 별도 경고를 남기고 후속 점검 대상으로 분류한다.

DAO 메서드 호출 1차 전환 규칙:

* `EgovAbstractMapper` 또는 `EgovComAbstractDAO` 기반 DAO에 대해 아래 메서드 호출을 1차 자동 변환한다.
  * `list(...)` → `selectList(...)`
  * `select(...)` → `selectOne(...)`
* 이 규칙은 DAO 파일에 한정해서 적용한다.
* `insert(...)`, `update(...)`, `delete(...)`는 우선 그대로 유지한다.
* 변환 후에도 `list()` 또는 `select()`가 남아 있으면 postcheck에서 수동 검토 대상으로 다시 보고한다.

### `transform_spring_xml.py`

역할:

* Spring XML 중 iBatis/MyBatis 연계 bean 구조 변환 후보 처리

우선 구현 방식:

* `SqlMapClientFactoryBean` 등 구조 변경 후보 탐지
* 자동 수정 가능한 경우만 변환
* 그렇지 않으면 warning 등록

Spring XML 1차 전환 규칙:

* `org.springframework.orm.ibatis.SqlMapClientFactoryBean`
  → `org.mybatis.spring.SqlSessionFactoryBean`
* `<property name="configLocations">`
  → `<property name="mapperLocations">`
* `bean id="egov.sqlMapClient"` 는 참조 호환성 때문에 1차 단계에서는 유지한다.
* `sqlMapClient` property/ref, `lobHandler` 연결처럼 프로젝트별 영향이 있을 수 있는 항목은 자동 치환 대신 경고로 남긴다.
* `sqlmapclient-usage-targets.json` 이 있으면 `자동 변환 가능`으로 분류된 XML 파일만 실제 자동 변환 대상으로 태운다.

### `postcheck.py`

역할:

* 변환 후 잔존 패턴 재탐지
* 자동 수정 가능 / 수동 검토 필요 / LLM 보정 필요 분류
* DAO 전환 후 Mapper 기반 코드의 잔존 위험 신호 점검

대표 잔존 패턴:

* `EgovAbstractDAO`
* `EgovComAbstractDAO`
* `SqlMapClientTemplate`
* `#...#`
* `<dynamic>`
* `<isNotEmpty>`

DAO 후속 점검 항목:

* `EgovAbstractMapper` 또는 `EgovComAbstractDAO` 기반으로 바뀐 DAO 안에 기존 `list()` 호출이 남아 있는지 확인
* `EgovAbstractMapper` 또는 `EgovComAbstractDAO` 기반으로 바뀐 DAO 안에 기존 `select()` 호출이 남아 있는지 확인
* 이런 호출이 남아 있으면 `selectList()` / `selectOne()` 계열로의 후속 전환 검토 대상으로 분류

### `report.py`

역할:

* JSON 리포트 생성
* Markdown 리포트 생성
* 여러 변환기 결과는 파일 경로 기준으로 병합 집계

## JSON 스키마

### `phase2-discovery.schema.json`

용도:

* 스캔 결과와 프로젝트 분류를 구조화해서 저장

주요 필드:

* `source_root`
* `working_root`
* `classifications`
* `findings`
* `file_counts`

### `phase2-report.schema.json`

용도:

* 실제 변환 결과 및 postcheck 결과 저장

주요 필드:

* `summary`
* `transform_results`
* `warnings`
* `manual_review`

## 추천 구현 단계

1. `discover.py`
2. `classify.py`
3. `transform_sqlmap.py`
4. `postcheck.py`
5. `report.py`
6. `run_phase2.py`
7. `transform_dao.py`
8. `transform_spring_xml.py`

현재 구현 상태:

* `tools.analysis.analyze_dao`는 Markdown과 JSON을 함께 생성한다.
* `tools.conversion.run_phase2`는 `--dao-analysis-json` 옵션으로 DAO 분석 JSON을 받아 classification과 report summary에 반영한다.

## MVP 범위

첫 번째 동작 가능한 버전은 아래까지만 자동화해도 충분하다.

* 워킹 트리 복사
* iBatis/MyBatis 패턴 스캔
* `#...#` -> `#{...}` 단순 변환
* `<sqlMap>` -> `<mapper>` 단순 변환
* 잔존 패턴 리포트 생성

그 다음 단계에서 DAO / Spring XML 변환을 확장하는 것이 안전하다.

## Phase 2 남은 작업 체크리스트

### 1. 실제 프로젝트 재검증

- [ ] 실제 전환 대상 프로젝트 소스를 기준으로 inventory/analysis를 다시 수행한다.
- [ ] 실제 프로젝트에서 `EgovAbstractDAO`, `EgovComAbstractDAO`, `sqlMapClient`, `SqlMapClientFactoryBean` 사용 분포를 다시 확인한다.
- [ ] 샘플 기준으로 만든 규칙이 실제 프로젝트 구조에도 그대로 적용 가능한지 검증한다.
- [ ] 실제 DB 벤더(`mysql`, `oracle`, `tibero`, `cubrid`, `altibase`) 기준으로 `mapperLocations` 전개 전략을 확정한다.

### 2. SQL Map 후속 정리

- [ ] `#파라미터# -> ${}` 식별자 치환 항목은 자동 승인하지 않고 수동 검토 대상으로 유지한다.
- [ ] 실제 프로젝트에서 이런 식별자 치환 패턴이 발견되면 품질/보안 정책 위반 후보로 별도 조치한다.
- [ ] `${}` 치환 경고는 “문법 이관 완료”와 “보안 승인 완료”를 구분해서 해석하도록 문서화한다.
- [ ] SQL Map 수동 검토 보고서는 “단순 문법 이관”, “식별자 치환”, “구조적 재설계 필요”로 구분할지 검토한다.

### 3. Spring XML 후속 정리

- [ ] `sqlMapClient` property/ref가 남는 bean들을 실제 프로젝트 기준으로 재분석한다.
- [ ] `context-excel.xml` 계열처럼 `sqlMapClient`를 직접 주입받는 bean의 MyBatis 대체 방식(`SqlSessionTemplate`, 다른 서비스 주입 등)을 확정한다.
- [ ] `lobHandler` 연결이 실제 프로젝트에서도 유지되어야 하는지 검토한다.
- [ ] `mapperLocations` 전개 보조기 사용 방식을 운영 절차에 포함할지 결정한다.
- [ ] `--db-type` 입력값을 실제 운영 대상 DB와 맞춰 적용하는 절차를 문서화한다.

### 4. DAO 후속 정리

- [ ] 직접 `iBatis` API를 사용하는 DAO가 실제 프로젝트에 존재하는지 다시 확인한다.
- [ ] `EgovComAbstractDAO` wrapper 변환 이후 하위 DAO가 정상 동작하는지 샘플 외 실제 프로젝트 기준으로 확인한다.
- [ ] `list() -> selectList()`, `select() -> selectOne()` 외 추가 DAO API 패턴이 필요한지 검토한다.
- [ ] DAO 자동변환 결과 중 “정보성 안내”와 “실제 수동검토 경고”를 계속 분리 유지한다.

### 5. 보고서 및 산출물 정리

- [ ] 최종 보고서에서 수동 검토 항목을 “조치 필요 / 예외 검토 / 범위 외”로 세분화할지 결정한다.
- [ ] 실제 프로젝트 적용 시 보관할 JSON/Markdown 산출물 목록을 확정한다.
- [ ] 폐쇄망 반입용으로 필요한 최소 산출물 세트를 정리한다.
- [ ] phase2 보고서의 핵심 지표(`changed_file_count`, `manual_review_file_count`, `residual_warning_count`)를 운영 기준으로 사용할지 확정한다.

### 6. 처리 원칙 문서화

- [ ] 자동 변환 가능 항목과 자동 변환 제외 항목을 명확히 구분한다.
- [ ] 품질 정책/보안 정책 위반 가능 코드(`식별자 위치 ${}` 치환 등)는 자동 승인하지 않는다는 원칙을 유지한다.
- [ ] 실제 프로젝트에서는 “없어야 하는 코드”로 간주하는 항목을 별도 목록으로 관리한다.
- [ ] 샘플 프로젝트 결과와 실제 프로젝트 결과를 혼동하지 않도록 문서에 적용 범위를 명시한다.

### 7. 현재 기준 해석

- [x] SQL Map 기본 문법 변환 규칙은 MVP 수준으로 구현되었다.
- [x] DAO 기본 변환 규칙과 postcheck는 동작 가능한 수준으로 정리되었다.
- [x] Spring XML 1차 변환과 `mapperLocations` 전개 보조기가 준비되었다.
- [x] 보고서/JSON 산출 체계는 phase2 운영 검토가 가능한 수준으로 정리되었다.
- [ ] 남은 핵심은 “실제 프로젝트 기준 재보정”과 “수동 검토 정책 확정”이다.
