#!/usr/bin/env python3
"""Bounded sampler stress for the 2e9bbcd910a7 parametric adapter."""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "2e9bbcd910a7"


def load_prototype():
    root = find_root(__file__)
    path = root / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_stress_2e9bbcd910a7", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 1000:
        raise ValueError("seed_count must be an integer in 1..1000")
    proto = load_prototype()
    started = time.monotonic()
    episodes = 0
    pairs = 0
    failures = []
    shapes = set()
    lengths = set()
    directions = set()
    profiles = ((2, 4), (6, 4))
    for demos, queries in profiles:
        for seed in range(seed_count):
            generated = {}
            for target in proto.PAINT_TARGETS:
                try:
                    episode = proto.generate(seed, {"paint_target": target}, demos, queries)
                    generated[target] = episode
                    grids = [
                        pair["input"]
                        for split in ("train", "test")
                        for pair in episode[split]
                    ]
                    keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
                    if len(keys) != len(set(keys)) or len(keys) != demos + queries:
                        raise AssertionError("episode inputs are not distinct")
                    for grid in grids:
                        if proto.GEN.self_check(grid):
                            raise AssertionError("input left reviewed grammar")
                        winner = proto.GEN._ranked_runs(grid)[0]
                        shapes.add((len(grid), len(grid[0])))
                        lengths.add(len(winner["cells"]))
                        directions.add(winner["direction"])
                    episodes += 1
                    pairs += len(grids)
                except Exception as exc:  # retain bounded failure evidence
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "queries": queries,
                            "setting": target,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
            if set(generated) == set(proto.PAINT_TARGETS):
                canonical = generated["winner"]
                follower = generated["crossing_follower"]
                for split in ("train", "test"):
                    if [row["input"] for row in canonical[split]] != [
                        row["input"] for row in follower[split]
                    ]:
                        raise AssertionError("settings do not share matched inputs")
                    if not all(
                        left["output"] != right["output"]
                        for left, right in zip(canonical[split], follower[split])
                    ):
                        raise AssertionError("settings collapse on a generated pair")
    attempted = seed_count * len(profiles) * len(proto.PAINT_TARGETS)
    return {
        "schema": "arcpuzzles-parametric-sampler-stress-v1",
        "task_id": proto.TASK_ID,
        "seed_range": [0, seed_count - 1],
        "count_profiles": [
            {"demos": demos, "queries": queries} for demos, queries in profiles
        ],
        "settings": list(proto.PAINT_TARGETS),
        "episodes_attempted": attempted,
        "episodes_succeeded": episodes,
        "pairs_checked": pairs,
        "failures": failures,
        "coverage": {
            "shapes": [list(shape) for shape in sorted(shapes)],
            "winner_lengths": sorted(lengths),
            "winner_directions": sorted(directions),
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limits": "Finite Python sampler/label stress; protected Racket parity is established separately by native qualification.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "episodes_attempted",
                    "episodes_succeeded",
                    "pairs_checked",
                    "failures",
                    "coverage",
                    "elapsed_seconds",
                )
            },
            indent=2,
        )
    )
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
