# Agents Remediation — Phase 2 Evidence

Date: 2026-08-02  
Scope: governed lifecycle, immutable versions, tool/knowledge/access assignments, runtime enforcement, administration APIs, and forward migration.  
Baseline: Phase 1 commit `94730084c555a342114a5a82ebcb558aeeabffe7` on `feature/AI-Platform`.

## Working-tree safety

The pre-existing Sprint 11–14 working tree remained dirty and was not reset, cleaned, rebased, or overwritten. Phase 2 was implemented as additive files and targeted edits. The complete `git status --short` was captured before implementation and checked again after verification. No production infrastructure or credentials were accessed.

## Implementation

### Persistence and migration

- Added tenant-scoped `agent_tool_assignments`, `agent_knowledge_assignments`, `agent_access_assignments`, and `agent_execution_settings` models.
- Added stable tool-name/version constraints, assignment actions, enabled state, actor/timestamp provenance, and uniqueness/index constraints.
- Added user, group, role, and service access subjects with governed actions.
- Extended knowledge sources with tenant, owner, readiness, health, and synchronization metadata.
- Added forward-only Alembic revision `d3e5f7a9b1c2`, based on Phase 1 revision `c2d4e6f8a0b1`; no prior revision was rewritten.
- Preserved application loggers during in-process Alembic runs so migration tests cannot disable audit/redaction logging globally.

### Governed application service

- Centralized legal lifecycle transitions for publish, enable, disable, archive, and restore.
- Added configuration validation on publish, published-version enforcement on enable, optimistic version checks, confirmation gates, soft archive, dependency checks, immutable activity events, and cache invalidation.
- Added immutable version history retrieval.
- Added tenant-catalog validation for tool assignments and tenant/readiness validation for knowledge assignments.
- Added enforceable object-level access assignments and assignment management permissions.
- Runtime resolution revalidates database lifecycle and assigned tool/knowledge availability before returning cached state; stale or revoked authorization fails closed.

### Administration APIs

- Added explicit publish, enable, disable, archive, and restore endpoints.
- Added version list/detail and activity endpoints.
- Added explicit tool, knowledge, and access GET/PUT endpoints plus governed assignment removal.
- Request schemas reject unknown fields and expose only allow-listed writable fields.
- Tenant and object access checks remain in the shared Agent application service.

## Automated coverage

New tests cover:

- legal lifecycle flow, immutable versions, optimistic conflicts, invalid transitions, and required configuration;
- archive confirmation and dependency protection;
- tenant tool catalog/version validation and runtime failure after global tool disablement;
- tenant knowledge isolation and readiness enforcement;
- access-assignment visibility and direct edit denial;
- lifecycle, assignment, version, and activity API flows;
- migration upgrade of legacy knowledge rows, schema assertions, downgrade to Phase 1, and re-upgrade to head.

## Verification evidence

### Focused Phase 2 suite

```text
cd backend
.venv/bin/pytest -q tests/test_agent_governance_phase2.py tests/test_agents_v1_api.py tests/test_agent_application_service.py tests/test_agent_phase2_migration.py tests/test_sprint_migrations.py
19 passed, 1 warning in 5.17s
```

### Complete backend suite

```text
cd backend
.venv/bin/pytest -q
181 passed, 4 warnings in 6.90s
```

Warnings are existing dependency/runtime deprecations: Starlette `httpx` TestClient, `pythonjsonlogger` import relocation, and two `datetime.utcnow()` warnings.

### Static analysis

```text
cd backend
.venv/bin/ruff check app/database/models/agent_assignment.py app/database/models/knowledge_source.py app/agents/application_service.py app/api/agents_v1.py alembic/env.py alembic/versions/d3e5f7a9b1c2_agent_governance_assignments.py tests/test_agent_governance_phase2.py tests/test_agents_v1_api.py tests/test_agent_phase2_migration.py
All checks passed!

.venv/bin/mypy --follow-imports=skip app/database/models/agent_assignment.py app/database/models/knowledge_source.py app/agents/application_service.py app/api/agents_v1.py
Success: no issues found in 4 source files
```

### Migration smoke test

```text
cd backend
env DATABASE_URL=sqlite:////private/tmp/enterprise-ai-copilot-phase2-20260802.sqlite .venv/bin/alembic upgrade head
Running upgrade c2d4e6f8a0b1 -> d3e5f7a9b1c2, Governed agent assignments and tenant-scoped knowledge.
exit 0
```

The automated migration test additionally performs `c2d4e6f8a0b1 → head → c2d4e6f8a0b1 → head` and verifies legacy-row preservation.

## Requirement classification

| Requirement | Classification | Evidence |
|---|---|---|
| Forward models/migration for tool, knowledge, access, and execution settings | Implemented and verified | Migration smoke plus round-trip automated test |
| Assignment uniqueness, foreign keys, tenant indexes, provenance | Implemented and verified | Model/migration assertions and full suite |
| Governed lifecycle and legal transitions | Implemented and verified | Service and API lifecycle tests |
| Publish validation and immutable version history | Implemented and verified | Version/service/API tests |
| Optimistic concurrency and HTTP 409 conflicts | Implemented and verified | Negative lifecycle tests |
| Soft archive, confirmation, and dependency protection | Implemented and verified | Dependency/confirmation tests |
| Tenant-scoped tool assignments using stable registry identifiers | Implemented and fake-server tested | Local Tool Registry fixtures; no live third-party credentials required |
| Runtime failure after assigned tool is disabled globally | Implemented and verified | Runtime fail-closed test |
| Tenant-scoped knowledge assignments and readiness checks | Implemented and fake-server tested | Local tenant knowledge fixtures |
| User/group/role/service access assignments | Implemented and verified | Persistence and API tests |
| Object-access enforcement and direct API denial | Implemented and verified | Assigned-view/edit-denial tests |
| Assignment/activity administration APIs using real persistence | Implemented and verified | API integration tests |
| Live enterprise tool and knowledge providers | Implemented but awaiting live credentials | Local contracts and enforcement verified; production credentials intentionally not used |
| PostgreSQL migration execution | Blocked or incomplete | No disposable PostgreSQL service was provided; SQLite round trip and SQLAlchemy schema tests passed |
| Agent execution/chat prompt precedence, execution UI, analytics, browser accessibility | Blocked or incomplete | Scheduled for the subsequent remediation phases, outside this Phase 2 checkpoint |

## Exit assessment

Phase 2 is complete for its declared scope. All backend tests and touched-file static checks pass. No known Phase 2 correctness defect remains; the remaining work belongs to execution/runtime integration and frontend phases.
