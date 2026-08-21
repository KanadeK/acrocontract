# ADR-0001: Treat AcroForm as a contract graph

## Status

Accepted

## Date

2026-08-12

## Context

PDF page rendering, the canonical `/AcroForm/Fields` tree, and per-page `/Widget` annotations can disagree. High-level field APIs may collapse duplicate fully-qualified names, while visual comparison cannot reveal changed export values or a detached field that still looks normal.

## Decision

AcroContract will build a bounded graph from both the field tree and page widgets, then normalize that graph into a deterministic immutable contract. All lint, diff, rename, migration, and receipt behavior consumes the normalized contract rather than live pypdf objects.

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
- Malformed/cyclic structures require explicit traversal limits and incomplete verdicts.
- XFA can be inventoried without falsely claiming semantic support.
