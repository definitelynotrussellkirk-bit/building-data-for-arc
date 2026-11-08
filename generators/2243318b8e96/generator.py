"""Generator for ARC task 2243318b8e96: recolor objects by size parity.

The canonical rule extracts same-color four-connected objects, counts each
object's cells, paints odd objects green (3), and paints even objects cyan (8).
Ordinary scenes deliberately vary colors, sizes, boundary contact, and a
same-color diagonal contact so color-only, threshold, bounding-box, and
8-connectivity shortcuts are not reliable substitutes for counting cells.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2243318b8e96"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "419ce8882a3d"
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (0, 1, 2)
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains 3..6 same-color four-connected objects. "
    "Replace every odd-sized object by color 3 and every even-sized object by "
    "color 8, preserving all occupied coordinates."
)

INVARIANTS = [
    "8..16 rows and columns with exact ARC colors",
    "3..6 four-connected same-color objects",
    "1..3 distinct nonzero input colors",
    "at least one odd-sized and one even-sized object",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "8..16",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "8..16",
        "doc": "Grid width.",
    },
    "n_blobs": {
        "type": "int",
        "default": "profile schedule",
        "valid": "3..6",
        "doc": "Number of four-connected same-color objects.",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "profile schedule",
        "valid": "1..3",
        "doc": "Number of distinct nonzero input colors.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = _CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))

# Every prefix is connected.  Prefixes 3 and 8 deliberately have a bounding-box
# parity that differs from their cell-count parity, defeating bbox-area parity.
_SHAPE_PATH = (
    (0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1),
    (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3), (0, 3),
)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(seed: object, sample_index: object, difficulty: object,
                   overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an exact integer; got {seed!r}")
    if type(sample_index) is not int:
        raise TypeError(f"sample_index must be an exact integer; got {sample_index!r}")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative; got {sample_index}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}")


def _draw_int(ctx, label: str, global_lo: int, global_hi: int,
              default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _default_ranges(profile: int, difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        h_range, w_range = (8, 10), (8, 10)
    elif difficulty == "medium":
        h_range, w_range = (10, 13), (10, 13)
    elif difficulty == "hard":
        h_range, w_range = (13, 16), (13, 16)
    else:
        h_range, w_range = (8, 16), (8, 16)
    blob_ranges = ((3, 4), (4, 5), (5, 6))
    return h_range, w_range, blob_ranges[profile]


def _grid_errors(grid: object) -> list[str]:
    if type(grid) is not list or not grid:
        return ["grid must be a non-empty list"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 8 <= len(grid) <= 16 or not 8 <= width <= 16:
        return [f"grid dimensions must lie in 8..16; got {len(grid)}x{width}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an exact ARC integer 0..9; got {value!r}")
    return errors


def _components(grid: list[list[int]], *, connectivity: int = 4) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    deltas = _CARDINAL if connectivity == 4 else _EIGHT
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    found: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in deltas:
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        found.append({
            "color": color,
            "cells": cells,
            "size": len(cells),
            "bbox": (min(rs), min(cs), max(rs), max(cs)),
        })
    return found


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(components),
        "n_distinct_colors": len({obj["color"] for obj in components}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    errors = _grid_errors(grid)
    if errors:
        return errors
    components = _components(grid)
    if not 3 <= len(components) <= 6:
        errors.append(f"expected 3..6 objects, found {len(components)}")
    colors = {obj["color"] for obj in components}
    if not 1 <= len(colors) <= 3:
        errors.append(f"expected 1..3 nonzero colors, found {len(colors)}")
    sizes = [obj["size"] for obj in components]
    if sizes and not any(size % 2 for size in sizes):
        errors.append("no odd-sized object")
    if sizes and not any(size % 2 == 0 for size in sizes):
        errors.append("no even-sized object")
    overrides = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(overrides, dict):
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for name, expected in overrides.items():
                if name in AXES and observed[name] != expected:
                    errors.append(f"override {name}={expected!r} not realized; observed {observed[name]!r}")
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj in _components(grid):
        color = 3 if obj["size"] % 2 else 8
        for r, c in obj["cells"]:
            output[r][c] = color
    return output


def _paint_by(grid: list[list[int]], chooser: Callable[[dict[str, Any]], int],
              *, connectivity: int = 4) -> list[list[int]]:
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj in _components(grid, connectivity=connectivity):
        color = chooser(obj)
        for r, c in obj["cells"]:
            output[r][c] = color
    return output


def _swapped_parity(grid):
    return _paint_by(grid, lambda obj: 8 if obj["size"] % 2 else 3)


def _singleton_vs_rest(grid):
    return _paint_by(grid, lambda obj: 3 if obj["size"] == 1 else 8)


def _threshold_three(grid):
    return _paint_by(grid, lambda obj: 3 if obj["size"] <= 3 else 8)


def _bbox_area_parity(grid):
    def choose(obj):
        r0, c0, r1, c1 = obj["bbox"]
        area = (r1 - r0 + 1) * (c1 - c0 + 1)
        return 3 if area % 2 else 8
    return _paint_by(grid, choose)


def _eight_connected_parity(grid):
    return _paint_by(grid, lambda obj: 3 if obj["size"] % 2 else 8, connectivity=8)


def _color_total_parity(grid):
    totals = Counter(value for row in grid for value in row if value)
    return _paint_by(grid, lambda obj: 3 if totals[obj["color"]] % 2 else 8)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "swapped_parity": _swapped_parity,
    "singleton_vs_rest": _singleton_vs_rest,
    "size_at_most_three": _threshold_three,
    "bounding_box_area_parity": _bbox_area_parity,
    "eight_connected_components": _eight_connected_parity,
    "whole_color_frequency_parity": _color_total_parity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only heuristics that reproduce every labeled canonical pair belong here.
# The canonical examples do not expose diagonal same-color adjacency, so an
# 8-connected parser is the sole measured canonical ambiguity.
CANONICAL_SHORTCUTS = {
    "eight_connected_components": _eight_connected_parity,
}


def lesson_identifiable(demos, query=None) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
            errors.append(f"demo {index} must contain input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            errors.append(f"demo {index}: {exc}")
            continue
        if pair["output"] != expected:
            errors.append(f"demo {index} label disagrees with canonical rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos if isinstance(pair, dict)):
            errors.append(f"competitor survives demonstrations: {name}")
    if query is not None:
        if not isinstance(query, dict) or set(query) < {"input", "output"}:
            errors.append("query must contain input/output")
        elif rule_mirror(query["input"]) != query["output"]:
            errors.append("query label disagrees with canonical rule")
    return errors


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return _normalize((c, -r) for r, c in cells)


def _shape_variants(size: int) -> tuple[frozenset[tuple[int, int]], ...]:
    if not 1 <= size <= len(_SHAPE_PATH):
        raise ValueError(f"unsupported object size: {size}")
    base = _normalize(_SHAPE_PATH[:size])
    variants: set[frozenset[tuple[int, int]]] = set()
    current = base
    for _ in range(4):
        variants.add(current)
        variants.add(_normalize((r, -c) for r, c in current))
        current = _rotate(current)
    return tuple(sorted(variants, key=lambda cells: sorted(cells)))


def _transform_corner(cells: set[tuple[int, int]], h: int, w: int,
                      flip_rows: bool, flip_cols: bool) -> set[tuple[int, int]]:
    return {
        (h - 1 - r if flip_rows else r, w - 1 - c if flip_cols else c)
        for r, c in cells
    }


def _touches_cardinal(candidate: set[tuple[int, int]], used: set[tuple[int, int]]) -> bool:
    return any((r + dr, c + dc) in used for r, c in candidate for dr, dc in _CARDINAL)


def _candidate_placements(shape: frozenset[tuple[int, int]], h: int, w: int) -> list[set[tuple[int, int]]]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    return [
        {(top + r, left + c) for r, c in shape}
        for top in range(h - sh + 1)
        for left in range(w - sw + 1)
    ]


def _place_layout(h: int, w: int, sizes: list[int], rng, profile: int) -> list[set[tuple[int, int]]]:
    # The first two objects meet only diagonally.  When they share a color this
    # is a direct ordinary-scene counterexample to 8-connectivity counting.
    first = {(0, c) for c in range(sizes[0])}
    second = {(r, sizes[0]) for r in range(1, sizes[1] + 1)}
    if max(c for _, c in first | second) >= w or max(r for r, _ in first | second) >= h:
        raise RuntimeError("fixed diagonal pair does not fit")
    flip_rows, flip_cols = ((False, False), (False, True), (True, False))[profile]
    first = _transform_corner(first, h, w, flip_rows, flip_cols)
    second = _transform_corner(second, h, w, flip_rows, flip_cols)
    placements: dict[int, set[tuple[int, int]]] = {0: first, 1: second}
    used = first | second

    order = sorted(range(2, len(sizes)), key=lambda index: (-sizes[index], index))

    def search(position: int, occupied: set[tuple[int, int]]) -> bool:
        if position == len(order):
            return True
        index = order[position]
        candidates: list[set[tuple[int, int]]] = []
        for shape in _shape_variants(sizes[index]):
            candidates.extend(_candidate_placements(shape, h, w))
        rng.shuffle(candidates)
        # Prefer new border contacts on the last object while retaining a broad
        # randomized candidate tail for deterministic backtracking.
        if position == len(order) - 1:
            candidates.sort(key=lambda cells: not any(
                r in (0, h - 1) or c in (0, w - 1) for r, c in cells
            ))
        for candidate in candidates:
            if candidate & occupied or _touches_cardinal(candidate, occupied):
                continue
            placements[index] = candidate
            if search(position + 1, occupied | candidate):
                return True
            placements.pop(index, None)
        return False

    if not search(0, used):
        raise RuntimeError(f"could not place {len(sizes)} separated objects in {h}x{w}")
    return [placements[index] for index in range(len(sizes))]


def _sizes(profile: int, n_blobs: int, h: int, w: int) -> list[int]:
    banks = (
        (1, 2, 3, 4, 5, 2),
        (2, 3, 4, 5, 2, 3),
        (3, 4, 5, 2, 3, 4),
    )
    offset = 2 if min(h, w) >= 12 else 0
    return [value + offset for value in banks[profile][:n_blobs]]


def _color_roles(rng, n_blobs: int, n_colors: int) -> list[int]:
    palette = rng.sample(list(range(1, 10)), n_colors)
    if n_colors == n_blobs:
        return palette[:]
    roles = [palette[0], palette[0]]
    for color in palette[1:]:
        if len(roles) < n_blobs:
            roles.append(color)
    index = 1
    while len(roles) < n_blobs:
        roles.append(palette[index % n_colors])
        index += 1
    return roles


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    h_range, w_range, blob_range = _default_ranges(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_int(ctx, "grid_h", 8, 16, *h_range)
    w = _draw_int(ctx, "grid_w", 8, 16, *w_range)
    n_blobs = _draw_int(ctx, "n_blobs", 3, 6, *blob_range)
    default_colors = profile + 1
    n_colors = _draw_int(ctx, "n_distinct_colors", 1, 3,
                       default_colors, default_colors)

    rng = ctx.draw_rng("layout")
    sizes = _sizes(profile, n_blobs, h, w)
    placements = _place_layout(h, w, sizes, rng, profile)
    colors = _color_roles(rng, n_blobs, n_colors)
    grid = full_grid(h, w, 0)
    for cells, color in zip(placements, colors):
        for r, c in cells:
            grid[r][c] = color

    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_blobs": n_blobs,
        "n_distinct_colors": n_colors,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes differ: expected {expected}, observed {observed}")
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": expected})
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    empty: list[list[int]] = []
    ragged = [[0] * 8 for _ in range(8)]
    ragged[-1].pop()
    boolean_cell = [[0] * 8 for _ in range(8)]
    boolean_cell[0][0] = True
    all_odd = [[0] * 8 for _ in range(8)]
    for color, (r, c) in zip((1, 2, 3), ((0, 0), (3, 3), (7, 7))):
        all_odd[r][c] = color
    all_even = [[0] * 8 for _ in range(8)]
    for color, (r, c) in zip((1, 2, 3), ((0, 0), (3, 3), (6, 6))):
        all_even[r][c] = color
        all_even[r][c + (1 if c < 7 else -1)] = color
    too_many_colors = [[0] * 8 for _ in range(8)]
    for color, (r, c) in zip((1, 2, 4, 5), ((0, 0), (2, 2), (4, 4), (6, 6))):
        too_many_colors[r][c] = color
    return [
        ("empty", empty),
        ("ragged", ragged),
        ("boolean_cell", boolean_cell),
        ("all_odd", all_odd),
        ("all_even", all_even),
        ("too_many_colors", too_many_colors),
    ]


SEMANTIC_WITNESSES = {
    "diagonal_same_color_pair": lambda grid: _eight_connected_parity(grid) != rule_mirror(grid),
    "irregular_bbox": lambda grid: _bbox_area_parity(grid) != rule_mirror(grid),
    "color_reuse_across_parity": lambda grid: _color_total_parity(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "diagonal_same_color_pair": ("eight_connected_components",),
    "irregular_bbox": ("bounding_box_area_parity",),
    "color_reuse_across_parity": ("whole_color_frequency_parity",),
}
