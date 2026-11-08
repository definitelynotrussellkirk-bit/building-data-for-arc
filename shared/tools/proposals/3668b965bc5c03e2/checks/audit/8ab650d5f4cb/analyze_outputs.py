from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / "inputs.json").read_text())
receipt = json.loads((HERE / "racket.json").read_text())
outputs = [row["output"] for row in receipt["results"]]

def rival(grid):
    out = [row[:] for row in grid]
    c1 = grid[2][2]
    for r in range(2, 4):
        for c in range(2, 4): out[r][c] = c1
    c2 = grid[6][9]
    for r in range(6, 8):
        for c in range(8, 11): out[r][c] = c2
    return out

matches = [rival(g) == o for g, o in zip(inputs, outputs)]
report = {
    "schema": "arc-generator-audit-rival-comparison-v1",
    "task_id": "8ab650d5f4cb",
    "generator_sha256": receipt["generator_sha256"],
    "rule_hash": receipt["executed_rule_hash"],
    "draws": len(inputs),
    "fixed_coordinate_rival_matches": sum(matches),
    "all_generated_labels_fit_shortcut": all(matches),
    "mismatching_indices": [i for i, ok in enumerate(matches) if not ok],
}
(HERE / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
