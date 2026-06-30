# Tools Guide

`tools/` 디렉터리는 전자정부프레임워크 3.x -> 4.3 전환을 위한 Python 도구 모음이다.

이 문서는 도구 구조와 Phase2 실행 방법에 초점을 맞춘다. 전체 전환 절차는 상위 문서인 `README.md`와 `docs/migration-process.md`를 참고한다.

---

## 관련 문서

* `../README.md`
* `../docs/migration-process.md`
* `CONVERSION_ARCHITECTURE.md`
* `SQLMAPCLIENT_USAGE_ANALYZER.md`

---

## 디렉터리 구조

```text
tools/
├── README.MD
├── CONVERSION_ARCHITECTURE.md
├── inventory/
│   └── collect_inventory.py
├── analysis/
│   ├── analyze_dao.py
│   ├── analyze_sqlmapclient_usage.py
│   ├── classify_dao_targets.py
│   ├── classify_sqlmapclient_targets.py
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

---

## 역할 분리

### inventory

`tools/inventory/collect_inventory.py`는 Java/Maven 기반 프로젝트를 읽기 전용으로 분석하여 AS-IS 인벤토리를 생성한다.

주요 기능:

* 프로젝트 기본 정보 수집
* `pom.xml` 기반 Maven 정보 수집
* Java 소스 통계 및 위험 패턴 수집
* Spring XML / SQL Map / JSP / properties 파일 현황 수집

### analysis

`tools/analysis/`는 특정 전환 주제의 판단 자료를 만드는 분석 도구 영역이다.

현재 포함 도구:

* `analyze_dao.py`
  DAO 후보, 상속, 호출 패턴, 위험 요소 분석
* `analyze_sqlmapclient_usage.py`
  `sqlMapClient` Java/XML 사용처 전수 수집
* `classify_sqlmapclient_targets.py`
  `sqlMapClient` 사용처를 자동/조건부/수동 검토 대상으로 분류
* `classify_dao_targets.py`
  DAO 분석 결과를 바탕으로 전환 후보 분류
* `generate_dao_rag_questions.py`
  RAG/LLM 확인용 질문 생성

### conversion

`tools/conversion/`은 Phase2 규칙 기반 변환을 수행하는 프로그램 영역이다.

기본 파이프라인:

1. `discover`
   프로젝트 스캔 및 변환 대상 탐지
2. `classify`
   iBatis/MyBatis 혼재 여부, DAO 래퍼 존재 여부 등 분류
3. `transform_*`
   DAO / SQL Map / Spring XML 변환
4. `postcheck`
   잔존 패턴과 수동 검토 대상을 탐지
5. `report`
   JSON + Markdown 리포트 생성
6. `run_phase2`
   전체 오케스트레이션

---

## JSON 우선 원칙

분석/변환 프로그램 간 중간 데이터는 JSON을 기준으로 관리한다.

이유:

* Markdown 파싱은 헤더나 표 형식 변경에 취약하다
* JSON은 다음 프로그램 입력으로 안정적이다
* Markdown은 사람 검토용, JSON은 기계 처리용으로 역할 분리가 쉽다

기본 산출물 예시:

```text
output/reports/
├── dao-analysis.md
├── dao-analysis.json
├── phase2-discovery.json
├── phase2-report.json
└── phase2-report.md
```

---

## Phase2 실행 절차

### 1. 사전 준비

필수 입력:

* `--source-root`
  원본 프로젝트 루트
* `--working-root`
  변환 작업 디렉터리
* `--report-root`
  리포트 출력 디렉터리

선택 입력:

* `--dao-analysis-json`
  `tools.analysis.analyze_dao` 결과 JSON
* `--sqlmapclient-targets-json`
  `tools.analysis.classify_sqlmapclient_targets` 결과 JSON
* `--db-type`
  `mapperLocations` 확장이 필요한 경우 DB 타입
* `--copy-source`
  원본을 작업 디렉터리로 복사한 뒤 변환 수행

### 2. 기본 실행

```bash
python -m tools.conversion.run_phase2 ^
  --source-root samples/asis/hello-egov-board ^
  --working-root converted/phase2/hello-egov-board ^
  --report-root output/reports/hello-egov-board ^
  --copy-source
```

### 3. 분석 결과를 연결한 실행

```bash
python -m tools.conversion.run_phase2 ^
  --source-root samples/asis/hello-egov-board ^
  --working-root converted/phase2/hello-egov-board ^
  --report-root output/reports/hello-egov-board ^
  --dao-analysis-json output/reports/dao-pattern-analysis.json ^
  --sqlmapclient-targets-json output/reports/sqlmapclient-usage-targets.json ^
  --copy-source
```

### 4. 내부 처리 순서

`run_phase2.py`는 내부적으로 아래 순서로 동작한다.

1. 작업 디렉터리 준비
2. 프로젝트 탐지와 분류
3. 선택 분석 JSON 병합
4. SQL Map 변환
5. DAO 변환
6. Spring XML 변환
7. 후처리 경고 수집
8. JSON/Markdown 보고서 생성

### 5. 주요 출력물

```text
output/reports/<run-name>/
├── phase2-discovery.json
├── phase2-report.json
└── phase2-report.md
```

`phase2-report.md`에서 특히 확인할 항목:

* 변경 파일 수
* 경고 유형 요약
* 수동 검토 필요 파일
* 잔존 iBatis / Spring 연계 패턴

---

## 권장 운영 방식

1. `inventory`로 AS-IS 범위를 먼저 수집한다.
2. `analysis`로 DAO와 `sqlMapClient` 위험 영역을 분류한다.
3. `run_phase2`로 규칙 기반 변환을 수행한다.
4. `phase2-report.md`를 보고 수동 검토 대상을 정리한다.
5. 반복되는 예외는 규칙으로 환류한다.

---

## 권장 개발 순서

1. `inventory` / `analysis` 스크립트의 JSON 출력을 확장한다.
2. `conversion/discover.py`와 `conversion/classify.py`를 보강한다.
3. `conversion/transform_sqlmap.py`의 규칙 커버리지를 확대한다.
4. `conversion/transform_dao.py`의 DAO 구조 변환 규칙을 보강한다.
5. `conversion/postcheck.py`의 잔존 패턴 검증을 강화한다.
