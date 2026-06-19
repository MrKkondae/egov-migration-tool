from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_INPUT = Path("output/reports/dao-conversion-targets.md")
DEFAULT_OUTPUT = Path("output/reports/dao-rag-questions.md")

LOW_RELEVANCE_INHERITANCE = {
    "UserDefaultVO",
    "Thread",
    "HandlerInterceptorAdapter",
    "EgovExcelMapping",
    "HttpServlet",
    "TagSupport",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DAO RAG review questions from DAO conversion target report.")
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
        rows.append(dict(zip(header, cells)))
    return rows


def generate_inheritance_questions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        candidate = row.get("후보", "").strip()
        count = row.get("출현 건수", "0").strip()
        if not candidate or candidate == "없음" or candidate in seen:
            continue
        seen.add(candidate)

        if candidate in LOW_RELEVANCE_INHERITANCE:
            question = f"`{candidate}`는 DAO 전환 후보인지, 아니면 DAO 후보 탐지 과정에서 포함된 비DAO 가능성으로 제외해야 하는지 어떻게 검토해야 하는가?"
            criteria = [
                "DAO 계층과의 직접 관련성 여부",
                "DAO 후보 탐지 과정에서 함께 포함된 비DAO 패턴인지 여부",
                "DAO 전환 검토 범위에 포함할지 제외할지 판단 기준",
                "수동검토가 필요한 조건",
            ]
        else:
            question = f"eGovFrame 4.3 기준에서 `{candidate}` 상속 구조를 사용하는 DAO는 어떤 방식으로 검토해야 하는가?"
            criteria = [
                "해당 상속 구조를 유지할 수 있는지",
                "eGovFrame 4.3에서 권장되는 DAO 상속 방식이 있는지",
                "공통 DAO를 유지하는 방식과 개별 DAO를 검토하는 방식의 차이",
                "자동변환 가능한 조건과 수동검토가 필요한 조건",
            ]

        questions.append(
            {
                "title": candidate,
                "question": question,
                "criteria": criteria,
                "evidence": f"AS-IS DAO 분석에서 `{candidate}` 상속 구조가 {count}건 발견됨",
                "expected": [
                    "확정 가능한 전환룰 후보",
                    "수동검토 필요 항목",
                    "SQL Map 또는 Spring XML과 추가 매칭이 필요한 항목",
                    "참고 근거",
                ],
            }
        )
    return questions


def generate_dao_api_questions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        name = row.get("호출명", "").strip()
        count = row.get("호출 건수", "0").strip()
        file_count = row.get("사용 파일 수", "0").strip()
        if not name or name == "없음" or name in seen:
            continue
        seen.add(name)

        question = f"eGovFrame 4.3 기준에서 DAO 내부의 `{name}(...)` 호출은 어떤 기준으로 검토해야 하는가?"
        criteria = [
            "이 호출이 어떤 조회/처리 성격의 API인지 판단하는 기준",
            "SQL Map statement id와 매칭해야 할 항목",
            "반환 타입을 함께 확인해야 하는 이유",
            "자동변환 가능한 조건과 수동검토가 필요한 조건",
        ]

        questions.append(
            {
                "title": name,
                "question": question,
                "criteria": criteria,
                "evidence": f"AS-IS DAO 분석에서 `{name}(...)` 호출이 {count}건, {file_count}개 파일에서 발견됨",
                "expected": [
                    "확정 가능한 전환룰 후보",
                    "SQL Map 매칭 필요 항목",
                    "반환 타입 검토 필요 항목",
                    "수동검토 필요 항목",
                ],
            }
        )
    return questions


def generate_import_questions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        import_name = row.get("Import", "").strip()
        count = row.get("출현 건수", "0").strip()
        if not import_name or import_name == "없음" or import_name in seen:
            continue
        seen.add(import_name)

        question = f"eGovFrame 4.3 기준에서 `{import_name}` import를 사용하는 DAO는 어떤 방식으로 검토해야 하는가?"
        criteria = [
            "해당 import가 eGovFrame 4.3에서 유지 가능한지",
            "관련 dependency 변경이 필요한지",
            "import 검토 시 관련 상속/메서드 호출과 함께 확인해야 할 항목",
            "자동변환 가능한 조건과 수동검토가 필요한 조건",
        ]

        questions.append(
            {
                "title": import_name,
                "question": question,
                "criteria": criteria,
                "evidence": f"AS-IS DAO 분석에서 해당 import가 {count}건 발견됨",
                "expected": [
                    "유지 가능 여부",
                    "변경 필요 여부",
                    "함께 검토할 상속/메서드 호출 패턴",
                    "수동검토 필요 항목",
                ],
            }
        )
    return questions


def generate_return_value_questions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        pattern = row.get("패턴", "").strip()
        count = row.get("건수", "0").strip()
        if not pattern or pattern == "없음" or pattern in seen:
            continue
        seen.add(pattern)

        if pattern == "return DAO API 호출":
            question = "DAO API 호출 결과를 바로 return하는 패턴은 eGovFrame 4.3 전환 시 어떤 기준으로 검토해야 하는가?"
        elif pattern == "변수 = 메서드호출":
            question = "메서드 호출 결과를 변수에 대입하는 패턴은 eGovFrame 4.3 전환 시 어떤 기준으로 검토해야 하는가?"
        else:
            question = "메서드 호출 결과를 바로 return하는 패턴은 eGovFrame 4.3 전환 시 어떤 기준으로 검토해야 하는가?"

        criteria = [
            "기존 API의 반환 타입과 전환 후 후보 API의 반환 타입 차이",
            "Service 계층에서 기대하는 반환 타입",
            "SQL Map statement 결과 유형",
            "자동변환 가능한 조건과 수동검토가 필요한 조건",
        ]

        questions.append(
            {
                "title": pattern,
                "question": question,
                "criteria": criteria,
                "evidence": f"AS-IS DAO 분석에서 `{pattern}` 패턴이 {count}건 발견됨",
                "expected": [
                    "자동변환 가능 조건",
                    "수동검토 필요 조건",
                    "반환 타입 검토 기준",
                    "SQL Map 매칭 필요 여부",
                ],
            }
        )
    return questions


def generate_manual_review_questions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for row in rows:
        pattern = row.get("패턴", "").strip()
        count = row.get("사용 파일 수", "0").strip()
        if not pattern or pattern == "없음" or pattern in seen:
            continue
        seen.add(pattern)

        if pattern in {"SqlMapClient", "sqlMapClient"}:
            question = f"DAO 또는 관련 Java 코드에서 `{pattern}` 직접 사용이 발견된 경우 eGovFrame 4.3 전환 시 어떤 방식으로 검토해야 하는가?"
        elif pattern in {"SqlSession", "sqlSession"}:
            question = f"DAO 또는 관련 Java 코드에서 `{pattern}` 사용이 발견된 경우 eGovFrame 4.3 환경에서 어떤 방식으로 검토해야 하는가?"
        elif pattern == "getSqlMapClientTemplate":
            question = "DAO 또는 관련 Java 코드에서 `getSqlMapClientTemplate` 사용이 발견된 경우 어떤 기준으로 검토해야 하는가?"
        elif pattern == '@SuppressWarnings("unchecked")':
            question = '`@SuppressWarnings("unchecked")` 사용 패턴은 DAO 전환 시 어떤 기준으로 검토해야 하는가?'
        elif pattern == "$ 문자열 포함":
            question = "DAO Java 코드에서 `$` 문자열 포함 패턴이 발견된 경우 어떤 의미로 사용되는지 어떻게 검토해야 하는가?"
        else:
            question = "DAO Java 코드에서 `#` 문자열 포함 패턴이 발견된 경우 어떤 의미로 사용되는지 어떻게 검토해야 하는가?"

        criteria = [
            "자동변환 가능 여부",
            "관련 설정 파일 또는 SQL Map과 함께 확인해야 할 항목",
            "eGovFrame 4.3 환경에서 대응 방식 검토 필요 여부",
            "수동검토가 필요한 조건",
        ]

        questions.append(
            {
                "title": pattern,
                "question": question,
                "criteria": criteria,
                "evidence": f"AS-IS DAO 분석에서 `{pattern}` 패턴이 {count}개 파일에서 발견됨",
                "expected": [
                    "자동변환 가능 여부",
                    "수동검토 필요 여부",
                    "관련 설정 파일 확인 항목",
                    "전환룰 반영 가능 여부",
                ],
            }
        )
    return questions


def render_question_blocks(items: list[dict[str, str]]) -> list[str]:
    if not items:
        return ["생성된 질문 없음", ""]

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        lines.append(f"### Q{index}. {item['title']}")
        lines.append("")
        lines.append("질문:")
        lines.append(item["question"])
        lines.append("")
        lines.append("검토 기준:")
        for criterion in item["criteria"]:
            lines.append(f"- {criterion}")
        lines.append("")
        lines.append("근거:")
        lines.append(f"- {item['evidence']}")
        lines.append("")
        lines.append("기대 답변 형식:")
        for expected in item["expected"]:
            lines.append(f"- {expected}")
        lines.append("")
    return lines


def generate_report(questions: dict[str, list[dict[str, str]]]) -> str:
    lines = [
        "# DAO RAG 검토 질문 목록",
        "",
        "## 1. 질문 생성 요약",
        "",
        "| 구분 | 질문 수 |",
        "|---|---:|",
        f"| 상속 전환 후보 질문 | {len(questions['inheritance'])} |",
        f"| DAO API 호출 질문 | {len(questions['dao_api'])} |",
        f"| Import 전환 후보 질문 | {len(questions['imports'])} |",
        f"| 반환값 사용 검토 질문 | {len(questions['return_values'])} |",
        f"| 수동 검토 질문 | {len(questions['manual_review'])} |",
        "",
        "## 2. 상속 전환 후보 질문",
        "",
        *render_question_blocks(questions["inheritance"]),
        "## 3. DAO API 호출 질문",
        "",
        *render_question_blocks(questions["dao_api"]),
        "## 4. Import 전환 후보 질문",
        "",
        *render_question_blocks(questions["imports"]),
        "## 5. 반환값 사용 검토 질문",
        "",
        *render_question_blocks(questions["return_values"]),
        "## 6. 수동 검토 후보 질문",
        "",
        *render_question_blocks(questions["manual_review"]),
        "## 7. RAG 실행 방법",
        "",
        "아래 순서로 실행한다.",
        "",
        "1. 질문을 한 번에 모두 넣지 않는다.",
        "2. 상속 후보 질문부터 실행한다.",
        "3. DAO API 호출 질문을 실행한다.",
        "4. Import / iBatis 관련 질문을 실행한다.",
        "5. 반환값 / 수동검토 질문을 실행한다.",
        "6. 답변은 output/reports/rag/ 디렉토리에 질문 단위로 저장한다.",
        "",
        "## 8. 후속 작업",
        "",
        "- RAG 답변을 기준으로 DAO 전환룰 후보 보고서를 작성한다.",
        "- 전환담당자가 확정 가능한 룰과 보류 룰을 구분한다.",
        "- 확정된 룰만 rules/dao-rules.yaml에 반영한다.",
        "- RAG 답변을 전환룰로 바로 사용하지 않는다.",
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
    inheritance_rows = parse_markdown_table(extract_section(markdown, "## 2. 상속 전환 후보"))
    dao_api_rows = parse_markdown_table(extract_section(markdown, "## 3. DAO API 호출 전환 후보"))
    import_rows = parse_markdown_table(extract_section(markdown, "## 4. Import 전환 후보"))
    return_rows = parse_markdown_table(extract_section(markdown, "## 5. 반환값 사용 검토 후보"))
    manual_rows = parse_markdown_table(extract_section(markdown, "## 6. 수동 검토 후보"))

    questions = {
        "inheritance": generate_inheritance_questions(inheritance_rows),
        "dao_api": generate_dao_api_questions(dao_api_rows),
        "imports": generate_import_questions(import_rows),
        "return_values": generate_return_value_questions(return_rows),
        "manual_review": generate_manual_review_questions(manual_rows),
    }

    report = generate_report(questions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("DAO RAG question generation completed.")
    print(f"Inheritance questions: {len(questions['inheritance'])}")
    print(f"DAO API questions: {len(questions['dao_api'])}")
    print(f"Import questions: {len(questions['imports'])}")
    print(f"Return-value questions: {len(questions['return_values'])}")
    print(f"Manual-review questions: {len(questions['manual_review'])}")
    print(f"Report: {output_path}")


if __name__ == "__main__":
    main()
