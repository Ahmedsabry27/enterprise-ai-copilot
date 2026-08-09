# Agents Remediation — Phase 1 Checkpoint

Date: 2026-08-02  
Baseline: `feature/AI-Platform` at `94730084c555a342114a5a82ebcb558aeeabffe7` with 91 pre-existing modified/untracked entries. No resets, cleanups, or destructive source-control operations were used.

## Outcome

Phase 1 is implemented and verified: a canonical tenant-scoped persisted Agent aggregate, immutable configuration versions, activity events, explicit authorization, optimistic concurrency, bounded runtime resolution/cache, forward data migration, and versioned `/api/v1/agents` CRUD now exist. Legacy agent reads are tenant-scoped, legacy writes delegate to the application service, GET-time default seeding is removed, and legacy hard delete is disabled.

This checkpoint does not claim the entire 15-phase remediation is complete. Governed publish/enable/disable/archive, relational tool/knowledge/access assignments, agent-aware Chat, Test Console, the complete frontend, analytics, and browser E2E belong to the following requested phases.

## Requirements completed

- Stable external UUID while retaining the legacy integer key internally for compatibility.
- Tenant/workspace ID, stable tenant-scoped slug, owner, lifecycle status, separate operational health, version pointers, model/planner/memory references, execution/risk/environment limits, actor/timestamps, archive/delete metadata, and optimistic lock version.
- Immutable `AgentVersion` snapshots containing instructions, model, planner, memory, execution limits, tool-discovery configuration, change note, actor, timestamp, and published marker.
- Append-only `AgentActivityEvent` records for creates and updates.
- `AgentApplicationService` is the controller boundary for create/list/get/update and executable runtime resolution.
- Database-backed runtime definitions load exact published instructions/model/planner/limits and fail closed unless the agent is enabled and its requested version is the published version.
- Runtime cache is bounded to 256 entries, keyed by tenant/UUID/version, and invalidated on update.
- List and detail are tenant-scoped; cross-tenant IDs return safe 404.
- Explicit `agents.list`, `agents.read`, `agents.create`, `agents.update`, `agents.execute`, and `agents.executions.read` enforcement with platform-admin compatibility.
- Owners can edit their own agents; other actors need update permission.
- Unknown request fields and oversized instructions are rejected.
- PATCH requires `If-Match`; stale updates return HTTP 409.
- Server-side list search, lifecycle status, owner, pagination, stable sort, archived inclusion, and permission-aware owner visibility.
- No automatic `ONLINE`/`HEALTHY`; new records are `draft` with `unknown` operational health.
- Legacy GET no longer inserts a default agent. Legacy hard DELETE now returns 405.

## Files changed

- `backend/app/database/models/agent.py`
- `backend/app/database/models/__init__.py`
- `backend/alembic/versions/c2d4e6f8a0b1_canonical_agents_phase1.py`
- `backend/app/agents/application_service.py`
- `backend/app/api/agents_v1.py`
- `backend/app/api/management.py`
- `backend/app/main.py`
- `backend/tests/conftest.py`
- `backend/tests/test_agent_application_service.py`
- `backend/tests/test_agents_v1_api.py`

## Migration

Forward revision: `c2d4e6f8a0b1`, following `b1c3d5e7f9a2`.

Migration behavior:

- Existing integer IDs are preserved.
- Each existing agent receives a generated stable UUID and collision-safe slug.
- Existing rows are explicitly assigned to tenant `default`; this is the documented legacy migration rule.
- Legacy status maps to `enabled` only for `online`, `ready`, or `enabled`; all other values map to `draft`.
- Existing operational health is preserved separately and normalized to lowercase.
- Legacy configuration is converted into version 1 without dropping unknown keys.
- Invalid legacy JSON is preserved as `legacy_configuration` with a safe migration diagnostic.
- Existing tool display strings are retained only as `legacy_tools` diagnostic configuration for later validated assignment migration.
- Downgrade removes only Phase 1 tables/columns and was verified through the existing round-trip test.

Production/RDS was deliberately not migrated because the request prohibits production credentials/infrastructure for this implementation phase. Disposable SQLite migration verification was used.

## Exact verification

| Command | Exit | Result |
|---|---:|---|
| `cd backend && .venv/bin/pytest -q tests/test_agent_application_service.py tests/test_agent_persistence.py tests/test_agent_models.py` | 0 | 12 passed in 0.94s |
| `cd backend && .venv/bin/pytest -q tests/test_sprint_migrations.py tests/test_agent_application_service.py` | 0 | 8 passed in 1.43s after correcting downgrade constraint ordering |
| Disposable `alembic upgrade head` + `alembic current` | 0 | `c2d4e6f8a0b1 (head)` |
| `cd backend && .venv/bin/pytest -q tests/test_agent_application_service.py tests/test_agents_v1_api.py tests/test_sprint_migrations.py` | 0 | 11 passed, 1 dependency deprecation warning in 2.24s |
| `cd backend && .venv/bin/pytest -q` | 0 | 173 passed, 4 warnings in 22.31s |
| Ruff on new Phase 1 model/service/API/migration/tests | 0 | All checks passed |
| `mypy --follow-imports=skip` on Phase 1 model/service/API | 0 | Success, no issues in 3 source files |
| OpenAPI import/assertion | 0 | 114 paths; `/api/v1/agents` and `/api/v1/agents/{agent_id}` present |

