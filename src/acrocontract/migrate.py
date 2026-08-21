"""Apply explicitly reviewed field mappings to external JSON values."""

from collections.abc import Mapping

from .plan import MigrationPlan, PlanField


class MigrationError(ValueError):
    """The reviewed plan or supplied values cannot be migrated safely."""


def migrate_values(values: Mapping[str, object], plan: MigrationPlan) -> dict[str, object]:
    if not plan.reviewed:
        raise MigrationError("Migration plan must be explicitly reviewed before use.")

    source_fields = {field.name: field for field in plan.source_fields}
    target_fields = {field.name: field for field in plan.target_fields}
    unknown = sorted(set(values) - set(source_fields))
    if unknown:
        raise MigrationError(f"Unknown source field: {unknown[0]}")

    mappings: dict[str, str] = {}
    sources_by_target: dict[str, str] = {}
    for mapping in plan.mappings:
        if mapping.source in mappings:
            raise MigrationError(f"Source field has multiple mappings: {mapping.source}")
        if mapping.source not in source_fields:
            raise MigrationError(f"Mapping source does not exist: {mapping.source}")
        if mapping.target not in target_fields:
            raise MigrationError(f"Mapping target does not exist: {mapping.target}")
        if mapping.target in sources_by_target:
            raise MigrationError(f"Target field has multiple sources: {mapping.target}")
        source_field = source_fields[mapping.source]
        target_field = target_fields[mapping.target]
        if source_field.field_type != target_field.field_type:
            raise MigrationError(
                f"Mapping changes field type: {mapping.source} -> {mapping.target}"
            )
        if target_field.read_only:
            raise MigrationError(f"Mapping target is read-only: {mapping.target}")
        mappings[mapping.source] = mapping.target
        sources_by_target[mapping.target] = mapping.source

    migrated: dict[str, object] = {}
    for source in sorted(values):
        if source not in mappings:
            raise MigrationError(f"Source field has no reviewed mapping: {source}")
        target = mappings[source]
        if target in migrated:
            raise MigrationError(f"Multiple values collide at target field: {target}")
        target_field = target_fields[target]
        _validate_value(values[source], target_field)
        migrated[target] = values[source]

    missing_required = sorted(
        field.name for field in plan.target_fields if field.required and field.name not in migrated
    )
    if missing_required:
        raise MigrationError(f"Required target field has no value: {missing_required[0]}")
    return migrated


def _validate_value(value: object, field: PlanField) -> None:
    if field.field_type in {"text", "choice", "radio"} and not isinstance(value, str):
        raise MigrationError(f"Field requires a string value: {field.name}")
    if field.field_type == "checkbox" and not isinstance(value, (bool, str)):
        raise MigrationError(f"Checkbox requires a boolean or export-name string: {field.name}")
    if field.field_type in {"signature", "pushbutton"}:
        raise MigrationError(f"Field type cannot be filled: {field.name}")
    if field.field_type == "choice" and field.options and value not in field.options:
        raise MigrationError(f"Value is not allowed for field: {field.name}")
    if field.field_type == "radio" and isinstance(value, str):
        normalized = value if value.startswith("/") else f"/{value}"
        if normalized not in field.options:
            raise MigrationError(f"Value is not allowed for field: {field.name}")
