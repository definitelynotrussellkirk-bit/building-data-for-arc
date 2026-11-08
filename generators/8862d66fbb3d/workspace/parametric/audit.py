#!/usr/bin/env python3
"""Bounded structural, teaching, and protected-Racket audit for this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "8862d66fbb3d"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = ("all_overlap", "adjacent_overlap")
RIVAL_FILES = {
    "horizontal_only": "horizontal_only.rkt",
    "vertical_only": "vertical_only.rkt",
    "eight_neighbor": "eight_neighbor.rkt",
    "degree_one_only": "degree_one_only.rkt",
    "left_mask_intermediate": "wrong_left_intermediate.rkt",
}


def _load_adapter():
    path = HERE / "adapter.py"
    name = "_audit_adapter_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _same_inputs(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(
        [pair["input"] for pair in left[split]] == [pair["input"] for pair in right[split]]
        for split in ("train", "test")
    )


def _structural(adapter, seed_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    episodes = pairs = public_turns = public_payloads = 0
    settings_jobs = fixed_domain_pairs = 0
    ids: set[str] = set()

    for seed in range(seed_count):
        for demos in range(2, 7):
            by_setting = {}
            for finish in SETTINGS:
                settings = {"finish": finish}
                try:
                    episode = adapter.generate(seed, settings, demos=demos, queries=4)
                    one = adapter.generate(seed, settings, demos=demos, queries=1)
                except Exception as error:
                    failures.append({
                        "seed": seed,
                        "demos": demos,
                        "setting": finish,
                        "kind": type(error).__name__,
                        "message": str(error),
                    })
                    continue
                episodes += 1
                settings_jobs += 1
                pairs += demos + 4
                by_setting[finish] = episode
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "count"})
                if episode["train"] != one["train"] or episode["test"][:1] != one["test"]:
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "prefix"})
                fingerprints = [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for split in ("train", "test") for pair in episode[split]
                ]
                if len(fingerprints) != len(set(fingerprints)):
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "duplicate_input"})
                certificate = adapter.teaching_check(episode)
                if certificate["surviving_rivals"]:
                    harmful.append({
                        "seed": seed,
                        "demos": demos,
                        "setting": finish,
                        "rivals": certificate["surviving_rivals"],
                    })
                for split in ("train", "test"):
                    for pair in episode[split]:
                        grid = pair["input"]
                        if len(grid) == 4 and len(grid[0]) == 7 and len(pair["output"]) == 3 and len(pair["output"][0]) == 3:
                            fixed_domain_pairs += 1
                        else:
                            failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "canonical_domain"})
                        if pair["output"] != adapter.solve(grid, settings):
                            failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "python_label"})
                first = adapter.public_turn(episode, 0)
                try:
                    public_challenge_bytes(first)
                    ids.add(public_challenge_id(first))
                    public_payloads += 1
                except Exception as error:
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "public_bytes", "message": str(error)})
                if first != adapter.public_turn(one, 0):
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "public_prefix"})
                for query_index in range(4):
                    turn = adapter.public_turn(episode, query_index)
                    public_turns += 1
                    expected = (
                        {"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
                         "test": [{"input": episode["test"][0]["input"]}]}
                        if query_index == 0
                        else {"test": [{"input": episode["test"][query_index]["input"]}]}
                    )
                    if turn != expected:
                        failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "public_turn", "query": query_index})
            if set(by_setting) == set(SETTINGS) and not _same_inputs(by_setting[SETTINGS[0]], by_setting[SETTINGS[1]]):
                failures.append({"seed": seed, "demos": demos, "kind": "settings_input_mismatch"})

    structural = {
        "seed_count": seed_count,
        "settings_jobs": settings_jobs,
        "episodes": episodes,
        "pairs": pairs,
        "fixed_4x7_to_3x3_pairs": fixed_domain_pairs,
        "public_turns": public_turns,
        "public_payloads": public_payloads,
        "unique_public_ids": len(ids),
        "domain_note": "The exact canonical program is intrinsically 4x7 input to 3x3 output; a 30x30 case would not preserve canonical behavior.",
        "failures": failures,
    }
    teaching = {
        "certificates": episodes,
        "named_rivals": ["other_setting", *RIVAL_FILES],
        "harmful_survivors": harmful,
        "scope_note": "Finite named rivals fitted to visible demonstrations only; not a proof of unique induction.",
    }
    return structural, teaching


def _protected_racket(adapter) -> dict[str, Any]:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    programs = {name: (HERE / filename).read_text(encoding="utf-8") for name, filename in RIVAL_FILES.items()}
    mismatches: list[dict[str, Any]] = []
    harmful: list[dict[str, Any]] = []
    cache: dict[tuple[str, str], list[list[int]]] = {}
    evaluations = 0

    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def run(program_text: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal evaluations
                key = (program_text, json.dumps(grid, separators=(",", ":")))
                if key not in cache:
                    cache[key] = apply(program_text, grid)
                    evaluations += 1
                return cache[key]

            for seed in (0, 17):
                for finish in SETTINGS:
                    settings = {"finish": finish}
                    episode = adapter.generate(seed, settings, demos=2, queries=4)
                    selected_program = adapter.program(settings)
                    alternate = {"finish": SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]}
                    rival_programs = {"other_setting": adapter.program(alternate), **programs}
                    labels: list[list[list[int]]] = []
                    rival_labels: dict[str, list[list[list[int]]]] = {name: [] for name in rival_programs}
                    all_pairs = episode["train"] + episode["test"]
                    for pair_index, pair in enumerate(all_pairs):
                        selected = run(selected_program, pair["input"])
                        labels.append(selected)
                        if selected != pair["output"]:
                            mismatches.append({"seed": seed, "setting": finish, "pair": pair_index, "rival": "selected_program"})
                        python_rivals = adapter.rival_outputs(pair["input"], settings)
                        for name, rival_program in rival_programs.items():
                            output = run(rival_program, pair["input"])
                            rival_labels[name].append(output)
                            if output != python_rivals[name]:
                                mismatches.append({"seed": seed, "setting": finish, "pair": pair_index, "rival": name})
                    for name, outputs in rival_labels.items():
                        fits_demos = outputs[:2] == labels[:2]
                        differs_query = any(left != right for left, right in zip(outputs[2:], labels[2:]))
                        if fits_demos and differs_query:
                            harmful.append({"seed": seed, "setting": finish, "rival": name})

            witness_episode = adapter.generate(0, {"finish": SETTINGS[1]}, demos=2, queries=4)
            witness_input = witness_episode["train"][0]["input"]
            selected_output = run(adapter.program({"finish": SETTINGS[1]}), witness_input)
            counterfactual_program = (HERE / "wrong_left_intermediate.rkt").read_text(encoding="utf-8")
            counterfactual_output = run(counterfactual_program, witness_input)
            causal = {
                "seed": 0,
                "pair": "train[0]",
                "ablation": "replace the command-dependent intersection with the raw left-panel mask before adjacency filtering",
                "outputs_differ": selected_output != counterfactual_output,
                "changed_cells": adapter.changed_cells(selected_output, counterfactual_output),
                "selected_matches_python": selected_output == adapter.solve(witness_input, {"finish": SETTINGS[1]}),
                "counterfactual_matches_python": counterfactual_output == adapter.wrong_intermediate_solve(witness_input),
            }
        finally:
            bridge.close()
    return {
        "executed": True,
        "runtime_identity": identity,
        "jobs": 4,
        "selected_and_rival_evaluations": evaluations,
        "python_racket_mismatches": mismatches,
        "harmful_survivors": harmful,
        "causal_counterfactual": causal,
    }


def build_report(seed_count: int = 64, execute_racket: bool = True) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an integer in 1..4096")
    adapter = _load_adapter()
    structural, teaching = _structural(adapter, seed_count)
    racket = _protected_racket(adapter) if execute_racket else {"executed": False}
    problems = bool(structural["failures"] or teaching["harmful_survivors"])
    if execute_racket:
        problems = problems or bool(
            racket["python_racket_mismatches"]
            or racket["harmful_survivors"]
            or not racket["causal_counterfactual"]["outputs_differ"]
            or not racket["causal_counterfactual"]["selected_matches_python"]
            or not racket["causal_counterfactual"]["counterfactual_matches_python"]
        )
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "status": "failed" if problems else "passed",
        "structural": structural,
        "teaching": teaching,
        "racket": racket,
        "sequential_dependency": {
            "step_a": "transform the right mask by the command and intersect it with the left mask",
            "intermediate": "the command-dependent 3x3 overlap mask",
            "step_b": "retain only overlap cells with an orthogonal overlap neighbor",
            "why_b_depends_on_a": "adjacency must be measured inside the intersection produced by step A, not in either source panel",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--skip-racket", action="store_true")
    args = parser.parse_args()
    report = build_report(seed_count=args.seeds, execute_racket=not args.skip_racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "status": report["status"],
        "episodes": report["structural"]["episodes"],
        "pairs": report["structural"]["pairs"],
        "racket_evaluations": report["racket"].get("selected_and_rival_evaluations", 0),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
