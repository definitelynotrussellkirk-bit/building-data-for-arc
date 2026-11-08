"""Native parametric family for 677dcb71e2be.

The canonical setting preserves the selected Racket source byte-for-byte.  The
alternate setting first finds the unique border-touching component, uses its
occupied-cell count modulo the component count as an input-dependent rotation,
then packs the canonical size-sorted bars in that rotated order.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


HOME = Path(__file__).resolve().parent
MODES = ("size_desc", "border_shift")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each size has a compact and an expanded connected shape.  Expanded selector
# shapes make occupied-cell count observably different from bounding-box area.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (((0, 0), (0, 1), (1, 0)), ((0, 0), (1, 0), (2, 0))),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (3, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (3, 1), (3, 2)),
    ),
    9: (
        tuple((r, c) for r in range(3) for c in range(3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
    ),
    10: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2)),
    ),
}

_DEMO_PROFILES = (
    # The minimum two-example lesson is a crossed pair: dimensions, component
    # count, non-selector sizes, and border side stay fixed while selector size
    # changes the intended modulo rotation from one to two.
    {"height": 14, "width": 15, "sizes": (2, 5, 7, 9), "selector": 5, "side": "bottom"},
    {"height": 14, "width": 15, "sizes": (2, 6, 7, 9), "selector": 6, "side": "bottom"},
    {"height": 16, "width": 17, "sizes": (3, 6, 7, 9), "selector": 6, "side": "left"},
    {"height": 18, "width": 19, "sizes": (4, 7, 8), "selector": 7, "side": "top"},
    {"height": 20, "width": 21, "sizes": (2, 5, 7, 10), "selector": 7, "side": "bottom"},
    {"height": 22, "width": 23, "sizes": (3, 5, 8), "selector": 8, "side": "left"},
)

_QUERY_PROFILES = (
    {"height": 15, "width": 16, "sizes": (3, 4, 7), "selector": 4, "side": "bottom"},
    {"height": 21, "width": 23, "sizes": (2, 6, 7, 9), "selector": 6, "side": "right"},
    {"height": 26, "width": 27, "sizes": (2, 4, 7, 8), "selector": 7, "side": "top"},
    {"height": 30, "width": 30, "sizes": (3, 5, 8, 10), "selector": 5, "side": "left"},
)


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"order_mode"}:
        raise ValueError("settings must contain exactly order_mode")
    mode = settings["order_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("order_mode must be size_desc or border_shift")
    return mode


def _validate_request(seed: Any, demos: Any, queries: Any) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise TypeError("seed must be an integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise TypeError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise TypeError("queries must be an integer in 1..4")


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"677dcb71e2be|{seed}|{label}|v1".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(
    cells: tuple[tuple[int, int], ...], rng: random.Random
) -> tuple[tuple[int, int], ...]:
    result = list(cells)
    turns = rng.randrange(4)
    for _ in range(turns):
        result = [(c, -r) for r, c in result]
    if rng.choice((False, True)):
        result = [(r, -c) for r, c in result]
    return _normalize(tuple(result))


def _bbox_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _cells(origin: tuple[int, int], shape) -> set[tuple[int, int]]:
    top, left = origin
    return {(top + r, left + c) for r, c in shape}


def _separated(cells: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _origins(height: int, width: int, shape, side: str | None) -> list[tuple[int, int]]:
    sh, sw = _bbox_dims(shape)
    if side == "top":
        return [(0, c) for c in range(1, width - sw)]
    if side == "bottom":
        return [(height - sh, c) for c in range(1, width - sw)]
    if side == "left":
        return [(r, 0) for r in range(1, height - sh)]
    if side == "right":
        return [(r, width - sw) for r in range(1, height - sh)]
    return [
        (r, c)
        for r in range(1, height - sh)
        for c in range(1, width - sw)
    ]


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        result.append(
            {
                "cells": tuple(sorted(cells)),
                "color": color,
                "size": len(cells),
                "bbox": (r1, c1, r2, c2),
                "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
            }
        )
    return sorted(result, key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))


def _touches_border(comp: dict[str, Any], height: int, width: int) -> bool:
    r1, c1, r2, c2 = comp["bbox"]
    return r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1


def _bars(comps: list[dict[str, Any]]) -> list[list[int]]:
    row: list[int] = []
    for index, comp in enumerate(comps):
        if index:
            row.append(0)
        row.extend([comp["color"]] * comp["size"])
    if not 1 <= len(row) <= 30:
        raise ValueError(f"output width {len(row)} is outside 1..30")
    return [row]


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be a rectangular exact-integer ARC grid")
    comps = _components(grid)
    border = [comp for comp in comps if _touches_border(comp, len(grid), len(grid[0]))]
    if len(border) != 1:
        raise ValueError(f"expected one border component, found {len(border)}")
    offset = border[0]["size"] % len(comps)
    return {
        "components": comps,
        "component_count": len(comps),
        "border_components": border,
        "rotation_offset": offset,
    }


def output_for(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("unknown order mode")
    facts = scene_facts(grid)
    ordered = sorted(
        facts["components"], key=lambda comp: (-comp["size"], comp["color"])
    )
    if mode == "border_shift":
        offset = facts["rotation_offset"]
        if offset == 0:
            raise ValueError("border selector produced a collapsing zero rotation")
        ordered = ordered[offset:] + ordered[:offset]
    return _bars(ordered)


def _choose_colors(rng: random.Random, sizes: tuple[int, ...], selector: int) -> tuple[int, ...]:
    colors = rng.sample(range(1, 10), len(sizes))
    selector_index = sizes.index(selector)
    n = len(sizes)
    true_offset = selector % n
    rank = sorted(colors).index(colors[selector_index]) % n
    forbidden = {0, true_offset}
    if rank in forbidden:
        swap_index = next(
            index
            for index in range(len(colors))
            if index != selector_index
            and sorted(colors).index(colors[index]) % n not in forbidden
        )
        colors[selector_index], colors[swap_index] = colors[swap_index], colors[selector_index]
    return tuple(colors)


def _make_scene(seed: int, label: str, profile: dict[str, Any]) -> list[list[int]]:
    rng = _rng(seed, label)
    height = profile["height"]
    width = profile["width"]
    sizes = tuple(profile["sizes"])
    selector_size = profile["selector"]
    selector_index = sizes.index(selector_size)
    if selector_size % len(sizes) == 0:
        raise ValueError("profile selector collapses to zero rotation")

    shapes = []
    for index, size in enumerate(sizes):
        # The selector deliberately takes an expanded shape; others vary.
        variant = 1 if index == selector_index else rng.randrange(len(_SHAPES[size]))
        shapes.append(_transform(_SHAPES[size][variant], rng))
    colors = _choose_colors(rng, sizes, selector_size)

    candidate_lists = []
    for index, shape in enumerate(shapes):
        side = profile["side"] if index == selector_index else None
        candidates = _origins(height, width, shape, side)
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    chosen: list[tuple[int, int] | None] = [None] * len(sizes)
    occupied: set[tuple[int, int]] = set()
    nodes = 0

    def search(index: int) -> bool:
        nonlocal nodes
        nodes += 1
        if nodes > 250_000:
            return False
        if index == len(sizes):
            origins = [origin for origin in chosen if origin is not None]
            row_span = max(r for r, _ in origins) - min(r for r, _ in origins)
            col_span = max(c for _, c in origins) - min(c for _, c in origins)
            if row_span < max(3, height // 3) or col_span < max(3, width // 3):
                return False
            # For the two-example minimum, make top-left-size shortcuts disagree.
            if label.endswith("demo-0") or label.endswith("demo-1"):
                first_index = min(range(len(origins)), key=lambda i: origins[i])
                if sizes[first_index] % len(sizes) == selector_size % len(sizes):
                    return False
            return True
        for origin in candidate_lists[index]:
            cells = _cells(origin, shapes[index])
            if not _separated(cells, occupied):
                continue
            chosen[index] = origin
            occupied.update(cells)
            if search(index + 1):
                return True
            occupied.difference_update(cells)
            chosen[index] = None
        return False

    # Place the constrained selector first, then large objects, to keep search bounded.
    order = [selector_index] + sorted(
        (index for index in range(len(sizes)) if index != selector_index),
        key=lambda index: -sizes[index],
    )
    reordered_shapes = [shapes[index] for index in order]
    reordered_candidates = [candidate_lists[index] for index in order]
    reordered_sizes = [sizes[index] for index in order]
    reordered_colors = [colors[index] for index in order]
    shapes = reordered_shapes
    candidate_lists = reordered_candidates
    sizes = tuple(reordered_sizes)
    colors = tuple(reordered_colors)
    selector_index = 0
    chosen = [None] * len(sizes)
    occupied = set()
    if not search(0):
        raise ValueError(f"unable to construct profile {label}")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for origin, shape, color in zip(chosen, shapes, colors):
        assert origin is not None
        for r, c in _cells(origin, shape):
            if grid[r][c] != 0:
                raise AssertionError("placement overlap")
            grid[r][c] = color

    facts = scene_facts(grid)
    if facts["border_components"][0]["size"] != profile["selector"]:
        raise AssertionError("wrong selector component")
    return grid


def _pair(seed: int, split: str, index: int, mode: str) -> dict[str, list[list[int]]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    grid = _make_scene(seed, f"{split}-{index}", profiles[index])
    return {"input": grid, "output": output_for(grid, mode)}


def program(settings: dict[str, Any]) -> str:
    mode = _validate_settings(settings)
    filename = "canonical.rkt" if mode == "size_desc" else "border_shift.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    mode = _validate_settings(settings)
    _validate_request(seed, demos, queries)
    train = [_pair(seed, "demo", index, mode) for index in range(demos)]
    full_query_bank = [_pair(seed, "query", index, mode) for index in range(4)]
    pairs = train + full_query_bank
    identities = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    if len(identities) != len(set(identities)):
        raise ValueError("episode inputs must be distinct")
    return {
        "train": train,
        "test": full_query_bank[:queries],
        "program_solution": program(settings),
    }


def _rotate_output(grid: list[list[int]], offset_fn: Callable[[dict[str, Any]], int]) -> list[list[int]]:
    facts = scene_facts(grid)
    ordered = sorted(facts["components"], key=lambda comp: (-comp["size"], comp["color"]))
    offset = offset_fn(facts) % len(ordered)
    return _bars(ordered[offset:] + ordered[:offset])


def _selector(facts: dict[str, Any]) -> dict[str, Any]:
    return facts["border_components"][0]


def _fixed(value: int) -> Callable[[dict[str, Any]], int]:
    return lambda facts: value


def _largest(facts: dict[str, Any]) -> int:
    return max(comp["size"] for comp in facts["components"])


def _smallest(facts: dict[str, Any]) -> int:
    return min(comp["size"] for comp in facts["components"])


def _top_left(facts: dict[str, Any]) -> int:
    return min(facts["components"], key=lambda comp: comp["bbox"][:2])["size"]


def _bbox_area(facts: dict[str, Any]) -> int:
    return _selector(facts)["bbox_area"]


def _color_rank(facts: dict[str, Any]) -> int:
    colors = sorted(comp["color"] for comp in facts["components"])
    return colors.index(_selector(facts)["color"])


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_offset_1": lambda grid: _rotate_output(grid, _fixed(1)),
    "fixed_offset_2": lambda grid: _rotate_output(grid, _fixed(2)),
    "fixed_offset_3": lambda grid: _rotate_output(grid, _fixed(3)),
    "largest_size_offset": lambda grid: _rotate_output(grid, _largest),
    "smallest_size_offset": lambda grid: _rotate_output(grid, _smallest),
    "top_left_size_offset": lambda grid: _rotate_output(grid, _top_left),
    "selector_bbox_area_offset": lambda grid: _rotate_output(grid, _bbox_area),
    "selector_color_rank_offset": lambda grid: _rotate_output(grid, _color_rank),
}


def lesson_identifiable(demos: list[dict[str, Any]], queries: list[dict[str, Any]]) -> list[str]:
    """Return finite shortcut rules that survive the labeled demonstrations."""
    if not isinstance(demos, list) or not demos:
        return ["lesson needs demonstrations"]
    reasons = []
    official_modes = {
        mode
        for mode in MODES
        if all(output_for(pair["input"], mode) == pair["output"] for pair in demos)
    }
    if len(official_modes) != 1:
        reasons.append(f"declared settings surviving demos: {sorted(official_modes)}")
    for name, rival in _RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            differs = any(rival(pair["input"]) != pair["output"] for pair in queries)
            reasons.append(
                f"competitor {name!r} fits every demo"
                + (" but disagrees on a query" if differs else " and all sampled queries")
            )
    return reasons
