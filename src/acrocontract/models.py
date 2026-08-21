"""Stable data model shared by inspection, comparison, and reports."""

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """Compatibility impact of one finding."""

    BREAKING = "breaking"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class WidgetContract:
    """One page widget attached to a form field."""

    page: int
    rect: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class FieldContract:
    """Machine-facing properties of one fully-qualified AcroForm field."""

    name: str
    field_type: str
    required: bool = False
    read_only: bool = False
    max_length: int | None = None
    options: tuple[str, ...] = ()
    alternate_name: str | None = None
    widgets: tuple[WidgetContract, ...] = ()


@dataclass(frozen=True, slots=True)
class PdfContract:
    """Normalized contract extracted from a PDF."""

    page_count: int
    has_acroform: bool
    has_xfa: bool
    need_appearances: bool
    fields: tuple[FieldContract, ...]
    source_name: str | None = None
    duplicate_names: tuple[str, ...] = ()
    unattached_widgets: tuple[str, ...] = ()
    schema_version: str = "acrocontract.contract.v1"


@dataclass(frozen=True, slots=True)
class Finding:
    """One deterministic compatibility result."""

    rule_id: str
    severity: Severity
    subject: str
    message: str


@dataclass(frozen=True, slots=True)
class RenameProposal:
    """Advisory, explainable mapping between a removed and added field."""

    source: str
    target: str
    confidence: float
    name_score: float
    label_score: float
    position_score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiffResult:
    """Ordered findings for a baseline and candidate contract."""

    findings: tuple[Finding, ...]
    rename_proposals: tuple[RenameProposal, ...] = ()

    @property
    def has_breaking_changes(self) -> bool:
        return any(finding.severity is Severity.BREAKING for finding in self.findings)
