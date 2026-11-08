from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
SOURCE = ROOT / "generators" / "8d37d130fec1" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_8d37d130fec1", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

cases = [True, False, 1.0, "1", -1]
rows = []
for value in cases:
    try:
        grid = module.generate(0, value)
    except Exception as exc:
        rows.append({"sample_index": repr(value), "accepted": False,
                     "error": f"{type(exc).__name__}: {exc}"})
    else:
        rows.append({"sample_index": repr(value), "accepted": True,
                     "shape": [len(grid), len(grid[0])],
                     "self_check": module.self_check(grid)})
print(json.dumps({"task_id": module.TASK_ID, "cases": rows}, indent=2))
