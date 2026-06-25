from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .mapper_locations_helper import collect_mapper_resources, replace_mapper_locations_property
from .models import TransformResult, rel_path


SPRING_SQLMAP_FACTORY = "org.springframework.orm.ibatis.SqlMapClientFactoryBean"
MYBATIS_SQLSESSION_FACTORY = "org.mybatis.spring.SqlSessionFactoryBean"


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def transform_sqlmap_factory_bean(text: str) -> tuple[str, int, list[str]]:
    updated = text
    change_count = 0
    warnings: list[str] = []

    if SPRING_SQLMAP_FACTORY in updated:
        updated = updated.replace(SPRING_SQLMAP_FACTORY, MYBATIS_SQLSESSION_FACTORY)
        change_count += 1

    config_locations_pattern = re.compile(r'(<property\s+name=")configLocations(")')
    updated, count = config_locations_pattern.subn(r"\1mapperLocations\2", updated)
    change_count += count

    if 'name="lobHandler"' in updated:
        warnings.append("Spring XML: lobHandler 연결은 MyBatis 적용 적합성 별도 검토 필요")

    return updated, change_count, warnings


def has_sqlmap_config_mapper_location(text: str) -> bool:
    return "mapperLocations" in text and "/sqlmap/config/" in text


def expand_mapper_locations(text: str, working_root: Path, db_type: str | None) -> tuple[str, int, list[str]]:
    if not db_type or not has_sqlmap_config_mapper_location(text):
        return text, 0, []

    _, resources = collect_mapper_resources(working_root, db_type)
    if not resources:
        return text, 0, [f"Spring XML: dbType `{db_type}` 기준 mapperLocations 전개 대상을 찾지 못함"]

    updated, count = replace_mapper_locations_property(text, resources)
    if count == 0:
        return text, 0, [f"Spring XML: dbType `{db_type}` 기준 mapperLocations 전개 대상 property를 찾지 못함"]

    return updated, count, []


def build_sqlmapclient_target_sets(payload: dict[str, Any] | None) -> tuple[set[str], set[str], set[str]]:
    automatic: set[str] = set()
    conditional: set[str] = set()
    manual: set[str] = set()

    if not payload:
        return automatic, conditional, manual

    for item in payload.get("automatic", []):
        if item.get("type") == "xml" and item.get("file"):
            automatic.add(item["file"])
    for item in payload.get("conditional", []):
        if item.get("type") == "xml" and item.get("file"):
            conditional.add(item["file"])
    for item in payload.get("manual", []):
        if item.get("type") == "xml" and item.get("file"):
            manual.add(item["file"])

    return automatic, conditional, manual


def transform_spring_xml_files(
    working_root: Path,
    sqlmapclient_targets: dict[str, Any] | None = None,
    db_type: str | None = None,
) -> list[TransformResult]:
    results: list[TransformResult] = []
    automatic_files, conditional_files, manual_files = build_sqlmapclient_target_sets(sqlmapclient_targets)

    for path in sorted(working_root.rglob("*.xml")):
        rel = rel_path(path, working_root)
        text = read_text(path)
        updated = text
        change_count = 0
        warnings: list[str] = []

        if SPRING_SQLMAP_FACTORY in updated:
            if not sqlmapclient_targets or rel in automatic_files:
                updated, factory_change_count, factory_warnings = transform_sqlmap_factory_bean(updated)
                change_count += factory_change_count
                warnings.extend(factory_warnings)
            else:
                warnings.append("Spring XML: sqlMapClient 분류 결과상 자동 변환 대상이 아니므로 변경 보류")

        updated, mapper_change_count, mapper_warnings = expand_mapper_locations(updated, working_root, db_type)
        change_count += mapper_change_count
        warnings.extend(mapper_warnings)

        if has_sqlmap_config_mapper_location(updated):
            warnings.append("Spring XML: mapperLocations가 sqlMapConfig 경로를 참조하므로 실제 mapper XML 목록으로 전개 필요")

        if 'name="sqlMapClient"' in updated or 'ref="egov.sqlMapClient"' in updated:
            if rel in conditional_files:
                warnings.append("Spring XML: 조건부 자동 변환 대상이므로 bean/property 구조 확인 후 후속 규칙 검토")
            elif rel in manual_files:
                warnings.append("Spring XML: 수동 검토 대상으로 분류되어 bean/property 치환은 보류")
            else:
                warnings.append("Spring XML: sqlMapClient 참조가 남아 있어 후속 bean/property 정리 필요")

        if "DefaultBeanValidator" in updated:
            warnings.append("Validation bean detected: Bean Validation migration should be reviewed separately")

        changed = updated != text
        if changed:
            path.write_text(updated, encoding="utf-8")

        if changed or warnings:
            results.append(
                TransformResult(
                    path=rel,
                    changed=changed,
                    change_count=change_count,
                    warnings=warnings,
                )
            )

    return results
