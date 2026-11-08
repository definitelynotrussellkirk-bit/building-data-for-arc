from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "004ca3500787"
HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
SAVED = (
    REPO
    / "generators"
    / TASK
    / "counterexamples"
    / "current-shortcut"
    / "checks"
    / "rotation-limit.json"
)

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

saved = json.loads(SAVED.read_text())
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_sha == saved["generator_sha256"]

instance = saved["lesson"]["instance"]
pairs = instance["train"] + instance["test"]
query_index = 1
train_indices = [i for i in range(len(pairs)) if i != query_index]
rival = module.LESSON_COMPETITORS["rotation_only_odd_one_out"]

demo_rows = []
for index in train_indices:
    prediction = rival(pairs[index]["input"])
    demo_rows.append(
        {
            "pair_index": index,
            "matches_intended": prediction == pairs[index]["output"],
        }
    )
query_prediction = rival(pairs[query_index]["input"])
result = {
    "schema": "audit-reproduction-v1",
    "task_id": TASK,
    "generator_sha256": source_sha,
    "finding": "rotation-only rival is indistinguishable after holding out pair 1",
    "saved_evidence": str(SAVED.relative_to(WORK)),
    "query_index": query_index,
    "train_indices": train_indices,
    "rival": "rotation_only_odd_one_out",
    "demonstrations": demo_rows,
    "all_demonstrations_match": all(row["matches_intended"] for row in demo_rows),
    "query_input": pairs[query_index]["input"],
    "intended_query_output": pairs[query_index]["output"],
    "rival_query_output": query_prediction,
    "query_disagrees": query_prediction != pairs[query_index]["output"],
}
assert result["all_demonstrations_match"]
assert result["query_disagrees"]
(HERE.parent / "reproduction.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({k: result[k] for k in ("task_id", "all_demonstrations_match", "query_disagrees")}, sort_keys=True))
