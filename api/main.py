"""Nexus Pipeline API — thin HTTP wrapper around pipeline scripts.

Run: uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
"""
from __future__ import annotations

import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Nexus Pipeline API", version="0.1.0")
_write_lock = threading.Lock()

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
    # Pull first to sync latest changes
    pull = run(["git", "pull", "--ff-only"], cwd=VAULT_PATH)
    if pull.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git pull failed: {pull.stderr}")

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
    summary: str = ""
    domain: str = "misc"
    tags: list[str] = []
    entities: list[str] = []
    key_claims: list[str] = []


class ReadClipResponse(BaseModel):
    status: str
    path: str
    content: str


@app.post("/ingest-read-clip")
def ingest_read_clip(path: str) -> ReadClipResponse:
    """Return raw markdown content of a clip file."""
    clip_file = VAULT_PATH / path
    if not clip_file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return ReadClipResponse(
        status="ok",
        path=path,
        content=clip_file.read_text(encoding="utf-8"),
    )


class QdrantSearchRequest(BaseModel):
    vector: list[float]
    collection: str = "atlas"
    limit: int = 3
    threshold: float = 0.80


class QdrantSearchResponse(BaseModel):
    status: str
    matches: list[dict]
    decision: str  # "create" or "merge"
    best_match_path: str | None = None
    best_score: float | None = None


@app.post("/ingest-search-qdrant")
def ingest_search_qdrant(req: QdrantSearchRequest) -> QdrantSearchResponse:
    """Search Qdrant for similar notes. Returns decision."""
    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/{req.collection}/points/search",
            json={"vector": req.vector, "limit": req.limit, "score_threshold": req.threshold},
            timeout=30,
        )
        resp.raise_for_status()
        matches = resp.json().get("result", [])
    except requests.exceptions.RequestException:
        # Collection missing or Qdrant down — treat as no matches
        matches = []

    decision = "create"
    best_path = None
    best_score = None
    if matches:
        top = matches[0]
        best_score = top.get("score")
        if best_score and best_score > 0.85:
            decision = "merge"
            best_path = top.get("payload", {}).get("file_path") or top.get("payload", {}).get("path")

    return QdrantSearchResponse(
        status="ok",
        matches=matches,
        decision=decision,
        best_match_path=best_path,
        best_score=best_score,
    )


class IngestWriteRequest(BaseModel):
    clip_path: str
    metadata: ClipMetadata
    body: str
    decision: str  # "create" or "merge"
    merge_target: str | None = None
    model: str = "gemma4:26b"


class IngestWriteResponse(BaseModel):
    status: str
    atlas_path: str
    action: str  # "created" or "merged"


def _slugify(text: str) -> str:
    """Make filename-safe slug from title."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80] or "untitled"


def _format_frontmatter(metadata: ClipMetadata, clip_path: str, model: str) -> str:
    """Build YAML frontmatter block."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tags = ", ".join(f'"{t}"' for t in metadata.tags)
    entities = ", ".join(f'"{e}"' for e in metadata.entities)
    return (
        "---\n"
        f'title: "{metadata.title}"\n'
        "aliases: []\n"
        "type: atlas\n"
        "status: active\n"
        f'domain: "{metadata.domain}"\n'
        f"tags: [{tags}]\n"
        f"entities: [{entities}]\n"
        "provenance: synthesized\n"
        "confidence: medium\n"
        f'source: "{clip_path}"\n'
        f'created: "{now}"\n'
        f'modified: "{now}"\n'
        f'summary: "{metadata.summary}"\n'
        f'llm_model: "{model}"\n'
        "---\n\n"
    )


@app.post("/ingest-write-atlas")
def ingest_write_atlas(req: IngestWriteRequest) -> IngestWriteResponse:
    """Write new atlas note or append to merge target."""
    atlas_dir = VAULT_PATH / "atlas"
    atlas_dir.mkdir(exist_ok=True)

    if req.decision == "merge" and req.merge_target:
        target = VAULT_PATH / req.merge_target
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Merge target missing: {req.merge_target}")

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        append_block = (
            f"\n\n## Added {now} (from {req.clip_path})\n\n"
            f"{req.body}\n"
        )
        with target.open("a", encoding="utf-8") as fh:
            fh.write(append_block)
        return IngestWriteResponse(
            status="ok",
            atlas_path=req.merge_target,
            action="merged",
        )

    # Create new atlas note — lock prevents concurrent collision
    with _write_lock:
        slug = _slugify(req.metadata.title)
        atlas_path = atlas_dir / f"{slug}.md"

        i = 2
        while atlas_path.exists():
            atlas_path = atlas_dir / f"{slug}-{i}.md"
            i += 1

        content = _format_frontmatter(req.metadata, req.clip_path, req.model) + req.body.strip() + "\n"
        atlas_path.write_text(content, encoding="utf-8")

    rel_path = atlas_path.relative_to(VAULT_PATH).as_posix()
    return IngestWriteResponse(
        status="ok",
        atlas_path=rel_path,
        action="created",
    )


