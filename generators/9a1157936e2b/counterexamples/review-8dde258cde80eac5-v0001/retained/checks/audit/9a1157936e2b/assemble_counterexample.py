from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TASK = "9a1157936e2b"
sys.path.insert(0, str(ROOT / "repo" / "shared" / "runtime"))
GEN = ROOT / "repo" / "generators" / TASK / "generator.py"


def digest_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


rotation = json.loads((HERE / "rotation_ambiguity.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
inputs = json.loads((HERE / "input.json").read_text())
actual = [entry["output"] for entry in racket["results"]]
rival = rotation["lesson_rival_outputs"] + [rotation["rival_output"]]

spec = importlib.util.spec_from_file_location("audit_gen_9a", GEN)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
self_checks = [module.self_check(grid) for grid in inputs]
agreements = [got == alt for got, alt in zip(actual, rival)]

assert len(inputs) == len(actual) == len(rival) == 4
assert self_checks == [[], [], [], []]
assert agreements == [True, True, True, False]

payload = {
    "schema": "arc-generator-audit-counterexample-v1",
    "task_id": TASK,
    "generator_sha256": rotation["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "seed": rotation["seed"],
    "difficulty": rotation["difficulty"],
    "lesson_sample_indices": rotation["lesson_sample_indices"],
    "query_sample_index": rotation["query_sample_index"],
    "lesson_policy": rotation["lesson_policy"],
    "rival": rotation["rival"],
    "lesson_shapes": rotation["lesson_shapes"],
    "correct_and_rival_offsets_on_lesson": rotation[
        "correct_and_rival_offsets_on_lesson"
    ],
    "query_template_offsets": rotation["query_template_offsets"],
    "correct_query_offsets": rotation["correct_query_offsets"],
    "rival_query_offsets": rotation["rival_query_offsets"],
    "input_self_checks": self_checks,
    "racket_agrees_with_rival": agreements,
    "lesson_ambiguous": all(agreements[:3]),
    "query_disagrees": not agreements[3],
    "inputs": inputs,
    "actual_racket_outputs": actual,
    "rival_outputs": rival,
    "input_sha256": digest_json(inputs),
    "actual_outputs_sha256": digest_json(actual),
    "rival_outputs_sha256": digest_json(rival),
    "sources": {
        "witness": "checks/audit/9a1157936e2b/rotation_ambiguity.json",
        "racket": "checks/audit/9a1157936e2b/racket.json",
    },
    "commands": [
        rotation["command"],
        racket["command"],
        ["python3", "checks/audit/9a1157936e2b/assemble_counterexample.py"],
    ],
    "cwd": "packet_root",
}
(HERE / "counterexample.json").write_text(json.dumps(payload, indent=2) + "\n")
print(
    json.dumps(
        {
            "task_id": TASK,
            "agreements": agreements,
            "lesson_ambiguous": payload["lesson_ambiguous"],
            "query_disagrees": payload["query_disagrees"],
            "counterexample": str(HERE / "counterexample.json"),
        },
        indent=2,
    )
)
