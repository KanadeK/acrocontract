"""Stable JSON serialization for PDF contracts."""

import json

from .models import PdfContract


def contract_to_json(contract: PdfContract) -> str:
    """Serialize a contract with deterministic ordering and public field names."""
    payload = {
        "acroForm": contract.has_acroform,
        "duplicateNames": list(contract.duplicate_names),
        "fields": [
            {
                "alternateName": field.alternate_name,
                "maxLength": field.max_length,
                "name": field.name,
                "options": list(field.options),
                "readOnly": field.read_only,
                "required": field.required,
                "type": field.field_type,
                "widgets": [
                    {"page": widget.page, "rect": list(widget.rect)} for widget in field.widgets
                ],
            }
            for field in contract.fields
        ],
        "needAppearances": contract.need_appearances,
        "pageCount": contract.page_count,
        "schemaVersion": contract.schema_version,
        "source": contract.source_name,
        "unattachedWidgets": list(contract.unattached_widgets),
        "xfa": contract.has_xfa,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
