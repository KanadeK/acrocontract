from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject

from acrocontract.fill import FillError, fill_pdf
from acrocontract.inspect import InspectionError, _qualified_name, inspect_pdf


def test_reports_duplicate_field_reference_and_rejects_fill(
    pdf_fixtures: Path, tmp_path: Path
) -> None:
    output = tmp_path / "duplicate.pdf"
    reader = PdfReader(pdf_fixtures / "customer-intake-v1.pdf")
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    fields = writer.root_object["/AcroForm"]["/Fields"]
    fields.append(fields[0])
    writer.write(output)

    contract = inspect_pdf(output)

    assert contract.duplicate_names == ("customer.email",)
    with pytest.raises(FillError, match="Duplicate field name"):
        fill_pdf(output, {"customer.email": "value"}, tmp_path / "filled.pdf")


def test_reports_widget_missing_from_field_tree_and_rejects_fill(
    pdf_fixtures: Path, tmp_path: Path
) -> None:
    output = tmp_path / "detached.pdf"
    reader = PdfReader(pdf_fixtures / "customer-intake-v1.pdf")
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    fields = writer.root_object["/AcroForm"]["/Fields"]
    del fields[0]
    writer.write(output)

    contract = inspect_pdf(output)

    assert contract.unattached_widgets == ("customer.email",)
    with pytest.raises(FillError, match="Unattached widget"):
        fill_pdf(output, {"customer.role": "buyer"}, tmp_path / "filled.pdf")


def test_rejects_cyclic_parent_hierarchy() -> None:
    first = DictionaryObject({NameObject("/T"): NameObject("/first")})
    second = DictionaryObject({NameObject("/T"): NameObject("/second")})
    first[NameObject("/Parent")] = second
    second[NameObject("/Parent")] = first

    with pytest.raises(InspectionError, match="Cycle detected"):
        _qualified_name(first)
