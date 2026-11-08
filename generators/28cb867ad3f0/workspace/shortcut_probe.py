#!/usr/bin/env python3
"""Probe canonical shortcut fit and finite lesson identifiability for 28cb867ad3f0.

Run from a review packet through ``review.py run``.  This is a Python authoring
probe over the selected generator source; use ``arcpuzzles lesson-census`` for
Racket-labelled production evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "28cb867ad3f0"
BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def _predict(rival, grid):
    original = deepcopy(grid)
    output = rival(grid)
    if grid != original:
        raise AssertionError("rival mutated its input")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--per-band", type=int, default=36)
    args = parser.parse_args(argv)
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    if args.out.exists():
        parser.error("--out must be a new path")

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root)
    rivals: dict[str, Any] = dict(gen.SEMANTIC_RIVALS)

    canonical_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        rows = []
        for pair in canonical:
            guess = _predict(rival, deepcopy(pair["input"]))
            rows.append({
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "matches": guess == pair["output"],
                "diff_cells": _diff_cells(guess, pair["output"]),
            })
        canonical_fit[name] = {
            "pairs": len(rows),
            "matches": sum(row["matches"] for row in rows),
            "details": rows,
        }

    generated = {}
    first_counterexample = {}
    for band in BANDS:
        counts = {name: 0 for name in rivals}
        unique_inputs = set()
        for index in range(args.per_band):
            grid = gen.generate(args.seed, index, difficulty=band)
            expected = gen.rule_mirror(grid)
            unique_inputs.add(_grid_hash(grid))
            for name, rival in rivals.items():
                guess = _predict(rival, deepcopy(grid))
                if guess != expected:
                    counts[name] += 1
                    first_counterexample.setdefault(name, {
                        "band": band,
                        "seed": args.seed,
                        "sample_index": index,
                        "scene_profile": gen.observe_overrides(grid)["scene_profile"],
                        "input_sha256": _grid_hash(grid),
                        "diff_cells": _diff_cells(expected, guess),
                        "input": grid,
                        "intended_output": expected,
                        "rival_output": guess,
                    })
        generated[band] = {
            "draws": args.per_band,
            "unique_inputs": len(unique_inputs),
            "rival_disagreements": counts,
        }

    period = gen.LESSON_SCHEDULE_PERIOD
    schedule = {
        "period": period,
        "window_size": gen.EXAMPLES_NEEDED + 1,
        "bands": {},
        "ambiguous_rotations": 0,
        "hook_warnings": 0,
        "first_failure": None,
    }
    for band in BANDS:
        band_rows = {"windows": period, "rotations": 0, "profiles": {}}
        for start in range(period):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = gen.generate(args.seed, index, difficulty=band)
                profile = gen.observe_overrides(grid)["scene_profile"]
                band_rows["profiles"][profile] = band_rows["profiles"].get(profile, 0) + 1
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                band_rows["rotations"] += 1
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                surviving = [
                    name for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(_predict(rival, deepcopy(pair["input"])) == pair["output"] for pair in demos)
                    and _predict(rival, deepcopy(query["input"])) != query["output"]
                ]
                if reasons:
                    schedule["hook_warnings"] += 1
                if surviving:
                    schedule["ambiguous_rotations"] += 1
                if (reasons or surviving) and schedule["first_failure"] is None:
                    schedule["first_failure"] = {
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "hook_reasons": reasons,
                        "surviving_rivals": surviving,
                    }
        schedule["bands"][band] = band_rows

    report = {
        "schema": "28cb867ad3f0-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": gen.RULE_HASH,
        "version": gen.VERSION,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "settings": {"seed": args.seed, "per_band": args.per_band, "bands": list(BANDS)},
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "generated": generated,
        "first_counterexample": first_counterexample,
        "schedule": schedule,
        "limits": [
            "Python mirror and declared-rival probe; not independent Racket authority evidence.",
            "Finite generated census and one fixed seed; not a proof against undeclared rules.",
            "Raw consecutive samples; production accepted-pair behavior is checked separately.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "canonical_shortcuts": canonical_fit,
        "schedule": {
            "period": period,
            "ambiguous_rotations": schedule["ambiguous_rotations"],
            "hook_warnings": schedule["hook_warnings"],
        },
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
