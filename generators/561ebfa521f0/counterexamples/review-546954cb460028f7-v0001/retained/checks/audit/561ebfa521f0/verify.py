from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path

BASE = Path("../checks/audit/561ebfa521f0")
inputs = json.loads((BASE / "input.json").read_text())
racket = json.loads((BASE / "racket.json").read_text())


def marker(grid, color):
    return next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color)


def distances(grid, start):
    h, w = len(grid), len(grid[0]); q = deque([start]); dist = {start: 0}
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            p = (r+dr, c+dc)
            if 0 <= p[0] < h and 0 <= p[1] < w and grid[p[0]][p[1]] != 5 and p not in dist:
                dist[p] = dist[(r,c)] + 1; q.append(p)
    return dist


def leg(grid, a, b):
    da, db = distances(grid, a), distances(grid, b)
    if b not in da: return set()
    d = da[b]
    return {p for p in da.keys() & db.keys() if da[p] + db[p] == d}


def intended(grid):
    out = deepcopy(grid); a, b, c = marker(grid, 2), marker(grid, 4), marker(grid, 3)
    for r, col in leg(grid, a, b) | leg(grid, b, c):
        if out[r][col] == 0: out[r][col] = 8
    return out

expected = [intended(g) for g in inputs]
actual = [row["output"] for row in racket["results"]]
report = {
    "schema": "review-audit-racket-verification-v1",
    "task_id": racket["task_id"],
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "inputs": len(inputs),
    "independent_bfs_matches_racket": [a == e for a, e in zip(actual, expected)],
    "all_match": actual == expected,
    "disconnected_output": actual[-1],
}
(BASE / "verification-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
if not report["all_match"]:
    raise SystemExit(1)
