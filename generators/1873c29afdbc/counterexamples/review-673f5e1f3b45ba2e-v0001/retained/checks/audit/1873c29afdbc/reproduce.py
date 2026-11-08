from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = next(p for p in HERE.parents if (p / "repo/generators").is_dir())
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "shared/tools"))
TASK_ID = "1873c29afdbc"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location("audit_1873", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
grid = mod.generate(0, 3, difficulty="easy", texture="full_grid", grid_h=11)
record = {
    "task_id": TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "reproduction": {
        "call": "generate(0, 3, difficulty='easy', texture='full_grid', grid_h=11)",
        "requested_grid_h": 11,
        "observed_shape": [len(grid), len(grid[0])],
        "self_check": mod.self_check(grid),
    },
    "semantic_contract": {
        "strict_canonical_like": hasattr(mod, "strict_canonical_like"),
        "SEMANTIC_WITNESSES": hasattr(mod, "SEMANTIC_WITNESSES"),
        "lesson_identifiable": hasattr(mod, "lesson_identifiable"),
    },
    "full_check_logs": [
        "checks/audit/1873c29afdbc/checks/1873c29afdbc_audit_semantic_gate.log",
        "checks/audit/1873c29afdbc-override/checks/1873c29afdbc_audit_override.log",
    ],
}
(HERE.parent / "reproduction.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
