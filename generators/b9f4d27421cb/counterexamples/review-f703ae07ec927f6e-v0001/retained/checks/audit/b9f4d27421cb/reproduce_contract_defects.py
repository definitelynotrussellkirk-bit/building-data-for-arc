from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "b9f4d27421cb"
REPO_ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator", GEN_PATH
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

blank_1 = [[0]]
blank_8 = [[0] * 8 for _ in range(8)]

requested_panel_size = 7
grid = module.generate(12345, 0, difficulty="easy", panel_size=requested_panel_size)
h, w = len(grid), len(grid[0])
observed_panel_size = (h - 2) // 3

unknown_override_error = None
try:
    module.generate(12345, 0, difficulty="easy", typo_axis=123)
except Exception as exc:  # evidence captures whether unknown axes are rejected
    unknown_override_error = {"type": type(exc).__name__, "message": str(exc)}

result = {
    "schema": "arcpuzzles-audit-reproduction-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "checks": {
        "blank_1x1_self_check": module.self_check(blank_1),
        "blank_8x8_self_check": module.self_check(blank_8),
        "panel_size_override": {
            "requested": requested_panel_size,
            "observed": observed_panel_size,
            "grid_shape": [h, w],
            "honored": observed_panel_size == requested_panel_size,
        },
        "unknown_override": {
            "requested": {"typo_axis": 123},
            "error": unknown_override_error,
            "rejected": unknown_override_error is not None,
        },
    },
}

assert result["generator_sha256"] == "0fd67fca9fc47b51105c821c5a756e4b61d83369e288a2b04fa7976d6fe0c8ef"
assert result["checks"]["blank_1x1_self_check"] == []
assert result["checks"]["blank_8x8_self_check"] == []
assert not result["checks"]["panel_size_override"]["honored"]
assert not result["checks"]["unknown_override"]["rejected"]

out = Path(__file__).with_name("contract_defects.json")
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
