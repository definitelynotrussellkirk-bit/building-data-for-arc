#!/usr/bin/env python3
"""Bounded protected-Racket authoring verification for e64c021e29ad.

Run through ``review.py run``.  This writes source-bound authoring evidence; it
is neither owner acceptance nor training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _real_evaluator, evaluate_contract
from reviewer_support import find_root, public_challenge_bytes

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "e64c021e29ad"
DIRECT = {"sweep_mode": "all"}
RELAY = {"sweep_mode": "first_hit_relay"}


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_e64_parametric_verified", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def jobs() -> list[dict]:
    """Return the finite authoring matrix, including both API count bounds."""
    rows = []
    for settings in (DIRECT, RELAY):
        rows.extend(
            [
                {"seed": 0, "settings": deepcopy(settings), "demos": 2, "queries": 1},
                {"seed": 0, "settings": deepcopy(settings), "demos": 3, "queries": 4},
                {"seed": 17, "settings": deepcopy(settings), "demos": 3, "queries": 4},
                {"seed": 17, "settings": deepcopy(settings), "demos": 6, "queries": 4},
            ]
        )
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _occupied_stats(grid: list[list[int]]) -> dict:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return {
        "shape": [len(grid), len(grid[0])],
        "occupied": len(cells),
        "row_span": max(r for r, _ in cells) - min(r for r, _ in cells),
        "column_span": max(c for _, c in cells) - min(c for _, c in cells),
    }


def verify(output: Path) -> dict:
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    started = time.monotonic()
    prototype = _load_prototype()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    matrix = jobs()

    native = evaluate_contract(ROOT, TASK_ID, contract, matrix)
    if native["racket"].get("backend") != "racket" or native["racket"].get("protected") is not True:
        raise AssertionError("authoring verification requires protected Racket")
    if len(native["checks"]) != len(matrix):
        raise AssertionError("native worker omitted an authoring job")

    generated = [prototype.generate(**job) for job in matrix]
    teaching = []
    for job, claimed, replayed in zip(matrix, generated, native["episodes"]):
        if replayed["train"] != claimed["train"] or replayed["test"] != claimed["test"]:
            raise AssertionError(f"protected replay disagreed with adapter claim: {job}")
        report = prototype.lesson_report(claimed, job["settings"])
        if report["setting_survivors"] != [job["settings"]]:
            raise AssertionError(f"visible demonstrations did not identify setting: {job}")
        if report["surviving_query_disagreements"]:
            raise AssertionError(f"finite rival fit demos and failed query: {job}: {report}")
        teaching.append({"job": job, "report": report})

    matched = []
    for seed, demos, queries in ((0, 2, 1), (0, 3, 4), (17, 3, 4), (17, 6, 4)):
        chosen = [
            episode
            for job, episode in zip(matrix, generated)
            if (job["seed"], job["demos"], job["queries"]) == (seed, demos, queries)
        ]
        if len(chosen) != 2:
            raise AssertionError("missing matched-setting pair")
        left = [pair["input"] for split in ("train", "test") for pair in chosen[0][split]]
        right = [pair["input"] for split in ("train", "test") for pair in chosen[1][split]]
        if left != right:
            raise AssertionError("settings did not retain matched inputs")
        matched.append({"seed": seed, "demos": demos, "queries": queries, "input_count": len(left)})

    projection_checks = []
    for settings in (DIRECT, RELAY):
        one = prototype.generate(33, settings, 3, 1)
        four = prototype.generate(33, settings, 3, 4)
        first = deepcopy(four)
        first["test"] = first["test"][:1]
        expected = public_challenge_bytes(one)
        if expected != public_challenge_bytes(first):
            raise AssertionError("single-query and first sequential turn bytes differ")
        private_mutation = deepcopy(first)
        private_mutation["program_solution"] = "PRIVATE PROGRAM MUST NOT AFFECT PUBLIC BYTES"
        private_mutation["settings"] = {"private": True}
        private_mutation["test"][0]["output"] = [[9]]
        if expected != public_challenge_bytes(private_mutation):
            raise AssertionError("public bytes leaked a private program, setting, or query answer")
        projection_checks.append({"settings": settings, "public_sha256": hashlib.sha256(expected).hexdigest()})

    relay_episode = next(
        episode
        for job, episode in zip(matrix, generated)
        if job == {"seed": 17, "settings": RELAY, "demos": 3, "queries": 4}
    )
    stress_pair = relay_episode["test"][3]
    last_hit_program = (HERE / "last_hit.rkt").read_text(encoding="utf-8")
    apply, runtime, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        counterfactual = apply(last_hit_program, deepcopy(stress_pair["input"]))
    finally:
        bridge.close()
    expected_counterfactual = prototype._relay(stress_pair["input"], target="last")
    if counterfactual != expected_counterfactual or counterfactual == stress_pair["output"]:
        raise AssertionError("last-hit Racket counterfactual did not isolate the relay intermediate")
    intermediate = prototype.relay_intermediate(stress_pair["input"])
    causal_candidate = {
        "schema": "e64c021e29ad-causal-candidate-v1",
        "settings": RELAY,
        "input": stress_pair["input"],
        "intermediate_value": intermediate,
        "program": prototype.program(RELAY),
        "output": stress_pair["output"],
        "counterfactual_program": last_hit_program,
        "counterfactual_output": counterfactual,
        "ablation": "wrong_intermediate",
        "step_a": "Trace the singleton color-9 probe along its coded cardinal ray to the first color-5..8 object.",
        "intermediate": "The first-hit object's identity, hit cell, and its own adjacent direction code.",
        "step_b": "Paint the probe path in 9, then sweep only that selected object using the selected object's code and color.",
        "why_b_depends_on_a": "The target object, target color, and sweep direction are unavailable until the ray trace identifies the first hit; substituting the farther hit changes the final grid.",
        "racket": runtime,
    }

    retained = [
        episode
        for job, episode in zip(matrix, generated)
        if job["demos"] == 3 and job["queries"] == 4
    ]
    source_paths = [
        HERE / name
        for name in (
            "adapter.py",
            "prototype.py",
            "verify.py",
            "promotion.json",
            "canonical.rkt",
            "relay.rkt",
            "last_hit.rkt",
            "README.md",
        )
    ] + [HERE.parents[1] / "tests/test_parametric.py"]
    source_hashes = {path.relative_to(ROOT).as_posix(): _sha256(path) for path in source_paths}

    report = {
        "schema": "e64c021e29ad-protected-authoring-check-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "source_sha256": source_hashes,
        "native_jobs": native["checks"],
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"],
        "episodes_attempted": len(matrix),
        "episodes_succeeded": len(matrix),
        "verified_pair_labels": sum(job["demos"] + job["queries"] for job in matrix),
        "matched_input_checks": matched,
        "teaching_checks": teaching,
        "public_projection_checks": projection_checks,
        "stress_30x30": {
            "input": _occupied_stats(stress_pair["input"]),
            "output": _occupied_stats(stress_pair["output"]),
            "intermediate": intermediate,
        },
        "causal_counterfactual": {
            "ablation": "wrong_intermediate",
            "program_sha256": hashlib.sha256(prototype.program(RELAY).encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(last_hit_program.encode()).hexdigest(),
            "outputs_differ": True,
            "candidate_path": "causal-candidate.private.json",
        },
        "retained_four_query_examples": len(retained),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "qualification_or_acceptance_performed": False,
        "training_admitted": False,
        "limits": [
            "Finite protected replay covers only the eight declared jobs and named task-local rivals.",
            "No finite audit proves universal learnability or excludes undeclared conjunctive shortcuts.",
            "This authoring report is not native qualification, owner acceptance, or training admission.",
        ],
    }

    output.mkdir(parents=True, exist_ok=False)
    _write_json(output / "verification.json", report)
    _write_json(output / "causal-candidate.private.json", causal_candidate)
    _write_json(output / "four-query-examples.private.json", retained)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes_succeeded": report["episodes_succeeded"],
                "verified_pair_labels": report["verified_pair_labels"],
                "racket_evaluations": report["racket_evaluations"],
                "elapsed_seconds": report["elapsed_seconds"],
            },
            sort_keys=True,
        )
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args()
    verify(args.out)


if __name__ == "__main__":
    main()
