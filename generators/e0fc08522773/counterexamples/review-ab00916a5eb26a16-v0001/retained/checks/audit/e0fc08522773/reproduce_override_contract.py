from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
PATH = REPO / "generators/e0fc08522773/generator.py"
EXPECTED_SHA = "816a85b9e362ddd9532a14fcdd97cdcd76622033adc41ef7fd88fcd19090cf80"

spec = importlib.util.spec_from_file_location("audit_e0fc08522773", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def observe(grid: list[list[int]]) -> dict[str, object]:
    rows = [row for row, values in enumerate(grid) if 2 in values]
    if len(rows) != 1:
        return {"shape": [len(grid), len(grid[0])], "rows_with_2": rows}
    row = rows[0]
    cols = [col for col, value in enumerate(grid[row]) if value == 2]
    return {
        "shape": [len(grid), len(grid[0])],
        "bar_row": row,
        "bar_cols": cols,
        "bar_length": len(cols),
        "anchor_left": bool(cols and cols[0] == 0),
    }

sha = hashlib.sha256(PATH.read_bytes()).hexdigest()
assert sha == EXPECTED_SHA, (sha, EXPECTED_SHA)
grid = mod.generate(11, 7, difficulty="medium", anchor_left=False)
observed = observe(grid)
issues = mod.self_check(grid)
assert observed["anchor_left"] is True, observed
assert issues == [], issues

try:
    mod.generate(1, 1, difficulty="hard", bar_length=6)
except Exception as exc:  # exact public contract failure under test
    rejected = {"type": type(exc).__name__, "message": str(exc)}
else:
    raise AssertionError("documented bar_length=6 unexpectedly accepted")
assert rejected["type"] == "ValueError"

out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
metadata = {
    "task_id": mod.TASK_ID,
    "generator_sha256": sha,
    "seed": 11,
    "sample_index": 7,
    "difficulty": "medium",
    "overrides": {"anchor_left": False},
    "observed": observed,
    "self_check": issues,
    "documented_bar_length_6": {"seed": 1, "sample_index": 1, "difficulty": "hard", "exception": rejected},
    "finding": "anchor_left=false is ignored and documented bar_length=6 is rejected",
    "command": "PYTHONPATH=repo/shared/runtime python3 checks/audit/e0fc08522773/reproduce_override_contract.py",
    "cwd": str(WORK),
}
(out_dir / "input_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
print("CONFIRMED: anchor_left=false ignored; bar_length=6 rejected.")
