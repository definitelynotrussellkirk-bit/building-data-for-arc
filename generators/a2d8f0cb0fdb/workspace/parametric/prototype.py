"""Matched-input parametric family for ARC task a2d8f0cb0fdb.

The canonical setting uses the first nonzero header color and recolors every
blue body cell. The alternate segments the blue body, selects its unique
largest component, uses that component's input-derived size to index the three
visible header markers, and paints only the retained component with the
selected header color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "a2d8f0cb0fdb"
MODES = ("first_header_all", "largest_component_indexed_header")
DEFAULT_MODE = "first_header_all"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
CANONICAL_SHA256 = hashlib.sha256(CANONICAL_PROGRAM.encode()).hexdigest()

RELAY_PROGRAM = """(rule!
 (lambda (g)
   (let* ((header (filter (lambda (v) (!= v 0)) (first g)))
          (targets (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0)))
          (largest (first (sort targets (lambda (a b) (> (obj-size a) (obj-size b))))))
          (k (obj-size largest))
          (color (nth header (modulo (- k 1) (length header)))))
     (paint-cells (empty-grid (rows g) (cols g) 0) (obj-cells largest) color))))"""

WRONG_SMALLEST_PROGRAM = """(rule!
 (lambda (g)
   (let* ((header (filter (lambda (v) (!= v 0)) (first g)))
          (targets (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0)))
          (smallest (first (sort targets (lambda (a b) (< (obj-size a) (obj-size b))))))
          (k (obj-size smallest))
          (color (nth header (modulo (- k 1) (length header)))))
     (paint-cells (empty-grid (rows g) (cols g) 0) (obj-cells smallest) color))))"""

# (height, width, body component sizes). Sizes are unique in every scene.
_DEMO_SPECS = (
    (14, 18, (2, 4, 1, 3)),
    (15, 19, (3, 2, 5, 1)),
    (16, 20, (4, 1, 3, 6)),
    (18, 22, (7, 2, 5, 3)),
    (20, 24, (4, 8, 2, 6)),
    (22, 26, (5, 3, 9, 7)),
)
_QUERY_SPECS = (
    (15, 18, (2, 6, 4, 3)),
    (19, 22, (8, 3, 5, 6)),
    (24, 26, (2, 5, 7, 4)),
    (30, 30, (11, 9, 8, 7, 6, 5, 4, 3)),
)
_SLOTS4 = ("tl", "tr", "bl", "br")
_SLOTS8 = ("tl", "tc", "tr", "ml", "mc", "mr", "bl", "br")


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"selection_mode"}:
        raise ValueError("settings must contain exactly selection_mode")
    mode = settings["selection_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"selection_mode must be one of {MODES}")
    return {"selection_mode": mode}


def rule_text(mode: str) -> str:
    if mode == "first_header_all":
        return CANONICAL_PROGRAM
    if mode == "largest_component_indexed_header":
        return RELAY_PROGRAM
    raise ValueError(f"unknown selection_mode {mode!r}")


def counterfactual_program() -> str:
    return WRONG_SMALLEST_PROGRAM


def _mix(*parts: object) -> int:
    raw = ":".join(map(str, (TASK_ID, "largest-component-relay-v1", *parts)))
    return int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape(size: int, variant: int):
    if type(size) is not int or not 1 <= size <= 15:
        raise ValueError("component size must be in 1..15")
    width = min(4, max(2, (size + 2) // 3))
    cells = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    if variant & 1:
        cells = [(r, -c) for r, c in cells]
    for _ in range((variant >> 1) % 4):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _slot_position(slot: str, height: int, width: int, shape):
    sh = 1 + max(r for r, _ in shape)
    sw = 1 + max(c for _, c in shape)
    if sh > 5 or sw > 5:
        raise ValueError("component shape exceeds slot budget")
    middle_top = max(3, (height - sh) // 2)
    top = {
        "tl": 2, "tc": 2, "tr": 2,
        "ml": middle_top, "mc": middle_top, "mr": middle_top,
        "bl": height - sh, "br": height - sh,
    }[slot]
    left = {
        "tl": 0, "ml": 0, "bl": 0,
        "tc": (width - sw) // 2, "mc": (width - sw) // 2,
        "tr": width - sw, "mr": width - sw, "br": width - sw,
    }[slot]
    return top, left


def _blue_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r > 0 and value == 1
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        components.append(tuple(sorted(cells)))
    return sorted(components, key=min)


def analyze(grid) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    header = [value for value in grid[0] if value != 0]
    if len(header) != 3 or len(set(header)) != 3 or 1 in header:
        raise ValueError("family requires three distinct non-blue header markers")
    components = _blue_components(grid)
    if len(components) < 2:
        raise ValueError("family requires at least two blue body components")
    sizes = [len(component) for component in components]
    if len(set(sizes)) != len(sizes):
        raise ValueError("component sizes must be unique")
    largest_index = max(range(len(components)), key=lambda i: sizes[i])
    smallest_index = min(range(len(components)), key=lambda i: sizes[i])
    largest = components[largest_index]
    smallest = components[smallest_index]
    selected_header_index = (len(largest) - 1) % len(header)
    return {
        "header_colors": header,
        "component_sizes": sizes,
        "components": components,
        "largest_index": largest_index,
        "largest_size": len(largest),
        "largest_cells": list(largest),
        "smallest_index": smallest_index,
        "smallest_size": len(smallest),
        "smallest_cells": list(smallest),
        "selected_header_index": selected_header_index,
        "selected_header_color": header[selected_header_index],
    }


def _empty_like(grid):
    return [[0 for _ in row] for row in grid]


def apply_mode(grid, mode: str):
    info = analyze(grid)
    out = _empty_like(grid)
    if mode == "first_header_all":
        color = info["header_colors"][0]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if r > 0 and value == 1:
                    out[r][c] = color
        return out
    if mode == "largest_component_indexed_header":
        for r, c in info["largest_cells"]:
            out[r][c] = info["selected_header_color"]
        return out
    raise ValueError(f"unknown selection_mode {mode!r}")


def apply_wrong_smallest(grid):
    info = analyze(grid)
    color = info["header_colors"][(info["smallest_size"] - 1) % 3]
    out = _empty_like(grid)
    for r, c in info["smallest_cells"]:
        out[r][c] = color
    return out


def _header_colors(seed: int, split: str, index: int):
    palette = list(range(2, 10))
    offset = _mix(seed, split, index, "header") % len(palette)
    step = 3 if (_mix(seed, split, index, "step") & 1) else 5
    colors = []
    pos = offset
    while len(colors) < 3:
        color = palette[pos % len(palette)]
        if color not in colors:
            colors.append(color)
        pos += step
    return colors


def _build_input(seed: int, split: str, index: int, spec):
    height, width, sizes = spec
    slots = _SLOTS4 if len(sizes) == 4 else _SLOTS8
    if len(slots) != len(sizes):
        raise ValueError("unsupported component count")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col, color in zip((0, width // 2, width - 1), _header_colors(seed, split, index)):
        grid[0][col] = color
    occupied = set()
    for component_index, (size, slot) in enumerate(zip(sizes, slots)):
        shape = _shape(size, _mix(seed, split, index, component_index, "shape"))
        top, left = _slot_position(slot, height, width, shape)
        cells = {(top + r, left + c) for r, c in shape}
        if occupied & cells:
            raise ValueError("component overlap")
        if any(
            (r + dr, c + dc) in occupied
            for r, c in cells
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            raise ValueError("components became adjacent")
        occupied |= cells
        for r, c in cells:
            grid[r][c] = 1
    info = analyze(grid)
    if sorted(info["component_sizes"]) != sorted(sizes):
        raise ValueError(f"constructed sizes differ: {info['component_sizes']} vs {list(sizes)}")
    return grid


def _pair(seed: int, split: str, index: int, spec, mode: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, selection_mode: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if selection_mode not in MODES:
        raise ValueError(f"unknown selection_mode {selection_mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [
        _pair(seed, "train", index, _DEMO_SPECS[index], selection_mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "test", index, _QUERY_SPECS[index], selection_mode)
        for index in range(queries)
    ]
    return {"train": train, "test": test, "program_solution": rule_text(selection_mode)}


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return (
        json.dumps(
            public_turn(episode, query_index),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def public_id(episode: dict[str, Any], query_index: int) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    pair = generate_episode(
        seed,
        selection_mode="largest_component_indexed_header",
        demos=3,
        queries=4,
    )["test"][0]
    info = analyze(pair["input"])
    return {
        "settings": {"selection_mode": "largest_component_indexed_header"},
        "input": deepcopy(pair["input"]),
        "program": RELAY_PROGRAM,
        "output": deepcopy(pair["output"]),
        "counterfactual_program": WRONG_SMALLEST_PROGRAM,
        "counterfactual_output": apply_wrong_smallest(pair["input"]),
        "intermediate_value": {
            "header_colors": info["header_colors"],
            "largest_size": info["largest_size"],
            "largest_cells": info["largest_cells"],
            "selected_header_index": info["selected_header_index"],
            "smallest_size": info["smallest_size"],
            "smallest_cells": info["smallest_cells"],
            "wrong_header_index": (info["smallest_size"] - 1) % 3,
        },
        "ablation": "wrong_intermediate",
    }
