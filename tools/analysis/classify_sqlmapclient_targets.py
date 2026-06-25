from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("output/reports/sqlmapclient-usage-analysis.json")
DEFAULT_OUTPUT = Path("output/reports/sqlmapclient-usage-targets.md")
DEFAULT_JSON_OUTPUT = Path("output/reports/sqlmapclient-usage-targets.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify sqlMapClient usage targets from analysis JSON.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input analysis JSON path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown report output path.")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT), help="JSON report output path.")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_java_item(item: dict[str, Any]) -> dict[str, Any]:
    category = item.get("category", "")
    usage_tokens = set(item.get("usage_tokens", []))

    if category == "공통 DAO 래퍼":
        decision = "조건부 자동 변환"
        reason = "공통 래퍼는 자동 변환 규칙 적용이 가능하지만 하위 DAO 영향 검토가 함께 필요하다."
        follow_up = "브리지 래퍼 전략 적용 후 DAO/postcheck 결과 확인"
    elif category == "DAO 직접 사용":
        if usage_tokens & {"SqlMapClientTemplate", "getSqlMapClientTemplate"}:
            decision = "수동 검토 필요"
            reason = "DAO 내부에서 iBatis 템플릿 계열 API를 직접 사용하므로 단순 치환이 어렵다."
            follow_up = "메서드/반환 타입과 SQL Map 연계 방식 개별 검토"
        else:
            decision = "조건부 자동 변환"
            reason = "DAO 계열이지만 공통 래퍼/mapper 전환 규칙과 함께 후속 검증이 필요하다."
            follow_up = "DAO 규칙 적용 후 list/select 잔존 여부 postcheck"
    else:
        decision = "수동 검토 필요"
        reason = "DAO 외 일반 Java 코드의 iBatis 직접 의존은 자동 규칙으로 일반화하기 어렵다."
        follow_up = "호출 목적과 대체 API 직접 확인"

    return {
        "type": "java",
        "decision": decision,
        "file": item.get("file", ""),
        "target": item.get("fqcn") or item.get("class_name") or item.get("file", ""),
        "category": category,
        "reason": reason,
        "follow_up": follow_up,
    }


def classify_xml_item(item: dict[str, Any]) -> dict[str, Any]:
    category = item.get("category", "")
    bean_class = item.get("bean_class", "")
    bean_origin = item.get("bean_class_origin", "")
    property_name = item.get("property_name", "")

    if category == "Spring Factory Bean":
        decision = "자동 변환 가능"
        reason = "SqlMapClientFactoryBean은 SqlSessionFactoryBean으로 1차 치환 규칙 적용 가능하다."
        follow_up = "configLocations/mapperLocations 및 bean 후속 참조 점검"
    elif bean_origin == "project":
        decision = "조건부 자동 변환"
        reason = "프로젝트 클래스는 소스 확인 후 sqlSessionFactory/sqlSessionTemplate 치환 규칙을 만들 수 있다."
        follow_up = "해당 bean class의 setter/field 타입 확인 후 property 규칙 확정"
    elif bean_class.startswith("egovframework.rte."):
        decision = "수동 검토 필요"
        reason = "eGov 제공 클래스는 sqlMapClient 대체 property 지원 여부를 별도 확인해야 한다."
        follow_up = f"{bean_class} 의 {property_name or 'sqlMapClient'} 대체 가능 여부 확인"
    else:
        decision = "수동 검토 필요"
        reason = "외부/프레임워크 bean 참조는 내부 구현 확인 없이 자동 치환하기 어렵다."
        follow_up = "문서/소스 기준으로 대체 bean/property 수동 확인"

    return {
        "type": "xml",
        "decision": decision,
        "file": item.get("file", ""),
        "target": item.get("bean_id") or item.get("bean_class") or item.get("file", ""),
        "category": category,
        "reason": reason,
        "follow_up": follow_up,
    }


