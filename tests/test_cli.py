import json
from pathlib import Path

from typer.testing import CliRunner

from acrocontract.cli import app

runner = CliRunner()


def test_snapshot_diff_and_version_commands(pdf_fixtures: Path, tmp_path: Path) -> None:
    baseline = pdf_fixtures / "customer-intake-v1.pdf"
    candidate = pdf_fixtures / "customer-intake-v2.pdf"
    snapshot = tmp_path / "contract.json"

    snapshot_result = runner.invoke(app, ["snapshot", str(baseline), "--output", str(snapshot)])
    assert snapshot_result.exit_code == 0
    assert json.loads(snapshot.read_text(encoding="utf-8"))["source"] == baseline.name

    breaking = runner.invoke(app, ["diff", str(baseline), str(candidate), "--format", "json"])
    assert breaking.exit_code == 1
    assert json.loads(breaking.stdout)["summary"]["breaking"] == 4

    compatible = runner.invoke(app, ["diff", str(baseline), str(baseline)])
    assert compatible.exit_code == 0
    assert "ACR000 info" in compatible.stdout

    version = runner.invoke(app, ["version"])
    assert version.exit_code == 0
    assert version.stdout.strip() == "acrocontract 0.1.0"


def test_reviewed_plan_migrate_and_fill_flow(pdf_fixtures: Path, tmp_path: Path) -> None:
    baseline = pdf_fixtures / "customer-intake-v1.pdf"
    candidate = pdf_fixtures / "customer-intake-v2.pdf"
    plan_path = tmp_path / "migration.json"
    values_path = tmp_path / "values.json"
    migrated_path = tmp_path / "migrated-values.json"
    filled_path = tmp_path / "filled.pdf"
    report_path = tmp_path / "fill-report.json"

    plan_result = runner.invoke(
        app, ["plan", str(baseline), str(candidate), "--output", str(plan_path)]
    )
    assert plan_result.exit_code == 0
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["reviewed"] is False
    plan["reviewed"] = True
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    values_path.write_text(
        json.dumps({"customer.email": "ada@example.test", "customer.role": "buyer"}),
        encoding="utf-8",
    )

    migrate_result = runner.invoke(
        app,
        [
            "migrate-values",
            str(values_path),
            "--plan",
            str(plan_path),
            "--output",
            str(migrated_path),
        ],
    )
    assert migrate_result.exit_code == 0
    assert json.loads(migrated_path.read_text(encoding="utf-8"))["contact.email"] == (
        "ada@example.test"
    )

    fill_result = runner.invoke(
        app,
        [
            "fill-test",
            str(candidate),
            str(migrated_path),
            "--output",
            str(filled_path),
            "--report",
            str(report_path),
        ],
    )
    assert fill_result.exit_code == 0
    assert filled_path.is_file()
    assert json.loads(report_path.read_text(encoding="utf-8"))["success"] is True


def test_invalid_external_input_exits_two(pdf_fixtures: Path, tmp_path: Path) -> None:
    malformed = tmp_path / "values.json"
    malformed.write_text("not json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "fill-test",
            str(pdf_fixtures / "customer-intake-v1.pdf"),
            str(malformed),
            "--output",
            str(tmp_path / "filled.pdf"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid JSON" in result.stderr


def test_non_object_json_exits_two(pdf_fixtures: Path, tmp_path: Path) -> None:
    values = tmp_path / "values.json"
    values.write_text("[]", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "fill-test",
            str(pdf_fixtures / "customer-intake-v1.pdf"),
            str(values),
            "--output",
            str(tmp_path / "filled.pdf"),
        ],
    )

    assert result.exit_code == 2
    assert "must be an object" in result.stderr
