#!/usr/bin/env python3
"""Find a four-pair cbf77aa253ac lesson ambiguous to a horizontal-only rival.

Run from WORK/repo through review.py so the selected generator and runtime are
source-bound:
  python3 review.py run python3 ../checks/audit/cbf77aa253ac/find_shortcut.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "cbf77aa253ac"


def load_generator():
    path = Path("generators") / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def horizontal_only(module, grid):
    """Process guided components only when the inferred guide axis is horizontal."""
    plans = []
    for cells in module._components(grid):
        plan = module._component_plan(grid, cells)
        if plan is not None and plan["horizontal"]:
            plans.append(plan)
    return module._execute(grid, plans)[0]


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def search(*, seed_limit: int, start_limit: int):
    module, source_path = load_generator()
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    for band in (None, "easy", "medium", "hard"):
        for seed in range(seed_limit):
            for start in range(start_limit):
                pairs = []
                try:
                    for offset in range(4):
                        grid = module.generate(seed, start + offset, difficulty=band)
                        expected = module.rule_mirror(grid)
                        rival = horizontal_only(module, grid)
                        pairs.append({
                            "pair_index": offset,
                            "sample_index": start + offset,
                            "profile": module.observe_overrides(grid)["scene_profile"],
                            "input_sha256": grid_hash(grid),
                            "expected_sha256": grid_hash(expected),
                            "rival_sha256": grid_hash(rival),
                            "rival_matches_expected": rival == expected,
                            "input": grid,
                            "python_mirror_output": expected,
                            "horizontal_only_output": rival,
                        })
                except Exception:
                    continue
                for query_index in range(4):
                    demo_indices = [i for i in range(4) if i != query_index]
                    if (
                        all(pairs[i]["rival_matches_expected"] for i in demo_indices)
                        and not pairs[query_index]["rival_matches_expected"]
                    ):
                        return {
                            "schema": "arc-audit-lesson-shortcut-v1",
                            "task_id": TASK_ID,
                            "generator_sha256": source_sha,
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "demonstration_indices": demo_indices,
                            "rival": "horizontal_only",
                            "profiles": [pair["profile"] for pair in pairs],
                            "rival_fits_all_demonstrations": True,
                            "rival_changes_query": True,
                            "pairs": pairs,
                        }
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-limit", type=int, default=1000)
    parser.add_argument("--start-limit", type=int, default=80)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("../checks/audit/cbf77aa253ac/shortcut_counterexample.json"),
    )
    args = parser.parse_args()
    report = search(seed_limit=args.seed_limit, start_limit=args.start_limit)
    if report is None:
        print("no ambiguity found")
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": report["generator_sha256"],
        "band": report["band"],
        "seed": report["seed"],
        "start": report["start"],
        "query_index": report["query_index"],
        "profiles": report["profiles"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
