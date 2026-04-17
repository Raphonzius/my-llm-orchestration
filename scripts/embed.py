#!/usr/bin/env python3
"""Batch embedding script for an Obsidian vault.

Reads markdown files, parses YAML frontmatter, generates embeddings via
Ollama, and upserts vectors to Qdrant with frontmatter metadata for
filtered retrieval.

Requires: Python 3.10+, requests, pyyaml
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "mxbai-embed-large"
EMBEDDING_DIM = 1024

# Folder -> Qdrant collection mapping
FOLDER_COLLECTION_MAP: dict[str, str] = {
    "atlas": "atlas",
    "sources": "sources",
    "projects": "projects",
    "areas": "areas",
}

# Folders to skip entirely
SKIP_FOLDERS: set[str] = {"_system", "_inbox", "templates", "daily"}

# Frontmatter fields to extract as Qdrant payload metadata
PAYLOAD_FIELDS: list[str] = [
    "title",
    "type",
    "status",
    "domain",
    "tags",
    "provenance",
    "confidence",
    "created",
    "modified",
    "summary",
    "source",
]

BODY_CHAR_LIMIT = 500

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?\r?\n)---\r?\n?(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body) from a markdown string."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def file_point_id(path: Path, vault_root: Path) -> str:
    """Deterministic UUID derived from the vault-relative path."""
    rel = path.relative_to(vault_root).as_posix()
    digest = hashlib.sha256(rel.encode()).hexdigest()
    # Qdrant accepts UUID strings as point IDs
    return str(uuid.UUID(digest[:32]))


def resolve_collection(path: Path, vault_root: Path) -> str | None:
    """Return the Qdrant collection name for a file, or None to skip."""
    rel = path.relative_to(vault_root).as_posix()
    top_folder = rel.split("/")[0].lower()
    return FOLDER_COLLECTION_MAP.get(top_folder)


def should_skip(path: Path, vault_root: Path) -> bool:
    """Return True if the file lives under a folder we want to ignore."""
    rel = path.relative_to(vault_root).as_posix()
    parts = rel.split("/")
    return any(p.lower() in SKIP_FOLDERS for p in parts)


def build_embed_text(fm: dict[str, Any], body: str) -> str:
    """Combine summary + truncated body for embedding input."""
    summary = fm.get("summary", "") or ""
    body_snippet = body[:BODY_CHAR_LIMIT].strip()
    parts = [p for p in (summary, body_snippet) if p]
    return "\n\n".join(parts) if parts else ""


def extract_payload(fm: dict[str, Any], path: Path, vault_root: Path) -> dict[str, Any]:
    """Build the metadata payload dict from frontmatter."""
    payload: dict[str, Any] = {}
    for key in PAYLOAD_FIELDS:
        val = fm.get(key)
        if val is not None:
            # Convert dates/datetimes to ISO strings for JSON serialisation
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            payload[key] = val
    # Always include the vault-relative file path
    payload["file_path"] = path.relative_to(vault_root).as_posix()
    return payload


# ---------------------------------------------------------------------------
# API callers
# ---------------------------------------------------------------------------


def ollama_embed(text: str, ollama_url: str, model: str) -> list[float]:
    """Call the Ollama embedding endpoint and return the vector."""
    resp = requests.post(
        f"{ollama_url}/api/embed",
        json={"model": model, "input": text},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    # Ollama returns {"embeddings": [[...], ...]} for /api/embed
    embeddings = data.get("embeddings")
    if embeddings and len(embeddings) > 0:
        return embeddings[0]
    raise ValueError(f"Unexpected Ollama response: {data}")


def qdrant_ensure_collection(qdrant_url: str, collection: str, dim: int) -> None:
    """Create a Qdrant collection if it does not already exist."""
    url = f"{qdrant_url}/collections/{collection}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return  # already exists
    requests.put(
        url,
        json={
            "vectors": {
                "size": dim,
                "distance": "Cosine",
            }
        },
        timeout=30,
    ).raise_for_status()


def qdrant_upsert(
    qdrant_url: str,
    collection: str,
    point_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:
    """Upsert a single point into Qdrant."""
    url = f"{qdrant_url}/collections/{collection}/points"
    body = {
        "points": [
            {
                "id": point_id,
                "vector": vector,
                "payload": payload,
            }
        ]
    }
    resp = requests.put(url, json=body, timeout=30)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def collect_files(vault_path: Path) -> list[Path]:
    """Gather all .md files eligible for embedding."""
    files: list[Path] = []
    for p in sorted(vault_path.rglob("*.md")):
        if should_skip(p, vault_path):
            continue
        if resolve_collection(p, vault_path) is None:
            continue
        files.append(p)
    return files


def run(
    vault_path: Path,
    qdrant_url: str,
    ollama_url: str,
    model: str,
    dry_run: bool,
) -> None:
    files = collect_files(vault_path)
    total = len(files)
    if total == 0:
        print("No eligible markdown files found.")
        return

    print(f"Found {total} file(s) to embed.\n")

    # Track which collections we have already ensured exist
    ensured_collections: set[str] = set()
    errors: list[tuple[str, str]] = []

    for idx, fpath in enumerate(files, start=1):
        rel = fpath.relative_to(vault_path).as_posix()
        collection = resolve_collection(fpath, vault_path)
        assert collection is not None  # guaranteed by collect_files

        label = f"[{idx}/{total}]"

        if dry_run:
            print(f"{label} (dry-run) would embed: {rel} -> {collection}")
            continue

        print(f"{label} embedding: {fpath.name} -> {collection}")

        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append((rel, f"read error: {exc}"))
            continue

        fm, body = parse_frontmatter(text)
        embed_text = build_embed_text(fm, body)

        if not embed_text.strip():
            errors.append((rel, "empty content after parsing"))
            continue

        point_id = file_point_id(fpath, vault_path)
        payload = extract_payload(fm, fpath, vault_path)

        try:
            # Ensure collection exists
            if collection not in ensured_collections:
                qdrant_ensure_collection(qdrant_url, collection, EMBEDDING_DIM)
                ensured_collections.add(collection)

            vector = ollama_embed(embed_text, ollama_url, model)
            qdrant_upsert(qdrant_url, collection, point_id, vector, payload)
        except Exception as exc:
            errors.append((rel, str(exc)))
            continue

    # Final report
    print()
    succeeded = total - len(errors) if not dry_run else 0
    if dry_run:
        print(f"Dry run complete. {total} file(s) would be processed.")
    else:
        print(f"Done. {succeeded}/{total} file(s) embedded successfully.")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for path, msg in errors:
            print(f"  - {path}: {msg}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-embed Obsidian vault notes into Qdrant via Ollama."
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        type=Path,
        help="Path to the Obsidian vault root directory.",
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant REST API base URL (default: http://localhost:6333).",
    )
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama embedding model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be embedded without calling any APIs.",
    )

    args = parser.parse_args()

    vault = args.vault_path.resolve()
    if not vault.is_dir():
        print(f"Error: vault path does not exist or is not a directory: {vault}", file=sys.stderr)
        sys.exit(1)

    run(
        vault_path=vault,
        qdrant_url=args.qdrant_url.rstrip("/"),
        ollama_url=args.ollama_url.rstrip("/"),
        model=args.model,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
