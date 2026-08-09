# Final 64-row Agents traceability matrix

Date: 2026-08-03. `O` is the original audit classification; P1–P4 are checkpoint classifications. Evidence abbreviations: `A` = `backend/app/api/agents_v1.py`; `E` = `backend/app/api/agent_executions.py`; `S` = Agent application/execution services; `F` = Agents React pages/components/services; `B` = `frontend/e2e/agents.spec.ts`; `T` = backend/frontend automated suites; `DB` = canonical migrations/models. A PASS is awarded only where execution evidence exists.

|#|Requirement|O|P1|P2|P3|P4|Files|API evidence|Database evidence|Runtime evidence|Frontend evidence|Browser evidence|Test evidence|Remaining limitation|Final status|
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1|List route|PASS|PASS|PASS|PASS|PASS|F|GET list|DB|S|route|rendered|T/B|none|PASS — Implemented and verified|
|2|Details route|PASS|PASS|PASS|PASS|PASS|F|GET detail|DB|S|route|rendered|T/B|none|PASS — Implemented and verified|
|3|Navigation|PASS|PASS|PASS|PASS|PASS|layout/router|n/a|n/a|n/a|sidebar|rendered|B|mobile sidebar hidden|PASS — Implemented and verified|
|4|Active navigation|NOT TESTED|PARTIAL|PARTIAL|PARTIAL|PARTIAL|layout|n/a|n/a|n/a|route aware|not asserted|source|explicit active-state assertion|PARTIAL — Implemented but incomplete|
|5|Services ready|PASS|PASS|PASS|PASS|PASS|main/Vite|OpenAPI|Postgres|startup|build|Playwright server|T/B|none|PASS — Implemented and verified|
|6|Authenticated render|BLOCKED|PARTIAL|PARTIAL|PASS|PASS|auth/e2e.py,F|Bearer auth|tenant claims|signed identity|E2E mode|rendered|auth tests/B|Cognito live not used|PASS — Implemented and verified|
|7|Real API load|BLOCKED|PASS|PASS|PASS|PARTIAL|A,F|real API|DB|S|React Query|contract fixture|T/B|live-backend browser absent|PARTIAL — Implemented but incomplete|
|8|Failure/retry|PARTIAL|PARTIAL|PARTIAL|PARTIAL|PARTIAL|F|error statuses|n/a|n/a|retry|not automated|source|error simulation pending|PARTIAL — Implemented but incomplete|
|9|Real API client|PASS|PASS|PASS|PASS|PASS|agentService|v1 endpoints|DB|S|all actions wired|network fixtures|T/B|none|PASS — Implemented and verified|
|10|Search|PARTIAL|PASS|PASS|PASS|PASS|A,F|server search|indexed DB query|n/a|URL state|asserted|T/B|debounce depth limited|PASS — Implemented and verified|
|11|Lifecycle filter|PARTIAL|PASS|PASS|PASS|PASS|A,F|server status|DB enum|n/a|URL filter|fixture coverage|T/B|none|PASS — Implemented and verified|
|12|Sorting|MISSING|PASS|PASS|PASS|PASS|A,F|allowlisted stable sort|SQL order|n/a|URL controls|directory render|T/B|browser sort click not covered|PASS — Implemented and verified|
|13|Pagination|MOCK-ONLY|PASS|PASS|PASS|PASS|A,F|page/page_size/totals|limit/offset|n/a|disabled names|rendered|T/B|multi-page UI scenario pending|PASS — Implemented and verified|
|14|Empty states|PARTIAL|PASS|PASS|PASS|PASS|F|zero items|n/a|n/a|whole/filtered|asserted screenshot|B|none|PASS — Implemented and verified|
|15|Refresh URL state|NOT TESTED|PARTIAL|PARTIAL|PARTIAL|PARTIAL|F|refetch|n/a|cache|query params|URL asserted|B|reload assertion incomplete|PARTIAL — Implemented but incomplete|
|16|Builder fields|PARTIAL|PASS|PASS|PASS|PASS|Builder,A|capability options|DB catalogs|assignment validation|six steps|not fully captured|T/source|full browser create pending|PARTIAL — Implemented but incomplete|
|17|Real stepper|MOCK-ONLY|PARTIAL|PARTIAL|PARTIAL|PASS|Builder|create/lifecycle|DB|S|Back/Next/review|not automated|source/build|browser step screenshots pending|PARTIAL — Implemented but incomplete|
|18|Validation|PARTIAL|PASS|PASS|PASS|PARTIAL|Builder/A|422 contract|constraints|validation|step guards|not automated|backend tests|field mapping incomplete|PARTIAL — Implemented but incomplete|
|19|Invalid values|SECURITY GAP|PASS|PASS|PASS|PASS|schemas/S|forbid/enums|FK/unique|registry/readiness|errors|not automated|194 tests|none material|PASS — Implemented and verified|
|20|Create persistence|PARTIAL|PASS|PASS|PASS|PASS|A/S|POST|Agent/version|cache|draft save|not automated|API tests|none|PASS — Implemented and verified|
|21|Duplicate submit|PARTIAL|PARTIAL|PARTIAL|PARTIAL|PARTIAL|Builder/DB|pending guard|unique slug|transaction|disabled pending|not automated|source|idempotency key absent|PARTIAL — Implemented but incomplete|
|22|Success feedback|PARTIAL|PASS|PASS|PASS|PARTIAL|Builder|mutation response|persisted|refresh|explicit message|not automated|source|toast/link depth|PARTIAL — Implemented but incomplete|
|23|Create errors|MISSING|PASS|PASS|PASS|PARTIAL|Builder|422/general|constraints|n/a|visible general error|not automated|source|field mapping breadth|PARTIAL — Implemented but incomplete|
|24|Authentication|PASS|PASS|PASS|PASS|PASS|dependencies/e2e|Bearer|tenant|claims|token attach|signed mode|auth tests|none|PASS — Implemented and verified|
|25|Role authorization|SECURITY GAP|PASS|PASS|PASS|PASS|S/A|permission gates|access rows|action check|controls|not identity-E2E|negative API tests|browser identity matrix|PARTIAL — Implemented but incomplete|
|26|Tenant isolation|SECURITY GAP|PASS|PASS|PASS|PASS|DB/S/A/E|tenant predicates|tenant FK/data|tenant resolution|scoped results|not cross-tenant browser|backend negatives|browser matrix pending|PASS — Implemented and verified|
|27|Object authorization|SECURITY GAP|PASS|PASS|PASS|PASS|S/E|object gates|access assignments|action evaluation|permission states|not full browser|backend tests|none material|PASS — Implemented and verified|
|28|Safe delete/archive|SECURITY GAP|PASS|PASS|PASS|PASS|S/A|archive/restore|soft lifecycle|execution rejection|confirm controls|not automated|lifecycle tests|hard-delete wrapper remains unused|PARTIAL — Implemented but incomplete|
|29|Unknown-field rejection|SECURITY GAP|PASS|PASS|PASS|PASS|A schemas|extra forbid|n/a|n/a|safe errors|n/a|API tests|none|PASS — Implemented and verified|
|30|Canonical schema|PASS|PASS|PASS|PASS|PASS|DB|n/a|Postgres verified|S|real fields|rendered|PG/T/B|none|PASS — Implemented and verified|
|31|Enterprise schema depth|PARTIAL|PASS|PASS|PASS|PASS|DB|full DTO|versions/tenant/owner|S|displayed|rendered|PG/T/B|none|PASS — Implemented and verified|
|32|GET side-effect free|SECURITY GAP|PASS|PASS|PASS|PASS|S/A|read-only GET|no seed writes|cache reads|n/a|n/a|tests|none|PASS — Implemented and verified|
|33|Operational health|MOCK-ONLY|PARTIAL|PASS|PASS|PASS|DB/S|serialized health|persisted|runtime invalidation|real value|rendered|tests/B|provider live health separate|PASS — Implemented and verified|
|34|Overview|PARTIAL|PASS|PASS|PASS|PASS|Details/A|GET detail|DB|version/runtime|cards|rendered|B|none|PASS — Implemented and verified|
|35|Error distinction|PARTIAL|PASS|PASS|PASS|PARTIAL|Details|status branches|n/a|n/a|401/403/404/409/429/5xx/network|not automated|source|422 mapping limited|PARTIAL — Implemented but incomplete|
|36|URL tabs|MISSING|PASS|PASS|PASS|PASS|Details/router|tab data APIs|DB|n/a|13 semantic tabs|keyboard/URL asserted|B|none|PASS — Implemented and verified|
|37|Edit/save|BACKEND-ONLY|PASS|PASS|PASS|PARTIAL|Details/A/S|PATCH If-Match|new draft version|cache invalidation|edit forms|not automated|backend tests|browser persistence pending|PARTIAL — Implemented but incomplete|
|38|Conflict handling|MISSING|PASS|PASS|PASS|PARTIAL|Details/S|409 lock|lock_version|no overwrite|clear reload text|not automated|backend tests|browser conflict flow|PARTIAL — Implemented but incomplete|
|39|History|MISSING|PASS|PASS|PASS|PASS|A/S/Details|versions/activity|immutable rows|events|tabs|rendered empty|backend tests|browser populated history|PARTIAL — Implemented but incomplete|
|40|Tool catalog assignment|MOCK-ONLY|PASS|PASS|PASS|PARTIAL|A/S/Details|real options/assignments|Tool FK/name|discovery invalidation|add/remove|not automated|backend tests|advanced fields/filters|PARTIAL — Implemented but incomplete|
|41|Tool validation|SECURITY GAP|PASS|PASS|PASS|PASS|S|registry validation|catalog|runtime recheck|warnings basic|n/a|backend tests|none material|PASS — Implemented and verified|
|42|Tool enforcement|PASS|PASS|PASS|PASS|PASS|execution S|discovery/executor|assignments|governed execution|Test Console|Phase3 evidence|194 tests|none|PASS — Implemented and verified|
|43|Knowledge assignment|MOCK-ONLY|PASS|PASS|PASS|PARTIAL|A/S/Details|real options|source FK|retrieval restriction|add/remove|not automated|backend tests|metadata cards shallow|PARTIAL — Implemented but incomplete|
|44|Knowledge enforcement|PASS|PASS|PASS|PASS|PASS|execution S|resume/execute|tenant ready FK|citations|Test Console|Phase3 evidence|194 tests|none|PASS — Implemented and verified|
|45|Access UI|UI-ONLY|PASS|PASS|PASS|PARTIAL|A/S/Details|assignment API|access rows|effective checks|subject/action editor|not automated|backend tests|deny/approval preview UI|PARTIAL — Implemented but incomplete|
|46|Permission enforcement|PASS|PASS|PASS|PASS|PASS|S/E|action gates|access rows|runtime deny|permission controls|not full identity UI|negative tests|none material|PASS — Implemented and verified|
|47|Least-privilege identity|NOT TESTED|PASS|PASS|PASS|PARTIAL|auth/S|signed roles supported|tenant/access|denials|states|not matrix|backend negatives|six-identity browser suite|PARTIAL — Implemented but incomplete|
|48|Backend focused tests|PASS|PASS|PASS|PASS|PASS|tests|API/service|SQLite/PG migrations|runtime|n/a|n/a|10 focused; 194 full|none|PASS — Implemented and verified|
|49|Frontend tests|PASS|PASS|PASS|PASS|PASS|frontend tests|contracts|n/a|n/a|components|n/a|6 passed|coverage breadth|PARTIAL — Implemented but incomplete|
|50|Frontend lint|PASS|PASS|PASS|PASS|PASS|frontend|n/a|n/a|n/a|ESLint|n/a|exit 0|none|PASS — Implemented and verified|
|51|Production build|PASS|PASS|PASS|PASS|PASS|router/build|n/a|n/a|n/a|lazy routes|browser server|exit 0|main chunk warning|PASS — Implemented and verified|
|52|TypeScript|REGRESSION|PASS|PASS|PASS|PASS|frontend|n/a|n/a|n/a|tsc|n/a|exit 0|none|PASS — Implemented and verified|
|53|Full backend|PASS|PASS|PASS|PASS|PASS|backend|139 paths|SQLite+PG migration|runtime|n/a|n/a|194 passed|warnings only|PASS — Implemented and verified|
|54|Backend lint|REGRESSION|PARTIAL|PARTIAL|PASS|PASS|touched files|n/a|n/a|n/a|n/a|n/a|Ruff exit 0|repo-wide baseline not rerun green|PASS — Implemented and verified|
|55|Backend typing|REGRESSION|PARTIAL|PARTIAL|PASS|PASS|touched files|typed APIs|typed models|typed services|n/a|n/a|mypy exact exit 0|repository-wide baseline errors exist|PASS — Implemented and verified|
|56|Agents frontend tests|PARTIAL|PARTIAL|PARTIAL|PASS|PARTIAL|unit+B|fixtures|n/a|n/a|console/directory/details|browser tests|6 unit + responsive B|required inventory incomplete|PARTIAL — Implemented but incomplete|
|57|Management API tests|PASS|PASS|PASS|PASS|PASS|API tests|CRUD/lifecycle/options/analytics|DB|S|n/a|n/a|focused/full pass|new aggregation depth modest|PASS — Implemented and verified|
|58|Persisted runtime|PASS|PASS|PASS|PASS|PASS|S|execution APIs|exact version|canonical executor|status visible|Phase3 browser evidence|194 tests|none|PASS — Implemented and verified|
|59|Instructions execute|PASS|PASS|PASS|PASS|PASS|execution S|test/chat|immutable version|prompt consumption|console|Phase3 evidence|tests|live provider awaits credential|PASS — Implemented and verified|
|60|Chat Agent selection|PASS|PASS|PASS|PASS|PASS|Chat/S|authorized endpoint|conversation pin|same execution|selector|Phase3 evidence|tests|Phase4 full browser chat not rerun|PASS — Implemented and verified|
|61|Test Console|PARTIAL|PARTIAL|PASS|PASS|PARTIAL|Console/E|execution/resume/cancel|durable continuation|governed|functional UI|not full Phase4 flow|component/backend tests|browser continuation matrix|PARTIAL — Implemented but incomplete|
|62|Execution details|PASS|PASS|PASS|PASS|PASS|E/Details|safe linked detail|durable rows|trace linkage|details route|rendered shell|backend tests|populated browser lifecycle pending|PARTIAL — Implemented but incomplete|
|63|Accessibility/responsive|BLOCKED|PARTIAL|PARTIAL|PARTIAL|PARTIAL|layout/F/B|n/a|n/a|n/a|semantic/responsive|axe + 3 viewports|browser passes|dialogs/contrast breadth|PARTIAL — Implemented but incomplete|
|64|Browser artifacts|BLOCKED|BLOCKED|BLOCKED|BLOCKED|PARTIAL|config/B/artifacts|fixture statuses|n/a|n/a|rendered UI|screenshots/traces/report|responsive runs|mandatory workflow set incomplete|PARTIAL — Implemented but incomplete|

PASS rows: 38 / 64 = **59.4%**. This deliberately excludes every partial row, including browser-fixture coverage where the specification required a complete live-backend workflow.
