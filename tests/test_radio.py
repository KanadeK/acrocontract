from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from acrocontract.fill import fill_pdf
from acrocontract.inspect import inspect_pdf


def test_inspects_and_fills_radio_export_values(tmp_path: Path) -> None:
    source = tmp_path / "radio.pdf"
    output = tmp_path / "radio-filled.pdf"
    pdf = canvas.Canvas(str(source), pagesize=letter, invariant=1)
    pdf.acroForm.radio(
        name="contact.method",
        value="email",
        selected=True,
        x=72,
        y=700,
        buttonStyle="circle",
    )
    pdf.acroForm.radio(
        name="contact.method",
        value="phone",
        selected=False,
        x=120,
        y=700,
        buttonStyle="circle",
    )
    pdf.showPage()
    pdf.save()

    contract = inspect_pdf(source)
    field = contract.fields[0]
    assert field.field_type == "radio"
    assert field.options == ("/email", "/phone")
    assert len(field.widgets) == 2

    fill_pdf(source, {"contact.method": "phone"}, output)

    fields = PdfReader(output).get_fields()
    assert fields is not None
    assert str(fields["contact.method"]["/V"]) == "/phone"
