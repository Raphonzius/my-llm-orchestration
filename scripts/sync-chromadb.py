#!/usr/bin/env python3
"""Sync recent vault embeddings from Qdrant (desktop) to ChromaDB (ultrabook).

Maintains two ChromaDB collections:
  - "recent": embeddings modified within the last N days
  - "workspace": embeddings for a specific project (optional)

Usage:
    python sync-chromadb.py --qdrant-url http://desktop:6333 --chromadb-url http://localhost:8000 --days 30
    python sync-chromadb.py --qdrant-url http://desktop:6333 --chromadb-url http://localhost:8000 --days 30 --project myproject
    python sync-chromadb.py --qdrant-url http://desktop:6333 --chromadb-url http://localhost:8000 --days 30 --dry-run

Requires: Python 3.10+, requests, chromadb
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from typing import Any

import chromadb
import requests


QDRANT_SCROLL_LIMIT = 256
CHROMADB_BATCH_SIZE = 128

RECENT_COLLECTION = "recent"
WORKSPACE_COLLECTION = "workspace"

QDRANT_SOURCE_COLLECTIONS = ["atlas", "sources"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync recent vault embeddings from Qdrant to ChromaDB.",
    )
    parser.add_argument(
        "--qdrant-url",
        required=True,
        help="Qdrant REST API base URL (e.g. http://desktop:6333)",
    )
    parser.add_argument(
        "--chromadb-url",
        required=True,
        help="ChromaDB HTTP client URL (e.g. http://localhost:8000)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Project name to sync into the workspace collection",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without writing to ChromaDB",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Qdrant helpers (REST API via requests)
# ---------------------------------------------------------------------------

def _qdrant_scroll(
    base_url: str,
    collection: str,
    scroll_filter: dict[str, Any],
    with_vectors: bool = True,
) -> list[dict[str, Any]]:
    """Scroll through all matching points in a Qdrant collection."""
    url = f"{base_url}/collections/{collection}/points/scroll"
    all_points: list[dict[str, Any]] = []
    offset: str | int | None = None

    while True:
        body: dict[str, Any] = {
            "filter": scroll_filter,
            "limit": QDRANT_SCROLL_LIMIT,
            "with_payload": True,
            "with_vector": with_vectors,
        }
        if offset is not None:
            body["offset"] = offset

        resp = requests.post(url, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json().get("result", {})

        points = data.get("points", [])
        all_points.extend(points)

        next_offset = data.get("next_page_offset")
        if next_offset is None or len(points) == 0:
            break
        offset = next_offset

    return all_points


def fetch_recent_points(
    base_url: str,
    collection: str,
    cutoff_ts: float,
) -> list[dict[str, Any]]:
    """Fetch points from a Qdrant collection where `modified` >= cutoff timestamp."""
    scroll_filter = {
        "must": [
            {
                "key": "modified",
                "range": {
                    "gte": cutoff_ts,
                },
            }
        ]
    }
    return _qdrant_scroll(base_url, collection, scroll_filter)


def fetch_project_points(
    base_url: str,
    project_name: str,
) -> list[dict[str, Any]]:
    """Fetch points from Qdrant 'projects' collection filtered by project name."""
    scroll_filter = {
        "must": [
            {
                "key": "project",
                "match": {
                    "value": project_name,
                },
            }
        ]
    }
    return _qdrant_scroll(base_url, "projects", scroll_filter)


# ---------------------------------------------------------------------------
# ChromaDB helpers
# ---------------------------------------------------------------------------

def _sanitize_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure metadata values are ChromaDB-compatible (str, int, float, bool).

    Drops keys whose values are None, lists, or dicts since ChromaDB metadata
    only supports scalar types.
    """
    clean: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif v is None:
            continue
        else:
            # Coerce other types to string so nothing is silently lost
            clean[k] = str(v)
    return clean


def upsert_to_chromadb(
    collection: chromadb.Collection,
    points: list[dict[str, Any]],
    dry_run: bool = False,
) -> int:
    """Upsert Qdrant points into a ChromaDB collection. Returns count upserted."""
    if not points:
        return 0

    if dry_run:
        return len(points)

    # Process in batches
    for i in range(0, len(points), CHROMADB_BATCH_SIZE):
        batch = points[i : i + CHROMADB_BATCH_SIZE]

        ids: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []

        for pt in batch:
            pt_id = str(pt["id"])
            vector = pt.get("vector")
            payload = pt.get("payload", {})

            if vector is None:
                continue

            ids.append(pt_id)
            embeddings.append(vector)
            metadatas.append(_sanitize_metadata(payload))

        if ids:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
            )

    return len(points)


def prune_old_entries(
    collection: chromadb.Collection,
    cutoff_ts: float,
    dry_run: bool = False,
) -> int:
    """Delete entries from a ChromaDB collection where `modified` < cutoff.

    Returns the number of entries deleted.
    """
    try:
        results = collection.get(
            where={"modified": {"$lt": cutoff_ts}},
        )
    except Exception:
        # Collection may be empty or field may not exist yet
        return 0

    ids_to_delete = results.get("ids", [])
    if not ids_to_delete:
        return 0

    if not dry_run:
        collection.delete(ids=ids_to_delete)

    return len(ids_to_delete)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    cutoff_ts = cutoff_dt.timestamp()

    prefix = "[dry-run]" if args.dry_run else "[sync]"

    # -- 1. Pull recent points from Qdrant atlas + sources --
    all_recent: list[dict[str, Any]] = []
    for qdrant_col in QDRANT_SOURCE_COLLECTIONS:
        try:
            pts = fetch_recent_points(args.qdrant_url, qdrant_col, cutoff_ts)
            all_recent.extend(pts)
            print(f"{prefix} Fetched {len(pts)} points from Qdrant '{qdrant_col}'")
        except requests.RequestException as exc:
            print(f"{prefix} Warning: failed to read Qdrant '{qdrant_col}': {exc}", file=sys.stderr)

    total_pulled = len(all_recent)

    # -- 2. Connect to ChromaDB --
    chroma = chromadb.HttpClient(host=args.chromadb_url.rstrip("/"))
    recent_col = chroma.get_or_create_collection(
        name=RECENT_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # -- 3. Upsert to "recent" collection --
    recent_upserted = upsert_to_chromadb(recent_col, all_recent, dry_run=args.dry_run)

    # -- 4. Prune entries older than N days from "recent" --
    pruned = prune_old_entries(recent_col, cutoff_ts, dry_run=args.dry_run)
    if pruned:
        print(f"{prefix} Pruned {pruned} old entries from ChromaDB '{RECENT_COLLECTION}'")

    # -- 5. Optionally sync project to "workspace" collection --
    workspace_upserted = 0
    if args.project:
        try:
            project_pts = fetch_project_points(args.qdrant_url, args.project)
            print(f"{prefix} Fetched {len(project_pts)} points from Qdrant 'projects' (project={args.project})")
            total_pulled += len(project_pts)

            workspace_col = chroma.get_or_create_collection(
                name=WORKSPACE_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            workspace_upserted = upsert_to_chromadb(workspace_col, project_pts, dry_run=args.dry_run)
        except requests.RequestException as exc:
            print(f"{prefix} Warning: failed to read Qdrant 'projects': {exc}", file=sys.stderr)

    # -- Summary --
    print(
        f"{prefix} Pulled {total_pulled} points from Qdrant, "
        f"upserted to ChromaDB recent ({recent_upserted}) + workspace ({workspace_upserted})"
    )


if __name__ == "__main__":
    main()
