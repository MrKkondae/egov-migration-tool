from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path("samples/asis")
DEFAULT_OUTPUT = Path("output/reports/sqlmapclient-usage-analysis.md")
DEFAULT_JSON_OUTPUT = Path("output/reports/sqlmapclient-usage-analysis.json")

JAVA_USAGE_TOKENS = {
    "SqlMapClient": re.compile(r"\bSqlMapClient\b"),
    "SqlMapClientTemplate": re.compile(r"\bSqlMapClientTemplate\b"),
    "setSuperSqlMapClient": re.compile(r"\bsetSuperSqlMapClient\s*\("),
    "getSqlMapClientTemplate": re.compile(r"\bgetSqlMapClientTemplate\s*\("),
}

DAO_BASE_CLASSES = {"EgovAbstractDAO", "EgovComAbstractDAO", "EgovAbstractMapper"}
SPRING_SQLMAP_FACTORY = "org.springframework.orm.ibatis.SqlMapClientFactoryBean"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze sqlMapClient usage across Java and Spring XML sources.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Directory to scan.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown report output path.")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT), help="JSON report output path.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_java_files(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.rglob("*.java") if path.is_file())


def iter_xml_files(source_dir: Path) -> list[Path]:
    return sorted(path for path in source_dir.rglob("*.xml") if path.is_file())


def strip_comments(content: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return re.sub(r"//.*", "", without_block)


def find_package_name(content: str) -> str:
    match = re.search(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", content, re.MULTILINE)
    return match.group(1) if match else ""


def find_class_name(content: str) -> str:
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z_]\w*)", content)
    return match.group(1) if match else ""


def find_extends_name(content: str) -> str:
    match = re.search(
        r"\b(?:class|interface|enum)\s+[A-Za-z_]\w*(?:\s*<[^>{}]+>)?\s+extends\s+([A-Za-z_][\w.]*)",
        content,
    )
    return match.group(1) if match else ""


