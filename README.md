# eGov Migration Tool

전자정부프레임워크 3.x → 4.3 전환 자동화를 위한 도구 및 전환 규칙 관리 프로젝트

---

# 목표

본 프로젝트는 전자정부프레임워크 3.x 시스템을 4.3 환경으로 전환하기 위한 전환 절차, 전환 규칙, 자동화 도구 및 검증 체계를 구축하는 것을 목표로 한다.

최종적으로는 다음과 같은 전환 프로세스를 자동화한다.

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

# 수행 주체

| 단계        | OpenRewrite | Python | LLM | 전환담당자 |
| --------- | ----------- | ------ | --- | ----- |
| AS-IS 분석  | -           | 주관     | 보조  | 검토    |
| TO-BE 조사  | -           | -      | 주관  | 검토    |
| 전환규칙 수립   | -           | -      | 주관  | 승인    |
| Phase1 변환 | 주관          | -      | -   | 검토    |
| Phase2 변환 | 보조          | 주관     | -   | 검토    |
| Phase3 변환 | -           | -      | 주관  | 승인    |
| 컴파일 검증    | -           | 주관     | 보조  | 검토    |
| 룰 보강      | -           | -      | 주관  | 승인    |

---

## 전환 기준 문서

전자정부프레임워크 전환 절차와 역할 기준은 아래 문서를 따른다.

* `docs/migration-process.md`

본 프로젝트의 모든 프롬프트, 분석 도구, 변환 도구는 해당 문서를 기준으로 작성한다.

---

# 전환 절차

## 1. AS-IS 인벤토리 수집

### 목적

현재 시스템의 구조 및 기술 스택을 분석하여 전환 범위를 식별한다.

### 수행 주체

* Python 프로그램
* 전환 담당자

### 수행 내용

#### 프로젝트 구조 분석

* Maven 프로젝트 수
* 모듈 수
* Java Source 수
* JSP 수
* SQL Map 수
* Spring XML 수

#### Dependency 분석

* pom.xml 분석
* Library 분석
* eGovFrame 버전 확인

#### 기술 스택 분석

* Spring MVC
* iBatis
* MyBatis
* Security
* Scheduler
* Validator
* Property Service
* ID Generator

### 산출물

```text
output/inventory/
```

---

## 2. TO-BE 후보 조사 (RAG 기반)

### 목적

전자정부프레임워크 4.3 기준 변경사항을 수집한다.

### 수행 주체

* LLM
* 전환 담당자

### 수행 내용

#### 공식 자료 분석

* eGovFrame Wiki
* Release Note
* Migration Guide

#### 샘플 프로젝트 분석

* eGovFrame 4.3 Sample

#### 기존 전환 사례 분석

* 사내 전환 프로젝트
* 검증 완료된 전환 규칙

#### 변경점 수집

예)

```text
EgovAbstractDAO
→ EgovAbstractMapper
```

```text
sqlMapClient
→ SqlSessionFactory
```

```text
iBatis
→ MyBatis
```

### 산출물

```text
knowledge/
```

---

## 3. 전환 규칙 수립

### 목적

자동 변환 가능한 규칙을 정의한다.

### 수행 주체

* LLM
* 전환 담당자

### 수행 내용

#### pom.xml 규칙

* Dependency 변경
* Version 변경
* Plugin 변경

#### DAO 규칙

* Class 변경
* Import 변경
* Method 변경

#### SQL Map 규칙

* XML Namespace 변경
* Dynamic SQL 변경
* Parameter 변경

#### Spring XML 규칙

* Bean 변경
* DataSource 변경
* Transaction 변경

#### Controller 규칙

* Annotation 변경
* Import 변경

### 산출물

```text
rules/
├── pom-rules.yaml
├── dao-rules.yaml
├── sqlmap-rules.yaml
├── spring-rules.yaml
└── controller-rules.yaml
```

---

# 전환 Phase 정의

전자정부프레임워크 전환은 모든 항목을 동일한 방식으로 처리할 수 없다.

변경 난이도와 자동화 가능 수준에 따라 전환 대상을 Phase 단위로 분류한다.

---

## Phase 1 : OpenRewrite 기반 구조 변환

### 특징

* 패턴이 명확함
* 변경 전/후 매핑이 확정됨
* 소스 의미 변경 없음
* 대규모 자동 변환 가능

### 수행 도구

* OpenRewrite

### 대상

#### Maven Dependency

```text
egovframework.rte.*
→
org.egovframe.rte.*
```

#### Spring Dependency

```text
Spring 3.x
→
Spring 5.x / Boot 관리
```

#### Jackson

```text
org.codehaus.jackson.*
→
com.fasterxml.jackson.*
```

#### Oracle JDBC

```text
ojdbc14
→
ojdbc8
```

#### Logging

```text
commons-logging
→
slf4j
```

### 산출물

```text
converted/phase1/
```

---

## Phase 2 : 규칙 기반 소스 변환

### 특징

* 코드 구조 변경 필요
* 규칙은 명확
* OpenRewrite만으로 부족

### 수행 도구

* Python
* OpenRewrite 일부

### 대상

#### DAO

```java
extends EgovAbstractDAO
→
extends EgovAbstractMapper
```

#### Import

```java
egovframework.*
→
org.egovframe.*
```

