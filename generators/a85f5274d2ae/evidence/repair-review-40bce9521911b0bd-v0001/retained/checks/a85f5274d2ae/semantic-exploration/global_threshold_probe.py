"""Replay the private predecessor ambiguity after the prototype is repaired.

From the packet outer root:
  WORK/.venv/bin/python review.py run python3 \
    ../checks/a85f5274d2ae/semantic-exploration/global_threshold_probe.py

The JSON stores the exact programs, visible lesson, query, and minimal witness.
Its old prototype source binding remains historical; replay does not qualify new
source or imply current-source ambiguity.
"""
from pathlib import Path
import json
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

source = Path(__file__).with_name("global-dead-zone.json")
record = json.loads(source.read_text())

def execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")

with RacketBridge(timeout=20.0) as bridge:
    identity = bridge.runtime_identity
    assert identity["backend"] == "racket" and identity["protected"] is True
    for case in record["cases"]:
        expected = execute(bridge, record["program"], case["input"])
        wrong = execute(bridge, record["rival_program"], case["input"])
        assert expected == case["output"]
        assert wrong == case["rival_output"]
        assert (expected == wrong) == case["rival_agrees"]
assert all(case["rival_agrees"] for case in record["cases"][:3])
assert not record["cases"][3]["rival_agrees"]
assert not record["cases"][4]["rival_agrees"]
print(json.dumps({
    "status": "pass",
    "source": str(source),
    "source_scope": "Retained predecessor lesson; no claim about the repaired current prototype",
    "racket": {"backend": "racket", "protected": True},
    "cases": [{"role": case["role"], "rival_agrees": case["rival_agrees"], "changed_cells": case["changed_cells"]} for case in record["cases"]],
}, indent=2))
