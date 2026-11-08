#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / "baseline-generated.json").read_text())
receipt = json.loads((HERE / "baseline-racket.json").read_text())
outputs = [row["output"] for row in receipt["results"]]


def mark_every_right_cell(grid):
    h, w = len(grid), len(grid[0])
    bars = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    assert len(bars) == 1
    b = bars[0]
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(b + 1, w):
            if grid[r][c] != 0:
                out[r][c] = 2
    return out

rows=[]
for i,(grid,oracle) in enumerate(zip(inputs,outputs)):
    rival=mark_every_right_cell(grid)
    rows.append({
        "index": i,
        "input_sha256": receipt["results"][i]["input_sha256"],
        "oracle_output_sha256": receipt["results"][i]["output_sha256"],
        "rival_fits": rival == oracle,
        "right_nonzero_count": sum(v != 0 for row in grid for v in row[([c for c in range(len(row)) if all(grid[r][c] == 8 for r in range(len(grid)) )][0]+1):]),
    })
report={
    "task_id":"0c4c1974cbf2",
    "baseline_generator_sha256":"a19577219fe4077fa102b17c6af84e8caac9dcbe6fd5698e2f85339b1946be91",
    "racket_executed_rule_hash":receipt["executed_rule_hash"],
    "rival":"mark_every_right_cell",
    "pair_count":len(rows),
    "fits_all":all(row["rival_fits"] for row in rows),
    "rows":rows,
    "finding":"Every ordinary baseline sample has no right-only object cell, so right-side occupancy alone reproduces the authoritative label; a learner need not inspect the left half.",
}
(HERE / "baseline-shortcut-analysis.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps(report, indent=2))
