"""Shared JSON, Markdown, and console reports for compatibility results."""

import json
from collections import Counter

from .models import DiffResult, PdfContract


def diff_to_json(result: DiffResult, before: PdfContract, after: PdfContract) -> str:
    return (
        json.dumps(_payload(result, before, after), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    )


def diff_to_markdown(result: DiffResult, before: PdfContract, after: PdfContract) -> str:
    lines = [
        "# AcroContract compatibility report",
        "",
        f"Baseline: `{_markdown_cell(before.source_name or '<contract>')}`  ",
        f"Candidate: `{_markdown_cell(after.source_name or '<contract>')}`",
        "",
        "| Rule / severity | Subject | Finding |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {finding.rule_id} {finding.severity.value} | `{_markdown_cell(finding.subject)}` | "
        f"{_markdown_cell(finding.message)} |"
        for finding in result.findings
    )
    if not result.findings:
        lines.append("| ACR000 info | `$document` | No observable contract changes. |")
    return "\n".join(lines) + "\n"


def _markdown_cell(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("`", "\\`")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def diff_to_console(result: DiffResult, before: PdfContract, after: PdfContract) -> str:
    lines = [
        f"AcroContract: {before.source_name or '<contract>'} -> {after.source_name or '<contract>'}"
    ]
    lines.extend(
        f"[{finding.rule_id} {finding.severity.value}] {finding.subject}: {finding.message}"
        for finding in result.findings
    )
    if not result.findings:
        lines.append("[ACR000 info] $document: No observable contract changes.")
    return "\n".join(lines) + "\n"


def _payload(result: DiffResult, before: PdfContract, after: PdfContract) -> dict[str, object]:
    counts = Counter(finding.severity.value for finding in result.findings)
    return {
        "baseline": before.source_name,
        "candidate": after.source_name,
        "findings": [
            {
                "message": finding.message,
                "ruleId": finding.rule_id,
                "severity": finding.severity.value,
                "subject": finding.subject,
            }
            for finding in result.findings
        ],
        "renameProposals": [
            {
                "confidence": proposal.confidence,
                "reasons": list(proposal.reasons),
                "scores": {
                    "label": proposal.label_score,
                    "name": proposal.name_score,
                    "position": proposal.position_score,
                },
                "source": proposal.source,
                "target": proposal.target,
            }
            for proposal in result.rename_proposals
        ],
        "schemaVersion": "acrocontract.diff.v1",
        "summary": {
            "breaking": counts["breaking"],
            "info": counts["info"],
            "warning": counts["warning"],
        },
    }
