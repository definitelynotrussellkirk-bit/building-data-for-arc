#!/usr/bin/env python3
"""Bounded adversarial audit for the b9ada70e7181 native candidate.

This is deliberately task-local and reusable by later reviewers.  It attacks the
minimum two-demo lesson with semantic rivals, checks crossed controls and matched
inputs, replays representative labels through protected Racket, exercises the
base generator's documented dimension corners, and verifies certificate rejection
of duplicate/tampered data.  It writes one source-bound compact JSON report.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load(HERE / "prototype.py", "_b9ada70e7181_probe_prototype")
generator = _load(TASK_HOME / "generator.py", "_b9ada70e7181_probe_generator")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonpalindromic_stacks(grid: list[list[int]]) -> list[dict[str, Any]]:
    rows = []
    for column in range(len(grid[0])):
        values = [row[column] for row in grid if row[column] not in (0, 8)]
        if len(values) >= 2 and values != list(reversed(values)):
            rows.append({"column": column, "values": values})
    return rows


def run(seed_count: int) -> dict[str, Any]:
    started = time.monotonic()
    failures: list[dict[str, Any]] = []
    rival_rejections = {policy: {rival: 0 for rival in prototype.RIVAL_POLICIES[policy]}
                        for policy in prototype.GRAVITY_POLICIES}
    scene_count = 0
    episode_count = 0
    matched_input_checks = 0
    demo_cross_control_checks = 0
    threshold_shortcut_checks = 0
    parity_direction_counts = {"up": 0, "down": 0}
    dimensions: set[tuple[int, int]] = set()

    for seed in range(seed_count):
        episodes = {}
        for policy in prototype.GRAVITY_POLICIES:
            episode = prototype.generate(seed, {"gravity_policy": policy}, 2, 4)
            episodes[policy] = episode
            episode_count += 1
            try:
                prototype.certify(episode)
            except Exception as exc:  # pragma: no cover - retained failure evidence
                failures.append({"kind": "certificate", "seed": seed, "policy": policy,
                                 "error": f"{type(exc).__name__}: {exc}"})
            labels = [pair["output"] for pair in episode["train"]]
            for rival in prototype.RIVAL_POLICIES[policy]:
                guesses = [prototype.transform_rival(pair["input"], rival)
                           for pair in episode["train"]]
                if guesses == labels:
                    failures.append({"kind": "surviving_rival", "seed": seed,
                                     "policy": policy, "rival": rival})
                else:
                    rival_rejections[policy][rival] += 1
            for pair in episode["train"] + episode["test"]:
                report = prototype.analyze_scene(pair["input"])
                scene_count += 1
                dimensions.add((report["height"], report["width"]))
                for chamber in report["chambers"]:
                    parity_direction_counts[chamber["direction"]] += 1
                if {chamber["count"] % 2 for chamber in report["chambers"]} != {0, 1}:
                    failures.append({"kind": "missing_mixed_parity", "seed": seed,
                                     "policy": policy, "scene": scene_count})
                if not report["opposite_parity_shared_stack_profiles"]:
                    failures.append({"kind": "missing_crossed_stack_control", "seed": seed,
                                     "policy": policy, "scene": scene_count})
                if not report["mixed_column_count_chambers"]:
                    failures.append({"kind": "missing_mixed_column_counts", "seed": seed,
                                     "policy": policy, "scene": scene_count})
                if report["nonpalindromic_stack_count"] < 2:
                    failures.append({"kind": "weak_order_evidence", "seed": seed,
                                     "policy": policy, "scene": scene_count})
            if policy == "chamber_parity":
                threshold_shortcut_checks += 1
                threshold_survivors = prototype._threshold_shortcuts(episode["train"])
                if threshold_survivors:
                    failures.append({
                        "kind": "threshold_shortcut_survives",
                        "seed": seed,
                        "survivors": threshold_survivors,
                    })
                directions = [
                    [state["direction"] for state in prototype.derive_chamber_states(
                        pair["input"], "chamber_parity"
                    )]
                    for pair in episode["train"]
                ]
                common = min(map(len, directions))
                demo_cross_control_checks += 1
                if not any(
                    directions[0][index] != directions[1][index]
                    for index in range(common)
                ):
                    failures.append({"kind": "static_chamber_rank_survives", "seed": seed})
                if not any(
                    (directions[0][index] == directions[0][0])
                    != (directions[1][index] == directions[1][0])
                    for index in range(1, common)
                ):
                    failures.append({"kind": "first_chamber_relative_map_survives", "seed": seed})
        down_inputs = [pair["input"] for pair in episodes["all_down"]["train"] + episodes["all_down"]["test"]]
        parity_inputs = [pair["input"] for pair in episodes["chamber_parity"]["train"] + episodes["chamber_parity"]["test"]]
        matched_input_checks += 1
        if down_inputs != parity_inputs:
            failures.append({"kind": "setting_leakage_to_inputs", "seed": seed})

    base_failures = []
    base_draws = 0
    for height in range(6, 13):
        for width in range(9, 17):
            for seed in range(16):
                base_draws += 1
                try:
                    grid = generator.generate(
                        seed,
                        height * 100000 + width * 1000 + seed,
                        grid_h=height,
                        grid_w=width,
                    )
                    errors = generator.self_check(grid)
                    if errors or not nonpalindromic_stacks(grid):
                        base_failures.append({"height": height, "width": width,
                                              "seed": seed, "errors": errors})
                except Exception as exc:  # pragma: no cover - retained failure evidence
                    base_failures.append({"height": height, "width": width, "seed": seed,
                                          "error": f"{type(exc).__name__}: {exc}"})
    failures.extend({"kind": "base_boundary", **row} for row in base_failures)

    old_window = []
    for sample_index in (36, 37, 38, 39):
        grid = generator.generate(222, sample_index, difficulty="medium")
        old_window.append({
            "sample_index": sample_index,
            "self_check": generator.self_check(grid),
            "nonpalindromic_stacks": nonpalindromic_stacks(grid),
        })

    # Negative certificate cases: the certificate must recompute rather than
    # trusting serialized claims.
    negative_results = []
    clean = prototype.generate(41, {"gravity_policy": "chamber_parity"}, 2, 4)
    duplicate = copy.deepcopy(clean)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    tampered = copy.deepcopy(clean)
    tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
    bool_cell = copy.deepcopy(clean)
    bool_cell["train"][0]["input"][0][0] = True
    too_few = copy.deepcopy(clean)
    too_few["train"] = too_few["train"][:1]
    too_many = prototype.generate(42, {"gravity_policy": "chamber_parity"}, 6, 4)
    extra_input = prototype.sample_input(43, "demo", 0)
    too_many["train"].append({
        "input": extra_input,
        "output": prototype.transform(extra_input, too_many["settings"]),
    })
    stale_program = copy.deepcopy(clean)
    stale_program["program_solution"] = stale_program["program_solution"] + "\n"
    threshold_settings = {"gravity_policy": "chamber_parity"}
    threshold_train = [
        prototype.sample_input(1, "query", 3),
        prototype.sample_input(2, "query", 0),
    ]
    threshold_test = [prototype.sample_input(50, "query", index) for index in range(4)]
    threshold_lesson = {
        "settings": threshold_settings,
        "program_solution": prototype.program(threshold_settings),
        "train": [
            {"input": grid, "output": prototype.transform(grid, threshold_settings)}
            for grid in threshold_train
        ],
        "test": [
            {"input": grid, "output": prototype.transform(grid, threshold_settings)}
            for grid in threshold_test
        ],
    }
    for name, candidate in (
        ("duplicate_input", duplicate),
        ("tampered_label", tampered),
        ("bool_cell", bool_cell),
        ("too_few_demos", too_few),
        ("too_many_demos", too_many),
        ("stale_program", stale_program),
        ("threshold_lesson", threshold_lesson),
    ):
        try:
            prototype.certify(candidate)
        except ValueError as exc:
            negative_results.append({"case": name, "rejected": True, "error": str(exc)})
        else:
            negative_results.append({"case": name, "rejected": False})
            failures.append({"kind": "certificate_negative_accepted", "case": name})

    # Protected-Racket agreement on representative seeds, every pair and both
    # setting programs.  This is independent of the larger Python rival sweep.
    from arc_repl.racket_bridge import RacketBridge
    racket_evaluations = 0
    with RacketBridge(timeout=60) as bridge:
        runtime = bridge.runtime_identity
        for seed in (0, 17, max(0, seed_count - 1)):
            for policy in prototype.GRAVITY_POLICIES:
                episode = prototype.generate(seed, {"gravity_policy": policy}, 2, 4)
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(episode[split]):
                        racket_evaluations += 1
                        actual = prototype.execute_rule(
                            episode["program_solution"], pair["input"], bridge=bridge
                        )
                        if actual != pair["output"]:
                            failures.append({"kind": "racket_mismatch", "seed": seed,
                                             "policy": policy, "split": split,
                                             "pair_index": pair_index})

    source_files = [
        TASK_HOME / "generator.py",
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "adversarial_probe.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "parity.rkt",
        HERE / "tests" / "test_prototype.py",
        TASK_HOME / "tests" / "test_generator.py",
    ]
    return {
        "schema": "b9ada70e7181-adversarial-self-review-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "minimum_demos": 2,
        "queries_per_episode": 4,
        "episode_count": episode_count,
        "scene_count": scene_count,
        "matched_input_checks": matched_input_checks,
        "demo_cross_control_checks": demo_cross_control_checks,
        "threshold_shortcut_checks": threshold_shortcut_checks,
        "rival_rejections": rival_rejections,
        "parity_direction_counts": parity_direction_counts,
        "dimensions": [list(value) for value in sorted(dimensions)],
        "base_boundary_sweep": {
            "draws": base_draws,
            "failures": base_failures,
            "old_ambiguous_window_after_repair": old_window,
        },
        "certificate_negative_cases": negative_results,
        "protected_racket": {
            "evaluations": racket_evaluations,
            "runtime": {key: runtime[key] for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"
            ) if key in runtime},
        },
        "failures": failures,
        "source_sha256": {str(path.relative_to(REPO)): sha256(path) for path in source_files},
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "limits": (
            "Finite seeds and enumerated rivals do not prove universal uniqueness. "
            "Owner qualification/acceptance and fresh integration replay remain separate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1:
        raise SystemExit("--seeds must be positive")
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = run(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["episode_count"],
        "scenes": report["scene_count"],
        "base_draws": report["base_boundary_sweep"]["draws"],
        "racket_evaluations": report["protected_racket"]["evaluations"],
        "failures": len(report["failures"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
