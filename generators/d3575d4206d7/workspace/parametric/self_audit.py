#!/usr/bin/env python3
"""Bounded self-review for the post-stamp component family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK_ID = "d3575d4206d7"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_d357_self_audit", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _diff(a, b) -> int:
    return sum(x != y for ra, rb in zip(a, b, strict=True) for x, y in zip(ra, rb, strict=True))


def run(output: str) -> dict:
    started = time.monotonic()
    prototype = _load()
    episodes = pairs = matched = prefixes = public_checks = survivor_checks = 0
    max_nonzero = 0
    min_setting_difference = None
    shapes: dict[str, int] = {}
    component_signatures: dict[str, int] = {}
    thirty_cases = 0

    for seed in range(16):
        full = {
            finish: prototype.generate_episode(seed, finish, demos=6, queries=4)
            for finish in prototype.FINISHES
        }
        matched += 1
        left = [p["input"] for p in full["stamp_only"]["train"] + full["stamp_only"]["test"]]
        right = [p["input"] for p in full["mark_largest_new_components"]["train"] + full["mark_largest_new_components"]["test"]]
        if left != right:
            raise AssertionError(f"settings changed inputs at seed {seed}")
        for finish, episode in full.items():
            episodes += 1
            pairs += len(episode["train"]) + len(episode["test"])
            if prototype.teaching_survivors(episode["train"][:2]) != [finish]:
                raise AssertionError(f"two-demo survivor at seed {seed}, finish {finish}")
            survivor_checks += 1
            for count in range(2, 7):
                small = prototype.generate_episode(seed, finish, demos=count, queries=1)
                if small["train"] != episode["train"][:count] or small["test"] != episode["test"][:1]:
                    raise AssertionError("count-dependent prefix")
                prefixes += 1
            for pair in episode["train"] + episode["test"]:
                if prototype.solve(pair["input"], finish) != pair["output"]:
                    raise AssertionError("Python label mismatch")
                info = prototype.analyze(pair["input"])
                sizes = sorted((len(component) for component in info["new_components"]), reverse=True)
                if len(set(sizes)) < 2:
                    raise AssertionError("scene lacks component-size contrast")
                signature = ",".join(map(str, sizes))
                component_signatures[signature] = component_signatures.get(signature, 0) + 1
                h, w = len(pair["input"]), len(pair["input"][0])
                shapes[f"{h}x{w}"] = shapes.get(f"{h}x{w}", 0) + 1
                if (h, w) == (30, 30):
                    thirty_cases += 1
                max_nonzero = max(max_nonzero, sum(value != 0 for row in pair["input"] for value in row))
            for query in episode["test"]:
                other = prototype.solve(
                    query["input"],
                    "mark_largest_new_components" if finish == "stamp_only" else "stamp_only",
                )
                difference = _diff(query["output"], other)
                if difference == 0:
                    raise AssertionError("query does not distinguish settings")
                min_setting_difference = difference if min_setting_difference is None else min(min_setting_difference, difference)

        from reviewer_support import public_challenge_bytes
        for finish in prototype.FINISHES:
            one = prototype.generate_episode(seed, finish, demos=3, queries=1)
            four = prototype.generate_episode(seed, finish, demos=3, queries=4)
            p1 = {"train": one["train"], "test": [{"input": one["test"][0]["input"]}]}
            p4 = {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
            if public_challenge_bytes(p1) != public_challenge_bytes(p4):
                raise AssertionError("public first turn depends on future query count")
            public_checks += 1

    evaluations = 0
    jobs = []
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for seed in (0, 17):
                for finish in prototype.FINISHES:
                    episode = prototype.generate_episode(seed, finish, demos=2, queries=4)
                    program = prototype.program_for(finish)
                    for pair in episode["train"] + episode["test"]:
                        if apply(program, pair["input"]) != pair["output"]:
                            raise AssertionError(f"protected Racket mismatch: {seed} {finish}")
                        evaluations += 1
                    jobs.append({"seed": seed, "finish": finish, "labels": 6})
            witness_input = prototype.sample_input(17, "test", 3)
            correct = apply(prototype.program_for("mark_largest_new_components"), witness_input)
            wrong = apply(prototype.counterfactual_program(), witness_input)
            evaluations += 2
            changed = _diff(correct, wrong)
            if changed == 0:
                raise AssertionError("wrong original-cyan intermediate did not change final output")
        finally:
            bridge.close()
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise AssertionError("self-audit requires protected Racket")

    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "episodes": episodes,
        "pairs": pairs,
        "matched_input_requests": matched,
        "count_prefix_requests": prefixes,
        "public_first_turn_requests": public_checks,
        "two_demo_survivor_checks": survivor_checks,
        "declared_policies": list(prototype.POLICIES),
        "shapes": shapes,
        "component_size_signatures": component_signatures,
        "size_stress": {
            "thirty_by_thirty_pairs": thirty_cases,
            "maximum_nonzero_input_cells": max_nonzero,
            "minimum_setting_output_difference": min_setting_difference,
        },
        "protected_racket": {"identity": identity, "jobs": jobs, "evaluations": evaluations},
        "causal_counterfactual": {
            "ablation": "wrong_intermediate",
            "correct_setting": {"finish": "mark_largest_new_components"},
            "counterfactual": "rank original cyan mask components instead of the newly painted Stage-A component mask",
            "changed_cells": changed,
        },
        "source_sha256": {name: _sha(HERE / name) for name in (
            "adapter.py", "prototype.py", "promotion.json", "canonical.rkt",
            "mark_largest_new_components.rkt", "wrong_original_cyan_intermediate.rkt", "self_audit.py")},
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "The 30x30 case extends the canonical_27 trailing divider border while preserving the same panel lattice and canonical semantics.",
            "Reviewer qualification evidence only; owner acceptance and training admission remain separate.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "training_admitted": False,
    }
    destination = Path(output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"], "out": str(destination), "episodes": episodes,
        "pairs": pairs, "racket_evaluations": evaluations,
        "counterfactual_changed_cells": changed,
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
