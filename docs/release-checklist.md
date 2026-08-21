# Release checklist

## Local gate

- [x] `uv lock --check`
- [x] `uv run python scripts/verify.py`
- [x] `uv run python scripts/demo.py`
- [x] Working tree is clean and tag version matches `src/acrocontract/__init__.py`.
- [x] Author, committer, shortlog, and absence of unintended co-author trailers are verified.
- [x] No secrets or private PDFs are tracked.

## Public gate

- [x] Public repository default branch is `main` and CI is green on the release commit.
- [x] Tag `v0.1.0` points at that exact commit.
- [x] GitHub Release contains wheel, sdist, and example ZIP.
- [x] A clean environment can install the wheel and run `acrocontract version`.
- [x] Public contributor list contains only intended authors.
- [x] Gmail notification is sent only after all checks above succeed.

## Rollback

This release has no hosted service, database, or package-registry mutation. If a critical defect is
found, mark the GitHub Release as a pre-release, publish a corrective patch tag, and direct users to
the last known-good release. Never rewrite an already published tag.
