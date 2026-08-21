"""Pure compatibility comparison for two normalized PDF contracts."""

from .models import DiffResult, FieldContract, Finding, PdfContract, Severity
from .rename import propose_renames


def compare_contracts(before: PdfContract, after: PdfContract) -> DiffResult:
    """Return deterministic findings for observable form-contract changes."""
    before_fields = {field.name: field for field in before.fields}
    after_fields = {field.name: field for field in after.fields}
    findings: list[Finding] = []
    removed_names = sorted(before_fields.keys() - after_fields.keys())
    added_names = sorted(after_fields.keys() - before_fields.keys())

    for name in removed_names:
        findings.append(_finding("ACR201", Severity.BREAKING, name, "Field was removed."))

    for name in added_names:
        field = after_fields[name]
        if field.required:
            findings.append(
                _finding("ACR209", Severity.BREAKING, name, "A new required field was added.")
            )
        else:
            findings.append(_finding("ACR001", Severity.INFO, name, "An optional field was added."))

    rename_proposals = propose_renames(
        [before_fields[name] for name in removed_names],
        [after_fields[name] for name in added_names],
    )
    for proposal in rename_proposals:
        findings.append(
            _finding(
                "ACR101",
                Severity.WARNING,
                f"{proposal.source} -> {proposal.target}",
                f"Likely rename with {proposal.confidence:.2f} confidence; review before mapping.",
            )
        )

    for name in sorted(before_fields.keys() & after_fields.keys()):
        findings.extend(_compare_field(before_fields[name], after_fields[name]))

    for name in sorted(set(after.duplicate_names) - set(before.duplicate_names)):
        findings.append(
            _finding("ACR207", Severity.BREAKING, name, "A duplicate field name was introduced.")
        )

    if before.has_acroform and not after.has_acroform and after.has_xfa:
        findings.append(
            _finding(
                "ACR208",
                Severity.BREAKING,
                "$document",
                "The AcroForm contract was replaced by XFA-only content.",
            )
        )

    if not before.need_appearances and after.need_appearances:
        findings.append(
            _finding(
                "ACR104",
                Severity.WARNING,
                "$document",
                "Candidate now requires viewer-generated appearances.",
            )
        )

    return DiffResult(tuple(findings), rename_proposals)


def _compare_field(before: FieldContract, after: FieldContract) -> list[Finding]:
    findings: list[Finding] = []
    name = before.name
    if before.field_type != after.field_type:
        findings.append(
            _finding(
                "ACR202",
                Severity.BREAKING,
                name,
                f"Field type changed from {before.field_type} to {after.field_type}.",
            )
        )
    if not before.required and after.required:
        findings.append(_finding("ACR203", Severity.BREAKING, name, "Field became required."))
    if not before.read_only and after.read_only:
        findings.append(_finding("ACR204", Severity.BREAKING, name, "Field became read-only."))
    if after.max_length is not None and (
        before.max_length is None or after.max_length < before.max_length
    ):
        findings.append(
            _finding(
                "ACR205",
                Severity.BREAKING,
                name,
                f"Maximum length shrank from {before.max_length} to {after.max_length}.",
            )
        )
    removed_options = sorted(set(before.options) - set(after.options))
    if removed_options:
        findings.append(
            _finding(
                "ACR206",
                Severity.BREAKING,
                name,
                f"Choice export values were removed: {', '.join(removed_options)}.",
            )
        )
    if _widgets_moved(before, after):
        findings.append(
            _finding(
                "ACR102",
                Severity.WARNING,
                name,
                "Widget count, page, or position changed materially.",
            )
        )
    if before.alternate_name and not after.alternate_name:
        findings.append(_finding("ACR103", Severity.WARNING, name, "Alternate name was removed."))
    elif not before.alternate_name and after.alternate_name:
        findings.append(_finding("ACR002", Severity.INFO, name, "Alternate name was added."))
    return findings


def _widgets_moved(before: FieldContract, after: FieldContract) -> bool:
    if not before.widgets or not after.widgets:
        return False
    if len(before.widgets) != len(after.widgets):
        return True
    for old, new in zip(before.widgets, after.widgets, strict=True):
        if old.page != new.page:
            return True
        old_center = ((old.rect[0] + old.rect[2]) / 2, (old.rect[1] + old.rect[3]) / 2)
        new_center = ((new.rect[0] + new.rect[2]) / 2, (new.rect[1] + new.rect[3]) / 2)
        if (old_center[0] - new_center[0]) ** 2 + (old_center[1] - new_center[1]) ** 2 > 144:
            return True
    return False


def _finding(rule_id: str, severity: Severity, subject: str, message: str) -> Finding:
    return Finding(rule_id=rule_id, severity=severity, subject=subject, message=message)
