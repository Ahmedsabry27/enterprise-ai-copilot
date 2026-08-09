# Agents Screen and Supporting Functionality Gap Audit

Date: 2026-08-02  
Scope: Agents UI, management API, persistence, runtime wiring, tool/knowledge/permission integration, chat integration, lifecycle, execution history, analytics, security, accessibility, and automated verification.  
Method: read-only source trace, local service readiness checks, existing automated suites, static/type/build gates, and mandatory browser capability investigation. No product code, migrations, live records, credentials, or authentication configuration were changed.

## Executive summary

**Verdict: The Agents screen is a partial administration mock backed by basic CRUD persistence; it is not a production-complete agent management surface and is not connected to the actual runtime agent architecture.**

The repository contains real `/agents` and `/agents/:agentId` routes, a real authenticated CRUD API client, a database-backed `agents` table, list/create/read views, and read-only execution summaries. The implementation stops well short of the supplied product requirements: editing and lifecycle controls are absent, tool/knowledge assignments are unvalidated strings, permission switches are cosmetic configuration, chat ignores saved agents and instructions, runtime registries are separate from persisted agents, audit/activity is not implemented, list controls are largely client-only, and there is no Agents-specific UI or API test coverage.

PASS-only completion ratio: **12 / 64 = 18.8%**. This intentionally counts only `PASS`; `PARTIAL`, `MOCK-ONLY`, and `BACKEND-ONLY` are not counted as complete.

Critical release blockers:

1. Persisted agents do not register with, configure, or execute through the runtime; chat always builds from a global system prompt.
2. All agent CRUD is authenticated but lacks tenant scoping and role/permission authorization; any authenticated user can patch status or hard-delete any globally visible agent.
3. Tool, knowledge, and permission assignments are arbitrary JSON/string configuration and are not enforced at execution time.
4. No edit, lifecycle, test console, assignment management, audit history, agent-aware chat selection, or agent analytics UI exists.
5. Authenticated browser verification is blocked: the in-app browser backend is unavailable, no existing headless E2E infrastructure exists, and the repository has Cognito redirect authentication but no approved local test identity/fixture.
6. Quality gates are red despite green unit tests: Ruff 428 errors, mypy 185 errors, and frontend TypeScript configuration failure.

## Repository checkpoint

- Branch: `feature/AI-Platform`
- Commit: `94730084c555a342114a5a82ebcb558aeeabffe7`
- Initial working tree: **91 changed/untracked entries**. These pre-existing Sprint 11–14 and RDS remediation changes were preserved. The only audit artifact added is this report.
- No project-level `AGENTS.md` was found. Root README is a one-line description; frontend README is the default Vite template and does not document Agents startup, E2E, or test authentication.
- Backend documented deployment commands: `gunicorn -k uvicorn.workers.UvicornWorker ...` in `backend/Procfile`, and `uvicorn app.main:app` in `backend/Dockerfile`. Frontend package command: `npm run dev` (`vite`).

## Architecture and screen inventory

| Surface | Evidence | Finding | Classification |
|---|---|---|---|
| `/agents` route | `frontend/src/app/router.jsx:108-119` | Real route to `AgentsPage`. | PASS |
| `/agents/:agentId` route | `frontend/src/app/router.jsx:119` | Real detail route. | PASS |
| Sidebar entry | `frontend/src/components/layout/Sidebar.jsx` | Agents navigation entry exists. | PASS |
| Agents directory | `frontend/src/pages/agents/AgentsPage.jsx:9-10` | API-backed list with client search/status filter and embedded detail. | PARTIAL |
| Agent builder | `frontend/src/components/agents/AgentBuilder.jsx:2-7` | Single large form presented as six steps; only name is required and “Review & Save” directly creates. | PARTIAL |
| Full details | `frontend/src/pages/agents/AgentDetailsPage.jsx:5-7` | Six read-only local-state tabs; configuration is raw JSON. | PARTIAL |
| Edit | Client method exists at `frontend/src/services/agentService.js:6`; no control consumes it. | No edit workflow. | BACKEND-ONLY |
| Delete | Client method exists at `frontend/src/services/agentService.js:7`; no UI. Backend hard-deletes. | Unsafe backend-only operation. | SECURITY GAP |
| Lifecycle | Patch accepts arbitrary status at `backend/app/api/management.py:155-165`. | No governed enable/disable/archive workflow or UI. | BACKEND-ONLY |
| Test console | No route/component/API in Agents implementation. | Missing. | MISSING |
| Agent analytics | Only per-user execution count/success calculation in list response. | No agent analytics surface. | MISSING |
| Activity/audit | Details tab displays explanatory placeholder. | No configuration/lifecycle audit history. | UI-ONLY |

