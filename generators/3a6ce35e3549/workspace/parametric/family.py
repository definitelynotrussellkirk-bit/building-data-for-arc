"""Matched-input interior-mask family for ``3a6ce35e3549``.

The four minority-color corner markers first determine an input-dependent
rectangle.  The episode-fixed setting then projects either the majority-color
blob cells (the exact canonical default) or the complementary gaps from that
rectangle's strict interior, recoloring selected cells with the marker color.
"""
from __future__ import annotations

import copy
import hashlib
import random
from typing import Any

TASK_ID = "3a6ce35e3549"
SETTINGS = ("blob", "gaps")
DEFAULT = "blob"
RIVALS = ("opposite_mask", "inclusive_rectangle", "fixed_origin", "paint_all", "preserve_source_color")

# (grid_h, grid_w, top, left, rect_h, rect_w, texture)
DEMO_SPECS = (
    (9, 11, 1, 2, 6, 7, "checker"),
    (12, 14, 3, 1, 7, 9, "bands"),
    (16, 13, 2, 4, 11, 7, "diagonal"),
    (20, 21, 1, 5, 16, 12, "rings"),
    (25, 19, 4, 1, 18, 16, "noise"),
    (30, 30, 0, 0, 30, 30, "mixed"),
)
QUERY_SPECS = (
    (10, 13, 2, 3, 7, 8, "stair"),
    (18, 16, 1, 2, 15, 11, "checker"),
    (24, 27, 3, 1, 20, 24, "noise"),
    (30, 30, 0, 0, 30, 30, "mixed"),
)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("mask must be blob or gaps")
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


def _analyze(value: object) -> dict[str, Any]:
    data = grid(value)
    counts: dict[int, int] = {}
    for row in data:
        for cell in row:
            if cell:
                counts[cell] = counts.get(cell, 0) + 1
    if len(counts) != 2:
        raise ValueError("expected exactly two nonzero colors")
    ordered = sorted(counts, key=lambda color: (counts[color], color))
    dot, big = ordered[0], ordered[1]
    if counts[dot] != 4 or counts[big] <= counts[dot]:
        raise ValueError("minority marker must have four cells and blob must be larger")
    dots = [(r, c) for r, row in enumerate(data) for c, cell in enumerate(row) if cell == dot]
    r1, r2 = min(r for r, _ in dots), max(r for r, _ in dots)
    c1, c2 = min(c for _, c in dots), max(c for _, c in dots)
    expected = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
    if set(dots) != expected or r2 - r1 < 3 or c2 - c1 < 3:
        raise ValueError("marker cells must be the four corners of a nontrivial rectangle")
    interior = [row[c1 + 1:c2] for row in data[r1 + 1:r2]]
    if not any(cell == big for row in interior for cell in row):
        raise ValueError("rectangle interior must contain blob cells")
    if not any(cell == 0 for row in interior for cell in row):
        raise ValueError("rectangle interior must contain gaps")
    return {
        "data": data,
        "dot": dot,
        "big": big,
        "dot_count": counts[dot],
        "big_count": counts[big],
        "bounds": (r1, c1, r2, c2),
        "interior": interior,
    }


def intermediate(value: object) -> dict[str, Any]:
    info = _analyze(value)
    r1, c1, r2, c2 = info["bounds"]
    interior = info["interior"]
    return {
        "dot_color": info["dot"],
        "big_color": info["big"],
        "dot_count": info["dot_count"],
        "big_count": info["big_count"],
        "marker_bounds": [r1, c1, r2, c2],
        "interior_height": len(interior),
        "interior_width": len(interior[0]),
        "blob_cells_interior": sum(cell == info["big"] for row in interior for cell in row),
        "gap_cells_interior": sum(cell == 0 for row in interior for cell in row),
    }


def solve(value: object, mask: str) -> list[list[int]]:
    mode = setting(mask)
    info = _analyze(value)
    selected = info["big"] if mode == "blob" else 0
    return [
        [info["dot"] if cell == selected else 0 for cell in row]
        for row in info["interior"]
    ]


