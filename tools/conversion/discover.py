from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .models import DiscoveryResult, Finding, rel_path


SKIP_DIRS = {".git", ".idea", ".vscode", "target", "build", "dist", "node_modules"}

PATTERNS: dict[str, re.Pattern[str]] = {
    "egov_abstract_dao": re.compile(r"\bEgovAbstractDAO\b"),
    "egov_com_abstract_dao": re.compile(r"\bEgovComAbstractDAO\b"),
    "sql_map_client_factory_bean": re.compile(r"\bSqlMapClientFactoryBean\b"),
    "sql_map_client_template": re.compile(r"\bSqlMapClientTemplate\b"),
    "ibatis_param_hash": re.compile(r"#([A-Za-z_]\w*)#"),
    "ibatis_dynamic": re.compile(r"<dynamic\b", re.IGNORECASE),
    "ibatis_is_not_empty": re.compile(r"<isNotEmpty\b", re.IGNORECASE),
    "ibatis_iterate": re.compile(r"<iterate\b", re.IGNORECASE),
    "mybatis_mapper": re.compile(r"<mapper\b", re.IGNORECASE),
    "ibatis_sqlmap": re.compile(r"<sqlMap\b", re.IGNORECASE),
}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def discover_project(source_root: Path, working_root: Path) -> DiscoveryResult:
    file_counts: Counter[str] = Counter()
    findings: list[Finding] = []

    for path in sorted(source_root.rglob("*")):
        if should_skip(path) or not path.is_file():
            continue

        suffix = path.suffix.lower() or "(noext)"
        file_counts[suffix] += 1

        if suffix not in {".java", ".xml"}:
            continue

        text = read_text(path)
        for category, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = text.splitlines()[line - 1].strip() if text.splitlines() else ""
                findings.append(
                    Finding(
                        category=category,
                        path=rel_path(path, source_root),
                        line=line,
                        message=f"{category} detected",
                        snippet=snippet,
                    )
                )

    return DiscoveryResult(
        source_root=str(source_root),
        working_root=str(working_root),
        file_counts=dict(file_counts),
        findings=findings,
    )
