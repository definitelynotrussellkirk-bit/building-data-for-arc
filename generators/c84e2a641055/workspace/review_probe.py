#!/usr/bin/env python3
"""Fast source-bound rival and rotation probe for c84e2a641055.

This is deliberately independent of the heavier Racket-backed lesson census.  It
uses the generator's Python mirror to give future reviewers an immediate exact
counterexample for every declared canonical shortcut and to exhaust a requested
set of consecutive lesson starts and single-query rotations.  Confirm any final
claim with ``arcpuzzles apply`` / ``lesson-census``; this probe is a development
reproducer, not an authority replacement.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]

# Work in both the full repository and the portable task-test runtime.
for candidate in (TASK_DIR, *TASK_DIR.parents):
    runtime = candidate / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (candidate / "reviewer_support.py").is_file():
        sys.path.insert(0, str(candidate))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_generator_c84e2a641055", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counterexample(shortcut, *, seed: int, search_limit: int) -> dict[str, Any] | None:
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(search_limit):
            grid = GEN.generate(seed, sample_index, difficulty=difficulty)
            intended = GEN.rule_mirror(grid)
            rival = shortcut(grid)
            if rival != intended:
                return {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "observed_overrides": GEN.observe_overrides(grid),
                    "input": grid,
                    "intended_output": intended,
                    "rival_output": rival,
                }
    return None


def build_report(*, seed: int = 7300, starts: int = 16) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(starts) is not int or starts < 1:
        raise ValueError("starts must be a positive integer")

    root = find_root(__file__)
    public_pairs = canonical_pairs(GEN.TASK_ID, root=root, labeled_only=True)
    shortcuts: dict[str, Any] = {}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        matches = [shortcut(pair["input"]) == pair["output"] for pair in public_pairs]
        shortcuts[name] = {
            "canonical_matches": sum(matches),
            "canonical_total": len(matches),
            "fits_all_canonical": all(matches),
            "counterexample": _counterexample(
                shortcut,
                seed=seed,
                search_limit=max(16, starts + GEN.EXAMPLES_NEEDED),
            ),
        }

    rotation_failures: list[dict[str, Any]] = []
    schedule_counts: dict[str, int] = {}
    checked_rotations = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(starts):
            materialized = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                profile = str(GEN.schedule_profile(seed, sample_index, difficulty))
                schedule_counts[profile] = schedule_counts.get(profile, 0) + 1
                materialized.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(materialized):
                demos = [
                    pair for index, pair in enumerate(materialized) if index != query_index
                ]
                reasons = GEN.lesson_identifiable(demos, query)
                ambiguous = [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(rival(demo["input"]) == demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ]
                checked_rotations += 1
                if reasons or ambiguous:
                    rotation_failures.append(
                        {
                            "difficulty": difficulty,
                            "start": start,
                            "query_index": query_index,
                            "reasons": list(reasons),
                            "ambiguous_rivals": ambiguous,
                        }
                    )

    generator_path = TASK_DIR / "generator.py"
    return {
        "schema": "c84e2a641055-review-probe-v1",
        "task_id": GEN.TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": _sha256(generator_path),
        "rule_hash": GEN.RULE_HASH,
        "seed": seed,
        "starts_per_band": starts,
        "canonical_pair_count": len(public_pairs),
        "canonical_shortcuts": shortcuts,
        "checked_rotations": checked_rotations,
        "rotation_failures": rotation_failures,
        "schedule_counts": dict(sorted(schedule_counts.items())),
        "authority_note": (
            "Outputs here use generator.rule_mirror; confirm retained claims with "
            "the selected Racket authority."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7300)
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--out", default="-", help="JSON path, or - for stdout")
    args = parser.parse_args(argv)
    report = build_report(seed=args.seed, starts=args.starts)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        sys.stdout.write(rendered)
    else:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
