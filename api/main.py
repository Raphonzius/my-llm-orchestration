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


# ============================================================================
# Ingest endpoints (Flow 2)
# ============================================================================


class IngestListResponse(BaseModel):
    status: str
    files: list[str]


@app.post("/ingest-list-clips")
def ingest_list_clips() -> IngestListResponse:
    """List new _inbox/clips/*.md files since last commit."""
    result = run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        cwd=VAULT_PATH,
    )
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=result.stderr)

    clips = [
        line for line in result.stdout.split("\n")
        if line.startswith("_inbox/clips/") and line.endswith(".md")
    ]
    return IngestListResponse(status="ok", files=clips)


class ClipMetadata(BaseModel):
    title: str
    summary: str
    domain: str
    tags: list[str]
    entities: list[str]


class IngestProcessResponse(BaseModel):
    status: str
    path: str
    metadata: ClipMetadata
    qdrant_matches: list[dict]
    decision: str  # "create" or "merge"
    best_match_path: str | None = None


@app.post("/ingest-process-clip")
def ingest_process_clip(path: str) -> IngestProcessResponse:
    """Extract metadata, embed, search Qdrant, decide merge vs create."""
    clip_file = VAULT_PATH / path
    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    # Read clip
    clip_text = clip_file.read_text(encoding="utf-8")

    # Extract via gemma4:26b (simplified — just return structure for now)
    # TODO: call Ollama /api/generate with ingestor system prompt
    metadata = ClipMetadata(
        title=clip_file.stem,
        summary=clip_text[:100],
        domain="misc",
        tags=[],
        entities=[],
    )

    # TODO: embed + Qdrant search
    # For now, return empty matches
    qdrant_matches = []

    decision = "create" if not qdrant_matches else "merge"
    best_match = None
    if qdrant_matches and qdrant_matches[0].get("score", 0) > 0.85:
        best_match = qdrant_matches[0].get("payload", {}).get("file_path")

    return IngestProcessResponse(
        status="ok",
        path=path,
        metadata=metadata,
        qdrant_matches=qdrant_matches,
        decision=decision,
        best_match_path=best_match,
    )


class IngestWriteRequest(BaseModel):
    clip_path: str
    metadata: ClipMetadata
    decision: str  # "create" or "merge"
    merge_target: str | None = None


class IngestWriteResponse(BaseModel):
    status: str
    atlas_path: str
    message: str


@app.post("/ingest-write-atlas")
def ingest_write_atlas(req: IngestWriteRequest) -> IngestWriteResponse:
    """Write new atlas note or merge into existing."""
    # TODO: implement merge vs create logic
    # For now, just return success
    atlas_path = f"atlas/{req.metadata.title}.md"
    return IngestWriteResponse(
        status="ok",
        atlas_path=atlas_path,
        message=f"Would write to {atlas_path}",
    )


@app.post("/ingest-commit")
def ingest_commit(message: str = "ingest: new notes") -> CommandResult:
    """Commit and push ingest changes."""
    result = run(["git", "add", "atlas/"], cwd=VAULT_PATH)
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git add failed: {result.stderr}")

    result = run(["git", "commit", "-m", message], cwd=VAULT_PATH)
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git commit failed: {result.stderr}")

    result = run(["git", "push"], cwd=VAULT_PATH)
    if result.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git push failed: {result.stderr}")

    return result
