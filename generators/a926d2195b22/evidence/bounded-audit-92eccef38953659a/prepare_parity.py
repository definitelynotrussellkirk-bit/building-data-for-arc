#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "a926d2195b22"
root = find_root(__file__)
gen, path, sha = load_selected_generator(TASK_ID, root=root)
rows = []
for seed in range(8):
    for sample_index in range(8):
        difficulty = (None, "easy", "medium", "hard")[(seed + sample_index) % 4]
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        rows.append({
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "input": grid,
            "python_expected": gen.rule_mirror(grid),
            "self_check": gen.self_check(grid),
            "profile": gen.schedule_profile(seed, sample_index, difficulty),
        })
base = Path(__file__).parent
(base / "parity-inputs.json").write_text(json.dumps({"inputs": [r["input"] for r in rows]}, indent=2)+"\n")
(base / "parity-expected.json").write_text(json.dumps({
    "task_id": TASK_ID,
    "generator_path": str(path.relative_to(root)),
    "generator_sha256": sha,
    "cases": rows,
}, indent=2, sort_keys=True)+"\n")
print(json.dumps({"cases": len(rows), "generator_sha256": sha}, sort_keys=True))
