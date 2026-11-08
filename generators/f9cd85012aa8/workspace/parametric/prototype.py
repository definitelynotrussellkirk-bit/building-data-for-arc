"""Native parametric family for ARC task f9cd85012aa8.

The default is the byte-exact canonical rule.  The alternate keeps the same
"select an object, then fill its bounding box" output grammar but composes two
input-derived steps:

1. measure the number of cells in the sole sparse color-6 anchor;
2. use ``(anchor_size - 3) mod candidate_count`` to select a row-major
   non-6 object, then fill that object's bounding box with its own color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "f9cd85012aa8"
MODES = ("canonical_target", "anchor_size_relay")
DEFAULT_MODE = "canonical_target"
CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
PALETTE = (1, 2, 3, 4, 5, 7, 8, 9)

CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
RELAY_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (anchor (first (filter (lambda (obj) (= (obj-color obj) 6)) objs)))
         (candidates (filter (lambda (obj) (not (= (obj-color obj) 6))) objs))
         (anchor-size (obj-size anchor))
         (target-index (modulo (- anchor-size 3) (length candidates)))
         (target (nth candidates target-index))
         (bb (obj-bbox target))
         (color (obj-color target)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (if (and (>= r (first bb)) (<= r (third bb))
                 (>= c (second bb)) (<= c (fourth bb)))
            color
            0))))))"""