Repository-wide Ruff/mypy remain red from the audited legacy baseline and are scheduled for the requested incremental Phase 15 cleanup. No ignore rule or weakened global configuration was added.

## Phase 1 traceability improvement

| Audit row | Previous | Phase 1 evidence | New classification | Remaining limitation |
|---:|---|---|---|---|
| 10 Search | PARTIAL | Server-side name/slug/description search in v1 list, API tests. | PASS | Frontend still uses legacy client search until Phase 4. |
| 11 Status filtering | PARTIAL | Validated lifecycle status filter in v1 API. | PASS | Frontend wiring remains. |
| 12 Sorting | MISSING | Stable updated-time/UUID server sort. | PARTIAL | User-selectable sort fields come with complete frontend phase. |
| 13 Pagination | MOCK-ONLY | Server page/page-size/total/pages contract. | BACKEND-ONLY | Frontend controls remain unwired. |
| 19 Invalid values | SECURITY GAP | Extra fields forbidden; key string/list bounds introduced. | PARTIAL | Model/provider/planner registries and nested limits remain Phase 5. |
| 20 Creation persistence | PARTIAL | Service/API persistence, version, audit, and endpoint tests. | PASS | Browser persistence remains untested. |
| 24 Authentication | PASS | Cognito dependency retained. | PASS | None for Phase 1. |
| 25 Role authorization | SECURITY GAP | Explicit permissions and admin group mapping on v1 and legacy compatibility routes. | PARTIAL | Full action matrix/lifecycle/assignments arrive in Phase 2. |
| 26 Tenant isolation | SECURITY GAP | Every Phase 1 query scoped by tenant; negative cross-tenant service/API tests. | PASS | Later assignment/execution endpoints must use the same boundary. |
| 27 Object authorization | SECURITY GAP | Safe tenant lookup plus owner/update rules. | PASS | Access-assignment policies arrive in Phase 2. |
| 28 Safe delete | SECURITY GAP | Legacy hard delete disabled. | PARTIAL | Governed archive/dependency checks arrive in Phase 2. |
| 29 Mass assignment | SECURITY GAP | `extra='forbid'`; allowlisted service updates. | PASS | Nested registry validation remains. |
| 30 Agent model | PASS | Expanded canonical aggregate plus immutable version/activity models. | PASS | Assignment relations arrive in Phase 2. |
| 31 Enterprise schema | PARTIAL | UUID/tenant/slug/owner/lifecycle/version/timestamps/soft-delete/concurrency added. | PASS | Execution linkage and assignment tables remain. |
| 32 Side-effect-free reads | SECURITY GAP | GET-time default seeding removed. | PASS | Explicit optional bootstrap command remains to be added if default behavior is required. |
| 33 Honest health | MOCK-ONLY | Draft/unknown defaults; lifecycle separated from operational health. | PASS | Health producer/telemetry integration is a later phase. |
| 38 Concurrency | MISSING | Required `If-Match`, lock version, HTTP 409 test. | PASS | Frontend conflict UI remains. |
| 39 Configuration history | MISSING | Immutable version snapshots and activity events on create/update. | PARTIAL | Publish/lifecycle/assignment events remain Phase 2. |
| 47 Negative identity tests | NOT TESTED | Missing permission and cross-tenant tests added. | PARTIAL | Browser/multi-role matrix remains Phase 5. |
| 53 Full backend suite | PASS | Expanded suite 173 passed. | PASS | Warnings remain. |
| 57 Agents API tests | MISSING | v1 CRUD/validation/concurrency/tenant tests added. | PARTIAL | Lifecycle/assignment/execution endpoints remain. |
| 58 Runtime registration | MISSING | Published DB version resolves to `AgentDefinition`; bounded cache and fail-closed lifecycle tests. | PARTIAL | Runtime execution and multi-worker invalidation transport remain. |
| 59 Instructions used | MISSING | Published instructions are present in resolved runtime metadata and tested. | PARTIAL | Chat consumption is Phase 3. |

PASS-only whole-audit ratio is not recalculated as final yet because the untouched frontend/browser and later backend phases remain open. On the affected rows above, 10 rows are now PASS, 9 PARTIAL, 1 BACKEND-ONLY, with prior PASS rows preserved.

## Next phase

Phase 2: governed lifecycle and immutable publishing, relational tool/knowledge/access assignments, validation against the real tenant registries, assignment APIs, dependency-aware soft archive, full audit events, and negative authorization tests.
