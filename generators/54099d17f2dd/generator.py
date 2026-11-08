"""Constructive sampler for copying a color-2 template to a color-1 anchor.

The selected authority normalizes the sole color-2 component to bounding-box
coordinates and stamps those offsets in color 8 with the color-1 marker as the
new bounding-box top-left.  The output is a fresh blank grid: neither source
object nor marker survives.

The canonical demonstrations leave two especially plausible shortcuts alive:
(1) mirror the template whenever the marker lies left of the source, because
that canonical left-moving example is horizontally symmetric; and (2) copy
only four cells, because every canonical template is a tetromino.  The four-
example schedule below emits two leftward asymmetric five-cell witnesses in
every cycle, so both shortcuts are repeatedly falsified, including after any
one query is withheld from a five-pair lesson.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "54099d17f2dd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4a6409bfdf9a"

SUMMARY = (
    "A 0-background grid contains one connected color-2 template and one "
    "separate color-1 marker. Normalize the template to its bounding-box "
    "offsets, then on a fresh blank grid stamp exactly those offsets in color "
    "8 with the marker as the new bounding-box top-left. The source and marker "
    "vanish. Scheduled asymmetric five-cell leftward cases refute mirror-on-"
    "left and tetromino-only shortcuts that fit every canonical demonstration."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0; inputs use only colors 0, 1, and 2",
    "exactly one color-1 marker and one 4-connected color-2 template are present",
    "the normalized template is one of nine explicit connected 3..5-cell shapes",
    "the marker is in a strict quadrant from the source bounding-box top-left",
    "source, marker, and marker-anchored stamp fit with at least one background-cell gap",
]

_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "t4": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "s4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "z4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "i3": ((0, 0), (0, 1), (0, 2)),
    "l3": ((0, 0), (1, 0), (1, 1)),
    "zigzag5": ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    "long_l5": ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
}
_SHAPE_NAMES = tuple(_SHAPES)
_SHAPE_BY_OFFSETS = {offsets: name for name, offsets in _SHAPES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-prior or difficulty-aware 8..13",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-prior or difficulty-aware 10..16",
        "valid": "10..16",
    },
    "template_shape": {
        "type": "str",
        "default": "scheduled connected stencil",
        "valid": "l4|t4|s4|z4|square4|i3|l3|zigzag5|long_l5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "left_five_a",
    "right_tetromino",
    "left_five_b",
    "right_small",
)
_PROFILE_RELATION = {
    "left_five_a": "lower_left",
    "right_tetromino": "upper_right",
    "left_five_b": "upper_left",
    "right_small": "lower_right",
}
_PROFILE_SHAPES = {
    "left_five_a": ("zigzag5",),
    "right_tetromino": ("l4", "t4", "s4", "z4", "square4"),
    "left_five_b": ("long_l5",),
    "right_small": ("i3", "l3", "l4", "t4"),
}
_CANONICAL_DIMENSIONS = ((8, 12), (9, 12), (8, 13))
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Every four consecutive draws cover both canonical-fitting shortcuts."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _has_override(ctx: Any, name: str) -> bool:
    return name in ctx.overrides and ctx.overrides[name] is not None


def _draw_axis_int(
    ctx: Any,
    name: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    bounds = valid_bounds if _has_override(ctx, name) else default_bounds
    return ctx.draw_int_strict(name, *bounds)


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _translated(
    shape: tuple[tuple[int, int], ...], anchor: tuple[int, int]
) -> frozenset[tuple[int, int]]:
    r0, c0 = anchor
    return frozenset((r0 + dr, c0 + dc) for dr, dc in shape)


def _one_cell_gap(
    left: frozenset[tuple[int, int]], right: frozenset[tuple[int, int]]
) -> bool:
    return all(
        max(abs(lr - rr), abs(lc - rc)) > 1
        for lr, lc in left
        for rr, rc in right
    )


def _relation_ok(
    source: tuple[int, int], marker: tuple[int, int], relation: str
) -> bool:
    sr, sc = source
    mr, mc = marker
    return {
        "upper_left": mr < sr and mc < sc,
        "upper_right": mr < sr and mc > sc,
        "lower_left": mr > sr and mc < sc,
        "lower_right": mr > sr and mc > sc,
    }[relation]


@lru_cache(maxsize=256)
def _layout_candidates(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    relation: str,
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    """Enumerate all legal source/marker anchors; never use rejection loops."""
    sh, sw = _shape_size(shape)
    anchors = tuple(
        (r, c)
        for r in range(1, h - sh)
        for c in range(1, w - sw)
    )
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for source in anchors:
        source_cells = _translated(shape, source)
        for marker in anchors:
            if not _relation_ok(source, marker, relation):
                continue
            stamp_cells = _translated(shape, marker)
            marker_cell = frozenset({marker})
            if not _one_cell_gap(source_cells, marker_cell):
                continue
            if not _one_cell_gap(source_cells, stamp_cells):
                continue
            candidates.append((source, marker))
    return tuple(candidates)


def _dimension_defaults(ctx: Any, profile: str, difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if profile == "left_five_a":
        h, w = ctx.draw_rng("canonical_dimensions").choice(_CANONICAL_DIMENSIONS)
        return (h, h), (w, w)
    if difficulty == "easy":
        return (8, 9), (10, 12)
    if difficulty == "hard":
        return (11, 13), (13, 16)
    if difficulty == "medium":
        return (9, 11), (11, 14)
    return (8, 13), (10, 16)


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
    shape_override = overrides.get("template_shape")
    if shape_override is not None and type(shape_override) is not str:
        raise TypeError("template_shape override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    h_defaults, w_defaults = _dimension_defaults(ctx, profile, difficulty)
    h = _draw_axis_int(ctx, "grid_h", h_defaults, (8, 13))
    w = _draw_axis_int(ctx, "grid_w", w_defaults, (10, 16))

    shape_options = _SHAPE_NAMES if _has_override(ctx, "template_shape") else _PROFILE_SHAPES[profile]
    shape_name = ctx.draw_choice("template_shape", shape_options)
    shape = _SHAPES[shape_name]
    relation = _PROFILE_RELATION[profile]
    candidates = _layout_candidates(h, w, shape, relation)
    if not candidates:
        raise ValueError(
            f"no constructive layout for grid {h}x{w}, shape {shape_name}, relation {relation}"
        )
    source, marker = ctx.draw_rng("layout").choice(candidates)

    grid = full_grid(h, w, 0)
    for r, c in _translated(shape, source):
        grid[r][c] = 2
    grid[marker[0]][marker[1]] = 1

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"constructive generator emitted invalid grid: {findings}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "template_shape": shape_name}
    if observed != expected:
        raise RuntimeError(f"constructed axes disagree: expected {expected}, observed {observed}")
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not isinstance(grid[0], list) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _normalise(cells: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[tuple[int, int], ...]]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    offsets = tuple(sorted((r - r0, c - c0) for r, c in cells))
    return (r0, c0), offsets


def _connected(cells: list[tuple[int, int]]) -> bool:
    if not cells:
        return False
    unseen = set(cells)
    start = unseen.pop()
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS4:
            point = (r + dr, c + dc)
            if point in unseen:
                unseen.remove(point)
                queue.append(point)
    return not unseen


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    shape = _grid_shape(grid)
    if shape is None:
        return {}, ["grid must be a non-empty rectangular list of non-empty rows"]
    h, w = shape
    errors: list[str] = []
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"grid_h": h, "grid_w": w}, ["grid values must be integer ARC colours 0..9"]

    colours = {value for row in grid for value in row}
    illegal = sorted(colours - {0, 1, 2})
    if illegal:
        errors.append(f"input uses illegal colours {illegal}; expected only 0, 1, and 2")

    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    template = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-1 marker, found {len(markers)}")
    if not 3 <= len(template) <= 5:
        errors.append(f"expected 3..5 color-2 template cells, found {len(template)}")
    if template and not _connected(template):
        errors.append("color-2 template must be one 4-connected component")

    info: dict[str, Any] = {
        "grid_h": h,
        "grid_w": w,
        "markers": markers,
        "template_cells": tuple(sorted(template)),
    }
    if template:
        source, offsets = _normalise(template)
        info.update(
            source_anchor=source,
            offsets=offsets,
            template_shape=_SHAPE_BY_OFFSETS.get(offsets),
        )
        if offsets not in _SHAPE_BY_OFFSETS:
            errors.append(f"normalized template {offsets} is outside the declared shape bank")
    if len(markers) == 1 and template:
        marker = markers[0]
        source = info["source_anchor"]
        offsets = info["offsets"]
        info["marker"] = marker
        stamp = frozenset((marker[0] + dr, marker[1] + dc) for dr, dc in offsets)
        info["stamp_cells"] = stamp
        if any(not (0 <= r < h and 0 <= c < w) for r, c in stamp):
            errors.append("marker-anchored template stamp must fit inside the grid")
        source_cells = frozenset(template)
        if not _one_cell_gap(source_cells, frozenset({marker})):
            errors.append("marker must be separated from the source template by a background-cell gap")
        if stamp and not _one_cell_gap(source_cells, stamp):
            errors.append("marker-anchored stamp must be separated from the source by a background-cell gap")
        sr, sc = source
        mr, mc = marker
        if mr == sr or mc == sc:
            errors.append("marker must lie in a strict quadrant from the source top-left")
        else:
            info["relation"] = (
                ("upper" if mr < sr else "lower")
                + "_"
                + ("left" if mc < sc else "right")
            )
    return info, errors


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    info, errors = _analyse(grid)
    if not info:
        return errors
    if not 8 <= info["grid_h"] <= 13:
        errors.append(f"grid height must be 8..13, found {info['grid_h']}")
    if not 10 <= info["grid_w"] <= 16:
        errors.append(f"grid width must be 10..16, found {info['grid_w']}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """All structurally lawful samples belong to this task's rule manifold."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int | str]:
    info, errors = _analyse(grid)
    errors.extend(
        error for error in self_check(grid) if error not in errors
    )
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "template_shape": info["template_shape"],
    }


