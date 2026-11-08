#!/usr/bin/env python3
"""Compare exact Racket labels with the smallest-any-color rival."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path

TASK_ID = "04e2ffe8dc8e"
ROOT = Path.cwd().resolve()
OUTDIR = ROOT.parent / "checks" / "audit" / TASK_ID


def digest(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    found = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        q = deque([start])
        cells = {start}
        while q:
            r, c = q.popleft()
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    q.append((nr, nc))
        found.append((color, sorted(cells)))
    return found


def smallest_any_color(grid):
    objects = components(grid)
    if not objects:
        raise ValueError("no foreground object")
    # Same deterministic top-left tie convention as the authority's green sort.
    color, cells = min(objects, key=lambda item: (len(item[1]), item[1][0], item[0]))
    out = deepcopy(grid)
    for r, c in cells:
        out[r][c] = 6
    return out, {"source_color": color, "size": len(cells), "first_cell": cells[0]}


case = json.loads((OUTDIR / "case.json").read_text(encoding="utf-8"))
racket = json.loads((OUTDIR / "racket.json").read_text(encoding="utf-8"))
results = racket["results"]
if len(results) != len(case["inputs"]):
    raise AssertionError("Racket result/input length mismatch")

rows = []
for name, grid, result in zip(case["inputs_order"], case["inputs"], results):
    authority = result["output"]
    rival, chosen = smallest_any_color(grid)
    rows.append({
        "name": name,
        "valid_output": result["valid_output"],
        "error": result["error"],
        "rival_fits": rival == authority,
        "rival_choice": chosen,
        "input_sha256": digest(grid),
        "authority_sha256": digest(authority),
        "rival_sha256": digest(rival),
        "difference_cells": sum(
            a != b for ar, br in zip(authority, rival) for a, b in zip(ar, br)
        ),
        "input": grid,
        "authority_output": authority,
        "rival_output": rival,
    })

override = rows[0]
default = rows[1:]
report = {
    "schema": "arc-audit-reproducer-v1",
    "task_id": TASK_ID,
    "generator_sha256": case["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "rival": "recolor the globally smallest same-color 4-connected non-background object magenta",
    "explicit_override": {
        "call": case["override_call"],
        "self_check": case["override_self_check"],
        "non_green_nonzero_cells": case["override_non_green_nonzero_cells"],
        "row": override,
        "reproduced": (
            not case["override_self_check"]
            and case["override_non_green_nonzero_cells"] == 0
            and override["rival_fits"]
        ),
    },
    "default_three_demo_window": {
        "calls": case["default_calls"],
        "self_checks": case["default_self_checks"],
        "demo_rival_fits": [row["rival_fits"] for row in default[:3]],
        "query_rival_fits": default[3]["rival_fits"],
        "rows": default,
        "reproduced": (
            all(not errors for errors in case["default_self_checks"])
            and all(row["rival_fits"] for row in default[:3])
            and not default[3]["rival_fits"]
        ),
    },
    "target_modified": False,
}
report["reproduced"] = report["explicit_override"]["reproduced"] and report["default_three_demo_window"]["reproduced"]
(OUTDIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": report["generator_sha256"],
    "executed_rule_hash": report["executed_rule_hash"],
    "explicit_override_reproduced": report["explicit_override"]["reproduced"],
    "default_window_reproduced": report["default_three_demo_window"]["reproduced"],
    "demo_rival_fits": report["default_three_demo_window"]["demo_rival_fits"],
    "query_rival_fits": report["default_three_demo_window"]["query_rival_fits"],
    "out": str(OUTDIR / "probe.json"),
}, indent=2))
raise SystemExit(0 if report["reproduced"] else 1)
