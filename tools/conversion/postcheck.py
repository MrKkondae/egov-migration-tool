from __future__ import annotations

import re
from pathlib import Path

from .transform_dao import find_extends_name, is_dao_candidate


GENERIC_POSTCHECK_PATTERNS: dict[str, tuple[re.Pattern[str], str]] = {
    "egov_abstract_dao": (
        re.compile(r"\bEgovAbstractDAO\b"),
        "기존 EgovAbstractDAO가 남아 있음",
    ),
    "sql_map_client_factory_bean": (
        re.compile(r"\bSqlMapClientFactoryBean\b"),
        "Spring iBatis FactoryBean이 남아 있음",
    ),
    "sql_map_client_template": (
        re.compile(r"\bSqlMapClientTemplate\b"),
        "Spring iBatis Template이 남아 있음",
    ),
    "ibatis_dynamic": (
        re.compile(r"<dynamic\b", re.IGNORECASE),
        "iBatis <dynamic> 태그가 남아 있음",
    ),
    "ibatis_is_not_empty": (
        re.compile(r"<isNotEmpty\b", re.IGNORECASE),
        "iBatis <isNotEmpty> 태그가 남아 있음",
    ),
    "ibatis_iterate": (
        re.compile(r"<iterate\b", re.IGNORECASE),
        "iBatis <iterate> 태그가 남아 있음",
    ),
    "ibatis_hash_param": (
        re.compile(r"#([A-Za-z_]\w*)#"),
        "iBatis #파라미터# 구문이 남아 있음",
    ),
}

DAO_LEGACY_API_PATTERNS: dict[str, re.Pattern[str]] = {
    "list": re.compile(r"\blist\s*\("),
    "select": re.compile(r"\bselect\s*\("),
}

DAO_MAPPER_BASES = {"EgovAbstractMapper", "EgovComAbstractDAO"}
XML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
JAVA_BLOCK_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
JAVA_LINE_COMMENT_PATTERN = re.compile(r"//.*?$", re.MULTILINE)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def strip_xml_comments(text: str) -> str:
    return XML_COMMENT_PATTERN.sub("", text)


def strip_java_comments(text: str) -> str:
    text = JAVA_BLOCK_COMMENT_PATTERN.sub("", text)
    return JAVA_LINE_COMMENT_PATTERN.sub("", text)


def normalize_for_postcheck(path: Path, text: str) -> str:
    if path.suffix.lower() == ".xml":
        return strip_xml_comments(text)
    if path.suffix.lower() == ".java":
        return strip_java_comments(text)
    return text


def collect_generic_postcheck_warnings(path: Path, working_root: Path, text: str) -> list[str]:
    warnings: list[str] = []
    rel = path.relative_to(working_root).as_posix()

    for _, (pattern, message) in GENERIC_POSTCHECK_PATTERNS.items():
        if pattern.search(text):
            warnings.append(f"{rel}: {message}")

    return warnings


def collect_dao_postcheck_warnings(path: Path, working_root: Path, raw_text: str, normalized_text: str) -> list[str]:
    if not is_dao_candidate(path, raw_text):
        return []

    extends_name = find_extends_name(raw_text)
    if extends_name not in DAO_MAPPER_BASES:
        return []

    warnings: list[str] = []
    rel = path.relative_to(working_root).as_posix()

    for api_name, pattern in DAO_LEGACY_API_PATTERNS.items():
        match_count = len(pattern.findall(normalized_text))
        if match_count:
            warnings.append(f"{rel}: Mapper 기반 DAO에 기존 {api_name}() 호출 {match_count}건이 남아 있음")

    return warnings


def collect_postcheck_warnings(working_root: Path) -> list[str]:
    warnings: list[str] = []

    for path in sorted(working_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".java", ".xml"}:
            continue

        raw_text = read_text(path)
        normalized_text = normalize_for_postcheck(path, raw_text)
        warnings.extend(collect_generic_postcheck_warnings(path, working_root, normalized_text))

        if path.suffix.lower() == ".java":
            warnings.extend(collect_dao_postcheck_warnings(path, working_root, raw_text, normalized_text))

    return warnings
