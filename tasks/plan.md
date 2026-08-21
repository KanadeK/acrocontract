# Implementation Plan: AcroContract 0.1.0

## Overview

Build the highest-risk evidence path first: generate controlled PDFs, inspect both field and widget graphs, and prove deterministic compatibility output. Add reviewed value migration and write/reopen verification only after that contract is stable. Finish with documentation, packaging, security review, CI, GitHub publication, release asset verification, contributor audit, and Gmail notification.

## Architecture Decisions

- Python provides a small cross-platform CLI and mature low-level PDF access through pypdf.
- The immutable contract model is the boundary between unsafe PDF parsing and pure deterministic comparison/reporting.
- Rename detection is advisory; a migration plan is a separate reviewed artifact.
- Reports share one finding model so console, JSON, and Markdown cannot disagree.
- Example PDFs are generated from code and committed because they are both documentation and integration fixtures.

## Dependency Graph

```text
fixture generator
  -> inspector + contract model
      -> compatibility diff
          -> rename proposals
              -> reviewed migration plan
                  -> value migration
                      -> fill + reopen verification
  -> shared finding model -> console/JSON/Markdown
  -> CLI -> packaging -> CI/release -> online verification -> Gmail
```

## Task List

### Phase 1: Contract foundation

- [x] Task 1: Scaffold package, fixture generator, and failing contract tests.
- [x] Task 2: Implement field-tree and widget-graph inspection.
- [x] Task 3: Stabilize canonical contract serialization and snapshot CLI.

### Checkpoint: Foundation

- [x] Generated v1 fixture renders cleanly.
- [x] Snapshot is deterministic and records both fields and widgets.
- [x] Focused and full tests pass.

### Phase 2: Compatibility gate

- [x] Task 4: Implement shared findings and field/widget compatibility rules.
- [x] Task 5: Implement explainable rename proposals and diff/plan CLI.
- [x] Task 6: Implement JSON, Markdown, and console renderers.

### Checkpoint: Compatibility

- [x] Deliberately broken v2 fixture yields expected stable breaking findings.
- [x] CLI exit codes match the public contract.
- [x] Reports contain identical rule IDs and severities.

### Phase 3: Migration proof

- [x] Task 7: Implement reviewed migration-plan validation and value migration.
- [x] Task 8: Implement safe fill, reopen, field/widget readback, and value-free report generation.
- [x] Task 9: Cover the end-to-end CLI flow.

### Checkpoint: End-to-end

- [x] Example values migrate only through a reviewed plan.
- [x] Filled PDF reopens with canonical and widget values intact.

### Phase 4: Ship

- [x] Task 10: Write README, research report, ADR, rule catalog, examples, contributing, security, and repair guide.
- [x] Task 11: Add verification/demo scripts, license, changelog, and packaging metadata.
- [x] Task 12: Add CI and release workflows.
- [ ] Task 13: Review only the changed code for correctness, security boundaries, and unnecessary complexity.
- [ ] Task 14: Commit atomic increments and perform author/secret/contributor preflight.
- [ ] Task 15: Create public GitHub repository, push, verify CI, tag, create Release, and smoke-test its install path.
- [ ] Task 16: Send Gmail self-notification with verified public links and acceptance commands.

### Checkpoint: Complete

- [ ] All SPEC success criteria are met.
- [ ] Public release assets match the local manifest.
- [ ] Online contributor history contains only the intended author.
- [ ] Gmail notification was sent after publication verification.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `get_fields()` hides duplicate/widget problems | High | Traverse `/Fields`, `/Kids`, and page `/Annots` by indirect identity |
| Rename heuristics create false confidence | High | Advisory only; include scores/reasons; require reviewed plan |
| Appearance streams disagree with values | High | Reopen and verify canonical/effective values plus `/AP /N` |
| Malformed PDFs contain cyclic structures | High | Parent and field-tree cycle detection with explicit inspection failure |
| Reports leak real form values or paths | Medium | Redact values by default; store hashes and basenames only |
| Packaging drifts | Medium | Build and install-test the wheel and sdist in CI |
| GitHub rate/auth/network failures | Medium | Real-time auth check, HTTP/1.1 fallback, online verification before completion |

## Open Questions

None block 0.1.0. The deferred surfaces in SPEC.md remain explicitly unsupported.
