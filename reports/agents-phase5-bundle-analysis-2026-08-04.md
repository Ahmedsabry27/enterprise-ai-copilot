# Phase 5 bundle analysis

| Measurement | Before | After |
|---|---:|---:|
| Entry chunk | 1,201.23 kB | 305.03 kB |
| Entry gzip | 400.09 kB | 99.46 kB |

Reduction: 896.20 kB (74.6%) in the uncompressed entry chunk.

Changes: route-level lazy loading for chat, dashboard, workflows, actions, audit, settings, knowledge, tools, integrations, MCP/native/discovery administration, and Agents. The remaining largest chunks are Chat (813.83 kB, loaded only on `/chat`) and charts (354.87 kB, loaded only by chart routes). These are driven by syntax highlighting and chart libraries and no longer affect initial application load.

