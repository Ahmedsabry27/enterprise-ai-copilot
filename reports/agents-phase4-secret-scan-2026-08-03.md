# Phase 4 secret-scan report

Scanner: gitleaks 8.30.1 with `.gitleaks.toml`.

- Git-history scan: exit 0, 50 commits, zero findings.
- Current-tree scan: exit 1, one high-confidence OpenAI API key finding in ignored local file `backend/.env`, line 1.
- The secret value was redacted and was never printed or copied into a report.
- CI now enforces gitleaks current-content and history scans using pinned container version 8.30.0.
- The existing narrow synthetic-redaction-test allowlist remains; no broad baseline was added.

Required operator action: rotate/revoke the detected local credential, replace it through the approved secret injector, and remove it from the workstation file. Codex did not delete or expose the user's local environment file.
