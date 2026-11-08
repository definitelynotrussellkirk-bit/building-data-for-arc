"""Bounded deterministic self-review for the extension-mode family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seed_count: int, base_draws_per_band: int) -> dict:
    module = _load(HERE / "prototype.py", "_task_334c_audit_prototype")
    source = _load(TASK_HOME / "generator.py", "_task_334c_audit_generator")
    checked_pairs = 0
    large_query_banks = 0
    observed_sizes: set[tuple[int, int]] = set()
    observed_key_sizes: set[int] = set()
    observed_rectangle_counts: set[int] = set()
    minimum_canonical_change = None
    minimum_alternative_change = None

    for seed in range(seed_count):
        episodes = {
            mode: module.generate(seed, {"extension_mode": mode}, 6, 4)
            for mode in ("to_edges", "key_only")
        }
        edge_inputs = [
            pair["input"] for pair in episodes["to_edges"]["train"] + episodes["to_edges"]["test"]
        ]
        key_inputs = [
            pair["input"] for pair in episodes["key_only"]["train"] + episodes["key_only"]["test"]
        ]
        if edge_inputs != key_inputs:
            raise AssertionError("input generation depends on private setting")

        for mode, episode in episodes.items():
            if module.fit_settings(episode["train"][:2]) != [{"extension_mode": mode}]:
                raise AssertionError("minimum demonstrations do not identify extension_mode")
            for demos in range(2, 7):
                prefix = module.generate(seed, {"extension_mode": mode}, demos, 4)
                if prefix["train"] != episode["train"][:demos] or prefix["test"] != episode["test"]:
                    raise AssertionError("demonstration count changed another stream")
            for queries in range(1, 5):
                prefix = module.generate(seed, {"extension_mode": mode}, 2, queries)
                if prefix["test"] != episode["test"][:queries]:
                    raise AssertionError("query stream is not prefix stable")

        for grid in edge_inputs:
            facts = module.analyze(grid)
            canonical = module.transform(grid, {"extension_mode": "to_edges"})
            alternative = module.transform(grid, {"extension_mode": "key_only"})
            if canonical == alternative:
                raise AssertionError("settings agree on a generated scene")
            for setting, label in (
                ({"extension_mode": "to_edges"}, canonical),
                ({"extension_mode": "key_only"}, alternative),
            ):
                if module.no_key_erase(grid, setting) == label:
                    raise AssertionError("no-key-erase shortcut fits a generated label")
                if module.rotated_arm_colors(grid, setting) == label:
                    raise AssertionError("rotated-arm-color shortcut fits a generated label")
            canonical_change = sum(
                before != after
                for input_row, output_row in zip(grid, canonical)
                for before, after in zip(input_row, output_row)
            )
            alternative_change = sum(
                before != after
                for input_row, output_row in zip(grid, alternative)
                for before, after in zip(input_row, output_row)
            )
            minimum_canonical_change = (
                canonical_change
                if minimum_canonical_change is None
                else min(minimum_canonical_change, canonical_change)
            )
            minimum_alternative_change = (
                alternative_change
                if minimum_alternative_change is None
                else min(minimum_alternative_change, alternative_change)
            )
            observed_sizes.add((len(grid), len(grid[0])))
            observed_key_sizes.add(len(facts["key_offsets"]))
            observed_rectangle_counts.add(len(facts["rectangles"]))
            checked_pairs += 1

        large = [
            pair
            for pair in episodes["to_edges"]["test"]
            if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
        ]
        if len(large) != 1:
            raise AssertionError("four-query bank lacks exactly one 30x30 stress scene")
        facts = module.analyze(large[0]["input"])
        changed = sum(
            before != after
            for input_row, output_row in zip(large[0]["input"], large[0]["output"])
            for before, after in zip(input_row, output_row)
        )
        if len(facts["rectangles"]) < 3 or len(facts["key_offsets"]) < 11 or changed < 50:
            raise AssertionError("30x30 stress scene is not substantive")
        large_query_banks += 1

    base_draws = 0
    for difficulty in (None, "medium", "hard"):
        for index in range(base_draws_per_band):
            grid = source.generate(9000 + index, index, difficulty=difficulty)
            errors = source.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(f"base self-check failed: {difficulty=} {index=} {errors=}")
            facts = module.analyze(grid)
            if (
                len(facts["rectangles"]) != 1
                or len(facts["markers"]) != 1
                or len(facts["key_offsets"]) != 9
            ):
                raise AssertionError(f"base draw is not a single rectangle/radius-2 key: {difficulty=} {index=}")
            base_draws += 1

    return {
        "schema": "arcpuzzles-task-parametric-self-review-v1",
        "task_id": module.TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "episodes": seed_count * 2,
        "generated_pairs_checked": checked_pairs,
        "base_draws_checked": base_draws,
        "large_query_banks": large_query_banks,
        "observed_sizes": [list(size) for size in sorted(observed_sizes)],
        "observed_key_sizes": sorted(observed_key_sizes),
        "observed_rectangle_counts": sorted(observed_rectangle_counts),
        "minimum_changed_cells": {
            "to_edges": minimum_canonical_change,
            "key_only": minimum_alternative_change,
        },
        "checks": [
            "setting-independent matched inputs",
            "2..6 demonstration stream independence",
            "1..4 query prefix stability",
            "two-demo finite-setting identification",
            "to_edges versus key_only disagreement",
            "no-key-erase and rotated-arm-color shortcut rejection",
            "input-dependent key extraction across varied scenes",
            "one substantive 30x30 multi-rectangle scene in every four-query bank",
            "ordinary base draws parse across default, medium, and hard bands",
        ],
        "limits": "Finite deterministic audit; it does not prove uniqueness against all conceivable rules.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--base-draws-per-band", type=int, default=80)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        raise ValueError("--seeds must be in 1..256")
    if not 1 <= args.base_draws_per_band <= 512:
        raise ValueError("--base-draws-per-band must be in 1..512")
    result = audit(args.seeds, args.base_draws_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "pairs": result["generated_pairs_checked"],
                "base_draws": result["base_draws_checked"],
                "out": str(args.out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
