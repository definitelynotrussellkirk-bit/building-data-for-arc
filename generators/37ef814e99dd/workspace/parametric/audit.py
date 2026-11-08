"""Bounded adversarial audit for the 37ef814e99dd boundary-scope family."""
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
    module_name = f"_audit_37ef_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:10]}"
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

    rival_failures: list[dict] = []
    prefix_failures: list[dict] = []
    distinct_failures: list[dict] = []
    domain_failures: list[dict] = []
    stress: list[dict] = []
    profiles_seen: set[str] = set()
    object_counts_seen: set[int] = set()
    bbox_witnesses = 0
    episodes = 0
    pairs = 0

    # Probe the repaired production domain independently of the authored family.
    production_profiles: set[str] = set()
    production_nonrectangular = 0
    for difficulty in (None, "medium", "hard"):
        for index in range(24):
            grid = base.generate(37_000 + index, index, difficulty=difficulty)
            errors = base.self_check(grid)
            if errors:
                domain_failures.append(
                    {"kind": "production_self_check", "difficulty": difficulty, "index": index, "errors": errors}
                )
                continue
            info = base.analyze_scene(grid)
            production_profiles.add(info["scene_profile"])
            production_nonrectangular += sum(not obj["solid_bbox"] for obj in info["objects"])
            if base.rule_mirror(grid) != base.bbox_outline_rival(grid):
                bbox_witnesses += 1
    for texture in base.DEGENERATE_TEXTURES:
        grid = base.generate(0, 0, texture=texture)
        if not base.self_check(grid):
            domain_failures.append({"kind": "degenerate_accepted", "texture": texture})

    for seed in range(seed_count):
        full = {
            scope: adapter.generate(seed, {"scope": scope}, 6, 4)
            for scope in family.SETTINGS
        }
        canonical_inputs = [
            pair["input"]
            for pair in full["all_objects"]["train"] + full["all_objects"]["test"]
        ]
        alternate_inputs = [
            pair["input"]
            for pair in full["largest_only"]["train"] + full["largest_only"]["test"]
        ]
        if canonical_inputs != alternate_inputs:
            prefix_failures.append({"seed": seed, "reason": "settings changed inputs"})
        encoded = [json.dumps(grid, separators=(",", ":")) for grid in canonical_inputs]
        if len(encoded) != len(set(encoded)):
            distinct_failures.append({"seed": seed, "reason": "duplicate episode input"})

        for scope, episode in full.items():
            episodes += 1
            pairs += len(episode["train"]) + len(episode["test"])
            for pair in episode["train"] + episode["test"]:
                info = family.intermediate(pair["input"])
                profiles_seen.add(info["scene_profile"])
                object_counts_seen.add(info["object_count"])
                if not info["largest_is_unique"]:
                    domain_failures.append({"seed": seed, "scope": scope, "reason": "largest tie"})
                if not any(not obj["solid_bbox"] for obj in info["objects"]):
                    domain_failures.append({"seed": seed, "scope": scope, "reason": "all-rectangle family input"})

            survivors = set(family.RIVALS)
            for pair in episode["train"][:2]:
                survivors = {
                    rival
                    for rival in survivors
                    if family.solve_rival(pair["input"], scope, rival) == pair["output"]
                }
            if survivors:
                rival_failures.append(
                    {"seed": seed, "scope": scope, "survivors": sorted(survivors)}
                )

            stress_pair = episode["test"][-1]
            stress_info = family.intermediate(stress_pair["input"])
            stress.append(
                {
                    "seed": seed,
                    "scope": scope,
                    "input_shape": [len(stress_pair["input"]), len(stress_pair["input"][0])],
                    "output_shape": [len(stress_pair["output"]), len(stress_pair["output"][0])],
                    "nonzero_input_cells": sum(
                        value != 0 for row in stress_pair["input"] for value in row
                    ),
                    "object_count": stress_info["object_count"],
                    "nonrectangular_objects": sum(
                        not obj["solid_bbox"] for obj in stress_info["objects"]
                    ),
                    "smallest_counterfactual_changes_output": (
                        family.solve_smallest_only(stress_pair["input"])
                        != stress_pair["output"]
                    ),
                }
            )

        for demos in range(2, 7):
            for scope in family.SETTINGS:
                short = adapter.generate(seed, {"scope": scope}, demos, 1)
                expected = full[scope]
                if (
                    short["train"] != expected["train"][:demos]
                    or short["test"] != expected["test"][:1]
                ):
                    prefix_failures.append(
                        {"seed": seed, "scope": scope, "demos": demos, "reason": "prefix instability"}
                    )

    failures = rival_failures + prefix_failures + distinct_failures + domain_failures
    if production_profiles != set(base.SCENE_PROFILES):
        failures.append(
            {"reason": "production profile coverage failed", "seen": sorted(production_profiles)}
        )
    if production_nonrectangular <= 0 or bbox_witnesses <= 0:
        failures.append(
            {
                "reason": "production did not refute bbox shortcut",
                "nonrectangular": production_nonrectangular,
                "bbox_witnesses": bbox_witnesses,
            }
        )
    if any(
        row["input_shape"] != [30, 30]
        or row["output_shape"] != [30, 30]
        or row["nonzero_input_cells"] < 180
        or row["nonrectangular_objects"] < 1
        or not row["smallest_counterfactual_changes_output"]
        for row in stress
    ):
        failures.append({"reason": "stress or causal-counterfactual condition failed"})

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
        "profiles_seen": sorted(profiles_seen),
        "object_counts_seen": sorted(object_counts_seen),
        "production_probe": {
            "draws": 72,
            "profiles_seen": sorted(production_profiles),
            "nonrectangular_objects": production_nonrectangular,
            "bbox_shortcut_witnesses": bbox_witnesses,
            "degenerates_rejected": list(base.DEGENERATE_TEXTURES),
        },
        "stress_cases": stress,
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
            "by the native preflight and causal witness."
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
