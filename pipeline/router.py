"""Tier-dispatch router — replaces n8n router.json.

Classify query with gemma4:e2b → dispatch to Ollama (tier 1/2) or Claude API (tier 3).
"""
from __future__ import annotations

import argparse
import json
import os

import requests

from pipeline.common import (
    ANTHROPIC_URL,
    ANTHROPIC_VERSION,
    ROUTER_MODEL,
    TIER1_MODEL,
    TIER2_MODEL,
    TIER3_MODEL,
    append_log,
    extract_last_json,
    ollama_generate,
)

ROUTER_SYSTEM_PROMPT = (
    "You are a query router. Classify the query into exactly one tier.\n"
    "Return ONLY JSON in a ```json code fence: "
    '{"tier": 1|2|3, "domain": ["tag"], "reason": "one sentence"}\n\n'
    "Tier 1 (gemma4:e4b — fast, local): lookup, classification, yes/no, draft, "
    "template fill, short answers\n"
    "Tier 2 (gemma4:26b — GPU): code generation, summarization, analysis, "
    "RAG synthesis, multi-paragraph output\n"
    "Tier 3 (claude — API, expensive): multi-step reasoning, planning, "
    "judgment calls, final user-facing output\n\n"
    "Never route to tier 3 for anything a local model can handle."
)


def classify(query: str, model: str = ROUTER_MODEL) -> dict:
    raw = ollama_generate(f"/no_think\n\n{query}", system=ROUTER_SYSTEM_PROMPT, model=model)
    parsed = extract_last_json(raw)
    tier = parsed.get("tier", 2)
    try:
        tier_int = int(tier)
    except (TypeError, ValueError):
        tier_int = 2
    if tier_int not in (1, 2, 3):
        tier_int = 2
    return {
        "tier": tier_int,
        "domain": parsed.get("domain", []),
        "reason": parsed.get("reason", ""),
    }


def call_tier1(query: str) -> str:
    return ollama_generate(query, model=TIER1_MODEL).strip()


def call_tier2(query: str) -> str:
    return ollama_generate(query, model=TIER2_MODEL, timeout=600).strip()


def call_tier3(query: str, max_tokens: int = 2048) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — cannot route to tier 3")
    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": TIER3_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": query}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json().get("content", [])
    return "".join(c.get("text", "") for c in content).strip()


def route(query: str, context: str = "", force_tier: int = 0) -> dict:
    if force_tier in (1, 2, 3):
        tier = force_tier
        reason = "forced"
        domain: list = []
    else:
        cls = classify(query)
        tier = cls["tier"]
        reason = cls["reason"]
        domain = cls["domain"]

    prompt = f"{context}\n\n{query}".strip() if context else query

    if tier == 1:
        answer = call_tier1(prompt)
        model = TIER1_MODEL
    elif tier == 2:
        answer = call_tier2(prompt)
        model = TIER2_MODEL
    else:
        answer = call_tier3(prompt)
        model = TIER3_MODEL

    append_log(f"route | tier:{tier} | {model} | {reason} | `{query[:80]}`")
    return {
        "status": "ok",
        "answer": answer,
        "tier": tier,
        "model": model,
        "domain": domain,
        "reason": reason,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Tier-dispatch router.")
    p.add_argument("--query", required=True)
    p.add_argument("--context", default="")
    p.add_argument("--force-tier", type=int, default=0, choices=[0, 1, 2, 3])
    args = p.parse_args()
    print(json.dumps(route(args.query, args.context, args.force_tier), indent=2))


if __name__ == "__main__":
    main()
