from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
PATH = REPO / "generators/04400a6b6096/generator.py"
EXPECTED_SHA = "48809ce6334ad7ad76ddc535dae3fbffb77a96af2dfeb06d2a978e7a575da361"

spec = importlib.util.spec_from_file_location("audit_04400a6b6096", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def complete_x_centers(grid: list[list[int]]) -> list[dict[str, int]]:
    found: list[dict[str, int]] = []
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            corners = [
                grid[row - 1][col - 1],
                grid[row - 1][col + 1],
                grid[row + 1][col - 1],
                grid[row + 1][col + 1],
            ]
            if corners[0] != 0 and len(set(corners)) == 1:
                found.append({"row": row, "col": col, "color": corners[0]})
    return found

sha = hashlib.sha256(PATH.read_bytes()).hexdigest()
assert sha == EXPECTED_SHA, (sha, EXPECTED_SHA)
requested = {
    "seed": 1,
    "sample_index": 0,
    "overrides": {
        "grid_h": 7,
        "grid_w": 7,
        "motif_count": 4,
        "texture": "plain",
    },
}
grid = mod.generate(requested["seed"], requested["sample_index"], **requested["overrides"])
observed = complete_x_centers(grid)
issues = mod.self_check(grid)
assert len(observed) == 2, observed
assert issues == [], issues

out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
metadata = {
    "task_id": mod.TASK_ID,
    "generator_sha256": sha,
    **requested,
    "observed_complete_motif_count": len(observed),
    "observed_complete_motifs": observed,
    "self_check": issues,
    "finding": "exact motif_count=4 silently materialized only two complete motifs",
    "command": "PYTHONPATH=repo/shared/runtime python3 checks/audit/04400a6b6096/reproduce_motif_count.py",
    "cwd": str(WORK),
}
(out_dir / "input_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
print("CONFIRMED: requested motif_count=4, observed 2, self_check passed.")
