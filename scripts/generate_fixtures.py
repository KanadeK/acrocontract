"""Generate public, synthetic PDF fixtures used by tests and documentation."""

from argparse import ArgumentParser
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_examples(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_form(output_dir / "customer-intake-v1.pdf", version=1)
    _write_form(output_dir / "customer-intake-v2.pdf", version=2)


def _write_form(path: Path, *, version: int) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    pdf.setTitle(f"AcroContract customer intake v{version}")
    pdf.setFillColor(HexColor("#172033"))
    pdf.rect(0, 720, letter[0], 72, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(54, 755, "Customer intake")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(54, 738, f"Synthetic AcroContract example - template v{version}")

    pdf.setFillColor(HexColor("#172033"))
    pdf.setFont("Helvetica", 11)
    email_name = "customer.email" if version == 1 else "contact.email"
    pdf.drawString(54, 688, "Email address")
    pdf.acroForm.textfield(
        name=email_name,
        tooltip="Customer email address",
        x=180,
        y=675,
        width=340,
        height=24,
        maxlen=120 if version == 1 else 60,
        fieldFlags="" if version == 1 else "required",
        forceBorder=True,
    )

    pdf.drawString(54, 636, "Customer role")
    role_options = ["buyer", "seller"] if version == 1 else ["buyer"]
    pdf.acroForm.choice(
        name="customer.role",
        tooltip="Customer role",
        value="buyer",
        options=role_options,
        x=180,
        y=623,
        width=180,
        height=24,
        forceBorder=True,
    )

    if version == 1:
        pdf.acroForm.checkbox(
            name="terms",
            tooltip="Accept terms",
            x=180,
            y=573,
            size=18,
            fieldFlags="",
            forceBorder=True,
        )
        pdf.drawString(208, 578, "Accept the terms")
    else:
        pdf.drawString(54, 584, "Optional note")
        pdf.acroForm.textfield(
            name="customer.note",
            tooltip="Optional note",
            x=180,
            y=571,
            width=340,
            height=24,
            maxlen=200,
            fieldFlags="",
            forceBorder=True,
        )

    pdf.setFillColor(HexColor("#5D6472"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(54, 48, "All names and values in this fixture are fictional.")
    pdf.save()


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("examples"))
    args = parser.parse_args()
    generate_examples(args.output_dir)


if __name__ == "__main__":
    main()
