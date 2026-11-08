from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "306332da48b4"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append([rr, cc])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append({"color": color, "cells": sorted(cells)})
    return out

calls = {}
for requested in (2, 3):
    grid = GEN.generate(
        17,
        0,
        difficulty="medium",
        n_blobs=requested,
    )
    calls[str(requested)] = {
        "grid": grid,
        "grid_sha256": hashlib.sha256(
            json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "self_check": GEN.self_check(grid),
        "components": components(grid),
    }

report = {
    "schema": "arc-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "source_path": str(SOURCE_PATH.relative_to(ROOT)),
    "seed": 17,
    "sample_index": 0,
    "difficulty": "medium",
    "override": "n_blobs",
    "calls": calls,
    "same_grid": calls["2"]["grid"] == calls["3"]["grid"],
    "observed_component_counts": {
        key: len(value["components"]) for key, value in calls.items()
    },
    "finding": (
        "advertised exact n_blobs override is ignored"
        if calls["2"]["grid"] == calls["3"]["grid"]
        else "not reproduced"
    ),
}

out = Path("../checks/audit/306332da48b4/probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
Path("../checks/audit/306332da48b4/input.json").write_text(
    json.dumps(calls["3"]["grid"], indent=2) + "\n"
)
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "same_grid": report["same_grid"],
    "observed_component_counts": report["observed_component_counts"],
    "self_check": {k: v["self_check"] for k, v in calls.items()},
}, sort_keys=True))
