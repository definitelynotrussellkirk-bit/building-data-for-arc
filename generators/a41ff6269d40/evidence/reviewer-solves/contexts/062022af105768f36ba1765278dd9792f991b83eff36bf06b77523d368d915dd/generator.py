"""Generator for ``copy_the_template_to_anchors_with_reflection_controls``.

The input contains one connected color-4 template and three or four colored
anchor origins.  The selected Racket authority paints the normalized template
at every anchor on a blank output: color 1 uses the identity transform, color 2
uses a left-right reflection, and color 3 uses an up-down reflection.

Generated lessons deliberately contain all three roles and a template whose
three transformed forms are distinct.  Anchor stamp bounding boxes are placed
in disjoint quadrants, so another stamp cannot hide the pixels that distinguish
a role from a plausible shortcut.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a41ff6269d40"
TASK_ID = GENERATOR_ID
RULE_HASH = "9011a3cbeac9"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A connected color-4 template and 3-4 anchor origins occur on a zero "
    "background.  On a blank output, stamp the normalized template at every "
    "anchor: color 1 unchanged, color 2 reflected left-right, and color 3 "
    "reflected up-down.  Generated templates make all three transforms "
    "visibly distinct, and generated inputs contain every anchor role."
)

INVARIANTS = [
    "the color-4 template is one connected 4-7 cell polyomino",
    "generated templates differ from both axial reflections, which also differ from each other",
    "generated inputs contain 3-4 anchors and at least one anchor of each color 1, 2, and 3",
    "every transformed copy fits in-bounds and generated stamp bounding boxes are disjoint",
    "the selected rule outputs only color-4 stamps on a zero background",
]

AXES = {
    "grid_h": {"type": "int", "default": "12 in core; weighted 11..18 otherwise", "valid": "11..18"},
    "grid_w": {"type": "int", "default": "12 in core; weighted 11..18 otherwise", "valid": "11..18"},
    "template_cells": {"type": "int", "default": "4 in core; weighted 4..7 otherwise", "valid": "4..7"},
    "n_anchors": {"type": "int", "default": "3 in core; weighted 3..4 otherwise", "valid": "3..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
SCHEDULE_PROFILES = ("canonical_core", "broad")

_BOUNDS = {
    "grid_h": (11, 18),
    "grid_w": (11, 18),
    "template_cells": (4, 7),
    "n_anchors": (3, 4),
}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        raise ValueError("cannot normalize an empty shape")
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _flip_lr(shape: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    right = max(c for _, c in shape)
    return _normalize((r, right - c) for r, c in shape)


def _flip_ud(shape: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    bottom = max(r for r, _ in shape)
    return _normalize((bottom - r, c) for r, c in shape)


def _bbox(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


@lru_cache(maxsize=4)
def _asymmetric_polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate connected fixed polyominoes with a <=4x4 bounding box.

    Enumeration is finite (at most the fixed heptominoes), sorted before use,
    and therefore independent of Python hash iteration order.
    """
    shapes: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    for _ in range(1, size):
        grown: set[tuple[tuple[int, int], ...]] = set()
        for shape in shapes:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in _NEIGHBORS:
                    point = (r + dr, c + dc)
                    if point not in occupied:
                        grown.add(_normalize((*shape, point)))
        shapes = grown

    rich = []
    for shape in shapes:
        height, width = _bbox(shape)
        transforms = {shape, _flip_lr(shape), _flip_ud(shape)}
        if height <= 4 and width <= 4 and len(transforms) == 3:
            rich.append(shape)
    if not rich:
        raise RuntimeError(f"no asymmetric {size}-cell template is available")
    return tuple(sorted(rich))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """A two-step semantic schedule; seed is intentionally irrelevant here."""
    del seed, difficulty
    return "canonical_core" if sample_index % 2 == 0 else "broad"


def _validate_request(difficulty, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, overrides, name: str, choices: Sequence[int]) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(choices))


