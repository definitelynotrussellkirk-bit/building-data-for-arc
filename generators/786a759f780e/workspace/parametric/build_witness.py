#!/usr/bin/env python3
"""Build and owner-replay a qualification-bound hole-count witness."""
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

TASK_ID = "786a759f780e"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"

STEP_A = (
    "Find every four-connected component of all nonzero cells, crop it, and derive its "
    "enclosed-hole count, painted area, first row-major color, and complete crop."
)
INTERMEDIATE = (
    "The input-dependent ordered component records `(holes, area, key color, crop)`; these "
    "records retain mixed-color connectivity and the exact enclosed-hole measurements."
)
STEP_B = (
    "Sort those records using the episode's hole_order primary key, canonical area/color "
    "tie-breaks, then pack every complete crop left-to-right with one black separator."
)
WHY = (
    "Step B cannot choose component order from area or color alone: it must consume Step A's "
    "enclosed-hole counts. Replacing them with an area-only intermediate changes the packed answer."
)


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_786a759f780e_witness"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _padded_diff(a, b) -> int:
    height = max(len(a), len(b))
    width = max(len(a[0]), len(b[0]))
    return sum((a[r][c] if r < len(a) and c < len(a[0]) else 0)
               != (b[r][c] if r < len(b) and c < len(b[0]) else 0)
               for r in range(height) for c in range(width))


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
    settings = {"hole_order": "ascending"}
    key = json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    program = prototype.program_for("ascending")
    counterfactual = prototype.program_for("area_only")
    if qualification["programs"].get(key) != hashlib.sha256(program.encode()).hexdigest():
        raise ValueError("current canonical program is not the qualified default program")

    grid = prototype.sample_input(seed, "query", query_index)
    analysis = prototype.analyze(grid)
    correct_order = prototype.sorted_objects(analysis["objects"], "ascending")
    wrong_order = prototype.sorted_objects(analysis["objects"], "area_only")
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
        raise RuntimeError("wrong-intermediate counterfactual did not change final output")
    changed = _padded_diff(output, counterfactual_output)
    summarize = lambda objects: [
        {"holes": obj["holes"], "area": obj["area"], "key_color": obj["color"],
         "height": obj["height"], "width": obj["width"]}
        for obj in objects
    ]
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
            "intermediate_value": {
                "component_records": summarize(analysis["objects"]),
                "correct_hole_first_order": summarize(correct_order),
                "wrong_area_only_order": summarize(wrong_order),
                "changed_cells": changed,
            },
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
        "out": str(destination), "cases": len(witness["cases"]),
        "changed_cells": witness["cases"][0]["intermediate_value"]["changed_cells"],
        "owner_replay_status": replay["status"], "owner_replay_evaluations": replay["evaluations"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
