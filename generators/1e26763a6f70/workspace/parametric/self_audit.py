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

TASK_ID = "1e26763a6f70"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_1e26763a6f70_self_audit"
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


def run(output: str) -> dict:
    start = time.monotonic()
    prototype = _load_prototype()
    jobs = []
    evaluations = 0
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for selection in prototype.SETTING_NAMES:
                for seed in (0, 17):
                    for demos in (2, 6):
                        episode = prototype.generate_episode(seed, selection, demos=demos, queries=4)
                        alternate = prototype.SETTING_NAMES[1 - prototype.SETTING_NAMES.index(selection)]
                        chosen_program = prototype.program_for(selection)
                        alternate_program = prototype.program_for(alternate)
                        survivors = []
                        for candidate, program in ((selection, chosen_program), (alternate, alternate_program)):
                            outputs = [apply(program, pair["input"]) for pair in episode["train"]]
                            evaluations += len(outputs)
                            if all(output == pair["output"] for output, pair in zip(outputs, episode["train"], strict=True)):
                                survivors.append(candidate)
                        if survivors != [selection]:
                            raise AssertionError((selection, seed, demos, survivors))
                        for pair in episode["train"] + episode["test"]:
                            actual = apply(chosen_program, pair["input"])
                            evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(f"Racket/Python mismatch for {selection} seed={seed}")
                        jobs.append({
                            "selection": selection,
                            "seed": seed,
                            "demos": demos,
                            "queries": 4,
                            "finite_survivors": survivors,
                            "python_rival_survivors": prototype.teaching_survivors(episode["train"]),
                            "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
                        })

            witness_grid = prototype.sample_input(17, "query", 3)
            longest_output = apply(prototype.program_for("longest_pairs"), witness_grid)
            shortest_output = apply(prototype.program_for("shortest_pairs"), witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if longest_output == shortest_output:
        raise AssertionError("wrong-intermediate counterfactual did not change final output")

    matched_requests = 0
    prefix_requests = 0
    public_requests = 0
    stress_episodes = 0
    max_nonzero = 0
    min_longest_changes = 10**9
    for seed in range(128):
        all_episode = prototype.generate_episode(seed, "all_pairs", demos=6, queries=4)
        longest_episode = prototype.generate_episode(seed, "longest_pairs", demos=6, queries=4)
        if [pair["input"] for pair in all_episode["train"] + all_episode["test"]] != [
            pair["input"] for pair in longest_episode["train"] + longest_episode["test"]
        ]:
            raise AssertionError("settings changed sampled inputs")
        matched_requests += 1
        for selection, large in (("all_pairs", all_episode), ("longest_pairs", longest_episode)):
            small = prototype.generate_episode(seed, selection, demos=2, queries=1)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed a stable prefix")
            if prototype.teaching_survivors(small["train"]) != [selection]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefix_requests += 1
            stress_episodes += 1
            q4 = large["test"][3]
            max_nonzero = max(max_nonzero, sum(v != 0 for row in q4["input"] for v in row))
            if selection == "longest_pairs":
                changes = sum(
                    a != b
                    for row_a, row_b in zip(q4["input"], q4["output"], strict=True)
                    for a, b in zip(row_a, row_b, strict=True)
                )
                min_longest_changes = min(min_longest_changes, changes)

        first = prototype.generate_episode(seed, "longest_pairs", demos=3, queries=1)
        four = prototype.generate_episode(seed, "longest_pairs", demos=3, queries=4)
        if public_challenge_bytes(_public(first, 0)) != public_challenge_bytes(_public(four, 0)):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(first, 0)) != public_challenge_id(_public(four, 0)):
            raise AssertionError("future queries changed first public ID")
        public_requests += 1

    analysis = prototype.analyze(witness_grid)
    diff = sum(
        a != b
        for row_a, row_b in zip(longest_output, shortest_output, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )
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
            "minimum_longest_pair_changes": min_longest_changes,
            "shape": [30, 30],
        },
        "causal_counterfactual": {
            "setting": {"pair_selection": "longest_pairs"},
            "eligible_spans": [pair["span"] for pair in analysis["eligible_pairs"]],
            "correct_intermediate": max(pair["span"] for pair in analysis["eligible_pairs"]),
            "wrong_intermediate": min(pair["span"] for pair in analysis["eligible_pairs"]),
            "changed_cells": diff,
            "program_sha256": hashlib.sha256(prototype.program_for("longest_pairs").encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(prototype.program_for("shortest_pairs").encode()).hexdigest(),
        },
        "source_sha256": {
            name: _sha(HERE / name)
            for name in (
                "adapter.py",
                "prototype.py",
                "promotion.json",
                "canonical.rkt",
                "longest_pairs.rkt",
                "shortest_pairs.rkt",
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
    print(json.dumps({
        "status": result["status"],
        "out": str(path),
        "racket_evaluations": evaluations,
        "jobs": len(jobs),
        "python_stress_episodes": stress_episodes,
        "causal_changed_cells": diff,
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
