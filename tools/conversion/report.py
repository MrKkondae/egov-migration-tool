from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .models import Phase2Report


def write_json_report(report: Phase2Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_bool(value: object) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def classify_path_group(path: str) -> str:
    lowered = path.replace("\\", "/").lower()
    if "/sqlmap/" in lowered:
        return "SQL Map"
    if "/spring/" in lowered or path.endswith(".xml"):
        return "Spring XML"
    if path.endswith(".java"):
        return "DAO/Java"
    if path.endswith("pom.xml"):
        return "Build"
    return "Other"


def build_group_summary(results: list) -> list[tuple[str, dict[str, object]]]:
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "file_count": 0,
            "change_count": 0,
            "warning_count": 0,
            "paths": [],
        }
    )

    for item in results:
        group = classify_path_group(item.path)
        grouped[group]["file_count"] = int(grouped[group]["file_count"]) + 1
        grouped[group]["change_count"] = int(grouped[group]["change_count"]) + item.change_count
        grouped[group]["warning_count"] = int(grouped[group]["warning_count"]) + len(item.warnings)
        grouped[group]["paths"].append(item.path)

    preferred_order = {"SQL Map": 0, "DAO/Java": 1, "Spring XML": 2, "Build": 3, "Other": 4}
    return sorted(grouped.items(), key=lambda item: (preferred_order.get(item[0], 99), item[0]))


def classify_warning_type(warning: str) -> str:
    if "공통 DAO wrapper" in warning:
        return "공통 DAO wrapper"
    if "공통 기반 클래스 상속 DAO" in warning:
        return "공통 기반 클래스 상속 DAO"
    if "DAO 메서드 호출 1차 변환" in warning or "Mapper 기반 DAO에 기존" in warning:
        return "DAO 메서드 호출 후속 확인"
    if "Validation bean" in warning:
        return "Validation"
    if "sqlMapClient" in warning:
        return "Spring sqlMapClient 참조"
    if "SqlSessionFactoryBean" in warning or "lobHandler" in warning or "bean id `egov.sqlMapClient`" in warning:
        return "Spring FactoryBean 후속 확인"
    if "SQL Map Config" in warning:
        return "SQL Map Config"
    if "식별자 위치" in warning or "${}" in warning:
        return "SQL Map 치환 검토"
    if "<dynamic" in warning or "<iterate>" in warning or "property 해석 실패" in warning:
        return "SQL Map 동적 구문 검토"
    return "기타"


def build_warning_type_summary(results: list) -> list[tuple[str, dict[str, object]]]:
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "file_count": 0,
            "warning_count": 0,
            "paths": [],
        }
    )

    for item in results:
        seen_types_for_file: set[str] = set()
        for warning in item.warnings:
            warning_type = classify_warning_type(warning)
            grouped[warning_type]["warning_count"] = int(grouped[warning_type]["warning_count"]) + 1
            if warning_type not in seen_types_for_file:
                grouped[warning_type]["file_count"] = int(grouped[warning_type]["file_count"]) + 1
                grouped[warning_type]["paths"].append(item.path)
                seen_types_for_file.add(warning_type)

    return sorted(grouped.items(), key=lambda item: (-int(item[1]["file_count"]), item[0]))


def write_markdown_report(report: Phase2Report, output_path: Path) -> None:
    changed_results = [item for item in report.transform_results if item.changed]
    manual_review_results = [item for item in report.transform_results if item.warnings]
    clean_unchanged_count = sum(1 for item in report.transform_results if not item.changed and not item.warnings)
    changed_groups = build_group_summary(changed_results)
    manual_groups = build_group_summary(manual_review_results)
    manual_warning_types = build_warning_type_summary(manual_review_results)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Phase 2 Conversion Report",
        "",
        "## 요약",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
    ]

    for key, value in report.summary.items():
        lines.append(f"| {key} | {format_bool(value)} |")

    lines.extend(
        [
            f"| changed_file_count | {len(changed_results)} |",
            f"| manual_review_file_count | {len(manual_review_results)} |",
            f"| residual_warning_count | {len(report.warnings)} |",
            f"| unchanged_clean_file_count | {clean_unchanged_count} |",
            "",
            "변경이 없고 경고도 없는 파일은 아래 상세 목록에서 생략했습니다.",
            "",
            "## 자동변경",
            "",
        ]
    )

    if not changed_results:
        lines.append("없음")
    else:
        lines.extend(["| 구분 | 파일 수 | 변경 건수 합계 | 경고 수 합계 |", "|---|---:|---:|---:|"])
        for group_name, data in changed_groups:
            lines.append(
                f"| {group_name} | {data['file_count']} | {data['change_count']} | {data['warning_count']} |"
            )
        lines.extend(["", "주요 변경 파일:", ""])
        for group_name, data in changed_groups:
            lines.append(f"- {group_name}")
            for path in list(data["paths"])[:5]:
                lines.append(f"  - {path}")
            if len(data["paths"]) > 5:
                lines.append(f"  - ... 외 {len(data['paths']) - 5}건")

    lines.extend(["", "## 수동검토", ""])
    if not manual_review_results:
        lines.append("없음")
    else:
        lines.extend(["### 파일 구분 요약", "", "| 구분 | 파일 수 | 검토 항목 합계 |", "|---|---:|---:|"])
        for group_name, data in manual_groups:
            lines.append(f"| {group_name} | {data['file_count']} | {data['warning_count']} |")
        lines.extend(["", "### 경고 유형 요약", "", "| 경고 유형 | 관련 파일 수 | 경고 건수 |", "|---|---:|---:|"])
        for warning_type, data in manual_warning_types:
            lines.append(f"| {warning_type} | {data['file_count']} | {data['warning_count']} |")
        lines.extend(["", "### 주요 수동검토 파일", ""])
        for item in manual_review_results[:15]:
            status = "변경됨" if item.changed else "미변경"
            lines.append(f"- {item.path} | 상태: {status} | 검토 항목: {len(item.warnings)}")
            for warning in item.warnings:
                lines.append(f"  - {warning}")
        if len(manual_review_results) > 15:
            lines.append(f"- ... 외 {len(manual_review_results) - 15}건")

    lines.extend(["", "## 잔존경고", ""])
    if not report.warnings:
        lines.append("없음")
    else:
        for item in report.warnings:
            lines.append(f"- {item}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
