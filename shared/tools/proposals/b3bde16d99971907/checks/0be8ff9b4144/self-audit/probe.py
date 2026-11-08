from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

ROOT = Path.cwd().resolve()
TASK = "0be8ff9b4144"
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"

spec = importlib.util.spec_from_file_location("intersection_policy_self_audit", HOME / "prototype.py")
assert spec is not None and spec.loader is not None
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)

reports = []
for seed in (0, 17, 91):
    for policy in prototype.POLICIES:
        episode = prototype.generate_episode(seed, intersection_policy=policy, demos=2, queries=4)
        rivals = prototype.audit_rivals(policy)
        rows = []
        for name, rival in rivals.items():
            demo_mismatches = [
                index for index, pair in enumerate(episode["train"])
                if rival(pair["input"]) != pair["output"]
            ]
            query_mismatches = [
                index for index, pair in enumerate(episode["test"])
                if rival(pair["input"]) != pair["output"]
            ]
            if not demo_mismatches or not query_mismatches:
                raise AssertionError((seed, policy, name, demo_mismatches, query_mismatches))
            rows.append({
                "rival": name,
                "demo_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
                "survives_visible_demonstrations": False,
            })
        reports.append({"seed": seed, "settings": {"intersection_policy": policy}, "rivals": rows})

rival_program = "(rule! (let ((active-rows (filter (lambda (r) (= (at g r 0) 3)) (range 1 (rows g)))) (active-cols (filter (lambda (c) (= (at g 0 c) 2)) (range 1 (cols g))))) (for*/fold ((out g)) ((r (in-list active-rows)) (c (in-list active-cols))) (if (= (modulo (+ r c) 2) 0) (set-cell out r c 5) out))))"
episode = prototype.generate_episode(0, intersection_policy="same_parity", demos=2, queries=4)
case = episode["train"][0]

def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"

with RacketBridge(timeout=20.0) as bridge:
    identity = bridge.runtime_identity
    official_program = prototype.rule_text("same_parity")
    official_output = bridge.eval_text(f"({wrap_rule(official_program)} {literal(case['input'])})")
    rival_output = bridge.eval_text(f"({wrap_rule(rival_program)} {literal(case['input'])})")

if official_output != case["output"] or official_output == rival_output:
    raise AssertionError("protected-Racket self-audit witness failed")
differences = [
    [row, col]
    for row in range(len(official_output))
    for col in range(len(official_output[0]))
    if official_output[row][col] != rival_output[row][col]
]
record = {
    "schema": "header-intersection-policy-self-audit-v1",
    "task_id": TASK,
    "status": "passed",
    "scope": "Five plausible rivals, three settings, seeds 0/17/91, two visible demonstrations and four private queries. Finite audit only.",
    "reports": reports,
    "retained_racket_case": {
        "seed": 0,
        "settings": {"intersection_policy": "same_parity"},
        "rival": "absolute_coordinate_parity",
        "input": case["input"],
        "program": official_program,
        "program_sha256": hashlib.sha256(official_program.encode()).hexdigest(),
        "output": official_output,
        "rival_program": rival_program,
        "rival_program_sha256": hashlib.sha256(rival_program.encode()).hexdigest(),
        "rival_output": rival_output,
        "differing_cells": differences,
        "racket": {k: identity[k] for k in identity if k in {"schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256"}},
    },
}
out = HOME / "evidence" / "current" / "self_audit.json"
out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "passed", "evidence": str(out.relative_to(ROOT)), "racket_differences": len(differences), "reports": len(reports)}, sort_keys=True))