## Full traceability matrix

| # | Requirement | Evidence and result | Classification |
|---:|---|---|---|
| 1 | Agents list route exists | Router maps `/agents` to `AgentsPage`. | PASS |
| 2 | Agent details route exists | Router maps `/agents/:agentId`. | PASS |
| 3 | Agents navigation item exists | Sidebar contains the Agents destination. | PASS |
| 4 | Navigation active state rendered correctly | Source suggests route-aware layout, but no rendered browser was available. | NOT TESTED |
| 5 | Backend and frontend services ready | Escalated loopback checks returned backend 200 and frontend 200. | PASS |
| 6 | Authenticated Agents page renders | Cognito session could not be established in a browser. | BLOCKED |
| 7 | Agents load from real API in browser | Client is real, but browser network/render evidence is unavailable. | BLOCKED |
| 8 | API failure/retry state | `ResourceState` receives query error; no retry control observed. | PARTIAL |
| 9 | Frontend uses real Agents API | `agentService.js:2-7` calls real `/api/agents` endpoints. | PASS |
| 10 | Search | Implemented only by client-side `useMemo`; no server query support. | PARTIAL |
| 11 | Status filtering | Client-only exact status filter. No server filtering. | PARTIAL |
| 12 | Sorting | No sort control or backend sort contract beyond name order. | MISSING |
| 13 | Pagination | Arrow buttons at `AgentDirectory.jsx:4` have no handlers; API returns an unpaginated array. | MOCK-ONLY |
| 14 | Controlled empty state | Whole-list empty state exists; filtered zero-result state leaves a blank directory. | PARTIAL |
| 15 | Refresh preserves list state | State is component-local; browser refresh behavior not exercised. | NOT TESTED |
| 16 | Create form fields | Name, purpose, description, instructions, model, memory, tools, knowledge, permissions exist. | PARTIAL |
| 17 | Real multi-step builder | Six step labels are visual only; step 1 remains highlighted and all fields render together. | MOCK-ONLY |
| 18 | Required validation | Only HTML `required` on name; no robust validation/error associations. | PARTIAL |
| 19 | Invalid-value handling | Backend bounds only name; arbitrary models, tools, sources, permissions, and status remain accepted. | SECURITY GAP |
| 20 | Valid agent creation persistence | POST serializes configuration and commits to DB. No endpoint-specific test. | PARTIAL |
| 21 | Duplicate submission protection/idempotency | Pending disables only final button; no idempotency key or duplicate-submit API protection beyond name uniqueness. | PARTIAL |
| 22 | Creation success feedback | Form closes and cache invalidates; no explicit success notification. | PARTIAL |
| 23 | Creation error feedback | `create.isError` is not rendered by `AgentsPage`/builder. | MISSING |
| 24 | Authentication required by API | All management handlers depend on `get_current_user`. | PASS |
| 25 | Role-based create/update/delete authorization | No role/group/permission check in agent handlers. | SECURITY GAP |
| 26 | Tenant isolation | Agent model has no tenant key; all rows are queried globally. | SECURITY GAP |
| 27 | Object-level authorization | `db.get(Agent, id)` has no tenant/owner condition. | SECURITY GAP |
| 28 | Safe delete | DELETE performs immediate hard delete with no dependency check, soft delete, audit, or concurrency guard. | SECURITY GAP |
| 29 | Mass-assignment/unknown field rejection | Pydantic models do not declare `extra='forbid'`; unknown fields are not explicitly rejected. | SECURITY GAP |
| 30 | Agent DB table/model exists | `backend/app/database/models/agent.py` defines persisted agents. | PASS |
| 31 | Enterprise agent schema | Missing tenant, owner, slug, version, updated timestamps/users, lifecycle constraints, and soft-delete fields. | PARTIAL |
| 32 | Read endpoints are side-effect free | GET list/detail calls `_ensure_default_agent()` and may insert/commit. | SECURITY GAP |
| 33 | Health/status reflects runtime | Creation hard-codes `ONLINE`/`HEALTHY`; no runtime health registration occurs. | MOCK-ONLY |
| 34 | Agent details overview | Basic persisted values and user-specific execution aggregates render. | PARTIAL |
| 35 | Details deep-link error distinction | All query errors render “Agent not found,” including auth/network/server errors. | PARTIAL |
| 36 | Details tabs use URL state | Tabs are component-local and not deep-linkable. | MISSING |
| 37 | Edit and save | PATCH client/backend exist; no edit UI consumes them. | BACKEND-ONLY |
| 38 | Concurrency/version conflict handling | No ETag/version/updated-at contract. | MISSING |
| 39 | Configuration history | No version records or audit events on create/patch/delete. | MISSING |
| 40 | Tool catalog assignment | Builder uses five hard-coded display names, not Tool Registry IDs/versions. | MOCK-ONLY |
| 41 | Tool authorization and schema validation | Agent update does not validate Tool Registry existence, enabled state, permissions, or version. | SECURITY GAP |
| 42 | Tool restriction enforced at runtime | Phase 3 restricts discovery/direct execution to the exact published Agent tool assignments and rechecks catalog/marketplace state before Tool Executor invocation. | PASS |
| 43 | Knowledge assignment | Builder uses three generic hard-coded labels, not knowledge-source records. | MOCK-ONLY |
| 44 | Knowledge readiness/retrieval/removal enforcement | Phase 3 resolves only assigned tenant sources, requires readiness, records source IDs, and returns untrusted citation metadata. | PASS |
| 45 | Permission assignment UI | Boolean labels are saved in JSON and displayed read-only. | UI-ONLY |
| 46 | Permission enforcement | Relational access assignments and action permissions are enforced by AgentApplicationService at execute/resume/detail boundaries. | PASS |
| 47 | Least-privilege negative identity test | No Agents authorization tests and no browser identity fixture. | NOT TESTED |
| 48 | Low-level agent backend tests | Focused suite: 40 passed. | PASS |
| 49 | Existing frontend unit tests | Vitest: 4 passed in 2 files. They target other screens. | PASS |
| 50 | Frontend lint | `npm run lint` exited 0. | PASS |
| 51 | Frontend production build | Build exited 0; emitted a 1,218 kB main chunk warning. | PASS |
| 52 | Frontend type check | TypeScript 7 rejects removed `baseUrl` and non-relative path mapping. | REGRESSION |
| 53 | Backend full test suite | 164 passed with 4 deprecation warnings. | PASS |
| 54 | Backend lint | Ruff found 428 errors across app/tests. | REGRESSION |
| 55 | Backend type check | mypy found 185 errors in 28 files, including core agent/runtime typing defects. | REGRESSION |
| 56 | Agents-specific frontend tests | Test Console component tests cover execution linkage and schema-driven continuation/resume. | PARTIAL |
| 57 | Agents management API tests | Versioned CRUD/lifecycle/assignment/execution/continuation APIs have service and HTTP integration tests. | PASS |
| 58 | Runtime registration of persisted agents | Canonical AgentExecutionService resolves an enabled persisted Agent and exact immutable published version before every start/resume. | PASS |
| 59 | Saved instructions affect execution | Controlled Phase 3 test proves a unique harmless published instruction changes the user-visible execution result. | PASS |
| 60 | Chat agent selection | Chat loads authorized enabled Agents, sends stable UUID, and conversations pin Agent UUID/version with switch rejection. | PASS |
| 61 | Agent test console workflows | Protected Test Console uses the real execution API with version, progress/status, cancel, input continuation, approval state, result, and linkage identifiers. | PARTIAL |
| 62 | Execution details and linkage | Durable details include Agent/version, discovery, ToolExecution IDs, knowledge IDs, correlation, safe errors, duration, test mode, and continuation state. | PASS |
| 63 | Visual/keyboard/responsive/semantic accessibility audit | Interactive browser unavailable and no configured headless fallback. | BLOCKED |
| 64 | Browser screenshots/console/network artifacts | No browser session or existing E2E runner; no artifacts could be safely produced. | BLOCKED |

