"""Nightly curation — rewrite seed atlas notes via gemma4:26b.

Replaces n8n curation-nightly.json. Run via systemd timer
(deploy/systemd/curation-nightly.timer) or manually with --dry-run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.common import (
    TIER2_MODEL,
    VAULT_PATH,
    append_log,
    ollama_generate,
    run_git,
)

CURATION_SYSTEM_PROMPT = (
    "You are a knowledge curator. Rewrite the given raw atlas note into a clean, "
    "well-structured note.\n\n"
    "Rules:\n"
    "- Preserve ALL factual content and key claims\n"
    "- Write in clear, concise prose (not bullet soup)\n"
    "- Add [[wikilinks]] around concepts, entities, and tools that deserve their own notes\n"
    "- Keep frontmatter intact — only change: status: seed → status: active, modified: today\n"
    "- Remove web clutter (ads, nav text, boilerplate)\n"
    "- Add a '## See Also' section with 2-3 related concept suggestions as [[wikilinks]]\n"
    "- Never invent information not present in the source\n"
    "- Output ONLY the complete rewritten markdown file starting with --- "
    "(frontmatter + body)"
)


def find_seed_notes(vault: Path) -> list[Path]:
    seeds: list[Path] = []
    atlas = vault / "atlas"
    if not atlas.is_dir():
        return seeds
    for f in atlas.rglob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        if "status: seed" in text or 'status: "seed"' in text:
            seeds.append(f)
    return seeds


def extract_note(raw: str) -> str:
    """Strip LLM reasoning prefix, keep from first `---` onward."""
    idx = raw.find("---")
    return raw[idx:].strip() if idx >= 0 else raw.strip()


def curate_note(path: Path, model: str = TIER2_MODEL) -> str:
    content = path.read_text(encoding="utf-8")
    raw = ollama_generate(content, system=CURATION_SYSTEM_PROMPT, model=model, timeout=900)
    return extract_note(raw)


def run_curation(
    vault: Path = VAULT_PATH,
    dry_run: bool = False,
    model: str = TIER2_MODEL,
) -> dict:
    seeds = find_seed_notes(vault)
    if not seeds:
        return {"status": "ok", "curated": 0, "total": 0, "files": []}

    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "total": len(seeds),
            "files": [p.relative_to(vault).as_posix() for p in seeds],
        }

    curated: list[str] = []
    errors: list[dict] = []
    for f in seeds:
        rel = f.relative_to(vault).as_posix()
        try:
            new_content = curate_note(f, model=model)
            if not new_content.startswith("---"):
                errors.append({"path": rel, "error": "LLM output missing frontmatter"})
                continue
            f.write_text(new_content, encoding="utf-8")
            curated.append(rel)
        except Exception as exc:
            errors.append({"path": rel, "error": str(exc)})

    if not curated:
        append_log(f"curate | {model} | 0 curated, {len(errors)} errors")
        return {"status": "ok", "curated": 0, "total": len(seeds), "errors": errors}

    run_git(["add", "atlas/"], cwd=vault)
    status = run_git(["status", "--porcelain"], cwd=vault)
    if status.stdout.strip():
        commit = run_git(
            ["commit", "-m", f"[llm:{model}] curate: rewrite {len(curated)} seed notes"],
            cwd=vault,
        )
        if commit.exit_code != 0:
            return {
                "status": "error",
                "curated": len(curated),
                "errors": errors + [{"git": commit.stderr}],
            }
        push = run_git(["push"], cwd=vault)
        if push.exit_code != 0:
            return {
                "status": "error",
                "curated": len(curated),
                "errors": errors + [{"git": push.stderr}],
            }

    append_log(f"curate | {model} | curated {len(curated)} notes")
    return {
        "status": "ok",
        "curated": len(curated),
        "total": len(seeds),
        "files": curated,
        "errors": errors,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Nightly atlas curation.")
    p.add_argument("--vault-path", type=Path, default=VAULT_PATH)
    p.add_argument("--model", default=TIER2_MODEL)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    result = run_curation(args.vault_path, dry_run=args.dry_run, model=args.model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
