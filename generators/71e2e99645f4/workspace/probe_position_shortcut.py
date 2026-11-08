#!/usr/bin/env python3
"""Reproduce the canonical position shortcut and audit lesson coverage.

The rival is derived only from the four canonical demonstrations: it memorizes
pattern-to-color mappings separately for each of the three section positions and
uses the no-hole color 2 for an unseen position/pattern pair. The canonical query
contains all three unseen pairs at once. This probe also measures whether ordinary
generator draws and every three-of-four lesson rotation expose the shortcut.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_pairs, find_root

TASK_ID = "71e2e99645f4"
TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"position_shortcut_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_position_table(generator: Any, demonstrations: list[dict[str, Any]]):
    table: list[dict[str, int]] = [{}, {}, {}]
    for pair in demonstrations:
        patterns = generator.observe_overrides(pair["input"])["hole_patterns"]
        colors = [row[0] for row in pair["output"]]
        for index, (pattern, color) in enumerate(zip(patterns, colors)):
            existing = table[index].setdefault(pattern, color)
            if existing != color:
                raise ValueError(
                    f"inconsistent canonical class for position {index}, pattern {pattern}"
                )
    return tuple(table)


def rival_output(generator: Any, grid: Any, table) -> list[list[int]]:
    patterns = generator.observe_overrides(grid)["hole_patterns"]
    return [[table[index].get(pattern, 2)] * 3 for index, pattern in enumerate(patterns)]


def build_report(
    *,
    draws_per_band: int = 120,
    window_starts: int = 120,
    seeds: Iterable[int] = (0, 1, 2, 3),
    root: Path | None = None,
) -> dict[str, Any]:
    if draws_per_band <= 0 or window_starts <= 0:
        raise ValueError("draws_per_band and window_starts must be positive")
    seeds = tuple(seeds)
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a non-empty iterable of literal integers")

    root = find_root(__file__) if root is None else Path(root)
    generator = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=root)
    if len(pairs) != 5:
        raise ValueError(f"expected four demonstrations and one query, got {len(pairs)} pairs")
    demonstrations, query = pairs[:4], pairs[4]
    table = derive_position_table(generator, demonstrations)

    demo_rows = []
    for index, pair in enumerate(demonstrations):
        prediction = rival_output(generator, pair["input"], table)
        demo_rows.append(
            {
                "index": index,
                "patterns": generator.observe_overrides(pair["input"])["hole_patterns"],
                "fits": prediction == pair["output"],
                "rival_output": prediction,
            }
        )
    query_prediction = rival_output(generator, query["input"], table)

    draw_total = 0
    draw_disagreements = 0
    first_draw_witness = None
    band_draw_counts: dict[str, dict[str, int]] = {}
    for band in ("easy", "medium", "hard"):
        band_total = 0
        band_disagreements = 0
        for seed in seeds:
            for sample_index in range(draws_per_band):
                grid = generator.generate(seed, sample_index, difficulty=band)
                intended = generator.rule_mirror(grid)
                rival = rival_output(generator, grid, table)
                band_total += 1
                draw_total += 1
                if rival != intended:
                    band_disagreements += 1
                    draw_disagreements += 1
                    if first_draw_witness is None:
                        first_draw_witness = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "input": grid,
                            "patterns": generator.observe_overrides(grid)["hole_patterns"],
                            "intended_output": intended,
                            "rival_output": rival,
                        }
        band_draw_counts[band] = {
            "draws": band_total,
            "rival_disagreements": band_disagreements,
        }

    four_pair_windows = 0
    three_demo_rotations = 0
    surviving_rotations = 0
    minimum_refutations_in_window = 4
    first_survivor = None
    for band in ("easy", "medium", "hard"):
        for seed in seeds:
            for start in range(window_starts):
                grids = [
                    generator.generate(seed, start + offset, difficulty=band)
                    for offset in range(4)
                ]
                refutes = [
                    rival_output(generator, grid, table) != generator.rule_mirror(grid)
                    for grid in grids
                ]
                four_pair_windows += 1
                minimum_refutations_in_window = min(
                    minimum_refutations_in_window, sum(refutes)
                )
                for demo_indices in combinations(range(4), 3):
                    three_demo_rotations += 1
                    survives = not any(refutes[index] for index in demo_indices)
                    if survives:
                        surviving_rotations += 1
                        if first_survivor is None:
                            first_survivor = {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "demo_indices": list(demo_indices),
                                "patterns": [
                                    generator.observe_overrides(grids[index])["hole_patterns"]
                                    for index in demo_indices
                                ],
                            }

    source_bytes = GENERATOR_PATH.read_bytes()
    return {
        "schema": "71e2e99645f4-position-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "position_table": [dict(row) for row in table],
        "canonical": {
            "demonstrations": demo_rows,
            "demonstrations_all_fit": all(row["fits"] for row in demo_rows),
            "query_patterns": generator.observe_overrides(query["input"])["hole_patterns"],
            "query_intended_output": query["output"],
            "query_rival_output": query_prediction,
            "query_disagrees": query_prediction != query["output"],
        },
        "ordinary_draws": {
            "draws": draw_total,
            "rival_disagreements": draw_disagreements,
            "by_band": band_draw_counts,
            "first_witness": first_draw_witness,
        },
        "lesson_windows": {
            "four_pair_windows": four_pair_windows,
            "three_demo_rotations": three_demo_rotations,
            "surviving_three_demo_rotations": surviving_rotations,
            "minimum_refutations_per_four_pair_window": minimum_refutations_in_window,
            "first_survivor": first_survivor,
        },
        "scope": {
            "draws_per_band_per_seed": draws_per_band,
            "window_starts_per_band_per_seed": window_starts,
            "seeds": list(seeds),
            "bands": ["easy", "medium", "hard"],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-per-band", type=int, default=120)
    parser.add_argument("--window-starts", type=int, default=120)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(
        draws_per_band=args.draws_per_band,
        window_starts=args.window_starts,
        seeds=args.seeds,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
