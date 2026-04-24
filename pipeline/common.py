"""Shared helpers for pipeline flows.

Centralizes config, git/subprocess, Ollama, Qdrant, and LLM-output parsing
so that each flow module stays focused on orchestration logic.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

VAULT_PATH = Path(os.environ.get("NEXUS_VAULT_PATH", "/home/raphonzius/obsidian-nexus"))
SCRIPTS_DIR = Path(os.environ.get("NEXUS_SCRIPTS_DIR", "/home/raphonzius/llm-orchestration/scripts"))
QDRANT_URL = os.environ.get("NEXUS_QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("NEXUS_OLLAMA_URL", "http://localhost:11434")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
PYTHON = sys.executable

EMBED_MODEL = "mxbai-embed-large"
TIER1_MODEL = "gemma4:e4b"
TIER2_MODEL = "gemma4:26b"
TIER3_MODEL = "claude-opus-4-7"
ROUTER_MODEL = "gemma4:e2b"


@dataclass
class CmdResult:
    status: str
    stdout: str
    stderr: str
    exit_code: int


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> CmdResult:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return CmdResult(
        status="ok" if result.returncode == 0 else "error",
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        exit_code=result.returncode,
    )


def run_git(args: list[str], cwd: Path = VAULT_PATH) -> CmdResult:
    return run(["git", *args], cwd=cwd)


def ollama_embed(text: str, model: str = EMBED_MODEL, ollama_url: str = OLLAMA_URL) -> list[float]:
    resp = requests.post(
        f"{ollama_url}/api/embed",
        json={"model": model, "input": text},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    embeddings = data.get("embeddings")
    if not embeddings:
        raise ValueError(f"Ollama returned no embeddings: {data}")
    return embeddings[0]


def ollama_generate(
    prompt: str,
    system: str = "",
    model: str = TIER1_MODEL,
    ollama_url: str = OLLAMA_URL,
    timeout: int = 300,
) -> str:
    body: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
    if system:
        body["system"] = system
    resp = requests.post(
        f"{ollama_url}/api/generate",
        json=body,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def qdrant_search(
    vector: list[float],
    collection: str = "atlas",
    domain: str = "",
    limit: int = 10,
    threshold: float = 0.70,
    qdrant_url: str = QDRANT_URL,
) -> list[dict]:
    body: dict[str, Any] = {
        "vector": vector,
        "limit": limit,
        "score_threshold": threshold,
        "with_payload": True,
    }
    if domain:
        body["filter"] = {"must": [{"key": "domain", "match": {"value": domain}}]}
    try:
        resp = requests.post(
            f"{qdrant_url}/collections/{collection}/points/search",
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
    except requests.exceptions.RequestException:
        return []


_SLUG_STRIP = re.compile(r"[^\w\s-]")
_SLUG_DASH = re.compile(r"[\s_-]+")
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```")
_OBJ_RE = re.compile(r"(\{[\s\S]*\})")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = _SLUG_STRIP.sub("", text)
    text = _SLUG_DASH.sub("-", text)
    return text[:80] or "untitled"


def extract_last_json(raw: str) -> dict:
    """Pull JSON object out of verbose LLM output. Prefers last fenced block."""
    fences = _FENCE_RE.findall(raw or "")
    candidate = fences[-1].strip() if fences else ""
    if not candidate:
        m = _OBJ_RE.search(raw or "")
        candidate = (m.group(1) if m else "{}").strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


def append_log(line: str, vault: Path = VAULT_PATH) -> None:
    log_file = vault / "_system" / "log.md"
    log_file.parent.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"- {now} | {line}\n")
