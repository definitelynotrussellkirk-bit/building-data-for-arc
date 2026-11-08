"""Constructive sampler for recoloring border-touching components.

The selected Racket rule recolors each same-color 4-connected component to 7
when any cell touches the outer grid border.  This sampler deliberately varies
component shape, side, position, color reuse, and count.  Every generated grid
contains both a row-edge-only and a column-edge-only component, plus an interior
component sharing a color with a border component.  Those cases distinguish the
intended component rule from side-only and global-border-color shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7f31c4f794b2"
TASK_ID = GENERATOR_ID
RULE_HASH = "187a145d27eb"
VERSION = "3.0.0"
SUMMARY = (
    "8..14 by 8..14 zero-background grids with 2..3 border-touching and "
    "2..3 interior monochrome polyominoes of sizes 3..5. Shapes, colors, "
    "positions, and touched sides vary. Each sample includes a top/bottom-only "
    "component, a left/right-only component, and a border/interior color reuse "
    "that forces component-level reasoning. Border-touching components recolor "
    "to 7; interior components retain their colors."
)

INVARIANTS = [
    "background is 0 and input never contains output color 7",
    "4..6 same-color 4-connected polyominoes, each of size 3..5",
    "2..3 components touch the outer border and 2..3 remain interior",
    "a row-edge-only and a column-edge-only component occur in every generated input",
    "at least one color is reused by a border component and an interior component",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "weighted 8..14", "valid": "8..14"},
    "n_border_components": {"type": "int", "default": "weighted 2..3", "valid": "2..3"},
    "n_interior_components": {"type": "int", "default": "weighted 2..3", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

# Canonical component shapes (plus rotations/reflections): L triomino,
# zig-zag and T tetrominoes, and the V/W pentominoes seen in the source task.
_BASE_SHAPES = {
    "L3": ((0, 0), (1, 0), (1, 1)),
    "S4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "V5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "W5": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
}


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(cells):
    result = set()
    current = tuple(cells)
    for reflected in (False, True):
        transformed = tuple((r, -c if reflected else c) for r, c in current)
        for _ in range(4):
            result.add(_normalize(transformed))
            transformed = tuple((c, -r) for r, c in transformed)
    return tuple(sorted(result))


_SHAPE_VARIANTS = {name: _shape_variants(cells) for name, cells in _BASE_SHAPES.items()}
_ALLOWED_NORMALIZED_SHAPES = frozenset(
    variant for variants in _SHAPE_VARIANTS.values() for variant in variants
)


def _grid_diagnostics(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["ragged grid"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9")
                return None, errors
    return (len(grid), width), errors


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
            sides = set()
            if any(rr == 0 for rr, _ in cells):
                sides.add("top")
            if any(rr == h - 1 for rr, _ in cells):
                sides.add("bottom")
            if any(cc == 0 for _, cc in cells):
                sides.add("left")
            if any(cc == w - 1 for _, cc in cells):
                sides.add("right")
            result.append({"color": color, "cells": tuple(sorted(cells)), "sides": frozenset(sides)})
    return result


def _shape_key(cells):
    return _normalize(cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler grammar while still accepting all canonical inputs."""
    dims, errors = _grid_diagnostics(grid)
    if errors:
        return errors
    h, w = dims
    if not (8 <= h <= 14 and 8 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 8..14")
    flat = [value for row in grid for value in row]
    if 7 in flat:
        errors.append("input contains reserved output color 7")
    components = _components(grid)
    border = [obj for obj in components if obj["sides"]]
    interior = [obj for obj in components if not obj["sides"]]
    if not (2 <= len(border) <= 3):
        errors.append(f"expected 2..3 border components, found {len(border)}")
    if not (2 <= len(interior) <= 3):
        errors.append(f"expected 2..3 interior components, found {len(interior)}")
    colors = {obj["color"] for obj in components}
    if not (3 <= len(colors) <= 4):
        errors.append(f"expected 3..4 nonzero colors, found {len(colors)}")
    for index, obj in enumerate(components):
        size = len(obj["cells"])
        if not (3 <= size <= 5):
            errors.append(f"component {index} has size {size}, expected 3..5")
        elif _shape_key(obj["cells"]) not in _ALLOWED_NORMALIZED_SHAPES:
            errors.append(f"component {index} has unsupported polyomino shape")
    return errors


def strict_canonical_like(grid):
    """Recognize the canonical 8x8/10x10 profile and generated close variants."""
    dims, errors = _grid_diagnostics(grid)
    if errors:
        return errors
    h, w = dims
    if (h, w) not in {(8, 8), (10, 10)}:
        errors.append("dimensions are not a canonical 8x8 or 10x10 profile")
    flat = [value for row in grid for value in row]
    if 7 in flat:
        errors.append("input uses reserved output color 7")
    components = _components(grid)
    border = [obj for obj in components if obj["sides"]]
    interior = [obj for obj in components if not obj["sides"]]
    if not (4 <= len(components) <= 6):
        errors.append(f"expected 4..6 components, found {len(components)}")
    if not (2 <= len(border) <= 3 and 2 <= len(interior) <= 3):
        errors.append("canonical profile needs 2..3 border and 2..3 interior components")
    if len({value for value in flat if value != 0}) != 4:
        errors.append("canonical profile needs exactly four nonzero colors")
    for index, obj in enumerate(components):
        if not (3 <= len(obj["cells"]) <= 5):
            errors.append(f"component {index} size is outside 3..5")
        elif _shape_key(obj["cells"]) not in _ALLOWED_NORMALIZED_SHAPES:
            errors.append(f"component {index} shape is outside the canonical family")
    return errors


def observe_overrides(grid):
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_border_components": sum(bool(obj["sides"]) for obj in components),
        "n_interior_components": sum(not obj["sides"] for obj in components),
    }


