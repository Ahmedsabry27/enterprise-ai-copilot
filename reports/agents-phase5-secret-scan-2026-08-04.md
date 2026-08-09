# Phase 5 secret-scan report

- Current tree: exit 1; one finding; report is redacted.
- Git history: exit 0; zero findings.
- Artifacts: `reports/phase5-artifacts/gitleaks-current.json` and `gitleaks-history.json`.
- **BLOCKED — external operator action required:** revoke/rotate the ignored local credential, replace it through approved injection, remove the compromised value from `backend/.env`, then rerun the current-tree scan.
- No credential value was displayed, copied, used, deleted, baselined, or allowlisted.

