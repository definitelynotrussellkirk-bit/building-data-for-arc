"""Input generator for efb59efe0080 — normalize two masks, XOR, then crop.

The selected Racket authority is unchanged.  Inputs contain exactly one
4-connected red (2) object and one 4-connected green (3) object.  Each object
is cropped to its own bounding box and top-left aligned; the output is the cyan
(8) symmetric difference, cropped once more to its non-zero bounding box.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "efb59efe0080"
TASK_ID = GENERATOR_ID
RULE_HASH = "1cb444e6f050"
VERSION = "3.0.0"
SUMMARY = (
    "A canonical-size 0-background canvas contains one connected red (2) mask "
    "and one connected green (3) mask. Crop each mask to its own bbox, align "
    "their top-left corners, XOR occupancy into cyan (8), then crop the XOR. "
    "Consecutive lessons alternate crop-required and crop-noop counterexamples."
)

INVARIANTS = [
    "canvas dimensions are one of the five canonical input profiles",
    "each color 2/3 forms one connected 4..8-cell mask inside a 3x3 bbox",
    "normalized masks overlap, differ on both sides, and are not identical",
    "generated shape detail refutes filled-bbox XOR; positions refute absolute-coordinate XOR",
    "the selected Racket authority, not this generator, remains label authority",
]

CANVAS_PROFILES: dict[str, tuple[int, int]] = {
    "8x12": (8, 12),
    "9x13": (9, 13),
    "10x14": (10, 14),
    "11x15": (11, 15),
    "12x16": (12, 16),
}

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "uniform over canonical profiles",
        "valid": "8x12|9x13|10x14|11x15|12x16",
    },
    "size_2": {"type": "int", "default": "difficulty-aware 4..8", "valid": "4..8"},
    "size_3": {"type": "int", "default": "difficulty-aware 4..8", "valid": "4..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("crop_required", "crop_noop")

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_BOARD_3X3 = tuple((r, c) for r in range(3) for c in range(3))
Shape = tuple[tuple[int, int], ...]
Grid = list[list[int]]


def _normalize(points: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(points)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _connected(points: Iterable[tuple[int, int]]) -> bool:
    cells = set(points)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


@lru_cache(maxsize=5)
def _shape_catalog(size: int) -> tuple[Shape, ...]:
    """Every normalized connected ``size``-cell subset of a 3x3 board."""
    if not 4 <= size <= 8:
        raise ValueError(f"shape size {size} is outside 4..8")
    shapes = {
        _normalize(candidate)
        for candidate in combinations(_BOARD_3X3, size)
        if _connected(candidate)
    }
    return tuple(sorted(shapes))


def _crop_points(points: Iterable[tuple[int, int]]) -> Shape:
    return _normalize(points)


def _raw_xor(a: Shape, b: Shape) -> tuple[set[tuple[int, int]], tuple[int, int]]:
    aset, bset = set(a), set(b)
    ah, aw = _shape_dims(a)
    bh, bw = _shape_dims(b)
    return aset ^ bset, (max(ah, bh), max(aw, bw))


def _filled_bbox(shape: Shape) -> set[tuple[int, int]]:
    h, w = _shape_dims(shape)
    return {(r, c) for r in range(h) for c in range(w)}


def _requires_final_crop(a: Shape, b: Shape) -> bool:
    xor, (h, w) = _raw_xor(a, b)
    cropped = _crop_points(xor)
    return _shape_dims(cropped) != (h, w)


@lru_cache(maxsize=50)
def _shape_pairs(size_2: int, size_3: int, profile: str) -> tuple[tuple[Shape, Shape], ...]:
    """Constructive pair catalog for every advertised size cross-product."""
    if profile not in SCHEDULE_PROFILES:
        raise ValueError(f"unknown schedule profile {profile!r}")
    pairs: list[tuple[Shape, Shape]] = []
    for shape_2 in _shape_catalog(size_2):
        a = set(shape_2)
        for shape_3 in _shape_catalog(size_3):
            b = set(shape_3)
            if a == b or not (a & b) or not (a - b) or not (b - a):
                continue
            xor, _ = _raw_xor(shape_2, shape_3)
            intended = _crop_points(xor)
            bbox_xor = _filled_bbox(shape_2) ^ _filled_bbox(shape_3)
            bbox_result = _crop_points(bbox_xor) if bbox_xor else ()
            if intended == bbox_result:
                continue
            crop_required = _requires_final_crop(shape_2, shape_3)
            if crop_required != (profile == "crop_required"):
                continue
            pairs.append((shape_2, shape_3))
    if not pairs:
        raise RuntimeError(
            f"no constructive pair for sizes ({size_2}, {size_3}) and {profile}"
        )
    return tuple(pairs)


@lru_cache(maxsize=625)
def _legal_placements(
    h: int,
    w: int,
    h2: int,
    w2: int,
    h3: int,
    w3: int,
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    """All bbox placements with at least one blank row or column between them."""
    out: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r2 in range(h - h2 + 1):
        for c2 in range(w - w2 + 1):
            for r3 in range(h - h3 + 1):
                for c3 in range(w - w3 + 1):
                    separated = (
                        r2 + h2 < r3
                        or r3 + h3 < r2
                        or c2 + w2 < c3
                        or c3 + w3 < c2
                    )
                    if separated:
                        out.append(((r2, c2), (r3, c3)))
    if not out:
        raise RuntimeError("canvas cannot place two separated shape bboxes")
    return tuple(out)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternate crop-sensitive and crop-insensitive examples in every band."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if "canvas_profile" in overrides:
        value = overrides["canvas_profile"]
        if not isinstance(value, str):
            raise TypeError("canvas_profile override must be a string")
        if value not in CANVAS_PROFILES:
            raise ValueError(f"canvas_profile override {value!r} is not supported")
    for name in ("size_2", "size_3"):
        if name not in overrides:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} override must be an integer")
        if not 4 <= value <= 8:
            raise ValueError(f"{name} override {value} is outside 4..8")


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canvas_profile = ctx.draw_choice("canvas_profile", tuple(CANVAS_PROFILES))
    size_2 = ctx.draw_int_diff("size_2", 4, 8)
    size_3 = ctx.draw_int_diff("size_3", 4, 8)
    profile = schedule_profile(seed, sample_index, difficulty)

    pair_rng = ctx.draw_rng("shape_pair")
    shape_2, shape_3 = pair_rng.choice(_shape_pairs(size_2, size_3, profile))
    h, w = CANVAS_PROFILES[canvas_profile]
    h2, w2 = _shape_dims(shape_2)
    h3, w3 = _shape_dims(shape_3)
    placement_rng = ctx.draw_rng("placement")
    (r2, c2), (r3, c3) = placement_rng.choice(
        _legal_placements(h, w, h2, w2, h3, w3)
    )

    grid = full_grid(h, w, 0)
    for r, c in shape_2:
        grid[r2 + r][c2 + c] = 2
    for r, c in shape_3:
        grid[r3 + r][c3 + c] = 3
    return grid


def _grid_cells(grid: Grid, color: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _normalized_masks(grid: Grid) -> tuple[Shape, Shape]:
    return _normalize(_grid_cells(grid, 2)), _normalize(_grid_cells(grid, 3))


def _points_grid(points: Iterable[tuple[int, int]], *, empty: Grid | None = None) -> Grid:
    cells = set(points)
    if not cells:
        return [[0]] if empty is None else [row[:] for row in empty]
    h, w = _shape_dims(cells)
    out = full_grid(h, w, 0)
    for r, c in cells:
        out[r][c] = 8
    return out


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains selected authority."""
    shape_2, shape_3 = _normalized_masks(grid)
    xor, _ = _raw_xor(shape_2, shape_3)
    return _points_grid(_crop_points(xor))


