"""Bounded adversarial self-review for the d3ace3f5d190 axis family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

BASE = Path(__file__).resolve().parent
TASK_HOME = BASE.parents[1]
ROOT = find_root(__file__)


def _load(name: str):
    path = BASE / f"{name}.py"
    module_name = f"_audit_d3a_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:10]}"
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
    sizes_seen: set[int] = set()
    selected_axes_seen: set[str] = set()
    main_conflicts_seen: set[int] = set()
    anti_conflicts_seen: set[int] = set()
    stress_cases: list[dict] = []

    canonical = canonical_pairs(family.TASK_ID, root=ROOT, labeled_only=True)
    for row in canonical:
        if base.rule_mirror(row["input"], "main") != row["output"]:
            failures.append(
                {
                    "reason": "canonical replay mismatch",
                    "variant": row["variant"],
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                }
            )

    production_draws = 0
    production_conflict_witnesses = 0
    production_blank_shortcut_witnesses = 0
    production_both_sides = 0
    for difficulty in (None, "easy", "hard"):
        for index in range(24):
            grid = base.generate(73_000 + index, index, difficulty=difficulty)
            production_draws += 1
            errors = base.self_check(grid)
            if errors:
                failures.append(
                    {
                        "reason": "production self_check failed",
                        "difficulty": difficulty,
                        "index": index,
                        "errors": errors,
                    }
                )
                continue
            info = base.analyze_scene(grid)
            if info["upper_marks"] and info["lower_marks"]:
                production_both_sides += 1
            if info["main_conflicts"]:
                production_conflict_witnesses += 1
            if base.rule_mirror(grid, "main") != base.copy_blank_only_rival(grid, "main"):
                production_blank_shortcut_witnesses += 1

    for texture in base.DEGENERATE_TEXTURES:
        if not base.self_check(base.generate(0, 0, texture=texture)):
            failures.append({"reason": "degenerate accepted", "texture": texture})

    control_probe = {
        "unknown_rejected": False,
        "size_conflict_rejected": False,
        "anchor_changes_scene": False,
        "palette_changes_scene": False,
        "asymmetry_changes_conflicts": False,
    }
    try:
        base.generate(0, 0, unknown_axis=True)
    except ValueError:
        control_probe["unknown_rejected"] = True
    try:
        base.generate(0, 0, grid_h=6, grid_w=7)
    except ValueError:
        control_probe["size_conflict_rejected"] = True
    control_probe["anchor_changes_scene"] = (
        base.generate(4, 2, grid_size=8, anchor_corner=True, palette_kind="warm")
        != base.generate(4, 2, grid_size=8, anchor_corner=False, palette_kind="warm")
    )
    control_probe["palette_changes_scene"] = (
        base.generate(7, 1, grid_size=9, palette_kind="warm")
        != base.generate(7, 1, grid_size=9, palette_kind="cool")
    )
    forced = base.generate(11, 3, grid_size=9, asymmetry_force=True)
    unforced = base.generate(11, 3, grid_size=9, asymmetry_force=False)
    control_probe["asymmetry_changes_conflicts"] = (
        base.analyze_scene(forced)["main_conflicts"] >= 1
        and base.analyze_scene(unforced)["main_conflicts"] == 0
    )
    if not all(control_probe.values()):
        failures.append({"reason": "declared control probe failed", "probe": control_probe})

    for seed in range(seed_count):
        full = {
            mode: adapter.generate(seed, {"axis_rule": mode}, 6, 4)
            for mode in family.SETTINGS
        }
        canonical_inputs = [
            pair["input"] for pair in full["main"]["train"] + full["main"]["test"]
        ]
        alternate_inputs = [
            pair["input"]
            for pair in full["anchor_selected"]["train"] + full["anchor_selected"]["test"]
        ]
        if canonical_inputs != alternate_inputs:
            failures.append({"reason": "settings changed sampled inputs", "seed": seed})
        if len({json.dumps(grid, separators=(",", ":")) for grid in canonical_inputs}) != 10:
            failures.append({"reason": "episode contains duplicate inputs", "seed": seed})

        episode_axes = {family.intermediate(grid)["selected_axis"] for grid in canonical_inputs}
        if episode_axes != {"main", "anti"}:
            failures.append(
                {"reason": "episode lacks both input-dependent axis decisions", "seed": seed, "seen": sorted(episode_axes)}
            )

        for demos in range(2, 7):
            for mode in family.SETTINGS:
                episode = adapter.generate(seed, {"axis_rule": mode}, demos, 4)
                episodes += 1
                if episode["train"] != full[mode]["train"][:demos] or episode["test"] != full[mode]["test"]:
                    failures.append(
                        {"reason": "prefix instability", "seed": seed, "demos": demos, "mode": mode}
                    )
                survivors = set(family.RIVALS)
                for split in ("train", "test"):
                    for pair in episode[split]:
                        pairs += 1
                        grid = pair["input"]
                        if family.solve(grid, mode) != pair["output"]:
                            failures.append(
                                {"reason": "Python claim mismatch", "seed": seed, "demos": demos, "mode": mode, "split": split}
                            )
                        errors = base.self_check(grid)
                        if errors:
                            failures.append(
                                {"reason": "family grid outside repaired base grammar", "seed": seed, "demos": demos, "mode": mode, "errors": errors}
                            )
                            continue
                        info = family.intermediate(grid)
                        sizes_seen.add(info["height"])
                        selected_axes_seen.add(info["selected_axis"])
                        main_conflicts_seen.add(info["main_conflicts"])
                        anti_conflicts_seen.add(info["anti_conflicts"])
                        if not info["unique_corner_anchor"]:
                            failures.append({"reason": "anchor is not unique", "seed": seed, "mode": mode})
                        if info["main_conflicts"] < 1 or info["anti_conflicts"] < 1:
                            failures.append({"reason": "missing axis conflict", "seed": seed, "mode": mode})
                    if split == "train":
                        for pair in episode[split]:
                            survivors = {
                                rival
                                for rival in survivors
                                if family.solve_rival(pair["input"], mode, rival) == pair["output"]
                            }
                if survivors:
                    failures.append(
                        {
                            "reason": "visible demonstrations leave semantic rival",
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "survivors": sorted(survivors),
                        }
                    )

        for mode in family.SETTINGS:
            stress = full[mode]["test"][-1]
            info = family.intermediate(stress["input"])
            counter_axis = "anti" if info["selected_axis"] == "main" else "main"
            stress_cases.append(
                {
                    "seed": seed,
                    "mode": mode,
                    "shape": [len(stress["input"]), len(stress["input"][0])],
                    "nonzero_input_cells": info["nonzero_cells"],
                    "selected_axis": info["selected_axis"],
                    "wrong_axis_changes_output": family.solve_axis(stress["input"], counter_axis) != stress["output"],
                }
            )

    if production_both_sides != production_draws:
        failures.append(
            {"reason": "production lacks marks on both diagonal sides", "draws": production_draws, "witnesses": production_both_sides}
        )
    if production_conflict_witnesses != production_draws:
        failures.append(
            {"reason": "production lacks conflicting transpose pairs", "draws": production_draws, "witnesses": production_conflict_witnesses}
        )
    if production_blank_shortcut_witnesses != production_draws:
        failures.append(
            {"reason": "production fails to refute copy-blank-only rival", "draws": production_draws, "witnesses": production_blank_shortcut_witnesses}
        )
    if any(
        row["shape"] != [30, 30]
        or row["nonzero_input_cells"] < 80
        or not row["wrong_axis_changes_output"]
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
        "canonical_pairs_replayed": len(canonical),
        "episodes_checked": episodes,
        "pairs_checked": pairs,
        "supported_demo_prefixes_checked": [2, 3, 4, 5, 6],
        "query_count_checked": 4,
        "sizes_seen": sorted(sizes_seen),
        "selected_axes_seen": sorted(selected_axes_seen),
        "main_conflict_counts_seen": sorted(main_conflicts_seen),
        "anti_conflict_counts_seen": sorted(anti_conflicts_seen),
        "production_probe": {
            "draws": production_draws,
            "both_sides_witnesses": production_both_sides,
            "conflicting_pair_witnesses": production_conflict_witnesses,
            "copy_blank_only_counterexamples": production_blank_shortcut_witnesses,
            "degenerates_rejected": list(base.DEGENERATE_TEXTURES),
            "control_probe": control_probe,
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
                    "anchor_selected.rkt",
                    "always_anti.rkt",
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
