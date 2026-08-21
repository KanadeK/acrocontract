import json
from pathlib import Path

from acrocontract.diff import compare_contracts
from acrocontract.inspect import inspect_pdf
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
