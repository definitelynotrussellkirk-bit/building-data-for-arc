"""Spatial-vs-largest-first object packing for ARC task e68b376152cd.

The canonical setting is byte-for-byte the selected ARC rule.  Both settings
share deterministic inputs.  Step A extracts tight object crops and orders them
from the input; step B center-packs that ordered intermediate with one blank
column.  The alternate setting changes only the ordering computation.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import find_root, load_selected_generator

TASK_ID = "e68b376152cd"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
POLICIES = ("spatial", "largest_first")
DEFAULT_POLICY = "spatial"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
Grid = list[list[int]]

# Connected, non-rectangular masks.  The stress five sum to 70 occupied cells.
_MASKS: dict[str, tuple[str, ...]] = {
    "a3": ("##", "#."),
    "a4": ("###", ".#."),
    "a5": (".#.", "###", ".#."),
    "a6": ("##.", "###", "..#"),
    "a7": ("###", "#..", "###"),
    "a8": ("####", "#..#", "##.."),
    "a9": ("###", "###", "##.", "#.."),
    "a10": ("####", "#..#", "####"),
    "a11": ("####", "###.", "##..", "##.."),
    "a12": ("#####", "#...#", "#####"),
    "a14": ("#####", "##.##", "#####"),
    "a16": ("#####", "#####", "###..", "###.."),
    "a18": ("####", "##.#", "####", "#..#", "####", "..#."),
}

# Six prefix-stable demonstrations followed by four query-bank scenes.
_PROFILES: tuple[dict[str, Any], ...] = (
    {"size": (12, 14), "masks": ("a4", "a9", "a5")},
    {"size": (14, 18), "masks": ("a6", "a3", "a8", "a5")},
    {"size": (16, 20), "masks": ("a7", "a10", "a4", "a9", "a6")},
    {"size": (18, 22), "masks": ("a5", "a11", "a7", "a3")},
    {"size": (20, 24), "masks": ("a12", "a6", "a10", "a4", "a8")},
    {"size": (24, 28), "masks": ("a9", "a14", "a5", "a12", "a7")},
    {"size": (10, 12), "masks": ("a5", "a3", "a4")},
    {"size": (22, 26), "masks": ("a10", "a6", "a12", "a8")},
    {"size": (27, 29), "masks": ("a14", "a9", "a16", "a10", "a12")},
    {"size": (30, 30), "masks": ("a10", "a18", "a12", "a16", "a14")},
)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _setting(settings: dict[str, Any]) -> str:
    if (type(settings) is not dict or set(settings) != {"order_policy"}
            or settings["order_policy"] not in POLICIES):
        raise ValueError("Exactly order_policy=spatial|largest_first is required")
    return settings["order_policy"]


def _integer(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def program(settings: dict[str, Any]) -> str:
    policy = _setting(settings)
    return (HERE / ("canonical.rkt" if policy == "spatial" else "largest_first.rkt")).read_text(encoding="utf-8")


def selected_generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _validate_grid(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC color integers")
    return len(grid), width


def components(grid: Grid) -> list[dict[str, Any]]:
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append({"color": color, "cells": tuple(cells),
                           "bbox": (min(rows), min(cols), max(rows), max(cols)),
                           "area": len(cells)})
    return result


def _ordered(records: Iterable[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    if policy == "spatial":
        return sorted(records, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    return sorted(records, key=lambda obj: (-obj["area"], obj["bbox"][1], obj["bbox"][0]))


def _crop(record: dict[str, Any]) -> Grid:
    r0, c0, r1, c1 = record["bbox"]
    piece = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for row, col in record["cells"]:
        piece[row - r0][col - c0] = record["color"]
    return piece


def intermediate(grid: Grid, settings: dict[str, Any]) -> dict[str, Any]:
    policy = _setting(settings)
    records = _ordered(components(grid), policy)
    if len(records) < 2:
        raise ValueError("packing grammar requires at least two objects")
    pieces = [_crop(record) for record in records]
    return {"order_policy": policy,
            "ordered_colors": [record["color"] for record in records],
            "ordered_areas": [record["area"] for record in records],
            "ordered_bboxes": [list(record["bbox"]) for record in records],
            "pieces": pieces}


def pack_intermediate(stage: dict[str, Any], *, gap: int = 1, align: str = "center",
                      fill_bbox: bool = False) -> Grid:
    pieces = deepcopy(stage["pieces"])
    if fill_bbox:
        pieces = [[[next(value for row in piece for value in row if value)] * len(piece[0])
                   for _ in piece] for piece in pieces]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + gap * (len(pieces) - 1)
    output = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        if align == "top":
            top = 0
        elif align == "bottom":
            top = height - len(piece)
        elif align == "center":
            top = (height - len(piece)) // 2
        else:
            raise ValueError("unknown alignment")
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    output[top + r][left + c] = value
        left += len(piece[0]) + gap
    return output


def predict(grid: Grid, policy_or_settings: str | dict[str, Any]) -> Grid:
    settings = ({"order_policy": policy_or_settings}
                if isinstance(policy_or_settings, str) else policy_or_settings)
    return pack_intermediate(intermediate(grid, settings))


def _mask_cells(name: str, transform: int) -> tuple[tuple[int, int], ...]:
    rows = [list(row) for row in _MASKS[name]]
    if transform & 1:
        rows = [list(reversed(row)) for row in rows]
    if transform & 2:
        rows = list(reversed(rows))
    return tuple((r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == "#")


def _columns(width: int, piece_widths: list[int]) -> list[int]:
    required = sum(piece_widths) + len(piece_widths) - 1
    if required > width:
        raise ValueError("profile cannot fit its objects")
    extra = width - required
    gaps = [1] * (len(piece_widths) - 1)
    for index in range(extra):
        if gaps:
            gaps[index % len(gaps)] += 1
    result = [0]
    for pw, gap in zip(piece_widths, gaps):
        result.append(result[-1] + pw + gap)
    return result


def _scene(seed: int, index: int) -> Grid:
    profile = _PROFILES[index]
    h, w = profile["size"]
    names = profile["masks"]
    rng = _rng(seed, f"scene:{index}")
    transforms = [rng.randrange(4) for _ in names]
    cells = [_mask_cells(name, transform) for name, transform in zip(names, transforms)]
    dims = [(1 + max(r for r, _ in shape), 1 + max(c for _, c in shape)) for shape in cells]
    columns = _columns(w, [pw for _, pw in dims])
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], len(names))
    # Alternating boundary/center rows make top-order and simple scan-order rivals fail.
    row_modes = (0, 4, 2, 1, 3)
    rows: list[int] = []
    for slot, (ph, _) in enumerate(dims):
        mode = row_modes[(slot + index) % len(row_modes)]
        candidates = (0, 1, max(0, (h - ph) // 2), max(0, h - ph - 1), h - ph)
        rows.append(candidates[mode])
    grid = [[0] * w for _ in range(h)]
    for color, shape, top, left in zip(palette, cells, rows, columns):
        for r, c in shape:
            if grid[top + r][left + c] != 0:
                raise ValueError("constructive objects overlap")
            grid[top + r][left + c] = color
    if predict(grid, "spatial") == predict(grid, "largest_first"):
        raise ValueError("profile failed to distinguish the declared settings")
    return grid


@lru_cache(maxsize=32)
def _bank(seed: int) -> tuple[Grid, ...]:
    return tuple(_scene(seed, index) for index in range(len(_PROFILES)))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    policy = _setting(settings)
    _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    scenes = _bank(seed)
    order = list(range(6, 10))
    _rng(seed, "presentation").shuffle(order)
    train_indices = list(range(demos))
    test_indices = order[:queries]
    chosen = [scenes[index] for index in train_indices + test_indices]
    if len({json.dumps(grid, separators=(",", ":")) for grid in chosen}) != len(chosen):
        raise ValueError("episode inputs must be distinct")
    def pair(index: int) -> dict[str, Grid]:
        grid = scenes[index]
        return {"input": grid, "output": predict(grid, policy)}
    return deepcopy({"train": [pair(i) for i in train_indices],
                     "test": [pair(i) for i in test_indices],
                     "program_solution": program(settings)})


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return deepcopy({"train": [{"input": p["input"], "output": p["output"]}
                                for p in episode["train"]],
                     "test": [{"input": episode["test"][query_index]["input"]}]})


def describe_scene(grid: Grid) -> dict[str, Any]:
    records = components(grid)
    pieces = [_crop(record) for record in records]
    return {"object_count": len(records),
            "areas": sorted(record["area"] for record in records),
            "max_bbox_height": max(len(piece) for piece in pieces),
            "max_bbox_width": max(len(piece[0]) for piece in pieces),
            "packed_width": sum(len(piece[0]) for piece in pieces) + len(pieces) - 1,
            "occupied": sum(record["area"] for record in records)}


def rival_predictions(grid: Grid, intended: str) -> dict[str, Grid]:
    records = components(grid)
    variants: dict[str, tuple[list[dict[str, Any]], int, str, bool]] = {
        "opposite_setting": (_ordered(records, "largest_first" if intended == "spatial" else "spatial"), 1, "center", False),
        "reverse_spatial": (list(reversed(_ordered(records, "spatial"))), 1, "center", False),
        "smallest_first": (sorted(records, key=lambda o: (o["area"], o["bbox"][1], o["bbox"][0])), 1, "center", False),
        "color_ascending": (sorted(records, key=lambda o: o["color"]), 1, "center", False),
        "color_descending": (sorted(records, key=lambda o: -o["color"]), 1, "center", False),
        "top_then_left": (sorted(records, key=lambda o: (o["bbox"][0], o["bbox"][1])), 1, "center", False),
        "top_aligned": (_ordered(records, intended), 1, "top", False),
        "bottom_aligned": (_ordered(records, intended), 1, "bottom", False),
        "filled_bboxes": (_ordered(records, intended), 1, "center", True),
        "zero_gap": (_ordered(records, intended), 0, "center", False),
        "two_gap": (_ordered(records, intended), 2, "center", False),
    }
    result = {}
    for name, (ordered, gap, align, filled) in variants.items():
        stage = {"pieces": [_crop(record) for record in ordered]}
        result[name] = pack_intermediate(stage, gap=gap, align=align, fill_bbox=filled)
    return result