def _uncropped_xor(grid: Grid) -> Grid:
    shape_2, shape_3 = _normalized_masks(grid)
    xor, (h, w) = _raw_xor(shape_2, shape_3)
    out = full_grid(h, w, 0)
    for r, c in xor:
        out[r][c] = 8
    return out


def _normalized_union(grid: Grid) -> Grid:
    shape_2, shape_3 = _normalized_masks(grid)
    return _points_grid(_crop_points(set(shape_2) | set(shape_3)))


def _filled_bbox_xor(grid: Grid) -> Grid:
    shape_2, shape_3 = _normalized_masks(grid)
    points = _filled_bbox(shape_2) ^ _filled_bbox(shape_3)
    return _points_grid(_crop_points(points)) if points else [[0]]


def _red_mask_only(grid: Grid) -> Grid:
    shape_2, _ = _normalized_masks(grid)
    return _points_grid(shape_2)


def _absolute_position_xor(grid: Grid) -> Grid:
    points = _grid_cells(grid, 2) | _grid_cells(grid, 3)
    return _points_grid(_crop_points(points))


def _crop_required_grid(grid: Grid) -> bool:
    return rule_mirror(grid) != _uncropped_xor(grid)


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["every grid row must be a list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return ["grid must be rectangular and non-empty"]
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for row in grid
        for value in row
    ):
        return ["all cells must be integer ARC colors"]
    return []


