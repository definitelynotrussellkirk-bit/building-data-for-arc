#!/usr/bin/env python3
"""Source-bound curriculum probe for ARC task 7f3446077e8e.

This is deliberately independent of generator.rule_mirror: it derives the
translation from the visible colors, checks the declared diagonal-only rival,
and enumerates every single-query holdout in consecutive four-pair windows.
It is finite evidence for the named rival, not a proof of unique induction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7f3446077e8e"
HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == color]


def intended(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    p8 = positions(grid, 8)[0]
    p9 = positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    for r, c in positions(grid, 2):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 3
    return out


def diagonal_only(grid):
    p8 = positions(grid, 8)[0]
    p9 = positions(grid, 9)[0]
    dr, dc = p9[0] - p8[0], p9[1] - p8[1]
    return intended(grid) if dr and dc else deepcopy(grid)


def vector(grid):
    p8 = positions(grid, 8)[0]
    p9 = positions(grid, 9)[0]
    return p9[0] - p8[0], p9[1] - p8[1]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def run(seeds: int, windows: int) -> dict[str, Any]:
    gen = load_generator()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_fits = [diagonal_only(pair["input"]) == pair["output"] for pair in canonical]

    band_results = {}
    example_witness = None
    all_inputs = set()
    for band in ("easy", "medium", "hard"):
        ambiguous = []
        schedule_failures = []
        rotations = 0
        for seed in range(seeds):
            for start in range(windows):
                pairs = []
                modes = []
                for offset in range(4):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    label = intended(grid)
                    pairs.append({"input": grid, "output": label})
                    all_inputs.add(frozen(grid))
                    dr, dc = vector(grid)
                    modes.append("axial" if (dr == 0) ^ (dc == 0) else "diagonal")
                    if example_witness is None and modes[-1] == "axial":
                        rival = diagonal_only(grid)
                        example_witness = {
                            "seed": seed,
                            "sample_index": start + offset,
                            "difficulty": band,
                            "delta": [dr, dc],
                            "input": grid,
                            "intended_output": label,
                            "diagonal_only_output": rival,
                            "differences": [
                                {"row": r, "col": c,
                                 "intended": label[r][c], "rival": rival[r][c]}
                                for r in range(len(grid))
                                for c in range(len(grid[0]))
                                if label[r][c] != rival[r][c]
                            ],
                        }
                if modes.count("axial") != 2:
                    schedule_failures.append({"seed": seed, "start": start, "modes": modes})
                for query_index, query in enumerate(pairs):
                    rotations += 1
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    fits = all(diagonal_only(pair["input"]) == pair["output"] for pair in demos)
                    changes = diagonal_only(query["input"]) != query["output"]
                    if fits and changes:
                        ambiguous.append({
                            "seed": seed, "start": start,
                            "query_index": query_index, "modes": modes,
                        })
        band_results[band] = {
            "windows": seeds * windows,
            "rotations": rotations,
            "schedule_failures": schedule_failures,
            "ambiguous_rotations": ambiguous,
        }

    return {
        "schema": "7f3446077e8e-shortcut-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "label_basis": "independent Python coordinate oracle in this file",
        "scope": {
            "seeds": seeds,
            "consecutive_starts_per_seed": windows,
            "bands": ["easy", "medium", "hard"],
            "pairs_per_window": 4,
            "query_policy": "all four single-pair holdouts",
        },
        "canonical": {
            "labeled_pairs": len(canonical),
            "diagonal_only_fit_count": sum(canonical_fits),
            "fits_each": canonical_fits,
        },
        "bands": band_results,
        "unique_generated_inputs": len(all_inputs),
        "axial_counterexample": example_witness,
        "verdict": "no_named_rival_ambiguity_found" if (
            all(not info["schedule_failures"] and not info["ambiguous_rotations"]
                for info in band_results.values())
            and all(canonical_fits)
            and example_witness is not None
        ) else "finding",
        "limitations": [
            "finite check of the declared diagonal-only rival only",
            "uses consecutive sample indices; other assemblers must preserve that schedule",
            "generated labels come from an independent Python oracle, not live Racket",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--windows", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds, args.windows)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps({
        "verdict": report["verdict"],
        "unique_generated_inputs": report["unique_generated_inputs"],
        "canonical": report["canonical"],
        "bands": {
            name: {
                "windows": info["windows"],
                "rotations": info["rotations"],
                "schedule_failures": len(info["schedule_failures"]),
                "ambiguous_rotations": len(info["ambiguous_rotations"]),
            }
            for name, info in report["bands"].items()
        },
    }, indent=2))
    raise SystemExit(0 if report["verdict"] == "no_named_rival_ambiguity_found" else 1)


if __name__ == "__main__":
    main()
