from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
GENERATOR = REPO / "generators/b87dcd3011b1/generator.py"
OUT = Path(__file__).with_name("portal_support.json")

spec = importlib.util.spec_from_file_location("audit_b87dcd3011b1", GENERATOR)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

per_band = {}
for band in ("easy", "medium", "hard"):
    portal_pairs = Counter()
    wall_counts = Counter()
    validator_failures = []
    for sample_index in range(100):
        grid = mod.generate(870031, sample_index, difficulty=band)
        counts = Counter(value for row in grid for value in row)
        pairs = sum(counts[color] == 2 for color in (4, 5, 6))
        portal_pairs[pairs] += 1
        wall_counts[counts[8]] += 1
        errors = mod.self_check(grid)
        if errors:
            validator_failures.append({"sample_index": sample_index, "errors": errors})
    per_band[band] = {
        "seed": 870031,
        "sample_indices": [0, 99],
        "draws": 100,
        "portal_pair_counts": dict(sorted(portal_pairs.items())),
        "wall_cell_counts": dict(sorted(wall_counts.items())),
        "validator_failures": validator_failures,
    }

report = {
    "schema": "b87dcd3011b1-audit-portal-support-v1",
    "task_id": "b87dcd3011b1",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "finding": (
        "The easy band emits no portal pairs by construction, so an easy lesson "
        "cannot distinguish portal-aware BFS from ordinary obstacle-avoiding BFS."
    ),
    "per_band": per_band,
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
