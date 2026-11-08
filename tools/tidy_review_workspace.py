#!/usr/bin/env python3
"""Keep the review handoff view clean while retaining stable evidence paths.

The default is a dry run. --apply writes a file-manager .hidden list and an
INTERNAL index. --archive-loose also moves unreferenced historical JSON/log
console receipts into INTERNAL/receipts, retaining their original bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def referenced_names(root: Path, names: set[str]) -> set[str]:
    """Find exact filenames in maintained source and current local helpers.

    Dynamic helper inputs and latest receipts are protected separately. This
    intentionally errs toward keeping a historical receipt at its old path.
    """
    found: set[str] = set()
    if not names:
        return found
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as patterns:
        patterns.write("\n".join(sorted(names)) + "\n")
        patterns.flush()
        result = subprocess.run(
            ["git", "grep", "-l", "-F", "-f", patterns.name, "--", "."],
            cwd=root, capture_output=True, text=True, check=False,
        )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr or "Cannot inspect tracked references")
    sources = [root / name for name in result.stdout.splitlines()]
    review = root / "var/review"
    sources.extend(review.glob("*.py"))
    local_helpers = review / "internal"
    if local_helpers.is_dir():
        sources.extend(local_helpers.rglob("*.py"))
    sources.extend(p for p in review.iterdir() if p.suffix in {".json", ".md", ".txt"})
    for path in sources:
        content = path.read_text(encoding="utf-8", errors="replace")
        found.update(name for name in names if name in content)
    return found


def clean(root: Path, *, apply: bool = False, archive_loose: bool = False,
          retain: set[str] | None = None) -> dict:
    review = root / "var/review"
    if not (root / "AGENTS.md").is_file() or not (root / "REVIEW").is_dir():
        raise ValueError("Choose an ARCpuzzles checkout with --library")
    if not review.is_dir():
        raise ValueError(f"Review working folder is absent: {review}")
    entries = sorted(review.iterdir())
    keep = retain or set()
    # Keep named pipeline inputs and recent collection receipts in place even
    # when a scratch helper computes their filenames dynamically.
    candidates = [p for p in entries
                  if p.is_file() and not p.is_symlink()
                  and p.suffix in {".json", ".log"}
                  and "latest" not in p.name
                  and not p.name.endswith(".collect.json")
                  and p.name not in keep]
    referenced = referenced_names(root, {p.name for p in candidates})
    movable = [p for p in candidates if p.name not in referenced] if archive_loose else []
    sendable = lambda p: p.name.startswith("SEND-THIS-")
    hidden = [p.name for p in entries if p.name != "INTERNAL"
              and not p.name.startswith(".") and not sendable(p)
              and p not in movable]
    moves = [{"from": str(p.relative_to(root)),
              "to": str((review / "INTERNAL/receipts" / p.name).relative_to(root)),
              "bytes": p.stat().st_size, "sha256": digest(p)} for p in movable]
    report = {"schema": "arcpuzzles-review-workspace-cleanup-v1",
              "at": datetime.now(timezone.utc).isoformat(), "applied": apply,
              "before_top_files": sum(p.is_file() for p in entries),
              "before_top_directories": sum(p.is_dir() for p in entries),
              "moves": moves, "moved_bytes": sum(row["bytes"] for row in moves),
              "hidden_entries": hidden,
              "visible_entries": sorted([p.name for p in entries if sendable(p)] + ["INTERNAL"]),
              "referenced_receipts_kept": sorted(referenced)}
    if not apply:
        return report
    internal = review / "INTERNAL"
    receipts = internal / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    for row in moves:
        source, destination = root / row["from"], root / row["to"]
        if destination.exists():
            raise FileExistsError(f"Archive destination already exists: {destination}")
        if digest(source) != row["sha256"]:
            raise RuntimeError(f"Receipt changed while planning: {source}")
    for row in moves:
        source, destination = root / row["from"], root / row["to"]
        source.rename(destination)
        if digest(destination) != row["sha256"]:
            raise RuntimeError(f"Receipt hash changed after relocation: {destination}")
    # Re-read the folder so newly arrived handoff partials remain visible and
    # concurrent pipeline output is included in the hidden operational view.
    hidden = sorted(p.name for p in review.iterdir()
                    if p.name != "INTERNAL" and not p.name.startswith(".") and not sendable(p))
    (review / ".hidden").write_text("\n".join(hidden) + "\n", encoding="utf-8")
    report["hidden_entries"] = hidden
    report["after_top_files"] = sum(p.is_file() and not p.name.startswith(".") for p in review.iterdir())
    report["after_top_directories"] = sum(p.is_dir() for p in review.iterdir())
    links = [f'<li><a href="../{quote(name)}">{html.escape(name)}</a></li>' for name in hidden]
    (internal / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Review internals</title>'
        '<style>body{font:16px system-ui;max-width:70em;margin:3em auto;line-height:1.6}'
        'li{margin:.15em 0}</style><h1>Review internals</h1>'
        '<p>The SEND-THIS ZIPs live one folder up. This page opens retained internal '
        'artifacts at their stable paths. The folder’s .hidden file hides them in '
        'supporting file managers; “Show Hidden Files” reveals them.</p>'
        '<p><a href="receipts/">Archived console receipts</a> · '
        '<a href="cleanup-receipts/">Cleanup hash receipts</a></p><ul>'
        + "\n".join(links) + '</ul>\n', encoding="utf-8")
    audit = internal / "cleanup-receipts"
    audit.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    receipt = audit / f"{stamp}.json"
    receipt.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["cleanup_receipt"] = str(receipt)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true", help="Apply the planned cleanup")
    parser.add_argument("--archive-loose", action="store_true", help="Archive unreferenced historical JSON/log console receipts")
    parser.add_argument("--retain", action="append", default=[], metavar="NAME", help="Keep a receipt at its current path")
    args = parser.parse_args()
    print(json.dumps(clean(args.library.resolve(), apply=args.apply,
                           archive_loose=args.archive_loose, retain=set(args.retain)), indent=2))


if __name__ == "__main__":
    main()
