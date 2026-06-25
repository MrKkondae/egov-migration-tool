# MapperLocations Helper

`sqlMapConfig` 기반 iBatis 설정을 MyBatis `mapperLocations` 목록으로 펼칠 때 쓰는 보조기입니다.

## 목적

다음과 같은 Spring 설정은 바로 MyBatis에 맞지 않습니다.

```xml
<property name="configLocations">
    <list>
        <value>classpath:/egovframework/sqlmap/config/${Globals.DbType}/*.xml</value>
    </list>
</property>
```

이 경우 실제로는 `sqlmap/config/<dbType>/*.xml` 안의 `<sqlMap resource="..."/>` 목록을 읽어서
`mapperLocations`에 실제 mapper XML 경로를 넣어줘야 합니다.

## 지원 방식

1. `run_phase2`에 `--db-type`을 넘겨 자동 전개
2. `expand_mapper_locations.py`를 독립 실행해서 JSON 생성 또는 Spring XML 직접 반영

## run_phase2 예시

```bash
python -m tools.conversion.run_phase2 ^
  --source-root samples/asis/hello-egov-board ^
  --working-root tmp/phase2-mapper-helper ^
  --report-root output/reports/phase2-mapper-helper ^
  --copy-source ^
  --db-type mysql
```

## 독립 실행 예시

JSON만 생성:

```bash
python -m tools.conversion.expand_mapper_locations ^
  --source-root samples/asis/hello-egov-board ^
  --db-type mysql ^
  --output-json output/reports/mapper-locations-mysql.json
```

Spring XML 직접 반영:

```bash
python -m tools.conversion.expand_mapper_locations ^
  --source-root tmp/phase2-mapper-helper ^
  --db-type mysql ^
  --spring-xml tmp/phase2-mapper-helper/src/main/resources/egovframework/spring/com/context-sqlMap.xml ^
  --apply
```

## 출력 JSON

- `db_type`
- `config_file_count`
- `config_files`
- `mapper_resource_count`
- `mapper_resources`

## 주의

- `db-type`은 실제 운영 대상 DB 벤더와 맞아야 합니다.
- 여러 DB용 mapper를 한꺼번에 섞어 넣으면 statement 충돌 위험이 있으므로 자동 전개는 반드시 단일 `db-type` 기준으로만 수행합니다.
