#!/usr/bin/env python3
"""Build and owner-replay a qualification-bound rail-transfer witness."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from arcpuzzles.review_sequential_replay import replay_witness

TASK_ID = "9c50790b939c"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"

STEP_A = (
    "Locate the unique mixed 8/9 source rail, derive its full extent, end-aligned "
    "9-block length and occupied end, then locate the unique pure-8 target rail "
    "whose input-derived length is exactly source_length + 2."
)
INTERMEDIATE = (
    "The source and target rail records together with the source block end and "
    "the transfer length source_block_length + the episode growth_delta."
)
STEP_B = (
    "Clear the source 9 block to 8 and paint exactly the derived transfer length "
    "on the corresponding end of the derived target rail."
)
WHY = (
    "Step B cannot choose a target, an end, or a paint extent without Step A's "
    "input-dependent source extent, source-block record and matched target rail."
)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_9c50790b939c_witness"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _changed(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def build(qualification: dict, seed: int = 17, query_index: int = 3) -> dict:
    if (
        type(qualification) is not dict
        or qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
    ):
        raise ValueError("qualification must be a qualified native report for this task")
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be an exact integer in 0..3")

    prototype = _load_prototype()
    settings = {"growth_delta": 2}
    key = json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    program = prototype.program(settings)
    if qualification["programs"].get(key) != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("current growth-2 program is not the qualified setting program")
    counterfactual = prototype.program({"growth_delta": 0})
    grid = prototype.native_sample_input(seed, "query", query_index)
    analysis = prototype.native_analyze(grid)

    with _local_imports(RUNTIME, HERE):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            output = apply(program, grid)
            counterfactual_output = apply(counterfactual, grid)
        finally:
            bridge.close()
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("witness requires protected Racket")
    if output == counterfactual_output:
        raise RuntimeError("wrong transfer-length intermediate changed no output")

    changed = _changed(output, counterfactual_output)
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": copy.deepcopy(qualification["source_binding"]),
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": [
            {
                "input": grid,
                "settings": settings,
                "intermediate_value": {
                    "source": analysis["source"],
                    "target": analysis["target"],
                    "correct_transfer_length": analysis["source"]["block_length"] + 2,
                    "wrong_transfer_length": analysis["source"]["block_length"],
                    "changed_cells": changed,
                },
                "program": program,
                "output": output,
                "counterfactual_program": counterfactual,
                "counterfactual_output": counterfactual_output,
                "ablation": "wrong_intermediate",
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--query-index", type=int, default=3)
    args = parser.parse_args(argv)
    qualification = json.loads(Path(args.qualification).read_text())
    witness = build(qualification, seed=args.seed, query_index=args.query_index)
    destination = Path(args.out).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    replay = replay_witness(REPO, witness)
    print(
        json.dumps(
            {
                "out": str(destination),
                "cases": len(witness["cases"]),
                "changed_cells": witness["cases"][0]["intermediate_value"]["changed_cells"],
                "owner_replay_status": replay["status"],
                "owner_replay_evaluations": replay["evaluations"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
