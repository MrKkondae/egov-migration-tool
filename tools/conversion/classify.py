from __future__ import annotations

from typing import Any

from .models import Classification, DiscoveryResult


def classify_discovery(result: DiscoveryResult) -> DiscoveryResult:
    categories = {item.category for item in result.findings}

    has_ibatis = any(
        key in categories
        for key in {
            "egov_abstract_dao",
            "egov_com_abstract_dao",
            "sql_map_client_factory_bean",
            "sql_map_client_template",
            "ibatis_param_hash",
            "ibatis_dynamic",
            "ibatis_is_not_empty",
            "ibatis_iterate",
            "ibatis_sqlmap",
        }
    )
    has_mybatis = "mybatis_mapper" in categories

    result.classifications = Classification(
        ibatis_only=has_ibatis and not has_mybatis,
        mybatis_only=has_mybatis and not has_ibatis,
        mixed_persistence=has_ibatis and has_mybatis,
        dao_wrapper_present="egov_com_abstract_dao" in categories,
        manual_review_required=(
            "sql_map_client_factory_bean" in categories
            or "sql_map_client_template" in categories
            or ("egov_com_abstract_dao" in categories)
        ),
    )
    return result


def merge_dao_analysis(result: DiscoveryResult, dao_analysis: dict[str, Any]) -> DiscoveryResult:
    summary = dao_analysis.get("summary", {})
    extends_counter = summary.get("extends_counter", {})

    has_dao_wrapper = (
        result.classifications.dao_wrapper_present
        or summary.get("dao_candidates", 0) > 0
        and (
            summary.get("egov_import_used_dao", 0) > 0
            or int(extends_counter.get("EgovComAbstractDAO", 0)) > 0
            or int(extends_counter.get("EgovAbstractDAO", 0)) > 0
        )
    )
    needs_manual_review = (
        result.classifications.manual_review_required
        or summary.get("ibatis_import_used_dao", 0) > 0
        or summary.get("sql_map_client_used_dao", 0) > 0
    )

    result.classifications = Classification(
        ibatis_only=result.classifications.ibatis_only,
        mybatis_only=result.classifications.mybatis_only,
        mixed_persistence=result.classifications.mixed_persistence,
        dao_wrapper_present=has_dao_wrapper,
        manual_review_required=needs_manual_review,
    )
    return result
