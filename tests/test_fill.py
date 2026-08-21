import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from acrocontract.fill import FillError, fill_pdf, fill_report_to_json


def test_fills_reopens_and_verifies_field_and_widget_values(
    pdf_fixtures: Path, tmp_path: Path
) -> None:
    source = pdf_fixtures / "customer-intake-v1.pdf"
    source_before = source.read_bytes()
    output = tmp_path / "filled.pdf"
    values = {
        "customer.email": "ada@example.test",
        "customer.role": "seller",
        "terms": True,
    }

    report = fill_pdf(source, values, output)

    assert source.read_bytes() == source_before
    assert report.success is True
    assert report.requested_fields == ("customer.email", "customer.role", "terms")
    assert report.verified_fields == report.requested_fields
    fields = PdfReader(output).get_fields()
    assert fields is not None
    assert str(fields["customer.email"]["/V"]) == "ada@example.test"
    assert str(fields["customer.role"]["/V"]) == "seller"
    assert str(fields["terms"]["/V"]) == "/Yes"

    report_json = fill_report_to_json(report)
    assert "ada@example.test" not in report_json
    assert json.loads(report_json)["verifiedFields"] == list(report.verified_fields)


def test_rejects_unknown_field_and_source_overwrite(pdf_fixtures: Path, tmp_path: Path) -> None:
    source = pdf_fixtures / "customer-intake-v1.pdf"

    with pytest.raises(FillError, match="Unknown field"):
        fill_pdf(source, {"missing": "value"}, tmp_path / "filled.pdf")
    with pytest.raises(FillError, match="must differ"):
        fill_pdf(source, {"customer.email": "value"}, source)
