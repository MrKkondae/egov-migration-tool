# Tools Guide

`tools/` 디렉터리는 전자정부프레임워크 3.x -> 4.3 전환을 위한 Python 도구를 모아두는 영역이다.

이 도구들은 현재 기준으로 별도 `pip` 설치 없이 표준 라이브러리만으로 실행할 수 있다.

핵심 원칙은 아래와 같다.

* `inventory/`는 프로젝트를 읽어서 전체 현황을 수집한다.
* `analysis/`는 특정 전환 주제에 대해 위험 요소와 후보를 분석한다.
* `conversion/`은 실제 규칙 기반 변환을 수행한다.
* 사람이 읽는 산출물은 Markdown으로, 프로그램 간 전달 데이터는 JSON으로 관리한다.

## 디렉터리 구조

```text
tools/
├── README.MD
├── CONVERSION_ARCHITECTURE.md
├── inventory/
│   └── collect_inventory.py
├── analysis/
│   ├── analyze_dao.py
│   ├── classify_dao_targets.py
│   └── generate_dao_rag_questions.py
├── conversion/
│   ├── __init__.py
│   ├── models.py
│   ├── run_phase2.py
│   ├── discover.py
│   ├── classify.py
│   ├── transform_dao.py
│   ├── transform_sqlmap.py
│   ├── transform_spring_xml.py
│   ├── postcheck.py
│   └── report.py
└── schemas/
    ├── phase2-discovery.schema.json
    └── phase2-report.schema.json
```

## 역할 분리

### inventory

`tools/inventory/collect_inventory.py`는 Java/Maven 기반 전자정부프레임워크 프로젝트를 읽기 전용으로 분석하여 AS-IS 인벤토리 Markdown을 생성한다.

주요 기능:

* 프로젝트 기본 정보 수집
* `pom.xml` 기반 Maven 정보 수집
* Java 소스 통계 및 위험 패턴 수집
* Spring XML / SQL Map / `web.xml` / JSP / `.properties` 수집
* 전환 우선순위 후보 생성

현재 권장 방향:

* 기존 Markdown 출력 유지
* 향후 JSON 출력도 병행 추가

### analysis

`tools/analysis/`는 특정 전환 주제의 판단 자료를 만드는 분석 도구 영역이다.

현재 포함 도구:

* `analyze_dao.py`
  DAO 후보, import, 상속, API 호출, 위험 요소 분석
* `analyze_sqlmapclient_usage.py`
  `sqlMapClient` Java/XML 사용처 전수 수집 및 분류
* `classify_sqlmapclient_targets.py`
  `sqlMapClient` 분석 JSON을 자동/조건부/수동 검토 대상으로 후속 분류
* `classify_dao_targets.py`
  DAO 분석 결과를 바탕으로 전환 후보 분류
* `generate_dao_rag_questions.py`
  RAG/LLM 확인용 질문 생성

현재 권장 방향:

* Markdown 보고서는 유지
* 다음 단계부터는 JSON도 함께 출력
* 다음 프로그램 입력은 Markdown보다 JSON 우선
* 폐쇄망 프로젝트 분석용으로 Java/XML 사용처 전수 수집기를 함께 운영

### conversion

`tools/conversion/`은 Phase 2 규칙 기반 변환 프로그램 영역이다.

기본 파이프라인:

1. `discover`
   프로젝트 스캔 및 변환 대상 탐지
2. `classify`
   iBatis/MyBatis 혼재 여부, DAO 래퍼 존재 여부 등 분류
3. `transform_*`
   DAO / SQL Map / Spring XML 변환
4. `postcheck`
   잔존 패턴, 실패 후보, 수동 검토 대상을 탐지
5. `report`
   JSON + Markdown 리포트 생성
6. `run_phase2`
   전체 오케스트레이션

## JSON 우선 원칙

분석/변환 프로그램 간 중간 데이터는 JSON을 기준으로 관리한다.

이유:

* Markdown 파싱은 헤더나 표 형식 변경에 취약하다
* JSON은 다음 프로그램 입력으로 안정적이다
* Markdown은 사람 검토용, JSON은 기계 처리용으로 역할 분리가 가능하다

기본 산출물 예시:

```text
output/reports/
├── dao-analysis.md
├── dao-analysis.json
├── phase2-discovery.json
├── phase2-report.json
└── phase2-report.md
```

## 권장 개발 순서

1. `inventory` / `analysis` 스크립트에 JSON 출력 추가
2. `conversion/discover.py`와 `conversion/classify.py` 완성
3. `conversion/transform_sqlmap.py`에 MVP 규칙 구현
4. `conversion/transform_dao.py`에 DAO 구조 변환 규칙 추가
5. `conversion/postcheck.py`로 잔존 패턴 검증 자동화

## 실행 예시

### inventory

```bash
python tools/inventory/collect_inventory.py ^
  --source-root samples/asis/hello-egov-board ^
  --output output/inventory/as-is-inventory.md
```

### conversion skeleton

```bash
python -m tools.conversion.run_phase2 ^
  --source-root samples/asis/hello-egov-board ^
  --working-root converted/phase2/hello-egov-board ^
  --report-root output/reports
```

## 관련 문서

* [CONVERSION_ARCHITECTURE.md](./CONVERSION_ARCHITECTURE.md)
* [SQLMAPCLIENT_USAGE_ANALYZER.md](./SQLMAPCLIENT_USAGE_ANALYZER.md)