def rule_mirror(grid):
    """Independent Python mirror of the selected authority, used by contracts/tests."""
    out = deepcopy(grid)
    for obj in _components(grid):
        if obj["sides"]:
            for r, c in obj["cells"]:
                out[r][c] = 7
    return out


def _paint_components(grid, predicate):
    out = deepcopy(grid)
    for obj in _components(grid):
        if predicate(obj):
            for r, c in obj["cells"]:
                out[r][c] = 7
    return out


def _rival_global_border_colors(grid):
    border_colors = {obj["color"] for obj in _components(grid) if obj["sides"]}
    return [[7 if value in border_colors else value for value in row] for row in grid]


def _rival_top_bottom_only(grid):
    return _paint_components(grid, lambda obj: bool(obj["sides"] & {"top", "bottom"}))


def _rival_left_right_only(grid):
    return _paint_components(grid, lambda obj: bool(obj["sides"] & {"left", "right"}))


def _rival_all_nonzero(grid):
    return [[7 if value else 0 for value in row] for row in grid]


def _shared_color_split(grid):
    components = _components(grid)
    border_colors = {obj["color"] for obj in components if obj["sides"]}
    interior_colors = {obj["color"] for obj in components if not obj["sides"]}
    return bool(border_colors & interior_colors)


def _horizontal_only_contact(grid):
    return any(
        obj["sides"] and obj["sides"] <= {"top", "bottom"}
        for obj in _components(grid)
    )


def _vertical_only_contact(grid):
    return any(
        obj["sides"] and obj["sides"] <= {"left", "right"}
        for obj in _components(grid)
    )


def _mixed_border_and_interior(grid):
    components = _components(grid)
    return any(obj["sides"] for obj in components) and any(not obj["sides"] for obj in components)


SEMANTIC_RIVALS = {
    "global_border_colors": _rival_global_border_colors,
    "top_bottom_only": _rival_top_bottom_only,
    "left_right_only": _rival_left_right_only,
    "all_nonzero": _rival_all_nonzero,
}
CANONICAL_SHORTCUTS = {"global_border_colors": _rival_global_border_colors}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "shared_color_split": _shared_color_split,
    "horizontal_only_contact": _horizontal_only_contact,
    "vertical_only_contact": _vertical_only_contact,
    "mixed_border_and_interior": _mixed_border_and_interior,
}
WITNESS_RIVALS = {
    "shared_color_split": ["global_border_colors"],
    "horizontal_only_contact": ["left_right_only"],
    "vertical_only_contact": ["top_bottom_only"],
    "mixed_border_and_interior": ["all_nonzero"],
}


def lesson_identifiable(demos, query):
    reasons = []
    query_input = query["input"]
    query_output = query.get("output", rule_mirror(query_input))
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query_input) != query_output:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons


def _touch_sides(cells, h, w):
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


