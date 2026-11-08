"""Generator for selecting a legend-matched object and rotating it clockwise.

The nonzero cell at (0, 0) is a legend swatch.  After removing that swatch,
exactly one connected component has the same color.  The task output is that
component cropped to its bounding box and quarter-turned clockwise.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c425a7cc61c7"
VERSION = "3.0.0"
TASK_ID = "c425a7cc61c7"
RULE_HASH = "07f3dbff434c"
SUMMARY = (
    "A top-left color swatch selects one separated component; crop that "
    "component and rotate the crop 90 degrees clockwise."
)

INVARIANTS = [
    "background is integer color 0 and the top-left legend swatch is nonzero",
    "after removing the legend swatch, exactly one component has its color",
    "the selected component has 4-8 cells and a nontrivial clockwise rotation",
    "one or two separated distractor components use distinct nonzero colors",
    "all components are four-connected and separated by at least one cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw within 10..16",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw within 12..18",
        "valid": "12..18",
    },
    "n_distractors": {
        "type": "int",
        "default": "2",
        "valid": "1..2",
    },
    "target_cells": {
        "type": "int",
        "default": "difficulty-aware draw within 4..8",
        "valid": "4..8",
    },
    "target_profile": {
        "type": "str",
        "default": "feasible draw from wide|tall|square",
        "valid": "wide|tall|square",
    },
    "target_color": {
        "type": "color",
        "default": "rng nonzero color",
        "valid": "1..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AROUND = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _quarter_turn(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _connected(cells: frozenset[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(cells)


def _binary_crop(
    cells: tuple[tuple[int, int], ...], height: int, width: int
) -> list[list[int]]:
    result = full_grid(height, width, 0)
    for r, c in cells:
        result[r][c] = 1
    return result


@lru_cache(maxsize=None)
def _shape_bank(
    height: int,
    width: int,
    count: int,
    require_changed_turn: bool,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate small connected shapes with the requested exact bounding box."""
    if count < 1 or count > height * width:
        return ()
    universe = tuple((r, c) for r in range(height) for c in range(width))
    options: list[tuple[tuple[int, int], ...]] = []
    for candidate in combinations(universe, count):
        rows = {r for r, _ in candidate}
        cols = {c for _, c in candidate}
        if not ({0, height - 1} <= rows and {0, width - 1} <= cols):
            continue
        frozen = frozenset(candidate)
        if not _connected(frozen):
            continue
        if require_changed_turn:
            crop = _binary_crop(candidate, height, width)
            if _quarter_turn(crop) == crop:
                continue
        options.append(candidate)
    return tuple(options)


def _target_dimensions(profile: str, count: int) -> tuple[int, int]:
    if profile == "square":
        if count < 5:
            raise ValueError(
                "target_profile='square' is incompatible with target_cells=4; "
                "a connected non-no-op square lesson needs at least five cells"
            )
        return 3, 3
    if count <= 6:
        return (2, 3) if profile == "wide" else (3, 2)
    return (3, 4) if profile == "wide" else (4, 3)


def _distractor_dimensions(count: int, rng) -> tuple[int, int]:
    if count <= 6:
        choices = ((2, 3), (3, 2))
    else:
        # Keeping large distractors at height three makes every declared axis
        # combination feasible even on the 10x12 boundary canvas.
        choices = ((3, 4), (3, 4), (4, 3))
    return rng.choice(choices)


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _component_crop(
    cells: list[tuple[int, int]], color: int
) -> list[list[int]]:
    r0, c0, r1, c1 = _bbox(cells)
    result = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    for r, c in cells:
        result[r - r0][c - c0] = color
    return result


def _components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "bbox": _bbox(cells),
                    "size": len(cells),
                }
            )
    return result


