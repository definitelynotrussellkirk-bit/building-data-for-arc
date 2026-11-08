"""Native parametric family for left-to-right versus area-descending packing."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from collections import deque
from pathlib import Path


HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ORDERS = ("left_to_right", "area_descending")
_DEMO_INDICES = (1, 2, 3, 5, 6, 7)
_QUERY_INDICES = (9, 10, 11)


def _load_generator():
    path = HOME / "generator.py"
    name = "_gallery_base_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_generator()


def _settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {"object_order"}:
        raise ValueError("settings must contain exactly object_order")
    order = settings["object_order"]
    if type(order) is not str or order not in ORDERS:
        raise ValueError(f"object_order must be one of {ORDERS}")
    return order


def _seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _count(name: str, value, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def program(settings) -> str:
    order = _settings(settings)
    name = "canonical.rkt" if order == "left_to_right" else "area_descending.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _large_scene(seed: int) -> list[list[int]]:
    rng = random.Random((seed ^ 0xE68B376152CD) & ((1 << 64) - 1))
    colors = rng.sample(range(1, 10), 5)
    grid = [[0] * 30 for _ in range(30)]
    rectangles = (
        (1, 0, 4, 2),    # 4x3 = 12
        (20, 5, 25, 9),  # 6x5 = 30
        (8, 12, 12, 15), # 5x4 = 20
        (24, 18, 28, 22),# 5x5 = 25
        (1, 26, 7, 29),  # 7x4 = 28
    )
    for color, (r0, c0, r1, c1) in zip(colors, rectangles):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = color
    return grid


def sample_inputs(seed: int, demos: int = 3, queries: int = 4):
    seed = _seed(seed)
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_bank = [
        _BASE.generate(seed, index, difficulty="medium" if pos % 2 else None)
        for pos, index in enumerate(_DEMO_INDICES)
    ]
    query_bank = [
        _BASE.generate(seed ^ 0x2468ACE0, index, difficulty="medium" if pos % 2 else None)
        for pos, index in enumerate(_QUERY_INDICES)
    ] + [_large_scene(seed)]
    selected = demo_bank[:demos] + query_bank[:queries]
    if len({json.dumps(grid, separators=(",", ":")) for grid in selected}) != len(selected):
        raise RuntimeError("input sampler produced a duplicate visible grid")
    return copy.deepcopy(demo_bank[:demos]), copy.deepcopy(query_bank[:queries])


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            records.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "area": len(cells),
            })
    return records


def _crop(record: dict[str, object]) -> list[list[int]]:
    r0, c0, r1, c1 = record["bbox"]  # type: ignore[misc]
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in record["cells"]:  # type: ignore[assignment]
        out[r - r0][c - c0] = int(record["color"])
    return out


def _pack(records: list[dict[str, object]]) -> list[list[int]]:
    pieces = [_crop(record) for record in records]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _label(grid: list[list[int]], order: str) -> list[list[int]]:
    records = _components(grid)
    if order == "left_to_right":
        records.sort(key=lambda record: (record["bbox"][1], record["bbox"][0]))  # type: ignore[index]
    else:
        records.sort(key=lambda record: (-int(record["area"]), record["bbox"][1], record["bbox"][0]))  # type: ignore[index]
    return _pack(records)


def generate(seed, settings, demos=3, queries=4):
    order = _settings(settings)
    train_inputs, test_inputs = sample_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [{"input": grid, "output": _label(grid, order)} for grid in train_inputs],
        "test": [{"input": grid, "output": _label(grid, order)} for grid in test_inputs],
        "program_solution": program(settings),
    }