WRONG_PLUS_ONE_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects g 0))
         (anchor (first (filter (lambda (obj) (= (obj-color obj) 6)) objs)))
         (candidates (filter (lambda (obj) (not (= (obj-color obj) 6))) objs))
         (anchor-size (obj-size anchor))
         (target-index (modulo (- anchor-size 2) (length candidates)))
         (target (nth candidates target-index))
         (bb (obj-bbox target))
         (color (obj-color target)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (if (and (>= r (first bb)) (<= r (third bb))
                 (>= c (second bb)) (<= c (fourth bb)))
            color
            0))))))"""

# height, width, anchor size, row-major candidate sizes.
_DEMO_SPECS = (
    (14, 18, 3, (4, 8, 5, 7)),
    (16, 20, 5, (8, 3, 6, 4)),
    (18, 22, 4, (7, 5, 9, 3)),
    (20, 24, 6, (4, 8, 5, 9)),
    (22, 26, 7, (6, 3, 10, 5)),
    (24, 28, 10, (5, 9, 4, 8)),
)
_QUERY_SPECS = (
    (16, 20, 4, (9, 4, 7, 5)),
    (20, 24, 8, (5, 8, 3, 10)),
    (24, 28, 9, (4, 7, 9, 5)),
    (30, 30, 10, (3, 4, 5, 6, 7, 8)),
)
_FIVE_SLOTS = ("tl", "tr", "ml", "mr", "bc")
_SEVEN_SLOTS = ("tl", "tc", "tr", "ml", "mr", "bl", "br")


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"target_mode"}:
        raise ValueError("settings must contain exactly target_mode")
    mode = settings["target_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"target_mode must be one of {MODES}")
    return {"target_mode": mode}


def rule_text(mode: str) -> str:
    if mode == "canonical_target":
        return CANONICAL_PROGRAM
    if mode == "anchor_size_relay":
        return RELAY_PROGRAM
    raise ValueError(f"unknown target_mode {mode!r}")


def counterfactual_program() -> str:
    return WRONG_PLUS_ONE_PROGRAM


def _mix(*parts: object) -> int:
    text = ":".join(map(str, (TASK_ID, "anchor-size-relay-v1", *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape(size: int, variant: int):
    """Connected exact-size sparse shape touching every side of its bbox."""
    if type(size) is not int or not 3 <= size <= 10:
        raise ValueError("object size must be in 3..10")
    options = [
        (height, width)
        for height in range(2, 6)
        for width in range(2, 6)
        if height + width - 1 <= size < height * width
    ]
    options.sort(key=lambda hw: (hw[0] * hw[1], max(hw), hw))
    height, width = options[variant % len(options)]
    cells = {(r, 0) for r in range(height)} | {(height - 1, c) for c in range(width)}
    rng = random.Random(variant)
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in CARD
            if 0 <= r + dr < height and 0 <= c + dc < width
        } - cells)
        cells.add(rng.choice(frontier))
    transformed = list(cells)
    if (variant // 5) % 2:
        transformed = [(r, width - 1 - c) for r, c in transformed]
    if (variant // 11) % 2:
        transformed = [(height - 1 - r, c) for r, c in transformed]
    if (variant // 17) % 2:
        transformed = [(c, r) for r, c in transformed]
    return _normalize(transformed)


def _slot_position(slot: str, height: int, width: int, shape):
    shape_h = 1 + max(r for r, _ in shape)
    shape_w = 1 + max(c for _, c in shape)
    if shape_h > 5 or shape_w > 5 or height < 14 or width < 18:
        raise ValueError("slot geometry expects <=5x5 shapes on >=14x18 grids")
    # A shared row band keeps the two middle candidates in left-to-right
    # order regardless of their independently varied shape heights.
    middle_top = max(5, height // 2 - 2)
    top = {
        "tl": 0, "tc": 0, "tr": 0,
        "ml": middle_top, "mr": middle_top,
        "bl": height - shape_h, "bc": height - shape_h, "br": height - shape_h,
    }[slot]
    left = {
        "tl": 0, "ml": 0, "bl": 0,
        "tc": (width - shape_w) // 2,
        "bc": (width - shape_w) // 2,
        "tr": width - shape_w, "mr": width - shape_w, "br": width - shape_w,
    }[slot]
    return top, left


def objects4(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    objects = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        objects.append({
            "color": color,
            "cells": frozenset(cells),
            "bbox": (r0, c0, r1, c1),
            "size": len(cells),
        })
    return sorted(objects, key=lambda obj: min(obj["cells"]))


def analyze(grid) -> dict[str, Any]:
    objects = objects4(grid)
    anchors = [obj for obj in objects if obj["color"] == 6]
    candidates = [obj for obj in objects if obj["color"] != 6]
    if len(anchors) != 1 or not candidates:
        raise ValueError("expected one color-6 anchor and at least one candidate")
    anchor = anchors[0]
    target_index = (anchor["size"] - 3) % len(candidates)
    return {
        "objects": objects,
        "anchor": anchor,
        "candidates": candidates,
        "anchor_size": anchor["size"],
        "target_index": target_index,
        "target": candidates[target_index],
    }


def _fill_bbox(grid, obj):
    out = [[0 for _ in row] for row in grid]
    r0, c0, r1, c1 = obj["bbox"]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = obj["color"]
    return out


def apply_mode(grid, mode: str):
    info = analyze(grid)
    if mode == "canonical_target":
        target = info["anchor"]
    elif mode == "anchor_size_relay":
        target = info["target"]
    else:
        raise ValueError(f"unknown target_mode {mode!r}")
    return _fill_bbox(grid, target)


def apply_wrong_plus_one(grid):
    info = analyze(grid)
    wrong_index = (info["anchor_size"] - 2) % len(info["candidates"])
    return _fill_bbox(grid, info["candidates"][wrong_index])


def _build_input(seed: int, split: str, index: int, spec):
    height, width, anchor_size, candidate_sizes = spec
    sizes = (anchor_size, *candidate_sizes)
    slots = _FIVE_SLOTS if len(sizes) == 5 else _SEVEN_SLOTS
    if len(sizes) != len(slots):
        raise ValueError("spec and slot count differ")
    colors = list(PALETTE)
    random.Random(_mix(seed, split, index, "colors")).shuffle(colors)
    object_colors = (6, *colors[:len(candidate_sizes)])
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied = set()
    for object_index, (size, slot, color) in enumerate(zip(sizes, slots, object_colors)):
        shape = _shape(size, _mix(seed, split, index, object_index, "shape"))
        top, left = _slot_position(slot, height, width, shape)
        cells = {(top + r, left + c) for r, c in shape}
        if occupied & cells:
            raise ValueError("object overlap")
        if any(
            (r + dr, c + dc) in occupied
            for r, c in cells
            for dr, dc in CARD
        ):
            raise ValueError("object adjacency")
        occupied.update(cells)
        for r, c in cells:
            grid[r][c] = color
    info = analyze(grid)
    if info["anchor_size"] != anchor_size:
        raise ValueError(f"anchor size drift: {info['anchor_size']} != {anchor_size}")
    if sorted(obj["size"] for obj in info["candidates"]) != sorted(candidate_sizes):
        raise ValueError("candidate size drift")
    if len({obj["color"] for obj in info["objects"]}) != len(info["objects"]):
        raise ValueError("object colors are not unique")
    if any(
        obj["size"] == (obj["bbox"][2] - obj["bbox"][0] + 1)
        * (obj["bbox"][3] - obj["bbox"][1] + 1)
        for obj in info["objects"]
    ):
        raise ValueError("constructed object unexpectedly fills its bbox")
    return grid


def _pair(seed: int, split: str, index: int, spec, mode: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, target_mode: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    if target_mode not in MODES:
        raise ValueError(f"unknown target_mode {target_mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [
        _pair(seed, "train", index, _DEMO_SPECS[index], target_mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _QUERY_SPECS[index], target_mode)
        for index in range(queries)
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": rule_text(target_mode),
    }


def public_turn(episode: dict[str, Any], query_index: int = 0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (
        json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    episode = generate_episode(seed, target_mode="anchor_size_relay", demos=6, queries=4)
    pair = next(
        candidate
        for candidate in episode["train"] + episode["test"]
        if apply_wrong_plus_one(candidate["input"]) != candidate["output"]
    )
    info = analyze(pair["input"])
    wrong_index = (info["anchor_size"] - 2) % len(info["candidates"])
    return {
        "settings": {"target_mode": "anchor_size_relay"},
        "program": RELAY_PROGRAM,
        "input": deepcopy(pair["input"]),
        "output": deepcopy(pair["output"]),
        "intermediate_value": {
            "anchor_size": info["anchor_size"],
            "candidate_count": len(info["candidates"]),
            "target_index": info["target_index"],
            "wrong_target_index": wrong_index,
        },
        "counterfactual_program": WRONG_PLUS_ONE_PROGRAM,
        "counterfactual_output": apply_wrong_plus_one(pair["input"]),
        "ablation": "wrong_intermediate",
    }
