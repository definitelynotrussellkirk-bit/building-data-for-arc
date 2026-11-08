#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.runtime import apply_rule

TASK_ID = "8d7d1364cf11"
ROOT = Path.cwd()
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK_ID / "duplicate-anchor-witness.json"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def components8(grid, bg=4):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == bg or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != bg and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            found.append(sorted(cells))
    return found


def solve_with_match_policy(grid, choose_last=False):
    h, w = len(grid), len(grid[0])
    comps = components8(grid)
    shapes = [cells for cells in comps if len(cells) > 1]
    dots = [cells[0] for cells in comps if len(cells) == 1]
    flattened = [(shape, cell) for shape in shapes for cell in shape]
    out = [[4] * w for _ in range(h)]
    for dr, dc in dots:
        color = grid[dr][dc]
        matches = [(shape, cell) for shape, cell in flattened if grid[cell[0]][cell[1]] == color]
        if not matches:
            continue
        shape, (ar, ac) = matches[-1 if choose_last else 0]
        for r, c in shape:
            nr, nc = dr + r - ar, dc + c - ac
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = grid[r][c]
    return out


def main():
    grid = [[4] * 12 for _ in range(10)]
    # Two valid-looking 2x2 source templates share productive accent color 5.
    for r, c, value in (
        (1, 1, 2), (1, 2, 2), (2, 1, 2), (2, 2, 5),
        (1, 7, 3), (1, 8, 3), (2, 7, 3), (2, 8, 5),
        (6, 5, 5),  # productive dot, now ambiguous
        (8, 10, 9), # absent-color decoy
    ):
        grid[r][c] = value

    report = apply_rule(Catalog(ROOT), TASK_ID, [grid], reference="canonical", timeout=240)
    result = report["results"][0]
    if result.get("error"):
        raise RuntimeError(result["error"])
    authority = result["output"]
    first = solve_with_match_policy(grid, choose_last=False)
    last = solve_with_match_policy(grid, choose_last=True)
    module = load_generator()
    differing = [
        [r, c, authority[r][c], last[r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if authority[r][c] != last[r][c]
    ]
    payload = {
        "schema": "audit-duplicate-anchor-witness-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "finding": "production excludes duplicate productive source colors, so canonical first-match tie-breaking is not taught",
        "input": grid,
        "authority_output": authority,
        "first_match_mirror": first,
        "last_match_rival": last,
        "authority_matches_first": authority == first,
        "authority_differs_from_last": authority != last,
        "differing_cells": differing,
        "generator_self_check": module.self_check(grid),
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ("task_id", "generator_sha256", "authority_matches_first", "authority_differs_from_last", "differing_cells", "generator_self_check")}, indent=2))


if __name__ == "__main__":
    main()
