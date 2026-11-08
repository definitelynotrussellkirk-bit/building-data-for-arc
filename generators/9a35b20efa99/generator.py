"""Constructive sampler for the orbit-stamp-around-anchor task.

The input contains one color-9 anchor and one monochrome connected template.
The unchanged Racket authority crops the template and stamps, around the anchor,
the original, clockwise, 180-degree, and counter-clockwise variants.  This
module emits inputs only; ``rule_mirror`` is supplemental test evidence.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9a35b20efa99"
TASK_ID = GENERATOR_ID
RULE_HASH = "019ee1056dff"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "One color-9 anchor and one monochrome asymmetric connected template. "
    "Crop the template and stamp its 0/90/180/270-degree rotations in the "
    "upper-left, upper-right, lower-left, and lower-right anchor quadrants."
)

INVARIANTS = [
    "background is color 0 and exactly one anchor cell has color 9",
    "exactly one 4-connected monochrome template uses a color from 1..8",
    "the template is one of four asymmetric 3..6-cell curriculum shapes",
    "the anchor has enough margin that every stamped nonzero cell is in bounds",
    "the production schedule includes above, below, left, and right source placements",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot canonical-profile schedule",
        "valid": "13|15",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot canonical-profile schedule",
        "valid": "13|15|17",
    },
    "motif_color": {
        "type": "int",
        "default": "uniform 1..8",
        "valid": "1..8",
    },
    "motif_rotation": {
        "type": "int",
        "default": "uniform 0..3 clockwise quarter-turns",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_BASE_SHAPES = {
    "corner_l3": frozenset({(0, 0), (1, 0), (1, 1)}),
    "corner_l4": frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
    "branch5": frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)}),
    "blob6": frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0)}),
}

SCHEDULE_PROFILES = (
    "corner_l3_above",
    "branch5_below",
    "corner_l4_left",
    "blob6_right",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_PROFILE_CONFIG = {
    "corner_l3_above": ("corner_l3", "above", 13, 13),
    "branch5_below": ("branch5", "below", 15, 15),
    "corner_l4_left": ("corner_l4", "left", 13, 15),
    "blob6_right": ("blob6", "right", 15, 17),
}
_VALID_HEIGHTS = (13, 15)
_VALID_WIDTHS = (13, 15, 17)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic teaching role; every four consecutive samples cover all roles."""
    del seed
    if difficulty not in DIFFICULTY_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    index = (int(sample_index) + DIFFICULTY_OFFSETS[difficulty]) % LESSON_SCHEDULE_PERIOD
    return SCHEDULE_PROFILES[index]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in DIFFICULTY_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if name == "grid_h" and value not in _VALID_HEIGHTS:
            raise ValueError(f"grid_h must be one of {_VALID_HEIGHTS}")
        if name == "grid_w" and value not in _VALID_WIDTHS:
            raise ValueError(f"grid_w must be one of {_VALID_WIDTHS}")
        if name == "motif_color" and not 1 <= value <= 8:
            raise ValueError("motif_color must be in 1..8")
        if name == "motif_rotation" and not 0 <= value <= 3:
            raise ValueError("motif_rotation must be in 0..3")


