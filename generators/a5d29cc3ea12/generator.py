"""Generator for arc_additional_puzzle_bank_volume12:M83.

A blue component is the legend.  Exactly three red candidate components are
shown; exactly one is the same shape as the legend under rotation and is
recolored cyan by the Racket oracle.  The two red controls are deliberately
hard negatives: one is the legend's mirror image (not a rotation), and one has
the same cell count and bounding-box dimensions but a different shape.

The public demonstrations never require rotation: their matching candidate is
already in the legend's normalized orientation in all five train/test pairs.
The six-step schedule below therefore alternates exact and rotated matches so
every sliding three-example lesson refutes the plausible "exact orientation
only" shortcut while also moving the answer through all three candidate ranks.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5d29cc3ea12"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6170a2c7de36"

SUMMARY = (
    "A canonical-sized zero-background grid contains one blue legend, exactly "
    "three red candidates, and one tiny irrelevant-color marker. Exactly one "
    "red candidate is rotation-equivalent to the legend and is recolored cyan "
    "8. A mirrored-but-not-rotated control and a same-size/same-bbox different "
    "shape remain red."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is 0; input color 8 is absent",
    "canvas dimensions use the canonical 10..12 by 12..15 envelope",
    "exactly one blue 4-connected legend component is present",
    "exactly three separated red 4-connected candidate components are present",
    "exactly one red candidate is a rotation of the legend",
    "at least one nonmatch has the legend's cell count",
    "one auxiliary color contributes one connected 1..2-cell irrelevant marker",
    "ordinary draws include both a reflection-only control and a same-bbox different-shape control",
]

# Four pairwise-distinct chiral rotation classes.  Every shape has four unique
# orientations and its mirror is outside its rotation orbit, making both
# absolute and relative rotation observably recoverable from the returned grid.
_BASE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),                  # L tetromino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),          # P pentomino
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),          # F pentomino
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1)),          # N pentomino
)
NOISE_COLORS = (3, 4, 5, 6, 7, 9)
NOISE_COLOR_TOKENS = ("3", "4", "5", "6", "7", "9")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-step schedule over canonical heights",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "six-step schedule over canonical widths",
        "valid": "12..15",
    },
    "shape_id": {
        "type": "int",
        "default": "six-step semantic schedule",
        "valid": "0..3",
    },
    "legend_rotation": {
        "type": "int",
        "default": "six-step semantic schedule",
        "valid": "0..3",
    },
    "match_rotation": {
        "type": "int",
        "default": "relative clockwise quarter-turns from legend, scheduled",
        "valid": "0..3",
    },
    "target_slot": {
        "type": "int",
        "default": "matching candidate reading-order rank, scheduled",
        "valid": "0..2",
    },
    "noise_color": {
        "type": "str",
        "default": "six-step canonical palette schedule",
        "valid": "3|4|5|6|7|9",
    },
    "noise_size": {
        "type": "int",
        "default": "six-step canonical 1/2-cell schedule",
        "valid": "1..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_PROFILES = (
    (12, 14),
    (11, 13),
    (12, 12),
    (10, 15),
    (11, 12),
)

# target_slot cycles 0/1/2; match_rotation follows 0/1/1/0/3/2.  Every cyclic
# window of three consecutive samples therefore contains all target ranks, at
# least one exact-orientation anchor, and at least one genuinely rotated match.
_SCHEDULE = (
    {"profile": (12, 14), "shape_id": 0, "legend_rotation": 0,
     "match_rotation": 0, "target_slot": 0, "noise_color": "6", "noise_size": 2},
    {"profile": (11, 13), "shape_id": 0, "legend_rotation": 1,
     "match_rotation": 1, "target_slot": 1, "noise_color": "7", "noise_size": 1},
    {"profile": (12, 12), "shape_id": 2, "legend_rotation": 2,
     "match_rotation": 1, "target_slot": 2, "noise_color": "4", "noise_size": 1},
    {"profile": (10, 15), "shape_id": 3, "legend_rotation": 3,
     "match_rotation": 0, "target_slot": 0, "noise_color": "6", "noise_size": 2},
    {"profile": (11, 12), "shape_id": 1, "legend_rotation": 1,
     "match_rotation": 3, "target_slot": 1, "noise_color": "7", "noise_size": 1},
    {"profile": (12, 14), "shape_id": 2, "legend_rotation": 3,
     "match_rotation": 2, "target_slot": 2, "noise_color": "4", "noise_size": 2},
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the six-way lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % len(_SCHEDULE)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _rotate_n(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(int(turns) % 4):
        result = _rotate_cw(result)
    return result


def _mirror_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _rotation_orbit(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    base = _normalize(cells)
    return frozenset(_rotate_n(base, turns) for turns in range(4))


def _dihedral_orbit(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    base = _normalize(cells)
    mirror = _mirror_lr(base)
    return frozenset(
        [_rotate_n(base, turns) for turns in range(4)]
        + [_rotate_n(mirror, turns) for turns in range(4)]
    )


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == remaining


@lru_cache(maxsize=None)
def _same_bbox_rivals(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Connected same-size/same-bbox shapes outside the legend's D4 orbit."""
    shape = _normalize(shape)
    height, width = _shape_dims(shape)
    forbidden = _dihedral_orbit(shape)
    cells = tuple((r, c) for r in range(height) for c in range(width))
    rivals: set[tuple[tuple[int, int], ...]] = set()
    for combo in combinations(cells, len(shape)):
        if (
            min(r for r, _ in combo) != 0
            or min(c for _, c in combo) != 0
            or max(r for r, _ in combo) != height - 1
            or max(c for _, c in combo) != width - 1
        ):
            continue
        if not _connected(combo):
            continue
        candidate = _normalize(combo)
        if candidate not in forbidden:
            rivals.add(candidate)
    if not rivals:
        raise RuntimeError(f"no same-bbox rival for shape {shape}")
    return tuple(sorted(rivals))