def classify_targets(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    automatic: list[dict[str, Any]] = []
    conditional: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []

    for item in payload.get("java_usages", []):
        classified = classify_java_item(item)
        if classified["decision"] == "자동 변환 가능":
            automatic.append(classified)
        elif classified["decision"] == "조건부 자동 변환":
            conditional.append(classified)
        else:
            manual.append(classified)

    for item in payload.get("xml_usages", []):
        classified = classify_xml_item(item)
        if classified["decision"] == "자동 변환 가능":
            automatic.append(classified)
        elif classified["decision"] == "조건부 자동 변환":
            conditional.append(classified)
        else:
            manual.append(classified)

    return {
        "automatic": automatic,
        "conditional": conditional,
        "manual": manual,
    }


def summarize(classified: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    type_counter: Counter[str] = Counter()
    decision_counter = {
        "자동 변환 가능": len(classified["automatic"]),
        "조건부 자동 변환": len(classified["conditional"]),
        "수동 검토 필요": len(classified["manual"]),
    }

    for group in classified.values():
        for item in group:
            type_counter[item["type"]] += 1

    return {
        "decision_counter": decision_counter,
        "type_counter": dict(type_counter),
        "total_count": sum(decision_counter.values()),
    }


def render_rows(items: list[dict[str, Any]], empty_row: str) -> list[str]:
    if not items:
        return [empty_row]
    return [
        f"| {item['type']} | {item['file']} | {item['target']} | {item['category']} | {item['reason']} | {item['follow_up']} |"
        for item in items
    ]


def generate_markdown_report(source: str, classified: dict[str, list[dict[str, Any]]], summary: dict[str, Any]) -> str:
    lines = [
        "# sqlMapClient 사용처 후속 분류 보고서",
        "",
        f"- 분석 원본: `{source}`",
        "",
        "## 1. 요약",
        "",
        "| 구분 | 건수 |",
        "|---|---:|",
        f"| 자동 변환 가능 | {summary['decision_counter']['자동 변환 가능']} |",
        f"| 조건부 자동 변환 | {summary['decision_counter']['조건부 자동 변환']} |",
        f"| 수동 검토 필요 | {summary['decision_counter']['수동 검토 필요']} |",
        f"| 전체 | {summary['total_count']} |",
        "",
        "## 2. 자동 변환 가능",
        "",
        "| 타입 | 파일 | 대상 | 분류 | 판단 사유 | 후속 작업 |",
        "|---|---|---|---|---|---|",
        *render_rows(classified["automatic"], "| 없음 | 없음 | 없음 | 없음 | 없음 | 없음 |"),
        "",
        "## 3. 조건부 자동 변환",
        "",
        "| 타입 | 파일 | 대상 | 분류 | 판단 사유 | 후속 작업 |",
        "|---|---|---|---|---|---|",
        *render_rows(classified["conditional"], "| 없음 | 없음 | 없음 | 없음 | 없음 | 없음 |"),
        "",
        "## 4. 수동 검토 필요",
        "",
        "| 타입 | 파일 | 대상 | 분류 | 판단 사유 | 후속 작업 |",
        "|---|---|---|---|---|---|",
        *render_rows(classified["manual"], "| 없음 | 없음 | 없음 | 없음 | 없음 | 없음 |"),
        "",
        "## 5. 운영 메모",
        "",
        "- `자동 변환 가능`은 바로 규칙화 가능한 항목이다.",
        "- `조건부 자동 변환`은 bean/class 구조 확인 후 프로젝트별 규칙으로 승격할 수 있다.",
        "- `수동 검토 필요`는 외부/eGov 제공 클래스나 일반 Java 코드 직접 의존 항목이다.",
        "",
    ]
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    json_output_path = Path(args.json_output).expanduser().resolve()

    if not input_path.exists():
        raise SystemExit(f"Input JSON not found: {input_path}")

    payload = read_json(input_path)
    classified = classify_targets(payload)
    summary = summarize(classified)
    markdown = generate_markdown_report(str(input_path), classified, summary)

    write_text(output_path, markdown)
    write_json(
        json_output_path,
        {
            "source": str(input_path),
            "summary": summary,
            "automatic": classified["automatic"],
            "conditional": classified["conditional"],
            "manual": classified["manual"],
        },
    )

    print("sqlMapClient target classification completed.")
    print(f"Automatic: {summary['decision_counter']['자동 변환 가능']}")
    print(f"Conditional: {summary['decision_counter']['조건부 자동 변환']}")
    print(f"Manual: {summary['decision_counter']['수동 검토 필요']}")
    print(f"Markdown report: {output_path}")
    print(f"JSON report: {json_output_path}")


if __name__ == "__main__":
    main()