def _broad_choices(name: str, difficulty) -> tuple[int, ...]:
    lo, hi = _BOUNDS[name]
    full = tuple(range(lo, hi + 1))
    if name in ("grid_h", "grid_w"):
        favored = {
            "easy": (11, 11, 12, 12, 13),
            "medium": (12, 13, 14, 15),
            "hard": (15, 16, 17, 18, 18),
            None: (12, 13, 14, 15, 16),
        }[difficulty]
    elif name == "template_cells":
        favored = {
            "easy": (4, 4, 5),
            "medium": (4, 5, 6),
            "hard": (5, 6, 7, 7),
            None: (4, 5, 6, 7),
        }[difficulty]
    else:
        favored = {
            "easy": (3, 3, 3, 4),
            "medium": (3, 4),
            "hard": (3, 4, 4, 4),
            None: (3, 4),
        }[difficulty]
    return full + favored


def _quadrant_ranges(h: int, w: int, th: int, tw: int):
    top = (0, h // 2 - th)
    bottom = ((h + 1) // 2, h - th)
    left = (0, w // 2 - tw)
    right = ((w + 1) // 2, w - tw)
    ranges = (
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    )
    if any(rlo > rhi or clo > chi for (rlo, rhi), (clo, chi) in ranges):
        raise RuntimeError("grid cannot fit four disjoint template bounding boxes")
    return ranges


def _anchor_origins(ctx, h: int, w: int, shape, count: int):
    th, tw = _bbox(shape)
    ranges = _quadrant_ranges(h, w, th, tw)
    quadrant_rng = ctx.draw_rng("anchor_quadrants")
    quadrants = quadrant_rng.sample(range(4), count)
    position_rng = ctx.draw_rng("anchor_positions")
    origins = []
    for quadrant in quadrants:
        (rlo, rhi), (clo, chi) = ranges[quadrant]
        origins.append((position_rng.randint(rlo, rhi), position_rng.randint(clo, chi)))
    return origins


def _anchor_colors(ctx, count: int) -> list[int]:
    rng = ctx.draw_rng("anchor_colors")
    colors = [1, 2, 3]
    colors.extend(rng.choice((1, 2, 3)) for _ in range(count - 3))
    rng.shuffle(colors)
    return colors


def _template_origin(ctx, h: int, w: int, shape, anchors):
    th, tw = _bbox(shape)
    anchor_set = set(anchors)
    candidates = [
        (r, c)
        for r in range(h - th + 1)
        for c in range(w - tw + 1)
        if all((r + dr, c + dc) not in anchor_set for dr, dc in shape)
    ]
    if not candidates:
        raise RuntimeError("no source-template placement avoids the anchor origins")
    return ctx.draw_rng("template_position").choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    core = schedule_profile(seed, sample_index, difficulty) == "canonical_core"
    h = _draw_axis(ctx, overrides, "grid_h", (12,) if core else _broad_choices("grid_h", difficulty))
    w = _draw_axis(ctx, overrides, "grid_w", (12,) if core else _broad_choices("grid_w", difficulty))
    template_cells = _draw_axis(
        ctx,
        overrides,
        "template_cells",
        (4,) if core else _broad_choices("template_cells", difficulty),
    )
    n_anchors = _draw_axis(
        ctx,
        overrides,
        "n_anchors",
        (3,) if core else _broad_choices("n_anchors", difficulty),
    )

    shape = ctx.draw_rng("template_shape").choice(_asymmetric_polyominoes(template_cells))
    anchors = _anchor_origins(ctx, h, w, shape, n_anchors)
    colors = _anchor_colors(ctx, n_anchors)
    tr, tc = _template_origin(ctx, h, w, shape, anchors)

    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[tr + dr][tc + dc] = 4
    for (r, c), color in zip(anchors, colors):
        grid[r][c] = color
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid rows must have equal length"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be integers 0..9 (not bool)"]
    return []


def _positions(grid, colors: set[int]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in colors
    ]


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _NEIGHBORS:
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate lawful task inputs, including all selected-rule bounds."""
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 1, 2, 3, 4})
    if unexpected:
        errors.append(f"unexpected colors outside {{0,1,2,3,4}}: {unexpected}")

    template_cells = set(_positions(grid, {4}))
    anchors = [
        (r, c, grid[r][c])
        for r, c in _positions(grid, {1, 2, 3})
    ]
    if not template_cells:
        errors.append("no color-4 template cells found")
    elif not _connected(template_cells):
        errors.append("color-4 template must be one 4-connected shape")
    if not anchors:
        errors.append("no anchor cells (colors 1, 2, or 3) found")

    if template_cells and anchors:
        shape = _normalize(template_cells)
        th, tw = _bbox(shape)
        for r, c, color in anchors:
            if r + th > h or c + tw > w:
                errors.append(
                    f"color-{color} anchor at {(r, c)} clips the {th}x{tw} template bounding box"
                )
                break
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    template_cells = sum(value == 4 for row in grid for value in row)
    anchors = sum(value in (1, 2, 3) for row in grid for value in row)
    if not 11 <= h <= 18:
        errors.append(f"height {h} outside 11..18")
    if not 11 <= w <= 18:
        errors.append(f"width {w} outside 11..18")
    if not 4 <= template_cells <= 7:
        errors.append(f"template has {template_cells} cells outside 4..7")
    if not 3 <= anchors <= 4:
        errors.append(f"input has {anchors} anchors outside 3..4")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_cells": sum(value == 4 for row in grid for value in row),
        "n_anchors": sum(value in (1, 2, 3) for row in grid for value in row),
    }


def _template_shape(grid) -> tuple[tuple[int, int], ...]:
    return _normalize(_positions(grid, {4}))


def _solve_with_roles(grid, *, color2: str = "flip_lr", color3: str = "flip_ud"):
    shape = _template_shape(grid)
    transforms = {
        "identity": shape,
        "flip_lr": _flip_lr(shape),
        "flip_ud": _flip_ud(shape),
    }
    by_color = {1: transforms["identity"], 2: transforms[color2], 3: transforms[color3]}
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in by_color:
                continue
            for dr, dc in by_color[value]:
                out[r + dr][c + dc] = 4
    return out


def _selected_rule_mirror(grid):
    return _solve_with_roles(grid)


def _color2_is_identity(grid):
    """Plausible canonical-fitting shortcut: treat colors 1 and 2 alike."""
    return _solve_with_roles(grid, color2="identity")


def _color3_is_identity(grid):
    """Retained-audit rival: treat colors 1 and 3 alike."""
    return _solve_with_roles(grid, color3="identity")


def _horizontal_role_visible(grid) -> bool:
    return _selected_rule_mirror(grid) != _color2_is_identity(grid)


def _vertical_role_visible(grid) -> bool:
    return _selected_rule_mirror(grid) != _color3_is_identity(grid)


def _all_anchor_roles_present(grid) -> bool:
    return {value for row in grid for value in row if value in (1, 2, 3)} == {1, 2, 3}


SEMANTIC_WITNESSES = {
    "horizontal_role_visible": _horizontal_role_visible,
    "vertical_role_visible": _vertical_role_visible,
    "all_anchor_roles_present": _all_anchor_roles_present,
}
SEMANTIC_RIVALS = {
    "color2_is_identity": _color2_is_identity,
    "color3_is_identity": _color3_is_identity,
}
WITNESS_RIVALS = {
    "horizontal_role_visible": ["color2_is_identity"],
    "vertical_role_visible": ["color3_is_identity"],
}
BRANCH_WITNESSES = {"all_anchor_roles_present"}
CANONICAL_SHORTCUTS = {"color2_is_identity": _color2_is_identity}
LESSON_COMPETITORS = {
    "color2_is_identity": _color2_is_identity,
    "color3_is_identity": _color3_is_identity,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared rivals that fit all demonstrations but change the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but predicts a different query output"
                )
    return reasons
