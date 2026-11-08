from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "1366a5f01eb6"
source = Path(f"generators/{TASK}/generator.py")
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
common = dict(grid_h=7, grid_w=9, n_left_cells=3)
low = module.generate(917, 4, divider_col=1, **common)
high = module.generate(917, 4, divider_col=4, **common)
report = {
    "task_id": TASK,
    "finding": "declared divider_col override is ignored",
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "seed": 917,
    "sample_index": 4,
    "difficulty": None,
    "common_overrides": common,
    "cases": [
        {"overrides": {**common, "divider_col": 1}, "grid": low, "self_check": module.self_check(low)},
        {"overrides": {**common, "divider_col": 4}, "grid": high, "self_check": module.self_check(high)},
    ],
    "identical": low == high,
    "realized_full_height_gray_columns": [
        [c for c in range(len(low[0])) if all(row[c] == 5 for row in low)],
        [c for c in range(len(high[0])) if all(row[c] == 5 for row in high)],
    ],
}
out = Path("../checks/audit/1366a5f01eb6/probe.json")
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
