# Failure and repair guide

Always rerun the same command after applying the smallest relevant fix.

## Exit 1 from `diff`

The gate worked and found a breaking change. Read the `ACR2xx` findings. Either restore the candidate
contract or create a plan, review every mapping, migrate representative values, and run `fill-test`.
Do not suppress exit 1 in CI unless the change has been reviewed and the baseline is deliberately
updated in the same pull request.

## `Migration plan must be explicitly reviewed`

Open the plan, verify every `from`/`to` pair against the two templates, remove incorrect proposals,
then deliberately change `"reviewed": false` to `true`. Regenerating a plan resets it to false.

## Unknown, unmapped, collision, or invalid option

- Unknown source: correct the values key or regenerate the plan from the matching baseline.
- No reviewed mapping: add the intended target after human review, or remove an obsolete value.
- Collision: two sources point at one target; choose one destination per supplied value.
- Invalid option: use an export value listed in the candidate snapshot, not its visual label.

## Duplicate name or detached widget

The candidate PDF is ambiguous. Repair it in a PDF authoring tool or request a corrected vendor
template. AcroContract will not guess which object receives data. Re-run `snapshot`, then `fill-test`.

## XFA or encrypted PDF

Version 0.1.0 cannot safely fill these surfaces. Obtain an unencrypted AcroForm export. Do not remove
security or convert a production document unless you are authorized to do so.

## Readback or appearance verification failed

Keep the source and generated output for local diagnosis, without sharing real values publicly.
Reproduce with synthetic values, inspect the field's `/V`, widget `/V` or parent value, `/AS`, and
`/AP /N`, then open a private security report or a normal issue as appropriate. A verification
failure exits 1 and must not be treated as a successful fill.

## Development gate failure

```powershell
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest -q
uv run python -m build
uv run twine check dist/*
```

Fix the first failing command, rerun it, then rerun `uv run python scripts/verify.py`. Do not disable a
rule, lower coverage, or skip a test to make the gate green.
