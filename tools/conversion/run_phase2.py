from __future__ import annotations

import argparse
import json
import shutil
from collections import OrderedDict
from pathlib import Path

from .classify import classify_discovery, merge_dao_analysis
from .discover import discover_project
from .models import Phase2Report, TransformResult
from .postcheck import collect_postcheck_warnings
from .report import write_json_report, write_markdown_report
from .transform_dao import transform_dao_files
from .transform_spring_xml import transform_spring_xml_files
from .transform_sqlmap import transform_sqlmap_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 2 conversion skeleton.")
    parser.add_argument("--source-root", required=True, help="Source project root.")
    parser.add_argument("--working-root", required=True, help="Converted working tree root.")
    parser.add_argument("--report-root", required=True, help="Report output directory.")
    parser.add_argument(
        "--dao-analysis-json",
        help="Optional DAO analysis JSON created by tools.analysis.analyze_dao.",
    )
    parser.add_argument(
        "--sqlmapclient-targets-json",
        help="Optional sqlMapClient target classification JSON created by tools.analysis.classify_sqlmapclient_targets.",
    )
    parser.add_argument(
        "--copy-source",
        action="store_true",
        help="Copy source project into working root before conversion.",
    )
    parser.add_argument(
        "--db-type",
        help="Optional DB type for expanding sqlMapConfig into explicit mapperLocations.",
    )
    return parser.parse_args()


def prepare_working_tree(source_root: Path, working_root: Path, copy_source: bool) -> None:
    if copy_source:
        if working_root.exists():
            shutil.rmtree(working_root)
        shutil.copytree(source_root, working_root)
    else:
        working_root.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_transform_results(results: list[TransformResult]) -> list[TransformResult]:
    merged: OrderedDict[str, TransformResult] = OrderedDict()

    for item in results:
        existing = merged.get(item.path)
        if existing is None:
            merged[item.path] = TransformResult(
                path=item.path,
                changed=item.changed,
                change_count=item.change_count,
                warnings=list(item.warnings),
            )
            continue

        existing.changed = existing.changed or item.changed
        existing.change_count += item.change_count
        for warning in item.warnings:
            if warning not in existing.warnings:
                existing.warnings.append(warning)

    return list(merged.values())


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    working_root = Path(args.working_root).expanduser().resolve()
    report_root = Path(args.report_root).expanduser().resolve()
    dao_analysis_path = Path(args.dao_analysis_json).expanduser().resolve() if args.dao_analysis_json else None
    sqlmapclient_targets_path = (
        Path(args.sqlmapclient_targets_json).expanduser().resolve()
        if args.sqlmapclient_targets_json
        else None
    )

    if not source_root.exists():
        raise SystemExit(f"source root does not exist: {source_root}")
    if dao_analysis_path and not dao_analysis_path.exists():
        raise SystemExit(f"dao analysis json does not exist: {dao_analysis_path}")
    if sqlmapclient_targets_path and not sqlmapclient_targets_path.exists():
        raise SystemExit(f"sqlMapClient targets json does not exist: {sqlmapclient_targets_path}")

    prepare_working_tree(source_root, working_root, args.copy_source)

    discovery = classify_discovery(discover_project(source_root, working_root))
    dao_analysis = load_json(dao_analysis_path) if dao_analysis_path else None
    sqlmapclient_targets = load_json(sqlmapclient_targets_path) if sqlmapclient_targets_path else None
    if dao_analysis:
        discovery = merge_dao_analysis(discovery, dao_analysis)

    transform_results = []
    transform_results.extend(transform_sqlmap_files(working_root))
    transform_results.extend(transform_dao_files(working_root))
    transform_results.extend(transform_spring_xml_files(working_root, sqlmapclient_targets, args.db_type))
    transform_results = merge_transform_results(transform_results)

    postcheck_warnings = collect_postcheck_warnings(working_root)

    report = Phase2Report(
        source_root=str(source_root),
        working_root=str(working_root),
        summary={
            "finding_count": len(discovery.findings),
            "ibatis_only": discovery.classifications.ibatis_only,
            "mybatis_only": discovery.classifications.mybatis_only,
            "mixed_persistence": discovery.classifications.mixed_persistence,
            "dao_wrapper_present": discovery.classifications.dao_wrapper_present,
            "manual_review_required": discovery.classifications.manual_review_required,
            "dao_analysis_linked": bool(dao_analysis),
            "dao_analysis_candidate_count": (dao_analysis or {}).get("dao_candidate_count", 0),
            "sqlmapclient_targets_linked": bool(sqlmapclient_targets),
            "sqlmapclient_automatic_target_count": len((sqlmapclient_targets or {}).get("automatic", [])),
            "transform_result_count": len(transform_results),
        },
        transform_results=transform_results,
        warnings=postcheck_warnings,
        manual_review=[item.path for item in transform_results if item.warnings],
    )

    report_root.mkdir(parents=True, exist_ok=True)
    write_json_report(report, report_root / "phase2-report.json")
    write_markdown_report(report, report_root / "phase2-report.md")
    (report_root / "phase2-discovery.json").write_text(
        json.dumps(discovery.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
