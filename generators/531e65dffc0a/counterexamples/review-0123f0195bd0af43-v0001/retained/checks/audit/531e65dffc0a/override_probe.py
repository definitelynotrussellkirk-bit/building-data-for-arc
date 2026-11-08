from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
TASK = "531e65dffc0a"
PATH = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_531", PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
overrides = {"grid_h": 16, "grid_w": 16, "n_anchors": 6, "proto_size": 6}
grid = module.generate(0, 0, difficulty="hard", **overrides)
observed = {
    "grid_h": len(grid),
    "grid_w": len(grid[0]),
    "n_anchors": sum(value in {2, 3, 4, 5} for row in grid for value in row),
    "proto_size": sum(value not in {0, 2, 3, 4, 5} for row in grid for value in row),
}
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "seed": 0,
    "sample_index": 0,
    "difficulty": "hard",
    "requested": overrides,
    "observed": observed,
    "advertised": {name: axis["valid"] for name, axis in module.AXES.items()},
    "self_check": module.self_check(grid),
    "mismatch": observed != overrides,
}
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["mismatch"] else 1)
