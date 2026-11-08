from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5d321adb3a28"
ROOT = find_root(__file__)
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"
OUT_DIR = ROOT.parent / "checks" / "question-shortcut"
OUT_DIR.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

seed = 4401
sample_index = 7
difficulty = "medium"
overrides = {"scene_profile": "6x10", "target_relation": "different"}
grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
errors = gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
if errors:
    raise SystemExit(f"generated witness failed self_check: {errors}")

intended = gen.rule_mirror(grid)
rival_name = "ignore_endpoint_equality"
rival = gen.CANONICAL_SHORTCUTS[rival_name](grid)
if intended == rival:
    raise SystemExit("chosen witness does not distinguish the rival")

canonical_fit = []
for index, pair in enumerate(canonical_pairs(TASK_ID, root=ROOT)):
    candidate = gen.CANONICAL_SHORTCUTS[rival_name](pair["input"])
    canonical_fit.append({"pair_index": index, "fits": candidate == pair["output"]})

rival_only_changes = []
for row, (expected_row, rival_row) in enumerate(zip(intended, rival)):
    for column, (expected, wrong) in enumerate(zip(expected_row, rival_row)):
        if expected != wrong:
            rival_only_changes.append(
                {"row": row, "column": column, "intended": expected, "rival": wrong}
            )

(OUT_DIR / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(OUT_DIR / "python-intended.json").write_text(json.dumps(intended, indent=2) + "\n")
(OUT_DIR / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
metadata = {
    "schema": "arcpuzzles-shortcut-witness-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "declared_rule_hash": gen.RULE_HASH,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "overrides": overrides,
    "self_check_errors": errors,
    "rival_name": rival_name,
    "canonical_fit": canonical_fit,
    "canonical_fit_count": sum(row["fits"] for row in canonical_fit),
    "canonical_pair_count": len(canonical_fit),
    "disagreement_cells": rival_only_changes,
    "input_path": "checks/question-shortcut/input.json",
    "python_intended_path": "checks/question-shortcut/python-intended.json",
    "rival_path": "checks/question-shortcut/rival.json",
}
(OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
print(json.dumps(metadata, indent=2, sort_keys=True))
