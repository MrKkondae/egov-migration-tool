# eGov Migration Tool

전자정부프레임워크 3.x 프로젝트를 4.3 기준으로 전환하기 위한 규칙, 자동화 도구, 검증 절차를 관리하는 저장소다.

## 목표

이 프로젝트의 목표는 한 번에 전체 전환을 끝내는 것이 아니라, 반복 가능한 규칙과 검증 절차를 정리해서 전환 작업의 예측 가능성을 높이는 것이다.

전체 흐름은 아래와 같다.

```text
AS-IS 분석
    -> TO-BE 조사
    -> 전환 규칙 설계
    -> Phase1 변환 (OpenRewrite)
    -> Phase2 변환 (Python Rule Engine)
    -> Phase3 변환 (LLM 보정)
    -> 컴파일 검증
    -> 전환 규칙 보강
```

## 문서 안내

* `README.md`
  프로젝트 개요, 전체 전환 흐름, 현재 검증 상태
* `docs/migration-process.md`
  Phase1/Phase2 중심의 상세 수행 절차
* `rules/phase1-openrewrite/PHASE1_OPENREWRITE_MANUAL.md`
  OpenRewrite 기반 Phase1 실행 절차
* `nexus/Nexus_구축가이드.md`
  로컬 Nexus 구축 및 Maven 미러 설정
* `tools/PHASE2_TOOLS_GUIDE.md`
  Python 기반 도구 실행 방법

## Phase 정의

### Phase1

OpenRewrite 기반의 보수적 자동 전환 단계다.

주요 대상:

* `pom.xml` 의존성 좌표 정리
* Java import/package rename
* XML 문자열 기반 안전 치환

### Phase2

Python 규칙 기반 구조 전환 단계다.

주요 대상:

* DAO 구조 전환
* SQL Map -> MyBatis XML 구조 정리
* Spring XML 구조 보완

### Phase3

LLM 기반 예외 보정 단계다.

주요 대상:

* 프로젝트별 특수 케이스
* 동적 SQL, 커스텀 DAO, 복잡한 wiring

## Phase1 현재 검증 범위

현재까지 실제로 끝까지 검증된 범위는 Phase1 전체가 아니라 `POM eGovFrame 좌표 전환`이다.

검증 완료 조건:

* `JDK 8` 환경에서 Maven 실행
* 로컬 Nexus를 통한 의존성 해석
* `dryRunNoFork`
* `runNoFork`
* `validate`
* `dependency:tree`

검증 대상:

* `samples/asis/hello-egov-board/pom.xml`

현재 운영 기준:

* POM 전환 표준 진입점은 `rules/phase1-openrewrite/pom/egovframe-coordinates.yml`
* `rules/phase1-openrewrite/rewrite.yml`은 전체 통합 진입점으로 유지
* Java/XML 레시피는 아직 같은 수준으로 끝까지 검증되지 않았으므로 Phase1 전체 완료로 보지 않는다

상세 실행 방법은 아래 문서를 참고한다.

* [Phase1 OpenRewrite Manual](./rules/phase1-openrewrite/PHASE1_OPENREWRITE_MANUAL.md)

## 산출물 기준

* Phase1 결과물: `rules/phase1-openrewrite/`, `converted/phase1/`, `output/rewrite-patches/`
* Phase2 결과물: `converted/phase2/`, `output/reports/`, `output/logs/`
* 공통 검증 결과: `output/logs/`, `output/reports/`

운영 기준:

* `converted/phase1/<project>/` 는 Phase1 적용 및 검증 완료 후 보관한 최종 소스 기준본이다.
* Phase2는 기본적으로 이 `converted/phase1/<project>/` 를 입력 소스로 사용한다.

## 세부 문서

* [전환 수행 절차](./docs/migration-process.md)
* [OpenRewrite Phase1 매뉴얼](./rules/phase1-openrewrite/PHASE1_OPENREWRITE_MANUAL.md)
* [로컬 Nexus 구축 가이드](./nexus/Nexus_구축가이드.md)
* [도구 사용 안내](./tools/PHASE2_TOOLS_GUIDE.md)
* [전환 아키텍처](./tools/CONVERSION_ARCHITECTURE.md)
* [sqlMapClient 분석기 문서](./tools/SQLMAPCLIENT_USAGE_ANALYZER.md)
