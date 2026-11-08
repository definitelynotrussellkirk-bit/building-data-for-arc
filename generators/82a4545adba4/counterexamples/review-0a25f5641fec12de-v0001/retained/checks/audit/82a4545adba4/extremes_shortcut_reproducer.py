#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators/82a4545adba4/generator.py"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("audit_82a4545adba4", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def extremes_only(grid):
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    markers = module._marker_cells(grid)
    selected = markers if len(markers) <= 2 else (markers[0], markers[-1])
    for col, color in selected:
        k = 0
        while k < h and col + k < w:
            output[k][col + k] = color
            k += 1
    return output

inputs = [module.generate(0, index, difficulty="easy") for index in range(3)]
records = []
for index, grid in enumerate(inputs):
    records.append(
        {
            "role": "demo" if index < 2 else "query",
            "seed": 0,
            "sample_index": index,
            "difficulty": "easy",
            "input": grid,
            "self_check": module.self_check(grid),
            "marker_count": len(module._marker_cells(grid)),
            "python_rule_mirror": module.rule_mirror(grid),
            "extremes_only_output": extremes_only(grid),
            "rival_matches_python_mirror": extremes_only(grid) == module.rule_mirror(grid),
        }
    )
payload = {
    "schema": "arcpuzzles-audit-extremes-shortcut-v1",
    "task_id": module.TASK_ID,
    "generator_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "claim": "Paint down-right rays only from the leftmost and rightmost row-0 markers.",
    "records": records,
    "fits_all_demos": all(row["rival_matches_python_mirror"] for row in records[:2]),
    "changes_query": not records[2]["rival_matches_python_mirror"],
}
(OUT / "inputs.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(OUT / "extremes_shortcut_python.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"marker_counts": [r["marker_count"] for r in records], "fits_all_demos": payload["fits_all_demos"], "changes_query": payload["changes_query"]}))