## UI-to-backend-to-runtime trace

```text
AgentsPage / AgentDetailsPage
        |
        v
agentService.js -> /api/agents CRUD -> SQLAlchemy Agent(configuration JSON)
                                            X
                                            X no registration/config propagation
                                            X
Chat -> ChatService -> ConversationBuilder -> global SYSTEM_PROMPT -> AI provider

Separate runtime concepts:
- app.database.models.agent.Agent: persisted management record
- app.agents.models.agent.AgentDefinition + app.agents.registry.AgentRegistry: rich in-process runtime
- app.runtime.agent_registry.AgentRegistry: hard-coded ReportingAgent/GeneralAssistantAgent stub
```

This split is the central architectural defect. The UI can create a row that looks online and healthy without creating an executable runtime agent. Patching instructions, model, tools, knowledge, permissions, or status changes only JSON/database fields; no runtime object, tool executor policy, chat prompt, or authorization decision consumes those changes.

## API and data findings

### Available agent endpoints

- `GET /api/agents`
- `GET /api/agents/{agent_id}`
- `GET /api/agents/{agent_id}/executions`
- `POST /api/agents`
- `PATCH /api/agents/{agent_id}`
- `DELETE /api/agents/{agent_id}`

Missing contracts include publish/enable/disable/archive, test execution, cancellation, configuration versions, tool assignments, knowledge assignments, access assignments, activity/audit, detailed execution records, and analytics.

