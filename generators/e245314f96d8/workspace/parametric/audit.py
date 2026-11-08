#!/usr/bin/env python3
"""Bounded native-family and repaired-production audit for e245314f96d8."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root

TASK = "e245314f96d8"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _binary_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return tuple(tuple(1 if grid[r][c] else 0 for c in range(left, right + 1)) for r in range(top, bottom + 1))


def _rotate(grid):
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _flip(grid):
    return tuple(tuple(reversed(row)) for row in grid)


def _d4_key(grid):
    cropped = _binary_crop(grid)
    variants = []
    for reflected in (False, True):
        current = _flip(cropped) if reflected else cropped
        for _ in range(4):
            variants.append(current)
            current = _rotate(current)
    return min(variants)


def _topology_signature(generator, grid):
    facts = generator._analyze(grid)["facts"]
    by_degree = {
        degree: next(index for index, value in enumerate(facts["degrees"]) if value == degree)
        for degree in (2, 3, 4)
    }
    return tuple(
        by_degree[right] in facts["graph"][by_degree[left]]
        for left, right in ((4, 3), (4, 2), (3, 2))
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--production-seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256 or not 1 <= args.production_seeds <= 256:
        raise SystemExit("seed counts must be in [1, 256]")

    adapter = _load(HOME / "adapter.py", "audit_e245_contact_adapter")
    generator = adapter._PRODUCTION
    settings = [dict(item) for item in adapter.SETTINGS]
    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    episodes = pairs = stress_30 = causal_disagreements = 0

    for seed in range(args.seeds):
        baselines = {_key(setting): adapter.generate(seed, setting, 6, 4) for setting in settings}
        first_inputs = [pair["input"] for split in ("train", "test") for pair in baselines[_key(settings[0])][split]]
        for setting in settings[1:]:
            other_inputs = [pair["input"] for split in ("train", "test") for pair in baselines[_key(setting)][split]]
            if other_inputs != first_inputs:
                failures.append({"seed": seed, "kind": "settings_changed_inputs", "settings": setting})
        left, right = (baselines[_key(setting)] for setting in settings)
        causal_disagreements += sum(
            a["output"] != b["output"]
            for split in ("train", "test")
            for a, b in zip(left[split], right[split], strict=True)
        )
        for setting in settings:
            baseline = baselines[_key(setting)]
            if baseline != adapter.generate(seed, setting, 6, 4):
                failures.append({"seed": seed, "kind": "nondeterministic", "settings": setting})
            for demos in (2, 3, 6):
                for queries in (1, 4):
                    episode = adapter.generate(seed, setting, demos, queries)
                    episodes += 1
                    pairs += demos + queries
                    if episode["train"] != baseline["train"][:demos] or episode["test"] != baseline["test"][:queries]:
                        failures.append({"seed": seed, "kind": "prefix_instability", "settings": setting, "demos": demos, "queries": queries})
                    holes = adapter.audit_episode(episode, setting["contact_neighborhood"])
                    if holes:
                        failures.append({"seed": seed, "kind": "teaching_rival_survived", "settings": setting, "demos": demos, "details": holes})
                    for pair in episode["train"] + episode["test"]:
                        unique_inputs.add(_key(pair["input"]))
                        if adapter.solve(pair["input"], setting) != pair["output"]:
                            failures.append({"seed": seed, "kind": "python_label_mismatch", "settings": setting})
                        if len(pair["input"]) == len(pair["input"][0]) == 30:
                            stress_30 += 1

    normalized_masks = set()
    topologies = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(args.production_seeds):
            grid = generator.generate(
                20_000 + seed,
                band_index * 10_000 + seed * 3 + 2,
                difficulty=band,
                scene_profile="all_degrees",
            )
            normalized_masks.add(_d4_key(grid))
            topologies.add(_topology_signature(generator, grid))
            if generator.self_check(grid, meta={"scene_profile": "all_degrees"}):
                failures.append({"seed": seed, "band": band, "kind": "production_self_check_failed"})
    if len(normalized_masks) < 48:
        failures.append({"kind": "finite_template_regression", "normalized_masks": len(normalized_masks), "minimum": 48})
    if len(topologies) != 3:
        failures.append({"kind": "topology_coverage_regression", "topology_count": len(topologies), "expected": 3})

    protected_evaluations = 0
    protected_identity = None
    from arcpuzzles.parametric_worker import _real_evaluator

    evaluate, protected_identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
    try:
        replay_seeds = sorted({0, min(17, args.seeds - 1)})
        for seed in replay_seeds:
            episode = adapter.generate(seed, settings[0], 2, 4)
            grids = [pair["input"] for pair in episode["train"]] + [episode["test"][-1]["input"]]
            for setting in settings:
                text = adapter.program(setting)
                for grid in grids:
                    protected_evaluations += 1
                    actual = evaluate(text, grid)
                    expected = adapter.solve(grid, setting)
                    if actual != expected:
                        failures.append({
                            "seed": seed,
                            "kind": "protected_racket_mismatch",
                            "settings": setting,
                            "input_sha256": hashlib.sha256(_key(grid).encode()).hexdigest(),
                        })
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": TASK,
        "seed_count": args.seeds,
        "production_seed_count_per_band": args.production_seeds,
        "settings": settings,
        "demo_counts": [2, 3, 6],
        "query_counts": [1, 4],
        "episodes": episodes,
        "pairs_checked": pairs,
        "unique_input_count": len(unique_inputs),
        "causal_setting_disagreements": causal_disagreements,
        "stress_30_pair_occurrences": stress_30,
        "production_d4_normalized_masks": len(normalized_masks),
        "production_internal_topologies": len(topologies),
        "protected_racket_evaluations": protected_evaluations,
        "racket": protected_identity,
        "failure_count": len(failures),
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "finite_scope_note": "Finite seeds and the declared rival bank do not prove universal rule uniqueness.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "task_id", "status", "episodes", "pairs_checked", "unique_input_count",
        "causal_setting_disagreements", "stress_30_pair_occurrences",
        "production_d4_normalized_masks", "production_internal_topologies",
        "protected_racket_evaluations", "failure_count",
    )}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
