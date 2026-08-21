from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject, TextStringObject

from acrocontract.inspect import inspect_pdf


def test_extracts_canonical_fields_and_page_widgets(pdf_fixtures: Path) -> None:
    contract = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")

    assert contract.source_name == "customer-intake-v1.pdf"
    assert contract.page_count == 1
    assert contract.has_acroform is True
    assert contract.has_xfa is False
    assert contract.need_appearances is False
    assert contract.duplicate_names == ()
    assert contract.unattached_widgets == ()

    fields = {field.name: field for field in contract.fields}
    assert set(fields) == {"customer.email", "customer.role", "terms"}
    assert fields["customer.email"].field_type == "text"
    assert fields["customer.email"].max_length == 120
    assert fields["customer.email"].alternate_name == "Customer email address"
    assert fields["customer.email"].widgets[0].page == 0
    assert fields["customer.email"].widgets[0].rect == (180.0, 675.0, 520.0, 699.0)
    assert fields["customer.role"].field_type == "choice"
    assert fields["customer.role"].options == ("buyer", "seller")
    assert fields["terms"].field_type == "checkbox"


def test_extracts_required_renamed_field_from_candidate(pdf_fixtures: Path) -> None:
    contract = inspect_pdf(pdf_fixtures / "customer-intake-v2.pdf")
    fields = {field.name: field for field in contract.fields}

    assert fields["contact.email"].required is True
    assert fields["contact.email"].max_length == 60
    assert fields["customer.role"].options == ("buyer",)


def test_recognizes_xfa_with_empty_acroform_fields_as_xfa_only(
    pdf_fixtures: Path, tmp_path: Path
) -> None:
    output = tmp_path / "xfa-only.pdf"
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(pdf_fixtures / "customer-intake-v1.pdf"))
    acroform = writer.root_object["/AcroForm"]
    acroform[NameObject("/Fields")] = ArrayObject()
    acroform[NameObject("/XFA")] = TextStringObject("synthetic-xfa")
    writer.write(output)

    contract = inspect_pdf(output)

    assert contract.has_acroform is False
    assert contract.has_xfa is True
