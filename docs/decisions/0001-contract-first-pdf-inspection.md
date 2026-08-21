# ADR-0001: Treat AcroForm as a contract graph

## Status

Accepted

## Date

2026-08-21

## Context

PDF page rendering, the canonical `/AcroForm/Fields` tree, and per-page `/Widget` annotations can disagree. High-level field APIs may collapse duplicate fully-qualified names, while visual comparison cannot reveal changed export values or a detached field that still looks normal.

## Decision

AcroContract builds a normalized view from both the field tree and page widgets, then turns it into a deterministic immutable contract. Diff, rename, migration, and fill verification consume that contract rather than retaining live pypdf objects.

Renames remain proposals until a human-reviewed mapping is supplied. A successful PNG render is supporting evidence only; write verification reopens the PDF and checks both canonical and effective widget values.

## Alternatives Considered

### Compare only `PdfReader.get_fields()`

Rejected because it can hide duplicate names and does not by itself establish page/widget placement or effective inherited values.

### Compare rendered pages

Rejected because it is noisy for harmless artwork changes and blind to machine-facing type, flags, choice exports, actions, and field identity.

### Automatically rename and rewrite the candidate PDF

Rejected because a plausible heuristic can still route sensitive data to the wrong field. Version 0.1.0 produces a plan and migrates external values; it never silently rewrites field identities.

## Consequences

- Inspection is more complex but findings have object-level evidence.
- Pure comparison and report code stays deterministic and easy to test.
- Cyclic parent or field structures fail inspection instead of being followed indefinitely.
- XFA can be inventoried without falsely claiming semantic support.
