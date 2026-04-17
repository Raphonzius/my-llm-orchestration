#!/usr/bin/env python3
"""
delta-index.py -- Selective re-embedding for Obsidian vaults.

Only processes .md files changed since the last run, then upserts their
embeddings into Qdrant.  Uses _system/.manifest.json to track state.

Usage:
    python delta-index.py \
        --vault-path /path/to/vault \
        --qdrant-url http://localhost:6333 \
        --ollama-url http://localhost:11434

    python delta-index.py --vault-path /path/to/vault --full   # rebuild all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMBED_MODEL = "mxbai-embed-large"
MANIFEST_REL = "_system/.manifest.json"
SKIP_DIRS = {"_system", "_inbox", "templates", "daily"}

# folder -> qdrant collection
COLLECTION_MAP = {
    "atlas": "atlas",
    "sources": "sources",
    "projects": "projects",
    "areas": "areas",
}
DEFAULT_COLLECTION = "vault"

BODY_CHAR_LIMIT = 500

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body) from markdown text.

    Frontmatter is the YAML block between the first pair of ``---`` lines.
    Parsing is intentionally manual (no PyYAML dependency).
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    raw_fm = text[3:end].strip()
    body = text[end + 4 :].strip()

    fm: dict[str, Any] = {}
    for line in raw_fm.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        # Try to parse lists written as [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        fm[key] = value
    return fm, body


def file_path_hash(rel_path: str) -> str:
    """Deterministic point-ID derived from the relative file path."""
    digest = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()
    # Qdrant accepts UUIDs or unsigned ints; use first 16 hex chars as int.
    return str(int(digest[:16], 16))


def collection_for_path(rel_path: str) -> str:
    """Map a vault-relative path to a Qdrant collection name."""
    top = rel_path.split("/")[0] if "/" in rel_path else ""
    return COLLECTION_MAP.get(top, DEFAULT_COLLECTION)


def should_skip(rel_path: str) -> bool:
    """Return True if this path should be skipped."""
    if not rel_path.endswith(".md"):
        return True
    top = rel_path.split("/")[0] if "/" in rel_path else ""
    return top in SKIP_DIRS


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def git_changed_files(vault: Path) -> set[str]:
    """Return set of file paths changed in the most recent commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=str(vault),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        return set()


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------


def load_manifest(vault: Path) -> dict[str, float]:
    """Load {rel_path: mtime_epoch} from the manifest file."""
    path = vault / MANIFEST_REL
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def save_manifest(vault: Path, manifest: dict[str, float]) -> None:
    """Persist the manifest back to disk."""
    path = vault / MANIFEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


# ---------------------------------------------------------------------------
# Embedding via Ollama
# ---------------------------------------------------------------------------


def embed_text(text: str, ollama_url: str) -> list[float]:
    """Call Ollama embeddings endpoint and return the vector."""
    url = f"{ollama_url.rstrip('/')}/api/embed"
    resp = requests.post(url, json={"model": EMBED_MODEL, "input": text}, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    # Ollama returns {"embeddings": [[...]]} for /api/embed
    return data["embeddings"][0]


# ---------------------------------------------------------------------------
# Qdrant helpers
# ---------------------------------------------------------------------------


def ensure_collection(qdrant_url: str, name: str, vector_size: int) -> None:
    """Create a Qdrant collection if it does not already exist."""
    base = qdrant_url.rstrip("/")
    check = requests.get(f"{base}/collections/{name}", timeout=10)
    if check.status_code == 200:
        return
    requests.put(
        f"{base}/collections/{name}",
        json={
            "vectors": {
                "size": vector_size,
                "distance": "Cosine",
            }
        },
        timeout=30,
    ).raise_for_status()


def upsert_point(
    qdrant_url: str,
    collection: str,
    point_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:
    """Upsert a single point into a Qdrant collection."""
    base = qdrant_url.rstrip("/")
    ensure_collection(base, collection, len(vector))
    requests.put(
        f"{base}/collections/{collection}/points",
        json={
            "points": [
                {
                    "id": int(point_id),
                    "vector": vector,
                    "payload": payload,
                }
            ]
        },
        timeout=30,
    ).raise_for_status()


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def collect_all_md(vault: Path) -> list[str]:
    """Walk the vault and return all non-skipped .md relative paths."""
    results: list[str] = []
    for root, _dirs, files in os.walk(vault):
        for fname in files:
            abs_path = Path(root) / fname
            rel = abs_path.relative_to(vault).as_posix()
            if not should_skip(rel):
                results.append(rel)
    return sorted(results)


def detect_changed(
    vault: Path, manifest: dict[str, float], full: bool
) -> list[str]:
    """Return the list of vault-relative .md paths that need re-embedding."""
    all_files = collect_all_md(vault)

    if full:
        return all_files

    git_changed = git_changed_files(vault)
    changed: list[str] = []

    for rel in all_files:
        # 1. File appeared in git diff
        if rel in git_changed:
            changed.append(rel)
            continue

        # 2. mtime newer than manifest timestamp (catches uncommitted edits)
        abs_path = vault / rel
        try:
            current_mtime = abs_path.stat().st_mtime
        except OSError:
            continue

        prev_mtime = manifest.get(rel)
        if prev_mtime is None or current_mtime > prev_mtime:
            changed.append(rel)

    return sorted(changed)


def process_file(
    vault: Path,
    rel: str,
    ollama_url: str,
    qdrant_url: str,
) -> None:
    """Read, embed, and upsert a single markdown file."""
    abs_path = vault / rel
    text = abs_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    summary = fm.get("summary", "")
    snippet = body[:BODY_CHAR_LIMIT]
    embed_input = f"{summary}\n{snippet}".strip() if summary else snippet
    if not embed_input:
        raise ValueError("empty content")

    vector = embed_text(embed_input, ollama_url)
    collection = collection_for_path(rel)
    point_id = file_path_hash(rel)

    payload = {
        "path": rel,
        "title": fm.get("title", Path(rel).stem),
        "tags": fm.get("tags", []),
        "summary": summary,
        "indexed_at": time.time(),
    }

    upsert_point(qdrant_url, collection, point_id, vector, payload)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Selective re-embedding for Obsidian vaults."
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        type=Path,
        help="Root directory of the Obsidian vault.",
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant REST endpoint (default: http://localhost:6333).",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama API endpoint (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Ignore manifest and re-embed every file.",
    )
    args = parser.parse_args()

    vault: Path = args.vault_path.resolve()
    if not vault.is_dir():
        print(f"[delta] error: vault path does not exist: {vault}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(vault)
    changed = detect_changed(vault, manifest, args.full)

    embedded = 0
    skipped = 0
    errors: list[tuple[str, str]] = []

    for rel in changed:
        try:
            process_file(vault, rel, args.ollama_url, args.qdrant_url)
            manifest[rel] = (vault / rel).stat().st_mtime
            embedded += 1
        except Exception as exc:
            errors.append((rel, str(exc)))
            skipped += 1

    save_manifest(vault, manifest)

    print(f"[delta] {len(changed)} files changed, {embedded} embedded, {skipped} skipped")

    if errors:
        print(f"[delta] {len(errors)} error(s):")
        for path, msg in errors:
            print(f"  - {path}: {msg}")


if __name__ == "__main__":
    main()
