# Router Test Cases

Validate that the router classifies these correctly.

| Query | Expected Tier | Expected Domain | Needs RAG |
|-------|--------------|-----------------|-----------|
| "What is a semaphore?" | simple | engineering | false |
| "Convert 72F to Celsius" | simple | polymath | false |
| "Summarize the article about async Rust I saved yesterday" | medium | engineering | true |
| "Write a Python script to parse CSV files" | medium | engineering | false |
| "Compare Qdrant vs ChromaDB for my use case" | medium | engineering | true |
| "Design the n8n workflow for vault ingestion" | hard | engineering | true |
| "Review this ADR and suggest improvements" | hard | professional | true |
| "What patterns have emerged across my last 10 conversations?" | hard | polymath | true |
| "Turn on the living room lights" | simple | home-automation | false |
| "Plan the Jarvis voice command architecture" | hard | engineering, home-automation | true |
| "What did I decide about the database migration last week?" | medium | professional | true |
| "Explain the difference between TCP and UDP" | simple | engineering | false |
| "Synthesize my notes on memory systems into a coherent overview" | hard | polymath, engineering | true |
| "Add a tag to all notes about Docker" | simple | engineering | true |
| "What are the pros and cons of microservices?" | medium | engineering | false |
