#!/usr/bin/env python3
"""Bulk-lint every generator in puzzle_generators/per_puzzle/.

Wraps the per-file lint in `scripts/lint_generator.py` and emits a
corpus-wide conformance summary.

Usage:
    python3 scripts/lint_generators.py
    python3 scripts/lint_generators.py --json data/derived/generator_lint.jsonl
    python3 scripts/lint_generators.py --fail-on errors
        # exit non-zero if any generator has ANY error (default)

Wired into `scripts/regen_all.py` as a non-blocking step (warnings
are tolerated; structural errors trip the lint gate).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PER_PUZZLE_DIR = ROOT / "puzzle_generators" / "per_puzzle"

# Import the per-file linter
sys.path.insert(0, str(ROOT))
from scripts.lint_generator import lint_generator  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", default=None,
                   help="Write per-generator lint records to this JSONL path.")
    p.add_argument("--fail-on", choices=("errors", "warnings"),
                   default="errors",
                   help="Exit non-zero on errors (default) or any warning.")
    p.add_argument("--verbose", action="store_true",
                   help="Print per-generator details (off by default).")
    args = p.parse_args()

    if not PER_PUZZLE_DIR.is_dir():
        print(f"missing {PER_PUZZLE_DIR}", file=sys.stderr)
        return 2

    records = []
    n_total = 0
    n_pass = 0
    n_warn = 0
    n_err = 0
    err_kinds = Counter()
    warn_kinds = Counter()

    for sub in sorted(PER_PUZZLE_DIR.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_"):
            continue
        gen_path = sub / "generator.py"
        if not gen_path.exists():
            # Empty stub directory. Treated as a WARNING, not an error,
            # so codex's WIP scaffolding doesn't block the regen gate.
            # (Empty stubs are tracked by the warn count; clean them up
            # by either filling in or removing the directory.)
            records.append({
                "task_id_dir": sub.name,
                "status": "warn",
                "errors": [],
                "warnings": ["no generator.py (empty stub directory)"],
            })
            n_total += 1
            n_warn += 1
            warn_kinds["missing_generator_py_stub"] += 1
            continue

        n_total += 1
        try:
            r = lint_generator(gen_path, validate=False)
        except Exception as e:
            records.append({
                "task_id_dir": sub.name,
                "status": "lint_raised",
                "errors": [f"linter raised: {type(e).__name__}: {e}"],
                "warnings": [],
            })
            n_err += 1
            err_kinds["lint_raised"] += 1
            continue

        rec = {
            "task_id_dir": sub.name,
            "status": ("pass" if not r.errors and not r.warnings
                       else ("warn" if not r.errors else "err")),
            "errors": list(r.errors),
            "warnings": list(r.warnings),
        }
        records.append(rec)

        if rec["status"] == "pass":
            n_pass += 1
        elif rec["status"] == "warn":
            n_warn += 1
        else:
            n_err += 1

        for e in r.errors:
            err_kinds[_classify(e)] += 1
        for w in r.warnings:
            warn_kinds[_classify(w)] += 1

        if args.verbose:
            mark = "✓" if rec["status"] == "pass" else (
                "!" if rec["status"] == "warn" else "✗")
            print(f"  {mark} {sub.name}: "
                  f"{len(r.errors)}E {len(r.warnings)}W")

    # Summary
    print()
    print(f"Generators: {n_total}")
    print(f"  ✓ pass      : {n_pass}  ({100*n_pass/max(n_total,1):.1f}%)")
    print(f"  ! warn-only : {n_warn}")
    print(f"  ✗ has-error : {n_err}")
    print()
    if err_kinds:
        print("Top error kinds:")
        for k, n in err_kinds.most_common(10):
            print(f"    {n:>4}× {k}")
    if warn_kinds:
        print("Top warning kinds:")
        for k, n in warn_kinds.most_common(10):
            print(f"    {n:>4}× {k}")

    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        print(f"\nwrote {out_path} ({len(records)} rows)", file=sys.stderr)

    if args.fail_on == "errors" and n_err > 0:
        return 1
    if args.fail_on == "warnings" and (n_err > 0 or n_warn > 0):
        return 1
    return 0


def _classify(msg: str) -> str:
    """Bucket lint message → short kind label for histogram."""
    msg = msg.lower()
    if "missing required module constant" in msg:
        # Pull out which constant
        for k in ("generator_id", "version", "task_id", "concept_hash",
                  "summary", "invariants", "axes"):
            if k in msg:
                return f"missing_{k.upper()}"
        return "missing_constant"
    if "task_id" in msg and "match" in msg:
        return "task_id_dirname_mismatch"
    if "concept_hash" in msg:
        return "concept_hash_stale"
    if "rule_reimplementation" in msg or "rule re" in msg:
        return "rule_reimplementation_smell"
    if "syntax error" in msg:
        return "python_syntax_error"
    if "no generator" in msg:
        return "missing_generator_py"
    if "axes" in msg and "empty" in msg:
        return "axes_empty"
    if "import random" in msg or "bare random" in msg:
        return "bare_random"
    if "generate" in msg and "signature" in msg:
        return "generate_signature"
    return msg.split(":")[0][:40]


if __name__ == "__main__":
    sys.exit(main())
