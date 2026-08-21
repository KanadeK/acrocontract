# Contributing

Thanks for helping make PDF automation safer.

## Set up

```powershell
git clone https://github.com/KanadeK/acrocontract.git
cd acrocontract
uv sync --extra dev
uv run python scripts/verify.py
```

## Change rules

- Keep changes focused on one observable problem.
- Add a failing test before changing parsing, compatibility, migration, or fill behavior.
- Validate external PDFs and JSON at the boundary; do not suppress unexpected exceptions.
- Do not include real customer PDFs or field values. Extend the synthetic fixture generator instead.
- New compatibility behavior needs a stable rule ID and an entry in `docs/rules.md`.
- Public JSON changes require a schema-version decision and an ADR.

Open an issue before changing the contract schema, adding network access, or expanding into XFA,
signatures, flattening, or destructive PDF rewrites.

## Pull requests

Describe the failure being prevented, include the acceptance command, and confirm
`uv run python scripts/verify.py` passes. Do not add generated `output/`, secrets, private PDFs, or
`Co-authored-by` trailers for people who did not author the change.