@lru_cache(maxsize=4096)
def _placement_candidates(h, w, shape_name, role):
    candidates = []
    for shape in _SHAPE_VARIANTS[shape_name]:
        shape_h = 1 + max(r for r, _ in shape)
        shape_w = 1 + max(c for _, c in shape)
        for top in range(h - shape_h + 1):
            for left in range(w - shape_w + 1):
                cells = tuple(sorted((top + r, left + c) for r, c in shape))
                sides = _touch_sides(cells, h, w)
                if role == "horizontal" and sides and sides <= {"top", "bottom"}:
                    candidates.append(cells)
                elif role == "vertical" and sides and sides <= {"left", "right"}:
                    candidates.append(cells)
                elif role == "border" and sides:
                    candidates.append(cells)
                elif role == "interior" and not sides:
                    candidates.append(cells)
    return tuple(dict.fromkeys(candidates))


def _adjacent_to_color(cells, occupied_by_color):
    for r, c in cells:
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in occupied_by_color:
                return True
    return False


def _place_specs(h, w, specs, rng):
    candidate_lists = []
    for index, spec in enumerate(specs):
        candidates = list(_placement_candidates(h, w, spec["shape"], spec["role"]))
        local = rng.random()
        # Stable shuffle without touching process-global random state.
        keyed = sorted(candidates, key=lambda cells: (rng.random(), local, cells))
        candidate_lists.append(keyed)

    occupied = set()
    by_color = {}
    chosen = [None] * len(specs)
    attempts = 0

    def search(index):
        nonlocal attempts
        if index == len(specs):
            return True
        color = specs[index]["color"]
        same_color = by_color.setdefault(color, set())
        for cells in candidate_lists[index]:
            attempts += 1
            if attempts > 250_000:
                return False
            cell_set = set(cells)
            if cell_set & occupied or _adjacent_to_color(cells, same_color):
                continue
            occupied.update(cell_set)
            same_color.update(cell_set)
            chosen[index] = cells
            if search(index + 1):
                return True
            chosen[index] = None
            same_color.difference_update(cell_set)
            occupied.difference_update(cell_set)
        return False

    if not search(0):
        raise RuntimeError(
            f"constructive placement failed for {h}x{w} specs={[(s['role'], s['shape']) for s in specs]}"
        )
    return chosen


def _draw_axes(ctx):
    h_options = [8] * 8 + [10] * 8 + list(range(8, 15))
    h = ctx.draw_choice("grid_h", h_options)
    w_options = [h] * 20 + [8] * 4 + [10] * 4 + list(range(8, 15))
    w = ctx.draw_choice("grid_w", w_options)
    n_border = ctx.draw_choice("n_border_components", (2, 2, 2, 3))
    n_interior = ctx.draw_choice("n_interior_components", (2, 2, 3, 3))
    return h, w, n_border, n_interior


def _component_shapes(ctx, count, difficulty):
    if difficulty == "easy":
        options = ("L3", "L3", "S4", "T4", "V5")
    elif difficulty == "hard":
        options = ("L3", "S4", "V5", "V5", "W5", "W5")
    else:
        options = tuple(_BASE_SHAPES)
    shapes = [ctx.draw_rng(f"shape_{index}").choice(options) for index in range(count)]
    # Keep canonical object-size support in every draw without fixing which object carries it.
    shapes[ctx.draw_rng("size5_anchor").randrange(count)] = ctx.draw_rng("size5_kind").choice(("V5", "W5"))
    return shapes


def _component_colors(ctx, n_border, n_interior):
    count = n_border + n_interior
    n_colors = 3 if count == 4 else 4
    palette = ctx.draw_rng("palette").sample([1, 2, 3, 4, 5, 6, 8, 9], n_colors)
    colors = [None] * count
    colors[0] = palette[0]
    colors[n_border] = palette[0]
    remaining = [index for index, color in enumerate(colors) if color is None]
    for index, color in zip(remaining, palette[1:]):
        colors[index] = color
    fill_rng = ctx.draw_rng("repeat_colors")
    for index in remaining[len(palette) - 1 :]:
        colors[index] = fill_rng.choice(palette[1:])
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool/float/string)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_border, n_interior = _draw_axes(ctx)
    count = n_border + n_interior
    shapes = _component_shapes(ctx, count, difficulty)
    colors = _component_colors(ctx, n_border, n_interior)

    roles = ["horizontal", "vertical"] + ["border"] * (n_border - 2) + ["interior"] * n_interior
    specs = [
        {"role": role, "shape": shape, "color": color}
        for role, shape, color in zip(roles, shapes, colors)
    ]
    placements = _place_specs(h, w, specs, ctx.draw_rng("placements"))
    grid = full_grid(h, w, 0)
    for spec, cells in zip(specs, placements):
        for r, c in cells:
            if grid[r][c] != 0:
                raise RuntimeError("constructive placement overlap")
            grid[r][c] = spec["color"]

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"generated invalid grid: {errors}")
    return grid
