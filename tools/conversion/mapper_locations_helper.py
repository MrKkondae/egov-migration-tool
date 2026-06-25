from __future__ import annotations

import json
import re
from pathlib import Path


SQLMAP_RESOURCE_PATTERN = re.compile(
    r'<sqlMap\b[^>]*\bresource="([^"]+)"[^>]*(?:/?>.*?</sqlMap>|/>)',
    re.IGNORECASE | re.DOTALL,
)
MAPPER_PROPERTY_PATTERN = re.compile(
    r'(?P<indent>^[ \t]*)<property\s+name="(?:configLocations|mapperLocations)">.*?</property>',
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def collect_sqlmap_config_files(working_root: Path, db_type: str) -> list[Path]:
    config_root = working_root / "src" / "main" / "resources" / "egovframework" / "sqlmap" / "config" / db_type
    if not config_root.exists():
        return []
    return sorted(config_root.glob("*.xml"))


def extract_mapper_resources(config_text: str) -> list[str]:
    resources: list[str] = []
    seen: set[str] = set()

    for match in SQLMAP_RESOURCE_PATTERN.finditer(config_text):
        resource = match.group(1).strip()
        if resource and resource not in seen:
            seen.add(resource)
            resources.append(resource)

    return resources


def collect_mapper_resources(working_root: Path, db_type: str) -> tuple[list[Path], list[str]]:
    config_files = collect_sqlmap_config_files(working_root, db_type)
    resources: list[str] = []
    seen: set[str] = set()

    for config_file in config_files:
        for resource in extract_mapper_resources(read_text(config_file)):
            if resource not in seen:
                seen.add(resource)
                resources.append(resource)

    return config_files, resources


def build_mapper_locations_property(resources: list[str], indent: str) -> str:
    lines = [f'{indent}<property name="mapperLocations">', f"{indent}\t<list>"]
    for resource in resources:
        lines.append(f"{indent}\t\t<value>classpath:/{resource}</value>")
    lines.extend([f"{indent}\t</list>", f"{indent}</property>"])
    return "\n".join(lines)


def replace_mapper_locations_property(text: str, resources: list[str]) -> tuple[str, int]:
    if not resources:
        return text, 0

    def replace(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return build_mapper_locations_property(resources, indent)

    return MAPPER_PROPERTY_PATTERN.subn(replace, text, count=1)


def build_mapper_locations_payload(working_root: Path, db_type: str) -> dict[str, object]:
    config_files, resources = collect_mapper_resources(working_root, db_type)
    return {
        "db_type": db_type,
        "config_file_count": len(config_files),
        "config_files": [str(path.relative_to(working_root).as_posix()) for path in config_files],
        "mapper_resource_count": len(resources),
        "mapper_resources": resources,
    }


def payload_to_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
