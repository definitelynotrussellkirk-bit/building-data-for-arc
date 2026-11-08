#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.runtime import apply_rule

TASK_ID = "fdb8815ba528"
ROOT = Path.cwd()
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK_ID / "overlapping-bbox-witness.json"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def components4(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append({"color": color, "cells": sorted(cells)})
    return found


def border(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if r in (r0, r1) or c in (c0, c1)}


def solve(grid, reverse=False):
    comps = components4(grid)
    if reverse:
        comps = list(reversed(comps))
    out = [[0] * len(grid[0]) for _ in grid]
    for comp in comps:
        for r, c in border(comp["cells"]):
            out[r][c] = comp["color"]
    return out


def main():
    grid = [[0] * 7 for _ in range(7)]
    # Color-2 top/left L, bbox rows 1..4 cols 1..4.
    for cell in [(1,1),(1,2),(1,3),(1,4),(2,1),(3,1),(4,1)]:
        grid[cell[0]][cell[1]] = 2
    # Color-3 right/bottom L, bbox rows 2..5 cols 2..5.
    for cell in [(2,5),(3,5),(4,5),(5,2),(5,3),(5,4),(5,5)]:
        grid[cell[0]][cell[1]] = 3

    report = apply_rule(Catalog(ROOT), TASK_ID, [grid], reference="canonical", timeout=240)
    result = report["results"][0]
    if result.get("error"):
        raise RuntimeError(result["error"])
    authority = result["output"]
    forward = solve(grid, reverse=False)
    reverse = solve(grid, reverse=True)
    module = load_generator()
    differing = [
        [r, c, authority[r][c], reverse[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if authority[r][c] != reverse[r][c]
    ]
    payload = {
        "schema": "audit-overlapping-bbox-witness-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "finding": "production rejects overlapping bbox footprints, so overwrite precedence is not taught",
        "input": grid,
        "authority_output": authority,
        "row_major_component_order_output": forward,
        "reverse_component_order_rival": reverse,
        "authority_matches_row_major": authority == forward,
        "authority_differs_from_reverse": authority != reverse,
        "differing_cells": differing,
        "generator_self_check": module.self_check(grid),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("task_id", "generator_sha256", "authority_matches_row_major", "authority_differs_from_reverse", "differing_cells", "generator_self_check")}, indent=2))


if __name__ == "__main__":
    main()
