# AcroContract

**Catch breaking changes in fillable PDFs before they break your automation.**

[![CI](https://github.com/KanadeK/acrocontract/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/acrocontract/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0B7285.svg)](LICENSE)

A replacement PDF can look identical while silently renaming a field, shrinking its maximum
length, removing a choice export value, or detaching a widget. AcroContract treats the AcroForm
surface as an API: it snapshots the contract, classifies semantic changes, proposes explainable
renames, migrates values only through a reviewed plan, then fills and reopens the output to prove
the values and appearance streams survived.

- Local-first: PDFs and values never leave your machine.
- CI-friendly: deterministic JSON/Markdown output and stable `ACR` rule IDs.
- Review-first: rename guesses are advisory and every migration plan starts with `reviewed: false`.
- Real verification: `fill-test` checks canonical fields, page widgets, and non-empty appearances.

## Thirty-second proof

```powershell
git clone https://github.com/KanadeK/acrocontract.git
cd acrocontract
uv sync --extra dev

# Expected exit 1: the candidate contains four breaking changes.
uv run acrocontract diff examples/customer-intake-v1.pdf examples/customer-intake-v2.pdf

# Runs reviewed migration and write/reopen verification into output/demo/.
uv run python scripts/demo.py
```

The included synthetic example catches a removed field, a new required field, a removed choice
export value, and a likely rename. It then migrates `customer.email` to `contact.email`, fills the
candidate, reopens it, and verifies every requested widget without placing field values in the
report.

## Commands

| Command | Purpose | Gate exit |
|---|---|---|
| `snapshot FORM.pdf -o contract.json` | Extract a stable form contract | `0` |
| `diff BASE.pdf NEW.pdf [--format console\|json\|markdown]` | Classify compatibility changes | `1` if breaking |
| `plan BASE.pdf NEW.pdf -o migration.json` | Propose identity and likely-rename mappings | `0` |
| `migrate-values VALUES.json --plan PLAN.json -o OUT.json` | Apply an explicitly reviewed plan | `0` |
| `fill-test FORM.pdf VALUES.json -o filled.pdf [--report report.json]` | Fill, reopen, and verify | `1` if readback fails |
| `version` | Print the installed version | `0` |

Invalid JSON, unsupported PDFs, unreviewed plans, ambiguous mappings, and invalid field values exit
with `2`. Reports and snapshots contain basenames and field names, never absolute paths or field
values.

## Safe migration workflow

```powershell
uv run acrocontract plan old.pdf new.pdf --output migration.json

# Open migration.json. Verify every from/to mapping, then deliberately change:
#   "reviewed": false
# to:
#   "reviewed": true

uv run acrocontract migrate-values old-values.json `
  --plan migration.json `
  --output new-values.json

uv run acrocontract fill-test new.pdf new-values.json `
  --output filled.pdf `
  --report fill-report.json
```

AcroContract never rewrites field identities or silently accepts a rename. The input PDF is never
overwritten.

## What it detects

- field removal, type change, newly required/read-only fields, and shorter maximum lengths;
- removed choice export values and newly duplicated fully-qualified names;
- likely renames with component scores and human-readable reasons;
- material widget movement, tooltip removal, and newly required `NeedAppearances`;
- XFA presence and widgets not represented by the canonical field tree.

See the [rule catalog](docs/rules.md) for stable IDs and severities.

## Scope and limits

Version `0.1.0` supports AcroForm PDFs. XFA is inventoried but not semantically parsed or filled.
Encrypted PDFs, XFA forms, duplicate names, detached widgets, signatures, and pushbuttons fail fast
for filling. Verification proves PDF object-level readback and non-empty appearances; it does not
claim identical rendering in every PDF viewer.

## Development and acceptance

```powershell
uv sync --extra dev
uv run python scripts/verify.py
uv run python scripts/demo.py
```

`verify.py` runs formatting checks, lint, strict typing, coverage, package build, and package metadata
validation. If a gate fails, follow the [repair guide](docs/repair.md) and rerun the same command.

## Why this project exists

Existing open-source tools commonly fill forms, relabel one template, or render a visual audit.
The [research note](docs/research.md) records the search method and nearest projects. As of
2026-08-21, that search did not find a publicly discoverable tool covering the same complete
version-compatibility and verified-migration workflow. That is a dated search result, not a claim
that no private or future implementation exists.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Architectural rationale lives in
[ADR-0001](docs/decisions/0001-contract-first-pdf-inspection.md), security boundaries in
[SECURITY.md](SECURITY.md), and release history in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