def solve_rival(value: object, mask: str, rival: str) -> list[list[int]]:
    """A bounded set of plausible shortcut hypotheses for self-review."""
    mode = setting(mask)
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    info = _analyze(value)
    data = info["data"]
    r1, c1, r2, c2 = info["bounds"]
    selected = info["big"] if mode == "blob" else 0
    if rival == "opposite_mask":
        return solve(data, "gaps" if mode == "blob" else "blob")
    if rival == "inclusive_rectangle":
        return [[info["dot"] if data[r][c] == selected else 0
                 for c in range(c1, c2 + 1)]
                for r in range(r1, r2 + 1)]
    if rival == "fixed_origin":
        height, width = r2 - r1 - 1, c2 - c1 - 1
        return [[info["dot"] if data[r][c] == selected else 0
                 for c in range(width)] for r in range(height)]
    if rival == "paint_all":
        return [[info["dot"] for _ in row] for row in info["interior"]]
    # Preserve the source majority color instead of recoloring by the markers.
    return [[info["big"] if cell == selected else 0 for cell in row]
            for row in info["interior"]]


def solve_wrong_shifted_bounds(value: object, mask: str) -> list[list[int]]:
    """Counterfactual: use the same size but shift the inferred crop down/right."""
    mode = setting(mask)
    info = _analyze(value)
    data = info["data"]
    r1, c1, r2, c2 = info["bounds"]
    selected = info["big"] if mode == "blob" else 0
    return [
        [info["dot"] if data[r1 + 2 + r][c1 + 2 + c] == selected else 0
         for c in range(c2 - c1 - 1)]
        for r in range(r2 - r1 - 1)
    ]


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:interior-mask-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _texture_cells(height: int, width: int, texture: str, rng: random.Random) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for r in range(height):
        for c in range(width):
            if texture == "checker":
                keep = (r + c + rng.randrange(2)) % 3 != 0
            elif texture == "bands":
                keep = (r % 4 in (0, 1)) ^ (c % 5 == 0)
            elif texture == "diagonal":
                keep = ((2 * r + c) % 5 in (0, 1)) or (r == c % height)
            elif texture == "rings":
                distance = min(r, c, height - 1 - r, width - 1 - c)
                keep = distance % 3 != 1
            elif texture == "stair":
                keep = c <= (2 * r + 2) % max(1, width) or (r + c) % 5 == 0
            elif texture == "noise":
                keep = rng.random() < 0.47
            else:  # mixed
                keep = ((r + 2 * c) % 7 in (0, 1, 3)) ^ (rng.random() < 0.18)
            if keep:
                cells.add((r, c))
    # Make both masks substantive and make the crop boundary matter.
    anchors = {
        (0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1),
        (height // 2, width // 2),
    }
    cells.update(anchors)
    for p in ((0, width // 2), (height - 1, width // 2),
              (height // 2, 0), (height // 2, width - 1)):
        cells.add(p)
    # Preserve deterministic holes, including near the top-left so shifted-bounds
    # ablations disagree even on highly regular textures.
    for p in ((0, 1), (1, 0), (1, 1), (height // 2, max(0, width // 2 - 1))):
        cells.discard(p)
    all_cells = {(r, c) for r in range(height) for c in range(width)}
    if len(cells) < 5:
        cells.update(sorted(all_cells)[:5])
    if len(cells) >= len(all_cells):
        cells.discard((height - 1, max(0, width - 2)))
    return cells


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    specs = DEMO_SPECS if split == "train" else QUERY_SPECS
    h, w, top, left, rh, rw, texture = specs[index]
    rng = _rng(seed, split, index)
    big, dot = rng.sample(range(1, 10), 2)
    data = [[0] * w for _ in range(h)]
    corners = ((top, left), (top, left + rw - 1),
               (top + rh - 1, left), (top + rh - 1, left + rw - 1))
    for r, c in corners:
        data[r][c] = dot
    interior_h, interior_w = rh - 2, rw - 2
    for r, c in _texture_cells(interior_h, interior_w, texture, rng):
        data[top + 1 + r][left + 1 + c] = big
    # Validate every authored input against the exact semantic assumptions.
    _analyze(data)
    return data


def generate(seed: object, mask: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = integer(seed, 0, 2**63 - 1, "seed")
    mode = setting(mask)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    for index in range(demo_count):
        data = _draw(seed_i, "train", index)
        train.append({"input": data, "output": solve(data, mode)})
    test = []
    for index in range(query_count):
        data = _draw(seed_i, "test", index)
        test.append({"input": data, "output": solve(data, mode)})
    return {
        "train": train,
        "test": test,
        "private_query_bank": copy.deepcopy(test),
    }
