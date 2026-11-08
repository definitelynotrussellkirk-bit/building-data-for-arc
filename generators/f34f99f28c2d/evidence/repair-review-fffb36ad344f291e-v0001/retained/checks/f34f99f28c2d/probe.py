#!/usr/bin/env python3
"""Bounded two-seed learnability probe; labels use protected native Racket."""
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator
from arcpuzzles.parametric_worker import _real_evaluator

TASK = "f34f99f28c2d"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
module, source, source_hash = load_selected_generator(TASK, root=ROOT)
rows = [json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
record, = [row for row in rows if row.get("task_id") == TASK]
program = record["program_solution"]
rule_hash = hashlib.sha256(program.encode()).hexdigest()
needle = "(define rot-count (- (third control) 6))"
assert needle in program

# Named simple rivals, fixed before inspecting the sampled episode outputs.
expressions = {
    "ignore_control_no_rotation": "0",
    "ignore_control_one_cw_turn": "1",
    "ignore_control_half_turn": "2",
    "ignore_control_three_cw_turns": "3",
    "counterclockwise_control": "(if (= (third control) 7) 3 (if (= (third control) 9) 1 (- (third control) 6)))",
    "alternating_identity_and_cw": "(if (= (third control) 6) 0 (if (= (third control) 8) 0 1))",
    "control_8_identity": "(if (= (third control) 8) 0 (- (third control) 6))",
    "control_9_identity": "(if (= (third control) 9) 0 (- (third control) 6))",
    "control_7_identity": "(if (= (third control) 7) 0 (- (third control) 6))",
    "control_6_half_turn": "(if (= (third control) 6) 2 (- (third control) 6))",
}
rivals = {name: program.replace(needle, f"(define rot-count {expr})") for name, expr in expressions.items()}
apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
episodes = []
witnesses = []
try:
    for seed in (0, 1):
        pairs = []
        for index in range(5):
            grid = module.generate(seed, index)
            errors = module.self_check(grid)
            assert not errors, (seed, index, errors)
            output = apply(program, grid)
            assert isinstance(output, list) and isinstance(output[0], list)
            pairs.append({"sample_index": index, "input": grid, "output": output})
        survivors = []
        for name, rival in rivals.items():
            if all(apply(rival, p["input"]) == p["output"] for p in pairs[:4]):
                different = apply(rival, pairs[4]["input"]) != pairs[4]["output"]
                survivors.append({"name": name, "changes_query": different})
                if different and not witnesses:
                    witnesses.append({"seed": seed, "generator_sha256": source_hash,
                        "rule_sha256": rule_hash, "rival_name": name, "rival_program": rival,
                        "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
                        "train": pairs[:4], "test": [pairs[4]],
                        "rival_query_output": apply(rival, pairs[4]["input"])})
        controls = [next(v for row in p["input"] for v in row if v in (6, 7, 8, 9)) for p in pairs]
        episodes.append({"seed": seed, "demo_controls": controls[:4], "query_control": controls[4], "survivors": survivors})
finally:
    bridge.close()
report = {"schema": "bounded-peer-review-v1", "task_id": TASK,
    "generator_source": str(source.relative_to(ROOT)), "generator_sha256": source_hash,
    "rule_sha256": rule_hash, "racket": identity, "seeds": [0, 1],
    "demos_per_seed": 4, "queries_per_seed": 1, "rival_names": list(rivals),
    "episodes": episodes, "witnesses": witnesses,
    "scope": "Two seeds and ten predeclared rotation rivals only; no qualification or exhaustive survey."}
(OUT / "probe-result.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"task_id": TASK, "generator_sha256": source_hash, "rule_sha256": rule_hash,
    "episodes": episodes, "retained_witnesses": len(witnesses), "protected": identity["protected"]}, indent=2))
