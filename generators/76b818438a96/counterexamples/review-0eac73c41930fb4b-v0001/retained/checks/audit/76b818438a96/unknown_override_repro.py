from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / "76b818438a96" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_76b818438a96", GEN_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

grid = module.generate(
    0,
    3,
    difficulty="easy",
    __override_contract_unknown_axis__=123,
)
report = {
    "task_id": "76b818438a96",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "call": {
        "seed": 0,
        "sample_index": 3,
        "difficulty": "easy",
        "overrides": {"__override_contract_unknown_axis__": 123},
    },
    "unknown_override_accepted": True,
    "returned_dimensions": [len(grid), len(grid[0])],
    "declared_axes": sorted(module.AXES),
    "observe_overrides": module.observe_overrides(grid),
    "observer_keys_match_declared_axes": set(module.observe_overrides(grid)) == set(module.AXES),
    "self_check": module.self_check(grid),
}
print(json.dumps(report, indent=2, sort_keys=True))
