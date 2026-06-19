# OpenRewrite용 1차 매핑표

openRewrite용 1차 매핑표 샘플.

| ID | 파일유형 | 변경 전 | 변경 후 | 처리방식 |
|---|---|---|---|---|
| OR-001 | pom.xml | egovframework.rte:egovframework.rte.fdl.cmmn | org.egovframe.rte:org.egovframe.rte.fdl.cmmn | dependency 좌표 변경 |
| OR-002 | pom.xml | egovframework.rte:egovframework.rte.fdl.idgnr | org.egovframe.rte:org.egovframe.rte.fdl.idgnr | dependency 좌표 변경 |
| OR-003 | pom.xml | egovframework.rte:egovframework.rte.fdl.logging | org.egovframe.rte:org.egovframe.rte.fdl.logging | dependency 좌표 변경 |
| OR-004 | pom.xml | egovframework.rte:egovframework.rte.fdl.property | org.egovframe.rte:org.egovframe.rte.fdl.property | dependency 좌표 변경 |
| OR-005 | pom.xml | egovframework.rte:egovframework.rte.psl.dataaccess | org.egovframe.rte:org.egovframe.rte.psl.dataaccess | dependency 좌표 변경 |
| OR-006 | pom.xml | egovframework.rte:egovframework.rte.ptl.mvc | org.egovframe.rte:org.egovframe.rte.ptl.mvc | dependency 좌표 변경 |
| OR-007 | pom.xml | org.codehaus.jackson:jackson-core-asl | com.fasterxml.jackson.core:jackson-core | dependency 좌표 변경 |
| OR-008 | pom.xml | org.codehaus.jackson:jackson-mapper-asl | com.fasterxml.jackson.core:jackson-databind | dependency 좌표 변경 |
| OR-009 | pom.xml | com.oracle:ojdbc14 | com.oracle.database.jdbc:ojdbc8 | dependency 좌표 변경 |
| OR-010 | pom.xml | ojdbc14 | com.oracle.database.jdbc:ojdbc8 | dependency 좌표 변경 |
| OR-011 | Java | org.codehaus.jackson.map.ObjectMapper | com.fasterxml.jackson.databind.ObjectMapper | import 변경 |
| OR-012 | Java | org.codehaus.jackson.JsonNode | com.fasterxml.jackson.databind.JsonNode | import 변경 |
| OR-013 | Java | org.codehaus.jackson.type.TypeReference | com.fasterxml.jackson.core.type.TypeReference | import 변경 |
| OR-014 | Java | org.codehaus.jackson.annotate.JsonIgnoreProperties | com.fasterxml.jackson.annotation.JsonIgnoreProperties | import 변경 |
| OR-015 | Java | egovframework.rte.psl.dataaccess.EgovAbstractDAO | egovframework.rte.psl.dataaccess.EgovAbstractMapper | import 변경 |
| OR-016 | Java | extends EgovAbstractDAO | extends EgovAbstractMapper | class 상속 변경 |
| OR-017 | Java | import egovframework.com.cmm.service.impl.EgovComAbstractDAO; | 제거 | import 제거 |
| OR-018 | Java | extends EgovComAbstractDAO | extends EgovAbstractMapper | class 상속 변경 |