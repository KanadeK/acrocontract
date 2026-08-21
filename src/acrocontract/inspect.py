"""Extract a stable, machine-facing contract from a PDF AcroForm."""

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.constants import FieldDictionaryAttributes
from pypdf.generic import ArrayObject, DictionaryObject

from .models import FieldContract, PdfContract, WidgetContract


class InspectionError(ValueError):
    """The external PDF surface is unsupported for complete inspection."""


def inspect_pdf(path: Path) -> PdfContract:
    """Inspect one local PDF without retaining machine-specific path data."""
    if not path.is_file():
        raise FileNotFoundError(path)

    reader = PdfReader(path)
    if reader.is_encrypted:
        raise InspectionError(f"Encrypted PDFs are not supported: {path}")

    acroform_ref = reader.root_object.get("/AcroForm")
    acroform = acroform_ref.get_object() if acroform_ref is not None else None
    has_acroform = isinstance(acroform, DictionaryObject) and "/Fields" in acroform
    has_xfa = isinstance(acroform, DictionaryObject) and "/XFA" in acroform
    need_appearances = bool(acroform.get("/NeedAppearances", False)) if acroform else False

    widgets_by_name: dict[str, list[WidgetContract]] = defaultdict(list)
    unattached_widgets: list[str] = []
    for page_number, page in enumerate(reader.pages):
        for annotation_number, annotation_ref in enumerate(page.get("/Annots", [])):
            annotation = annotation_ref.get_object()
            if annotation.get("/Subtype") != "/Widget":
                continue
            name = _qualified_name(annotation)
            if not name:
                unattached_widgets.append(f"page[{page_number}].widget[{annotation_number}]")
                continue
            raw_rect = annotation["/Rect"]
            if len(raw_rect) != 4:
                raise InspectionError(f"Widget rectangle must contain four numbers: {name}")
            rect = (
                float(raw_rect[0]),
                float(raw_rect[1]),
                float(raw_rect[2]),
                float(raw_rect[3]),
            )
            widgets_by_name[name].append(WidgetContract(page=page_number, rect=rect))

    raw_fields = reader.get_fields() or {}
    field_names = set(raw_fields)
    for name in sorted(set(widgets_by_name) - field_names):
        unattached_widgets.append(name)

    fields = tuple(
        _field_contract(name, field, widgets_by_name.get(name, []))
        for name, field in sorted(raw_fields.items())
    )
    all_names = _field_names(acroform) if isinstance(acroform, DictionaryObject) else []
    duplicate_names = tuple(sorted(name for name, count in Counter(all_names).items() if count > 1))

    return PdfContract(
        page_count=len(reader.pages),
        has_acroform=has_acroform,
        has_xfa=has_xfa,
        need_appearances=need_appearances,
        fields=fields,
        source_name=path.name,
        duplicate_names=duplicate_names,
        unattached_widgets=tuple(sorted(unattached_widgets)),
    )


def _field_contract(
    name: str, field: DictionaryObject, widgets: list[WidgetContract]
) -> FieldContract:
    assert field.indirect_reference is not None
    original = field.indirect_reference.get_object()
    assert isinstance(original, DictionaryObject)
    flags = int(_inherited(original, "/Ff") or 0)
    field_type = str(_inherited(original, "/FT"))
    if field_type == "/Btn":
        if flags & FieldDictionaryAttributes.FfBits.Pushbutton:
            normalized_type = "pushbutton"
        elif flags & FieldDictionaryAttributes.FfBits.Radio:
            normalized_type = "radio"
        else:
            normalized_type = "checkbox"
    else:
        normalized_type = {"/Tx": "text", "/Ch": "choice", "/Sig": "signature"}.get(
            field_type, f"unknown:{field_type}"
        )

    max_length = _inherited(original, "/MaxLen")
    alternate_name = _inherited(original, "/TU")
    return FieldContract(
        name=name,
        field_type=normalized_type,
        required=bool(flags & FieldDictionaryAttributes.FfBits.Required),
        read_only=bool(flags & FieldDictionaryAttributes.FfBits.ReadOnly),
        max_length=int(max_length) if max_length is not None else None,
        options=_choice_options(_inherited(original, "/Opt")),
        alternate_name=str(alternate_name) if alternate_name is not None else None,
        widgets=tuple(sorted(widgets, key=lambda widget: (widget.page, widget.rect))),
    )


def _choice_options(raw_options: Any) -> tuple[str, ...]:
    if raw_options is None:
        return ()
    return tuple(
        str(option[0] if isinstance(option, ArrayObject) else option) for option in raw_options
    )


def _inherited(field: DictionaryObject, key: str) -> Any:
    current = field
    while True:
        if key in current:
            return current[key]
        parent = current.get("/Parent")
        if parent is None:
            return None
        current = parent.get_object()


def _qualified_name(field: DictionaryObject) -> str:
    parts: list[str] = []
    current = field
    while True:
        partial_name = current.get("/T")
        if partial_name:
            parts.append(str(partial_name))
        parent = current.get("/Parent")
        if parent is None:
            return ".".join(reversed(parts))
        current = parent.get_object()


def _field_names(acroform: DictionaryObject) -> list[str]:
    names: list[str] = []
    pending = list(acroform.get("/Fields", []))
    while pending:
        field = pending.pop().get_object()
        name = _qualified_name(field)
        if name:
            names.append(name)
        for child_ref in field.get("/Kids", []):
            child = child_ref.get_object()
            if child.get("/Subtype") != "/Widget" or child.get("/T"):
                pending.append(child_ref)
    return names