def _paint_offsets(
    h: int,
    w: int,
    marker: tuple[int, int],
    offsets: tuple[tuple[int, int], ...],
) -> list[list[int]]:
    output = full_grid(h, w, 0)
    for dr, dc in offsets:
        r, c = marker[0] + dr, marker[1] + dc
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError("marker-anchored template leaves the grid")
        output[r][c] = 8
    return output


def _valid_info(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    errors.extend(error for error in self_check(grid) if error not in errors)
    if errors:
        raise ValueError("; ".join(errors))
    return info


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected canonical Racket authority."""
    info = _valid_info(grid)
    return _paint_offsets(info["grid_h"], info["grid_w"], info["marker"], info["offsets"])


def _mirror_when_marker_left(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: reflect only leftward copies horizontally."""
    info = _valid_info(grid)
    offsets = info["offsets"]
    if info["marker"][1] < info["source_anchor"][1]:
        width = max(c for _, c in offsets)
        offsets = tuple(sorted((r, width - c) for r, c in offsets))
    return _paint_offsets(info["grid_h"], info["grid_w"], info["marker"], offsets)


def _copy_first_four_cells(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: assume every source is a tetromino."""
    info = _valid_info(grid)
    return _paint_offsets(
        info["grid_h"], info["grid_w"], info["marker"], info["offsets"][:4]
    )


def _left_asymmetric_witness(grid: Any) -> bool:
    try:
        info = _valid_info(grid)
    except (TypeError, ValueError):
        return False
    offsets = info["offsets"]
    width = max(c for _, c in offsets)
    mirrored = tuple(sorted((r, width - c) for r, c in offsets))
    return info["marker"][1] < info["source_anchor"][1] and mirrored != offsets


def _five_cell_witness(grid: Any) -> bool:
    try:
        return len(_valid_info(grid)["offsets"]) == 5
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "mirror_when_marker_left": _mirror_when_marker_left,
    "copy_first_four_cells": _copy_first_four_cells,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "leftward_asymmetric_template": _left_asymmetric_witness,
    "five_cell_template": _five_cell_witness,
}
WITNESS_RIVALS = {
    "leftward_asymmetric_template": ["mirror_when_marker_left"],
    "five_cell_template": ["copy_first_four_cells"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    del query
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survives = True
        for pair in demos:
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                return ["lesson demonstrations must contain input and output grids"]
            try:
                candidate = rival(pair["input"])
            except (TypeError, ValueError) as exc:
                return [f"invalid demonstration for {name}: {exc}"]
            if candidate != pair["output"]:
                survives = False
                break
        if survives:
            reasons.append(f"declared competitor {name} fits every demonstration")
    return reasons
