"""Constructive sampler for recoloring border-touching orange components.

The selected Racket authority finds same-color 4-connected objects, filters to
orange (7), and recolors an entire orange object green (3) when any of its cells
touches an outer grid border. Interior orange objects and all non-orange objects
remain unchanged.

The sampler deliberately includes both border and interior orange objects,
whole-object border witnesses, non-orange border distractors, varied sides,
multiple-border-object lessons, and exact canonical-scale profiles. These cases
separate the authority from common shortcuts such as recoloring every orange
cell, recoloring only edge cells, acting on every border object, or assuming
there can be only one border orange object.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d0a6f959321"
TASK_ID = GENERATOR_ID
RULE_HASH = "7af38e7dbf07"
VERSION = "3.0.0"
SUMMARY = (
    "Zero-background 7..12 by 9..14 grids contain 1..2 border-touching and "
    "1..2 interior orange(7) polyominoes plus 0..2 non-orange distractor "
    "objects. Recolor every whole border-touching orange component green(3); "
    "leave interior orange and all distractors unchanged."
)

INVARIANTS = [
    "background is 0 and input does not use reserved output color 3",
    "1..2 orange components touch the outer border and 1..2 remain interior",
    "orange components are 4-connected, separated, and contain 2..5 cells",
    "0..2 separated distractor components use colors outside {0,3,7}",
    "every border orange component extends inward so whole-component recoloring is visible",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical anchors plus broad profiles", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "scheduled canonical anchors plus broad profiles", "valid": "9..14"},
    "n_border_components": {"type": "int", "default": "cycle 1,2,2", "valid": "1..2"},
    "n_interior_components": {"type": "int", "default": "cycle 1,2,2,2", "valid": "1..2"},
    "n_distractors": {"type": "int", "default": "cycle 0,1,1,2", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.10

_CANONICAL_DIMENSIONS = ((8, 9), (9, 10), (7, 11), (10, 10), (8, 12))
_BROAD_DIMENSIONS = ((11, 13), (12, 14), (11, 14), (12, 13))
_SIDES = ("top", "right", "bottom", "left")
_DISTRACTOR_COLORS = (1, 2, 4, 5, 6, 8, 9)

_BASE_SHAPES = {
    "P1": ((0, 0),),
    "D2": ((0, 0), (0, 1)),
    "I3": ((0, 0), (0, 1), (0, 2)),
    "L3": ((0, 0), (1, 0), (1, 1)),
    "S4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "V5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    result = set()
    source = tuple(cells)
    for reflected in (False, True):
        transformed = tuple((r, -c if reflected else c) for r, c in source)
        for _ in range(4):
            result.add(_normalize(transformed))
            transformed = tuple((c, -r) for r, c in transformed)
    return tuple(sorted(result))


_SHAPE_VARIANTS = {
    name: _shape_variants(cells) for name, cells in _BASE_SHAPES.items()
}
_ALLOWED_ORANGE_SHAPES = frozenset(
    variant
    for name, variants in _SHAPE_VARIANTS.items()
    if name not in {"P1"}
    for variant in variants
)
_ALLOWED_DISTRACTOR_SHAPES = frozenset(
    variant
    for name, variants in _SHAPE_VARIANTS.items()
    if name in {"P1", "D2", "L3"}
    for variant in variants
)


def _grid_diagnostics(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return None, [f"cell ({r},{c}) must be an integer color 0..9"]
    return (len(grid), width), []


def _touch_sides(cells: Iterable[tuple[int, int]], h: int, w: int) -> frozenset[str]:
    cells = tuple(cells)
    sides = set()
    if any(r == 0 for r, _ in cells):
        sides.add("top")
    if any(r == h - 1 for r, _ in cells):
        sides.add("bottom")
    if any(c == 0 for _, c in cells):
        sides.add("left")
    if any(c == w - 1 for _, c in cells):
        sides.add("right")
    return frozenset(sides)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            frozen = frozenset(cells)
            result.append(
                {
                    "color": color,
                    "cells": frozen,
                    "sides": _touch_sides(frozen, h, w),
                    "shape": _normalize(frozen),
                }
            )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generated grammar while accepting every canonical input."""
    dims, errors = _grid_diagnostics(grid)
    if errors:
        return errors
    h, w = dims
    if not (7 <= h <= 12 and 9 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 7..12 by 9..14")
    flat = [value for row in grid for value in row]
    if 3 in flat:
        errors.append("input uses reserved output color 3")
    if 0 not in flat:
        errors.append("input has no background cells")

    components = _components(grid)
    orange = [obj for obj in components if obj["color"] == 7]
    border = [obj for obj in orange if obj["sides"]]
    interior = [obj for obj in orange if not obj["sides"]]
    distractors = [obj for obj in components if obj["color"] != 7]

    if not (1 <= len(border) <= 2):
        errors.append(f"expected 1..2 border orange components, found {len(border)}")
    if not (1 <= len(interior) <= 2):
        errors.append(f"expected 1..2 interior orange components, found {len(interior)}")
    if not (0 <= len(distractors) <= 2):
        errors.append(f"expected 0..2 distractor components, found {len(distractors)}")

    for index, obj in enumerate(orange):
        size = len(obj["cells"])
        if not (2 <= size <= 5):
            errors.append(f"orange component {index} has size {size}, expected 2..5")
        elif obj["shape"] not in _ALLOWED_ORANGE_SHAPES:
            errors.append(f"orange component {index} has unsupported shape")
    for index, obj in enumerate(distractors):
        if obj["color"] in {0, 3, 7}:
            errors.append(f"distractor component {index} uses reserved color {obj['color']}")
        size = len(obj["cells"])
        if not (1 <= size <= 3):
            errors.append(f"distractor component {index} has size {size}, expected 1..3")
        elif obj["shape"] not in _ALLOWED_DISTRACTOR_SHAPES:
            errors.append(f"distractor component {index} has unsupported shape")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical scale/palette manifold and close task variants."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]))
    if profile not in _CANONICAL_DIMENSIONS:
        reasons.append(f"dimensions {profile[0]}x{profile[1]} are outside canonical profiles")
    palette_size = len({value for row in grid for value in row})
    if palette_size != 3:
        reasons.append(f"canonical profile uses 3 colors including background, found {palette_size}")
    orange = [obj for obj in _components(grid) if obj["color"] == 7]
    if not (3 <= len(orange) <= 4):
        reasons.append(f"canonical-like profile needs 3..4 orange components, found {len(orange)}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    components = _components(grid)
    orange = [obj for obj in components if obj["color"] == 7]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border_components": sum(bool(obj["sides"]) for obj in orange),
        "n_interior_components": sum(not obj["sides"] for obj in orange),
        "n_distractors": sum(obj["color"] != 7 for obj in components),
    }


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    out = deepcopy(grid)
    for obj in _components(grid):
        if obj["color"] == 7 and obj["sides"]:
            for r, c in obj["cells"]:
                out[r][c] = 3
    return out


def _paint_components(grid, predicate):
    out = deepcopy(grid)
    for obj in _components(grid):
        if predicate(obj):
            for r, c in obj["cells"]:
                out[r][c] = 3
    return out


def _rival_recolor_all_orange(grid):
    return [[3 if value == 7 else value for value in row] for row in grid]


def _rival_border_cells_only(grid):
    h, w = len(grid), len(grid[0])
    return [
        [
            3 if value == 7 and (r in (0, h - 1) or c in (0, w - 1)) else value
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _rival_single_border_component(grid):
    out = deepcopy(grid)
    for obj in _components(grid):
        if obj["color"] == 7 and obj["sides"]:
            for r, c in obj["cells"]:
                out[r][c] = 3
            break
    return out


def _rival_all_border_objects(grid):
    return _paint_components(grid, lambda obj: bool(obj["sides"]))


def _rival_horizontal_edges_only(grid):
    return _paint_components(
        grid,
        lambda obj: obj["color"] == 7 and bool(obj["sides"] & {"top", "bottom"}),
    )


def _rival_vertical_edges_only(grid):
    return _paint_components(
        grid,
        lambda obj: obj["color"] == 7 and bool(obj["sides"] & {"left", "right"}),
    )


def _mixed_orange_status(grid) -> bool:
    orange = [obj for obj in _components(grid) if obj["color"] == 7]
    return any(obj["sides"] for obj in orange) and any(not obj["sides"] for obj in orange)


def _whole_component_extension(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        obj["color"] == 7
        and obj["sides"]
        and any(0 < r < h - 1 and 0 < c < w - 1 for r, c in obj["cells"])
        for obj in _components(grid)
    )


def _multiple_border_orange(grid) -> bool:
    return sum(obj["color"] == 7 and bool(obj["sides"]) for obj in _components(grid)) >= 2


def _border_distractor(grid) -> bool:
    return any(obj["color"] != 7 and obj["sides"] for obj in _components(grid))


def _horizontal_only_orange(grid) -> bool:
    return any(
        obj["color"] == 7 and obj["sides"] and obj["sides"] <= {"top", "bottom"}
        for obj in _components(grid)
    )


def _vertical_only_orange(grid) -> bool:
    return any(
        obj["color"] == 7 and obj["sides"] and obj["sides"] <= {"left", "right"}
        for obj in _components(grid)
    )


SEMANTIC_RIVALS = {
    "recolor_all_orange": _rival_recolor_all_orange,
    "border_cells_only": _rival_border_cells_only,
    "single_border_component_only": _rival_single_border_component,
    "all_border_objects": _rival_all_border_objects,
    "horizontal_edges_only": _rival_horizontal_edges_only,
    "vertical_edges_only": _rival_vertical_edges_only,
}
CANONICAL_SHORTCUTS = {
    "single_border_component_only": _rival_single_border_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "mixed_orange_status": _mixed_orange_status,
    "whole_component_extension": _whole_component_extension,
    "multiple_border_orange": _multiple_border_orange,
    "border_distractor": _border_distractor,
    "horizontal_only_orange": _horizontal_only_orange,
    "vertical_only_orange": _vertical_only_orange,
}
WITNESS_RIVALS = {
    "mixed_orange_status": ["recolor_all_orange"],
    "whole_component_extension": ["border_cells_only"],
    "multiple_border_orange": ["single_border_component_only"],
    "border_distractor": ["all_border_objects"],
    "horizontal_only_orange": ["vertical_edges_only"],
    "vertical_only_orange": ["horizontal_edges_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    query_input = query["input"]
    query_output = query.get("output", rule_mirror(query_input))
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query_input) != query_output:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons


def _scheduled_axis(ctx, label: str, domain: tuple[int, ...], default: int, overrides) -> int:
    """Use a deterministic curriculum default while keeping every override exact."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, domain)
    return ctx.draw_choice(label, (default,))


def _axis_values(ctx, sample_index: int, overrides):
    if sample_index % 8 == 7:
        h_default, w_default = _BROAD_DIMENSIONS[(sample_index // 8) % len(_BROAD_DIMENSIONS)]
    else:
        h_default, w_default = _CANONICAL_DIMENSIONS[sample_index % len(_CANONICAL_DIMENSIONS)]
    border_default = (1, 2, 2)[sample_index % 3]
    interior_default = (1, 2, 2, 2)[sample_index % 4]
    distractor_default = (0, 1, 1, 2)[sample_index % 4]
    return (
        _scheduled_axis(ctx, "grid_h", tuple(range(7, 13)), h_default, overrides),
        _scheduled_axis(ctx, "grid_w", tuple(range(9, 15)), w_default, overrides),
        _scheduled_axis(ctx, "n_border_components", (1, 2), border_default, overrides),
        _scheduled_axis(ctx, "n_interior_components", (1, 2), interior_default, overrides),
        _scheduled_axis(ctx, "n_distractors", (0, 1, 2), distractor_default, overrides),
    )


@lru_cache(maxsize=8192)
def _placement_candidates(
    h: int,
    w: int,
    shape_name: str,
    role: str,
    require_extension: bool,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    candidates = []
    for shape in _SHAPE_VARIANTS[shape_name]:
        sh = 1 + max(r for r, _ in shape)
        sw = 1 + max(c for _, c in shape)
        for top in range(h - sh + 1):
            for left in range(w - sw + 1):
                cells = tuple(sorted((top + r, left + c) for r, c in shape))
                sides = _touch_sides(cells, h, w)
                role_ok = (
                    (role == "interior" and not sides)
                    or (role == "border" and bool(sides))
                    or (role in _SIDES and sides == frozenset({role}))
                )
                if not role_ok:
                    continue
                if require_extension and not any(
                    0 < r < h - 1 and 0 < c < w - 1 for r, c in cells
                ):
                    continue
                candidates.append(cells)
    return tuple(dict.fromkeys(candidates))


def _has_halo_collision(cells, occupied) -> bool:
    return any(
        (r + dr, c + dc) in occupied
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_specs(h, w, specs, rng):
    candidate_lists = []
    for spec in specs:
        candidates = list(
            _placement_candidates(
                h,
                w,
                spec["shape"],
                spec["role"],
                spec.get("require_extension", False),
            )
        )
        rng.shuffle(candidates)
        if not candidates:
            return None
        candidate_lists.append(candidates)

    order = sorted(range(len(specs)), key=lambda index: len(candidate_lists[index]))
    occupied = set()
    chosen = [None] * len(specs)
    attempts = 0

    def search(position):
        nonlocal attempts
        if position == len(order):
            return True
        index = order[position]
        for cells in candidate_lists[index]:
            attempts += 1
            if attempts > 350_000:
                return False
            if _has_halo_collision(cells, occupied):
                continue
            occupied.update(cells)
            chosen[index] = cells
            if search(position + 1):
                return True
            chosen[index] = None
            occupied.difference_update(cells)
        return False

    return chosen if search(0) else None


def _orange_shape_options(difficulty, *, dense: bool, border: bool):
    if dense:
        return ("L3", "L3", "I3") if border else ("D2", "L3", "I3")
    if difficulty == "easy":
        return ("L3", "L3", "I3") if border else ("D2", "L3", "I3")
    if difficulty == "hard":
        return ("L3", "T4", "S4", "V5") if border else ("L3", "S4", "T4", "V5")
    return ("L3", "I3", "T4", "S4") if border else ("D2", "L3", "I3", "S4", "T4")


def _build_specs(ctx, h, w, n_border, n_interior, n_distractors, attempt):
    dense = h * w <= 72 and n_border + n_interior + n_distractors >= 5
    base_side = ctx.sample_index % len(_SIDES)
    specs = []
    for index in range(n_border):
        rng = ctx.draw_rng(f"shape_border_{attempt}_{index}")
        specs.append(
            {
                "role": _SIDES[(base_side + index) % len(_SIDES)],
                "shape": rng.choice(_orange_shape_options(ctx.difficulty, dense=dense, border=True)),
                "color": 7,
                "require_extension": True,
            }
        )
    for index in range(n_interior):
        rng = ctx.draw_rng(f"shape_interior_{attempt}_{index}")
        specs.append(
            {
                "role": "interior",
                "shape": rng.choice(_orange_shape_options(ctx.difficulty, dense=dense, border=False)),
                "color": 7,
                "require_extension": False,
            }
        )

    colors = list(_DISTRACTOR_COLORS)
    ctx.draw_rng(f"distractor_colors_{attempt}").shuffle(colors)
    for index in range(n_distractors):
        rng = ctx.draw_rng(f"shape_distractor_{attempt}_{index}")
        specs.append(
            {
                "role": _SIDES[(base_side + 2) % len(_SIDES)] if index == 0 else "interior",
                "shape": rng.choice(("P1", "D2") if dense else ("P1", "D2", "L3")),
                "color": colors[index],
                "require_extension": False,
            }
        )
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool/float/string)")

    ranges = {
        "grid_h": (7, 12),
        "grid_w": (9, 14),
        "n_border_components": (1, 2),
        "n_interior_components": (1, 2),
        "n_distractors": (0, 2),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = ranges[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_border, n_interior, n_distractors = _axis_values(ctx, sample_index, overrides)

    for attempt in range(48):
        specs = _build_specs(
            ctx,
            h,
            w,
            n_border,
            n_interior,
            n_distractors,
            attempt,
        )
        placements = _place_specs(h, w, specs, ctx.draw_rng(f"placements_{attempt}"))
        if placements is None:
            continue
        grid = full_grid(h, w, 0)
        for spec, cells in zip(specs, placements):
            for r, c in cells:
                if grid[r][c] != 0:
                    raise RuntimeError("constructive placement overlap")
                grid[r][c] = spec["color"]
        errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
        if not errors:
            return grid
    raise RuntimeError(
        "could not construct the requested separated border/interior component profile"
    )
