"""Bounded, rerunnable audit for the 4ebdc8d865ce target-degree family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes, public_challenge_id

_PROTO_PATH = HERE / "prototype.py"
_PROTO_NAME = "_task_4ebdc8d865ce_target_degree_self_audit"
_SPEC = importlib.util.spec_from_file_location(_PROTO_NAME, _PROTO_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTO_PATH}")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_PROTO_NAME] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)

ApplyProgram = Callable[[str, list[list[int]]], list[list[int]]]


def _difference(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for left_row, right_row in zip(left, right)
        for a, b in zip(left_row, right_row)
    )


def run_audit(apply_program: ApplyProgram, *, backend: dict[str, Any]) -> dict[str, Any]:
    jobs = []
    episodes: dict[tuple[int, int], dict[str, Any]] = {}
    label_evaluations = 0

    for setting in PROTOTYPE.SETTINGS:
        target = setting["target_degree"]
        for seed, demos in ((0, 2), (17, 6)):
            episode = PROTOTYPE.generate(seed, setting, demos=demos, queries=4)
            expected_survivor = [f"target_degree_{target}"]
            survivors = PROTOTYPE.fit_candidates(episode["train"][:2])
            if survivors != expected_survivor:
                raise AssertionError(
                    f"teaching failure for degree {target}: {survivors}"
                )
            for pair in episode["train"] + episode["test"]:
                actual = apply_program(PROTOTYPE.program(setting), pair["input"])
                label_evaluations += 1
                if actual != pair["output"]:
                    raise AssertionError(
                        f"label mismatch for degree={target}, seed={seed}"
                    )
            serial = [
                json.dumps(pair["input"], separators=(",", ":"))
                for pair in episode["train"] + episode["test"]
            ]
            if len(serial) != len(set(serial)):
                raise AssertionError("duplicate input inside audited episode")
            episodes[(target, seed)] = episode
            jobs.append(
                {
                    "settings": dict(setting),
                    "seed": seed,
                    "demos": demos,
                    "queries": 4,
                    "pairs": demos + 4,
                    "program_sha256": hashlib.sha256(
                        PROTOTYPE.program(setting).encode("utf-8")
                    ).hexdigest(),
                    "unique_inputs": len(set(serial)),
                    "survivors_after_two_demos": survivors,
                }
            )

    matched_checks = []
    for seed in (0, 17):
        left = episodes[(0, seed)]
        right = episodes[(1, seed)]
        left_inputs = [pair["input"] for pair in left["train"] + left["test"]]
        right_inputs = [pair["input"] for pair in right["train"] + right["test"]]
        if left_inputs != right_inputs:
            raise AssertionError(f"settings do not share inputs for seed {seed}")
        matched_checks.append({"seed": seed, "pairs": len(left_inputs)})

    prefix_checks = []
    for setting in PROTOTYPE.SETTINGS:
        short = PROTOTYPE.generate(29, setting, demos=2, queries=1)
        long = PROTOTYPE.generate(29, setting, demos=6, queries=4)
        if short["train"] != long["train"][:2] or short["test"] != long["test"][:1]:
            raise AssertionError(f"prefix instability for {setting}")
        query_short = PROTOTYPE.generate(29, setting, demos=2, queries=4)
        if query_short["test"] != long["test"]:
            raise AssertionError(f"query stream depends on demo count for {setting}")
        prefix_checks.append({"settings": dict(setting), "status": "pass"})

    projection_episode = episodes[(1, 17)]
    public_bytes = public_challenge_bytes(projection_episode)
    public_id = public_challenge_id(projection_episode)
    mutated = deepcopy(projection_episode)
    mutated["settings"] = {"private": "mutated"}
    mutated["seed"] = 999999
    mutated["program_solution"] = "private mutation"
    mutated["test"][0]["output"] = [[9]]
    if public_challenge_bytes(mutated) != public_bytes:
        raise AssertionError("private metadata or answers changed public bytes")
    visible = json.loads(public_bytes)
    if not all(set(pair) == {"input"} for pair in visible["test"]):
        raise AssertionError("query answers leaked into public challenge")

    stress_pair = episodes[(1, 17)]["test"][-1]
    stress_input = stress_pair["input"]
    stress_output = stress_pair["output"]
    foreground = [
        (row, col)
        for row, values in enumerate(stress_input)
        for col, value in enumerate(values)
        if value == 2
    ]
    stress = {
        "shape": [len(stress_input), len(stress_input[0])],
        "foreground_cells": len(foreground),
        "changed_cells": _difference(stress_input, stress_output),
        "touches_top_or_bottom": any(row in (0, len(stress_input) - 1) for row, _ in foreground),
        "touches_left_or_right": any(col in (0, len(stress_input[0]) - 1) for _, col in foreground),
    }
    if stress["shape"] != [30, 30] or stress["foreground_cells"] < 80 or stress["changed_cells"] < 20:
        raise AssertionError(f"insubstantial stress query: {stress}")

    witness = PROTOTYPE.causal_witness()
    correct = apply_program(witness["correct_program"], witness["input"])
    wrong = apply_program(witness["wrong_program"], witness["input"])
    if correct != witness["correct_output"] or wrong != witness["wrong_output"]:
        raise AssertionError("causal witness programs disagree with their recorded outputs")
    if correct == wrong:
        raise AssertionError("wrong intermediate did not change final output")
    witness_report = dict(witness)
    witness_report["protected_correct_output"] = correct
    witness_report["protected_wrong_output"] = wrong
    witness_report["difference_cells"] = _difference(correct, wrong)

    survivors = {
        f"target_degree_{setting['target_degree']}": PROTOTYPE.fit_candidates(
            episodes[(setting["target_degree"], 0)]["train"][:2]
        )
        for setting in PROTOTYPE.SETTINGS
    }

    return {
        "schema": "arcpuzzles-4ebdc8d865ce-bounded-self-audit-v1",
        "status": "pass",
        "backend": backend,
        "jobs": len(jobs),
        "job_details": jobs,
        "label_evaluations": label_evaluations,
        "causal_evaluations": 2,
        "matched_input_checks": matched_checks,
        "prefix_checks": prefix_checks,
        "finite_rivals": {
            "tested": list(PROTOTYPE.CANDIDATE_NAMES),
            "survivors": survivors,
            "claim_scope": "only the finite listed candidates",
        },
        "public_projection": {
            "public_id": public_id,
            "sha256": hashlib.sha256(public_bytes).hexdigest(),
            "query_count": len(visible["test"]),
            "query_keys": [sorted(pair) for pair in visible["test"]],
            "private_mutation_invariant": True,
        },
        "stress": stress,
        "causal_witness": witness_report,
    }


def _racket_grid(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        identity = dict(bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError(f"protected Racket required, got {identity}")

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        report = run_audit(apply, backend=identity)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "jobs": report["jobs"],
        "label_evaluations": report["label_evaluations"],
        "causal_evaluations": report["causal_evaluations"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
