"""Bounded adversarial audit for the 3a6ce35e3549 interior-mask family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent


def _load(name: str):
    path = BASE / f"{name}.py"
    module_name = f"_audit_3a6_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:10]}"
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
    rival_failures = []
    prefix_failures = []
    distinct_failures = []
    stress = []
    bounds_seen = set()
    output_shapes = set()
    episodes = 0
    pairs = 0
    for seed in range(seed_count):
        full = {
            mask: adapter.generate(seed, {"mask": mask}, 6, 4)
            for mask in family.SETTINGS
        }
        left_inputs = [p["input"] for p in full["blob"]["train"] + full["blob"]["test"]]
        right_inputs = [p["input"] for p in full["gaps"]["train"] + full["gaps"]["test"]]
        if left_inputs != right_inputs:
            prefix_failures.append({"seed": seed, "reason": "settings changed inputs"})
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in left_inputs]
        if len(encoded) != len(set(encoded)):
            distinct_failures.append({"seed": seed})
        for mask, episode in full.items():
            episodes += 1
            pairs += len(episode["train"]) + len(episode["test"])
            for pair in episode["train"] + episode["test"]:
                info = family.intermediate(pair["input"])
                bounds_seen.add(tuple(info["marker_bounds"]))
                output_shapes.add((len(pair["output"]), len(pair["output"][0])))
            survivors = set(family.RIVALS)
            for pair in episode["train"][:2]:
                survivors = {r for r in survivors
                             if family.solve_rival(pair["input"], mask, r) == pair["output"]}
            if survivors:
                rival_failures.append({"seed": seed, "mask": mask,
                                       "survivors": sorted(survivors)})
            stress_pair = episode["test"][-1]
            stress.append({
                "seed": seed,
                "mask": mask,
                "input_shape": [len(stress_pair["input"]), len(stress_pair["input"][0])],
                "output_shape": [len(stress_pair["output"]), len(stress_pair["output"][0])],
                "nonzero_input_cells": sum(v != 0 for row in stress_pair["input"] for v in row),
                "wrong_bounds_changes_output": (
                    family.solve_wrong_shifted_bounds(stress_pair["input"], mask)
                    != stress_pair["output"]
                ),
            })
        for demos in range(2, 7):
            for mask in family.SETTINGS:
                short = adapter.generate(seed, {"mask": mask}, demos, 1)
                expected = full[mask]
                if short["train"] != expected["train"][:demos] or short["test"] != expected["test"][:1]:
                    prefix_failures.append({"seed": seed, "mask": mask, "demos": demos})
    failures = rival_failures + prefix_failures + distinct_failures
    if any(row["input_shape"] != [30, 30] or row["nonzero_input_cells"] < 200
           or not row["wrong_bounds_changes_output"] for row in stress):
        failures.append({"reason": "stress or causal counterfactual condition failed"})
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
        "query_prefix_checked": 1,
        "marker_bounds_seen": len(bounds_seen),
        "output_shapes_seen": len(output_shapes),
        "stress_cases": stress,
        "failures": failures,
        "source_sha256": {
            name: sha256(BASE / name)
            for name in ("adapter.py", "family.py", "canonical.rkt", "gaps.rkt",
                         "wrong_shifted_bounds.rkt", "promotion.json")
        },
        "limits": (
            "Finite authored rivals and seeds only; this does not prove universal "
            "identifiability or owner acceptance. Racket replay is supplied by the native preflight."
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
    print(json.dumps({k: report[k] for k in ("status", "episodes_checked", "pairs_checked")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
