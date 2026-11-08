#!/usr/bin/env python3
"""Build the source-bound protected-Racket skip-A witness for fe54bfae4cee."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
WORK = ROOT.parent
TASK_ID = "fe54bfae4cee"
PROTOTYPE_PATH = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
QUALIFICATION_PATH = WORK / f"checks/{TASK_ID}/qualification/qualification.json"

STEP_A = "Execute one canonical exact-gap midpoint-fill pass on the source grid."
INTERMEDIATE = "The first-pass grid, including a newly colored relay endpoint that was zero in the source."
STEP_B = "Execute the same midpoint-fill rule on that first-pass grid."
WHY = (
    "The second relay midpoint has no valid pair in the source; it becomes fillable only after "
    "step A creates the endpoint consumed by step B. Skipping A changes the protected-Racket final output."
)

SPEC = importlib.util.spec_from_file_location("fe54_dependency_prototype", PROTOTYPE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(program)} {literal(grid)})")


def main() -> int:
    qualification = json.loads(QUALIFICATION_PATH.read_text(encoding="utf-8"))
    if qualification.get("status") != "qualified":
        raise RuntimeError("native qualification must be complete before building the witness")

    witness = prototype.causal_witness()
    source = witness["input"]
    one_program = prototype.program_for(1)
    two_program = prototype.program_for(2)
    qualified_key = json.dumps({"fill_passes": 2}, sort_keys=True, separators=(",", ":"))
    if qualification.get("programs", {}).get(qualified_key) != hashlib.sha256(two_program.encode()).hexdigest():
        raise RuntimeError("two-pass program is not the exact qualified setting program")

    bridge = RacketBridge()
    try:
        one_output = execute(bridge, one_program, source)
        two_output = execute(bridge, two_program, source)
        runtime = bridge.runtime_identity
    finally:
        bridge.close()

    if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
        raise RuntimeError("protected Racket backend is required")
    if one_output != prototype.apply_passes(source, 1):
        raise RuntimeError("canonical Racket intermediate differs from the Python sampler mirror")
    if two_output != prototype.apply_passes(source, 2):
        raise RuntimeError("two-pass Racket final differs from the Python sampler mirror")
    first = tuple(witness["created_first"])
    second = tuple(witness["created_second"])
    if one_output[first[0]][first[1]] != witness["color"]:
        raise RuntimeError("step A did not create the relay endpoint")
    if one_output[second[0]][second[1]] != 0:
        raise RuntimeError("step B fired before the second pass")
    if two_output[second[0]][second[1]] != witness["color"]:
        raise RuntimeError("step B did not consume the first-pass endpoint")
    if one_output == two_output:
        raise RuntimeError("skip-A ablation failed to change the final output")

    report = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "task_id": TASK_ID,
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        "step_a": STEP_A,
        "intermediate": INTERMEDIATE,
        "step_b": STEP_B,
        "why_b_depends_on_a": WHY,
        "cases": [
            {
                "input": source,
                "settings": {"fill_passes": 2},
                "intermediate_value": one_output,
                "output": two_output,
                "counterfactual_output": one_output,
                "ablation": "skip_a",
                "program": two_program,
                "counterfactual_program": one_program,
                "created_first": list(first),
                "created_second": list(second),
                "color": witness["color"],
            }
        ],
        "program_hashes": {
            "qualified_two_pass": hashlib.sha256(two_program.encode()).hexdigest(),
            "skip_a_one_pass": hashlib.sha256(one_program.encode()).hexdigest(),
        },
        "racket_identity": {
            key: runtime[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
            )
            if key in runtime
        },
        "racket_evaluations": 2,
        "training_admitted": False,
        "limits": "One bounded authored relay case; not a universal depth proof.",
    }
    output = HERE.with_name("dependency.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(output), "cases": 1, "racket_evaluations": 2}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