### Security priorities

**P0**

- Add tenant ownership to agents and every query; enforce object-level tenant scope.
- Require explicit administrative capabilities for create/patch/delete/lifecycle/assignment operations.
- Replace arbitrary permission JSON with validated policy references and enforce them at runtime and API boundaries.
- Validate tool/source IDs and versions against tenant-authorized registries; do not trust display strings.
- Replace hard delete with governed archive/soft delete, dependency checks, concurrency protection, and immutable audit events.
- Make list/detail GET operations read-only; move default seeding to migration/bootstrap logic.

**P1**

- Reject unknown request fields; bound instruction, description, collection sizes, and nested object complexity.
- Constrain status/model/type enums and legal lifecycle transitions.
- Do not claim `ONLINE`/`HEALTHY` until runtime registration and health checks succeed.
- Avoid returning all global agents and loading all user executions into memory; paginate and aggregate in SQL.
- Distinguish 401/403/404/409/422/5xx in UI without leaking sensitive details.

No credentials, tokens, headers, or sensitive response bodies were captured in this audit.

## Browser verification attempts

The mandatory browser workflow was attempted in the required order.

| Step | Exact evidence | Result |
|---|---|---|
| Skill | Browser-control skill read completely; required in-app-browser selector used. | Completed |
| Startup commands | Backend commands confirmed from `backend/Procfile`/`backend/Dockerfile`; frontend `npm run dev` confirmed from package.json. | Completed |
| Listener check | `lsof -nP -iTCP:8000 -sTCP:LISTEN` and port 5173 showed Python and Node listeners. | Completed |
| Sandbox readiness attempt | Plain `curl` returned connection refused despite host listeners, identifying sandbox loopback isolation. | Failed with curl exit 7 |
| Host loopback readiness | Escalated `curl http://127.0.0.1:8000/health` returned HTTP 200 with healthy JSON; `curl http://127.0.0.1:5173/agents` returned HTTP 200 HTML. | Services ready; HTTP is not treated as rendered evidence |
| Browser attempt 1 | Explicit in-app selection `agent.browsers.get("iab")`. | `Browser is not available: iab` |
| Browser discovery | Bootstrap troubleshooting read; `agent.browsers.list()` returned `[]`. | No browser backend/page/window selectable |
| Authentication investigation | Frontend uses Amplify Cognito hosted redirect; backend verifies Cognito access JWT. Search found no local dev auth, credentials, stored state, fixture, or E2E login helper. | Authenticated session unavailable without an approved test identity/browser |
| Logs | Backend audit log file produced no relevant output; expected frontend audit log path did not exist. | No browser/routing failure evidenced in logs |
| Browser attempt 2 | Repeated explicit `agent.browsers.get("iab")` after readiness/auth/log checks. | `Browser is not available: iab` |
| Headless fallback discovery | Searched dependency manifests and repository files for Playwright, Cypress, Selenium, Puppeteer, E2E configs, storage state, and auth fixtures. | None configured |
| Headless fallback command | No command exists to run. Installing a browser framework is prohibited by the read-only audit instruction. | BLOCKED; no exit code because no configured runner exists |
| Artifacts | Screenshot/trace/video/console/network directory not fabricated. | No artifacts produced |

