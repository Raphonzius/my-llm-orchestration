# System Architecture: AI Orchestration (3-Tier)

## 1. Tier Routing Flow

```
  User Query
      |
      v
+------------------+     simple      +------------------+
| Tier 1: Router   |--------------->| Tier 1: Worker   |
| gemma4:e2b       |                | gemma4:e4b       |
| (ultrabook)      |                | (ultrabook)      |
+------------------+                +------------------+
      |                                    |
      | medium                             | response
      v                                    v
+------------------+               [ Return to User ]
| Tier 2: Heavy    |                       ^
| gemma4:27b       |                       |
| (desktop server) |--- response ----------+
+------------------+                       |
      |                                    |
      | complex / long-context             |
      v                                    |
+------------------+                       |
| Tier 3: Cloud    |--- response ----------+
| Claude Pro API   |
+------------------+
```

## 2. Dual-Machine Architecture

```
ULTRABOOK (Samsung Book 4 Ultra)              DESKTOP SERVER (Ubuntu 24.04)
Win 11 | RTX 4070 8GB | 32GB DDR5            Ryzen 5 5600x | RTX 3060 12GB | 24GB DDR4
+--------------------------------------+     +--------------------------------------+
| Ollama :11434                        |     | Ollama :11434                        |
|   gemma4:e2b (router)                |     |   gemma4:27b (heavy inference)       |
|   gemma4:e4b (simple tasks)          |     |                                      |
|                                      |     | Qdrant :6333                         |
| ChromaDB :8000                       |     |   full corpus embeddings             |
|   recent/local embeddings            |     |                                      |
|                                      |     | n8n :5678                            |
| Obsidian (obsidian-nexus vault)      |     |   automation workflows               |
|   active editing + _inbox            |     |   5min polling catch-all             |
+--------------------------------------+     +--------------------------------------+
        |                                            |
        +------------ LAN (git sync) ---------------+
        |                                            |
        +-------- GitHub (obsidian-nexus) -----------+
```

## 3. Data Flow: Ingest to Response

```
_inbox/             atlas/              Vector Stores
  |                   |                   |
  v                   v                   v
+---------+     +-----------+     +-------------+     +-----------+
| Capture |---->| Ingest &  |---->| Embed       |---->| Store     |
| new note|     | normalize |     | (Ollama)    |     | Qdrant    |
+---------+     | frontmatter|    +-------------+     | ChromaDB  |
                +-----------+                         +-----+-----+
                                                            |
                      +-------------------------------------+
                      |
                      v
              +---------------+     RAG Pipeline
              | Query arrives |     1. Frontmatter filter (type, tags, date)
              +-------+-------+     2. Vector search (similarity top-k)
              |               |     3. Summary read (note summaries)
              v               v     4. Top-3 full load (complete notes)
        +----------+  +----------+  5. Tier-appropriate LLM generates response
        | Qdrant   |  | ChromaDB |
        | (full)   |  | (recent) |
        +----+-----+  +----+-----+
             |              |
             v              v
         [ Merge & Rank Results ]
                    |
                    v
         [ Tier 1/2/3 LLM ] ---> Response
```

## 4. Self-Improving Loop

```
+----------+     +------------+     +---------+     +----------+
| Ingest   |---->| Crosslink  |---->| Lint    |---->| Distill  |--+
| new/     |     | find related|    | check   |     | extract  |  |
| updated  |     | notes, add |     | quality,|     | insights,|  |
| notes    |     | wikilinks  |     | fix fmt |     | summaries|  |
+----------+     +------------+     +---------+     +----------+  |
     ^                                                            |
     +------------------------------------------------------------+
     |  loop: improved notes re-enter the pipeline
     |
     |  Triggers:
     |    - git hook (instant, LAN push)
     |    - n8n polling (5min catch-all)
```

## 5. Key Configuration

| Parameter          | Value                            |
|--------------------|----------------------------------|
| Ollama port        | :11434 (both machines)           |
| Qdrant             | desktop :6333                    |
| ChromaDB           | ultrabook :8000                  |
| n8n                | desktop :5678                    |
| Vault sync         | GitHub (obsidian-nexus)          |
| Instant trigger    | git post-receive hook (LAN)      |
| Polling trigger    | n8n every 5 min                  |
| RAG top-k          | 3 full notes loaded              |
| Router model       | gemma4:e2b                       |
| Simple model       | gemma4:e4b                       |
| Heavy model        | gemma4:27b                       |
| Cloud fallback     | Claude Pro API                   |
