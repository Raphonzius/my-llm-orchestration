"""Weekly purge — archive stale seed notes, flag near-duplicates.

Replaces n8n purge-weekly.json. Run via systemd timer
(deploy/systemd/purge-weekly.timer) or manually with --dry-run.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.common import (
    VAULT_PATH,
    append_log,
    ollama_embed,
    qdrant_search,
    run_git,
)

DUP_THRESHOLD = 0.95
STALE_DAYS = 30
EMBED_CHAR_LIMIT = 500


def find_candidates(vault: Path, stale_days: int = STALE_DAYS) -> tuple[list[Path], list[Path]]:
    """Return (stale_seeds_to_archive, to_check_for_dups)."""
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=stale_days)
    stale: list[Path] = []
    to_check: list[Path] = []
    atlas = vault / "atlas"
    if not atlas.is_dir():
        return stale, to_check

    for f in atlas.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if "provenance: human" in text:
            continue
        is_seed = "status: seed" in text or 'status: "seed"' in text
        if not is_seed:
            continue
        is_low = "confidence: low" in text or "key_claims: []" in text
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if is_low and mtime < stale_threshold:
            stale.append(f)
        else:
            to_check.append(f)
    return stale, to_check


def archive_note(path: Path, vault: Path) -> Path:
    archived_dir = vault / "_inbox" / "archived"
    archived_dir.mkdir(parents=True, exist_ok=True)
    dest = archived_dir / path.name
    i = 2
    while dest.exists():
        dest = archived_dir / f"{path.stem}-{i}{path.suffix}"
        i += 1
    path.rename(dest)
    return dest


def _body_for_embed(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        body = parts[2] if len(parts) >= 3 else text
    else:
        body = text
    return body.strip()[:EMBED_CHAR_LIMIT]


def check_duplicates(paths: list[Path], vault: Path, threshold: float = DUP_THRESHOLD) -> list[dict]:
    dups: list[dict] = []
    for f in paths:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        body = _body_for_embed(text)
        if not body:
            continue
        try:
            vector = ollama_embed(body)
            results = qdrant_search(vector, collection="atlas", limit=3, threshold=threshold)
        except Exception:
            continue
        rel = f.relative_to(vault).as_posix()
        for r in results:
            match_path = r.get("payload", {}).get("file_path") or r.get("payload", {}).get("path", "")
            if match_path and match_path != rel:
                dups.append({"path": rel, "match": match_path, "score": r.get("score", 0.0)})
                break
    return dups


def write_report(vault: Path, archived: list[str], dups: list[dict]) -> Path:
    report_file = vault / "_system" / "purge-candidates.md"
    report_file.parent.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [f"# Purge Report — {now}\n\n"]
    lines.append(f"## Archived ({len(archived)} notes)\n\n")
    for p in archived:
        lines.append(f"- {p}\n")
    lines.append(f"\n## Duplicate Candidates ({len(dups)} pairs — review manually)\n\n")
    for d in dups:
        lines.append(f"- `{d['path']}` ↔ `{d['match']}` (score: {d['score']:.3f})\n")
    report_file.write_text("".join(lines), encoding="utf-8")
    return report_file


def run_purge(
    vault: Path = VAULT_PATH,
    dry_run: bool = False,
    stale_days: int = STALE_DAYS,
) -> dict:
    stale, to_check = find_candidates(vault, stale_days)

    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "stale": [p.relative_to(vault).as_posix() for p in stale],
            "to_check_dups": [p.relative_to(vault).as_posix() for p in to_check],
        }

    archived_paths: list[str] = []
    for p in stale:
        try:
            dest = archive_note(p, vault)
            archived_paths.append(dest.relative_to(vault).as_posix())
        except OSError as exc:
            append_log(f"purge | archive error {p.name}: {exc}")

    dups = check_duplicates(to_check, vault)
    report = write_report(vault, archived_paths, dups)

    run_git(["add", "atlas/", "_inbox/archived/", "_system/purge-candidates.md"], cwd=vault)
    status = run_git(["status", "--porcelain"], cwd=vault)
    if status.stdout.strip():
        commit = run_git(
            ["commit", "-m", f"chore: purge {len(archived_paths)} stale atlas notes"],
            cwd=vault,
        )
        if commit.exit_code != 0:
            return {"status": "error", "archived": len(archived_paths), "error": commit.stderr}
        push = run_git(["push"], cwd=vault)
        if push.exit_code != 0:
            return {"status": "error", "archived": len(archived_paths), "error": push.stderr}

    append_log(f"purge | archived {len(archived_paths)}, {len(dups)} dup candidates")
    return {
        "status": "ok",
        "archived": archived_paths,
        "dup_candidates": dups,
        "report": report.relative_to(vault).as_posix(),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Weekly atlas purge.")
    p.add_argument("--vault-path", type=Path, default=VAULT_PATH)
    p.add_argument("--stale-days", type=int, default=STALE_DAYS)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    result = run_purge(args.vault_path, dry_run=args.dry_run, stale_days=args.stale_days)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
