#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / "repo/generators/b570c79ec730/generator.py"
CANONICAL_PATH = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
OUT_DIR = ROOT / "checks/audit/b570c79ec730"

spec = importlib.util.spec_from_file_location("audit_b570_generator", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        seed = min(unseen)
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        cells = set()
        while stack:
            r, c = stack.pop()
            if (r, c) not in unseen or grid[r][c] != color:
                continue
            unseen.remove((r, c))
            cells.add((r, c))
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in unseen:
                    stack.append((nr, nc))
        out.append((color, cells))
    return out


def full_bbox_outline_rival(grid):
    """Canonical-fitting rival: replace each component by its full bbox outline."""
    out = [row[:] for row in grid]
    for color, cells in components(grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        for r, c in cells:
            if r1 < r < r2 and c1 < c < c2:
                out[r][c] = 0
        for c in range(c1, c2 + 1):
            out[r1][c] = color
            out[r2][c] = color
        for r in range(r1, r2 + 1):
            out[r][c1] = color
            out[r][c2] = color
    return out


def load_task(task_id):
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


task = load_task("b570c79ec730")
pairs = list(task["train"])
test = task["test"]
if isinstance(test, dict):
    pairs.append(test)
else:
    pairs.extend(test)
canonical_fit = []
for index, pair in enumerate(pairs):
    predicted = full_bbox_outline_rival(pair["input"])
    canonical_fit.append({"pair_index": index, "fits": predicted == pair["output"]})
assert all(item["fits"] for item in canonical_fit), canonical_fit

seed = 570001
sample_index = 0
difficulty = "medium"
overrides = {"scene_profile": "notched_border"}
grid = mod.generate(seed, sample_index, difficulty=difficulty, **overrides)
errors = mod.self_check(grid, difficulty=difficulty)
observed = mod.observe_overrides(grid)
intended = mod.rule_mirror(grid)
rival = full_bbox_outline_rival(grid)
assert not errors, errors
assert observed == overrides, observed
assert intended != rival

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(OUT_DIR / "python_intended.json").write_text(json.dumps(intended, indent=2) + "\n")
(OUT_DIR / "rival_full_bbox_outline.json").write_text(json.dumps(rival, indent=2) + "\n")
report = {
    "schema": "arc-audit-probe-v1",
    "task_id": mod.TASK_ID,
    "version": mod.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": mod.RULE_HASH,
    "rival": "replace every monochrome component by the complete outline of its bounding box",
    "canonical_pairs_checked": len(canonical_fit),
    "canonical_fit": canonical_fit,
    "generation": {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "observed": observed,
        "self_check": errors,
        "documented_domain": True,
    },
    "disagreement": {
        "intended_differs_from_rival": intended != rival,
        "differing_cells": [
            {"row": r, "col": c, "intended": intended[r][c], "rival": rival[r][c]}
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if intended[r][c] != rival[r][c]
        ],
    },
}
(OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
