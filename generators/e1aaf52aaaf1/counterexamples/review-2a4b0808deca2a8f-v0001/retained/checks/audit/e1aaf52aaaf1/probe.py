from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "generators/e1aaf52aaaf1/generator.py"
SPEC = importlib.util.spec_from_file_location("audit_e1aaf52aaaf1", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

grid = [[3, 0, 3, 3, 0, 3, 3]]
result = {
    "schema": "review-audit-e1aaf52aaaf1/1",
    "task_id": "e1aaf52aaaf1",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "counterexample": {
        "input": grid,
        "shape": [len(grid), len(grid[0])],
        "declared_grid_h_domain": GEN.AXES["grid_h"]["valid"],
        "self_check_none": GEN.self_check(grid),
        "self_check_easy": GEN.self_check(grid, difficulty="easy"),
        "self_check_medium": GEN.self_check(grid, difficulty="medium"),
        "ordinary_generator_domain": False,
        "reason_outside_domain": "height 1 is below AXES grid_h valid minimum 6",
    },
    "override_probes": {},
}

try:
    GEN.generate(0, 0, difficulty="easy", grid_h=6)
except Exception as exc:
    result["override_probes"]["advertised_easy_grid_h_6"] = {
        "status": "rejected",
        "error": str(exc),
    }
else:
    result["override_probes"]["advertised_easy_grid_h_6"] = {"status": "accepted"}

base = GEN.generate(11, 7, difficulty="medium")
unknown = GEN.generate(11, 7, difficulty="medium", typo_axis=123)
result["override_probes"]["unknown_key"] = {
    "accepted": True,
    "byte_identical_to_default": unknown == base,
}

warm = GEN.generate(11, 7, difficulty="medium", palette_kind="warm")
cool = GEN.generate(11, 7, difficulty="medium", palette_kind="cool")
result["override_probes"]["palette_kind"] = {
    "warm_equals_cool": warm == cool,
    "note": "advertised helpful axis is not read by generate",
}
print(json.dumps(result, indent=2, sort_keys=True))
