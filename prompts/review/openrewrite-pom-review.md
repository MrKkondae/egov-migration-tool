이 OpenRewrite recipe는 전자정부프레임워크 3.1 프로젝트의 pom.xml 의존성을 eGovFrame 4.3 기준으로 변경하기 위한 초안이다.

검토 관점:
1. OpenRewrite YAML 문법 오류 여부
2. org.openrewrite.maven.* recipe 사용 방식 적절성
3. ChangeDependency / AddDependency / RemoveDependency 사용 구분 적절성
4. Maven dependencyManagement와 일반 dependencies 적용 시 문제 여부
5. 실제 적용 시 위험한 규칙 여부
6. eGovFrame 4.3 전환 기준에서 누락된 주요 의존성 여부

OpenRewrite Maven Plugin 6.11 기준으로 YAML 문법과 recipe 호환성을 검토해줘.