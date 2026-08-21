import json
from dataclasses import replace
from pathlib import Path

import pytest

from acrocontract.diff import compare_contracts
from acrocontract.inspect import inspect_pdf
from acrocontract.migrate import MigrationError, migrate_values
from acrocontract.plan import (
    FieldMapping,
    PlanError,
    build_migration_plan,
    plan_from_json,
    plan_to_json,
)


def example_plan(pdf_fixtures: Path):  # type: ignore[no-untyped-def]
    before = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")
    after = inspect_pdf(pdf_fixtures / "customer-intake-v2.pdf")
    result = compare_contracts(before, after)
    return build_migration_plan(before, after, result)


def test_plan_is_advisory_and_round_trips_stably(pdf_fixtures: Path) -> None:
    plan = example_plan(pdf_fixtures)

    assert plan.reviewed is False
    assert {(mapping.source, mapping.target) for mapping in plan.mappings} == {
        ("customer.email", "contact.email"),
        ("customer.role", "customer.role"),
    }
    assert plan_to_json(plan) == plan_to_json(plan_from_json(plan_to_json(plan)))


def test_migrates_only_after_explicit_review(pdf_fixtures: Path) -> None:
    plan = example_plan(pdf_fixtures)
    values = {"customer.email": "ada@example.test", "customer.role": "buyer"}

    with pytest.raises(MigrationError, match="reviewed"):
        migrate_values(values, plan)

    migrated = migrate_values(values, replace(plan, reviewed=True))
    assert migrated == {"contact.email": "ada@example.test", "customer.role": "buyer"}


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"unknown": "value"}, "Unknown source field"),
        ({"terms": True}, "has no reviewed mapping"),
        ({"customer.role": "seller", "customer.email": "a@example.test"}, "not allowed"),
    ],
)
def test_rejects_unmapped_unknown_and_invalid_values(
    pdf_fixtures: Path, values: dict[str, object], message: str
) -> None:
    plan = replace(example_plan(pdf_fixtures), reviewed=True)

    with pytest.raises(MigrationError, match=message):
        migrate_values(values, plan)


def test_rejects_invalid_plan_schema_fields(pdf_fixtures: Path) -> None:
    payload = json.loads(plan_to_json(example_plan(pdf_fixtures)))

    payload["schemaVersion"] = "unknown"
    with pytest.raises(PlanError, match="schemaVersion"):
        plan_from_json(json.dumps(payload))

    payload["schemaVersion"] = "acrocontract.migration.v1"
    payload["reviewed"] = "yes"
    with pytest.raises(PlanError, match="reviewed"):
        plan_from_json(json.dumps(payload))

    payload["reviewed"] = True
    payload["sourceFields"][0]["options"] = {}
    with pytest.raises(PlanError, match="options"):
        plan_from_json(json.dumps(payload))

    with pytest.raises(PlanError, match="object"):
        plan_from_json("[]")


def test_rejects_ambiguous_or_unknown_plan_mappings(pdf_fixtures: Path) -> None:
    plan = replace(example_plan(pdf_fixtures), reviewed=True)
    first = plan.mappings[0]
    collision = replace(
        plan,
        mappings=plan.mappings + (FieldMapping("terms", first.target, 1.0, ("manual",)),),
    )
    unknown = replace(
        plan,
        mappings=plan.mappings + (FieldMapping("ghost", "customer.note", 1.0, ("manual",)),),
    )

    with pytest.raises(MigrationError, match="multiple sources"):
        migrate_values({"customer.email": "a@example.test"}, collision)
    with pytest.raises(MigrationError, match="does not exist"):
        migrate_values({"customer.email": "a@example.test"}, unknown)
