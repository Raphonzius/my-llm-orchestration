# Quality Filters for Conversation Distillation

## Worth keeping (signal)

| Category | Examples | Where it goes |
|----------|----------|--------------|
| Architecture decisions | "We chose Qdrant over Pinecone because..." | projects/{name}/decisions/ |
| Reusable patterns | "The retry-with-backoff pattern works well for..." | atlas/patterns/ |
| Non-obvious facts | "mxbai-embed-large outputs 1024 dimensions" | atlas/entities/ or atlas/concepts/ |
| Mental models | "Think of embeddings as compressed meaning..." | atlas/concepts/ |
| Problem root causes | "The timeout was caused by connection pool exhaustion" | atlas/guides/ (if generalizable) |
| Tool evaluations | "n8n vs Dify: n8n has better webhook support but..." | atlas/entities/ |
| Workflow recipes | "To deploy: first X, then Y, verify with Z" | atlas/guides/ |

## Not worth keeping (noise)

| Category | Why skip |
|----------|---------|
| Syntax errors and fixes | The fix is in the code; git blame has context |
| "Try this... no, try this" iterations | Only the final working solution matters |
| Greeting / small talk | Zero knowledge value |
| Easily searchable facts | "What port does HTTP use?" — no vault value |
| Debugging print statements | Ephemeral; not generalizable |
| File contents discussed | Already in the codebase |
| "Can you also..." / task management | Not knowledge, just coordination |

## Edge cases

- **Long debugging sessions**: Skip the iteration, but keep the root cause if non-obvious
- **Code review feedback**: Keep patterns/principles, skip line-specific comments
- **Planning discussions**: Keep decisions and rationale, skip brainstorming that was rejected
- **Multi-topic conversations**: Extract from each topic independently
