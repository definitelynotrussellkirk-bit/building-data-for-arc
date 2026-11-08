#!/usr/bin/env python3
"""Protected-Racket parity, finite-rival, count, export, and stress audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "2376352117fc"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_2376352117fc_self_audit"
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
    height = max(len(a), len(b))
    width = max(len(a[0]), len(b[0]))
    return sum(
        (a[r][c] if r < len(a) and c < len(a[0]) else None)
        != (b[r][c] if r < len(b) and c < len(b[0]) else None)
        for r in range(height) for c in range(width)
    )


def run(output: str) -> dict:
    start = time.monotonic()
    prototype = _load_prototype()
    jobs = []
    evaluations = 0
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for direction in prototype.SETTING_NAMES:
                alternate = prototype.SETTING_NAMES[1 - prototype.SETTING_NAMES.index(direction)]
                for seed in (0, 17):
                    demos = 2
                    episode = prototype.generate_episode(seed, direction, demos=demos, queries=4)
                    survivors = []
                    for candidate in (direction, alternate):
                        outputs = [apply(prototype.program_for(candidate), pair["input"])
                                   for pair in episode["train"]]
                        evaluations += len(outputs)
                        if all(actual == pair["output"]
                               for actual, pair in zip(outputs, episode["train"], strict=True)):
                            survivors.append(candidate)
                    if survivors != [direction]:
                        raise AssertionError((direction, seed, demos, survivors))
                    for pair in episode["train"] + episode["test"]:
                        actual = apply(prototype.program_for(direction), pair["input"])
                        evaluations += 1
                        if actual != pair["output"]:
                            raise AssertionError(f"Racket/Python mismatch for {direction} seed={seed}")
                    python_survivors = prototype.teaching_survivors(episode["train"][:2])
                    if python_survivors != [direction]:
                        raise AssertionError((direction, seed, "finite rivals", python_survivors))
                    jobs.append({
                        "vector_direction": direction,
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "finite_program_survivors": survivors,
                        "python_rival_survivors_after_two": python_survivors,
                        "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                    })
            witness_grid = prototype.sample_input(17, "query", 3)
            correct_output = apply(prototype.program_for("blue_to_red"), witness_grid)
            wrong_output = apply(prototype.program_for("red_to_blue"), witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("reversing the derived vector did not change final output")

    matched = prefixes = public_checks = stress = 0
    min_query_difference = 10**9
    max_nonzero = 0
    min_large_output = 10**9
    for seed in range(128):
        forward = prototype.generate_episode(seed, "blue_to_red", demos=6, queries=4)
        reverse = prototype.generate_episode(seed, "red_to_blue", demos=6, queries=4)
        if [p["input"] for p in forward["train"] + forward["test"]] != [
            p["input"] for p in reverse["train"] + reverse["test"]
        ]:
            raise AssertionError("settings changed sampled inputs")
        matched += 1
        for direction, large in (("blue_to_red", forward), ("red_to_blue", reverse)):
            small = prototype.generate_episode(seed, direction, demos=2, queries=1)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed stable prefix")
            if prototype.teaching_survivors(small["train"]) != [direction]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefixes += 1
            stress += 1
        for left, right in zip(forward["test"], reverse["test"], strict=True):
            min_query_difference = min(min_query_difference, _diff(left["output"], right["output"]))
        large = forward["test"][3]
        max_nonzero = max(max_nonzero, sum(value != 0 for row in large["input"] for value in row))
        min_large_output = min(min_large_output, sum(value != 0 for row in large["output"] for value in row))
        one = prototype.generate_episode(seed, "red_to_blue", demos=3, queries=1)
        four = prototype.generate_episode(seed, "red_to_blue", demos=3, queries=4)
        if public_challenge_bytes(_public(one, 0)) != public_challenge_bytes(_public(four, 0)):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(one, 0)) != public_challenge_id(_public(four, 0)):
            raise AssertionError("future queries changed first public ID")
        public_checks += 1

    correct = prototype.analyze(witness_grid, "blue_to_red")
    wrong = prototype.analyze(witness_grid, "red_to_blue")
    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "racket": identity,
        "racket_evaluations": evaluations,
        "jobs": jobs,
        "finite_rivals": list(prototype.CANDIDATE_NAMES),
        "matched_input_requests": matched,
        "count_prefix_requests": prefixes,
        "public_first_turn_requests": public_checks,
        "python_stress_episodes": stress,
        "substantive_30x30": {
            "shape": [30, 30],
            "maximum_nonzero_input_cells": max_nonzero,
            "minimum_nonzero_canonical_output_cells": min_large_output,
            "minimum_setting_output_difference": min_query_difference,
        },
        "causal_counterfactual": {
            "setting": {"vector_direction": "blue_to_red"},
            "base_vector": list(correct["base_vector"]),
            "correct_applied_vector": list(correct["applied_vector"]),
            "wrong_applied_vector": list(wrong["applied_vector"]),
            "changed_cells": _diff(correct_output, wrong_output),
            "program_sha256": hashlib.sha256(prototype.program_for("blue_to_red").encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(prototype.program_for("red_to_blue").encode()).hexdigest(),
        },
        "source_sha256": {name: _sha(HERE / name) for name in (
            "adapter.py", "prototype.py", "promotion.json", "canonical.rkt", "red_to_blue.rkt",
            "self_audit.py", "build_witness.py")},
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "The parametric family extends connected motif size for substantive large-grid stress while preserving the exact rule.",
            "Reviewer qualification evidence only; owner acceptance and training admission remain separate.",
        ],
        "training_admitted": False,
    }
    destination = Path(output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "out": str(destination),
        "racket_evaluations": evaluations,
        "jobs": len(jobs),
        "python_stress_episodes": stress,
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
