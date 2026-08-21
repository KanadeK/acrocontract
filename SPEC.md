# Spec: AcroContract 0.1.0

## Objective

AcroContract is a local-first command-line tool that treats a fillable PDF form as a versioned software contract. It helps RPA, government, HR, legal, and document-automation teams answer three questions before replacing a template:

1. What machine-facing form contract does this PDF expose?
2. Is a candidate PDF compatible with the currently automated template?
3. Can representative values be migrated, written, reopened, and read back without silent loss?

The project is not a PDF editor, generic visual diff, form designer, or hosted upload service. It must inspect both the canonical AcroForm field tree and page widgets because either representation alone can hide broken or duplicate fields.

## Research Boundary

The project was selected after inventorying the local workspace and previously discussed ideas, then searching GitHub and the web for direct competitors. Existing tools fill forms, list fields, validate naming conventions, or compare rendered pages. The uncovered gap is an end-to-end semantic compatibility gate that produces a stable contract, classifies breaking changes, proposes explainable renames, migrates values, and verifies the written result after reopening it.

"No direct competitor found" means no publicly discoverable project with the same end-to-end scope was found on 2026-08-12. It is not a mathematical claim that nobody has ever implemented similar private code.

## Tech Stack

- Python 3.10+
- `pypdf` 6.15.x for low-level PDF object traversal and form writes
- Typer 0.27.x and Rich 15.x for the CLI
- Dataclasses and standard-library JSON/HTML escaping for deterministic reports
- pytest, pytest-cov, mypy, Ruff, build, and twine for verification
- ReportLab only in development for deterministic fixture generation
- Hatchling for PEP 517 packaging

Runtime functionality must not require Adobe Acrobat, Java, Node.js, a browser, a network connection, or user uploads.

## Public Commands

```text
acrocontract snapshot FORM.pdf --output contract.json
acrocontract diff BASELINE.pdf CANDIDATE.pdf [--format console|json|markdown] [--output PATH]
acrocontract plan BASELINE.pdf CANDIDATE.pdf --output migration.json
acrocontract migrate-values VALUES.json --plan migration.json --output migrated-values.json
acrocontract fill-test FORM.pdf VALUES.json --output filled.pdf [--report report.json]
acrocontract version
```

Exit codes are a public contract:

- `0`: command completed and the configured gate passed
- `1`: the diff contains a breaking change or fill-test readback failed
- `2`: invalid input, unsupported PDF surface, malformed policy/plan, or incomplete inspection
- `3`: unexpected internal failure

## Contract Model

`contract.json` uses `schemaVersion: "acrocontract.contract.v1"` and contains:

- source filename and page count;
- AcroForm/XFA/NeedAppearances metadata;
- fields with fully-qualified name, type, required/read-only flags, tooltip, maximum length, choice export values, and widgets;
- widgets with zero-based page number and normalized rectangle;
- duplicate field names and widgets that cannot be matched to the canonical field tree.

Stable output must never contain absolute input paths, timestamps, object memory addresses, or volatile PDF object numbers as identity. Every list has a defined deterministic sort order.

## Compatibility Rules

Version 0.1.0 rules include:

- **Breaking**: field removed; field type changed; optional field becomes required; writable field becomes read-only; maximum length shrinks; choice/radio export value is removed; duplicate fully-qualified name is introduced; AcroForm is replaced by XFA-only.
- **Warning**: likely rename; widget changes page or moves by more than 12 points; tooltip is removed; NeedAppearances becomes required.
- **Compatible/info**: optional field is added; tooltip is added; choice display label changes while its export value is preserved.

Rename proposals are advisory and never applied silently. Each proposal includes confidence, component scores, and reasons. Exact mapping requires a committed migration plan.

## Value Migration and Fill Test

Value migration consumes only a reviewed plan. Unknown source keys, ambiguous destinations, type-incompatible mappings, value collisions, or a value outside the candidate choice exports must stop with exit `2`.

Fill testing must:

1. clone the candidate document without mutating the source;
2. reject XFA-only, encrypted, duplicate/ambiguous, or detached field structures rather than guessing;
3. fill every mapped field with `auto_regenerate=False`;
4. write the candidate output;
5. reopen it and verify canonical `/V` values and effective widget values;
6. require non-empty normal appearance streams for updated widgets where supported;
7. emit an optional JSON report listing requested and verified field names without copying field values.

The tool does not claim cross-viewer visual parity in 0.1.0. Rendering examples is a release QA step, not a substitute for logical verification.

## Project Structure

```text
src/acrocontract/       library and CLI
tests/                  unit, integration, and CLI tests
examples/               generated safe PDFs, values, policy, and expected reports
scripts/                fixture, demo, release, and secret-scan automation
docs/                   research, rules, architecture decisions, repair guide
tasks/                  implementation plan and live checklist
.github/workflows/      CI, release, and CodeQL
```

## Code Style

```python
def classify_change(before: FieldContract, after: FieldContract) -> Finding:
    """Return a deterministic, evidence-bearing compatibility finding."""
    if before.field_type != after.field_type:
        return Finding.breaking(
            rule_id="ACR201",
            subject=before.name,
            message=f"Field type changed from {before.field_type} to {after.field_type}.",
        )
    return Finding.compatible(rule_id="ACR000", subject=before.name, message="Unchanged")
```

- Ruff formatting and linting; 100-character lines.
- Fully typed public functions; mypy strict mode for `src`.
- Immutable dataclasses for contracts and findings.
- Stable rule IDs and machine-readable evidence, not prose-only failures.
- No catch-all exception suppression in inspection or verification paths.

## Testing Strategy

- Unit tests for normalization, flags, compatibility rules, rename scoring, migration validation, and report serialization.
- Integration tests against generated AcroForm fixtures that cover field/tree/widget disagreement, duplicate names, removed/renamed/type-changed fields, choice export changes, geometry, tooltips, and write/reopen verification.
- CLI tests for stdout/stderr discipline, exit codes, deterministic JSON, and safe failure messages.
- Two deliberately separated full release-gate runs compare artifact bytes and ZIP metadata to detect nondeterminism.
- Coverage gate: at least 85% lines for `src/acrocontract`; no skipped tests.

## Commands

```powershell
uv sync --all-extras --dev
uv run python scripts/generate_fixtures.py
uv run pytest --cov=acrocontract --cov-report=term-missing --cov-fail-under=90
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run python -m build
uv run twine check dist/*
uv run python scripts/verify.py
uv run python scripts/demo.py
uv run python scripts/package_release.py
```

## Boundaries

- Always: operate on copies; validate every external file; disclose incomplete inspection; use deterministic artifacts; run the release gate before commits and release; verify the author and contributors before publication.
- Ask first: changing the public artifact schema after 0.1.0, destructive PDF rewrites, adding hosted storage, enabling external URL fetching, or publishing to registries other than GitHub Releases.
- Never: upload user PDFs; execute embedded PDF JavaScript/actions; silently accept a rename; overwrite source PDFs; claim XFA support when only inventory is implemented; log field values by default; commit secrets; weaken a failing gate to make CI green.

## Success Criteria

- A fresh user can install the wheel, run the documented demo, and reproduce a breaking diff and a successful reviewed value migration.
- The tool catches at least: removal, rename proposal, type change, option removal, required/read-only flag changes, duplicate name, detached widget, material movement, tooltip loss, and introduced action.
- `fill-test` proves written values after reopening and can emit a value-free JSON report.
- JSON, Markdown, and console reports agree on rule IDs and severities.
- Example PDFs are visually rendered and inspected, contain no private data, and are generated reproducibly.
- Local release gates pass, CI is green on the public commit, and a public `v0.1.0` GitHub Release contains a wheel, sdist, and example bundle.
- Git author/committer, shortlog, online contributors, and absence of `Co-authored-by` are verified before completion.
- The user receives a Gmail self-notification only after the public release and online verification succeed.

## Open Questions Deferred Beyond 0.1.0

- XFA semantic diff and fill support.
- Signature preservation and incremental updates.
- Cross-viewer rendering with PDFium and Adobe Acrobat.
- OCR/visual-label matching for unnamed fields.
- SARIF and direct GitHub PR annotations.