def build_local_class_index(source_dir: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in iter_java_files(source_dir):
        text = strip_comments(read_text(path))
        package_name = find_package_name(text)
        class_name = find_class_name(text)
        if package_name and class_name:
            index[f"{package_name}.{class_name}"] = relative_path(path, source_dir)
    return index


def classify_class_origin(class_name: str, local_classes: dict[str, str]) -> str:
    if not class_name:
        return "unknown"
    if class_name in local_classes:
        return "project"
    if class_name.startswith(("java.", "javax.", "jakarta.")):
        return "jdk"
    if class_name.startswith(("org.springframework.", "org.mybatis.")):
        return "framework"
    if class_name.startswith(("egovframework.", "org.egovframe.")):
        return "egov_framework_or_project"
    return "external_or_unknown"


def classify_java_usage(item: dict[str, Any]) -> str:
    if item["class_name"] == "EgovComAbstractDAO" or "setSuperSqlMapClient" in item["usage_tokens"]:
        return "공통 DAO 래퍼"
    if item["dao_candidate"]:
        return "DAO 직접 사용"
    return "iBatis 직접 의존 코드"


def analyze_java_usages(source_dir: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    local_classes = build_local_class_index(source_dir)
    results: list[dict[str, Any]] = []

    for path in iter_java_files(source_dir):
        raw = read_text(path)
        text = strip_comments(raw)
        usage_tokens = [name for name, pattern in JAVA_USAGE_TOKENS.items() if pattern.search(text)]
        if not usage_tokens:
            continue

        package_name = find_package_name(text)
        class_name = find_class_name(text)
        extends_name = find_extends_name(text)
        fqcn = f"{package_name}.{class_name}" if package_name and class_name else class_name
        dao_candidate = path.name.endswith("DAO.java") or class_name.endswith(("DAO", "Dao")) or extends_name in DAO_BASE_CLASSES

        results.append(
            {
                "type": "java",
                "category": classify_java_usage(
                    {
                        "class_name": class_name,
                        "usage_tokens": usage_tokens,
                        "dao_candidate": dao_candidate,
                    }
                ),
                "file": relative_path(path, source_dir),
                "package": package_name,
                "class_name": class_name,
                "fqcn": fqcn,
                "extends": extends_name,
                "usage_tokens": usage_tokens,
                "dao_candidate": dao_candidate,
            }
        )

    return results, local_classes


def element_local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def analyze_xml_usages(source_dir: Path, local_classes: dict[str, str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for path in iter_xml_files(source_dir):
        text = read_text(path)

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            continue

        for bean in root.iter():
            if element_local_name(bean.tag) != "bean":
                continue

            bean_id = bean.attrib.get("id", "")
            bean_class = bean.attrib.get("class", "")
            bean_origin = classify_class_origin(bean_class, local_classes)

            if bean_class == SPRING_SQLMAP_FACTORY:
                results.append(
                    {
                        "type": "xml",
                        "category": "Spring Factory Bean",
                        "file": relative_path(path, source_dir),
                        "bean_id": bean_id,
                        "bean_class": bean_class,
                        "bean_class_origin": bean_origin,
                        "property_name": "",
                        "property_ref": "",
                        "recommended_action": "SqlSessionFactoryBean으로 1차 치환 후보",
                    }
                )

            for prop in bean:
                if element_local_name(prop.tag) != "property":
                    continue

                prop_name = prop.attrib.get("name", "")
                prop_ref = prop.attrib.get("ref", "")
                prop_value = prop.attrib.get("value", "")

                if prop_name == "sqlMapClient" or prop_ref == "egov.sqlMapClient" or prop_value == "egov.sqlMapClient":
                    results.append(
                        {
                            "type": "xml",
                            "category": "Spring 참조 사용처",
                            "file": relative_path(path, source_dir),
                            "bean_id": bean_id,
                            "bean_class": bean_class,
                            "bean_class_origin": bean_origin,
                            "property_name": prop_name,
                            "property_ref": prop_ref or prop_value,
                            "recommended_action": recommend_xml_action(bean_class, bean_origin),
                        }
                    )

    return results


def recommend_xml_action(bean_class: str, bean_origin: str) -> str:
    if bean_origin == "project":
        return "프로젝트 클래스 확인 후 sqlSessionFactory/sqlSessionTemplate 대체 규칙 검토"
    if bean_class.startswith("egovframework.rte."):
        return "eGov 제공 클래스 여부 확인 후 대체 property 지원 여부 검토"
    return "외부/프레임워크 클래스이므로 수동 검토 우선"


def summarize(java_results: list[dict[str, Any]], xml_results: list[dict[str, Any]]) -> dict[str, Any]:
    category_counter: Counter[str] = Counter()
    java_token_counter: Counter[str] = Counter()
    bean_class_counter: Counter[str] = Counter()

    for item in java_results:
        category_counter[item["category"]] += 1
        java_token_counter.update(item["usage_tokens"])

    for item in xml_results:
        category_counter[item["category"]] += 1
        if item["bean_class"]:
            bean_class_counter[item["bean_class"]] += 1

    return {
        "java_usage_count": len(java_results),
        "xml_usage_count": len(xml_results),
        "total_usage_count": len(java_results) + len(xml_results),
        "category_counter": dict(category_counter),
        "java_token_counter": dict(java_token_counter),
        "bean_class_counter": dict(bean_class_counter),
    }


def generate_markdown_report(source_dir: Path, java_results: list[dict[str, Any]], xml_results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines: list[str] = [
        "# sqlMapClient 사용처 분석 보고서",
        "",
        f"- 분석 경로: `{source_dir}`",
        "",
        "## 1. 요약",
        "",
        "| 항목 | 건수 |",
        "|---|---:|",
        f"| Java 사용처 | {summary['java_usage_count']} |",
        f"| XML 사용처 | {summary['xml_usage_count']} |",
        f"| 전체 사용처 | {summary['total_usage_count']} |",
        "",
        "## 2. 사용처 분류",
        "",
        "| 분류 | 건수 |",
        "|---|---:|",
    ]

    for key, value in sorted(summary["category_counter"].items()):
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## 3. Java 사용처", "", "| 파일 | 클래스 | extends | 분류 | 사용 토큰 |", "|---|---|---|---|---|"])
    if java_results:
        for item in java_results:
            lines.append(
                f"| {item['file']} | {item['class_name'] or '없음'} | {item['extends'] or '없음'} | {item['category']} | {', '.join(item['usage_tokens'])} |"
            )
    else:
        lines.append("| 없음 | 없음 | 없음 | 없음 | 없음 |")

    lines.extend(["", "## 4. XML 사용처", "", "| 파일 | bean id | bean class | origin | property | 권장 조치 |", "|---|---|---|---|---|---|"])
    if xml_results:
        for item in xml_results:
            property_label = item["property_name"] or item["property_ref"] or "-"
            lines.append(
                f"| {item['file']} | {item['bean_id'] or '-'} | {item['bean_class'] or '-'} | {item['bean_class_origin']} | {property_label} | {item['recommended_action']} |"
            )
    else:
        lines.append("| 없음 | 없음 | 없음 | 없음 | 없음 | 없음 |")

    lines.extend(
        [
            "",
            "## 5. 권장 해석",
            "",
            "- `공통 DAO 래퍼`는 `EgovComAbstractDAO` 같은 공통 기반 클래스로, 전환 우선순위가 높다.",
            "- `DAO 직접 사용`은 DAO 내부에서 iBatis 흔적이 남아 있는 경우로, 공통 래퍼 전환 후 후속 규칙 검토 대상이다.",
            "- `Spring Factory Bean`은 `SqlMapClientFactoryBean -> SqlSessionFactoryBean` 1차 치환 후보다.",
            "- `Spring 참조 사용처`는 bean/property 참조 구조를 함께 봐야 하므로 사용 클래스 기준으로 자동/수동 분기를 결정해야 한다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    json_output_path = Path(args.json_output).expanduser().resolve()

    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    java_results, local_classes = analyze_java_usages(source_dir)
    xml_results = analyze_xml_usages(source_dir, local_classes)
    summary = summarize(java_results, xml_results)

    markdown = generate_markdown_report(source_dir, java_results, xml_results, summary)
    write_text(output_path, markdown)
    write_json(
        json_output_path,
        {
            "source": str(source_dir),
            "summary": summary,
            "java_usages": java_results,
            "xml_usages": xml_results,
        },
    )

    print("sqlMapClient usage analysis completed.")
    print(f"Java usages: {summary['java_usage_count']}")
    print(f"XML usages: {summary['xml_usage_count']}")
    print(f"Markdown report: {output_path}")
    print(f"JSON report: {json_output_path}")


if __name__ == "__main__":
    main()
