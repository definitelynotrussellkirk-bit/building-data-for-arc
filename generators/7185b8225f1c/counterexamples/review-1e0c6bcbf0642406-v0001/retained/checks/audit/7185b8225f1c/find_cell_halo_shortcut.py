from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / "7185b8225f1c" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_7185b8225f1c", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def local_cell_halo(grid):
    """Plausible rival: dilate each multi-cell component by one Chebyshev step."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for component in module._red_components(grid):
        if len(component) < 2:
            continue
        for row, col in component:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = row + dr, col + dc
                    if 0 <= rr < height and 0 <= cc < width and out[rr][cc] == 0:
                        out[rr][cc] = 3
    return out


found = None
for band in ("easy", "medium", "hard", None):
    for seed in range(64):
        for start in range(256):
            grids = [module.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            canonical = [module.rule_mirror(grid) for grid in grids]
            rival = [local_cell_halo(grid) for grid in grids]
            if all(canonical[index] == rival[index] for index in range(3)) and canonical[3] != rival[3]:
                differing = [
                    [row, col, canonical[3][row][col], rival[3][row][col]]
                    for row in range(len(grids[3]))
                    for col in range(len(grids[3][0]))
                    if canonical[3][row][col] != rival[3][row][col]
                ]
                found = {
                    "band": band,
                    "seed": seed,
                    "start_sample_index": start,
                    "demo_profiles": [module.observe_overrides(grid)["scene_profile"] for grid in grids[:3]],
                    "query_profile": module.observe_overrides(grids[3])["scene_profile"],
                    "demo_inputs": grids[:3],
                    "demo_outputs": canonical[:3],
                    "query_input": grids[3],
                    "canonical_query_output_python_mirror": canonical[3],
                    "rival_query_output": rival[3],
                    "differing_cells_row_col_canonical_rival": differing,
                }
                break
        if found:
            break
    if found:
        break

report = {
    "task_id": module.TASK_ID,
    "version": module.VERSION,
    "rule_hash": module.RULE_HASH,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rival": "paint the one-cell Chebyshev halo around each cell of every multi-cell component, rather than the full expanded bounding rectangle",
    "lesson_policy_tested": "three consecutive demonstrations followed by the fourth sample as query",
    "working_directory": str(ROOT),
    "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/7185b8225f1c/find_cell_halo_shortcut.py",
    "found": found,
}
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if found else 2)