class CommitRequest(BaseModel):
    message: str = "ingest: new notes"
    model: str = "gemma4:e4b"


# ============================================================================
# RAG endpoints (Flow 3)
# ============================================================================


class RagSearchRequest(BaseModel):
    vector: list[float]
    collection: str = "atlas"
    domain: str = ""
    limit: int = 10
    threshold: float = 0.70


class RagResult(BaseModel):
    file_path: str
    title: str
    summary: str
    score: float
    domain: str


class RagSearchResponse(BaseModel):
    status: str
    results: list[RagResult]
    total: int


@app.post("/rag-search")
def rag_search(req: RagSearchRequest) -> RagSearchResponse:
    """Vector search Qdrant with optional domain filter."""
    payload: dict = {
        "vector": req.vector,
        "limit": req.limit,
        "score_threshold": req.threshold,
        "with_payload": True,
    }
    if req.domain:
        payload["filter"] = {"must": [{"key": "domain", "match": {"value": req.domain}}]}

    try:
        resp = requests.post(
            f"{QDRANT_URL}/collections/{req.collection}/points/search",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json().get("result", [])
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

    results = [
        RagResult(
            file_path=r.get("payload", {}).get("file_path") or r.get("payload", {}).get("path", ""),
            title=r.get("payload", {}).get("title", "Untitled"),
            summary=r.get("payload", {}).get("summary", ""),
            score=r.get("score", 0.0),
            domain=r.get("payload", {}).get("domain", ""),
        )
        for r in raw
    ]
    return RagSearchResponse(status="ok", results=results, total=len(results))


class RouterLogRequest(BaseModel):
    query: str
    tier: int
    model: str
    tokens_estimate: int = 0
    reason: str = ""


@app.post("/router-log")
def router_log(req: RouterLogRequest) -> dict:
    """Append router decision to _system/log.md."""
    log_file = VAULT_PATH / "_system" / "log.md"
    log_file.parent.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = f"- {now} | tier:{req.tier} | {req.model} | {req.reason} | `{req.query[:80]}`\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    return {"status": "ok"}


# ============================================================================
# Curation endpoints (Flow 5)
# ============================================================================


@app.get("/curate-list")
def curate_list() -> dict:
    """Find atlas notes with status: seed."""
    seeds = []
    for f in (VAULT_PATH / "atlas").rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if "status: seed" in text or 'status: "seed"' in text:
            seeds.append(f.relative_to(VAULT_PATH).as_posix())
    return {"status": "ok", "files": seeds, "total": len(seeds)}


class CurateReadResponse(BaseModel):
    status: str
    path: str
    content: str


@app.post("/curate-read")
def curate_read(path: str) -> CurateReadResponse:
    """Read an atlas note for curation."""
    target = VAULT_PATH / path
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    return CurateReadResponse(status="ok", path=path, content=target.read_text(encoding="utf-8"))


class CurateWriteRequest(BaseModel):
    path: str
    content: str


@app.post("/curate-write")
def curate_write(req: CurateWriteRequest) -> dict:
    """Write curated note back (status seed → active)."""
    target = VAULT_PATH / req.path
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {req.path}")
    with _write_lock:
        target.write_text(req.content, encoding="utf-8")
    return {"status": "ok", "path": req.path, "action": "curated"}


@app.post("/curate-commit")
def curate_commit() -> CommandResult:
    """Commit and push curation changes."""
    add = run(["git", "add", "atlas/"], cwd=VAULT_PATH)
    if add.exit_code != 0:
        raise HTTPException(status_code=500, detail=add.stderr)
    status = run(["git", "status", "--porcelain"], cwd=VAULT_PATH)
    if not status.stdout.strip():
        return CommandResult(status="ok", stdout="nothing to commit", stderr="", exit_code=0)
    commit = run(["git", "commit", "-m", "[llm:gemma4-26b] curate: rewrite seed notes"], cwd=VAULT_PATH)
    if commit.exit_code != 0:
        raise HTTPException(status_code=500, detail=commit.stderr)
    push = run(["git", "push"], cwd=VAULT_PATH)
    if push.exit_code != 0:
        raise HTTPException(status_code=500, detail=push.stderr)
    return push


# ============================================================================
# Purge endpoints (Flow 6)
# ============================================================================


@app.get("/purge-candidates")
def purge_candidates() -> dict:
    """Find low-quality stale atlas notes for archiving."""
    from datetime import timedelta
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=30)
    stale, to_check = [], []
    for f in (VAULT_PATH / "atlas").rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if "provenance: human" in text:
            continue
        is_seed = "status: seed" in text or 'status: "seed"' in text
        is_low = "confidence: low" in text or "key_claims: []" in text
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        rel = f.relative_to(VAULT_PATH).as_posix()
        if is_seed and is_low and mtime < stale_threshold:
            stale.append(rel)
        elif is_seed:
            to_check.append(rel)
    return {"status": "ok", "stale": stale, "to_check_dups": to_check, "total_stale": len(stale)}


