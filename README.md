# eGov Migration Tool

전자정부프레임워크 3.x에서 4.3으로 전환하기 위한 절차, 규칙, 자동화 도구를 관리하는 프로젝트다.

---

# 목표

본 프로젝트의 목표는 전환 작업을 일회성 대응이 아니라 재사용 가능한 절차와 도구로 정리하는 것이다.

최종적으로는 아래 흐름을 기준으로 전환을 수행한다.

```text
AS-IS 분석
    ↓
TO-BE 조사
    ↓
전환 규칙 수립
    ↓
Phase1 변환 (OpenRewrite)
    ↓
Phase2 변환 (Python Rule Engine)
    ↓
Phase3 변환 (LLM 보정)
    ↓
컴파일 검증
    ↓
전환 규칙 보강
```

---

# 문서 안내

프로젝트 문서는 아래처럼 역할을 나눠 관리한다.

* `README.md`
  프로젝트 목표, 전체 전환 흐름, Phase 정의, 문서 구조 안내
* `docs/migration-process.md`
  Phase1/Phase2 중심의 상세 수행절차, 입력물/산출물, 검증 포인트
* `tools/README.MD`
  Python 도구 구조와 `run_phase2` 실행 방법

전환 관련 프롬프트, 분석 도구, 변환 도구는 위 문서 구조를 기준으로 정리한다.

---

# 수행 주체

| 단계 | OpenRewrite | Python | LLM | 전환담당자 |
| --- | --- | --- | --- | --- |
| AS-IS 분석 | - | 주관 | 보조 | 검토 |
| TO-BE 조사 | - | - | 주관 | 검토 |
| 전환 규칙 수립 | - | - | 주관 | 승인 |
| Phase1 변환 | 주관 | - | - | 검토 |
| Phase2 변환 | 보조 | 주관 | - | 검토 |
| Phase3 변환 | - | - | 주관 | 승인 |
| 컴파일 검증 | - | 주관 | 보조 | 검토 |
| 규칙 보강 | - | - | 주관 | 승인 |

---

# 전환 절차 개요

## 1. AS-IS 인벤토리 수집

현재 시스템 구조와 기술 스택을 분석하여 전환 범위를 식별한다.

주요 내용:

* Maven 프로젝트, 모듈, Java, JSP, SQL Map, Spring XML 수집
* `pom.xml` 및 라이브러리 분석
* iBatis, MyBatis, Security, Scheduler, Validator 등 기술 스택 파악

산출물:

```text
output/inventory/
```

## 2. TO-BE 후보 조사

전자정부프레임워크 4.3 기준 변경사항과 전환 사례를 수집한다.

주요 내용:

* eGovFrame Wiki, Release Note, Migration Guide 조사
* 샘플 프로젝트와 기존 전환 사례 검토
* `EgovAbstractDAO -> EgovAbstractMapper`
* `sqlMapClient -> SqlSessionFactory`
* `iBatis -> MyBatis`

산출물:

```text
knowledge/
```

## 3. 전환 규칙 수립

자동 변환 가능한 규칙을 정의하고 도구에 반영한다.

주요 대상:

* pom.xml 규칙
* DAO 규칙
* SQL Map 규칙
* Spring XML 규칙
* Controller 규칙

산출물:

```text
rules/
├── phase1-openrewrite/
└── analysis/
```

---

# 전환 Phase 정의

전자정부프레임워크 전환은 모든 항목을 같은 방식으로 처리할 수 없기 때문에, 변경 난이도와 자동화 가능 수준에 따라 Phase 단위로 나눈다.

## Phase1: OpenRewrite 기반 구조 변환

특징:

* 전후 매핑이 명확하다
* 의미 변경 없이 대량 치환이 가능하다
* 저위험 의존성/패키지/타입 변경에 적합하다

주요 대상:

* `egovframework.rte.* -> org.egovframe.rte.*`
* Spring 3.x 계열 의존성 정리
* Jackson 1.x -> 2.x 치환
* `ojdbc14 -> ojdbc8`
* logging 관련 저위험 치환

대표 산출물:

```text
converted/phase1/
rules/phase1-openrewrite/
```

## Phase2: Python 규칙 기반 소스 변환

특징:

* 코드 구조 변경이 필요한 영역을 다룬다
* OpenRewrite 단독으로 처리하기 어려운 변환을 Python이 주도한다
* 변환 후 잔존 패턴 탐지와 수동 검토 분류가 중요하다

주요 대상:

* DAO 상속 및 호출 패턴 변환
* SQL Map에서 MyBatis XML로의 구조 변환
* Spring XML의 `SqlMapClient` 연계 설정 정리
* 후처리 경고와 수동 검토 대상 보고서 생성

대표 산출물:

```text
converted/phase2/
output/reports/
output/logs/
```

실행 방법과 상세 절차는 아래 문서를 참고한다.

* `docs/migration-process.md`
* `tools/README.MD`

## Phase3: LLM 예외 보정

특징:

* 프로젝트별 편차가 큰 영역을 다룬다
* 정형화가 어렵거나 업무 코드 영향이 큰 항목을 보정한다

주요 대상:

* 복잡한 Dynamic SQL
* DAO API 의미 보정
* 특수 Spring XML wiring
* 솔루션 연계 설정
* 컴파일 오류 후속 수정

대표 산출물:

```text
output/reports/
```

---

# 자동 변환과 검증

## 자동 변환

전환 규칙을 이용해 Phase1과 Phase2 변환을 수행한다.

* Phase1: Dependency, Maven 구조, import 정리
* Phase2: DAO, SQL Map, Spring XML 변환

산출물:

```text
converted/
```

## 컴파일 검증

전환 결과의 정상 동작 여부를 검증한다.

주요 내용:

* `mvn clean compile`
* import 오류, dependency 오류, API 변경 오류, mapper 오류 분석
* `자동 수정 가능`, `규칙 추가 필요`, `수동 검토 필요`로 분류

산출물:

```text
output/logs/
output/reports/
```

## 전환 규칙 보강

검증 과정에서 발견된 오류를 규칙에 반영하여 재사용성을 높인다.

예:

```text
import egovframework.rte.psl.dataaccess.EgovAbstractMapper;
→
import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper;
```

---

# 상세 문서

* [전환 수행절차](./docs/migration-process.md)
* [도구 사용 안내](./tools/README.MD)
* [전환 아키텍처](./tools/CONVERSION_ARCHITECTURE.md)
* [sqlMapClient 분석기 문서](./tools/SQLMAPCLIENT_USAGE_ANALYZER.md)
