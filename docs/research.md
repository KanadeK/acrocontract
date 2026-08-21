# Research and differentiation

## Result

AcroContract was chosen after inventorying the existing local project portfolio and previously
discussed ideas, then searching GitHub for direct and adjacent projects. The local inventory already
contained many scanners, diff tools, release checkers, data validators, and earlier repository ideas,
so those categories were rejected to avoid repetition.

As of 2026-08-21, the searches below did not find a publicly discoverable project covering this full
workflow:

```text
stable AcroForm contract snapshot
  -> semantic breaking-change diff
  -> explainable cross-version rename proposal
  -> explicitly reviewed value migration
  -> write, reopen, field/widget/appearance verification
```

This is evidence of a search gap, not proof that nobody has ever built similar private code.

## GitHub search method

Repository searches included `acroform schema diff`, `pdf form breaking changes`, `acroform contract
test`, `pdf form migration fields`, `pdf form validator`, `acroform fields`, and `pdf form filler`.
The first four direct-scope queries returned no repositories through GitHub search on the date above.
Adjacent results were inspected by repository description and README.

Star counts below are a dated snapshot and will change.

| Project | Stars on 2026-08-21 | What it does | Boundary from AcroContract |
|---|---:|---|---|
| [AcroForge](https://github.com/Lzcorp-Solutions/acroforge) | 1 | Infers semantic names, asks for human review, then relabels a single PDF | Does not version contracts or classify cross-version breaking changes; its apply path changes PDF field identities |
| [pdf-form-validator](https://github.com/bbulson/pdf-form-validator) | 0 | Populates PDFs and produces annotated visual audit outputs in CI | Validates one fill run visually; no stable contract, semantic version diff, or reviewed cross-version value migration |
| [pdfforms](https://github.com/altaurog/pdfforms) | 63 | Populates forms from spreadsheet data and generates field-ID test PDFs | Filling workflow, not a template compatibility gate |
| [pdf-form-filler](https://github.com/WestHealth/pdf-form-filler) | 16 | Python library for automated PDF filling | Filling library, not version-diff and readback-proof tooling |

## Technical source

The implementation follows the official
[pypdf form documentation](https://pypdf.readthedocs.io/en/latest/user/forms.html): canonical fields
come from `/AcroForm/Fields`, while page `/Widget` annotations must also be inspected because the two
representations do not always point to the same object. The same documentation recommends
`auto_regenerate=False` when updating fields; AcroContract additionally reopens and verifies the
written output.

## Why it may earn attention

- The failure is expensive and easy to demonstrate: an unchanged-looking vendor form can break RPA.
- The two tiny synthetic PDFs reproduce the problem without accounts, services, or private data.
- Stable JSON and exit codes fit GitHub Actions and other CI systems.
- The local-only and review-first design is suitable for government, legal, HR, and health forms.

These factors improve discoverability and usefulness; stars and traffic cannot be guaranteed.
