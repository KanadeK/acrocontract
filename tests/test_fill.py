import json
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

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


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"customer.role": "buyer"}, "Required field"),
        ({"contact.email": 3, "customer.role": "buyer"}, "string value"),
        ({"contact.email": "x" * 61, "customer.role": "buyer"}, "maximum length"),
        ({"contact.email": "a@example.test", "customer.role": "seller"}, "not allowed"),
    ],
)
def test_rejects_invalid_candidate_values(
    pdf_fixtures: Path, tmp_path: Path, values: dict[str, object], message: str
) -> None:
    with pytest.raises(FillError, match=message) as error:
        fill_pdf(
            pdf_fixtures / "customer-intake-v2.pdf",
            values,
            tmp_path / "filled.pdf",
        )
    assert "seller" not in str(error.value)


@pytest.mark.parametrize(("value", "expected"), [(False, "/Off"), ("Yes", "/Yes")])
def test_accepts_checkbox_boolean_and_export_name(
    pdf_fixtures: Path, tmp_path: Path, value: object, expected: str
) -> None:
    output = tmp_path / f"checkbox-{expected.removeprefix('/')}.pdf"

    fill_pdf(
        pdf_fixtures / "customer-intake-v1.pdf",
        {"customer.email": "a@example.test", "customer.role": "buyer", "terms": value},
        output,
    )

    fields = PdfReader(output).get_fields()
    assert fields is not None
    assert str(fields["terms"]["/V"]) == expected


def test_rejects_unknown_pdf_field_type(pdf_fixtures: Path, tmp_path: Path) -> None:
    source = tmp_path / "unknown-type.pdf"
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(pdf_fixtures / "customer-intake-v1.pdf"))
    field = writer.root_object["/AcroForm"]["/Fields"][0].get_object()
    field[NameObject("/FT")] = NameObject("/Unknown")
    writer.write(source)

    with pytest.raises(FillError, match="Unsupported field type"):
        fill_pdf(
            source,
            {"customer.email": "a@example.test", "customer.role": "buyer"},
            tmp_path / "filled.pdf",
        )