Public/unauthenticated service readiness is **verified at HTTP level only**. Public rendered UI is **BLOCKED** because no browser backend exists. Authenticated Agents workflows are **BLOCKED** additionally by the lack of an approved local/test authentication mechanism. Consequently, the required screenshots (list, empty state, create, validation, details, edit, tools, knowledge, permissions, console, input/approval states, result/history/analytics, disabled, denied, and API error) could not be produced. Console, network, keyboard, responsive viewport, focus-management, and semantic accessibility-tree checks remain `BLOCKED`, not inferred from source.

## Accessibility source review

This is not a substitute for browser verification:

- Positive: visible text is generally present for form controls and table headers are real `<th>` elements.
- Gaps: the icon-only builder close button has no accessible name; the builder is not a dialog and has no focus trap/return; tabs lack `tablist`/`tab` roles, selected state, and keyboard semantics; loading/error/save states have no live regions; required/error association is absent; status depends on color and text but details always use green styling; pagination controls have no meaningful names or disabled states; horizontal layouts rely on overflow rather than verified responsive behavior.

Classification: source-level semantic review is `PARTIAL`; keyboard, focus, accessibility-tree, announcements, contrast, and screen-reader behavior are `BLOCKED` pending a browser.

## Test and command report

| Command | Exit | Exact result |
|---|---:|---|
| `cd backend && .venv/bin/pytest -q tests/test_agent_models.py ... tests/test_dynamic_agent_selection.py` | 0 | 40 passed in 3.08s |
| `cd frontend && npm test -- --run` | 0 | 2 files passed, 4 tests passed in 2.32s |
| `cd backend && .venv/bin/pytest -q` | 0 | 164 passed, 4 warnings in 15.03s |
| `cd frontend && npm run lint` | 0 | ESLint completed with no findings |
| `cd frontend && npm run build` | 0 | Build completed in 2.74s; main JS chunk 1,218.00 kB (402.94 kB gzip), size warning |
| `cd frontend && npx tsc --noEmit` | 1 | TS5102 removed `baseUrl`; TS5090 non-relative paths |
| `cd backend && .venv/bin/ruff check app tests` | 1 | 428 errors; 144 automatically fixable plus 2 unsafe fixes |
| `cd backend && .venv/bin/mypy app` | 1 | 185 errors in 28 files |
| Agents test inventory search | 0 | No tests matched `/api/agents`, AgentsPage, AgentBuilder, AgentDirectory, AgentDetails, agentService, or useAgents |
| Browser/E2E inventory search | 0 | No configured runner/config/auth state found; therefore no legitimate E2E command exists |