def observe_overrides(grid: Any) -> dict[str, int | str]:
    if _basic_grid_errors(grid):
        return {}
    h, w = len(grid), len(grid[0])
    return {
        "canvas_profile": f"{h}x{w}",
        "size_2": sum(value == 2 for row in grid for value in row),
        "size_3": sum(value == 3 for row in grid for value in row),
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected task's defended input/teaching manifold."""
    del difficulty
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    profile = f"{h}x{w}"
    if profile not in CANVAS_PROFILES:
        errors.append(f"canvas {profile} is not a canonical input profile")

    values = {value for row in grid for value in row}
    unexpected = sorted(values - {0, 2, 3})
    if unexpected:
        errors.append(f"unexpected colors {unexpected}; expected only 0, 2, and 3")
        return errors

    cells_2 = _grid_cells(grid, 2)
    cells_3 = _grid_cells(grid, 3)
    for color, cells in ((2, cells_2), (3, cells_3)):
        if not 4 <= len(cells) <= 8:
            errors.append(f"color-{color} object must contain 4..8 cells; got {len(cells)}")
        if cells and not _connected(cells):
            errors.append(f"color-{color} cells must form exactly one 4-connected object")
        if cells:
            shape = _normalize(cells)
            sh, sw = _shape_dims(shape)
            if sh > 3 or sw > 3:
                errors.append(f"color-{color} bbox {sh}x{sw} exceeds 3x3")

    if cells_2 and cells_3:
        shape_2, shape_3 = _normalize(cells_2), _normalize(cells_3)
        set_2, set_3 = set(shape_2), set(shape_3)
        if set_2 == set_3:
            errors.append("normalized color-2 and color-3 masks must differ")
        if not (set_2 & set_3):
            errors.append("normalized masks must overlap to teach XOR rather than union")
        if not (set_2 - set_3) or not (set_3 - set_2):
            errors.append("each normalized mask must contribute exclusive cells")
        bbox_points = _filled_bbox(shape_2) ^ _filled_bbox(shape_3)
        bbox_result = _points_grid(_crop_points(bbox_points)) if bbox_points else [[0]]
        try:
            intended = rule_mirror(grid)
        except ValueError as exc:
            errors.append(f"normalized XOR is invalid: {exc}")
        else:
            if bbox_result == intended:
                errors.append("shape detail does not refute filled-bbox XOR")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict):
        observed = observe_overrides(grid)
        for name, requested in overrides.items():
            if name in AXES and observed.get(name) != requested:
                errors.append(
                    f"override {name} requested {requested!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def _valid(grid: Any) -> bool:
    return self_check(grid) == []


def _two_sided_overlap(grid: Grid) -> bool:
    if not _valid(grid):
        return False
    shape_2, shape_3 = _normalized_masks(grid)
    a, b = set(shape_2), set(shape_3)
    return bool(a & b and a - b and b - a)


def _shape_detail_not_bbox(grid: Grid) -> bool:
    return _valid(grid) and _filled_bbox_xor(grid) != rule_mirror(grid)


def _normalization_required(grid: Grid) -> bool:
    return _valid(grid) and _absolute_position_xor(grid) != rule_mirror(grid)


def _final_crop_required(grid: Grid) -> bool:
    return _valid(grid) and _crop_required_grid(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "normalized_union": _normalized_union,
    "uncropped_xor": _uncropped_xor,
    "filled_bbox_xor": _filled_bbox_xor,
    "red_mask_only": _red_mask_only,
    "absolute_position_xor": _absolute_position_xor,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "two_sided_overlap": _two_sided_overlap,
    "final_crop_required": _final_crop_required,
    "shape_detail_not_bbox": _shape_detail_not_bbox,
    "normalization_required": _normalization_required,
}
WITNESS_RIVALS = {
    "two_sided_overlap": ["normalized_union", "red_mask_only"],
    "final_crop_required": ["uncropped_xor"],
    "shape_detail_not_bbox": ["filled_bbox_xor"],
    "normalization_required": ["absolute_position_xor"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["demos must be a non-empty list"]

    crop_states: set[bool] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        grid = pair["input"]
        issues = self_check(grid)
        if issues:
            reasons.append(f"demo {index} input is outside the grammar: {issues[0]}")
            continue
        intended = rule_mirror(grid)
        if pair["output"] != intended:
            reasons.append(f"demo {index} output disagrees with normalized XOR")
        crop_states.add(_crop_required_grid(grid))

    if crop_states != {False, True}:
        reasons.append(
            f"demos must include crop-required and crop-noop examples; saw {sorted(crop_states)}"
        )

    query_grid = query.get("input") if isinstance(query, dict) else None
    if self_check(query_grid):
        reasons.append("query input is outside the grammar")
    elif not isinstance(query, dict) or query.get("output") != rule_mirror(query_grid):
        reasons.append("query output disagrees with normalized XOR")

    for name, rival in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"demonstrations do not refute named rival {name!r}")
    return reasons