class PurgeArchiveRequest(BaseModel):
    path: str


@app.post("/purge-archive")
def purge_archive(req: PurgeArchiveRequest) -> dict:
    """Move note to _inbox/archived/ (never delete)."""
    src = VAULT_PATH / req.path
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {req.path}")
    archived_dir = VAULT_PATH / "_inbox" / "archived"
    archived_dir.mkdir(parents=True, exist_ok=True)
    dest = archived_dir / src.name
    i = 2
    while dest.exists():
        dest = archived_dir / f"{src.stem}-{i}{src.suffix}"
        i += 1
    with _write_lock:
        src.rename(dest)
    return {"status": "ok", "archived_to": dest.relative_to(VAULT_PATH).as_posix()}


class PurgeReportRequest(BaseModel):
    stale_archived: list[str] = []
    dup_candidates: list[dict] = []


@app.post("/purge-write-report")
def purge_write_report(req: PurgeReportRequest) -> dict:
    """Write purge summary to _system/purge-candidates.md for human review."""
    report_file = VAULT_PATH / "_system" / "purge-candidates.md"
    report_file.parent.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [f"# Purge Report — {now}\n"]
    lines.append(f"\n## Archived ({len(req.stale_archived)} notes)\n")
    for p in req.stale_archived:
        lines.append(f"- {p}\n")
    lines.append(f"\n## Duplicate Candidates ({len(req.dup_candidates)} pairs — review manually)\n")
    for d in req.dup_candidates:
        lines.append(f"- `{d.get('path')}` ↔ `{d.get('match')}` (score: {d.get('score', 0):.3f})\n")
    report_file.write_text("".join(lines), encoding="utf-8")
    return {"status": "ok", "report": str(report_file.relative_to(VAULT_PATH))}


@app.post("/purge-commit")
def purge_commit() -> CommandResult:
    """Commit purge changes."""
    add = run(["git", "add", "atlas/", "_inbox/archived/", "_system/purge-candidates.md"], cwd=VAULT_PATH)
    if add.exit_code != 0:
        raise HTTPException(status_code=500, detail=add.stderr)
    status = run(["git", "status", "--porcelain"], cwd=VAULT_PATH)
    if not status.stdout.strip():
        return CommandResult(status="ok", stdout="nothing to commit", stderr="", exit_code=0)
    commit = run(["git", "commit", "-m", "chore: purge stale atlas notes"], cwd=VAULT_PATH)
    if commit.exit_code != 0:
        raise HTTPException(status_code=500, detail=commit.stderr)
    push = run(["git", "push"], cwd=VAULT_PATH)
    if push.exit_code != 0:
        raise HTTPException(status_code=500, detail=push.stderr)
    return push


@app.post("/ingest-commit")
def ingest_commit(req: CommitRequest) -> CommandResult:
    """Commit and push ingest changes."""
    full_message = f"[llm:{req.model}] {req.message}"

    add = run(["git", "add", "atlas/", "_inbox/clips/"], cwd=VAULT_PATH)
    if add.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git add failed: {add.stderr}")

    # Check if anything to commit
    status = run(["git", "status", "--porcelain"], cwd=VAULT_PATH)
    if not status.stdout.strip():
        return CommandResult(status="ok", stdout="nothing to commit", stderr="", exit_code=0)

    commit = run(["git", "commit", "-m", full_message], cwd=VAULT_PATH)
    if commit.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git commit failed: {commit.stderr}")

    push = run(["git", "push"], cwd=VAULT_PATH)
    if push.exit_code != 0:
        raise HTTPException(status_code=500, detail=f"git push failed: {push.stderr}")

    return push
