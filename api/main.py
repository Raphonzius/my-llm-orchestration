"""Nexus Pipeline API — thin HTTP wrapper around pipeline scripts.

Run: uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Nexus Pipeline API", version="0.1.0")

VAULT_PATH = Path("/home/raphonzius/obsidian-nexus")
SCRIPTS_DIR = Path("/home/raphonzius/llm-orchestration/scripts")
QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
PYTHON = sys.executable


class VaultPushPayload(BaseModel):
    ref: str = "refs/heads/main"
    commit: str = "manual"
    pusher: str = "unknown"
    full: bool = False


class CommandResult(BaseModel):
    status: str
    stdout: str
    stderr: str
    exit_code: int


def run(cmd: list[str], cwd: Path | None = None) -> CommandResult:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return CommandResult(
        status="ok" if result.returncode == 0 else "error",
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
        exit_code=result.returncode,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "vault": str(VAULT_PATH), "vault_exists": VAULT_PATH.is_dir()}


@app.post("/delta-index")
def delta_index(payload: VaultPushPayload) -> CommandResult:
    """Pull vault then re-embed changed notes into Qdrant."""
    # 1. git pull
    pull = run(["git", "pull", "--ff-only"], cwd=VAULT_PATH)
    if pull.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git pull failed: {pull.stderr}")

    # 2. run delta-index
    cmd = [
        PYTHON,
        str(SCRIPTS_DIR / "delta-index.py"),
        "--vault-path", str(VAULT_PATH),
        "--qdrant-url", QDRANT_URL,
        "--ollama-url", OLLAMA_URL,
    ]
    if payload.full:
        cmd.append("--full")

    result = run(cmd)
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    return result


@app.post("/embed-all")
def embed_all() -> CommandResult:
    """Full vault batch embed (use once or for reset)."""
    cmd = [
        PYTHON,
        str(SCRIPTS_DIR / "embed.py"),
        "--vault-path", str(VAULT_PATH),
        "--qdrant-url", QDRANT_URL,
        "--ollama-url", OLLAMA_URL,
    ]
    result = run(cmd)
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    return result
