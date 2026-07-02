# 로컬 Nexus Repository 구축 가이드

## 1. 개요

이 문서는 eGovFrame 3.x -> 4.3 전환 과정에서 Maven 의존성 해석과 OpenRewrite 실행 안정성을 높이기 위한 로컬 Nexus 구성 방법을 정리한다.

목적:

* Maven 저장소 통합 관리
* 폐쇄망 또는 준폐쇄망 환경 대응
* Third-party library 관리
* OpenRewrite 실행 시 의존성 해석 실패 최소화

## 2. 권장 구조

```text
Maven
  -> settings.xml (mirror)
  -> http://localhost:8081/repository/maven-public/
      -> maven-central
      -> egovframe-proxy
      -> maven-releases
```

권장 원칙:

* 클라이언트 Maven은 `maven-public`만 바라본다
* 개별 프로젝트 `pom.xml`에 저장소를 추가하기보다 `settings.xml` mirror를 우선 사용한다

## 3. 사전 준비

# 3. 사전 준비

## 3.1 Docker Desktop 설치

로컬 Nexus Repository는 Docker Container로 실행한다.

### 다운로드

- Docker Desktop for Windows 설치
- WSL2 기반 설치(권장)

### 설치 확인

```cmd
docker version
```

예시

```text
Client:
 Version: 28.x.x

Server:
 Engine:
  Version: 28.x.x
```

또는

```cmd
docker --version
```

### Docker 실행 확인

```cmd
docker ps
```

실행 결과

```text
CONTAINER ID   IMAGE   COMMAND   STATUS   PORTS   NAMES
```

컨테이너가 없어도 오류가 발생하지 않으면 정상이다.

### 참고 사항

- Windows 11 + WSL2 환경 권장
- Docker Desktop 실행 상태에서만 Nexus Container를 실행할 수 있다.

### 3.2 권장 환경

* Windows 11 + WSL2
* Docker Desktop 실행 상태

## 4. Nexus 실행

```cmd
docker run -d ^
  --name nexus ^
  -p 8081:8081 ^
  -v nexus-data:/nexus-data ^
  sonatype/nexus3
```

접속:

```text
http://localhost:8081
```

초기 비밀번호 확인:

```cmd
docker exec -it nexus cat /nexus-data/admin.password
```

## 5. Repository 구성

### 5.1 Proxy Repository

`maven-central`

```text
https://repo1.maven.org/maven2/
```

`egovframe-proxy`

* Type: `maven2(proxy)`
* Name: `egovframe-proxy`
* Remote Storage: `https://maven.egovframe.go.kr/maven/`

### 5.2 Hosted Repository

`maven-releases`

용도:

* Third-party library
* 사내 공통 library
* 중앙 저장소에 없는 vendor library

### 5.3 Group Repository

`maven-public`

Member:

```text
maven-releases
maven-snapshots
maven-central
egovframe-proxy
```

## 6. Maven 설정

사용자 설정 파일:

```text
%USERPROFILE%\.m2\settings.xml
```

예시:

```xml
<settings>
  <mirrors>
    <mirror>
      <id>local-nexus</id>
      <mirrorOf>*</mirrorOf>
      <url>http://localhost:8081/repository/maven-public/</url>
    </mirror>
  </mirrors>
</settings>
```

확인:

```cmd
mvn help:effective-settings
```

## 7. 저장소 검증

특정 artifact 다운로드 확인:

```cmd
mvn dependency:get ^
  -Dartifact=egovframework.rte:egovframework.rte.ptl.mvc:3.1.0
```

성공 로그 예시:

```text
Downloaded from local-nexus
```

## 8. Third-party library 관리

로컬 정리 디렉터리:

```text
nexus/
  thirdparty-libs/
```

배포 예시:

```cmd
mvn deploy:deploy-file ^
  -DgroupId=... ^
  -DartifactId=... ^
  -Dversion=... ^
  -Dpackaging=jar ^
  -Dfile=... ^
  -DpomFile=... ^
  -DrepositoryId=maven-releases ^
  -Durl=http://localhost:8081/repository/maven-releases/
```

## 9. 의존성 검증

### 9.1 사전 다운로드

```cmd
mvn clean dependency:go-offline
```

목적:

* 의존성 사전 다운로드
* Nexus cache 생성

### 9.2 일반 빌드 확인

```cmd
mvn clean compile
```

```cmd
mvn clean package
```

## 10. OpenRewrite 실행 기준

이번 샘플 검증에서 실제로 성공한 기준은 아래와 같다.

### 10.1 JDK

OpenRewrite 실행용 Maven은 `JDK 8` 기준으로 수행한다.

예시:

```powershell
$env:JAVA_HOME="C:\Program Files\Java\jdk1.8.0_491"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
java -version
mvn -version
```

### 10.2 실행 순서

권장 순서:

1. `dryRunNoFork`
2. `runNoFork`
3. `validate`
4. `dependency:tree`

샘플 명령:

```cmd
mvn -f samples/asis/hello-egov-board/pom.xml org.openrewrite.maven:rewrite-maven-plugin:6.11.0:dryRunNoFork -Drewrite.configLocation=../../../rules/phase1-openrewrite/pom/egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

```cmd
mvn -f samples/asis/hello-egov-board/pom.xml org.openrewrite.maven:rewrite-maven-plugin:6.11.0:runNoFork -Drewrite.configLocation=../../../rules/phase1-openrewrite/pom/egovframe-coordinates.yml -Drewrite.activeRecipes=egov.migration.phase1.pom.EgovframeCoordinates
```

```cmd
mvn -f samples/asis/hello-egov-board/pom.xml validate
```

```cmd
mvn -f samples/asis/hello-egov-board/pom.xml dependency:tree
```

### 10.3 운영 메모

* `rewrite:dryRun`, `rewrite:run`은 lifecycle 영향이 더 크므로 현재 기준에서는 `NoFork` 계열을 우선 사용한다
* 의존성 해석은 가능한 한 `pom.xml` 수정이 아니라 Nexus와 `settings.xml` mirror로 해결한다

## 11. 운영 권장 사항

* Maven 클라이언트는 `maven-public`만 사용
* Third-party library는 `maven-releases`에 관리
* Nexus와 `settings.xml`은 OpenRewrite 실행 환경의 일부로 같이 관리

## 12. 향후 개선 항목

* Third-party 자동 업로드 스크립트
* Nexus backup / restore 스크립트
* 누락 library 자동 탐지 보조 도구
