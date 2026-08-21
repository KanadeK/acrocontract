"""Write AcroForm values to a copy, reopen it, and verify the result."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject

from .inspect import _inherited, _qualified_name, inspect_pdf
from .models import FieldContract


class FillError(ValueError):
    """The requested fill cannot be performed or verified safely."""


class FillVerificationError(FillError):
    """The output was written but did not pass reopen verification."""


@dataclass(frozen=True, slots=True)
class FillReport:
    source: str
    output: str
    requested_fields: tuple[str, ...]
    verified_fields: tuple[str, ...]
    success: bool
    schema_version: str = "acrocontract.fill-report.v1"


def fill_pdf(path: Path, values: Mapping[str, object], output: Path) -> FillReport:
    """Fill a copied AcroForm and prove field, widget, and appearance readback."""
    if path.resolve() == output.resolve():
        raise FillError("Input and output paths must differ.")
    contract = inspect_pdf(path)
    if not contract.has_acroform:
        raise FillError("PDF does not expose an AcroForm field tree.")
    if contract.has_xfa:
        raise FillError("XFA forms are inventory-only and cannot be filled.")
    if contract.duplicate_names:
        raise FillError(f"Duplicate field name: {contract.duplicate_names[0]}")
    if contract.unattached_widgets:
        raise FillError(f"Unattached widget: {contract.unattached_widgets[0]}")

    fields = {field.name: field for field in contract.fields}
    unknown = sorted(set(values) - set(fields))
    if unknown:
        raise FillError(f"Unknown field: {unknown[0]}")
    missing_required = sorted(
        field.name for field in contract.fields if field.required and field.name not in values
    )
    if missing_required:
        raise FillError(f"Required field has no value: {missing_required[0]}")

    reader = PdfReader(path)
    writer_values = {
        name: _writer_value(reader, fields[name], values[name]) for name in sorted(values)
    }
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.update_page_form_field_values(None, writer_values, auto_regenerate=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as output_file:
        writer.write(output_file)

    verified = _verify_output(output, writer_values)
    return FillReport(
        source=path.name,
        output=output.name,
        requested_fields=tuple(writer_values),
        verified_fields=verified,
        success=True,
    )


def fill_report_to_json(report: FillReport) -> str:
    payload = {
        "output": report.output,
        "requestedFields": list(report.requested_fields),
        "schemaVersion": report.schema_version,
        "source": report.source,
        "success": report.success,
        "verifiedFields": list(report.verified_fields),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _writer_value(reader: PdfReader, field: FieldContract, value: object) -> str:
    if field.read_only:
        raise FillError(f"Field is read-only: {field.name}")
    if field.field_type in {"text", "choice", "radio"} and not isinstance(value, str):
        raise FillError(f"Field requires a string value: {field.name}")
    if field.field_type == "checkbox" and not isinstance(value, (bool, str)):
        raise FillError(f"Checkbox requires a boolean or export-name string: {field.name}")
    if field.field_type in {"signature", "pushbutton"}:
        raise FillError(f"Field type cannot be filled: {field.name}")
    if field.max_length is not None and isinstance(value, str) and len(value) > field.max_length:
        raise FillError(f"Value exceeds maximum length for field: {field.name}")
    if field.options and value not in field.options:
        raise FillError(f"Value is not allowed for {field.name}: {value}")
    if field.field_type == "checkbox":
        states = _button_states(reader, field.name)
        if isinstance(value, bool):
            return next(state for state in states if state != "/Off") if value else "/Off"
        if not isinstance(value, str):
            raise FillError(f"Checkbox requires a boolean or export-name string: {field.name}")
        normalized = value if value.startswith("/") else f"/{value}"
        if normalized not in states:
            raise FillError(f"Unknown checkbox export name for {field.name}: {value}")
        return normalized
    if not isinstance(value, str):
        raise FillError(f"Unsupported field value: {field.name}")
    return value


def _button_states(reader: PdfReader, field_name: str) -> tuple[str, ...]:
    states: set[str] = set()
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            if annotation.get("/Subtype") != "/Widget" or _qualified_name(annotation) != field_name:
                continue
            normal = annotation["/AP"]["/N"].get_object()
            if isinstance(normal, DictionaryObject):
                states.update(str(state) for state in normal)
    active = sorted(state for state in states if state != "/Off")
    if len(active) != 1 or "/Off" not in states:
        raise FillError(f"Checkbox must expose one on-state and /Off: {field_name}")
    return tuple(active + ["/Off"])


def _verify_output(output: Path, expected: Mapping[str, str]) -> tuple[str, ...]:
    reader = PdfReader(output)
    fields = reader.get_fields() or {}
    for name, value in expected.items():
        if name not in fields or str(fields[name].get("/V")) != value:
            raise FillVerificationError(f"Canonical field readback failed: {name}")

    verified_widgets: set[str] = set()
    for page in reader.pages:
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            if annotation.get("/Subtype") != "/Widget":
                continue
            name = _qualified_name(annotation)
            if name not in expected:
                continue
            if str(_inherited(annotation, "/V")) != expected[name]:
                raise FillVerificationError(f"Widget value readback failed: {name}")
            if not _has_nonempty_appearance(annotation):
                raise FillVerificationError(f"Widget appearance readback failed: {name}")
            verified_widgets.add(name)

    missing = sorted(set(expected) - verified_widgets)
    if missing:
        raise FillVerificationError(f"No verified widget for field: {missing[0]}")
    return tuple(sorted(verified_widgets))


def _has_nonempty_appearance(annotation: DictionaryObject) -> bool:
    appearance = annotation.get("/AP")
    if appearance is None or "/N" not in appearance.get_object():
        return False
    normal: Any = appearance.get_object()["/N"].get_object()
    if hasattr(normal, "get_data"):
        return bool(normal.get_data())
    if isinstance(normal, DictionaryObject):
        state = annotation.get("/AS")
        if state not in normal:
            return False
        normal = normal[state].get_object()
    return bool(normal.get_data())
