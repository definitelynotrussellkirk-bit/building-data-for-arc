#!/usr/bin/env python3
"""Verify the frame-preserving rival against the retained canonical apply receipt."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "repo/shared/runtime"), str(ROOT / "repo/src")]
TASK = "ee64b9b0fe20"
SOURCE = ROOT / f"repo/generators/{TASK}/generator.py"
BASE = ROOT / f"checks/audit/{TASK}/frame-gap"

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def frame_preserving_rival(grid):
    out = module.rule_mirror(grid)
    h, w, _bg, components, _shapes = module._analyze(grid)
    for color, cells in components:
        if module._bbox(cells) == (0, 0, h - 1, w - 1):
            for r, c in cells:
                out[r][c] = color
    return out

inputs = json.loads((BASE / "input.json").read_text())
receipt = json.loads((BASE / "racket.json").read_text())
authority = [row["output"] for row in receipt["results"]]
rivals = [frame_preserving_rival(grid) for grid in inputs]
matches = [rival == actual for rival, actual in zip(rivals, authority)]
assert matches == [True, True, True, False], matches
assert module.self_check(inputs[-1]) == []
retained = json.loads((BASE / "rival_outputs.json").read_text())
assert rivals == retained
print(json.dumps({"status": "REPRODUCED", "rival_matches_authority": matches}))
