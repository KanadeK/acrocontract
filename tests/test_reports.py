import json
from pathlib import Path

from acrocontract.diff import compare_contracts
from acrocontract.inspect import inspect_pdf
from acrocontract.models import DiffResult, Finding, PdfContract, Severity
from acrocontract.reports import diff_to_console, diff_to_json, diff_to_markdown


def test_all_diff_reports_share_rule_ids_and_severities(pdf_fixtures: Path) -> None:
    before = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")
    after = inspect_pdf(pdf_fixtures / "customer-intake-v2.pdf")
    result = compare_contracts(before, after)

    json_report = diff_to_json(result, before, after)
    markdown = diff_to_markdown(result, before, after)
    console = diff_to_console(result, before, after)
    payload = json.loads(json_report)

    assert payload["summary"] == {"breaking": 4, "info": 1, "warning": 1}
    for finding in payload["findings"]:
        marker = f"{finding['ruleId']} {finding['severity']}"
        assert marker in markdown
        assert marker in console
    assert payload["renameProposals"][0]["source"] == "customer.email"
    assert payload["renameProposals"][0]["target"] == "contact.email"


def test_unchanged_markdown_has_explicit_no_change_row(pdf_fixtures: Path) -> None:
    contract = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")

    report = diff_to_markdown(compare_contracts(contract, contract), contract, contract)

    assert "ACR000 info" in report


def test_markdown_escapes_untrusted_field_text() -> None:
    contract = PdfContract(0, False, False, False, ())
    result = DiffResult(
        (Finding("ACR999", Severity.WARNING, "field|name", "first line\nsecond line"),)
    )

    report = diff_to_markdown(result, contract, contract)

    assert "field\\|name" in report
    assert "first line second line" in report
