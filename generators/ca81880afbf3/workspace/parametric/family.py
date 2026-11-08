"""Matched-input square-hole relay family for ``ca81880afbf3``.

The exact canonical setting fills every square-shaped zero pocket enclosed by a
color-5 component with color 2.  The alternate first performs that same step,
then derives the connected color-2 components and bridges aligned components of
equal area with color 4.  The bridge stage therefore consumes an input-dependent
intermediate produced by the canonical stage.
"""
from __future__ import annotations

import copy
import hashlib
import random
from typing import Any, Iterable

TASK_ID = "ca81880afbf3"
SETTINGS = ("fill_only", "bridge_equal_area")
DEFAULT = "fill_only"

# Rectangles are (top, left, height, width).  Square frames use odd interior
# side lengths, giving a unique integer center after the canonical fill.
DEMO_TEMPLATES = (
    (14, 20, ((2, 2, 3, 3), (2, 15, 3, 3), (7, 2, 5, 5), (8, 12, 4, 6))),
    (18, 18, ((2, 2, 3, 3), (13, 2, 3, 3), (2, 11, 5, 5), (11, 10, 4, 6))),
    (18, 24, ((2, 2, 5, 5), (2, 17, 5, 5), (12, 2, 3, 3), (11, 14, 4, 7))),
    (22, 20, ((2, 2, 5, 5), (15, 2, 5, 5), (2, 15, 3, 3), (14, 11, 5, 7))),
    (24, 27, ((2, 2, 7, 7), (2, 18, 7, 7), (18, 2, 3, 3), (17, 16, 5, 8))),
    (27, 24, ((2, 2, 7, 7), (18, 2, 7, 7), (2, 19, 3, 3), (19, 14, 5, 8))),
)
QUERY_TEMPLATES = (
    (16, 22, ((2, 3, 3, 3), (11, 3, 3, 3), (2, 14, 5, 5), (10, 13, 4, 7))),
    (20, 27, ((2, 2, 5, 5), (2, 20, 5, 5), (15, 2, 3, 3), (13, 17, 5, 8))),
    (26, 30, ((2, 2, 7, 7), (17, 2, 7, 7), (2, 25, 3, 3), (18, 18, 6, 9))),
    (30, 30, (
        (2, 2, 5, 5), (2, 23, 5, 5),
        (10, 14, 3, 3), (25, 14, 3, 3),
        (20, 2, 7, 7), (16, 20, 4, 8),
    )),
)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("finish_rule must be fill_only or bridge_equal_area")
    return value


def grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return value


