# Agents Remediation — Phase 3 Evidence

Date: 2026-08-02  
Baseline: verified Phase 2 checkpoint and migration `d3e5f7a9b1c2`  
Forward revision: `e4f6a8b0c2d3`

## Outcome

Phase 3 delivers the persisted-Agent execution vertical slice:

```text
Enabled persisted Agent
→ exact immutable published AgentVersion
→ saved instructions/model/planner/limits
→ assignment-constrained discovery
→ Sprint 11 Tool Executor
→ assigned tenant knowledge citations
→ durable execution/continuation/audit records
→ Agent-aware Chat or Test Console result
```

No production credentials or infrastructure were accessed. Existing Sprint 11–14 and Phase 1/2 changes were preserved; no earlier migration was rewritten.

## Architecture implemented

- `AgentExecutionService` is the canonical entry point for persisted-agent start, resume, detail, history, and cancellation.
- Every start and resume re-resolves the exact published version through `AgentApplicationService`, rechecking lifecycle, actor permission, object access, tool assignment/catalog availability, knowledge tenant/readiness, marketplace state, and execution cost/timeout controls.
- Prompt metadata records the documented precedence: platform security, runtime constraints, published Agent instructions, conversation, user request, and explicitly untrusted retrieved/tool data.
- The runtime consumes the published provider, model, planner, instructions, discovery settings, and execution limits. Invalid model/planner configuration fails closed without a silent global fallback.
- Tool selection is restricted to published Agent assignments. Discovery and ToolExecution records share Agent, conversation, execution, and correlation linkage.
- Knowledge retrieval uses only assigned, ready, same-tenant sources and emits bounded citation metadata marked `untrusted_data`.
- Structured input, clarification, and approval continuations use cryptographically random tokens while storing only SHA-256 hashes. Conditional database claims make consumption one-time and replay-safe.
- Cancellation is persisted and idempotent; pending continuations are cancelled with the execution.
- Structured immutable audit events cover start, waiting states, resume, success, failure, and cancellation without prompts or tokens.

## Models and migration

Added `agent_executions` with tenant, Agent/version, actor/service identity, conversation/workflow/discovery/parent linkage, status/phase, sanitized summaries, model/planner, selected tools, ToolExecution IDs, knowledge IDs, timing, token/cost metadata, safe errors, correlation/trace IDs, cancellation, and test-mode fields.

Added unified `agent_continuations` for input, clarification, and approval, including schema/known/missing values, safe choices, expiration, token hash, response, and consumed/cancelled timestamps.

Conversations now persist tenant, pinned Agent UUID, and pinned initial Agent version. Selecting a different Agent for an already-pinned conversation fails with an explicit switching-confirmation error.

## APIs

- `POST /api/v1/agents/{agent_id}/execute`
- `POST /api/v1/agents/{agent_id}/test`
- `GET /api/v1/agents/{agent_id}/executions`
- `GET /api/v1/agents/{agent_id}/executions/{execution_id}`
- `POST /api/v1/agents/{agent_id}/executions/{execution_id}/cancel`
- `GET /api/v1/agent-executions/{execution_id}/continuation`
- `POST /api/v1/agent-executions/{execution_id}/input`
- `POST /api/v1/agent-executions/{execution_id}/clarify`
- `POST /api/v1/agent-executions/{execution_id}/approve`
- `POST /api/v1/agent-executions/{execution_id}/deny`
- `POST /api/v1/agent-executions/{execution_id}/resume`

`POST /api/chat/start` now accepts a stable `agent_id`, validates and pins it, and delegates persisted-agent requests to `AgentExecutionService`. Unknown request fields are rejected by strict schemas.

## Chat and Test Console

- Chat loads only authorized enabled Agents from the real v1 API and sends the stable UUID.
- The selected Agent/version persists with the conversation.
- Chat renders execution completion, cancellation, schema-driven input forms, clarification choices, approval-required state, and same-execution resume behavior.
- Agent Details contains a functional Test Console backed by `/test`, not component-local mock state. It displays exact version, execution/correlation IDs, status, result, cancellation, input continuation, and approval state.
- Frontend tests cover Test Console execution linkage and schema-driven same-execution resume.

## Deployment Report flow

`DeploymentReportTool` is a registered Tool SDK implementation with a strict schema and deterministic safe report output. The verified flow selects it only when assigned, creates a durable input continuation for missing release data, resumes the same execution, reauthorizes, executes through `ToolExecutor`, and links discovery, tool execution, result, and audit history. Assignment approval can require a separate authorized approver and is replay-safe.

## Security controls verified

