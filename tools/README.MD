# Tools Guide

## inventory

`tools/inventory/collect_inventory.py` 는 Java/Maven 기반 전자정부프레임워크 프로젝트를 읽기 전용으로 분석해 AS-IS 인벤토리 Markdown을 생성하는 도구입니다.

### 기능

- 프로젝트 기본 정보 수집
- `pom.xml` 기반 Maven 정보 수집
- Java 소스 통계 및 위험 패턴 수집
- Spring XML 설정 수집
- iBatis / MyBatis SQL Map 수집
- `web.xml` 설정 수집
- JSP / 화면 패턴 수집
- `.properties` 파일 주요 키 수집
- 전환 우선순위 후보 자동 생성
- 분석 실패 파일 목록 수집

### 요구 사항

- Python 3.9 이상
- 외부 패키지 설치 불필요
- Python 표준 라이브러리만 사용

### 실행 방법

```bash
python3 tools/inventory/collect_inventory.py \
  --source-root samples/asis/hello-egov-board \
  --output output/inventory/as-is-inventory.md
```

### 인자 설명

- `--source-root`: 분석 대상 프로젝트 루트 디렉터리
- `--output`: 생성할 Markdown 결과 파일 경로

### 출력 파일

- 예시: `output/inventory/as-is-inventory.md`

### 동작 방식

- 원본 소스는 수정하지 않습니다.
- 프로젝트 파일은 읽기 전용으로 분석합니다.
- UTF-8 우선으로 읽고 실패 시 CP949로 재시도합니다.
- 바이너리 파일은 분석에서 제외합니다.
- 일부 파일 분석에 실패해도 전체 실행은 계속됩니다.
- `password`, `passwd`, `pwd`, `secret`, `token` 관련 값은 `******` 로 마스킹합니다.

### 분석 제외 디렉터리

- `target`
- `.git`
- `.idea`
- `.vscode`
- `node_modules`
- `build`
- `dist`

## analysis

`tools/analysis/analyze_dao.py` 는 AS-IS Java 소스에서 DAO 후보 파일을 찾아 전환 대상, 위험 요소, 자동변환 가능 여부를 분석하고 Markdown 보고서를 생성하는 도구입니다.

### 기능

- `.java` 파일 재귀 검색
- DAO 후보 탐지
- eGov DAO 관련 상속 / import 수집
- DAO API 사용 횟수 수집
- 위험 요소 플래그 수집
- 룰 파일 기반 분류
- DAO 분석 보고서 생성

### 요구 사항

- Python 3.11 이상
- 외부 패키지 설치 불필요
- Python 표준 라이브러리만 사용

### 실행 방법

```bash
python3 tools/analysis/analyze_dao.py \
  --source samples/asis \
  --output output/reports/dao-analysis.md
```

### 인자 설명

- `--source`: 분석 대상 루트 디렉터리
- `--output`: 생성할 Markdown 보고서 경로
- `--rules`: DAO 분류 기준 룰 파일 경로

### 룰 파일

- 기본 경로: `rules/analysis/dao-analysis-rules.yaml`
- 룰 파일이 없으면 기본 룰 파일을 자동 생성합니다.
- 룰 파일을 읽지 못하면 내장 기본 룰로 계속 실행합니다.

### 출력 파일

- 예시: `output/reports/dao-analysis.md`

### 동작 방식

- 원본 소스는 수정하지 않습니다.
- Java AST 파서 없이 정규식과 문자열 검색 기반으로 분석합니다.
- UTF-8 기준으로 읽고 인코딩 문제는 `errors="ignore"`로 처리합니다.
- DAO 후보 여부와 위험 플래그를 수집합니다.
- 최종 분류는 코드 내부 하드코딩이 아니라 룰 파일 기준으로 결정합니다.
- 분석 실패 파일도 보고서 대상에 포함할 수 있습니다.