def _scheduled_choice(ctx, label: str, options: Sequence[int], scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = set(cells)
    if not points:
        return frozenset()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return frozenset((r - min_r, c - min_c) for r, c in points)


def _rotate_cells_cw(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return _normalize_cells((c, -r) for r, c in cells)


def _rotated_cells(cells: Iterable[tuple[int, int]], turns: int) -> frozenset[tuple[int, int]]:
    result = _normalize_cells(cells)
    for _ in range(turns % 4):
        result = _rotate_cells_cw(result)
    return result


def _shape_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    return max(r for r, _ in points) + 1, max(c for _, c in points) + 1


@lru_cache(maxsize=256)
def _placement_options(
    height: int,
    width: int,
    shape_cells: tuple[tuple[int, int], ...],
    side: str,
) -> tuple[tuple[int, int, int, int], ...]:
    """Return all constructive (anchor_r, anchor_c, source_r, source_c) choices."""
    cells = frozenset(shape_cells)
    shape_h, shape_w = _shape_size(cells)
    max_dim = max(shape_h, shape_w)
    choices = []
    for anchor_r in range(max_dim + 1, height - max_dim):
        for anchor_c in range(max_dim + 1, width - max_dim):
            for source_r in range(height - shape_h + 1):
                for source_c in range(width - shape_w + 1):
                    if side == "above":
                        lawful = (
                            source_r + shape_h - 1 <= anchor_r - 2
                            and source_c <= anchor_c <= source_c + shape_w - 1
                        )
                    elif side == "below":
                        lawful = (
                            source_r >= anchor_r + 2
                            and source_c <= anchor_c <= source_c + shape_w - 1
                        )
                    elif side == "left":
                        lawful = (
                            source_c + shape_w - 1 <= anchor_c - 2
                            and source_r <= anchor_r <= source_r + shape_h - 1
                        )
                    elif side == "right":
                        lawful = (
                            source_c >= anchor_c + 2
                            and source_r <= anchor_r <= source_r + shape_h - 1
                        )
                    else:
                        raise ValueError(f"unknown schedule side {side!r}")
                    if lawful:
                        choices.append((anchor_r, anchor_c, source_r, source_c))
    return tuple(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    shape_kind, side, scheduled_h, scheduled_w = _PROFILE_CONFIG[profile]
    height = _scheduled_choice(ctx, "grid_h", _VALID_HEIGHTS, scheduled_h)
    width = _scheduled_choice(ctx, "grid_w", _VALID_WIDTHS, scheduled_w)
    motif_color = ctx.draw_int_strict("motif_color", 1, 8)
    motif_rotation = ctx.draw_int_strict("motif_rotation", 0, 3)
    cells = _rotated_cells(_BASE_SHAPES[shape_kind], motif_rotation)
    choices = _placement_options(height, width, tuple(sorted(cells)), side)
    if not choices:
        raise ValueError(
            f"no constructive placement for {profile} on {height}x{width} "
            f"with rotation {motif_rotation}"
        )
    anchor_r, anchor_c, source_r, source_c = ctx.draw_rng("placement").choice(choices)
    grid = full_grid(height, width, 0)
    grid[anchor_r][anchor_c] = 9
    for dr, dc in cells:
        grid[source_r + dr][source_c + dc] = motif_color
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid):
    errors = _grid_shape_errors(grid)
    if errors:
        return None, errors
    height, width = len(grid), len(grid[0])
    if height not in _VALID_HEIGHTS or width not in _VALID_WIDTHS:
        errors.append(
            f"dimensions {(height, width)} outside supported canonical profiles "
            f"{_VALID_HEIGHTS}x{_VALID_WIDTHS}"
        )
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, found {len(anchors)}")
    motif = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)]
    if not motif:
        errors.append("expected one non-{0,9} motif")
    colors = {value for _, _, value in motif}
    if any(not 1 <= value <= 8 for value in colors):
        errors.append("motif color must be in 1..8")
    if len(colors) != 1:
        errors.append(f"motif must be monochrome, found colors {sorted(colors)}")
    if errors:
        return None, errors

    cells = {(r, c) for r, c, _ in motif}
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    if seen != cells:
        errors.append("motif must be exactly one 4-connected component")

    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    local = _normalize_cells(cells)
    matches = []
    for name, base in _BASE_SHAPES.items():
        for turns in range(4):
            if local == _rotated_cells(base, turns):
                matches.append((name, turns))
    if len(matches) != 1:
        errors.append(f"motif is outside the declared four-shape manifold: {sorted(local)}")

    anchor_r, anchor_c = anchors[0]
    crop_h, crop_w = max_r - min_r + 1, max_c - min_c + 1
    local_variants = [local]
    for _ in range(3):
        local_variants.append(_rotate_cells_cw(local_variants[-1]))
    offsets = (
        (-crop_h - 1, -crop_w - 1),
        (-crop_h - 1, 1),
        (1, -crop_w - 1),
        (1, 1),
    )
    for variant, (dr, dc) in zip(local_variants, offsets):
        for r, c in variant:
            rr, cc = anchor_r + dr + r, anchor_c + dc + c
            if not (0 <= rr < height and 0 <= cc < width):
                errors.append("anchor margin would clip at least one stamped motif cell")
                break
        if errors and errors[-1].startswith("anchor margin"):
            break

    if errors:
        return None, errors
    return {
        "height": height,
        "width": width,
        "anchor": anchors[0],
        "motif_color": next(iter(colors)),
        "motif_cells": cells,
        "shape_kind": matches[0][0],
        "motif_rotation": matches[0][1],
        "bbox": (min_r, min_c, max_r, max_c),
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    if difficulty not in DIFFICULTY_OFFSETS:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    _info, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid):
    """Lawful instances in the declared task manifold, including all canonical pairs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError(f"cannot observe invalid grid: {errors[:2]}")
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "motif_color": info["motif_color"],
        "motif_rotation": info["motif_rotation"],
    }


def _rotate_grid_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_grid_180(grid):
    return _rotate_grid_cw(_rotate_grid_cw(grid))


def _rotate_grid_ccw(grid):
    return _rotate_grid_cw(_rotate_grid_180(grid))


def rule_mirror(grid):
    """Input-pure Python mirror for tests; Racket remains the label authority."""
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError(errors[0] if errors else "invalid grid")
    height, width = info["height"], info["width"]
    anchor_r, anchor_c = info["anchor"]
    min_r, min_c, max_r, max_c = info["bbox"]
    crop = [list(row[min_c : max_c + 1]) for row in grid[min_r : max_r + 1]]
    crop_h, crop_w = len(crop), len(crop[0])
    variants = (crop, _rotate_grid_cw(crop), _rotate_grid_180(crop), _rotate_grid_ccw(crop))
    offsets = (
        (-crop_h - 1, -crop_w - 1),
        (-crop_h - 1, 1),
        (1, -crop_w - 1),
        (1, 1),
    )
    out = full_grid(height, width, 0)
    out[anchor_r][anchor_c] = 9
    for variant, (dr, dc) in zip(variants, offsets):
        for r, row in enumerate(variant):
            for c, value in enumerate(row):
                if value:
                    out[anchor_r + dr + r][anchor_c + dc + c] = value
    return out


def _safe_input_copy(grid):
    try:
        return [list(row) for row in grid]
    except Exception:
        return grid


def _source_is_above(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(not errors and info is not None and info["bbox"][2] < info["anchor"][0])


def _is_corner_l(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(
        not errors
        and info is not None
        and info["shape_kind"] in {"corner_l3", "corner_l4"}
    )


def _above_only(grid):
    """Plausible canonical shortcut: apply the rule only to an upper template."""
    return rule_mirror(grid) if _source_is_above(grid) else _safe_input_copy(grid)


def _corner_l_only(grid):
    """Plausible canonical shortcut: apply the rule only to canonical corner-Ls."""
    return rule_mirror(grid) if _is_corner_l(grid) else _safe_input_copy(grid)


def _source_not_above(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(not errors and info is not None and not _source_is_above(grid))


def _non_corner_l(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(not errors and info is not None and not _is_corner_l(grid))


SEMANTIC_RIVALS: dict[str, Callable] = {
    "above_only": _above_only,
    "corner_l_only": _corner_l_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "source_not_above": _source_not_above,
    "non_corner_l": _non_corner_l,
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "source_not_above": ["above_only"],
    "non_corner_l": ["corner_l_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demonstrations that collectively refute both declared rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the orbit-stamp rule")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