- Authentication dependency on every API.
- Safe same-tenant lookup and object authorization.
- Enabled/published version enforcement on start and resume.
- Assignment/catalog/marketplace rechecks after continuation.
- Cross-tenant execution safe-not-found.
- Owner-only continuation/cancellation, except separately authorized approval.
- Approver/requester separation and `agents.approve` enforcement.
- Strict request models and 50,000-character prompt bound.
- Opaque one-time continuation tokens; plaintext tokens are never stored/logged.
- Tool schema, permission, timeout, governance, idempotency, cost, and redaction remain enforced by the existing Tool Executor.
- Retrieved content is citation data, never system instructions.
- Safe structured errors contain no stack trace, prompt, credential, or provider payload.

## Principal files changed

Backend:

- `backend/app/database/models/agent_execution.py`
- `backend/alembic/versions/e4f6a8b0c2d3_agent_execution_phase3.py`
- `backend/app/agents/execution_service.py`
- `backend/app/agents/application_service.py`
- `backend/app/api/agent_executions.py`
- `backend/app/api/chat.py`
- `backend/app/models/chat.py`
- `backend/app/models/conversation.py`
- `backend/app/tool_sdk/builtin_tools.py`
- `backend/app/audit/events.py` integration
- Phase 3 service/API/migration tests

Frontend:

- `frontend/src/components/agents/AgentTestConsole.jsx`
- `frontend/src/components/agents/AgentTestConsole.test.jsx`
- `frontend/src/pages/agents/AgentDetailsPage.jsx`
- `frontend/src/pages/ChatPage.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/services/agentService.js`
- TypeScript configuration and existing typed-service corrections

Traceability rows 42, 44, 46, and 56–62 were updated in `reports/agents-screen-gap-audit-2026-08-02.md`.

## Exact verification results

| Gate | Command | Result |
|---|---|---|
| Phase 3 focused backend | `cd backend && .venv/bin/pytest -q tests/test_agent_execution_phase3.py tests/test_agent_execution_phase3_api.py tests/test_agent_phase3_migration.py` | 9 passed, 2 warnings |
| Full backend | `cd backend && .venv/bin/pytest -q` | 190 passed, 4 warnings |
| Ruff | `.venv/bin/ruff check <Phase 3 model/service/API/migration/tests>` | All checks passed |
| Mypy | `.venv/bin/mypy --follow-imports=skip app/database/models/agent_execution.py app/agents/execution_service.py app/api/agent_executions.py` | Success, 3 files |
| Migration | `env DATABASE_URL=sqlite:////private/tmp/enterprise-ai-copilot-phase3-final.sqlite .venv/bin/alembic upgrade head && ... alembic current` | `e4f6a8b0c2d3 (head)` |
| OpenAPI | Import schema and assert Phase 3 routes | 137 paths; required Phase 3 routes present |
| TypeScript | `cd frontend && npx tsc --noEmit` | Passed |
| ESLint | `npm run lint` | Passed |
| Frontend tests | `npm test -- --run` | 3 files, 6 tests passed |
| Production build | `npm run build` | Passed; existing 1.22 MB main-chunk warning |
| Diff hygiene | `git diff --check` | Passed after whitespace correction |
| Secret fallback scan | `rg` high-confidence AWS/private-key signatures excluding dependencies/build output | No matches |

The four backend warnings are existing dependency/runtime deprecations: `pythonjsonlogger`, Starlette TestClient/httpx, and two `datetime.utcnow()` uses in the legacy runtime stream tests/service.

## Classification

| Requirement | Classification |
|---|---|
| Persisted Agent → exact version → instruction/model/planner execution | Implemented and verified |
| Tool assignment discovery and Tool Executor linkage | Implemented and fake-server tested |
| Assigned knowledge retrieval/citations | Implemented and fake-server tested |
| Durable execution, status, safe errors, audit and linkage | Implemented and verified |
| Input/clarification/approval continuation and replay prevention | Implemented and verified |
| Cancellation and configured timeout | Implemented and verified |
| Agent-aware Chat and conversation pinning | Implemented and verified through API/component tests |
| Real Agent Test Console | Implemented and verified through component/API tests |
| Deployment Report workflow | Implemented and fake-server tested |
| Live AI provider behavior and live enterprise knowledge | Implemented but awaiting live credentials |
| Gitleaks binary scan | Blocked or incomplete — binary is not installed; local high-confidence scan found no matches |
| PostgreSQL-specific migration run | Blocked or incomplete — production access prohibited and no disposable PostgreSQL service supplied; SQLite forward/round-trip migration passed |
| Browser E2E/screenshots | Blocked or incomplete by Phase 3 scope; explicitly scheduled for Phase 4 |

## Remaining Phase 4 work

Phase 4 remains responsible for the full Agents administration frontend, richer execution history/details and analytics, accessibility remediation, browser E2E infrastructure and artifacts, responsive/keyboard verification, and final cross-layer audit. This report does not claim the complete Agents remediation is finished.
