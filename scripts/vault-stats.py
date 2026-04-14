#!/usr/bin/env python3
"""Vault health metrics — scans Obsidian vault frontmatter and prints a report.

Usage:
    python vault-stats.py --vault-path /path/to/vault
    python vault-stats.py --vault-path /path/to/vault --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

# Directories to skip when scanning
EXCLUDED_DIRS = {"_system", "templates"}

# Regex for wikilinks: [[...]]
WIKILINK_RE = re.compile(r"\[\[.*?\]\]")

# Thresholds (days)
STALE_SEED_DAYS = 30
STALE_EVERGREEN_DAYS = 90


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter from markdown text.

    Splits on the first two '---' delimiters and parses simple
    key: value lines.  Handles quoted values, inline lists written
    as ``[a, b]``, and bare scalars.  Nested / multi-line YAML is
    intentionally unsupported — keeps us dependency-free.
    """
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    fm: dict[str, str] = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon = line.find(":")
        if colon == -1:
            continue
        key = line[:colon].strip()
        value = line[colon + 1 :].strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        fm[key] = value
    return fm


def parse_list_field(value: str) -> list[str]:
    """Turn an inline YAML list like '[a, b, c]' into a Python list.

    Returns an empty list for empty brackets or blank strings.
    """
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    if not value:
        return []
    return [value.strip().strip("\"'")]


def parse_date(value: str) -> date | None:
    """Best-effort ISO date parse (YYYY-MM-DD)."""
    value = value.strip().strip("\"'")
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def scan_vault(vault_path: Path) -> dict:
    """Walk the vault, collect per-note data, and compute aggregate metrics."""
    today = date.today()

    type_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()

    total_notes = 0
    total_links = 0
    orphans: list[str] = []
    stale_seeds: list[str] = []
    stale_evergreens: list[str] = []
    low_trust: list[str] = []

    for md_file in sorted(vault_path.rglob("*.md")):
        # Skip excluded directories
        try:
            rel = md_file.relative_to(vault_path)
        except ValueError:
            continue
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue

        text = md_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)

        total_notes += 1
        note_name = rel.as_posix()

        # --- Facet counts ---
        note_type = fm.get("type", "").lower()
        if note_type:
            type_counts[note_type] += 1

        status = fm.get("status", "").lower()
        if status:
            status_counts[status] += 1

        for d in parse_list_field(fm.get("domain", "")):
            domain_counts[d.lower()] += 1

        prov = fm.get("provenance", "").lower()
        if prov:
            provenance_counts[prov] += 1

        # --- Body analysis (everything after frontmatter) ---
        parts = text.split("---", 2)
        body = parts[2] if len(parts) >= 3 else text
        links_in_note = WIKILINK_RE.findall(body)
        total_links += len(links_in_note)

        # --- Orphan detection ---
        related = parse_list_field(fm.get("related", ""))
        if len(links_in_note) == 0 and len(related) == 0:
            orphans.append(note_name)

        # --- Staleness ---
        created = parse_date(fm.get("created", ""))
        modified = parse_date(fm.get("modified", ""))

        if status == "seed" and created:
            age = (today - created).days
            if age > STALE_SEED_DAYS:
                stale_seeds.append(note_name)

        if status == "evergreen" and modified:
            age = (today - modified).days
            if age > STALE_EVERGREEN_DAYS:
                stale_evergreens.append(note_name)

        # --- Low trust ---
        confidence = fm.get("confidence", "").lower()
        if prov == "inferred" and confidence == "low":
            low_trust.append(note_name)

    avg_links = round(total_links / total_notes, 1) if total_notes else 0.0

    return {
        "vault_name": vault_path.name,
        "total_notes": total_notes,
        "by_type": dict(type_counts.most_common()),
        "by_status": dict(status_counts.most_common()),
        "by_domain": dict(domain_counts.most_common()),
        "by_provenance": dict(provenance_counts.most_common()),
        "total_links": total_links,
        "avg_links_per_note": avg_links,
        "orphans": orphans,
        "stale_seeds": stale_seeds,
        "stale_evergreens": stale_evergreens,
        "low_trust": low_trust,
    }


def _format_counter(counts: dict[str, int]) -> str:
    """Format a dict as key=value pairs separated by two spaces."""
    return "  ".join(f"{k}={v}" for k, v in counts.items())


def print_report(stats: dict) -> None:
    """Print a human-readable health report to stdout."""
    print(f"Vault: {stats['vault_name']}")
    print(f"Notes: {stats['total_notes']} total")
    print(f"  By type:       {_format_counter(stats['by_type'])}")
    print(f"  By status:     {_format_counter(stats['by_status'])}")
    print(f"  By domain:     {_format_counter(stats['by_domain'])}")
    print(f"  By provenance: {_format_counter(stats['by_provenance'])}")
    print(
        f"Links: {stats['total_links']} total, "
        f"avg {stats['avg_links_per_note']} per note"
    )
    print("Attention:")
    print(f"  Orphans: {len(stats['orphans'])} notes")
    print(f"  Stale seeds (>{STALE_SEED_DAYS}d): {len(stats['stale_seeds'])} notes")
    print(
        f"  Stale evergreens (>{STALE_EVERGREEN_DAYS}d): "
        f"{len(stats['stale_evergreens'])} notes"
    )
    print(f"  Low trust: {len(stats['low_trust'])} notes")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Report health metrics for an Obsidian vault."
    )
    parser.add_argument(
        "--vault-path",
        required=True,
        type=Path,
        help="Root directory of the Obsidian vault.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output machine-readable JSON instead of a formatted report.",
    )
    args = parser.parse_args(argv)

    vault = args.vault_path.resolve()
    if not vault.is_dir():
        print(f"Error: {vault} is not a directory", file=sys.stderr)
        sys.exit(1)

    stats = scan_vault(vault)

    if args.as_json:
        print(json.dumps(stats, indent=2))
    else:
        print_report(stats)


if __name__ == "__main__":
    main()
