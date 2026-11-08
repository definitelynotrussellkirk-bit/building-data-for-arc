#!/usr/bin/env python3
"""Reproducible task-local shortcut census for cc100a8ad437.

Run from the repository root, for example::

    PYTHONPATH=shared/runtime python3 \
      generators/cc100a8ad437/workspace/review_census.py \
      --draws-per-band 2400 --out ../checks/probes/final_distribution.json

The report focuses on the failure modes that generic morphology gates missed:
origin-lattice placement, missing wildcard/orientation witnesses, overlapping
true windows, and loss of canonical-scale support.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import time

TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"
BANDS = ("easy", "medium", "hard")
CANONICAL_PROFILES = {(6, 12, 3), (7, 12, 3), (7, 13, 3)}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_cc100a8ad437_census", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _overlap(hits, shape_h: int, shape_w: int) -> bool:
    for index, (row, col) in enumerate(hits):
        for other_row, other_col in hits[index + 1 :]:
            if abs(row - other_row) < shape_h and abs(col - other_col) < shape_w:
                return True
    return False


def _grid_digest(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def census(draws_per_band: int, seed_base: int) -> dict:
    gen = _load_generator()
    started = time.perf_counter()
    report = {
        "schema": "cc100a8ad437-review-census-v1",
        "generator_version": gen.VERSION,
        "draws_per_band": draws_per_band,
        "seed_base": seed_base,
        "bands": {},
        "errors": [],
    }

    for band_index, band in enumerate(BANDS):
        counters = Counter()
        match_counts = Counter()
        profiles = Counter()
        textures = Counter()
        residue_total = 0
        minimum_residue_count = None
        digests = set()

        for index in range(draws_per_band):
            seed = seed_base + band_index * 1_000_000 + index
            sample_index = index
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
                left, board, _ = gen._split_input(grid)
                _, shape, color = gen._crop_template(left)
                hits = gen._match_positions(board, shape, color)
                shape_h, shape_w = gen._dims(shape)
                residues = {
                    (row % shape_h, col % shape_w) for row, col in hits
                }
                profile = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
            except Exception as exc:  # preserve the first few exact reproducers
                counters["crashes"] += 1
                if len(report["errors"]) < 20:
                    report["errors"].append(
                        {
                            "band": band,
                            "index": index,
                            "seed": seed,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                continue

            counters["draws"] += 1
            match_counts[len(hits)] += 1
            profiles[str(profile)] += 1
            textures[gen.schedule_profile(seed, sample_index, band)] += 1
            digests.add(_grid_digest(grid))
            residue_total += len(residues)
            minimum_residue_count = (
                len(residues)
                if minimum_residue_count is None
                else min(minimum_residue_count, len(residues))
            )
            if all(row % shape_h == 0 and col % shape_w == 0 for row, col in hits):
                counters["all_origin_lattice"] += 1
            if any(row % shape_h or col % shape_w for row, col in hits):
                counters["has_non_lattice_match"] += 1
            if _overlap(hits, shape_h, shape_w):
                counters["overlapping_match_windows"] += 1
            if gen.SEMANTIC_WITNESSES["wildcard_slot_clutter"](grid):
                counters["wildcard_witness"] += 1
            if gen.SEMANTIC_WITNESSES["same_color_orientation_decoy"](grid):
                counters["orientation_witness"] += 1
            if gen.SEMANTIC_WITNESSES["independent_match_offsets"](grid):
                counters["offset_witness"] += 1
            if profile in CANONICAL_PROFILES:
                counters["exact_canonical_profile"] += 1

        draws = counters["draws"]
        rate = lambda key: counters[key] / draws if draws else None
        report["bands"][band] = {
            "draws": draws,
            "crashes": counters["crashes"],
            "distinct_inputs": len(digests),
            "match_counts": dict(sorted(match_counts.items())),
            "schedule_profiles": dict(sorted(textures.items())),
            "minimum_offset_residue_count": minimum_residue_count,
            "mean_offset_residue_count": residue_total / draws if draws else None,
            "all_origin_lattice_rate": rate("all_origin_lattice"),
            "non_lattice_witness_rate": rate("has_non_lattice_match"),
            "offset_rival_refutation_rate": rate("offset_witness"),
            "wildcard_rival_refutation_rate": rate("wildcard_witness"),
            "orientation_rival_refutation_rate": rate("orientation_witness"),
            "overlap_rate": rate("overlapping_match_windows"),
            "exact_canonical_profile_rate": rate("exact_canonical_profile"),
            "top_profiles": profiles.most_common(12),
        }

    report["elapsed_seconds"] = time.perf_counter() - started
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=600)
    parser.add_argument("--seed-base", type=int, default=0xCC100000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.draws_per_band < 1:
        parser.error("--draws-per-band must be positive")
    result = census(args.draws_per_band, args.seed_base)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
