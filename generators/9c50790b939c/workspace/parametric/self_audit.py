#!/usr/bin/env python3
"""Protected-Racket audit for the native rail growth-delta family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "9c50790b939c"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_9c50790b939c_self_audit"
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
    return {
        "train": episode["train"],
        "test": [{"input": episode["test"][query_index]["input"]}],
    }


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def run(output: str) -> dict:
    start = time.monotonic()
    prototype = _load_prototype()
    deltas = tuple(prototype.ALLOWED_GROWTH_DELTAS)
    programs = {delta: prototype.program({"growth_delta": delta}) for delta in deltas}
    jobs = []
    evaluations = 0
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for delta in deltas:
                for seed in (0, 17):
                    for demos in (2, 6):
                        episode = prototype.generate(
                            seed, {"growth_delta": delta}, demos=demos, queries=4
                        )
                        setting_survivors = []
                        for candidate in deltas:
                            outputs = [
                                apply(programs[candidate], pair["input"])
                                for pair in episode["train"]
                            ]
                            evaluations += len(outputs)
                            if all(
                                actual == pair["output"]
                                for actual, pair in zip(
                                    outputs, episode["train"], strict=True
                                )
                            ):
                                setting_survivors.append(candidate)
                        if setting_survivors != [delta]:
                            raise AssertionError(
                                (delta, seed, demos, setting_survivors)
                            )
                        for pair in episode["train"] + episode["test"]:
                            actual = apply(programs[delta], pair["input"])
                            evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(
                                    f"Racket/Python mismatch delta={delta} seed={seed}"
                                )
                        python_survivors = prototype.native_teaching_survivors(
                            episode["train"]
                        )
                        if python_survivors != [f"growth_{delta}"]:
                            raise AssertionError(
                                (delta, seed, demos, python_survivors)
                            )
                        jobs.append(
                            {
                                "growth_delta": delta,
                                "seed": seed,
                                "demos": demos,
                                "queries": 4,
                                "finite_setting_survivors": setting_survivors,
                                "python_rival_survivors": python_survivors,
                                "query_shapes": [
                                    [len(pair["input"]), len(pair["input"][0])]
                                    for pair in episode["test"]
                                ],
                            }
                        )

            witness_grid = prototype.native_sample_input(17, "query", 3)
            correct_output = apply(programs[2], witness_grid)
            wrong_output = apply(programs[0], witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("wrong transfer-length intermediate changed no output")

    matched_requests = 0
    prefix_requests = 0
    public_requests = 0
    stress_episodes = 0
    minimum_changed = 10**9
    maximum_nonbackground_input = 0
    for seed in range(128):
        episodes = {
            delta: prototype.generate(
                seed, {"growth_delta": delta}, demos=6, queries=4
            )
            for delta in deltas
        }
        expected_inputs = [
            pair["input"]
            for pair in episodes[deltas[0]]["train"] + episodes[deltas[0]]["test"]
        ]
        for delta in deltas[1:]:
            actual_inputs = [
                pair["input"]
                for pair in episodes[delta]["train"] + episodes[delta]["test"]
            ]
            if actual_inputs != expected_inputs:
                raise AssertionError("settings changed sampled inputs")
        matched_requests += 1
        for delta, large in episodes.items():
            small = prototype.generate(
                seed, {"growth_delta": delta}, demos=2, queries=1
            )
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed a stable prefix")
            if prototype.native_teaching_survivors(small["train"]) != [
                f"growth_{delta}"
            ]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefix_requests += 1
            stress_episodes += 1
            q4 = large["test"][3]
            maximum_nonbackground_input = max(
                maximum_nonbackground_input,
                sum(value != 7 for row in q4["input"] for value in row),
            )
            minimum_changed = min(
                minimum_changed, _changed(q4["input"], q4["output"])
            )

        first = prototype.generate(
            seed, {"growth_delta": 2}, demos=3, queries=1
        )
        four = prototype.generate(
            seed, {"growth_delta": 2}, demos=3, queries=4
        )
        if public_challenge_bytes(_public(first, 0)) != public_challenge_bytes(
            _public(four, 0)
        ):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(first, 0)) != public_challenge_id(
            _public(four, 0)
        ):
            raise AssertionError("future queries changed first public ID")
        public_requests += 1

    analysis = prototype.native_analyze(witness_grid)
    diff = _changed(correct_output, wrong_output)
    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "racket": identity,
        "racket_evaluations": evaluations,
        "jobs": jobs,
        "finite_rivals": list(prototype.NATIVE_CANDIDATE_NAMES),
        "matched_input_requests": matched_requests,
        "count_prefix_requests": prefix_requests,
        "public_first_turn_requests": public_requests,
        "python_stress_episodes": stress_episodes,
        "substantive_30x30": {
            "maximum_nonbackground_input_cells": maximum_nonbackground_input,
            "minimum_changed_cells_from_input": minimum_changed,
            "shape": [30, 30],
        },
        "causal_counterfactual": {
            "setting": {"growth_delta": 2},
            "source_record": analysis["source"],
            "target_record": analysis["target"],
            "correct_transfer_length": analysis["source"]["block_length"] + 2,
            "wrong_transfer_length": analysis["source"]["block_length"],
            "changed_cells": diff,
            "program_sha256": hashlib.sha256(programs[2].encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(
                programs[0].encode()
            ).hexdigest(),
        },
        "source_sha256": {
            name: _sha(HERE / name)
            for name in (
                "adapter.py",
                "prototype.py",
                "promotion.json",
                "canonical.rkt",
                "rules/growth_0.rkt",
                "rules/growth_1.rkt",
                "rules/growth_2.rkt",
            )
        },
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "Reviewer qualification evidence only; owner acceptance and training admission remain separate.",
        ],
        "training_admitted": False,
    }
    path = Path(output).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "out": str(path),
                "racket_evaluations": evaluations,
                "jobs": len(jobs),
                "python_stress_episodes": stress_episodes,
                "causal_changed_cells": diff,
            },
            sort_keys=True,
        )
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    run(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
