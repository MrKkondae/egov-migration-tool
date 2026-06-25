# sqlMapClient 사용처 분석기

`tools/analysis/analyze_sqlmapclient_usage.py` 는 폐쇄망 환경에서도 실행할 수 있는 `sqlMapClient` 사용처 분석기다.

목표는 사람의 수작업 검색을 줄이고, 아래 항목을 자동으로 분류해서 보고서로 만드는 것이다.

* 공통 DAO 래퍼
* DAO 직접 사용
* iBatis 직접 의존 코드
* Spring Factory Bean
* Spring 참조 사용처

## 1. 언제 쓰는가

아래 상황에서 먼저 실행하는 것을 권장한다.

* 실제 프로젝트 소스가 폐쇄망 안에만 있는 경우
* `sqlMapClient` 를 무엇으로 바꿔야 할지 사용처별 분기가 필요한 경우
* Spring XML / DAO / 유틸 클래스 중 어느 쪽에 영향이 큰지 먼저 파악하고 싶은 경우

## 2. 입력과 출력

입력:

* Java 소스
* Spring XML

출력:

* Markdown 보고서
* JSON 보고서

기본 출력 경로:

```text
output/reports/sqlmapclient-usage-analysis.md
output/reports/sqlmapclient-usage-analysis.json
```

## 3. 실행 방법

샘플 실행:

```bash
python -m tools.analysis.analyze_sqlmapclient_usage ^
  --source samples/asis/hello-egov-board ^
  --output output/reports/sqlmapclient-usage-analysis.md ^
  --json-output output/reports/sqlmapclient-usage-analysis.json
```

폐쇄망 실제 프로젝트 실행 예:

```bash
python -m tools.analysis.analyze_sqlmapclient_usage ^
  --source D:\\closed-network-project\\legacy-app ^
  --output output/reports/legacy-app-sqlmapclient-usage.md ^
  --json-output output/reports/legacy-app-sqlmapclient-usage.json
```

## 4. 무엇을 찾는가

Java에서 찾는 패턴:

* `SqlMapClient`
* `SqlMapClientTemplate`
* `setSuperSqlMapClient(...)`
* `getSqlMapClientTemplate(...)`

XML에서 찾는 패턴:

* `org.springframework.orm.ibatis.SqlMapClientFactoryBean`
* `property name="sqlMapClient"`
* `ref="egov.sqlMapClient"`

## 5. 분류 기준

### 공통 DAO 래퍼

대표 예:

* `EgovComAbstractDAO`
* `setSuperSqlMapClient(...)` 를 가진 공통 DAO 기반 클래스

해석:

* 여러 DAO가 공통으로 상속하는 중심 클래스
* 변환 우선순위가 높다

### DAO 직접 사용

대표 예:

* `*DAO.java`
* `extends EgovAbstractDAO`
* `extends EgovComAbstractDAO`

해석:

* DAO 내부에 iBatis 흔적이 남아 있는 사용처
* 공통 래퍼 전환 후 후속 규칙 검토 대상

### iBatis 직접 의존 코드

대표 예:

* DAO가 아닌 일반 Java 클래스에서 `SqlMapClient` 나 `SqlMapClientTemplate` 사용

해석:

* 자동 변환보다 수동 검토 가능성이 높다

### Spring Factory Bean

대표 예:

* `SqlMapClientFactoryBean`

해석:

* `SqlSessionFactoryBean` 으로 1차 치환할 수 있는 후보

### Spring 참조 사용처

대표 예:

* `property name="sqlMapClient"`
* `ref="egov.sqlMapClient"`

해석:

* 단순 문자열 치환보다 bean/property 구조 검토가 먼저 필요

## 6. 결과 해석 방법

### Markdown 보고서

사람이 바로 읽기 좋은 요약 보고서다.

확인 포인트:

* Java 사용처 건수
* XML 사용처 건수
* 분류별 건수
* 어떤 bean/class 가 `sqlMapClient` 를 참조하는지

### JSON 보고서

후속 Python 스크립트나 내부 검토 도구가 읽기 좋은 구조다.

주요 필드:

* `summary`
* `java_usages`
* `xml_usages`

`xml_usages` 에는 아래 정보가 들어간다.

* 파일 경로
* bean id
* bean class
* bean class origin
* property 이름 / ref
* 권장 조치

## 7. 폐쇄망 운영 권장 절차

1. 실제 프로젝트 소스 확보
2. 본 분석기 실행
3. 후속 분류 스크립트 실행
4. 결과 JSON/Markdown 검토
5. 사용처를 아래 3가지로 확정
   * 자동 변환 가능
   * 조건부 자동 변환
   * 수동 검토 필요
6. 그 결과를 바탕으로 `transform_spring_xml.py`, `transform_dao.py` 규칙 보강

후속 분류 스크립트 예:

```bash
python -m tools.analysis.classify_sqlmapclient_targets ^
  --input output/reports/sqlmapclient-usage-analysis.json ^
  --output output/reports/sqlmapclient-usage-targets.md ^
  --json-output output/reports/sqlmapclient-usage-targets.json
```

## 8. 한계

이 분석기는 1차 분류 도구다.

즉 아래는 사람이 추가로 판단해야 한다.

* 특정 bean class 가 실제로 `SqlSessionFactory` 를 받을 수 있는지
* `sqlMapClient` 대신 `sqlSessionFactory` 가 맞는지 `sqlSessionTemplate` 이 맞는지
* 외부 라이브러리 / eGov 제공 클래스의 내부 구현 적합성

따라서 이 도구의 역할은:

* 다 찾기
* 1차 분류하기
* 검토 우선순위 정하기

까지로 보는 것이 맞다.
