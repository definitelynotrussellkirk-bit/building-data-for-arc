"""Constructive native lessons for the unchanged zero-component wall rules.

The retained prototype supplies both exact Racket materialization and claim
semantics. This module changes the input distribution: two mandatory teaching
scenes expose whole-bounding-side failures and the boundary asymmetries; a
fixed six-demo/four-query bank supplies compact, tall, wide, and dense cases.
Labels are deterministic Python claims for the native worker to replay through
protected Racket. No selected production generator or canonical source changes.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "5f9a2df57599"
VERSION = "2.0.0-native"
SIDE_POLICIES = ("canvas_edges", "gray_walls")
DEFAULT_SETTINGS = {"side_boundary_policy": "canvas_edges"}
MAX_DEMOS, MAX_QUERIES = 6, 4
_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_wall_prototype_5f9a2df57599_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent reviewed prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def normalize_settings(settings=None):
    if settings is None:
        return dict(DEFAULT_SETTINGS)
    if type(settings) is not dict or set(settings) != {"side_boundary_policy"}:
        raise ValueError("settings must name exactly side_boundary_policy")
    policy = settings["side_boundary_policy"]
    if type(policy) is not str or policy not in SIDE_POLICIES:
        raise ValueError("side_boundary_policy must be canvas_edges or gray_walls")
    return {"side_boundary_policy": policy}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain integer in {low}..{high}")
    return value


def program(settings=None):
    """Reuse the reviewed exact canonical source and its two-anchor extension."""
    return _PROTOTYPE.materialize_program(normalize_settings(settings)["side_boundary_policy"])


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _rng(seed, split, index):
    token = f"{TASK_ID}:{VERSION}:inputs:{seed}:{split}:{index}"
    return random.Random(int.from_bytes(hashlib.sha256(token.encode()).digest(), "big"))


def _blank(height, width, color=0):
    return [[color] * width for _ in range(height)]


def _stamp(grid, protected, row0, col0, height, width, zeros):
    """Stamp one disjoint gray-framed panel; never erase an earlier zero cue."""
    if not (0 <= row0 and row0 + height <= len(grid) and 0 <= col0 and col0 + width <= len(grid[0])):
        raise AssertionError("constructive panel escaped the canvas")
    absolute = {(row0 + r, col0 + c) for r, c in zeros}
    for r in range(row0, row0 + height):
        for c in range(col0, col0 + width):
            if (r, c) in protected and (r, c) not in absolute:
                raise AssertionError("constructive panels overlap a protected component")
            grid[r][c] = 0 if (r, c) in absolute else 5
    protected.update(absolute)


def _shape(height, width, style, rng):
    """Connected tight shapes, constructed without rejection sampling."""
    all_cells = {(r, c) for r in range(height) for c in range(width)}
    if style == "rectangle" or min(height, width) == 1:
        return all_cells
    if style == "ring" and min(height, width) >= 3:
        return {(r, c) for r, c in all_cells if r in (0, height - 1) or c in (0, width - 1)}
    if style == "notch":
        corner = rng.choice(((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)))
        return all_cells - {corner}
    row, col = rng.randrange(height), rng.randrange(width)
    cells = {(row, c) for c in range(width)} | {(r, col) for r in range(height)}
    # Every added row interval meets the vertical spine; the bbox stays tight.
    for r in range(height):
        if rng.randrange(3):
            low = rng.randrange(col + 1)
            high = rng.randrange(col, width)
            cells.update((r, c) for c in range(low, high + 1))
    if cells == all_cells:
        return all_cells - {(0 if row else height - 1, 0 if col else width - 1)}
    return cells


def _room(grid, protected, row, col, height, width, style, rng):
    cells = _shape(height, width, style, rng)
    top, left = max(0, row - 1), max(0, col - 1)
    bottom, right = min(len(grid), row + height + 1), min(len(grid[0]), col + width + 1)
    _stamp(grid, protected, top, left, bottom - top, right - left,
           {(row + r - top, col + c - left) for r, c in cells})


def _rejection_panel(grid, protected, top, left, side):
    """A three-cell L fails one entire bbox side because of a diagonal singleton.

    The singleton is an eligible separate four-component. Eight-connectivity
    merges it with the L, producing a different selection and painted support.
    """
    height, width = 5, 4
    zeros = {(1, 1), (1, 2), (2, 1), (3, 2)}
    rotations = {"bottom": 0, "left": 1, "top": 2, "right": 3}[side]
    for _ in range(rotations):
        zeros = {(c, height - 1 - r) for r, c in zeros}
        height, width = width, height
    _stamp(grid, protected, top, left, height, width, zeros)


def _background(grid, protected, rng, mode):
    """Vary interior wall spines and short top fragments without a solid top row."""
    height, width = len(grid), len(grid[0])
    segments = []
    if mode in ("horizontal", "elbow"):
        row = height // 2 + rng.choice((-1, 0, 1))
        segments.append([(row, c) for c in range(1, width - 1)])
    if mode in ("vertical", "elbow"):
        col = width // 2 + rng.choice((-1, 0, 1))
        segments.append([(r, col) for r in range(1, height - 1)])
    for _ in range(rng.randrange(1, 4)):
        row, col = rng.randrange(1, height - 1), rng.randrange(1, width - 1)
        if rng.randrange(2):
            segments.append([(row, c) for c in range(col, min(width - 1, col + rng.randrange(2, 6)))])
        else:
            segments.append([(r, col) for r in range(row, min(height - 1, row + rng.randrange(2, 6)))])
    start = rng.randrange(width - 3)
    segments.append([(0, c) for c in range(start, start + rng.randrange(1, 4))])
    for segment in segments:
        for r, c in segment:
            if (r, c) not in protected:
                grid[r][c] = 5


def _core(rng, index, mode):
    height = rng.randint(22, 24) if index == 0 else rng.randint(25, 27)
    width = rng.randint(24, 27) if index == 0 else rng.randint(25, 29)
    grid, protected = _blank(height, width), set()
    _room(grid, protected, 3, 4, rng.randint(5, 7), rng.randint(5, 7), rng.choice(("ring", "cross", "notch")), rng)
    _room(grid, protected, height - 9, 5, rng.randint(3, 4), rng.randint(4, 6), "rectangle", rng)
    _room(grid, protected, 2, 0, rng.randint(2, 3), rng.randint(2, 3), "rectangle", rng)
    _room(grid, protected, height - 6, 0, rng.randint(2, 3), 1, "rectangle", rng)
    _room(grid, protected, 10, width - 1, rng.randint(2, 4), 1, "rectangle", rng)
    _room(grid, protected, 0, width // 2, rng.randint(2, 3), rng.randint(2, 3), "rectangle", rng)
    _room(grid, protected, height - 2, width // 2, 2, rng.randint(2, 3), "rectangle", rng)
    sides = ("bottom", "right") if index == 0 else ("top", "left")
    _rejection_panel(grid, protected, 4, width - 7, sides[0])
    _rejection_panel(grid, protected, height - 7, width - 7, sides[1])
    _background(grid, protected, rng, mode)
    # The same three-cell L must sometimes pass: shape alone cannot replace
    # checking complete gray sides. Its frame shares only gray panel borders.
    _room(grid, protected, 11, 12, 2, 2, "notch", rng)
    return grid


def _compact(rng, height, width, mode):
    grid, protected = _blank(height, width, 5), set()
    _rejection_panel(grid, protected, 1, 1, rng.choice(("top", "bottom", "left", "right")))
    _room(grid, protected, 2, width - 1, 3, 1, "rectangle", rng)
    _room(grid, protected, height - 4, 0, 2, 1, "rectangle", rng)
    _room(grid, protected, 0, 2, 1, 2, "rectangle", rng)
    _room(grid, protected, height - 1, width - 2, 1, 2, "rectangle", rng)
    _room(grid, protected, height - 2, 2, 1, 2, "rectangle", rng)
    _background(grid, protected, rng, mode)
    # An all-gray compact background otherwise leaves only the four L rotations
    # as possible 8x8 inputs. Carve bounded extra zeros to vary connectivity and
    # side failures, keeping one interior region and all of its walls intact.
    # Existing boundary zeros remain, so both policies retain a rejected region.
    anchor = {(r, c) for r in range(height - 3, height) for c in range(1, 5)}
    candidates = [(r, c) for r in range(height) for c in range(width)
                  if grid[r][c] == 5 and (r, c) not in anchor]
    for row, col in rng.sample(candidates, rng.randint(2, 6)):
        grid[row][col] = 0
    return grid


def _tiled(rng, height, width, mode, *, stress=False):
    grid, protected = _blank(height, width), set()
    rows, cols = max(1, height // 9), max(1, width // 9)
    for i in range(rows):
        row_start, row_end = i * height // rows, (i + 1) * height // rows
        for j in range(cols):
            col_start, col_end = j * width // cols, (j + 1) * width // cols
            if stress and (i, j) == (1, 1):
                _rejection_panel(grid, protected, row_start + 2, col_start + 2, rng.choice(("top", "bottom", "left", "right")))
                continue
            inner_h, inner_w = row_end - row_start - 4, col_end - col_start - 4
            # Fixed margins leave lawful corridors for open edge contrasts.
            room_h = max(2, inner_h - rng.randrange(min(2, max(1, inner_h - 1))))
            room_w = max(2, inner_w - rng.randrange(min(2, max(1, inner_w - 1))))
            _room(grid, protected, row_start + 2, col_start + 2, room_h, room_w,
                  rng.choice(("rectangle", "ring", "cross", "notch")), rng)
    if stress:
        _room(grid, protected, 9, 0, 2, 3, "rectangle", rng)
        _room(grid, protected, 19, 0, 3, 1, "rectangle", rng)
        _room(grid, protected, 9, width - 1, 2, 1, "rectangle", rng)
        _room(grid, protected, 0, 9, 2, 2, "rectangle", rng)
        _room(grid, protected, height - 2, 19, 2, 2, "rectangle", rng)
    else:
        # These edge chambers stay outside the inset tiled region bounding boxes.
        _room(grid, protected, 0, width - 2, 1, 2, "rectangle", rng)
        _room(grid, protected, height - 1, 0, 1, 2, "rectangle", rng)
        _room(grid, protected, 2, width - 1, min(3, height - 3), 1, "rectangle", rng)
    _background(grid, protected, rng, mode)
    return grid


def analyze_scene(grid):
    """Private, input-derived intermediate facts; independent of chosen policy."""
    grid = _PROTOTYPE._validate_grid(grid)
    height, width = len(grid), len(grid[0])
    regions = []
    for cells in _PROTOTYPE._zero_components(grid):
        row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
        col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
        walls = {
            "top": row0 > 0 and all(grid[row0 - 1][c] == 5 for c in range(col0, col1 + 1)),
            "bottom": row1 < height - 1 and all(grid[row1 + 1][c] == 5 for c in range(col0, col1 + 1)),
            "left": col0 > 0 and all(grid[r][col0 - 1] == 5 for r in range(row0, row1 + 1)),
            "right": col1 < width - 1 and all(grid[r][col1 + 1] == 5 for r in range(row0, row1 + 1)),
        }
        excluded = col0 == col1 == 0 and row1 > row0
        common = walls["top"] and walls["bottom"] and not excluded
        eligible = {
            "canvas_edges": common and (walls["left"] or col0 == 0) and (walls["right"] or col1 == width - 1),
            "gray_walls": common and walls["left"] and walls["right"],
        }
        regions.append({
            "cells": [list(cell) for cell in sorted(cells)],
            "bbox": [row0, col0, row1, col1],
            "shape": [row1 - row0 + 1, col1 - col0 + 1], "size": len(cells),
            "rectangle": len(cells) == (row1 - row0 + 1) * (col1 - col0 + 1),
            "touches_edges": {"top": row0 == 0, "bottom": row1 == height - 1,
                              "left": col0 == 0, "right": col1 == width - 1},
            "walls": walls, "excluded_left_vertical": excluded, "eligible_by_policy": eligible,
        })
    return {
        "shape": [height, width], "component_count": len(regions), "regions": regions,
        "gray_cells": sum(value == 5 for row in grid for value in row),
        "top_row": list(grid[0]),
        "eligible_counts": {policy: sum(region["eligible_by_policy"][policy] for region in regions) for policy in SIDE_POLICIES},
        "painted_cells": {policy: sum(region["size"] for region in regions if region["eligible_by_policy"][policy]) for policy in SIDE_POLICIES},
    }


def _input_bank(seed):
    banks = {"train": [], "test": []}
    records = {"train": [], "test": []}
    for split, count in (("train", MAX_DEMOS), ("test", MAX_QUERIES)):
        for index in range(count):
            rng = _rng(seed, split, index)
            mode = ("horizontal", "vertical", "elbow")[(seed + index + (split == "test")) % 3]
            if split == "train" and index < 2:
                profile = "core_bottom_right" if index == 0 else "core_top_left"
                grid = _core(rng, index, mode)
            elif split == "train" and index == 2:
                profile = "compact_varied"
                grid = _compact(rng, rng.randint(9, 11), rng.randint(9, 12), mode)
            elif split == "test" and index == 0:
                profile = "compact_8x8"
                grid = _compact(rng, 8, 8, mode)
            elif split == "test" and index == 3:
                profile = "dense_30x30"
                grid = _tiled(rng, 30, 30, mode, stress=True)
            else:
                limits = {("train", 3): (14, 17, 15, 18), ("train", 4): (28, 30, 12, 14),
                          ("train", 5): (12, 14, 28, 30), ("test", 1): (18, 21, 19, 23),
                          ("test", 2): (30, 30, 19, 22)}
                loh, hih, low, hiw = limits[split, index]
                height, width = rng.randint(loh, hih), rng.randint(low, hiw)
                if split == "test" and index == 2 and seed % 2:
                    height, width = width, height
                profile = "tiled_tall" if height > width else "tiled_wide"
                grid = _tiled(rng, height, width, mode)
            banks[split].append(grid)
            records[split].append({"index": index, "profile": profile, "attempts": 1,
                                   "backbone": mode, "input_sha256": _digest(grid),
                                   "facts": analyze_scene(grid)})
    signatures = [_digest(grid) for split in ("train", "test") for grid in banks[split]]
    if len(signatures) != len(set(signatures)):
        raise AssertionError("constructive dimension-separated input bank is not distinct")
    return banks, records


def generate(seed, settings=None, demos=3, queries=4):
    """Build the entire deterministic bank before taking independent prefixes."""
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    selected = normalize_settings(settings)
    demos = _integer(demos, 2, MAX_DEMOS, "demos")
    queries = _integer(queries, 1, MAX_QUERIES, "queries")
    banks, records = _input_bank(seed)
    policy = selected["side_boundary_policy"]
    labeled = {
        split: [{"input": deepcopy(grid), "output": _PROTOTYPE.python_apply(grid, policy)} for grid in grids]
        for split, grids in banks.items()
    }
    return {
        "train": labeled["train"][:demos], "test": labeled["test"][:queries],
        "program_solution": program(selected),
        "meta": {
            "schema": "arcpuzzles-native-wall-family-v1", "task_id": TASK_ID, "version": VERSION,
            "seed": seed, "settings": selected, "counts": {"demos": demos, "queries": queries},
            "bank_counts": {"demos": MAX_DEMOS, "queries": MAX_QUERIES},
            "sampler": {"construction": "bounded direct panels and compact zero distractors", "max_attempts_per_scene": 1,
                        "settings_affect_inputs": False, "prefix_stable": True},
            "fixtures": records,
            "sequential_dependency": {"step_a": "Find orthogonally connected zero components in the input.",
                "intermediate": "Actual component cells, bounding boxes, and complete gray bbox-side facts.",
                "step_b": "Apply the episode side-boundary policy and column-zero exclusion, then paint eligible component cells.",
                "why_b_depends_on_a": "The selected cells and all four side extents are derived from each input component; size, enclosure, or a guessed bounding box gives different selections."},
            "label_status": "Python claims; protected Racket verification is external to generation",
        },
    }