def _identify_shape(cells: Iterable[tuple[int, int]]) -> tuple[int, int] | None:
    norm = _normalize(cells)
    for shape_id, base in enumerate(_BASE_SHAPES):
        for rotation in range(4):
            if norm == _rotate_n(base, rotation):
                return shape_id, rotation
    return None


def _scheduled_int(ctx, overrides, label: str, lo: int, hi: int, default: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(ctx, overrides, label: str, options, default):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _slot_rectangles(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Four separated rectangles, each large enough for every shape variant."""
    split_r = height // 2
    split_c = width // 2
    return (
        (0, split_r - 1, 0, split_c - 1),
        (0, split_r - 1, split_c + 1, width),
        (split_r + 1, height, 0, split_c - 1),
        (split_r + 1, height, split_c + 1, width),
    )


def _stamp_in_slot(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    rectangle: tuple[int, int, int, int],
    rng,
) -> None:
    top, bottom, left, right = rectangle
    shape_h, shape_w = _shape_dims(shape)
    if shape_h > bottom - top or shape_w > right - left:
        raise ValueError(
            f"shape {shape_h}x{shape_w} does not fit slot "
            f"{bottom - top}x{right - left}"
        )
    # Fix the row within each quadrant so physical quadrant order is also
    # bbox reading order; horizontal jitter still prevents fixed coordinates.
    row0 = top
    col0 = rng.randint(left, right - shape_w)
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    phase = int(sample_index) % len(_SCHEDULE)
    profile = _SCHEDULE[phase]
    default_h, default_w = profile["profile"]

    height = _scheduled_int(ctx, overrides, "grid_h", 10, 12, default_h)
    width = _scheduled_int(ctx, overrides, "grid_w", 12, 15, default_w)
    shape_id = _scheduled_int(ctx, overrides, "shape_id", 0, 3, profile["shape_id"])
    legend_rotation = _scheduled_int(
        ctx, overrides, "legend_rotation", 0, 3, profile["legend_rotation"]
    )
    match_rotation = _scheduled_int(
        ctx, overrides, "match_rotation", 0, 3, profile["match_rotation"]
    )
    target_slot = _scheduled_int(
        ctx, overrides, "target_slot", 0, 2, profile["target_slot"]
    )
    noise_color = _scheduled_choice(
        ctx, overrides, "noise_color", NOISE_COLOR_TOKENS, profile["noise_color"]
    )
    noise_size = _scheduled_int(
        ctx, overrides, "noise_size", 1, 2, profile["noise_size"]
    )

    base = _BASE_SHAPES[shape_id]
    legend = _rotate_n(base, legend_rotation)
    match = _rotate_n(base, legend_rotation + match_rotation)

    band_tag = difficulty if difficulty in ("easy", "medium", "hard") else "unspecified"
    detail_rng = ctx.draw_rng(f"distractor_detail_{band_tag}")
    mirrored = _rotate_n(
        _mirror_lr(base),
        detail_rng.randrange(4),
    )
    rival_options = _same_bbox_rivals(legend)
    same_bbox_rival = rival_options[detail_rng.randrange(len(rival_options))]

    grid = full_grid(height, width, 0)
    slots = _slot_rectangles(height, width)
    layout_rng = ctx.draw_rng(f"layout_{band_tag}")
    legend_slot = layout_rng.randrange(4)
    candidate_slots = [index for index in range(4) if index != legend_slot]
    candidate_slots.sort()
    target_physical_slot = candidate_slots[target_slot]
    other_physical_slots = [slot for slot in candidate_slots if slot != target_physical_slot]
    if layout_rng.randrange(2):
        other_physical_slots.reverse()

    _stamp_in_slot(grid, legend, 1, slots[legend_slot], layout_rng)
    _stamp_in_slot(grid, match, 2, slots[target_physical_slot], layout_rng)
    _stamp_in_slot(grid, mirrored, 2, slots[other_physical_slots[0]], layout_rng)
    _stamp_in_slot(grid, same_bbox_rival, 2, slots[other_physical_slots[1]], layout_rng)

    split_r = height // 2
    split_c = width // 2
    if noise_size == 1:
        noise_cells = ((split_r, split_c),)
    elif detail_rng.randrange(2):
        noise_cells = ((split_r, split_c - 1), (split_r, split_c))
    else:
        noise_cells = ((split_r - 1, split_c), (split_r, split_c))
    for row, col in noise_cells:
        grid[row][col] = int(noise_color)
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            min_r = min(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_r = max(r for r, _ in cells)
            max_c = max(c for _, c in cells)
            components.append(
                {
                    "color": color,
                    "cells": frozenset(cells),
                    "norm": _normalize(cells),
                    "size": len(cells),
                    "bbox": (min_r, min_c, max_r, max_c),
                    "height": max_r - min_r + 1,
                    "width": max_c - min_c + 1,
                }
            )
    return sorted(components, key=lambda item: item["bbox"][:2])


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    components = _components(grid)
    legends = [component for component in components if component["color"] == 1]
    reds = sorted(
        [component for component in components if component["color"] == 2],
        key=lambda item: item["bbox"][:2],
    )
    auxiliaries = [
        component for component in components if component["color"] not in (1, 2)
    ]
    legend = legends[0] if len(legends) == 1 else None
    matches: list[int] = []
    reflection_only: list[int] = []
    if legend is not None:
        rotations = _rotation_orbit(legend["norm"])
        dihedral = _dihedral_orbit(legend["norm"])
        matches = [i for i, candidate in enumerate(reds) if candidate["norm"] in rotations]
        reflection_only = [
            i
            for i, candidate in enumerate(reds)
            if candidate["norm"] in dihedral and candidate["norm"] not in rotations
        ]
    return {
        "components": components,
        "legends": legends,
        "legend": legend,
        "reds": reds,
        "auxiliaries": auxiliaries,
        "matches": matches,
        "reflection_only": reflection_only,
    }


def _different_colors_touch_orthogonally(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if nr < height and nc < width:
                    other = grid[nr][nc]
                    if other != 0 and other != color:
                        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural checker shared by canonical inputs and generated lessons."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]

    height = len(grid)
    errors: list[str] = []
    if not 10 <= height <= 12 or not 12 <= width <= 15:
        errors.append(f"canvas {height}x{width} outside 10..12 x 12..15")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors
    if any(8 in row for row in grid):
        errors.append("input color 8 is reserved for the output recolor")

    analysis = _analyze(grid)
    legends = analysis["legends"]
    reds = analysis["reds"]
    auxiliaries = analysis["auxiliaries"]
    if len(legends) != 1:
        errors.append(f"expected exactly one blue legend component, found {len(legends)}")
        return errors
    legend = legends[0]
    if legend["size"] not in (4, 5):
        errors.append(f"legend size must be 4 or 5 cells, found {legend['size']}")

    if len(reds) != 3:
        errors.append(f"expected exactly three red candidate components, found {len(reds)}")
    for index, candidate in enumerate(reds):
        if candidate["size"] not in (4, 5):
            errors.append(
                f"red candidate {index} size must be 4 or 5, found {candidate['size']}"
            )

    matches = analysis["matches"]
    if len(matches) != 1:
        errors.append(f"expected exactly one rotation-equivalent red candidate, found {len(matches)}")
    nonmatches = [candidate for i, candidate in enumerate(reds) if i not in matches]
    if not any(candidate["size"] == legend["size"] for candidate in nonmatches):
        errors.append("need a same-cell-count nonmatching red distractor")

    if len(auxiliaries) != 1:
        errors.append(f"expected exactly one auxiliary-color component, found {len(auxiliaries)}")
    elif auxiliaries[0]["color"] not in NOISE_COLORS:
        errors.append(f"unsupported auxiliary color {auxiliaries[0]['color']}")
    elif auxiliaries[0]["size"] not in (1, 2):
        errors.append(
            f"auxiliary marker size must be 1 or 2, found {auxiliaries[0]['size']}"
        )

    palette = {value for row in grid for value in row}
    if len(palette) != 4:
        errors.append(f"expected exactly four input colors, found {sorted(palette)}")
    if _different_colors_touch_orthogonally(grid):
        errors.append("different-colored components must not touch orthogonally")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic AXES value from the returned grid."""
    analysis = _analyze(grid)
    legend = analysis["legend"]
    if legend is None or len(analysis["matches"]) != 1 or len(analysis["auxiliaries"]) != 1:
        return {}
    legend_identity = _identify_shape(legend["norm"])
    match = analysis["reds"][analysis["matches"][0]]
    match_identity = _identify_shape(match["norm"])
    if legend_identity is None or match_identity is None:
        return {}
    shape_id, legend_rotation = legend_identity
    match_shape_id, absolute_match_rotation = match_identity
    if match_shape_id != shape_id:
        return {}
    auxiliary = analysis["auxiliaries"][0]
    return {
        "shape_id": shape_id,
        "legend_rotation": legend_rotation,
        "match_rotation": (absolute_match_rotation - legend_rotation) % 4,
        "target_slot": analysis["matches"][0],
        "noise_color": str(auxiliary["color"]),
        "noise_size": auxiliary["size"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold used by the semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    reasons: list[str] = []
    if (height, width) not in _CANONICAL_PROFILES:
        reasons.append(f"dimensions {height}x{width} are not a canonical profile")
    if len({value for row in grid for value in row}) != 4:
        reasons.append("canonical input palette contains exactly four colors")
    return reasons


def _official_output(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    analysis = _analyze(grid)
    for index in analysis["matches"]:
        for row, col in analysis["reds"][index]["cells"]:
            output[row][col] = 8
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python audit mirror; the canonical Racket program remains authority."""
    return _official_output(grid)


def _paint_selected(grid: list[list[int]], indices: Iterable[int]) -> list[list[int]]:
    output = [row[:] for row in grid]
    reds = _analyze(grid)["reds"]
    for index in indices:
        if 0 <= index < len(reds):
            for row, col in reds[index]["cells"]:
                output[row][col] = 8
    return output


def _rival_noop(grid):
    return [row[:] for row in grid]


def _rival_all_red(grid):
    return _paint_selected(grid, range(len(_analyze(grid)["reds"])))


def _rival_same_size(grid):
    analysis = _analyze(grid)
    legend = analysis["legend"]
    if legend is None:
        return [row[:] for row in grid]
    return _paint_selected(
        grid,
        [i for i, candidate in enumerate(analysis["reds"]) if candidate["size"] == legend["size"]],
    )


def _rival_exact_orientation(grid):
    analysis = _analyze(grid)
    legend = analysis["legend"]
    if legend is None:
        return [row[:] for row in grid]
    return _paint_selected(
        grid,
        [i for i, candidate in enumerate(analysis["reds"]) if candidate["norm"] == legend["norm"]],
    )


def _rival_allow_reflection(grid):
    analysis = _analyze(grid)
    legend = analysis["legend"]
    if legend is None:
        return [row[:] for row in grid]
    orbit = _dihedral_orbit(legend["norm"])
    return _paint_selected(
        grid,
        [i for i, candidate in enumerate(analysis["reds"]) if candidate["norm"] in orbit],
    )


def _rival_same_bbox(grid):
    analysis = _analyze(grid)
    legend = analysis["legend"]
    if legend is None:
        return [row[:] for row in grid]
    return _paint_selected(
        grid,
        [
            i
            for i, candidate in enumerate(analysis["reds"])
            if (candidate["height"], candidate["width"])
            == (legend["height"], legend["width"])
        ],
    )


def _rival_fixed_rank(rank: int) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _paint_selected(grid, (rank,))


SEMANTIC_RIVALS = {
    "leave_input_unchanged": _rival_noop,
    "recolor_all_red": _rival_all_red,
    "match_by_cell_count": _rival_same_size,
    "match_exact_orientation_only": _rival_exact_orientation,
    "allow_reflections": _rival_allow_reflection,
    "match_by_bbox": _rival_same_bbox,
    "always_candidate_rank_0": _rival_fixed_rank(0),
    "always_candidate_rank_1": _rival_fixed_rank(1),
    "always_candidate_rank_2": _rival_fixed_rank(2),
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _observed(grid, key, value) -> bool:
    return observe_overrides(grid).get(key) == value


def _has_reflection_control(grid) -> bool:
    return bool(_analyze(grid)["reflection_only"])


def _has_same_size_nonmatch(grid) -> bool:
    analysis = _analyze(grid)
    legend = analysis["legend"]
    match_set = set(analysis["matches"])
    return bool(
        legend
        and any(
            i not in match_set and candidate["size"] == legend["size"]
            for i, candidate in enumerate(analysis["reds"])
        )
    )


def _has_same_bbox_nonmatch(grid) -> bool:
    analysis = _analyze(grid)
    legend = analysis["legend"]
    match_set = set(analysis["matches"])
    return bool(
        legend
        and any(
            i not in match_set
            and (candidate["height"], candidate["width"])
            == (legend["height"], legend["width"])
            for i, candidate in enumerate(analysis["reds"])
        )
    )


SEMANTIC_WITNESSES = {
    "exact_orientation_match": lambda grid: _observed(grid, "match_rotation", 0),
    "quarter_turn_match": lambda grid: observe_overrides(grid).get("match_rotation") in (1, 3),
    "half_turn_match": lambda grid: _observed(grid, "match_rotation", 2),
    "reflection_only_control": _has_reflection_control,
    "same_size_nonmatch": _has_same_size_nonmatch,
    "same_bbox_nonmatch": _has_same_bbox_nonmatch,
    "target_rank_0": lambda grid: _observed(grid, "target_slot", 0),
    "target_rank_1": lambda grid: _observed(grid, "target_slot", 1),
    "target_rank_2": lambda grid: _observed(grid, "target_slot", 2),
    "one_cell_noise": lambda grid: _observed(grid, "noise_size", 1),
    "two_cell_noise": lambda grid: _observed(grid, "noise_size", 2),
}

WITNESS_RIVALS = {
    "quarter_turn_match": ["match_exact_orientation_only"],
    "half_turn_match": ["match_exact_orientation_only"],
    "reflection_only_control": ["allow_reflections"],
    "same_size_nonmatch": ["match_by_cell_count", "recolor_all_red"],
    "same_bbox_nonmatch": ["match_by_bbox"],
    "target_rank_0": ["always_candidate_rank_1", "always_candidate_rank_2"],
    "target_rank_1": ["always_candidate_rank_0", "always_candidate_rank_2"],
    "target_rank_2": ["always_candidate_rank_0", "always_candidate_rank_1"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if _official_output(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the rotation-match rule")
    if _official_output(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the rotation-match rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons
