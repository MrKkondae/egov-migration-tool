from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Finding:
    category: str
    path: str
    line: int | None
    message: str
    snippet: str = ""


@dataclass
class Classification:
    ibatis_only: bool = False
    mybatis_only: bool = False
    mixed_persistence: bool = False
    dao_wrapper_present: bool = False
    manual_review_required: bool = False


@dataclass
class DiscoveryResult:
    source_root: str
    working_root: str
    file_counts: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    classifications: Classification = field(default_factory=Classification)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["classifications"] = asdict(self.classifications)
        return data


@dataclass
class TransformResult:
    path: str
    changed: bool
    change_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Phase2Report:
    source_root: str
    working_root: str
    summary: dict[str, Any] = field(default_factory=dict)
    transform_results: list[TransformResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manual_review: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_root": self.source_root,
            "working_root": self.working_root,
            "summary": self.summary,
            "transform_results": [item.to_dict() for item in self.transform_results],
            "warnings": self.warnings,
            "manual_review": self.manual_review,
        }


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
