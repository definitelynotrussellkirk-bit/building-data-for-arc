from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "0eb4eaa46003"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = ROOT / "generators" / TASK / "generator.py"
OUT = Path(__file__).with_name("exact_copy_shortcut.json")

spec = importlib.util.spec_from_file_location("audited_0eb", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                        grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append({"color": color, "cells": sorted(cells)})
    return sorted(out, key=lambda obj: min(obj["cells"]))


def normalized(obj):
    cells = obj["cells"]
    top = min(r for r, _ in cells); left = min(c for _, c in cells)
    return tuple(sorted((r-top, c-left) for r, c in cells))


def row_profile(obj):
    cells = obj["cells"]
    lo, hi = min(r for r,_ in cells), max(r for r,_ in cells)
    return tuple(sum(r == rr for r,_ in cells) for rr in range(lo, hi+1))


def col_profile(obj):
    cells = obj["cells"]
    lo, hi = min(c for _,c in cells), max(c for _,c in cells)
    return tuple(sum(c == cc for _,c in cells) for cc in range(lo, hi+1))


def crop8(obj):
    cells = obj["cells"]
    top = min(r for r,_ in cells); bottom = max(r for r,_ in cells)
    left = min(c for _,c in cells); right = max(c for _,c in cells)
    out = [[0]*(right-left+1) for _ in range(bottom-top+1)]
    for r,c in cells: out[r-top][c-left] = 8
    return out


def selections(grid):
    objs = components(grid)
    blue = next(obj for obj in objs if obj["color"] == 1)
    red = next(obj for obj in objs if obj["color"] == 2)
    candidates = [obj for obj in objs if obj["color"] not in (1,2)]
    intended = next(obj for obj in candidates
                    if row_profile(obj) == row_profile(blue)
                    and col_profile(obj) == col_profile(red))
    rival = next(obj for obj in candidates if normalized(obj) == normalized(blue))
    return objs, blue, red, intended, rival

rows = []
matches = 0
calls = 0
example = None
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = module.generate(10000 + index, index, difficulty=band)
        objs, blue, red, intended, rival = selections(grid)
        calls += 1
        same = crop8(intended) == crop8(rival)
        matches += int(same)
        if example is None:
            example = {
                "band": band,
                "seed": 10000 + index,
                "sample_index": index,
                "input": grid,
                "blue_normalized": normalized(blue),
                "red_normalized": normalized(red),
                "intended_target_normalized": normalized(intended),
                "exact_copy_rival_target_normalized": normalized(rival),
                "intended_output": crop8(intended),
                "rival_output": crop8(rival),
                "object_sizes": [len(obj["cells"]) for obj in objs],
            }

report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "claim": "A blue-exact-copy shortcut ignores the red anchor yet matches generated lessons.",
    "calls": calls,
    "shortcut_matches": matches,
    "all_matched": matches == calls,
    "example": example,
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k:v for k,v in report.items() if k != "example"}, indent=2))
