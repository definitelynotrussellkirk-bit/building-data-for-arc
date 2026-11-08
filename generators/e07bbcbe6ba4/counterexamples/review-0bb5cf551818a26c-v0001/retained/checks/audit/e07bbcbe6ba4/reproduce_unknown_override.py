from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo/generators/e07bbcbe6ba4/generator.py"
spec = importlib.util.spec_from_file_location("audit_e07bbcbe6ba4", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

unknown = "__override_contract_unknown_axis__"
try:
    grid = module.generate(0, 3, difficulty="easy", **{unknown: 123})
except Exception as exc:
    outcome = {"status": "rejected", "exception": type(exc).__name__, "message": str(exc)}
else:
    outcome = {
        "status": "accepted",
        "shape": [len(grid), len(grid[0])],
        "self_check": module.self_check(grid),
    }
report = {
    "schema": "arc-generator-audit-reproduction-v1",
    "task_id": "e07bbcbe6ba4",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_axes": sorted(module.AXES),
    "unknown_override": {unknown: 123},
    "outcome": outcome,
}
print(json.dumps(report, indent=2, sort_keys=True))