Test interpretation: backend unit coverage demonstrates that several in-process agent primitives work independently. It does **not** verify the management endpoints, persisted-to-runtime propagation, tenant authorization, agent-aware chat, tool/knowledge enforcement, or browser workflows. The frontend tests target other pages and provide no Agents coverage.

## Prioritized remediation backlog

### P0 — correctness and security

1. Define one canonical Agent aggregate with tenant, owner, stable UUID/slug, version, lifecycle, timestamps, and soft-delete semantics; migrate safely.
2. Build a single application service that transactionally persists configuration, registers/updates runtime agents, validates health, and emits immutable audit events.
3. Apply tenant and object authorization to every agent read/write/execution query; add negative cross-tenant and non-admin tests.
4. Replace arbitrary tool/source/permission strings with tenant-scoped foreign-key assignments and validated versions/policies.
5. Route saved model/instructions/tool policy/knowledge policy through chat and the existing Tool Executor; prove disabled/unassigned tools cannot be discovered or executed.
6. Add governed lifecycle endpoints with legal transitions, execution rejection while disabled, optimistic concurrency, audit, and safe archive.
7. Remove database writes from GET; seed defaults through an explicit, idempotent bootstrap/migration process.

### P1 — complete product workflows

8. Implement real list query contracts: pagination, search, status/model/owner filters, sort, totals, empty results, retry, and URL state.
9. Replace the visual builder with a validated stepper/review flow backed by real model/tool/knowledge/policy data.
10. Implement edit with dirty-state protection, conflict handling, save feedback, reload persistence, and activity history.
11. Add tool and knowledge assignment screens with readiness, version drift, removal, and runtime enforcement tests.
12. Add role/group/user access management with direct API denial tests and correct hidden/disabled UI controls.
13. Add an agent test console supporting progress, cancel, clarification, input required, approval required, sanitized results, and execution links.
14. Add agent-aware Chat selection and demonstrate saved instructions, tool restrictions, and multi-turn input continuity.
15. Add execution detail and analytics endpoints/UI sourced from real telemetry, including correlation ID and sanitized errors.

### P1 — verification infrastructure

16. Add approved local test authentication and disposable test identities without weakening production Cognito enforcement.
17. Add Playwright/Cypress E2E infrastructure with storage-state fixtures, trace/video/screenshot retention, console/network failure capture, and cleanup.
18. Cover every mandatory Agents workflow, RBAC negative path, reload persistence, accessibility semantics, keyboard interactions, and desktop/tablet/mobile viewports.
19. Add Agents component/service tests and management API contract/security tests.

### P2 — quality and operability

20. Restore TypeScript, Ruff, and mypy to green and make them required CI checks.
21. Lazy-load the Agents/admin surfaces and reduce the 1.218 MB main bundle.
22. Add explicit loading/success/error live regions, semantic tabs/dialogs, accessible icon labels, focus management, and status styling.
23. Document local startup, test authentication, browser audit, seed/cleanup, and troubleshooting commands.

## Final classification

- **Implemented and verified:** routes/navigation source, real frontend API client, authentication dependency, database model existence, service readiness, backend test suite, frontend tests/lint/build.
- **Implemented but partial:** list/search/filter, builder fields, details/read-only executions, basic CRUD persistence, basic error/empty states.
- **Mock-only/UI-only:** stepper, pagination controls, hard-coded tool/knowledge choices, JSON permission switches, activity placeholder, hard-coded online/healthy state.
- **Backend-only:** PATCH and DELETE operations without corresponding governed UI workflows.
- **Blocked/not tested:** authenticated browser workflows, screenshots, console/network evidence, keyboard/responsive/accessibility-tree testing, live UI persistence, and negative identity testing.
- **Missing/security gaps:** runtime integration, agent-aware chat/instructions, governed lifecycle, enforceable tools/knowledge/permissions, tenant/RBAC isolation, audit/versioning, test console, analytics, Agents-specific tests, and E2E infrastructure.

**Final verdict: Do not accept the Agents screen as complete or production-ready. It is a visually credible, database-backed CRUD prototype with substantial architectural and authorization gaps.**