def _components(data: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(data), len(data[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if data[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = [start]
        while queue:
            r, c = queue.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    component.add((nr, nc))
                    queue.append((nr, nc))
        result.append(component)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    items = list(cells)
    return (
        min(r for r, _ in items), min(c for _, c in items),
        max(r for r, _ in items), max(c for _, c in items),
    )


def _square_zero_cells(data: list[list[int]], component: set[tuple[int, int]]) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = _bbox(component)
    zeros = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if data[r][c] == 0
    ]
    if not zeros:
        return []
    zr1, zc1, zr2, zc2 = _bbox(zeros)
    height, width = zr2 - zr1 + 1, zc2 - zc1 + 1
    if height != width or len(zeros) != height * width:
        return []
    return zeros


def _fill_square_holes(value: object) -> tuple[list[list[int]], list[dict[str, Any]], int]:
    data = grid(value)
    filled = copy.deepcopy(data)
    square_rows: list[dict[str, Any]] = []
    nonsquare = 0
    for component in _components(data, 5):
        zeros = _square_zero_cells(data, component)
        if zeros:
            for r, c in zeros:
                filled[r][c] = 2
            square_rows.append({
                "frame_bbox": list(_bbox(component)),
                "fill_cells": zeros,
                "fill_area": len(zeros),
            })
        else:
            nonsquare += 1
    return filled, square_rows, nonsquare


def _derived_parts(filled: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for component in _components(filled, 2):
        r1, c1, r2, c2 = _bbox(component)
        result.append({
            "cells": component,
            "area": len(component),
            "bbox": (r1, c1, r2, c2),
            "center": ((r1 + r2) // 2, (c1 + c2) // 2),
        })
    return sorted(result, key=lambda row: (row["center"], row["area"]))


def _line_cells(first: tuple[int, int], second: tuple[int, int]) -> list[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    if r1 == r2:
        return [(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)]
    if c1 == c2:
        return [(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)]
    return []


def _relay_pairs(parts: list[dict[str, Any]], *, shift_columns: int = 0) -> list[dict[str, Any]]:
    result = []
    for index, first in enumerate(parts):
        for second in parts[index + 1:]:
            if first["area"] != second["area"]:
                continue
            p = (first["center"][0], first["center"][1] + shift_columns)
            q = (second["center"][0], second["center"][1] + shift_columns)
            cells = _line_cells(p, q)
            if cells:
                result.append({"area": first["area"], "first": p, "second": q, "cells": cells})
    return result


def _paint_relays(filled: list[list[int]], pairs: list[dict[str, Any]]) -> list[list[int]]:
    out = copy.deepcopy(filled)
    h, w = len(out), len(out[0])
    for pair in pairs:
        for r, c in pair["cells"]:
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 4
    return out


def _analyze(value: object) -> dict[str, Any]:
    filled, square_rows, nonsquare = _fill_square_holes(value)
    parts = _derived_parts(filled)
    pairs = _relay_pairs(parts)
    if len(parts) != len(square_rows):
        raise ValueError("each square fill must form one derived color-2 component")
    if len(parts) < 3 or nonsquare < 1 or not pairs:
        raise ValueError("scene must contain at least three square fills, one distractor, and one relay")
    bridged = _paint_relays(filled, pairs)
    return {
        "filled": filled,
        "square_rows": square_rows,
        "nonsquare": nonsquare,
        "parts": parts,
        "pairs": pairs,
        "bridged": bridged,
    }


def intermediate(value: object) -> dict[str, Any]:
    info = _analyze(value)
    return {
        "square_components": len(info["parts"]),
        "nonsquare_components": info["nonsquare"],
        "derived_fill_cells": sum(part["area"] for part in info["parts"]),
        "derived_components": [
            {"area": part["area"], "center": list(part["center"]), "bbox": list(part["bbox"])}
            for part in info["parts"]
        ],
        "relay_pairs": len(info["pairs"]),
        "relay_descriptors": [
            {"area": pair["area"], "first": list(pair["first"]), "second": list(pair["second"])}
            for pair in info["pairs"]
        ],
        "bridge_cells": sum(cell == 4 for row in info["bridged"] for cell in row),
    }


def solve(value: object, mode: str) -> list[list[int]]:
    selected = setting(mode)
    info = _analyze(value)
    return copy.deepcopy(info["filled"] if selected == "fill_only" else info["bridged"])


def solve_wrong_shifted_centers(value: object) -> list[list[int]]:
    """Counterfactual: preserve square fills but shift every derived center right."""
    info = _analyze(value)
    return _paint_relays(info["filled"], _relay_pairs(info["parts"], shift_columns=1))


def _draw_outline(data: list[list[int]], rect: tuple[int, int, int, int]) -> None:
    top, left, height, width = rect
    bottom, right = top + height - 1, left + width - 1
    for c in range(left, right + 1):
        data[top][c] = 5
        data[bottom][c] = 5
    for r in range(top, bottom + 1):
        data[r][left] = 5
        data[r][right] = 5


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:equal-area-relay-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    templates = DEMO_TEMPLATES if split == "demo" else QUERY_TEMPLATES
    height, width, rectangles = templates[index]
    data = [[0 for _ in range(width)] for _ in range(height)]
    for rect in rectangles:
        _draw_outline(data, rect)

    # Add two seed-dependent isolated color-5 distractors outside every frame
    # and outside all intended relay lines.  They vary episodes without changing
    # either rule and exercise the canonical empty-interior branch.
    preliminary = _analyze(data)
    relay_cells = {cell for pair in preliminary["pairs"] for cell in pair["cells"]}
    boxed = set()
    for top, left, rect_h, rect_w in rectangles:
        boxed.update((r, c) for r in range(top, top + rect_h) for c in range(left, left + rect_w))
    rng = _rng(seed, split, index)
    candidates = []
    occupied = {(r, c) for r in range(height) for c in range(width) if data[r][c] != 0}
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if (r, c) in boxed or (r, c) in relay_cells or data[r][c] != 0:
                continue
            if any((r + dr, c + dc) in occupied for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
                continue
            candidates.append((r, c))
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    for candidate in candidates:
        if any(max(abs(candidate[0] - r), abs(candidate[1] - c)) <= 1 for r, c in selected):
            continue
        selected.append(candidate)
        data[candidate[0]][candidate[1]] = 5
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise RuntimeError("failed to place isolated distractors")
    _analyze(data)
    return data


def generate(seed: object, mode: object, demos: object, queries: object) -> dict[str, Any]:
    actual_seed = integer(seed, 0, 2**63 - 1, "seed")
    selected = setting(mode)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demo_count):
        input_grid = _scene(actual_seed, "demo", index)
        train.append({"input": input_grid, "output": solve(input_grid, selected)})
    for index in range(query_count):
        input_grid = _scene(actual_seed, "query", index)
        test.append({"input": input_grid, "output": solve(input_grid, selected)})
    return {"train": train, "test": test}
