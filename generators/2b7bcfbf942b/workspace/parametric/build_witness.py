#!/usr/bin/env python3
"""Build and owner-replay a qualification-bound local-origin witness."""
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

TASK_ID = "2b7bcfbf942b"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"

STEP_A = (
    "Extract every same-color four-connected object and derive its input-dependent bounding box, color, and local interior origin."
)
INTERMEDIATE = (
    "The reading-ordered object records containing exact bounding boxes and the local checker origin (r1+1,c1+1) for each object."
)
STEP_B = (
    "Complete each bounding-box border and fill its strict interior from that local origin using the episode-fixed colored-first checker phase."
)
WHY = (
    "Checker parity is relative to each derived box origin; shifting the intermediate row origin by one flips every interior parity decision while leaving the input and borders unchanged."
)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_2b7bcfbf942b_witness"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _diff(a, b) -> int:
    return sum(x != y for row_a, row_b in zip(a, b, strict=True)
               for x, y in zip(row_a, row_b, strict=True))


def build(qualification: dict, seed: int = 17, query_index: int = 3) -> dict:
    if (type(qualification) is not dict
            or qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or qualification.get("status") != "qualified"
            or qualification.get("task_id") != TASK_ID
            or type(qualification.get("source_binding")) is not dict
            or type(qualification.get("programs")) is not dict):
        raise ValueError("qualification must be a qualified native report for this task")
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be an exact integer in 0..3")

    prototype = _load_prototype()
    settings = {"checker_phase": "colored_first"}
    key = json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    program = prototype.program_for("colored_first")
    counterfactual = (HERE / "shifted_origin.rkt").read_text()
    if qualification["programs"].get(key) != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("current canonical program is not the qualified default program")

    grid = prototype.sample_input(seed, "query", query_index)
    analysis = prototype.analyze(grid)
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
        raise RuntimeError("wrong-origin counterfactual did not change final output")
    changed = _diff(output, counterfactual_output)
    records = []
    for obj in analysis["objects"]:
        r1, c1, r2, c2 = obj["bbox"]
        records.append({
            "color": obj["color"],
            "bbox": [r1, c1, r2, c2],
            "correct_local_origin": [r1 + 1, c1 + 1],
            "wrong_local_origin": [r1 + 2, c1 + 1],
            "style": obj["style"],
        })
    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": copy.deepcopy(qualification["source_binding"]),
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": [{
            "input": grid,
            "settings": settings,
            "intermediate_value": {"objects": records, "changed_cells": changed},
            "program": program,
            "output": output,
            "counterfactual_program": counterfactual,
            "counterfactual_output": counterfactual_output,
            "ablation": "wrong_intermediate",
        }],
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
    print(json.dumps({
        "out": str(destination),
        "cases": len(witness["cases"]),
        "changed_cells": witness["cases"][0]["intermediate_value"]["changed_cells"],
        "owner_replay_status": replay["status"],
        "owner_replay_evaluations": replay["evaluations"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
