from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "2cefa1581476"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec and spec.loader
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)


def facts(comp):
    r0, c0, r1, c1 = comp["bbox"]
    return {
        "color": comp["color"],
        "bbox": [r0, c0, r1, c1],
        "cells": len(comp["cells"]),
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
    }


def crop(grid, comp):
    r0, c0, r1, c1 = comp["bbox"]
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in comp["cells"]:
        out[r - r0][c - c0] = grid[r][c]
    return out


def pack(grid, ordered):
    crops = [crop(grid, comp) for comp in ordered]
    h = max(len(piece) for piece in crops)
    w = sum(len(piece[0]) for piece in crops) + len(crops) - 1
    out = [[0] * w for _ in range(h)]
    left = 0
    for piece in crops:
        top = h - len(piece)
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


grid = G.generate(0, 0, difficulty="easy")
validation = G.self_check(grid, difficulty="easy")
if validation:
    raise AssertionError(validation)
components = G._components4(grid)
authority = sorted(
    components,
    key=lambda comp: (
        -(comp["bbox"][2] - comp["bbox"][0] + 1),
        -(comp["bbox"][3] - comp["bbox"][1] + 1),
        comp["bbox"][1],
        comp["bbox"][0],
    ),
)
documented = sorted(
    components,
    key=lambda comp: (
        -(comp["bbox"][2] - comp["bbox"][0] + 1),
        comp["color"],
    ),
)
authority_output = pack(grid, authority)
rival_output = pack(grid, documented)
if authority_output == rival_output:
    raise AssertionError("selected seed does not distinguish tie-break rules")

(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
record = {
    "schema": "arcpuzzles-audit-probe-v1",
    "target_task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "overrides": {},
    "validator_result": validation,
    "components": [facts(comp) for comp in components],
    "authority_order": [facts(comp) for comp in authority],
    "documented_height_then_color_order": [facts(comp) for comp in documented],
    "independent_authority_mirror": authority_output,
    "documented_rival_output": rival_output,
    "outputs_differ": authority_output != rival_output,
    "input_file": "input.json",
}
(HERE / "probe.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "generator_sha256": record["generator_sha256"],
    "validator_result": validation,
    "authority_colors": [comp["color"] for comp in authority],
    "documented_colors": [comp["color"] for comp in documented],
    "outputs_differ": record["outputs_differ"],
}, indent=2))
