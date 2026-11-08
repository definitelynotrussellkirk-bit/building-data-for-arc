#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK_ID = "04a27ff51304"
root = find_root(__file__)
gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
rows = []
for sample_index in range(4):
    grid = gen.generate(0, sample_index, difficulty=None)
    rows.append({
        "seed": 0,
        "sample_index": sample_index,
        "difficulty": None,
        "input": grid,
        "self_check": gen.self_check(grid),
    })
assert all(not row["self_check"] for row in rows)
(HERE / "input.json").write_text(json.dumps([row["input"] for row in rows], indent=2) + "\n")
report = {
    "schema": "audit-generated-inputs-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(root)),
    "generator_sha256": source_sha,
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "rows": rows,
    "command": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "../checks/audit/04a27ff51304/prepare.py"],
    },
}
(HERE / "generated.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "self_checks": [row["self_check"] for row in rows],
    "shapes": [[len(row["input"]), len(row["input"][0])] for row in rows],
}, indent=2))
