# Production-readiness assessment — 2026-08-04

Verdict: **release candidate implemented; production deployment is not yet
authorized**.

## Implemented and verified locally

- Production configuration fails closed for missing database, Cognito, CORS, and
  AI provider settings; SQLite and non-TLS PostgreSQL are rejected in production.
- Startup no longer creates schema or performs catalog synchronization by default.
  Production startup verifies that the database is at the Alembic head.
- Liveness/readiness separation, database-aware readiness, trusted hosts, exact
  CORS origins, security headers, non-root container execution, pinned runtime
  dependencies, and production-only dependency installation are implemented.
- The frontend uses deployment-provided API/Cognito configuration and no longer
  logs authentication headers or response bodies in production.
- OIDC-based AWS deployment, immutable image tags, pre-deploy migrations,
  catalog initialization, deployment-circuit-breaker enforcement, health/stability
  assertions, and delayed `latest` promotion are implemented.
- Backend: `201 passed, 4 warnings in 13.75s`.
- Frontend: ESLint passed; TypeScript passed; `6 passed`; production build passed
  (`305.05 kB` entry chunk, `99.48 kB` gzip).
- Production-file Ruff, production-file mypy, workflow YAML parsing, and
  `git diff --check` passed.

## Implemented; CI fake/live-environment verification pending

- The browser workflow provisions PostgreSQL 16, applies all migrations, seeds a
  signed tenant-scoped identity, starts the real API, and exercises desktop/mobile
  Agents UI, search, persistence, accessibility, and cross-tenant denial.
- The latest local browser launch was blocked by macOS sandbox Mach-port policy
  before any page or assertion ran. A previous fixture suite run passed 6/6, but it
  is not evidence for the new live PostgreSQL gate.
- The seed contract is covered by the backend suite, including restricted file
  permissions and independently signed cross-tenant identity.

## Implemented but awaiting live credentials/platform validation

- AWS-managed RDS secret resolution, TLS connectivity, ECS migration task,
  application rollout, Cognito login, OpenAI requests, dashboard data, chat, and
  external MCP/native integrations.
- Actual ECS networking, task roles, deployment circuit breaker, alarms, load
  balancer `/ready` health check, and frontend host variables must be checked in the
  target account before release.
- The currently committed production API endpoint uses HTTP. The frontend now
  fails closed for a non-HTTPS production API; provision an ACM certificate and
  HTTPS ALB listener/custom domain, then set `VITE_API_URL` to that HTTPS endpoint.

## Blocked or incomplete

- Docker image build and target AWS inspection could not run because the execution
  approval service quota is exhausted until 2026-08-08 16:45 Africa/Cairo.
- The current-tree gitleaks report still identifies one redacted ignored
  `backend/.env` OpenAI credential. It must be revoked/rotated and removed by the
  workstation owner without exposing it. Git history scan is clean.
- Repository-wide Ruff currently reports 459 legacy findings outside the scoped
  production gate. Behavioral tests pass, but this debt prevents claiming a clean
  repository-wide static-quality baseline.
- The Chat lazy chunk is 813.83 kB (278.90 kB gzip). This is a performance backlog,
  not a correctness blocker, but should be budgeted and monitored.

Release only after every item in the last two sections has either passed in the
target environment or has an explicitly approved, time-bounded risk acceptance.
