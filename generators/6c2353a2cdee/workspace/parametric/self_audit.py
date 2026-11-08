#!/usr/bin/env python3
"""Protected-Racket parity, learnability, export, and stress audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "6c2353a2cdee"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_6c2353a2cdee_self_audit"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public(episode: dict, query_index: int) -> dict:
    return {"train": episode["train"], "test": [{"input": episode["test"][query_index]["input"]}]}


def _diff(a, b) -> int:
    return sum(x != y for row_a, row_b in zip(a, b, strict=True)
               for x, y in zip(row_a, row_b, strict=True))


def run(output: str) -> dict:
    start = time.monotonic()
    prototype = _load_prototype()
    jobs = []
    evaluations = 0
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for direction in prototype.SETTING_NAMES:
                for seed in (0, 17):
                    for demos in (2, 6):
                        episode = prototype.generate_episode(seed, direction, demos=demos, queries=4)
                        alternate = prototype.SETTING_NAMES[1 - prototype.SETTING_NAMES.index(direction)]
                        survivors = []
                        for candidate in (direction, alternate):
                            program = prototype.program_for(candidate)
                            outputs = [apply(program, pair["input"]) for pair in episode["train"]]
                            evaluations += len(outputs)
                            if all(actual == pair["output"] for actual, pair in zip(outputs, episode["train"], strict=True)):
                                survivors.append(candidate)
                        if survivors != [direction]:
                            raise AssertionError((direction, seed, demos, survivors))
                        for pair in episode["train"] + episode["test"]:
                            actual = apply(prototype.program_for(direction), pair["input"])
                            evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(f"Racket/Python mismatch for {direction} seed={seed}")
                        jobs.append({
                            "rotation_direction": direction,
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "finite_program_survivors": survivors,
                            "python_rival_survivors": prototype.teaching_survivors(episode["train"]),
                            "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
                        })
            witness_grid = prototype.sample_input(17, "query", 3)
            correct_output = apply(prototype.program_for("clockwise"), witness_grid)
            wrong_output = apply(prototype.program_for("counterclockwise"), witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("wrong transformed-panel intermediate did not change final output")

    matched_requests = prefix_requests = public_requests = 0
    stress_episodes = 0
    min_setting_diff = 10**9
    max_nonzero = 0
    for seed in range(128):
        clockwise = prototype.generate_episode(seed, "clockwise", demos=6, queries=4)
        counterclockwise = prototype.generate_episode(seed, "counterclockwise", demos=6, queries=4)
        if [p["input"] for p in clockwise["train"] + clockwise["test"]] != [
            p["input"] for p in counterclockwise["train"] + counterclockwise["test"]
        ]:
            raise AssertionError("settings changed sampled inputs")
        matched_requests += 1
        for direction, large in (("clockwise", clockwise), ("counterclockwise", counterclockwise)):
            small = prototype.generate_episode(seed, direction, demos=2, queries=1)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed a stable prefix")
            if prototype.teaching_survivors(small["train"]) != [direction]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefix_requests += 1
            stress_episodes += 1
        q_cw, q_ccw = clockwise["test"][3], counterclockwise["test"][3]
        max_nonzero = max(max_nonzero, sum(v != 0 for row in q_cw["input"] for v in row))
        min_setting_diff = min(min_setting_diff, _diff(q_cw["output"], q_ccw["output"]))
        first = prototype.generate_episode(seed, "counterclockwise", demos=3, queries=1)
        four = prototype.generate_episode(seed, "counterclockwise", demos=3, queries=4)
        if public_challenge_bytes(_public(first, 0)) != public_challenge_bytes(_public(four, 0)):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(first, 0)) != public_challenge_id(_public(four, 0)):
            raise AssertionError("future queries changed first public ID")
        public_requests += 1

    correct_analysis = prototype.analyze(witness_grid, "clockwise")
    wrong_analysis = prototype.analyze(witness_grid, "counterclockwise")
    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "racket": identity,
        "racket_evaluations": evaluations,
        "jobs": jobs,
        "finite_rivals": list(prototype.CANDIDATE_NAMES),
        "matched_input_requests": matched_requests,
        "count_prefix_requests": prefix_requests,
        "public_first_turn_requests": public_requests,
        "python_stress_episodes": stress_episodes,
        "substantive_30x30": {
            "maximum_nonzero_cells": max_nonzero,
            "minimum_setting_output_difference": min_setting_diff,
            "shape": [30, 30],
        },
        "causal_counterfactual": {
            "setting": {"rotation_direction": "clockwise"},
            "codes": list(correct_analysis["codes"]),
            "correct_intermediate_sha256": hashlib.sha256(json.dumps(correct_analysis["transformed_panels"], separators=(",", ":")).encode()).hexdigest(),
            "wrong_intermediate_sha256": hashlib.sha256(json.dumps(wrong_analysis["transformed_panels"], separators=(",", ":")).encode()).hexdigest(),
            "changed_cells": _diff(correct_output, wrong_output),
            "program_sha256": hashlib.sha256(prototype.program_for("clockwise").encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(prototype.program_for("counterclockwise").encode()).hexdigest(),
        },
        "source_sha256": {name: _sha(HERE / name) for name in (
            "adapter.py", "prototype.py", "promotion.json", "canonical.rkt", "counterclockwise.rkt")},
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "The 30x30 extension deliberately tests fixed-coordinate extraction with dense out-of-scope distractors.",
            "Reviewer qualification evidence only; owner acceptance and training admission remain separate.",
        ],
        "training_admitted": False,
    }
    path = Path(output).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"], "out": str(path), "racket_evaluations": evaluations,
        "jobs": len(jobs), "python_stress_episodes": stress_episodes,
        "causal_changed_cells": result["causal_counterfactual"]["changed_cells"],
    }, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    run(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
