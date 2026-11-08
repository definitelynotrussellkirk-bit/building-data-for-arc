#!/usr/bin/env python3
"""Reproduce fd9fa5d1f8a3's ignored advertised n_singletons control."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
PACKET = HERE.parents[4]
REPO = PACKET / "WORK" / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]
GENERATOR = REPO / "generators" / "fd9fa5d1f8a3" / "generator.py"

spec = importlib.util.spec_from_file_location("audit_fd9fa5d1f8a3", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def nonzero_count(grid: list[list[int]]) -> int:
    return sum(value != 0 for row in grid for value in row)


seed = 1
sample_index = 0
base = module.generate(seed, sample_index, difficulty="easy")
one = module.generate(seed, sample_index, difficulty="easy", n_singletons=1)
twelve = module.generate(seed, sample_index, difficulty="easy", n_singletons=12)

# Also measure the realized source-count support of ordinary hard samples.
hard_counts: Counter[int] = Counter()
for scan_seed in range(100):
    for scan_index in range(20):
        grid = module.generate(scan_seed, scan_index, difficulty="hard")
        hard_counts[nonzero_count(grid)] += 1

report = {
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "advertised_axis": module.AXES["n_singletons"],
    "reproduction": {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "easy",
        "base_nonzero_count": nonzero_count(base),
        "override_1_nonzero_count": nonzero_count(one),
        "override_12_nonzero_count": nonzero_count(twelve),
        "base_sha256": digest(base),
        "override_1_sha256": digest(one),
        "override_12_sha256": digest(twelve),
        "all_three_outputs_identical": base == one == twelve,
        "self_check_override_12": module.self_check(twelve, difficulty="easy"),
    },
    "hard_default_scan": {
        "samples": sum(hard_counts.values()),
        "realized_source_count_histogram": dict(sorted(hard_counts.items())),
        "minimum": min(hard_counts),
        "maximum": max(hard_counts),
    },
    "root_cause": "AXES advertises n_singletons, but generate() calls ctx.draw_int('singletons', ...); the override key is never consumed.",
}

assert report["reproduction"]["all_three_outputs_identical"]
assert report["reproduction"]["override_12_nonzero_count"] != 12

out = HERE.with_name("reproduction.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
