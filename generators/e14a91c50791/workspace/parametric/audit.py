#!/usr/bin/env python3
"""Bounded structural, teaching, public-projection, and Racket audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "e14a91c50791"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SETTINGS = ("bbox_only", "largest_orange_cluster")
RIVAL_FILES = {
    "mark_all_orange": "mark_all_orange.rkt",
    "first_orange_component": "first_orange_component.rkt",
    "wrong_intermediate": "wrong_intermediate.rkt",
}


def load_adapter():
    path = HERE / "adapter.py"
    name = "_e14_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def same_inputs(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(
        [pair["input"] for pair in left[split]] == [pair["input"] for pair in right[split]]
        for split in ("train", "test")
    )


def structural(adapter, seed_count: int) -> dict[str, Any]:
    failures = []
    harmful = []
    episodes = pairs = public_turns = stress = 0
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
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": type(error).__name__, "message": str(error)})
                    continue
                by_setting[finish] = episode
                episodes += 1
                pairs += demos + 4
                if episode["train"] != one["train"] or episode["test"][:1] != one["test"]:
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "prefix"})
                teaching = adapter.teaching_check(episode)
                if teaching["surviving_rivals"]:
                    harmful.append({"seed": seed, "demos": demos, "setting": finish, "rivals": teaching["surviving_rivals"]})
                for query_index in range(4):
                    turn = adapter.public_turn(episode, query_index)
                    public_turns += 1
                    if query_index == 0:
                        try:
                            public_challenge_bytes(turn)
                            ids.add(public_challenge_id(turn))
                        except Exception as error:
                            failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "public", "message": str(error)})
                    if any("output" in pair for pair in turn.get("test", [])):
                        failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "query_answer_leak"})
                large = episode["test"][3]["input"]
                if len(large) == 30 and len(large[0]) == 30 and sum(v != 0 for row in large for v in row) >= 25:
                    stress += 1
                else:
                    failures.append({"seed": seed, "demos": demos, "setting": finish, "kind": "stress"})
            if set(by_setting) == set(SETTINGS) and not same_inputs(by_setting[SETTINGS[0]], by_setting[SETTINGS[1]]):
                failures.append({"seed": seed, "demos": demos, "kind": "matched_inputs"})
    return {
        "seed_count": seed_count,
        "episodes": episodes,
        "pairs": pairs,
        "public_turns": public_turns,
        "unique_first_turn_ids": len(ids),
        "stress_30x30_cases": stress,
        "harmful_declared_rival_survivors": harmful,
        "failures": failures,
    }


def protected_racket(adapter) -> dict[str, Any]:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    rival_programs = {name: (HERE / filename).read_text(encoding="utf-8") for name, filename in RIVAL_FILES.items()}
    mismatches = []
    harmful = []
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
                    labels = []
                    selected_program = adapter.program(settings)
                    programs = {
                        "other_setting": adapter.program({"finish": SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]}),
                        **rival_programs,
                    }
                    rival_labels = {name: [] for name in programs}
                    for pair_index, pair in enumerate(episode["train"] + episode["test"]):
                        selected = run(selected_program, pair["input"])
                        labels.append(selected)
                        if selected != pair["output"]:
                            mismatches.append({"seed": seed, "setting": finish, "pair": pair_index, "program": "selected"})
                        python_rivals = adapter.rival_outputs(pair["input"], settings)
                        for name, text in programs.items():
                            output = run(text, pair["input"])
                            rival_labels[name].append(output)
                            if name in python_rivals and output != python_rivals[name]:
                                mismatches.append({"seed": seed, "setting": finish, "pair": pair_index, "program": name, "kind": "python_racket"})
                    for name, outputs in rival_labels.items():
                        if outputs[:2] == labels[:2] and any(a != b for a, b in zip(outputs[2:], labels[2:], strict=True)):
                            harmful.append({"seed": seed, "setting": finish, "rival": name})

            witness = adapter.generate(0, {"finish": SETTINGS[1]}, demos=2, queries=4)["test"][3]["input"]
            selected_output = run(adapter.program({"finish": SETTINGS[1]}), witness)
            wrong_output = run(rival_programs["wrong_intermediate"], witness)
            causal = {
                "input_shape": [len(witness), len(witness[0])],
                "ablation": "select one source target before canonical bbox fills can merge two targets",
                "outputs_differ": selected_output != wrong_output,
                "selected_matches_python": selected_output == adapter.solve(witness, {"finish": SETTINGS[1]}),
                "counterfactual_matches_python": wrong_output == adapter.wrong_intermediate_solve(witness),
                "changed_cells": sum(a != b for ra, rb in zip(selected_output, wrong_output, strict=True) for a, b in zip(ra, rb, strict=True)),
            }
        finally:
            bridge.close()
    return {
        "executed": True,
        "runtime_identity": identity,
        "evaluations": evaluations,
        "python_racket_mismatches": mismatches,
        "harmful_survivors": harmful,
        "causal_counterfactual": causal,
    }


def build(seed_count: int) -> dict[str, Any]:
    adapter = load_adapter()
    s = structural(adapter, seed_count)
    r = protected_racket(adapter)
    failed = bool(
        s["failures"]
        or s["harmful_declared_rival_survivors"]
        or r["python_racket_mismatches"]
        or r["harmful_survivors"]
        or not r["causal_counterfactual"]["outputs_differ"]
        or not r["causal_counterfactual"]["selected_matches_python"]
        or not r["causal_counterfactual"]["counterfactual_matches_python"]
    )
    return {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": TASK_ID,
        "status": "failed" if failed else "passed",
        "structural": s,
        "racket": r,
        "sequential_dependency": {
            "step_a": "fill bounding boxes of the unique odd rotation class orange",
            "intermediate": "canonical grid whose filled target boxes form 4- and 8-cell orange components",
            "step_b": "recolor the unique largest orange component blue",
            "why_b_depends_on_a": "the selected 8-cell component is formed by two red objects only after A fills their complementary missing bbox cells",
        },
        "scope_note": "Finite declared rivals and bounded seeds; not a proof of unique induction.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    report = build(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "status": report["status"],
        "episodes": report["structural"]["episodes"],
        "pairs": report["structural"]["pairs"],
        "racket_evaluations": report["racket"]["evaluations"],
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
