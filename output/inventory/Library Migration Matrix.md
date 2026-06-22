# Library Migration Matrix

전자정부프레임워크 3.1 → 4.3 전환 시 사용 라이브러리의 전환 대상 여부를 정리한 문서이다.

## 분류 기준

| 구분   | 설명                        |
| ---- | ------------------------- |
| 유지   | 그대로 사용 가능                 |
| 버전업  | 최신 버전으로 업그레이드             |
| 대체   | 다른 라이브러리 또는 프레임워크 기능으로 교체 |
| 제거   | 사용 중단                     |
| 검토   | 별도 분석 필요                  |
| 대상아님 | 전환 대상 아님                  |

## Library Matrix

|  NO | eGov 3.1 Lib                               | 구분          | 용도             | 전환대상 | eGov 4.3 Lib                     | 비고                |
| --: | ------------------------------------------ | ----------- | -------------- | ---- | -------------------------------- |  ---------------- |
|   1 | antlr-2.7.7.jar                            | Utility     | Parser         | 대상아님 | N/A                               | Maven 전이의존(org.hibernate:hibernate-core:jar:5.6.15.Final) |
|   2 | antlr-3.5.jar                              | Utility     | Parser         | 버전업  | Maven 최신                         |
|   3 | antlr-runtime-3.5.jar                      | Utility     | Parser Runtime | 버전업  | Maven 최신                         |
|   4 | aopalliance-1.0.jar                        | Spring      | AOP            | 유지   | Spring Dependency                |
|   5 | aspectjweaver-1.8.0.jar                    | Spring      | AOP            | 버전업  | AspectJ                          |
|   6 | bcprov-ext-jdk15-1.4.5.jar                 | Security    | 암호화            | 버전업  | BouncyCastle                     |
|   7 | commons-1.0.jar                            | Utility     | Commons        | 검토   | 확인 필요                            |
|   8 | commons-beanutils-1.8.3.jar                | Utility     | Bean 처리        | 버전업  | Commons BeanUtils                |
|   9 | commons-collections-3.1.jar                | Utility     | Collection     | 버전업  | Commons Collections4             |
|  10 | commons-dbcp-1.4.jar                       | Persistence | DB Pool        | 대체   | HikariCP                         |
|  11 | commons-digester-1.8.jar                   | Utility     | XML Parsing    | 검토   | 확인 필요                            |
|  12 | commons-fileupload-1.3.1.jar               | Web         | 파일업로드          | 버전업  | Commons FileUpload               |
|  13 | commons-io-2.2.jar                         | Utility     | IO 처리          | 버전업  | Commons IO                       |
|  14 | commons-lang3-3.3.2.jar                    | Utility     | 문자열            | 버전업  | Commons Lang3                    |
|  15 | commons-logging-1.1.1.jar                  | Logging     | Logging        | 제거   | SLF4J/Logback                    |
|  16 | commons-net-3.3.jar                        | Utility     | FTP 등          | 버전업  | Commons Net                      |
|  17 | commons-pool-1.5.4.jar                     | Persistence | Pool           | 대체   | HikariCP                         |
|  18 | commons-validator-1.4.0.jar                | Validation  | 검증             | 유지   | Commons Validator                |
|  19 | egovframework.rte.fdl.cmmn-3.1.0.jar       | eGov        | 공통기능           | 대체   | org.egovframe.rte.fdl.cmmn       |
|  20 | egovframework.rte.fdl.idgnr-3.1.0.jar      | eGov        | ID 생성          | 대체   | org.egovframe.rte.fdl.idgnr      |
|  21 | egovframework.rte.fdl.logging-3.1.0.jar    | eGov        | 로깅             | 대체   | org.egovframe.rte.fdl.logging    |
|  22 | egovframework.rte.fdl.property-3.1.0.jar   | eGov        | Property       | 대체   | org.egovframe.rte.fdl.property   |
|  23 | egovframework.rte.psl.dataaccess-3.1.0.jar | eGov        | DAO            | 대체   | org.egovframe.rte.psl.dataaccess |
|  24 | egovframework.rte.ptl.mvc-3.1.0.jar        | eGov        | MVC            | 대체   | org.egovframe.rte.ptl.mvc        |
| ... | ...                                        | ...         | ...            | ...  | ...                              |
|  73 | xecure-7.jar                               | Security    | 전자서명           | 검토   | Non-ActiveX 대체                   |
