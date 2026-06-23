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
|  10 | commons-dbcp-1.4.jar                       | Persistence | DB Pool        | 대체   | Tomcat JDBC, Commons DBCP2, PoolHikariCP (Spring Boot)                         |
|  11 | commons-digester-1.8.jar                   | Utility     | XML Parsing    | 검토대상(제거)   | 확인 필요                            |
|  12 | commons-fileupload-1.3.1.jar               | Web         | 파일업로드          | 검토  | Commons FileUpload               |
|  13 | commons-io-2.2.jar                         | Utility     | IO 처리          | 버전업  | Commons IO                       |
|  14 | commons-lang3-3.3.2.jar                    | Utility     | 문자열            | 버전업  | Commons Lang3                    |
|  15 | commons-logging-1.1.1.jar                  | Logging     | Logging        | 제거   | SLF4J/Logback                    |
|  16 | commons-net-3.3.jar                        | Utility     | FTP 등          | 버전업  | Commons Net                      |
|  17 | commons-pool-1.5.4.jar                     | Persistence | Pool           | 대체   | HikariCP                         |
|  18 | commons-validator-1.4.0.jar                | Validation  | 검증             | 검토대상(제거)   | Commons Validator                |
|  19 | egovframework.rte.fdl.cmmn-3.1.0.jar       | eGov        | 공통기능           | 대체   | org.egovframe.rte.fdl.cmmn       |
|  20 | egovframework.rte.fdl.idgnr-3.1.0.jar      | eGov        | ID 생성          | 대체   | org.egovframe.rte.fdl.idgnr      |
|  21 | egovframework.rte.fdl.logging-3.1.0.jar    | eGov        | 로깅             | 대체   | org.egovframe.rte.fdl.logging    |
|  22 | egovframework.rte.fdl.property-3.1.0.jar   | eGov        | Property       | 대체   | org.egovframe.rte.fdl.property   |
|  23 | egovframework.rte.psl.dataaccess-3.1.0.jar | eGov        | DAO            | 대체   | org.egovframe.rte.psl.dataaccess |
|  24 | egovframework.rte.ptl.mvc-3.1.0.jar        | eGov        | MVC            | 대체   | org.egovframe.rte.ptl.mvc        |
|  25 | exportfile-2.0.jar | ETC | 연말정산 | 검토 | 확인 필요 | SI 프로젝트에서 자체 제작 가능성 높음 | 
| 26 | `ibatis-sqlmap-2.3.4.726.jar` | Persistence | SQL Mapper | 대체 | `mybatis-3.5.x` + `mybatis-spring-2.1.x` / `org.egovframe.rte.psl.dataaccess` | iBatis 사용 범위 확인 후 MyBatis로 통합 전환 필요. `SqlMapClient`, `SqlMapClientTemplate`, `<sqlMap>`, `resultClass`, `parameterClass` 사용 여부 점검 |
| 27 | `icu4j-53.1.jar` | Utility | 국제화 / 문자 처리 | 버전업 | `icu4j` 최신 JDK8 호환 버전 | 유니코드, 로케일, 날짜/문자 처리용. 직접 사용 여부 확인 후 eGov 4.3 환경에서 호환 버전 적용 |
| 28 | `itext-2.1.7.jar` | Document | 연말정산, PDF 생성 / 편집 | 대체 | `OpenPDF 1.3.x` 또는 상용 `iText 7` | iText 5.x(2009년)부터 AGPL로 전환됨 (iText 3.x 공개 배포 버전 미존재). 현재 사용 중인 2.1.7도 IP 불명확성 이슈로 유지 부적합.  OpenPDF(LGPL/MPL, com.lowagie.text 패키지 유지)는 소스 수정 없이 전환 가능하여 1순위 대안. |
| 29 | `jackcess-2.0.7.jar` | Document / Data | MS Access 파일 처리 | 버전업 / 검토 | `jackcess` 최신 JDK8 호환 버전 | `.mdb`, `.accdb` 파일 사용 여부 확인. 실제 사용하지 않으면 제거 검토 가능 |
| 30 | `jackson-core-asl-1.9.13.jar` | JSON | JSON Core | 대체 | `com.fasterxml.jackson.core:jackson-core:2.x` | Jackson 1.x 계열에서 2.x 계열로 변경. `org.codehaus.jackson` → `com.fasterxml.jackson` import 변경 필요 |
| 31 | `jackson-mapper-asl-1.9.13.jar` | JSON | JSON Mapping | 대체 | `com.fasterxml.jackson.core:jackson-databind:2.x` + `jackson-annotations` | JSON ↔ Java 객체 매핑용. Spring MVC 설정에 `MappingJacksonHttpMessageConverter`가 있으면 `MappingJackson2HttpMessageConverter`로 변경 필요 |
| 32 | `jasypt-1.9.2.jar` | Security | 문자열 / Property 암호화 | 버전업 / 검토 | `jasypt-1.9.3` 또는 호환 설정 유지 | 암호화 알고리즘, 키 관리 방식, 운영 환경변수 관리 방식 확인 필요. 암호화/복호화 회귀 테스트 필수 |
| 33 | `jasypt-spring3-1.9.2.jar` | Security / Spring | Spring 암호화 연계 | 대체 / 검토 | `jasypt-spring31` 수동 Bean 설정 또는 Spring Boot 전환 시 `jasypt-spring-boot` | Jasypt 공식 1.9.x 라인에는 Spring 5 전용 모듈이 없음. XML 기반 Spring MVC 환경에서는 수동 Bean 설정 방식 검토 |
| 34 | `jcaos-client-arccert-1.4.7.1.jar` | Security | 연말정산, 인증서 / GPKI 추정 | 검토 | 공급사 최신 JDK8/WAS 호환 버전 | 사설/국산 인증서 모듈 가능성. GPKI, 인증서 로그인, ActiveX 제거 영향, 폐쇄망 반입 파일, 라이선스 확인 필요 |
| 35 | `jcl-over-slf4j-1.7.7.jar` | Logging | Commons Logging → SLF4J Bridge | 버전업 | `jcl-over-slf4j-1.7.36` 또는 eGov 4.3 검증 버전 | Commons Logging 호출을 SLF4J로 전달. `commons-logging.jar`와 중복 구성 여부 확인 필요 |
| 36 | `jdbc-14.jar` | Persistence | Oracle JDBC 추정 | 대체 / 검토 | `ojdbc8` 단일 적용 | `ojdbc14-10.2.0.1.0.jar`와 중복 가능성 큼. JAR Manifest 확인 후 Oracle JDBC 드라이버는 하나로 정리 필요 |
| 37 | `jdom-1.0.jar` | XML | XML 처리 | 대체 / 버전업 | `org.jdom:jdom2:2.x` | JDOM 1.x → JDOM2 전환 시 패키지와 API 변경 가능. XML 생성/파싱 사용 소스 확인 필요 |
| 38 | `jsch-0.1.54.jar` | Network | SSH / SFTP | 대체 / 버전업 | `com.github.mwiede:jsch:0.2.x` 또는 대체 라이브러리 | 원본 JCraft JSch는 유지보수가 제한적이므로 mwiede fork 검토. SFTP 업로드/다운로드, 암호화 알고리즘 호환성 테스트 필요 |
| 39 | `jstl-1.2.jar` | Web | JSTL API | 유지 / 검토 | `javax.servlet:jstl:1.2` 또는 WAS 기준 JSTL 구성 | eGovFrame 4.3 기본은 `javax.*` 유지. Tomcat 10/Servlet 5 이상이 아니면 `jakarta.*`로 일괄 전환하지 않음. WAS 내장 JSTL과 중복 확인 |
| 40 | `jta-1.1.jar` | Transaction | JTA API | 검토 | WAS 제공 JTA 또는 `javax.transaction-api` 계열 | JEUS/WebLogic 등 상용 WAS는 JTA를 제공할 수 있음. 단일 DB 트랜잭션은 Spring `DataSourceTransactionManager`로 처리 가능 여부 확인 |
| 41 | `lib.dstspdfSig-1.1.jar` | Security / Document | PDF 전자서명 추정 | 검토 | 공급사 최신 JDK8/WAS 호환 버전 | PDF 전자서명 모듈 가능성. 인증서, TSA, PDF 생성 라이브러리와 연계되므로 공급사 확인 및 업무 테스트 필수 |
| 42 | `lib.magic.tsaclient-1.1.jar` | Security | TSA 타임스탬프 클라이언트 추정 | 검토 | 공급사 최신 JDK8/WAS 호환 버전 | 타임스탬프 서버 연계 모듈 가능성. TSA 서버 주소, 인증서, 네트워크 정책, 공급사 API 변경 여부 확인 필요 |
| 43 | `log4j-api-2.3.2.jar` | Logging | Log4j2 API | 버전업 / 보안 | `log4j-api-2.17.1` 이상 또는 eGov 4.3 검증 버전 |  log4j-api 단독 사용 시 CVE-2021-44228(Log4Shell) 직접 영향 없음.   log4j-core 포함 환경에서는 2.17.1 이상으로 전체 세트 업그레이드 필요.  log4j-core(NO.44)·log4j-slf4j-impl(NO.46)과 반드시 동일 버전으로 통일. |
| 44 | `log4j-core-2.3.2.jar` | Logging | Log4j2 Core | 버전업 / 보안 | `log4j-core-2.17.1` 이상 또는 eGov 4.3 검증 버전 | Log4Shell 등 보안 취약점 조치 대상. 마이그레이션과 별개로 선제 패치 필요 |
| 45 | `log4j-over-slf4j-1.7.7.jar` | Logging | Log4j 1.x → SLF4J Bridge | 버전업 / 검토 | `log4j-over-slf4j-1.7.36` 또는 eGov 4.3 검증 버전 | 소스에서 `org.apache.log4j.Logger`를 직접 사용하면 필요. 직접 사용이 없으면 제거 검토 가능 |
| 46 | `log4j-slf4j-impl-2.3.1.jar` | Logging | SLF4J → Log4j2 Binding | 버전업 / 보안 | `log4j-slf4j-impl-2.17.1+` 또는 eGov 4.3 검증 버전 | `log4j-api/core`와 버전 통일 필요. log4j-to-slf4j.jar와 동시 클래스패스 존재 시 SLF4J ↔ Log4j2 무한루프 → StackOverflowError 반드시 발생. 구조적 충돌로 반드시 둘 중 하나만 유지해야 함. |
| 47 | `mail-1.4.jar` | Mail | 이메일 송수신 | 버전업 / 검토 | `javax.mail-1.6.x` 계열 | eGovFrame 4.3 기본 환경에서는 `javax.mail` 유지 검토. Tomcat 10/Servlet 5 이상이 아니면 `jakarta.mail` 전환은 별도 과제 |
| 48 | `mybatis-3.2.7.jar` | Persistence | SQL Mapper | 버전업 | `mybatis-3.5.x` | Spring 5 호환을 위해 `mybatis-spring-2.1.x`와 세트 업그레이드 필요. iBatis 잔존 영역과 통합 기준 수립 |
| 49 | `mybatis-spring-1.2.2.jar` | Persistence | MyBatis-Spring 연계 | 버전업 | `mybatis-spring-2.1.x` | Spring 5 호환 버전 필요. MyBatis 3.5.x 이상과 함께 적용하고 `SqlSessionFactoryBean`, `MapperScannerConfigurer` 설정 확인 |
| 50 | `ojdbc14-10.2.0.1.0.jar` | Persistence | Oracle JDBC Driver | 대체 | `ojdbc8` 단일 적용 | JDK8 기준 `ojdbc8`로 정리 권장. `jdbc-14.jar`와 중복 제거, DB/WAS 공통 lib 중복 확인, 드라이버 클래스 `oracle.jdbc.OracleDriver` 적용 확인 |
|  51 | ozenc_utf8.jar                             | Solution   | OZ 암호화/연계       | 대상아님   | OZ Report 프로그램 공급사 확인 필요                       | OZ Report 연계 기능이 존재할 경우 유지 필요, 실제 사용 여부 확인 후 제거, 유지, 대체 결정
|  52 | pdfbox-1.2.1.jar                          | Utility    | 연말정산, PDF 처리            | 버전업 | pdfbox-2.x                         |
|  53 | Petra-1.0.0.jar                           | Security   | DB 접근제어/보안      | 확인   | DB암호화 Petra 공급사 확인 필요                       | 암호화 라이브러리이므로 개인정보 암호화 요구사항과 연관성이 존재함 ,JDK 8 이상 호환성 검증, 암호화 알고리즘 지원 여부 확인, 개인정보 암호화 기능 검증, 인터페이스 연계 데이터 암호화 검증
|  54 | quartz-1.6.3.jar                          | Scheduler  | 배치 스케줄링         | 버전업 | quartz-2.3.x                       | JobDetail 생성 방식 변경, TriggerBuilder 적용, JobBuilder 적용, Scheduler API 변경, Listener API 변경, CronTrigger API 변경, Spring 연계 방식 개선
|  55 | slf4j-api-1.7.7.jar                       | Logging    | Logging API         | 버전업 | slf4j-api-1.7.36                  | jcl-over-slf4j, log4j-over-slf4j, log4j-slf4j-impl 버전 확인, Log4j 1.x 사용 여부 확인, Commons Logging 중복 여부 확인, Classpath 내 SLF4J Binding 중복 여부 확인, log4j2.xml, logback.xml, log4j.properties 설정 파일 확인
|  56 | spring-aop-3.2.9.RELEASE.jar              | Spring     | AOP                 | 버전업 | spring-aop-5.3.37                 | AOP XML 설정 확인, @Aspect, @Before, @After, @Around 사용 여부 확인, Transaction AOP 설정 확인, AspectJ 관련 라이브러리 버전 확인, ApplicationContext 기동 테스트 수행
|  57 | spring-beans-3.2.9.RELEASE.jar            | Spring     | Bean 처리            | 버전업 | spring-beans-5.3.37               | Bean 생성 및 DI 내부 구조 개선, JDK 8 이상 환경 적용, Spring Core 계열 라이브러리 버전 정합성 확보, Bean Lifecycle 처리 개선
|  58 | spring-context-3.2.9.RELEASE.jar          | Spring     | Application Context | 버전업 | spring-context-5.3.37             | ApplicationContext 내부 구조 개선, Component Scan 처리 개선, JDK 8 이상 환경 적용, Spring Core 계열 라이브러리 버전 정합성 확보, Event 처리 기능 개선
|  59 | spring-context-support-3.2.9.RELEASE.jar  | Spring     | Context 확장         | 버전업 | spring-context-support-5.3.37     | JavaMail 지원 라이브러리 버전 변경, Quartz 연계 기능 최신화, Task Scheduling 기능 개선, Spring Core 계열 라이브러리 버전 정합성 확보
|  60 | spring-core-3.2.9.RELEASE.jar             | Spring     | Spring Core         | 버전업 | spring-core-5.3.37                | JDK 8 이상 환경 적용, Resource 처리 기능 개선, Reflection 처리 기능 개선, Utility 기능 개선, Spring Framework 내부 구조 개선
|  61 | spring-expression-3.2.9.RELEASE.jar       | Spring     | SpEL                | 버전업 | spring-expression-5.3.37          | SpEL 엔진 성능 개선, 표현식 처리 기능 개선, JDK 8 이상 환경 적용, Spring Core 계열 라이브러리 버전 정합성 확보
|  62 | spring-jdbc-3.2.9.RELEASE.jar             | Spring     | JDBC 처리            | 버전업 | spring-jdbc-5.3.37                | JDBC Template 내부 구조 개선, Batch 처리 기능 개선, SQLException 처리 기능 개선, JDK 8 이상 환경 적용, Spring Framework 버전 정합성 확보
|  63 | spring-ldap-1.2.1.jar                     | Spring     | LDAP 연계            | 검토 대상 | spring-ldap-core                  | Spring LDAP 버전 업그레이드 검토, LDAP API 변경사항 검토, Active Directory 연계 검증, Spring Framework 5.3 호환성 확보
|  64 | spring-modules-validation-0.9.jar         | Validation | 검증                 | 대체   | Bean Validation / Hibernate Validator | Spring Modules Validation 제거, Bean Validation 기반 구조 적용, Hibernate Validator 적용, Annotation 기반 Validation 적용, Validation 메시지 처리 구조 개선
|  65 | spring-orm-3.2.9.RELEASE.jar              | Spring     | ORM 연계             | 버전업 | spring-orm-5.3.37                 | ORM 연계 기능 최신화, JPA 지원 기능 개선, Hibernate 연계 기능 개선, Spring Framework 버전 정합성 확보
|  66 | spring-tx-3.2.9.RELEASE.jar               | Spring     | Transaction         | 버전업 | spring-tx-5.3.37                  | Transaction 처리 기능 개선, Annotation 기반 Transaction 처리 개선, JDK 8 이상 환경 적용, Spring Framework 버전 정합성 확보
|  67 | spring-web-3.2.9.RELEASE.jar              | Spring     | Web 기능             | 버전업 | spring-web-5.3.37                 | REST 처리 기능 개선, Multipart 처리 기능 개선, HTTP Message Converter 개선, WebApplicationContext 기능 개선, Spring Framework 버전 정합성 확보
|  68 | spring-webmvc-3.2.9.RELEASE.jar           | Spring     | Spring MVC          | 버전업 | spring-webmvc-5.3.37              | MVC 처리 기능 개선, REST 처리 기능 개선, Request Mapping 처리 개선, Validation 처리 개선, Spring Framework 버전 정합성 확보
|  69 | ST4-4.0.7.jar                             | Utility    | Template Engine     | 검토   | 사용 여부 확인                       | eGovFrame 전환과 직접 관련 없음
|  70 | standard-1.1.2.jar                        | Web        | JSTL 구현            | 대체   | taglibs-standard-impl-1.2.5       | standard.jar 제거, JSTL 1.2 적용, 소스 수정 없음
|  71 | stringtemplate-3.2.1.jar                  | Utility    | Template Engine     | 검토대상(제거)   | 사용 여부 확인                       | eGovFrame 전환과 직접 관련 없음
|  72 | xdataset-1.0.1.jar                        | Solution   | XPlatform Dataset   | 확인   | 솔루션/업무 사용 확인                 | XPlatform5 전환시 확인 필요. 전자정부프레임워크 라이브러리가 아니며 XPlatform/MiPlatform 전용 데이터 처리 라이브러리 (eGovFrame 전환과 직접 관련 없음)
|  73 | xecure-7.jar                              | Security   | 암호화/보안모듈       | 확인 | Java API 전환 또는 공급사 확인       | eGovFrame 전환과 직접 관련 없음 |

