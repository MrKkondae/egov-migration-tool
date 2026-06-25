from __future__ import annotations

import re
from pathlib import Path

from .models import TransformResult, rel_path


HASH_PARAM_PATTERN = re.compile(r"#([A-Za-z_]\w*)#")
DOLLAR_PARAM_PATTERN = re.compile(r"\$([A-Za-z_]\w*)\$")
SQLMAP_OPEN_PATTERN = re.compile(r"<sqlMap(\s[^>]*)?>", re.IGNORECASE)
SQLMAP_CLOSE_PATTERN = re.compile(r"</sqlMap>", re.IGNORECASE)
SQLMAP_DOCTYPE_PATTERN = re.compile(r'<!DOCTYPE\s+sqlMap\s+PUBLIC[^>]+>', re.IGNORECASE)
SQLMAPCONFIG_DOCTYPE_PATTERN = re.compile(r'<!DOCTYPE\s+sqlMapConfig\s+PUBLIC[^>]+>', re.IGNORECASE)
PARAMETER_CLASS_PATTERN = re.compile(r'(\sparameter)Class="([^"]+)"')
RESULT_CLASS_PATTERN = re.compile(r'(\sresult)Class="([^"]+)"')
RESULTMAP_CLASS_PATTERN = re.compile(r'(<resultMap\b[^>]*\s)class="([^"]+)"', re.IGNORECASE)
SQLMAPCONFIG_PATTERN = re.compile(r"<sqlMapConfig\b", re.IGNORECASE)
SQLMAP_RESOURCE_PATTERN = re.compile(
    r'<sqlMap\b[^>]*\bresource="([^"]+)"[^>]*(?:/?>.*?</sqlMap>|/>)',
    re.IGNORECASE | re.DOTALL,
)
IDENTIFIER_HASH_PATTERN = re.compile(
    r"(?im)(^\s*(?:SELECT|,)\s*)#([A-Za-z_]\w*)#(\s+[A-Za-z_][A-Za-z0-9_]*)"
)
ITERATE_BODY_HASH_PATTERN = re.compile(r"#([A-Za-z_]\w*)\[\]#")
ITERATE_BODY_DOLLAR_PATTERN = re.compile(r"\$([A-Za-z_]\w*)\[\]\$")
SET_PATTERN = re.compile(r"<set>(?P<body>.*?)</set>", re.IGNORECASE | re.DOTALL)
WHERE_PATTERN = re.compile(r"<where>(?P<body>.*?)</where>", re.IGNORECASE | re.DOTALL)
TRIM_AND_OR_PATTERN = re.compile(
    r'<trim\b(?P<attrs>[^>]*prefixOverrides="AND \|OR "[^>]*)>(?P<body>.*?)</trim>',
    re.IGNORECASE | re.DOTALL,
)
IF_BODY_PREFIX_PATTERN = re.compile(r"(<if\b[^>]*>)(?P<body>.*?)(</if>)", re.IGNORECASE | re.DOTALL)

