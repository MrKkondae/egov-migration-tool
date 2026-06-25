from __future__ import annotations

import re
from pathlib import Path

from .models import TransformResult, rel_path


DAO_BASE_CLASSES = {"EgovAbstractDAO", "EgovComAbstractDAO"}
DAO_MAPPER_BASE_CLASSES = {"EgovAbstractDAO", "EgovComAbstractDAO", "EgovAbstractMapper"}
IBATIS_DIRECT_USAGE_TOKENS = {
    "SqlMapClient",
    "sqlMapClient",
    "SqlMapClientTemplate",
    "getSqlMapClientTemplate",
    "setSuperSqlMapClient",
    "com.ibatis",
}
DAO_API_REPLACEMENTS: dict[str, tuple[re.Pattern[str], str]] = {
    "list_to_selectList": (re.compile(r"\blist\s*\("), "selectList("),
    "select_to_selectOne": (re.compile(r"\bselect\s*\("), "selectOne("),
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def find_class_name(text: str) -> str:
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_]\w*)", text)
    return match.group(1) if match else ""


def find_extends_name(text: str) -> str:
    match = re.search(
        r"\b(?:class|interface|enum)\s+[A-Za-z_]\w*(?:\s*<[^>{}]+>)?\s+extends\s+([A-Za-z_][\w.]*)",
        text,
    )
    return match.group(1) if match else ""


def is_dao_candidate(path: Path, text: str) -> bool:
    class_name = find_class_name(text)
    extends_name = find_extends_name(text)
    return path.name.endswith("DAO.java") or class_name.endswith(("DAO", "Dao")) or extends_name in DAO_BASE_CLASSES


def is_common_dao_wrapper(text: str) -> bool:
    return find_class_name(text) == "EgovComAbstractDAO"


def has_direct_ibatis_usage(text: str) -> bool:
    return any(token in text for token in IBATIS_DIRECT_USAGE_TOKENS)


def replace_once(text: str, before: str, after: str) -> tuple[str, int]:
    if before not in text:
        return text, 0
    return text.replace(before, after, 1), 1


def remove_pattern(text: str, pattern: str) -> tuple[str, int]:
    updated, count = re.subn(pattern, "", text, flags=re.MULTILINE | re.DOTALL)
    return updated, count


def cleanup_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def transform_common_dao_wrapper(text: str) -> tuple[str, int, list[str]]:
    updated = text
    change_count = 0
    warnings: list[str] = []

    updated, count = replace_once(
        updated,
        "import egovframework.rte.psl.dataaccess.EgovAbstractDAO;",
        "import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper;",
    )
    change_count += count

    updated, count = replace_once(updated, "extends EgovAbstractDAO", "extends EgovAbstractMapper")
    change_count += count

    for import_line in (
        "import javax.annotation.Resource;\n",
        "import com.ibatis.sqlmap.client.SqlMapClient;\n",
    ):
        if import_line in updated:
            updated = updated.replace(import_line, "")
            change_count += 1

    method_pattern = (
        r"\n\s*@Resource\s*\(\s*name\s*=\s*\"egov\.sqlMapClient\"\s*\)\s*"
        r"public\s+void\s+setSuperSqlMapClient\s*\(\s*SqlMapClient\s+\w+\s*\)\s*\{.*?\n\s*\}\s*\n"
    )
    updated, count = remove_pattern(updated, method_pattern)
    change_count += count

    if "SqlMapClient" in updated or "setSuperSqlMapClient" in updated:
        warnings.append("공통 DAO wrapper 클래스: iBatis 초기화 코드가 일부 남아 있어 수동 검토 필요")

    return cleanup_blank_lines(updated), change_count, warnings


def transform_direct_egov_abstract_dao(text: str) -> tuple[str, int, list[str]]:
    updated = text
    change_count = 0
    warnings: list[str] = []

    updated, count = replace_once(
        updated,
        "import egovframework.rte.psl.dataaccess.EgovAbstractDAO;",
        "import org.egovframe.rte.psl.dataaccess.EgovAbstractMapper;",
    )
    change_count += count

    updated, count = replace_once(updated, "extends EgovAbstractDAO", "extends EgovAbstractMapper")
    change_count += count

    if "extends EgovAbstractDAO" in updated:
        warnings.append("기본 eGov DAO 상속 DAO: extends 변경이 일부 남아 있어 수동 검토 필요")

    return cleanup_blank_lines(updated), change_count, warnings


def transform_mapper_api_calls(text: str) -> tuple[str, int, list[str]]:
    updated = text
    change_count = 0
    warnings: list[str] = []

    for _, (pattern, replacement) in DAO_API_REPLACEMENTS.items():
        updated, count = pattern.subn(replacement, updated)
        change_count += count

    if re.search(r"\blist\s*\(", updated):
        warnings.append("DAO 메서드 호출 치환 이후에도 list()가 남아 있어 수동 검토 필요")
    if re.search(r"\bselect\s*\(", updated):
        warnings.append("DAO 메서드 호출 치환 이후에도 select()가 남아 있어 수동 검토 필요")

    return updated, change_count, warnings


def transform_dao_files(working_root: Path) -> list[TransformResult]:
    results: list[TransformResult] = []
    for path in sorted(working_root.rglob("*.java")):
        text = read_text(path)
        if not is_dao_candidate(path, text):
            continue

        updated = text
        change_count = 0
        warnings: list[str] = []
        class_name = find_class_name(text)
        extends_name = find_extends_name(text)
        wrapper_class = is_common_dao_wrapper(text)
        direct_ibatis_usage = has_direct_ibatis_usage(text)

        if wrapper_class:
            updated, wrapper_change_count, wrapper_warnings = transform_common_dao_wrapper(updated)
            change_count += wrapper_change_count
            warnings.extend(wrapper_warnings)
        elif extends_name == "EgovComAbstractDAO":
            pass
        elif extends_name == "EgovAbstractDAO":
            updated, dao_change_count, dao_warnings = transform_direct_egov_abstract_dao(updated)
            change_count += dao_change_count
            warnings.extend(dao_warnings)

        effective_extends_name = find_extends_name(updated)
        if not wrapper_class and effective_extends_name in DAO_MAPPER_BASE_CLASSES:
            updated, api_change_count, api_warnings = transform_mapper_api_calls(updated)
            change_count += api_change_count
            warnings.extend(api_warnings)

        if direct_ibatis_usage and wrapper_class:
            if "SqlMapClient" in updated or "setSuperSqlMapClient" in updated:
                warnings.append("공통 DAO wrapper 클래스: 기존 iBatis 초기화 코드 제거가 완전하지 않아 하위 DAO 확인 필요")
        elif direct_ibatis_usage:
            warnings.append("iBatis 직접 사용 DAO: 공통 wrapper 변환 외에 개별 수정 필요")

        if updated != text or warnings:
            changed = updated != text
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
