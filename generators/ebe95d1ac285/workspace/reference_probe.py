"""Independent geometry oracle and test helpers for ebe95d1ac285."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

TASK_ID = "ebe95d1ac285"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    root = find_root(__file__)
    assert canonical_path(root).is_file()
    return _canonical_pairs(TASK_ID, root=root, labeled_only=True)


def canonical_rule_hash() -> str:
    root = find_root(__file__)
    path = canonical_path(root)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                source = " ".join(str(row["program_solution"]).split())
                return hashlib.sha256(source.encode()).hexdigest()[:12]
    raise AssertionError("selected canonical rule not found")


def _norm(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def symmetry_class(cells) -> int:
    shape = _norm(cells)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    row_symmetric = all((height - 1 - row, col) in shape for row, col in shape)
    col_symmetric = all((row, width - 1 - col) in shape for row, col in shape)
    return 3 if row_symmetric and col_symmetric else 1 if row_symmetric else 2 if col_symmetric else 0


def components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for row_delta, col_delta in CARDINAL:
                    neighbor = (current[0] + row_delta, current[1] + col_delta)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append({"color": color, "cells": frozenset(cells)})
    return sorted(result, key=lambda item: min(item["cells"]))


def border_touch(cells, height, width) -> bool:
    return any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells)


def analyze(grid):
    height, width = len(grid), len(grid[0])
    objects = components(grid)
    anchors = [obj for obj in objects if obj["color"] == 2]
    if len(anchors) != 1:
        raise ValueError(f"expected one color-2 anchor, got {len(anchors)}")
    anchor = anchors[0]
    anchor_touch = border_touch(anchor["cells"], height, width)
    anchor_sym = symmetry_class(anchor["cells"])
    groups = {"match": [], "same_touch": [], "same_sym": [], "neutral": []}
    for obj in objects:
        touch = border_touch(obj["cells"], height, width)
        sym = symmetry_class(obj["cells"])
        obj = {**obj, "touch": touch, "sym": sym}
        if obj is anchor or obj["color"] == 2:
            continue
        if touch == anchor_touch and sym == anchor_sym:
            groups["match"].append(obj)
        elif touch == anchor_touch:
            groups["same_touch"].append(obj)
        elif sym == anchor_sym:
            groups["same_sym"].append(obj)
        else:
            groups["neutral"].append(obj)
    return {
        "height": height,
        "width": width,
        "objects": objects,
        "anchor": anchor,
        "anchor_touch": anchor_touch,
        "anchor_sym": anchor_sym,
        **groups,
    }


def observed(grid):
    info = analyze(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "anchor_sym": info["anchor_sym"],
        "anchor_touch": info["anchor_touch"],
        "match_count": len(info["match"]),
        "same_touch_distractors": len(info["same_touch"]),
        "same_sym_distractors": len(info["same_sym"]),
        "neutral_distractors": len(info["neutral"]),
    }


def _paint_selected(grid, selector):
    info = analyze(grid)
    output = deepcopy(grid)
    for obj in info["objects"]:
        if obj["color"] == 2:
            continue
        touch = border_touch(obj["cells"], info["height"], info["width"])
        sym = symmetry_class(obj["cells"])
        if selector(touch, sym, info["anchor_touch"], info["anchor_sym"]):
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def intended_output(grid):
    return _paint_selected(grid, lambda touch, sym, atouch, asym: touch == atouch and sym == asym)


def touch_only_rival(grid):
    return _paint_selected(grid, lambda touch, sym, atouch, asym: touch == atouch)


def symmetry_only_rival(grid):
    return _paint_selected(grid, lambda touch, sym, atouch, asym: sym == asym)
