#!/usr/bin/env python3
"""Find one deterministic draw showing d57d5daa0895's advertised exact axes are ignored."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "d57d5daa0895"
root = find_root(Path.cwd())
gen, source_path, source_hash = load_selected_generator(TASK_ID, root=root)


def observe(grid):
    key = [v for v in grid[0] if v in {1, 2, 3}]
    body = [v for row in grid[2:] for v in row if v]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "key_len": len(key),
        "key_codes": "".join(map(str, key)),
        "palette_size": len(set(body)),
    }

requested = {
    "grid_h": 14,
    "grid_w": 16,
    "key_len": 6,
    "key_codes": "333333",
    "palette_size": 1,
}
seed = 18
sample_index = 18
controlled = gen.generate(seed, sample_index, difficulty="easy", **requested)
baseline = gen.generate(seed, sample_index, difficulty="easy")
unknown_error = None
try:
    unknown = gen.generate(seed, sample_index, difficulty="easy", undeclared_axis="accepted")
except Exception as exc:
    unknown_error = f"{type(exc).__name__}: {exc}"
    unknown = None

record = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK_ID,
    "generator_sha256": source_hash,
    "generator_source": str(source_path),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": "easy",
    "advertised_overrides": requested,
    "observed_with_overrides": observe(controlled),
    "observed_without_overrides": observe(baseline),
    "controlled_equals_baseline": controlled == baseline,
    "unknown_override_error": unknown_error,
    "unknown_override_equals_baseline": unknown == baseline if unknown is not None else None,
    "input_with_overrides": controlled,
    "self_check": gen.self_check(controlled, difficulty="easy"),
}
assert record["controlled_equals_baseline"] is True
assert record["observed_with_overrides"] != requested
assert unknown_error is None and record["unknown_override_equals_baseline"] is True
out = Path.cwd().parent / "checks" / "audit" / TASK_ID / "override_repro.json"
out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "output": str(out),
    "generator_sha256": source_hash,
    "controlled_equals_baseline": True,
    "observed": record["observed_with_overrides"],
    "unknown_override_accepted": True,
}, sort_keys=True))
