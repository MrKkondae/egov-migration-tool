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
|   1 | antlr-2.7.7.jar                            | Utility     | Parser         | 대상아님 | N/A                               | Hibernate 종속으로 유지(org.hibernate:hibernate-core:jar:5.6.15.Final) |
|   2 | antlr-3.5.jar                              | Utility     | Parser         | 검토  |                         | 사용처 확인 후 유지/제거 판단 |
|   3 | antlr-runtime-3.5.jar                      | Utility     | Parser Runtime | 검토  |                          | 사용처 확인 후 유지/제거 판단 |
|   4 | aopalliance-1.0.jar                        | Spring      | AOP            | 유지   | Spring Dependency                |
|   5 | aspectjweaver-1.8.0.jar                    | Spring      | AOP            | 버전업  | AspectJ                          | LTW 사용여부 확인 필요 (grep -R "load-time-weaver" .  grep -R "aop.xml" . grep -R "javaagent.*aspectjweaver" . grep -R "META-INF/aop.xml" . ) |
|   6 | bcprov-ext-jdk15-1.4.5.jar                 | Security    | 암호화            | 버전업  | BouncyCastle                     | 자동변환 어려움. org.bouncycastle:bcprov-ext-jdk18on:1.84 Maven 의존성으로 교체하는 것을 권장 |
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
| 25 | ehcache-core-2.x.jar                       | Cache       | 캐시             | 버전업  | Ehcache 3.x                      |
| 26 | gson-2.2.x.jar                             | JSON        | JSON 처리        | 버전업  | Gson 최신                          |
| 27 | httpclient-4.3.x.jar                       | Network     | HTTP 통신        | 버전업  | HttpClient 5.x                   |
| 28 | httpcore-4.3.x.jar                         | Network     | HTTP Core      | 버전업  | HttpCore 5.x                     |
| 29 | ibatis-2.3.x.jar                           | Persistence | ORM            | 대체   | MyBatis 3.x                      |
| 30 | jackson-core-asl-1.x.jar                   | JSON        | JSON 처리        | 대체   | Jackson 2.x                      |
| 31 | jackson-mapper-asl-1.x.jar                 | JSON        | JSON Mapping   | 대체   | Jackson Databind                 |
| 32 | javassist-3.x.jar                          | Utility     | Bytecode       | 버전업  | Javassist 최신                     |
| 33 | jcl-over-slf4j.jar                         | Logging     | Logging Bridge | 유지   | SLF4J                            |
| 34 | jdom-1.x.jar                               | XML         | XML 처리         | 검토   | JDOM2                            |
| 35 | jedis-2.x.jar                              | Cache       | Redis          | 버전업  | Jedis 최신                         |
| 36 | jsch-0.1.x.jar                             | Network     | SSH/SFTP       | 버전업  | JSch 최신                          |
| 37 | json-lib-2.x.jar                           | JSON        | JSON 처리        | 대체   | Jackson/Gson                     |
| 38 | junit-4.x.jar                              | Test        | 단위테스트          | 버전업  | JUnit 5                          |
| 39 | log4j-1.2.x.jar                            | Logging     | Logging        | 제거   | Logback                          |
| 40 | log4jdbc-1.2.jar                           | Logging     | SQL Logging    | 검토   | log4jdbc-remix                   |
| 41 | mybatis-3.x.jar                            | Persistence | ORM            | 유지   | MyBatis 최신                       |
| 42 | mybatis-spring-1.x.jar                     | Persistence | Spring 연동      | 버전업  | MyBatis-Spring 3.x               |
| 43 | ojdbc6.jar                                 | Database    | Oracle JDBC    | 버전업  | ojdbc11.jar                      |
| 44 | poi-3.x.jar                                | Office      | Excel 처리       | 버전업  | Apache POI 최신                    |
| 45 | poi-ooxml-3.x.jar                          | Office      | Excel OOXML    | 버전업  | Apache POI 최신                    |
| 46 | quartz-2.x.jar                             | Batch       | Scheduler      | 유지   | Quartz 최신                        |
| 47 | slf4j-api-1.7.x.jar                        | Logging     | Logging API    | 버전업  | SLF4J 2.x                        |
| 48 | slf4j-log4j12-1.7.x.jar                    | Logging     | Log4j 연동       | 제거   | Logback                          |
| 49 | spring-aop-4.0.x.jar                       | Spring      | AOP            | 버전업  | Spring 6.x                       |
| 50 | spring-beans-4.0.x.jar                     | Spring      | Bean 관리        | 버전업  | Spring 6.x                       |
| 51 | spring-context-4.0.x.jar                   | Spring      | Context        | 버전업  | Spring 6.x                       |
| 52 | spring-core-4.0.x.jar                      | Spring      | Core           | 버전업  | Spring 6.x                       |
| 53 | spring-expression-4.0.x.jar                | Spring      | SpEL           | 버전업  | Spring 6.x                       |
| 54 | spring-jdbc-4.0.x.jar                      | Spring      | JDBC           | 버전업  | Spring 6.x                       |
| 55 | spring-tx-4.0.x.jar                        | Spring      | Transaction    | 버전업  | Spring 6.x                       |
| 56 | spring-web-4.0.x.jar                       | Spring      | Web            | 버전업  | Spring 6.x                       |
| 57 | spring-webmvc-4.0.x.jar                    | Spring      | MVC            | 버전업  | Spring 6.x                       |
| 58 | taglibs-standard-1.1.x.jar                 | Web         | JSTL           | 대체   | jakarta.servlet.jsp.jstl         |
| 59 | tiles-api-2.x.jar                          | Web         | 화면구성           | 제거   | Thymeleaf                        |
| 60 | tiles-core-2.x.jar                         | Web         | 화면구성           | 제거   | Thymeleaf                        |
| 61 | tiles-jsp-2.x.jar                          | Web         | 화면구성           | 제거   | Thymeleaf                        |
| 62 | velocity-1.7.jar                           | Template    | 템플릿 엔진         | 제거   | Thymeleaf                        |
| 63 | xalan-2.x.jar                              | XML         | XSLT           | 검토   | JDK 기본                           |
| 64 | xercesImpl-2.x.jar                         | XML         | XML Parser     | 검토   | JDK 기본                           |
| 65 | xml-apis-1.x.jar                           | XML         | XML API        | 제거   | JDK 기본                           |
| 66 | xmlbeans-2.x.jar                           | XML         | XML Binding    | 버전업  | XMLBeans 최신                      |
| 67 | activation-1.1.jar                         | Jakarta     | Mail 지원        | 대체   | jakarta.activation               |
| 68 | mail-1.4.x.jar                             | Jakarta     | 메일             | 대체   | jakarta.mail                     |
| 69 | servlet-api-2.5.jar                        | Web         | Servlet API    | 대체   | jakarta.servlet-api              |
| 70 | jsp-api-2.1.jar                            | Web         | JSP API        | 대체   | jakarta.servlet.jsp-api          |
| 71 | standard.jar                               | Web         | JSTL           | 대체   | jakarta.servlet.jsp.jstl         |
| 72 | validator-rules.xml 관련 라이브러리               | Validation  | 입력값 검증         | 유지   | Commons Validator                |
| 73 | xecure-7.jar                               | Security    | 전자서명           | 검토   | Non-ActiveX 대체                   |
