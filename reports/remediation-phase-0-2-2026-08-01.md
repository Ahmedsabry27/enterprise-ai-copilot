# Sprints 11–14 remediation checkpoint — phases 0–2

This checkpoint records independently verified work. It is not a completion claim.

## Completed

- Removed both tracked credential sources from the current tree without reproducing the value.
- Replaced the legacy hard-coded database module with central `DATABASE_URL` configuration.
- Enabled SQLAlchemy parameter hiding and application-level DSN/log sanitization.
- Replaced authentication and health-check exception reflection with stable public errors.
- Added regression tests for API and structured-log credential redaction.
- Added a current-tree secret scanner and CI security workflow.
- Added an operator incident note covering rotation, log review, clones/artifacts, and history cleanup.
- Isolated backend tests from production infrastructure and restored workflow API compatibility.
- Fixed frontend lint errors and warnings.
- Added route-level lazy loading for Native, MCP, Discovery, Marketplace, Governance, and Analytics.
- Made the historical migrations SQLite-compatible while preserving the PostgreSQL branch.
- Added empty-to-head and Sprint-head round-trip migration tests with Sprint table assertions.
- Fixed discovery indexing so catalogs beyond 500 tools are fully traversed with a keyset cursor.
- Added a 521-tool regression test.
- Neutralized instruction-like language in untrusted tool metadata and added an adversarial test.
- Enforced assignment action and tool-version matching in governance evaluation.

## Verification

- `python3 scripts/scan_secrets.py`: 0 findings.
- `cd backend && .venv/bin/pytest -q`: 154 passed, 0 failed, 4 warnings.
- Focused Sprint/security suite: 35 passed, 0 failed.
- Migration tests: 2 passed, 0 failed.
- Discovery scale/security tests: 10 passed, 0 failed.
- Backend Sprint type check: success, 25 source files.
- Touched security-file Ruff check: passed.
- `cd frontend && npm run lint`: passed with no warnings.
- `npm test`: 4 passed, 0 failed.
- `npm run build`: passed. Main chunk reduced from 1,888.79 kB to 1,217.97 kB; administration routes emit separate chunks.

## External actions still required

- An authorized operator must revoke/rotate the exposed RDS credential and perform the incident actions in `docs/SECURITY_INCIDENT_RDS_CREDENTIAL.md`.
- Disposable PostgreSQL migration verification remains required; no production credential was or will be used.

## Traceability impact

- S14-05 moves from SECURITY GAP to PASS based on adversarial sanitization tests.
- S14-06 moves from REGRESSION to PASS based on the 521-tool traversal test.
- Overall strict PASS count moves from 34/80 (43%) to 36/80 (45%).
- Sprint 14 moves from 5/22 (23%) to 7/22 (32%).
- All other rows retain their audit classification pending their dedicated remediation phases.
