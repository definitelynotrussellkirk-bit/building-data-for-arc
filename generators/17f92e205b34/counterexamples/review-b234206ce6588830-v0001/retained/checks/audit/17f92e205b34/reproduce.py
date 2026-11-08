#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, load_selected_generator

TASK = "17f92e205b34"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest_grid(grid) -> str:
    raw = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
invalid_calls = [
    {"axis": "seed", "seed": True, "sample_index": 0},
    {"axis": "seed", "seed": False, "sample_index": 0},
    {"axis": "seed", "seed": 1.0, "sample_index": 0},
    {"axis": "seed", "seed": 1.75, "sample_index": 0},
    {"axis": "seed", "seed": "1", "sample_index": 0},
    {"axis": "sample_index", "seed": 991, "sample_index": True},
    {"axis": "sample_index", "seed": 991, "sample_index": False},
    {"axis": "sample_index", "seed": 991, "sample_index": -1},
]
records = []
for call in invalid_calls:
    args = {"seed": call["seed"], "sample_index": call["sample_index"], "difficulty": None}
    try:
        grid = generator.generate(**args)
    except Exception as exc:
        records.append({**call, "accepted": False, "error": f"{type(exc).__name__}: {exc}"})
    else:
        records.append({
            **call,
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": generator.self_check(grid),
            "output_sha256": digest_grid(grid),
            "output": grid,
        })

valid_seed_1 = generator.generate(1, 0)
valid_seed_0 = generator.generate(0, 0)
valid_index_1 = generator.generate(991, 1)
valid_index_0 = generator.generate(991, 0)
valid_index_3 = generator.generate(991, 3)
row = Catalog(ROOT).describe(TASK)
report = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK,
    "classification": "nonliteral integer seeds and invalid sample indices are accepted",
    "source": {
        "path": source.relative_to(ROOT).as_posix(),
        "sha256": source_hash,
        "version": generator.VERSION,
        "catalog_rule_hash": row["rule_hash"],
    },
    "records": records,
    "accepted_count": sum(record["accepted"] for record in records),
    "alias_checks": {
        "seed_true_equals_seed_1": records[0].get("output") == valid_seed_1,
        "seed_false_equals_seed_0": records[1].get("output") == valid_seed_0,
        "seed_float_1_equals_seed_1": records[2].get("output") == valid_seed_1,
        "sample_index_true_equals_index_1": records[5].get("output") == valid_index_1,
        "sample_index_false_equals_index_0": records[6].get("output") == valid_index_0,
        "sample_index_minus_1_uses_profile_3": generator.schedule_profile(991, -1) == generator.schedule_profile(991, 3),
        "sample_index_minus_1_output_equals_index_3": records[7].get("output") == valid_index_3,
    },
    "scope": "findings-only audit; target source was not edited",
}
first = next(record["output"] for record in records if record["accepted"])
HERE.joinpath("input.json").write_text(json.dumps({"input": first}, indent=2) + "\n")
HERE.joinpath("reproducer.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "accepted_count": report["accepted_count"],
    "alias_checks": report["alias_checks"],
    "source_sha256": source_hash,
}))
