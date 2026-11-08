from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "probe-pre-racket.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
results = racket["results"]
assert len(results) == len(pre["lesson"])
assert racket["generator_sha256"] == pre["generator_sha256"]

for row, result in zip(pre["lesson"], results):
    assert result["generator_domain"]["status"] == "valid"
    assert result["output"] == row["mirror_output"]

query_index = pre["query_index"]
demo_indices = [index for index in range(len(results)) if index != query_index]
assert all(
    results[index]["output"] == pre["lesson"][index]["sorted_rival_output"]
    for index in demo_indices
)
assert results[query_index]["output"] != pre["lesson"][query_index]["sorted_rival_output"]
# In the ordinary fixed ordering, the last pair is the query and the descending
# sample at index 3 remains a demonstration, so this exact window is safe.
fixed_query_index = len(results) - 1
fixed_demo_indices = list(range(fixed_query_index))
fixed_refuters = [
    index
    for index in fixed_demo_indices
    if results[index]["output"] != pre["lesson"][index]["sorted_rival_output"]
]
assert fixed_refuters == [3]

witness = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": pre["task_id"],
    "finding_id": "AUD-8CBD-ROTATED-SORTED-COLOR-AMBIGUITY",
    "classification": "reproduced query-rotation teaching defect; ordered-production limitation",
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "source_call": {
        "seed": pre["seed"],
        "start_sample_index": pre["start_sample_index"],
        "difficulty": pre["difficulty"],
        "sample_indices": [row["sample_index"] for row in pre["lesson"]],
    },
    "lesson_policy": {
        "pairs": len(results),
        "demonstrations": pre["examples_needed"],
        "tested_query_index": query_index,
        "ordinary_fixed_query_index": fixed_query_index,
    },
    "rival": "sort the visible seed colors before cycling them at triangular-number columns",
    "seed_sequences": [row["seed_sequence"] for row in pre["lesson"]],
    "rotated_witness": {
        "demo_indices": demo_indices,
        "all_five_demos_fit_rival": True,
        "query_index": query_index,
        "query_input": results[query_index]["input"],
        "racket_output": results[query_index]["output"],
        "rival_output": pre["lesson"][query_index]["sorted_rival_output"],
        "lesson_identifiable_reasons": pre["lesson_identifiable_reasons"],
    },
    "ordinary_order_check": {
        "query_index": fixed_query_index,
        "sorted_rival_refuting_demo_indices": fixed_refuters,
        "status": "identified for this exact ordinary ordering",
    },
    "conclusion": (
        "When pair 3 (seed sequence [9,5,2]) is held out, every remaining demonstration has ascending "
        "seed colors, so sorting survives all five demos but changes the held-out answer. The same six-pair "
        "window is identified in the ordinary last-pair query ordering because pair 3 remains a demo."
    ),
    "commands": {
        "prepare": ["python3", "review.py", "run", "python", "../checks/audit/8cbd834f4187/prepare_probe.py"],
        "racket": racket["command"],
        "racket_cwd": racket["cwd"],
    },
    "evidence_sha256": {
        "probe_pre_racket": hashlib.sha256((HERE / "probe-pre-racket.json").read_bytes()).hexdigest(),
        "racket": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
    },
}
(HERE / "witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
print(json.dumps({"demo_indices": demo_indices, "query_index": query_index, "fixed_refuters": fixed_refuters, "rotated_query_disagrees": results[query_index]["output"] != pre["lesson"][query_index]["sorted_rival_output"]}, indent=2))
