#!/usr/bin/env python3
"""Build a qualification-bound causal witness for feedback-routed rings."""
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

TASK_ID = "84def340ce03"
HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
RUNTIME = REPO / "shared" / "runtime"

STEP_A = (
    "Complete the current center-out ring and inspect its rendered quadrant "
    "colors in top-left, top-right, bottom-left, bottom-right order."
)
INTERMEDIATE = (
    "The first quadrant index 0..3 attaining the completed ring's minimum color."
)
STEP_B = (
    "Rotate the next row-major 2x2 source tile clockwise by that index, then "
    "paint it as the next outer ring."
)
WHY_B_DEPENDS_ON_A = (
    "The next tile's orientation cannot be selected before the previous ring is "
    "rendered, because that rendered orientation determines the minimum-color "
    "quadrant index consumed by the next rotation."
)


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_arc_84def340ce03_witness_prototype"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def build_witness(qualification: dict, *, seed: int = 17, query_index: int = 0) -> dict:
    """Execute an actual/skip-A pair and bind it to native qualification bytes."""
    if (
        type(qualification) is not dict
        or qualification.get("schema") != "arcpuzzles-parametric-qualification-v1"
        or qualification.get("status") != "qualified"
        or qualification.get("task_id") != TASK_ID
        or type(qualification.get("source_binding")) is not dict
        or type(qualification.get("programs")) is not dict
    ):
        raise ValueError("qualification must be a qualified native report for this task")
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be an exact integer in 0..3")

    prototype = _load_prototype()
    settings = {"routing": "feedback_min"}
    setting_key = json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    program = prototype.program_for("feedback_min")
    expected_hash = qualification["programs"].get(setting_key)
    if hashlib.sha256(program.encode()).hexdigest() != expected_hash:
        raise ValueError("current feedback program is not the qualified setting program")
    counterfactual_program = prototype.program_for("direct")
    grid = prototype.sample_input(seed, "query", query_index)

    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            output = apply(program, grid)
            counterfactual_output = apply(counterfactual_program, grid)
        finally:
            bridge.close()
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("witness requires protected Racket")
    if output == counterfactual_output:
        raise RuntimeError("skip-A counterfactual did not change final output")

    return {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": copy.deepcopy(qualification["source_binding"]),
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY_B_DEPENDS_ON_A,
        "cases": [
            {
                "input": grid,
                "settings": settings,
                "intermediate_value": {
                    "prior_ring_minimum_quadrant_indices": prototype.feedback_trace(grid)
                },
                "program": program,
                "output": output,
                "counterfactual_program": counterfactual_program,
                "counterfactual_output": counterfactual_output,
                "ablation": "skip_a",
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--query-index", type=int, default=0)
    args = parser.parse_args(argv)

    qualification = json.loads(Path(args.qualification).read_text())
    witness = build_witness(
        qualification,
        seed=args.seed,
        query_index=args.query_index,
    )
    destination = Path(args.out).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    replay = replay_witness(REPO, witness)
    print(json.dumps({
        "out": str(destination),
        "cases": len(witness["cases"]),
        "owner_replay_status": replay["status"],
        "owner_replay_evaluations": replay["evaluations"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
