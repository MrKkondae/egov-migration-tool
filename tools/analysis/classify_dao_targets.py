from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_INPUT = Path("output/reports/dao-pattern-analysis.md")
DEFAULT_OUTPUT = Path("output/reports/dao-conversion-targets.md")

DAO_API_NAMES = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify DAO conversion target candidates from DAO pattern analysis report.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input markdown report path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output markdown report path.")
    return parser.parse_args()


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+\d+\.", markdown[start:], re.MULTILINE)
    if not next_heading:
        return markdown[start:].strip()
    return markdown[start : start + next_heading.start()].strip()


def parse_markdown_table(section: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []

    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []

    for line in lines[1:]:
        if re.fullmatch(r"\|?[\s:\-|\t]+\|?", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        rows.append(row)
    return rows


def parse_subsection_tables(section: str) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    current_heading = ""
    current_lines: list[str] = []

    for line in section.splitlines():
        if line.startswith("### "):
            if current_heading:
                tables[current_heading] = parse_markdown_table("\n".join(current_lines))
            current_heading = line.strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(line)

    if current_heading:
        tables[current_heading] = parse_markdown_table("\n".join(current_lines))
    return tables


def to_int(value: str) -> int:
    digits = re.sub(r"[^\d]", "", value or "")
    return int(digits) if digits else 0


def classify_inheritance_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        name = row.get("extends 클래스", "").strip()
        count = to_int(row.get("건수", "0"))
        if not name or name == "없음" or name in seen:
            continue

        is_candidate = (
            name.endswith("DAO")
            or "AbstractDAO" in name
            or "Mapper" in name
            or (count > 1 and "ServiceImpl" not in name)
        )
        if not is_candidate:
            continue

        seen.add(name)
        candidates.append(
            {
                "candidate": name,
                "count": str(count),
                "reason": f"{name} 상속 구조는 DAO 상속 전환 후보이다.",
                "follow_up": "RAG 검토 및 전환담당자 검토",
            }
        )
    return candidates


def classify_dao_api_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        name = row.get("호출명", "").strip()
        if not name or name not in DAO_API_NAMES or name in seen:
            continue
        seen.add(name)

        if name == "select":
            reason = "select 호출은 반환 타입 검토가 필요한 DAO API 전환 후보이다."
        else:
            reason = f"{name} 호출은 DAO API 전환 후보이다."

        candidates.append(
            {
                "name": name,
                "count": row.get("호출 건수", "0"),
                "files": row.get("사용 파일 수", "0"),
                "reason": reason,
                "follow_up": "RAG 검토 및 SQL Map 분석 결과와 매칭",
            }
        )
    return candidates


def classify_import_candidates(markdown: str) -> list[dict[str, str]]:
    section = extract_section(markdown, "## 6. DAO 관련 Import 분포")
    subsection_tables = parse_subsection_tables(section)
    rows: list[dict[str, str]] = []
    for table_rows in subsection_tables.values():
        rows.extend(table_rows)

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        import_name = row.get("Import", "").strip()
        count = row.get("건수", "0")
        if not import_name or import_name == "없음" or import_name in seen:
            continue

        lowered = import_name.lower()
        reason = ""
        if "egovframework.rte.psl.dataaccess" in import_name:
            reason = "egovframework.rte.psl.dataaccess 관련 import는 DAO import 전환 후보이다."
        elif "egovframework.com.cmm.service.impl.egovcomabstractdao" in lowered:
            reason = "egovframework.com.cmm.service.impl.EgovComAbstractDAO 관련 import는 DAO import 전환 후보이다."
        elif "com.ibatis" in lowered:
            reason = "com.ibatis 관련 import는 iBatis 기반 전환 검토 후보이다."
        elif "org.springframework.orm.ibatis" in lowered:
            reason = "org.springframework.orm.ibatis 관련 import는 iBatis 기반 전환 검토 후보이다."
        elif "sqlmapclient" in lowered:
            reason = "SqlMapClient 관련 import는 iBatis 기반 전환 검토 후보이다."
        elif "org.egovframe" in lowered:
            reason = "org.egovframe 관련 import는 DAO import 전환 후보이다."
        elif "mybatis" in lowered:
            reason = "mybatis 관련 import는 DAO import 전환 후보이다."

        if not reason:
            continue

        seen.add(import_name)
        candidates.append(
            {
                "import": import_name,
                "count": count,
                "reason": reason,
                "follow_up": "RAG 검토 및 전환담당자 검토",
            }
        )
    return candidates


def classify_return_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    patterns_of_interest = {
        "return DAO API 호출": "DAO API 호출 결과를 return하는 패턴은 반환 타입 및 API 의미 검토 대상이다.",
        "변수 = 메서드호출": "메서드 호출 결과를 변수에 대입하는 패턴은 반환 타입 및 사용 맥락 검토 대상이다.",
        "return 메서드호출": "메서드 호출 결과를 바로 return하는 패턴은 반환 타입 및 호출 의미 검토 대상이다.",
    }

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        pattern = row.get("패턴", "").strip()
        if pattern not in patterns_of_interest or pattern in seen:
            continue
        seen.add(pattern)
        candidates.append(
            {
                "pattern": pattern,
                "count": row.get("건수", "0"),
                "reason": patterns_of_interest[pattern],
                "follow_up": "전환담당자 검토 및 SQL Map 분석 결과와 매칭",
            }
        )
    return candidates


def classify_manual_review_candidates(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    target_patterns = {
        "SqlMapClient": "SqlMapClient 직접 사용 패턴은 수동 검토 후보이다.",
        "sqlMapClient": "sqlMapClient 직접 사용 패턴은 수동 검토 후보이다.",
        "getSqlMapClientTemplate": "getSqlMapClientTemplate 사용 패턴은 수동 검토 후보이다.",
        "SqlSession": "SqlSession 사용 패턴은 수동 검토 후보이다.",
        "sqlSession": "sqlSession 사용 패턴은 수동 검토 후보이다.",
        '@SuppressWarnings("unchecked")': '@SuppressWarnings("unchecked") 사용 패턴은 DAO API 반환 타입 검토 후보이다.',
        "$ 문자열 포함": "$ 문자열 포함 패턴은 수동 검토 후보이다.",
        "# 문자열 포함": "# 문자열 포함 패턴은 수동 검토 후보이다.",
    }

    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        pattern = row.get("패턴", "").strip()
        if pattern not in target_patterns or pattern in seen:
            continue
        seen.add(pattern)
        candidates.append(
            {
                "pattern": pattern,
                "count": row.get("사용 파일 수", "0"),
                "reason": target_patterns[pattern],
                "follow_up": "수동 검토 및 RAG 검토",
            }
        )
    return candidates


def generate_report(classified: dict[str, list[dict[str, str]]]) -> str:
    def table_or_none(rows: list[str], empty_row: str) -> list[str]:
        return rows if rows else [empty_row]

    inheritance_rows = [
        f"| {item['candidate']} | {item['count']} | {item['reason']} | {item['follow_up']} |"
        for item in classified["inheritance"]
    ]
    api_rows = [
        f"| {item['name']} | {item['count']} | {item['files']} | {item['reason']} | {item['follow_up']} |"
        for item in classified["dao_api"]
    ]
    import_rows = [
        f"| {item['import']} | {item['count']} | {item['reason']} | {item['follow_up']} |"
        for item in classified["imports"]
    ]
    return_rows = [
        f"| {item['pattern']} | {item['count']} | {item['reason']} | {item['follow_up']} |"
        for item in classified["return_values"]
    ]
    manual_rows = [
        f"| {item['pattern']} | {item['count']} | {item['reason']} | {item['follow_up']} |"
        for item in classified["manual_review"]
    ]

    lines = [
        "# DAO 전환 대상 분류 보고서",
        "",
        "## 1. 분류 요약",
        "",
        "| 구분 | 후보 수 |",
        "|---|---:|",
        f"| 상속 전환 후보 | {len(classified['inheritance'])} |",
        f"| DAO API 호출 전환 후보 | {len(classified['dao_api'])} |",
        f"| Import 전환 후보 | {len(classified['imports'])} |",
        f"| 반환값 사용 검토 후보 | {len(classified['return_values'])} |",
        f"| 수동 검토 후보 | {len(classified['manual_review'])} |",
        "",
        "## 2. 상속 전환 후보",
        "",
        "| 후보 | 출현 건수 | 분류 사유 | 후속 작업 |",
        "|---|---:|---|---|",
        *table_or_none(inheritance_rows, "| 없음 | 0 | 없음 | 없음 |"),
        "",
        "## 3. DAO API 호출 전환 후보",
        "",
        "| 호출명 | 호출 건수 | 사용 파일 수 | 분류 사유 | 후속 작업 |",
        "|---|---:|---:|---|---|",
        *table_or_none(api_rows, "| 없음 | 0 | 0 | 없음 | 없음 |"),
        "",
        "## 4. Import 전환 후보",
        "",
        "| Import | 출현 건수 | 분류 사유 | 후속 작업 |",
        "|---|---:|---|---|",
        *table_or_none(import_rows, "| 없음 | 0 | 없음 | 없음 |"),
        "",
        "## 5. 반환값 사용 검토 후보",
        "",
        "| 패턴 | 건수 | 분류 사유 | 후속 작업 |",
        "|---|---:|---|---|",
        *table_or_none(return_rows, "| 없음 | 0 | 없음 | 없음 |"),
        "",
        "## 6. 수동 검토 후보",
        "",
        "| 패턴 | 사용 파일 수 | 분류 사유 | 후속 작업 |",
        "|---|---:|---|---|",
        *table_or_none(manual_rows, "| 없음 | 0 | 없음 | 없음 |"),
        "",
        "## 7. RAG/LLM 검토 질문 목록",
        "",
        "다음 질문을 RAG/LLM에 질의하여 전환룰 확정 단계의 근거로 사용한다.",
        "",
        "### DAO 상속 관련",
        "",
        "- eGovFrame 4.3 기준 DAO 상속 구조는 어떤 방식이 권장되는가?",
        "- 기존 EgovAbstractDAO 또는 EgovComAbstractDAO 기반 DAO는 어떤 방식으로 전환하는 것이 적절한가?",
        "- 프로젝트 공통 DAO를 유지하는 방식과 개별 DAO를 직접 전환하는 방식의 차이는 무엇인가?",
        "",
        "### DAO API 호출 관련",
        "",
        "- eGovFrame 4.3 기준 list/select/insert/update/delete 계열 DAO API는 어떤 API로 대응되는가?",
        "- list 호출은 어떤 조건에서 목록 조회로 볼 수 있는가?",
        "- select 호출은 반환 타입에 따라 어떤 검토가 필요한가?",
        "- insert/update/delete 호출의 반환값은 기존 코드와 전환 후 코드에서 의미 차이가 있는가?",
        "",
        "### iBatis/MyBatis 관련",
        "",
        "- iBatis SQL Map 기반 DAO를 MyBatis 기반으로 전환할 때 DAO와 SQL Map은 어떤 순서로 검토해야 하는가?",
        "- SqlMapClient 직접 사용 코드는 자동변환이 가능한가, 아니면 수동검토가 필요한가?",
        "",
        "### 기타",
        "",
        "- @SuppressWarnings(\"unchecked\")는 어떤 경우 제거 가능한가?",
        "- DAO 전환룰을 확정하기 전에 SQL Map 분석 결과와 매칭해야 할 항목은 무엇인가?",
        "",
        "## 8. 전환룰 확정 전 확인사항",
        "",
        "- 이 보고서는 전환 대상 후보 분류 보고서이며, 확정 전환룰이 아니다.",
        "- 전환룰 확정은 RAG/LLM 검토와 전환담당자 승인을 거쳐 수행한다.",
        "- DAO API 호출 전환은 SQL Map 분석 결과와 함께 검토해야 한다.",
        "- 반환 타입이 명확하지 않은 select/list 호출은 자동변환 전 검토가 필요하다.",
        "- SqlMapClient 직접 사용 코드는 별도 수동 검토 대상으로 관리한다.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists() or not input_path.is_file():
        raise SystemExit(f"Input markdown report not found: {input_path}")

    markdown = read_markdown(input_path)

    inheritance_rows = parse_markdown_table(extract_section(markdown, "## 3. 상속 클래스 분포"))
    dao_api_rows = parse_markdown_table(extract_section(markdown, "## 8. DAO API 의심 호출 패턴"))
    return_rows = parse_markdown_table(extract_section(markdown, "## 10. 반환값 사용 패턴"))
    manual_rows = parse_markdown_table(extract_section(markdown, "## 11. 특이 패턴"))

    classified = {
        "inheritance": classify_inheritance_candidates(inheritance_rows),
        "dao_api": classify_dao_api_candidates(dao_api_rows),
        "imports": classify_import_candidates(markdown),
        "return_values": classify_return_candidates(return_rows),
        "manual_review": classify_manual_review_candidates(manual_rows),
    }

    report = generate_report(classified)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("DAO target classification completed.")
    print(f"Inheritance candidates: {len(classified['inheritance'])}")
    print(f"DAO API candidates: {len(classified['dao_api'])}")
    print(f"Import candidates: {len(classified['imports'])}")
    print(f"Return-value review candidates: {len(classified['return_values'])}")
    print(f"Manual review candidates: {len(classified['manual_review'])}")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