#### SQL Map

```xml
#id#
→
#{id}
```

#### MyBatis

```xml
sqlMap
→
mapper
```

#### Validation

```java
spring-modules-validation
→
Bean Validation
```

#### Quartz

```text
Quartz 1.x
→
Quartz 2.x
```

### 산출물

```text
converted/phase2/
```

---

## Phase 3 : LLM 예외 보정

### 특징

* 프로젝트별 편차 존재
* 정형화 어려움
* 업무 코드 영향 가능

### 수행 도구

* LLM
* 전환 담당자

### 대상

#### iBatis → MyBatis

```xml
<dynamic>
<isNotEmpty>
<iterate>
```

↓

```xml
<if>
<foreach>
<choose>
```

#### 복잡한 DAO

```java
queryForList()
queryForObject()
```

↓

```java
selectList()
selectOne()
```

#### Spring XML 특수 설정

```xml
Bean Wiring
Custom FactoryBean
```

#### 솔루션 연계

```text
OZ
Petra
Xecure
JCAOS
```

#### 컴파일 오류 보정

```text
Import 오류
Mapper 오류
API 변경 오류
```

### 산출물

```text
output/reports/
```

---

## 4. 자동 변환

### 목적

전환 규칙을 이용하여 자동 변환을 수행한다.

### 수행 주체

* OpenRewrite
* Python 프로그램

### 수행 내용

#### Phase1

* Dependency 변경
* Maven 구조 정리
* Import 변경

#### Phase2

* DAO 변환
* SQL Map 변환
* Spring XML 변환

### 산출물

```text
converted/
```

---

## 5. LLM 예외 보정

### 목적

규칙 기반 변환으로 처리하기 어려운 부분을 보완한다.

### 수행 주체

* LLM
* 전환 담당자

### 수행 내용

#### DAO 보정

```java
list()
→
selectList()
```

#### SQL Map 보정

```xml
#id#
→
#{id}
```

#### Dynamic SQL 보정

```xml
<isNotEmpty>
→
<if test="">
```

#### Spring XML 보정

* Bean Wiring 검토
* 복잡한 설정 검토

### 산출물

```text
output/reports/
```

---

## 6. 컴파일 검증

### 목적

전환 결과의 정상 동작 여부를 검증한다.

### 수행 주체

* Python 프로그램
* 전환 담당자

### 수행 내용

#### Build 수행

```bash
mvn clean compile
```

#### 오류 분석

* Import 오류
* Dependency 오류
* API 변경 오류
* Mapper 오류

#### 오류 분류

##### 자동 수정 가능

* Import 누락
* Package 변경

##### 규칙 추가 필요

* API 변경
* Framework 변경

##### 수동 검토 필요

* 업무 로직
* SQL 로직

### 산출물

```text
output/logs/
output/reports/
```

---

## 7. 전환 규칙 보강

### 목적

검증 과정에서 발견된 오류를 규칙에 반영하여 재사용성을 높인다.

### 수행 주체

* LLM
* 전환 담당자

### 수행 내용

#### 오류 패턴 분석

예)

```java
import egovframework.rte.psl.dataaccess.EgovAbstractMapper;
```

↓

```java
import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper;
```

#### 규칙 추가

```yaml
rule-id: DAO-001
phase: PHASE2
tool: python

dao-import:
  before:
    - egovframework.rte.psl.dataaccess.EgovAbstractMapper
  after:
    - org.egovframe.rte.psl.dataaccess.EgovAbstractMapper
```

#### 규칙 저장

* DAO 규칙
* SQL Map 규칙
* Spring 규칙
* pom.xml 규칙

### 산출물

```text
rules/
```

---

# 디렉토리 구조

```text
egov-migration-tool/
├── rules/
│   ├── phase1-openrewrite/
│   ├── phase2-python/
│   └── phase3-llm/
├── tools/
│   ├── inventory/
│   ├── analysis/
│   └── conversion/
├── prompts/
├── knowledge/
├── samples/
│   ├── asis/
│   └── expected/
├── output/
│   ├── inventory/
│   ├── reports/
│   └── logs/
├── converted/
│   ├── phase1/
│   ├── phase2/
│   └── phase3/
└── README.md
```

## 디렉토리 설명

* rules/phase1-openrewrite = OpenRewrite 규칙
* rules/phase2-python = Python 변환 규칙
* rules/phase3-llm = LLM 보정 규칙
* tools/inventory = AS-IS 인벤토리 분석
* tools/analysis = 패턴 분석
* tools/conversion = 변환 프로그램
* prompts = Codex/LLM 프롬프트
* knowledge = RAG 및 조사 결과
* samples/asis = 원본 소스
* samples/expected = 기대 결과 샘플
* output/inventory = 인벤토리 분석 결과
* output/reports = 검토 보고서
* output/logs = 실행 로그
* converted/phase1 = OpenRewrite 결과
* converted/phase2 = Python 변환 결과
* converted/final = 최종 결과

---

# 최종 목표

* 전환 규칙 자산화
* 반복 가능한 전환 프로세스 구축
* OpenRewrite + Python + LLM 역할 분리
* LLM 의존도 최소화
* Python 기반 자동 변환율 향상
* 프로젝트별 전환 품질 표준화
* 전자정부프레임워크 전환 방법론 정립
