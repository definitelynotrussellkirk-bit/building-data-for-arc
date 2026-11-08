"""Bounded adversarial self-review for the 34f8510e39d0 scope family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
TASK_HOME = BASE.parents[1]


def _load(name: str):
    path = BASE / f"{name}.py"
    module_name = f"_audit_34f_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:10]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(seed_count: int = 32) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 256:
        raise ValueError("seed_count must be an exact integer in 1..256")
    family = _load("family")
    adapter = _load("adapter")
    base = family.generator

    failures: list[dict] = []
    episodes = 0
    pairs = 0
    sizes_seen: set[tuple[int, int]] = set()
    green_counts_seen: set[int] = set()
    palette_seen: set[int] = set()
    stress_cases: list[dict] = []

    production_draws = 0
    production_size_witnesses = 0
    for difficulty in (None, "medium", "hard"):
        for index in range(24):
            grid = base.generate(34_000 + index, index, difficulty=difficulty)
            production_draws += 1
            errors = base.self_check(grid)
            if errors:
                failures.append({"reason": "production self_check failed", "difficulty": difficulty, "index": index, "errors": errors})
                continue
            if base._has_size_matched_distractor(grid):
                production_size_witnesses += 1
            if base.rule_mirror(grid) == base._outline_rectangles_by_size_rival(grid):
                failures.append({"reason": "production failed to refute size-only selector", "difficulty": difficulty, "index": index})

    for seed in range(seed_count):
        full = {
            scope: adapter.generate(seed, {"scope": scope}, 6, 4)
            for scope in family.SETTINGS
        }
        left_inputs = [pair["input"] for pair in full["all_green"]["train"] + full["all_green"]["test"]]
        right_inputs = [pair["input"] for pair in full["largest_only"]["train"] + full["largest_only"]["test"]]
        if left_inputs != right_inputs:
            failures.append({"reason": "settings changed sampled inputs", "seed": seed})
        if len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) != 10:
            failures.append({"reason": "episode contains duplicate inputs", "seed": seed})

        for demos in range(2, 7):
            for scope in family.SETTINGS:
                episode = adapter.generate(seed, {"scope": scope}, demos, 4)
                episodes += 1
                survivors = set(family.RIVALS)
                for split in ("train", "test"):
                    for pair in episode[split]:
                        pairs += 1
                        grid = pair["input"]
                        expected = family.solve(grid, scope)
                        if pair["output"] != expected:
                            failures.append({"reason": "Python claim mismatch", "seed": seed, "demos": demos, "scope": scope, "split": split})
                        errors = base.self_check(grid)
                        if errors:
                            failures.append({"reason": "family grid outside base grammar", "seed": seed, "demos": demos, "scope": scope, "errors": errors})
                            continue
                        info = family.intermediate(grid)
                        sizes_seen.add((info["height"], info["width"]))
                        green_counts_seen.add(len(info["green_rectangles"]))
                        palette_seen.add(len({v for row in grid for v in row}))
                        areas = [row["area"] for row in info["green_rectangles"]]
                        if len(areas) < 2 or areas.count(max(areas)) != 1:
                            failures.append({"reason": "selection intermediate is not uniquely ranked", "seed": seed, "demos": demos, "scope": scope})
                        if not info["size_matched_distractor"]:
                            failures.append({"reason": "missing size-matched distractor", "seed": seed, "demos": demos, "scope": scope})
                    if split == "train":
                        for pair in episode[split]:
                            survivors = {
                                rival for rival in survivors
                                if family.solve_rival(pair["input"], scope, rival) == pair["output"]
                            }
                if survivors:
                    failures.append({"reason": "visible demonstrations leave rival", "seed": seed, "demos": demos, "scope": scope, "survivors": sorted(survivors)})

        for query_index, (all_pair, largest_pair) in enumerate(zip(full["all_green"]["test"], full["largest_only"]["test"])):
            if all_pair["output"] == largest_pair["output"]:
                failures.append({"reason": "query does not distinguish settings", "seed": seed, "query_index": query_index})
        stress = full["largest_only"]["test"][-1]
        stress_info = family.intermediate(stress["input"])
        stress_cases.append({
            "seed": seed,
            "shape": [len(stress["input"]), len(stress["input"][0])],
            "nonzero_input_cells": sum(v != 0 for row in stress["input"] for v in row),
            "green_rectangles": len(stress_info["green_rectangles"]),
            "smallest_counterfactual_changes_output": family.solve_smallest_only(stress["input"]) != stress["output"],
        })

    if production_size_witnesses != production_draws:
        failures.append({"reason": "production size witness missing", "draws": production_draws, "witnesses": production_size_witnesses})
    if any(
        row["shape"] != [30, 30]
        or row["nonzero_input_cells"] < 220
        or row["green_rectangles"] < 2
        or not row["smallest_counterfactual_changes_output"]
        for row in stress_cases
    ):
        failures.append({"reason": "30x30 stress or causal-counterfactual condition failed"})

    return {
        "schema": "arcpuzzles-task-parametric-self-review-v1",
        "task_id": family.TASK_ID,
        "status": "passed" if not failures else "failed",
        "seed_schedule": {"start": 0, "count": seed_count},
        "settings": list(family.SETTINGS),
        "semantic_rivals": list(family.RIVALS),
        "episodes_checked": episodes,
        "pairs_checked": pairs,
        "supported_demo_prefixes_checked": [2, 3, 4, 5, 6],
        "query_count_checked": 4,
        "sizes_seen": [list(item) for item in sorted(sizes_seen)],
        "green_counts_seen": sorted(green_counts_seen),
        "palette_sizes_seen": sorted(palette_seen),
        "production_probe": {
            "draws": production_draws,
            "size_matched_distractor_witnesses": production_size_witnesses,
        },
        "stress_cases": stress_cases,
        "failures": failures,
        "source_sha256": {
            "generator.py": sha256(TASK_HOME / "generator.py"),
            **{
                name: sha256(BASE / name)
                for name in (
                    "adapter.py",
                    "family.py",
                    "canonical.rkt",
                    "largest_only.rkt",
                    "smallest_only.rkt",
                    "promotion.json",
                )
            },
        },
        "limits": (
            "Finite authored rivals, seeds, and production probes only; this does not prove "
            "universal identifiability or owner acceptance. Protected Racket replay is supplied "
            "by the authoring preflight and causal witness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    report = build_report(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "episodes_checked", "pairs_checked")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
