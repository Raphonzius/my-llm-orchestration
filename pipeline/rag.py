"""RAG query pipeline — replaces n8n rag-query.json.

Embed query → Qdrant search → LLM synthesis with top-K context.
"""
from __future__ import annotations

import argparse
import json

from pipeline.common import (
    TIER1_MODEL,
    append_log,
    ollama_embed,
    ollama_generate,
    qdrant_search,
)

RAG_SYSTEM_PROMPT = (
    "You are a knowledge assistant. Answer the user's query using ONLY the provided context.\n"
    "- Cite sources as [[note-title]] using titles from the context\n"
    "- If the context is insufficient, say so — do not invent\n"
    "- Keep answers concise and well-structured"
)


def build_context(results: list[dict], max_sources: int = 5) -> tuple[str, list[dict]]:
    sources: list[dict] = []
    lines: list[str] = []
    for i, r in enumerate(results[:max_sources], 1):
        payload = r.get("payload", {})
        title = payload.get("title", "Untitled")
        summary = payload.get("summary", "")
        path = payload.get("file_path") or payload.get("path", "")
        score = r.get("score", 0.0)
        sources.append({"title": title, "path": path, "score": score})
        lines.append(f"[{i}] {title}\n{summary}\n(source: {path})")
    return "\n\n".join(lines), sources


def run_rag_query(
    query: str,
    domain: str = "",
    collection: str = "atlas",
    model: str = TIER1_MODEL,
    limit: int = 10,
    threshold: float = 0.70,
    max_sources: int = 5,
) -> dict:
    vector = ollama_embed(query)
    results = qdrant_search(
        vector,
        collection=collection,
        domain=domain,
        limit=limit,
        threshold=threshold,
    )

    if not results:
        append_log(f"rag | {model} | no results | `{query[:80]}`")
        return {
            "status": "ok",
            "answer": "No relevant notes found in the vault for this query.",
            "sources": [],
            "model": model,
        }

    context, sources = build_context(results, max_sources=max_sources)
    prompt = f"Context:\n{context}\n\nQuery: {query}\n\nAnswer:"
    answer = ollama_generate(prompt, system=RAG_SYSTEM_PROMPT, model=model).strip()

    append_log(f"rag | {model} | {len(sources)} sources | `{query[:80]}`")
    return {
        "status": "ok",
        "answer": answer,
        "sources": sources,
        "model": model,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="RAG query pipeline.")
    p.add_argument("--query", required=True)
    p.add_argument("--domain", default="")
    p.add_argument("--collection", default="atlas")
    p.add_argument("--model", default=TIER1_MODEL)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--threshold", type=float, default=0.70)
    args = p.parse_args()
    result = run_rag_query(
        args.query,
        domain=args.domain,
        collection=args.collection,
        model=args.model,
        limit=args.limit,
        threshold=args.threshold,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
