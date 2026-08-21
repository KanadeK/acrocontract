# Release checklist

## Local gate

- [ ] `uv lock --check`
- [ ] `uv run python scripts/verify.py`
- [ ] `uv run python scripts/demo.py`
- [ ] Working tree is clean and tag version matches `src/acrocontract/__init__.py`.
- [ ] Author, committer, shortlog, and absence of unintended co-author trailers are verified.
- [ ] No secrets or private PDFs are tracked.

## Public gate

- [ ] Public repository default branch is `main` and CI is green on the release commit.
- [ ] Tag `v0.1.0` points at that exact commit.
- [ ] GitHub Release contains wheel, sdist, and example ZIP.
- [ ] A clean environment can install the wheel and run `acrocontract version`.
- [ ] Public contributor list contains only intended authors.
- [ ] Gmail notification is sent only after all checks above succeed.

## Rollback

This release has no hosted service, database, or package-registry mutation. If a critical defect is
found, mark the GitHub Release as a pre-release, publish a corrective patch tag, and direct users to
the last known-good release. Never rewrite an already published tag.
