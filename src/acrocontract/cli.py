"""AcroContract command-line interface."""

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from pypdf.errors import PdfReadError

from . import __version__
from .diff import compare_contracts
from .fill import FillError, FillVerificationError, fill_pdf, fill_report_to_json
from .inspect import InspectionError, inspect_pdf
from .migrate import MigrationError, migrate_values
from .models import PdfContract
from .plan import PlanError, build_migration_plan, plan_from_json, plan_to_json
from .reports import diff_to_console, diff_to_json, diff_to_markdown
from .serialize import contract_to_json

app = typer.Typer(
    add_completion=False,
    help="Contract tests for versioned PDF AcroForms.",
    no_args_is_help=True,
)

InputPdf = Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)]
InputJson = Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)]
OutputPath = Annotated[Path, typer.Option("--output", "-o")]


class ReportFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"
    MARKDOWN = "markdown"


@app.command()
def snapshot(form: InputPdf, output: OutputPath) -> None:
    """Extract a deterministic form contract as JSON."""
    contract = _inspect_or_exit(form)
    _write_or_exit(output, contract_to_json(contract))


@app.command(name="diff")
def diff_command(
    baseline: InputPdf,
    candidate: InputPdf,
    report_format: Annotated[ReportFormat, typer.Option("--format")] = ReportFormat.CONSOLE,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Compare two forms and exit 1 when breaking changes are found."""
    before = _inspect_or_exit(baseline)
    after = _inspect_or_exit(candidate)
    result = compare_contracts(before, after)
    renderers = {
        ReportFormat.CONSOLE: diff_to_console,
        ReportFormat.JSON: diff_to_json,
        ReportFormat.MARKDOWN: diff_to_markdown,
    }
    report = renderers[report_format](result, before, after)
    if output is None:
        typer.echo(report, nl=False)
    else:
        _write_or_exit(output, report)
    if result.has_breaking_changes:
        raise typer.Exit(1)


@app.command()
def plan(baseline: InputPdf, candidate: InputPdf, output: OutputPath) -> None:
    """Create an advisory migration plan with reviewed=false."""
    before = _inspect_or_exit(baseline)
    after = _inspect_or_exit(candidate)
    result = compare_contracts(before, after)
    migration_plan = build_migration_plan(before, after, result)
    _write_or_exit(output, plan_to_json(migration_plan))


@app.command(name="migrate-values")
def migrate_values_command(
    values_file: InputJson,
    plan_file: Annotated[Path, typer.Option("--plan", exists=True, dir_okay=False, readable=True)],
    output: OutputPath,
) -> None:
    """Apply a reviewed migration plan to a JSON object of field values."""
    values = _read_json_object_or_exit(values_file)
    try:
        migration_plan = plan_from_json(_read_text_or_exit(plan_file))
        migrated = migrate_values(values, migration_plan)
    except (json.JSONDecodeError, PlanError, MigrationError) as exc:
        _input_error(f"Invalid migration plan or values: {exc}")
    _write_or_exit(
        output, json.dumps(migrated, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


@app.command(name="fill-test")
def fill_test(
    form: InputPdf,
    values_file: InputJson,
    output: OutputPath,
    report: Annotated[Path | None, typer.Option("--report")] = None,
) -> None:
    """Fill a copy, reopen it, and verify field, widget, and appearance values."""
    values = _read_json_object_or_exit(values_file)
    try:
        fill_report = fill_pdf(form, values, output)
    except FillVerificationError as exc:
        typer.echo(f"verification failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    except (FillError, InspectionError, PdfReadError) as exc:
        _input_error(str(exc))
    if report is not None:
        _write_or_exit(report, fill_report_to_json(fill_report))
    typer.echo(f"verified {len(fill_report.verified_fields)} field(s): {output}")


@app.command()
def version() -> None:
    """Print the installed AcroContract version."""
    typer.echo(f"acrocontract {__version__}")


def _inspect_or_exit(path: Path) -> PdfContract:
    try:
        return inspect_pdf(path)
    except (FileNotFoundError, InspectionError, PdfReadError) as exc:
        _input_error(str(exc))


def _read_json_object_or_exit(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(_read_text_or_exit(path))
    except json.JSONDecodeError as exc:
        _input_error(f"Invalid JSON in {path}: {exc.msg}")
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        _input_error(f"JSON input must be an object with string keys: {path}")
    return payload


def _read_text_or_exit(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _input_error(str(exc))


def _write_or_exit(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        _input_error(str(exc))


def _input_error(message: str) -> NoReturn:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(2)
