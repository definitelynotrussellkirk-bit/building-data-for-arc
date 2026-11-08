#!/usr/bin/env python3
"""Measure per-color scatter-count and branch-histogram symmetry for this task.

The probe is intentionally independent of the review battery: it compares every
canonical input with deterministic default generator draws and writes a compact,
hash-bound JSON report suitable for before/after evidence.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "49c16a3506ab"
SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    spec = importlib.util.spec_from_file_location(f"scatter_probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ordered_profile(gen, grid):
    blocks = gen._find_blocks(grid)
    pair = gen._pair_name(value[0] for value in blocks.values())
    corners = gen._pair_corners(pair)
    colors_by_corner = {corner: color for color, (corner, _) in blocks.items()}
    scatter = gen._scatter_by_color(grid, blocks)
    counts = []
    branch_histograms = []
    for corner in corners:
        color = colors_by_corner[corner]
        cells = scatter[color]
        origin = blocks[color][1]
        counts.append(len(cells))
        branch_histograms.append(
            dict(sorted(collections.Counter(gen._classify(r, c, origin) for r, c in cells).items()))
        )
    return {
        "pair": pair,
        "counts": counts,
        "branch_histograms": branch_histograms,
        "equal_counts": counts[0] == counts[1],
        "equal_branch_histograms": branch_histograms[0] == branch_histograms[1],
    }


def canonical_profiles(gen):
    profiles = []
    for line_number, line in enumerate(CANONICAL_PATH.read_text().splitlines(), 1):
        if TASK_ID not in line:
            continue
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            pairs = row[split]
            pairs = [pairs] if isinstance(pairs, dict) else list(pairs)
            for pair_index, pair in enumerate(pairs):
                profiles.append(
                    {
                        "line": line_number,
                        "split": split,
                        "pair_index": pair_index,
                        **ordered_profile(gen, pair["input"]),
                    }
                )
    return profiles


def generated_summary(gen, samples):
    report = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles = []
        for index in range(samples):
            seed = 730_000 + band_index * 100_000 + index
            grid = gen.generate(seed, index * 37 + 11, difficulty=band)
            profiles.append(ordered_profile(gen, grid))
        count_pairs = collections.Counter(tuple(item["counts"]) for item in profiles)
        hist_pairs = collections.Counter(
            json.dumps(item["branch_histograms"], sort_keys=True, separators=(",", ":"))
            for item in profiles
        )
        report[band] = {
            "samples": samples,
            "equal_count_fraction": sum(item["equal_counts"] for item in profiles) / samples,
            "equal_branch_histogram_fraction": sum(
                item["equal_branch_histograms"] for item in profiles
            )
            / samples,
            "count_pairs": {f"{a},{b}": n for (a, b), n in sorted(count_pairs.items())},
            "distinct_branch_histogram_pairs": len(hist_pairs),
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples <= 0:
        parser.error("--samples must be positive")

    gen = load_generator()
    payload = {
        "schema": "scatter-profile-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "samples_per_band": args.samples,
        "canonical": canonical_profiles(gen),
        "generated": generated_summary(gen, args.samples),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
