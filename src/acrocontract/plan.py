"""Reviewed value-migration plan model and stable JSON format."""

import json
from dataclasses import dataclass

from .models import DiffResult, FieldContract, PdfContract


@dataclass(frozen=True, slots=True)
class PlanField:
    name: str
    field_type: str
    required: bool
    read_only: bool
    options: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FieldMapping:
    source: str
    target: str
    confidence: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    baseline: str | None
    candidate: str | None
    reviewed: bool
    source_fields: tuple[PlanField, ...]
    target_fields: tuple[PlanField, ...]
    mappings: tuple[FieldMapping, ...]
    schema_version: str = "acrocontract.migration.v1"


class PlanError(ValueError):
    """A supplied migration-plan document violates the public schema."""


def build_migration_plan(
    before: PdfContract, after: PdfContract, result: DiffResult
) -> MigrationPlan:
    before_by_name = {field.name: field for field in before.fields}
    after_by_name = {field.name: field for field in after.fields}
    mappings = [
        FieldMapping(name, name, 1.0, ("Field name and type are unchanged.",))
        for name in sorted(before_by_name.keys() & after_by_name.keys())
        if before_by_name[name].field_type == after_by_name[name].field_type
        and not after_by_name[name].read_only
    ]
    mappings.extend(
        FieldMapping(
            proposal.source,
            proposal.target,
            proposal.confidence,
            proposal.reasons,
        )
        for proposal in result.rename_proposals
    )
    return MigrationPlan(
        baseline=before.source_name,
        candidate=after.source_name,
        reviewed=False,
        source_fields=tuple(_plan_field(field) for field in before.fields),
        target_fields=tuple(_plan_field(field) for field in after.fields),
        mappings=tuple(sorted(mappings, key=lambda mapping: (mapping.source, mapping.target))),
    )


def plan_to_json(plan: MigrationPlan) -> str:
    payload = {
        "baseline": plan.baseline,
        "candidate": plan.candidate,
        "mappings": [
            {
                "confidence": mapping.confidence,
                "from": mapping.source,
                "reasons": list(mapping.reasons),
                "to": mapping.target,
            }
            for mapping in plan.mappings
        ],
        "reviewed": plan.reviewed,
        "schemaVersion": plan.schema_version,
        "sourceFields": [_field_payload(field) for field in plan.source_fields],
        "targetFields": [_field_payload(field) for field in plan.target_fields],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def plan_from_json(text: str) -> MigrationPlan:
    payload = json.loads(text)
    if payload.get("schemaVersion") != "acrocontract.migration.v1":
        raise PlanError("Unsupported migration-plan schemaVersion.")
    if not isinstance(payload.get("reviewed"), bool):
        raise PlanError("Migration plan 'reviewed' must be true or false.")
    return MigrationPlan(
        baseline=payload.get("baseline"),
        candidate=payload.get("candidate"),
        reviewed=payload["reviewed"],
        source_fields=tuple(_field_from_payload(field) for field in payload["sourceFields"]),
        target_fields=tuple(_field_from_payload(field) for field in payload["targetFields"]),
        mappings=tuple(
            FieldMapping(
                source=mapping["from"],
                target=mapping["to"],
                confidence=float(mapping["confidence"]),
                reasons=tuple(mapping["reasons"]),
            )
            for mapping in payload["mappings"]
        ),
    )


def _plan_field(field: FieldContract) -> PlanField:
    return PlanField(
        name=field.name,
        field_type=field.field_type,
        required=field.required,
        read_only=field.read_only,
        options=field.options,
    )


def _field_payload(field: PlanField) -> dict[str, object]:
    return {
        "name": field.name,
        "options": list(field.options),
        "readOnly": field.read_only,
        "required": field.required,
        "type": field.field_type,
    }


def _field_from_payload(payload: dict[str, object]) -> PlanField:
    raw_options = payload["options"]
    if not isinstance(raw_options, list):
        raise PlanError("Migration plan field 'options' must be an array.")
    return PlanField(
        name=str(payload["name"]),
        field_type=str(payload["type"]),
        required=bool(payload["required"]),
        read_only=bool(payload["readOnly"]),
        options=tuple(str(option) for option in raw_options),
    )
