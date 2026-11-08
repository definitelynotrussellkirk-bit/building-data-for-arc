from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo/generators/9e204e7ff3a2/generator.py"
spec = importlib.util.spec_from_file_location("audit_9e204e7ff3a2", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = [
    {"difficulty": "easy", "overrides": {"grid_h": 8}},
    {"difficulty": "easy", "overrides": {"grid_w": 18}},
    {"difficulty": "easy", "overrides": {"fg_palette_size": 1}},
    {"difficulty": "easy", "overrides": {"fg_palette_size": 6}},
]
rows = []
for index, case in enumerate(cases):
    try:
        grid = module.generate(101, index, difficulty=case["difficulty"], **case["overrides"])
    except Exception as exc:
        rows.append({**case, "status": "raised", "exception": type(exc).__name__, "message": str(exc)})
    else:
        rows.append({**case, "status": "accepted", "shape": [len(grid), len(grid[0])]})

report = {
    "schema": "arc-generator-audit-reproduction-v1",
    "task_id": "9e204e7ff3a2",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_axes": module.AXES,
    "finding": "Values declared legal by AXES are rejected because band-local draw bounds are also applied to exact overrides.",
    "cases": rows,
}
print(json.dumps(report, indent=2, sort_keys=True))