CONDITIONAL_TAG_RULES = {
    "isEqual": ("==", True),
    "isNotEqual": ("!=", True),
    "isNull": ("== null", False),
    "isNotNull": ("!= null", False),
    "isEmpty": ("{prop} == null or {prop} == ''", False),
    "isNotEmpty": ("{prop} != null and {prop} != ''", False),
}


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def add_unique_warning(warnings: list[str], message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def normalize_compare_value(value: str) -> str:
    return f"'{value}'"


def apply_prepend_to_body(body: str, prepend: str) -> str:
    if not prepend:
        return body

    match = re.search(r"\S", body)
    if not match:
        return f"{prepend} "

    index = match.start()
    return f"{body[:index]}{prepend} {body[index:]}"


def strip_leading_and_or(text: str) -> tuple[str, int]:
    return re.subn(r"^(\s*)(AND|OR)\b\s*", r"\1", text, flags=re.IGNORECASE)


def strip_if_body_leading_and_or(text: str) -> tuple[str, int]:
    total_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total_count
        body = match.group("body")
        updated_body, count = strip_leading_and_or(body)
        total_count += count
        return f"{match.group(1)}{updated_body}{match.group(3)}"

    updated = IF_BODY_PREFIX_PATTERN.sub(replace, text)
    return updated, total_count


def build_test_expression(tag_name: str, prop: str, compare_value: str | None) -> str:
    operator_or_expr, uses_compare_value = CONDITIONAL_TAG_RULES[tag_name]
    if uses_compare_value:
        return f"{prop} {operator_or_expr} {normalize_compare_value(compare_value or '')}"
    return operator_or_expr.format(prop=prop)


def transform_conditional_blocks(text: str, warnings: list[str]) -> tuple[str, int]:
    updated = text
    total_count = 0

    for tag_name in CONDITIONAL_TAG_RULES:
        pattern = re.compile(
            rf"<{tag_name}\b(?P<attrs>[^>]*)>(?P<body>.*?)</{tag_name}>",
            re.IGNORECASE | re.DOTALL,
        )

        def replace(match: re.Match[str]) -> str:
            attrs = match.group("attrs")
            body = match.group("body")

            prop_match = re.search(r'property="([^"]+)"', attrs)
            prepend_match = re.search(r'prepend="([^"]+)"', attrs)
            compare_match = re.search(r'compareValue="([^"]+)"', attrs)

            if not prop_match:
                add_unique_warning(warnings, f"SQL Map: <{tag_name}> property 해석 실패로 수동 검토 필요")
                return match.group(0)

            prop = prop_match.group(1)
            prepend = prepend_match.group(1).strip() if prepend_match else ""
            compare_value = compare_match.group(1) if compare_match else None
            test_expr = build_test_expression(tag_name, prop, compare_value)
            transformed_body = apply_prepend_to_body(body, prepend)
            return f'<if test="{test_expr}">{transformed_body}</if>'

        updated, count = pattern.subn(replace, updated)
        total_count += count

    return updated, total_count


def transform_hash_identifier_usage(text: str, warnings: list[str]) -> tuple[str, int]:
    def replace(match: re.Match[str]) -> str:
        add_unique_warning(warnings, "SQL Map: 식별자 위치의 #파라미터#는 ${} 치환 후 수동 검토 필요")
        return f"{match.group(1)}${{{match.group(2)}}}{match.group(3)}"

    return IDENTIFIER_HASH_PATTERN.subn(replace, text)


def transform_iterate_blocks(text: str, warnings: list[str]) -> tuple[str, int]:
    pattern = re.compile(r"<iterate\b(?P<attrs>[^>]*)>(?P<body>.*?)</iterate>", re.IGNORECASE | re.DOTALL)

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        body = match.group("body")

        property_match = re.search(r'property="([^"]+)"', attrs)
        open_match = re.search(r'open="([^"]*)"', attrs)
        close_match = re.search(r'close="([^"]*)"', attrs)
        conjunction_match = re.search(r'conjunction="([^"]*)"', attrs)
        prepend_match = re.search(r'prepend="([^"]*)"', attrs)

        if not property_match:
            add_unique_warning(warnings, "SQL Map: <iterate> property 해석 실패로 수동 검토 필요")
            return match.group(0)

        collection = property_match.group(1)
        item_name = "item"
        open_value = open_match.group(1) if open_match else ""
        close_value = close_match.group(1) if close_match else ""
        separator_value = conjunction_match.group(1) if conjunction_match else ","
        prepend_value = prepend_match.group(1).strip() if prepend_match else ""

        transformed_body = body
        transformed_body, hash_count = ITERATE_BODY_HASH_PATTERN.subn(r"#{item}", transformed_body)
        transformed_body, dollar_count = ITERATE_BODY_DOLLAR_PATTERN.subn(r"${item}", transformed_body)

        if hash_count == 0 and dollar_count == 0:
            add_unique_warning(warnings, "SQL Map: <iterate> 내부 바인딩 패턴을 자동 해석하지 못해 수동 검토 필요")

        if dollar_count:
            add_unique_warning(warnings, "SQL Map: <iterate> 내부 ${} 치환은 SQL 조립 여부를 다시 검토해야 함")

        foreach_tag = (
            f'<foreach collection="{collection}" item="{item_name}"'
            f' open="{open_value}" close="{close_value}" separator="{separator_value}">{transformed_body}</foreach>'
        )
        return apply_prepend_to_body(foreach_tag, prepend_value)

    return pattern.subn(replace, text)


def build_dynamic_tag(prepend: str, body: str) -> tuple[str, str | None]:
    normalized = prepend.strip()
    upper = normalized.upper()

    if upper == "WHERE":
        return f"<where>{body}</where>", None
    if upper == "SET":
        return f"<set>{body}</set>", None
    if normalized:
        warning = None
        if upper not in {"AND", "OR"}:
            warning = f'SQL Map: <dynamic prepend="{normalized}"> 는 <trim>으로 변환되어 SQL 의미 검토 필요'
        return f'<trim prefix="{normalized}" prefixOverrides="AND |OR ">{body}</trim>', warning
    return f'<trim prefixOverrides="AND |OR ">{body}</trim>', None


def transform_dynamic_blocks(text: str, warnings: list[str]) -> tuple[str, int]:
    pattern = re.compile(r"<dynamic\b(?P<attrs>[^>]*)>(?P<body>.*?)</dynamic>", re.IGNORECASE | re.DOTALL)

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        body = match.group("body")

        prepend_match = re.search(r'prepend="([^"]*)"', attrs)
        prepend_value = prepend_match.group(1) if prepend_match else ""
        transformed, warning = build_dynamic_tag(prepend_value, body)
        if warning:
            add_unique_warning(warnings, warning)
        return transformed

    return pattern.subn(replace, text)


def is_simple_sqlmap_config(text: str) -> bool:
    if not SQLMAPCONFIG_PATTERN.search(text):
        return False

    stripped = SQLMAPCONFIG_DOCTYPE_PATTERN.sub("", text)
    stripped = re.sub(r"<\?xml[^>]*\?>", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"<!--.*?-->", "", stripped, flags=re.DOTALL)
    stripped = re.sub(r"</?sqlMapConfig\b[^>]*>", "", stripped, flags=re.IGNORECASE)
    stripped = SQLMAP_RESOURCE_PATTERN.sub("", stripped)
    stripped = re.sub(r"\s+", "", stripped)
    return stripped == ""


def cleanup_set_block(text: str) -> tuple[str, int]:
    total_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total_count
        body = match.group("body")
        body, count = strip_if_body_leading_and_or(body)
        total_count += count
        body, count = re.subn(r",(\s*</if>)", r"\1", body)
        total_count += count
        return f"<set>{body}</set>"

    updated = SET_PATTERN.sub(replace, text)
    return updated, total_count


def cleanup_where_block(text: str) -> tuple[str, int]:
    total_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total_count
        body = match.group("body")
        body, count = strip_leading_and_or(body)
        total_count += count
        return f"<where>{body}</where>"

    updated = WHERE_PATTERN.sub(replace, text)
    return updated, total_count


def cleanup_trim_and_or_block(text: str) -> tuple[str, int]:
    total_count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total_count
        attrs = match.group("attrs")
        body = match.group("body")
        body, count = strip_leading_and_or(body)
        total_count += count
        return f"<trim{attrs}>{body}</trim>"

    updated = TRIM_AND_OR_PATTERN.sub(replace, text)
    return updated, total_count


def cleanup_dynamic_sql_blocks(text: str) -> tuple[str, int]:
    total_count = 0

    text, count = cleanup_where_block(text)
    total_count += count

    text, count = cleanup_trim_and_or_block(text)
    total_count += count

    text, count = cleanup_set_block(text)
    total_count += count

    return text, total_count


def transform_sqlmap_file_content(text: str, warnings: list[str]) -> tuple[str, int]:
    updated = text
    change_count = 0

    updated, count = transform_iterate_blocks(updated, warnings)
    change_count += count

    updated, count = transform_hash_identifier_usage(updated, warnings)
    change_count += count

    updated, count = HASH_PARAM_PATTERN.subn(r"#{\1}", updated)
    change_count += count

    updated, count = DOLLAR_PARAM_PATTERN.subn(r"${\1}", updated)
    change_count += count
    if count:
        add_unique_warning(warnings, "SQL Map: ${} 치환 구문은 SQL 조립 여부를 다시 검토해야 함")

    updated, count = PARAMETER_CLASS_PATTERN.subn(r'\1Type="\2"', updated)
    change_count += count

    updated, count = RESULT_CLASS_PATTERN.subn(r'\1Type="\2"', updated)
    change_count += count

    updated, count = RESULTMAP_CLASS_PATTERN.subn(r'\1type="\2"', updated)
    change_count += count

    updated, count = SQLMAP_OPEN_PATTERN.subn(r"<mapper\1>", updated)
    change_count += count

    updated, count = SQLMAP_CLOSE_PATTERN.subn(r"</mapper>", updated)
    change_count += count

    updated, count = SQLMAP_DOCTYPE_PATTERN.subn(
        '<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "https://mybatis.org/dtd/mybatis-3-mapper.dtd">',
        updated,
    )
    change_count += count

    updated, count = transform_conditional_blocks(updated, warnings)
    change_count += count

    updated, count = transform_dynamic_blocks(updated, warnings)
    change_count += count

    updated, count = cleanup_dynamic_sql_blocks(updated)
    change_count += count

    return updated, change_count


def transform_sqlmap_files(working_root: Path) -> list[TransformResult]:
    results: list[TransformResult] = []

    for path in sorted(working_root.rglob("*.xml")):
        original = read_text(path)
        updated = original
        change_count = 0
        warnings: list[str] = []

        if SQLMAPCONFIG_PATTERN.search(updated) and not is_simple_sqlmap_config(updated):
            add_unique_warning(warnings, "SQL Map Config: sqlMapConfig 파일은 mapperLocations 전환 후 별도 정리 필요")

        if (
            "<sqlMap" in updated
            or "<dynamic" in updated
            or "<iterate" in updated
            or "parameterClass=" in updated
            or "resultClass=" in updated
            or "<isEqual" in updated
            or "<isNotEqual" in updated
            or "<isNull" in updated
            or "<isNotNull" in updated
            or "<isEmpty" in updated
            or "<isNotEmpty" in updated
            or "$" in updated
            or "#" in updated
        ) and not SQLMAPCONFIG_PATTERN.search(updated):
            updated, change_count = transform_sqlmap_file_content(updated, warnings)

        if "<dynamic" in updated.lower():
            add_unique_warning(warnings, "SQL Map: <dynamic> 태그는 자동 변환되지 않아 수동 검토 필요")

        changed = updated != original
        if changed:
            path.write_text(updated, encoding="utf-8")

        results.append(
            TransformResult(
                path=rel_path(path, working_root),
                changed=changed,
                change_count=change_count,
                warnings=warnings,
            )
        )

    return results
