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

TASK_ID = "786a759f780e"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_786a759f780e_self_audit"
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


def _padded_diff(a, b) -> int:
    height = max(len(a), len(b))
    width = max(len(a[0]), len(b[0]))
    return sum((a[r][c] if r < len(a) and c < len(a[0]) else 0)
               != (b[r][c] if r < len(b) and c < len(b[0]) else 0)
               for r in range(height) for c in range(width))


def run(output: str) -> dict:
    start = time.monotonic()
    prototype = _load_prototype()
    jobs = []
    evaluations = 0
    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for order in prototype.SETTING_NAMES:
                for seed in (0, 17):
                    for demos in (2, 6):
                        episode = prototype.generate_episode(seed, order, demos=demos, queries=4)
                        alternate = prototype.SETTING_NAMES[1 - prototype.SETTING_NAMES.index(order)]
                        survivors = []
                        for candidate in (order, alternate):
                            outputs = [apply(prototype.program_for(candidate), pair["input"])
                                       for pair in episode["train"]]
                            evaluations += len(outputs)
                            if all(actual == pair["output"] for actual, pair in zip(outputs, episode["train"], strict=True)):
                                survivors.append(candidate)
                        if survivors != [order]:
                            raise AssertionError((order, seed, demos, survivors))
                        for pair in episode["train"] + episode["test"]:
                            actual = apply(prototype.program_for(order), pair["input"])
                            evaluations += 1
                            if actual != pair["output"]:
                                raise AssertionError(f"Racket/Python mismatch for {order} seed={seed}")
                        jobs.append({
                            "hole_order": order, "seed": seed, "demos": demos, "queries": 4,
                            "finite_program_survivors": survivors,
                            "python_rival_survivors": prototype.teaching_survivors(episode["train"]),
                            "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
                        })
            witness_grid = prototype.sample_input(17, "query", 3)
            correct_output = apply(prototype.program_for("ascending"), witness_grid)
            wrong_output = apply(prototype.program_for("area_only"), witness_grid)
            evaluations += 2
        finally:
            bridge.close()

    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("audit requires protected Racket")
    if correct_output == wrong_output:
        raise AssertionError("area-only wrong intermediate did not change final output")

    matched_requests = prefix_requests = public_requests = 0
    stress_episodes = 0
    min_setting_diff = 10**9
    max_nonzero = 0
    for seed in range(128):
        ascending = prototype.generate_episode(seed, "ascending", demos=6, queries=4)
        descending = prototype.generate_episode(seed, "descending", demos=6, queries=4)
        if [p["input"] for p in ascending["train"] + ascending["test"]] != [
            p["input"] for p in descending["train"] + descending["test"]
        ]:
            raise AssertionError("settings changed sampled inputs")
        matched_requests += 1
        for order, large in (("ascending", ascending), ("descending", descending)):
            small = prototype.generate_episode(seed, order, demos=2, queries=1)
            if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                raise AssertionError("count request changed a stable prefix")
            if prototype.teaching_survivors(small["train"]) != [order]:
                raise AssertionError("minimum demo prefix is underidentified")
            prefix_requests += 1
            stress_episodes += 1
        q_asc, q_desc = ascending["test"][3], descending["test"][3]
        max_nonzero = max(max_nonzero, sum(v != 0 for row in q_asc["input"] for v in row))
        min_setting_diff = min(min_setting_diff, _padded_diff(q_asc["output"], q_desc["output"]))
        first = prototype.generate_episode(seed, "descending", demos=3, queries=1)
        four = prototype.generate_episode(seed, "descending", demos=3, queries=4)
        if public_challenge_bytes(_public(first, 0)) != public_challenge_bytes(_public(four, 0)):
            raise AssertionError("future queries changed first public turn")
        if public_challenge_id(_public(first, 0)) != public_challenge_id(_public(four, 0)):
            raise AssertionError("future queries changed first public ID")
        public_requests += 1

    analysis = prototype.analyze(witness_grid)
    ascending_order = [(obj["holes"], obj["area"], obj["color"])
                       for obj in prototype.sorted_objects(analysis["objects"], "ascending")]
    area_order = [(obj["holes"], obj["area"], obj["color"])
                  for obj in prototype.sorted_objects(analysis["objects"], "area_only")]
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
            "hole_counts": sorted({obj["holes"] for obj in analysis["objects"]}),
        },
        "causal_counterfactual": {
            "setting": {"hole_order": "ascending"},
            "correct_intermediate_order": ascending_order,
            "wrong_intermediate_order": area_order,
            "changed_cells": _padded_diff(correct_output, wrong_output),
            "program_sha256": hashlib.sha256(prototype.program_for("ascending").encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(prototype.program_for("area_only").encode()).hexdigest(),
        },
        "source_sha256": {name: _sha(HERE / name) for name in (
            "adapter.py", "prototype.py", "promotion.json", "canonical.rkt", "descending.rkt", "area_only.rkt")},
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "limits": [
            "Finite declared-rival evidence only; arbitrary alternative programs were not ruled out.",
            "The constructive scene library is intentionally bounded although colors and mixed-cell positions vary by seed.",
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
