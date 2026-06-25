from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("samples/asis")
DEFAULT_OUTPUT = Path("output/reports/dao-pattern-analysis.md")
DEFAULT_JSON_OUTPUT = Path("output/reports/dao-pattern-analysis.json")

JAVA_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "throw",
    "throws",
    "try",
    "else",
    "do",
    "synchronized",
    "this",
    "super",
}

DAO_API_SUSPECTS = {
    "list",
    "select",
    "selectList",
    "selectOne",
    "insert",
    "update",
    "delete",
    "queryForList",
    "queryForObject",
    "queryForMap",
    "queryForInt",
    "queryForLong",
}

IMPORT_GROUP_PATTERNS = {
    "egov_imports": lambda text: "egovframework" in text,
    "egovframe_imports": lambda text: "org.egovframe" in text,
    "ibatis_imports": lambda text: "ibatis" in text.lower(),
    "mybatis_imports": lambda text: "mybatis" in text.lower(),
    "sqlmap_imports": lambda text: "sqlmap" in text.lower(),
    "dataaccess_imports": lambda text: "dataaccess" in text.lower(),
    "dao_imports": lambda text: "dao" in text.lower(),
    "mapper_imports": lambda text: "mapper" in text.lower(),
}

SPECIAL_PATTERN_RULES = {
    '@SuppressWarnings("unchecked")': lambda content: '@SuppressWarnings("unchecked")' in content,
    "SqlMapClient": lambda content: "SqlMapClient" in content,
    "sqlMapClient": lambda content: "sqlMapClient" in content,
    "SqlSession": lambda content: "SqlSession" in content,
    "sqlSession": lambda content: "sqlSession" in content,
    "getSqlMapClientTemplate": lambda content: "getSqlMapClientTemplate" in content,
    "getSqlSession": lambda content: "getSqlSession" in content,
    "$ 문자열 포함": lambda content: "$" in content,
    "# 문자열 포함": lambda content: "#" in content,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect AS-IS DAO patterns from Java sources.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Directory to scan for Java files.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown report output path.")
    parser.add_argument(
        "--json-output",
        default=str(DEFAULT_JSON_OUTPUT),
        help="JSON report output path.",
    )
    return parser.parse_args()


def find_java_files(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.rglob("*.java") if path.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relative_path(path: Path, source_dir: Path) -> str:
    return path.relative_to(source_dir).as_posix()


def strip_comments(content: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return re.sub(r"//.*", "", without_block)


def find_package_name(content: str) -> str:
    match = re.search(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", content, re.MULTILINE)
    return match.group(1) if match else ""


def find_class_name(content: str) -> str:
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_]\w*)", content)
    return match.group(1) if match else ""


def find_annotations(content: str) -> list[str]:
    return sorted(set(re.findall(r"(?m)^[ \t]*@([A-Za-z_]\w*)\b", content)))


def find_extends_name(content: str) -> str:
    match = re.search(
        r"\b(?:class|interface|enum)\s+[A-Za-z_]\w*(?:\s*<[^>{}]+>)?\s+extends\s+([A-Za-z_][\w.]*)",
        content,
    )
    return match.group(1) if match else ""


def find_implements_names(content: str) -> list[str]:
    match = re.search(r"\bclass\s+[A-Za-z_]\w*(?:\s*<[^>{}]+>)?(?:\s+extends\s+[A-Za-z_][\w.]*)?\s+implements\s+([^{]+)", content)
    if not match:
        return []
    raw_items = match.group(1).split(",")
    return [item.strip() for item in raw_items if item.strip()]


def find_imports(content: str) -> list[str]:
    return re.findall(r"^\s*import\s+([A-Za-z0-9_.*]+)\s*;", content, re.MULTILINE)


def collect_import_groups(imports: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {key: [] for key in IMPORT_GROUP_PATTERNS}
    for item in imports:
        for key, matcher in IMPORT_GROUP_PATTERNS.items():
            if matcher(item):
                grouped[key].append(item)
    return {key: sorted(set(values)) for key, values in grouped.items()}


def collect_method_calls(content: str) -> Counter:
    counter: Counter[str] = Counter()
    for match in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", content):
        name = match.group(1)
        if name in JAVA_KEYWORDS:
            continue
        counter[name] += 1
    return counter


def collect_call_samples(content: str, method_names: set[str]) -> dict[str, list[str]]:
    samples: dict[str, list[str]] = {name: [] for name in sorted(method_names)}
    if not method_names:
        return samples

    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for name in method_names:
            if len(samples[name]) >= 5:
                continue
            if re.search(rf"\b{name}\s*\(", line):
                samples[name].append(stripped)
    return {name: values for name, values in samples.items() if values}


def collect_return_value_patterns(content: str) -> tuple[list[dict[str, str]], Counter]:
    samples: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        return_match = re.search(r"\breturn\s+([A-Za-z_]\w*)\s*\(", line)
        if return_match:
            method_name = return_match.group(1)
            label = "return DAO API 호출" if method_name in DAO_API_SUSPECTS else "return 메서드호출"
            counts[label] += 1
            samples.append({"pattern": label, "method": method_name, "line": line})

        assign_match = re.search(r"\b[A-Za-z_][\w<>\[\], ?]*\s+[A-Za-z_]\w*\s*=\s*([A-Za-z_]\w*)\s*\(", line)
        if assign_match:
            method_name = assign_match.group(1)
            label = "변수 = DAO API 호출" if method_name in DAO_API_SUSPECTS else "변수 = 메서드호출"
            counts[label] += 1
            samples.append({"pattern": label, "method": method_name, "line": line})

    return samples[:20], counts


def analyze_java_file(path: Path, source_dir: Path) -> dict:
    content = read_text(path)
    structural_content = strip_comments(content)
    imports = find_imports(structural_content)
    method_calls = collect_method_calls(content)
    suspect_methods = {name for name in method_calls if name in DAO_API_SUSPECTS}
    return_samples, return_pattern_counts = collect_return_value_patterns(content)

    result = {
        "file": relative_path(path, source_dir),
        "package": find_package_name(structural_content),
        "class_name": find_class_name(structural_content),
        "annotations": find_annotations(structural_content),
        "extends": find_extends_name(structural_content),
        "implements": find_implements_names(structural_content),
        "imports": imports,
        "import_groups": collect_import_groups(imports),
        "method_calls": method_calls,
        "suspect_api_calls": Counter({name: count for name, count in method_calls.items() if name in DAO_API_SUSPECTS}),
        "call_samples": collect_call_samples(content, suspect_methods),
        "return_value_samples": return_samples,
        "return_value_pattern_counts": return_pattern_counts,
        "special_patterns": {
            label: checker(content) for label, checker in SPECIAL_PATTERN_RULES.items()
        },
        "repository_used": "Repository" in find_annotations(structural_content),
        "dao_candidate": False,
    }
    result["dao_candidate"] = is_dao_candidate(result)
    return result


def is_dao_candidate(result: dict) -> bool:
    class_name = result.get("class_name", "")
    extends_name = result.get("extends", "")
    annotations = result.get("annotations", [])
    imports = result.get("imports", [])
    suspect_api_calls = result.get("suspect_api_calls", Counter())

    import_text = "\n".join(imports).lower()
    extends_lower = extends_name.lower()

    class_is_dao = class_name.endswith(("DAO", "Dao"))
    repository_used = "Repository" in annotations

    extends_dao_base = any(
        token in extends_name
        for token in [
            "EgovAbstractDAO",
            "EgovComAbstractDAO",
            "EgovAbstractMapper",
        ]
    )

    import_dao_base = any(
        token in import_text
        for token in [
            "egovabstractdao",
            "egovcomabstractdao",
            "egovabstractmapper",
            "dataaccess",
        ]
    )

    uses_dao_api = any(
        name in suspect_api_calls and suspect_api_calls[name] > 0
        for name in DAO_API_SUSPECTS
    )

    # DAO 전용 분석 기준:
    # 단순히 extends가 있다고 DAO로 보지 않는다.
    # ServiceImpl, VO, Controller, Interceptor, Util 등은 제외한다.
    return any(
        [
            class_is_dao,
            repository_used,
            extends_dao_base,
            import_dao_base and uses_dao_api,
            class_is_dao and uses_dao_api,
        ]
    )


def summarize_patterns(results: list[dict]) -> dict:
    dao_results = [item for item in results if item["dao_candidate"]]

    extends_counter: Counter[str] = Counter()
    implements_counter: Counter[str] = Counter()
    annotation_counter: Counter[str] = Counter()
    egov_import_counter: Counter[str] = Counter()
    sql_import_counter: Counter[str] = Counter()
    dao_import_counter: Counter[str] = Counter()
    method_counter: Counter[str] = Counter()
    method_file_counter: Counter[str] = Counter()
    suspect_counter: Counter[str] = Counter()
    suspect_file_counter: Counter[str] = Counter()
    return_value_pattern_counter: Counter[str] = Counter()
    special_pattern_file_counter: Counter[str] = Counter()
    call_samples: dict[str, list[str]] = defaultdict(list)
    return_value_samples: list[dict[str, str]] = []

    for item in dao_results:
        extends_counter[item["extends"] or "없음"] += 1

        if item["implements"]:
            for impl in item["implements"]:
                implements_counter[impl] += 1
        else:
            implements_counter["없음"] += 1

        for annotation in item["annotations"]:
            annotation_counter[f"@{annotation}"] += 1

        for import_name in item["imports"]:
            lowered = import_name.lower()
            if "egovframework" in import_name or "org.egovframe" in import_name:
                egov_import_counter[import_name] += 1
            if any(token in lowered for token in ("ibatis", "mybatis", "sqlmap")):
                sql_import_counter[import_name] += 1
            if any(token in lowered for token in ("dao", "mapper", "dataaccess")):
                dao_import_counter[import_name] += 1

        method_counter.update(item["method_calls"])
        for method_name in item["method_calls"]:
            method_file_counter[method_name] += 1

        suspect_counter.update(item["suspect_api_calls"])
        for method_name in item["suspect_api_calls"]:
            suspect_file_counter[method_name] += 1

        return_value_pattern_counter.update(item["return_value_pattern_counts"])
        for sample in item["return_value_samples"]:
            if len(return_value_samples) < 20:
                return_value_samples.append(sample)

        for label, used in item["special_patterns"].items():
            if used:
                special_pattern_file_counter[label] += 1

        for method_name, samples in item["call_samples"].items():
            for sample in samples:
                if len(call_samples[method_name]) < 5 and sample not in call_samples[method_name]:
                    call_samples[method_name].append(sample)

    summary = {
        "total_java_files": len(results),
        "dao_candidates": len(dao_results),
        "extends_used_dao": sum(1 for item in dao_results if item["extends"]),
        "implements_used_dao": sum(1 for item in dao_results if item["implements"]),
        "repository_used_dao": sum(1 for item in dao_results if item["repository_used"]),
        "egov_import_used_dao": sum(
            1
            for item in dao_results
            if item["import_groups"]["egov_imports"] or item["import_groups"]["egovframe_imports"]
        ),
        "ibatis_import_used_dao": sum(1 for item in dao_results if item["import_groups"]["ibatis_imports"]),
        "mybatis_import_used_dao": sum(1 for item in dao_results if item["import_groups"]["mybatis_imports"]),
        "sql_map_client_used_dao": sum(
            1
            for item in dao_results
            if item["special_patterns"]["SqlMapClient"] or item["special_patterns"]["sqlMapClient"]
        ),
        "sql_session_used_dao": sum(
            1
            for item in dao_results
            if item["special_patterns"]["SqlSession"] or item["special_patterns"]["sqlSession"]
        ),
        "suppress_warnings_used_dao": sum(
            1 for item in dao_results if item["special_patterns"]['@SuppressWarnings("unchecked")']
        ),
        "extends_counter": extends_counter,
        "implements_counter": implements_counter,
        "annotation_counter": annotation_counter,
        "egov_import_counter": egov_import_counter,
        "sql_import_counter": sql_import_counter,
        "dao_import_counter": dao_import_counter,
        "method_counter": method_counter,
        "method_file_counter": method_file_counter,
        "suspect_counter": suspect_counter,
        "suspect_file_counter": suspect_file_counter,
        "call_samples": dict(call_samples),
        "return_value_pattern_counter": return_value_pattern_counter,
        "return_value_samples": return_value_samples,
        "special_pattern_file_counter": special_pattern_file_counter,
    }
    return summary


def render_table_rows(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["| 없음 | 0 |"]
    return [f"| {key} | {value} |" for key, value in counter.most_common()]


def generate_markdown_report(results: list[dict], summary: dict) -> str:
    dao_results = [item for item in results if item["dao_candidate"]]
    lines: list[str] = ["# DAO AS-IS 패턴 분석 보고서", ""]

    lines.extend(
        [
            "## 1. 분석 요약",
            "",
            "| 항목 | 건수 |",
            "|---|---:|",
            f"| 전체 Java 파일 | {summary['total_java_files']} |",
            f"| DAO 후보 파일 | {summary['dao_candidates']} |",
            f"| extends 사용 DAO | {summary['extends_used_dao']} |",
            f"| implements 사용 DAO | {summary['implements_used_dao']} |",
            f"| @Repository 사용 DAO | {summary['repository_used_dao']} |",
            f"| eGov 관련 import 사용 DAO | {summary['egov_import_used_dao']} |",
            f"| iBatis 관련 import 사용 DAO | {summary['ibatis_import_used_dao']} |",
            f"| MyBatis 관련 import 사용 DAO | {summary['mybatis_import_used_dao']} |",
            f"| SqlMapClient 문자열 포함 DAO | {summary['sql_map_client_used_dao']} |",
            f"| SqlSession 문자열 포함 DAO | {summary['sql_session_used_dao']} |",
            f'| @SuppressWarnings 사용 DAO | {summary["suppress_warnings_used_dao"]} |',
            "",
        ]
    )

    lines.extend(
        [
            "## 2. DAO 후보 파일 목록",
            "",
            "| 파일 | 클래스 | extends | implements | 주요 annotation |",
            "|---|---|---|---|---|",
        ]
    )
    if dao_results:
        for item in dao_results:
            annotations = ", ".join(f"@{name}" for name in item["annotations"]) if item["annotations"] else "없음"
            implements = ", ".join(item["implements"]) if item["implements"] else "없음"
            lines.append(
                f"| {item['file']} | {item['class_name'] or '없음'} | {item['extends'] or '없음'} | {implements} | {annotations} |"
            )
    else:
        lines.append("| 없음 | 없음 | 없음 | 없음 | 없음 |")
    lines.append("")

    lines.extend(["## 3. 상속 클래스 분포", "", "| extends 클래스 | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["extends_counter"]))
    lines.append("")

    lines.extend(["## 4. implements 분포", "", "| implements | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["implements_counter"]))
    lines.append("")

    lines.extend(["## 5. Annotation 분포", "", "| Annotation | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["annotation_counter"]))
    lines.append("")

    lines.extend(["## 6. DAO 관련 Import 분포", "", "### eGov / eGovFrame", "", "| Import | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["egov_import_counter"]))
    lines.append("")
    lines.extend(["### iBatis / MyBatis / SQL", "", "| Import | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["sql_import_counter"]))
    lines.append("")
    lines.extend(["### DAO / Mapper / DataAccess", "", "| Import | 건수 |", "|---|---:|"])
    lines.extend(render_table_rows(summary["dao_import_counter"]))
    lines.append("")

    lines.extend(["## 7. 메서드 호출 패턴 Top 30", "", "| 메서드명 | 호출 건수 | 사용 파일 수 |", "|---|---:|---:|"])
    top_methods = summary["method_counter"].most_common(30)
    if top_methods:
        for method_name, count in top_methods:
            lines.append(f"| {method_name} | {count} | {summary['method_file_counter'][method_name]} |")
    else:
        lines.append("| 없음 | 0 | 0 |")
    lines.append("")

    lines.extend(["## 8. DAO API 의심 호출 패턴", "", "| 호출명 | 호출 건수 | 사용 파일 수 |", "|---|---:|---:|"])
    suspect_methods = summary["suspect_counter"].most_common()
    if suspect_methods:
        for method_name, count in suspect_methods:
            lines.append(f"| {method_name} | {count} | {summary['suspect_file_counter'][method_name]} |")
    else:
        lines.append("| 없음 | 0 | 0 |")
    lines.append("")

    lines.extend(["## 9. DAO API 호출 샘플", ""])
    if summary["call_samples"]:
        for method_name in sorted(summary["call_samples"]):
            lines.append(f"### {method_name}")
            lines.append("")
            for sample in summary["call_samples"][method_name]:
                lines.append(f"- `{sample}`")
            lines.append("")
    else:
        lines.append("없음")
        lines.append("")

    lines.extend(["## 10. 반환값 사용 패턴", "", "| 패턴 | 건수 |", "|---|---:|"])
    if summary["return_value_pattern_counter"]:
        for pattern, count in summary["return_value_pattern_counter"].most_common():
            lines.append(f"| {pattern} | {count} |")
    else:
        lines.append("| 없음 | 0 |")
    lines.append("")
    lines.append("### 반환값 사용 샘플")
    lines.append("")
    if summary["return_value_samples"]:
        for sample in summary["return_value_samples"][:20]:
            lines.append(f"- `{sample['line']}`")
    else:
        lines.append("없음")
    lines.append("")

    lines.extend(["## 11. 특이 패턴", "", "| 패턴 | 사용 파일 수 |", "|---|---:|"])
    if summary["special_pattern_file_counter"]:
        for pattern, count in summary["special_pattern_file_counter"].most_common():
            lines.append(f"| {pattern} | {count} |")
    else:
        lines.append("| 없음 | 0 |")
    lines.append("")

    lines.extend(
        [
            "## 12. 전환룰 후보 검토 포인트",
            "",
            "아래 내용은 확정 전환룰이 아니라 AS-IS 분석 결과 기반의 검토 포인트이다.",
            "",
            "- 반복적으로 등장하는 extends 클래스는 DAO 상속 전환룰 후보이다.",
            "- 반복적으로 등장하는 DAO API 호출은 메서드 전환룰 후보이다.",
            "- 특정 import가 반복적으로 등장하면 dependency/import 전환룰 후보이다.",
            "- 반환값을 사용하는 DAO API 호출은 자동변환 전 수동 검토 후보이다.",
            "- SqlMapClient / sqlMapClient / getSqlMapClientTemplate 사용은 iBatis 기반 DAO 전환룰 후보이다.",
            "- 프로젝트 자체 BaseDAO / AbstractDAO가 발견되면 별도 전환룰 검토가 필요하다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(output_path: Path, markdown: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")


def normalize_json_value(value: Any) -> Any:
    if isinstance(value, Counter):
        return dict(value)
    if isinstance(value, defaultdict):
        return {key: normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {key: normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_json_value(item) for item in value]
    return value


def build_json_report(source_dir: Path, results: list[dict], summary: dict) -> dict[str, Any]:
    dao_results = [item for item in results if item["dao_candidate"]]
    return {
        "source": str(source_dir),
        "analyzed_file_count": len(results),
        "dao_candidate_count": len(dao_results),
        "summary": normalize_json_value(summary),
        "dao_candidates": [normalize_json_value(item) for item in dao_results],
    }


def write_json_report(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    json_output_path = Path(args.json_output).expanduser().resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    java_files = find_java_files(source_dir)
    results = [analyze_java_file(path, source_dir) for path in java_files]
    summary = summarize_patterns(results)
    markdown = generate_markdown_report(results, summary)
    write_report(output_path, markdown)
    write_json_report(json_output_path, build_json_report(source_dir, results, summary))

    print("DAO pattern analysis completed.")
    print(f"Java files: {summary['total_java_files']}")
    print(f"DAO candidates: {summary['dao_candidates']}")
    print(f"Extends classes: {len(summary['extends_counter'])}")
    print(f"Suspicious DAO API calls: {len(summary['suspect_counter'])}")
    print(f"Report: {output_path}")
    print(f"JSON report: {json_output_path}")


if __name__ == "__main__":
    main()