def _analysis(grid) -> dict:
    errors: list[str] = []
    result = {
        "errors": errors,
        "grid_h": 0,
        "grid_w": 0,
        "n_distractors": 0,
        "target_cells": 0,
        "target_profile": None,
        "target_color": None,
        "target_bbox": None,
        "target_component": None,
        "distractor_components": [],
        "output": None,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty list of rows")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be non-empty sequences")
        return result
    h, w = len(grid), len(grid[0])
    result["grid_h"], result["grid_w"] = h, w
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"grid colors must be integer values 0..9; got {bad_values}")
        return result
    if not 10 <= h <= 16 or not 12 <= w <= 18:
        errors.append(f"grid dimensions must be within 10..16 by 12..18; got {h}x{w}")

    marker = grid[0][0]
    result["target_color"] = marker
    if marker == 0:
        errors.append("cell (0,0) must contain a nonzero legend color")
        return result
    for r, c in ((0, 1), (1, 0), (1, 1)):
        if r < h and c < w and grid[r][c] != 0:
            errors.append("the top-left legend swatch must be isolated from scene components")
            break

    scene = [list(row) for row in grid]
    scene[0][0] = 0
    parts = _components(scene)
    if not 2 <= len(parts) <= 3:
        errors.append(
            f"expected one selected component and 1-2 distractors; found {len(parts)} components"
        )

    part_colors = [part["color"] for part in parts]
    if len(set(part_colors)) != len(part_colors):
        errors.append("every scene component must use a distinct nonzero color")

    selected = [part for part in parts if part["color"] == marker]
    if len(selected) != 1:
        errors.append(
            f"expected exactly one component of legend color {marker}; found {len(selected)}"
        )
        return result
    target = selected[0]
    distractors = [part for part in parts if part is not target]
    result["target_component"] = target
    result["distractor_components"] = distractors
    result["n_distractors"] = len(distractors)
    result["target_cells"] = target["size"]
    result["target_bbox"] = target["bbox"]

    if not 1 <= len(distractors) <= 2:
        errors.append(f"expected 1-2 distractors; found {len(distractors)}")
    if not 4 <= target["size"] <= 8:
        errors.append(f"selected component must have 4-8 cells; found {target['size']}")
    tr0, tc0, tr1, tc1 = target["bbox"]
    th, tw = tr1 - tr0 + 1, tc1 - tc0 + 1
    if th < 2 or tw < 2:
        errors.append(f"selected component bounding box must be at least 2x2; got {th}x{tw}")
    profile = "wide" if tw > th else "tall" if th > tw else "square"
    result["target_profile"] = profile

    for part in distractors:
        if not 3 <= part["size"] <= 9:
            errors.append(
                f"distractor color {part['color']} must have 3-9 cells; found {part['size']}"
            )

    cell_owner: dict[tuple[int, int], int] = {}
    for index, part in enumerate(parts):
        for cell in part["cells"]:
            cell_owner[cell] = index
    touching_pair = None
    for cell, owner in cell_owner.items():
        r, c = cell
        for dr, dc in _AROUND:
            other = cell_owner.get((r + dr, c + dc))
            if other is not None and other != owner:
                touching_pair = (owner, other)
                break
        if touching_pair is not None:
            break
    if touching_pair is not None:
        errors.append("scene components must be separated by at least one background cell")

    crop = _component_crop(target["cells"], marker)
    turned = _quarter_turn(crop)
    result["output"] = turned
    if turned == crop:
        errors.append("selected component is rotationally symmetric, making the task a no-op")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, touching, or no-op lessons."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_distractors": analysis["n_distractors"],
        "target_cells": analysis["target_cells"],
        "target_profile": analysis["target_profile"],
        "target_color": analysis["target_color"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent validation mirror; the Racket program remains authoritative."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def _draw_int_axis(ctx, overrides, name, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _difficulty_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (10, 11), (12, 14), (4, 5)
    if difficulty == "medium":
        return (11, 14), (13, 16), (5, 7)
    if difficulty == "hard":
        return (13, 16), (15, 18), (7, 8)
    return (10, 16), (12, 18), (4, 8)


def _rectangles_conflict(
    left: tuple[int, int, int, int], right: tuple[int, int, int, int]
) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return not (
        lr1 + 1 < rr0
        or rr1 + 1 < lr0
        or lc1 + 1 < rc0
        or rc1 + 1 < lc0
    )


def _place_shapes(
    height: int,
    width: int,
    shapes: list[tuple[tuple[int, int], ...]],
    rng,
) -> list[tuple[int, int]] | None:
    dimensions = [
        (max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1)
        for shape in shapes
    ]
    candidate_lists: list[list[tuple[int, int, int, int]]] = []
    for shape_h, shape_w in dimensions:
        candidates = [
            (r0, c0, r0 + shape_h - 1, c0 + shape_w - 1)
            for r0 in range(2, height - shape_h + 1)
            for c0 in range(0, width - shape_w + 1)
        ]
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    chosen: list[tuple[int, int, int, int]] = []

    def search(index: int) -> bool:
        if index == len(candidate_lists):
            return True
        for candidate in candidate_lists[index]:
            if any(_rectangles_conflict(candidate, prior) for prior in chosen):
                continue
            chosen.append(candidate)
            if search(index + 1):
                return True
            chosen.pop()
        return False

    if not search(0):
        return None
    return [(r0, c0) for r0, c0, _, _ in chosen]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (h_lo, h_hi), (w_lo, w_hi), (cells_lo, cells_hi) = _difficulty_ranges(difficulty)
    height = _draw_int_axis(ctx, overrides, "grid_h", h_lo, h_hi, 10, 16)
    width = _draw_int_axis(ctx, overrides, "grid_w", w_lo, w_hi, 12, 18)

    requested_profile = overrides.get("target_profile")
    if overrides.get("target_cells") is not None:
        target_cells = ctx.draw_int("target_cells", 4, 8)
    else:
        feasible_lo = max(cells_lo, 5) if requested_profile == "square" else cells_lo
        target_cells = ctx.draw_int("target_cells", feasible_lo, cells_hi)

    if target_cells == 4 and requested_profile == "square":
        raise ValueError(
            "target_profile='square' is incompatible with target_cells=4; "
            "a connected non-no-op square lesson needs at least five cells"
        )
    feasible_profiles = ["wide", "tall"]
    if target_cells >= 5:
        feasible_profiles.append("square")
    target_profile = ctx.draw_choice("target_profile", feasible_profiles)

    if overrides.get("n_distractors") is not None:
        n_distractors = ctx.draw_int("n_distractors", 1, 2)
    else:
        n_distractors = ctx.draw_int("n_distractors", 2, 2)
    target_color = ctx.draw_color("target_color", exclude={0})
    distractor_colors = ctx.draw_distinct_colors(
        "distractor_colors", n=n_distractors, exclude={0, target_color}
    )

    target_h, target_w = _target_dimensions(target_profile, target_cells)
    target_options = _shape_bank(
        target_h, target_w, target_cells, True
    )
    if not target_options:
        raise ValueError(
            f"no non-degenerate target shape for profile={target_profile!r}, "
            f"target_cells={target_cells}"
        )
    shape_rng = ctx.draw_rng("shape_selection")
    target_shape = shape_rng.choice(target_options)

    # The first distractor ties target object size.  The second, when present,
    # has one extra cell, tying the total frequency of the target color once
    # the legend swatch is counted.  Thus neither size nor modal color selects
    # the answer in generated lessons.
    distractor_sizes = [target_cells]
    if n_distractors == 2:
        distractor_sizes.append(target_cells + 1)

    layout_rng = ctx.draw_rng("layout")
    for _ in range(64):
        distractor_shapes: list[tuple[tuple[int, int], ...]] = []
        for count in distractor_sizes:
            dh, dw = _distractor_dimensions(count, layout_rng)
            options = _shape_bank(dh, dw, count, False)
            if not options:
                break
            distractor_shapes.append(layout_rng.choice(options))
        if len(distractor_shapes) != n_distractors:
            continue
        shapes = [target_shape, *distractor_shapes]
        positions = _place_shapes(height, width, shapes, layout_rng)
        if positions is None:
            continue

        grid = full_grid(height, width, 0)
        grid[0][0] = target_color
        colors = [target_color, *distractor_colors]
        for shape, (r0, c0), color in zip(shapes, positions, colors):
            paint_at(grid, r0, c0, shape, color)

        analysis = _analysis(grid)
        if analysis["errors"]:
            continue
        observed = {
            "grid_h": analysis["grid_h"],
            "grid_w": analysis["grid_w"],
            "n_distractors": analysis["n_distractors"],
            "target_cells": analysis["target_cells"],
            "target_profile": analysis["target_profile"],
            "target_color": analysis["target_color"],
        }
        expected = {
            "grid_h": height,
            "grid_w": width,
            "n_distractors": n_distractors,
            "target_cells": target_cells,
            "target_profile": target_profile,
            "target_color": target_color,
        }
        if observed != expected:
            raise AssertionError(
                f"realized axis drift: expected {expected}, observed {observed}"
            )
        return grid

    raise AssertionError(
        "failed to place an unambiguous legend-selection lesson after 64 attempts"
    )
