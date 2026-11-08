#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "4d730bbef8df"


def centers(grid):
    return [
        (r, c)
        for r in range(1, len(grid) - 1)
        for c in range(1, len(grid[0]) - 1)
        if all(
            grid[r + dr][c + dc] == 3
            for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
        )
    ]


def one_slope_rival(grid):
    """Connect only NW-SE aligned plus centers (same signed row/col delta)."""
    out = [row[:] for row in grid]
    points = centers(grid)
    for index, (r1, c1) in enumerate(points):
        for r2, c2 in points[index + 1 :]:
            if r2 - r1 != c2 - c1:
                continue
            step = 1 if r2 > r1 else -1
            for distance in range(1, abs(r2 - r1)):
                row, col = r1 + distance * step, c1 + distance * step
                if out[row][col] == 0:
                    out[row][col] = 2
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


episode = json.loads((HERE / "episode.jsonl").read_text())
pairs = episode["train"] + episode["test"]
comparisons = []
for index, pair in enumerate(pairs):
    rival = one_slope_rival(pair["input"])
    expected = pair["output"]
    diffs = [
        {"row": row, "col": col, "racket": expected[row][col], "rival": rival[row][col]}
        for row in range(len(expected))
        for col in range(len(expected[0]))
        if expected[row][col] != rival[row][col]
    ]
    comparisons.append(
        {
            "role": "train" if index < 3 else "query",
            "sample_index": episode["sample_indices"][index],
            "centers": centers(pair["input"]),
            "rival_matches": not diffs,
            "cell_diff": diffs,
        }
    )

result = {
    "schema": "arcpuzzles-audit-reproduction-v1",
    "task_id": TASK_ID,
    "finding": "three demonstrations permit a natural one-diagonal-orientation rival that fails the query",
    "seed": episode["seed"],
    "sample_indices": episode["sample_indices"],
    "generator_version": episode["generator_version"],
    "generator_sha256": episode["provenance"]["generator_sha256"],
    "current_generator_sha256": sha256(REPO / "generators" / TASK_ID / "generator.py"),
    "executed_rule_hash": episode["executed_rule_hash"],
    "program_utf8_sha256": hashlib.sha256(episode["program"].encode()).hexdigest(),
    "production_approved": episode["provenance"]["approved"],
    "train_safety": episode["provenance"]["train_safety"],
    "lesson_check": episode["lesson_check"],
    "comparisons": comparisons,
    "reproduced": all(row["rival_matches"] for row in comparisons[:3])
    and not comparisons[3]["rival_matches"],
    "scope": "one deterministic four-pair production episode; not a failure-rate estimate",
}
assert result["generator_sha256"] == result["current_generator_sha256"]
assert result["reproduced"]
(HERE / "comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"reproduced": True, "demo_matches": [r["rival_matches"] for r in comparisons[:3]], "query_diff": comparisons[3]["cell_diff"]}, sort_keys=True))
