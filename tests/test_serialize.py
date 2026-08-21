import json
from pathlib import Path

from acrocontract.inspect import inspect_pdf
from acrocontract.serialize import contract_to_json


def test_snapshot_json_is_stable_and_does_not_include_absolute_path(pdf_fixtures: Path) -> None:
    contract = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")

    first = contract_to_json(contract)
    second = contract_to_json(contract)
    payload = json.loads(first)

    assert first == second
    assert payload["schemaVersion"] == "acrocontract.contract.v1"
    assert payload["source"] == "customer-intake-v1.pdf"
    assert str(pdf_fixtures) not in first
    assert [field["name"] for field in payload["fields"]] == [
        "customer.email",
        "customer.role",
        "terms",
    ]
