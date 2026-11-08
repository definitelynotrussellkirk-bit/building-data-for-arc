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

TASK_ID = "2b7bcfbf942b"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_2b7bcfbf942b_self_audit"
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
            for phase in prototype.SETTING_NAMES:
                alternate = prototype.SETTING_NAMES[1 - prototype.SETTING_NAMES.index(phase)]
                for seed in (0, 17):
                    demos = 2
                    episode = prototype.generate_episode(seed, phase, demos=demos, queries=4)
                    survivors = []
                    for candidate in (phase, alternate):
                        outputs = [apply(prototype.program_for(candidate), pair["input"])
                                   for pair in episode["train"]]
                        evaluations += len(outputs)
                        if all(actual == pair["output"]
                               for actual, pair in zip(outputs, episode["train"], strict=True)):
                            survivors.append(candidate)
                    if survivors != [phase]:
                        raise AssertionError((phase, seed, survivors))
                    for pair in episode["train"] + episode["test"]:
                        actual = apply(prototype.program_for(phase), pair["input"])
                        evaluations += 1
                        if actual != pair["output"]:
                            raise AssertionError(f"Racket/Python mismatch for {phase} seed={seed}")
                    python_survivors = prototype.teaching_survivors(episode["train"])
                    if python_survivors != [phase]:
                        raise AssertionError((phase, seed, "finite rivals", python_survivors))
                    jobs.append({
                        "checker_phase": phase,
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "finite_program_survivors": survivors,
                        "python_rival_survivors_after_two": python_survivors,
                        "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                    })
            witness_grid = prototype.sample_input(17, "query", 3)
            correct_output = apply(prototype.program_for("colored_first"), witness_grid)
            shifted_output = apply((HERE / "shifted_origin.rkt").read_text(), witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if correct_output == shifted_output:
        raise AssertionError("shifted bounding-box origin did not change final output")

    matched = prefixes = public_checks = stress = 0
    min_setting_difference = 10**9
    max_input_nonzero = max_output_nonzero = 0
    for seed in range(128):
        colored = prototype.generate_episode(seed, "colored_first", demos=6, queries=4)
        zero = prototype.generate_episode(seed, "zero_first", demos=6, queries=4)
        if [p["input"] for p in colored["train"] + colored["test"]] != [
            p["input"] for p in zero["train"] + zero["test"]
        ]:
            raise AssertionError("settings changed sampled inputs")
        matched += 1
        for phase, large in (("colored_first", colored), ("zero_first", zero)):
            small = prototype.generate_episode(seed, phase, demos=2, queries=1)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed stable prefix")
            if prototype.teaching_survivors(small["train"]) != [phase]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefixes += 1
            stress += 1
        for left, right in zip(colored["test"], zero["test"], strict=True):
            min_setting_difference = min(min_setting_difference, _diff(left["output"], right["output"]))
        large = colored["test"][3]
        max_input_nonzero = max(max_input_nonzero, sum(v != 0 for row in large["input"] for v in row))
        max_output_nonzero = max(max_output_nonzero, sum(v != 0 for row in large["output"] for v in row))
        one = prototype.generate_episode(seed, "zero_first", demos=3, queries=1)
        four = prototype.generate_episode(seed, "zero_first", demos=3, queries=4)
        if public_challenge_bytes(_public(one, 0)) != public_challenge_bytes(_public(four, 0)):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(one, 0)) != public_challenge_id(_public(four, 0)):
            raise AssertionError("future queries changed first public ID")
        public_checks += 1

    analysis = prototype.analyze(witness_grid)
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
            "object_count": len(analysis["objects"]),
            "maximum_nonzero_input_cells": max_input_nonzero,
            "maximum_nonzero_canonical_output_cells": max_output_nonzero,
            "minimum_setting_output_difference": min_setting_difference,
        },
        "causal_counterfactual": {
            "setting": {"checker_phase": "colored_first"},
            "bounding_boxes": [list(obj["bbox"]) for obj in analysis["objects"]],
            "changed_cells": _diff(correct_output, shifted_output),
            "program_sha256": hashlib.sha256(prototype.program_for("colored_first").encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256((HERE / "shifted_origin.rkt").read_bytes()).hexdigest(),
        },
        "source_sha256": {name: _sha(HERE / name) for name in (
            "adapter.py", "prototype.py", "promotion.json", "canonical.rkt", "zero_first.rkt",
            "shifted_origin.rkt", "self_audit.py", "build_witness.py")},
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "Large profiles extend object count and canvas size while preserving the same object/bounding-box rule.",
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
