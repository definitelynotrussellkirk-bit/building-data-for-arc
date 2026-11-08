"""Generator for ARC task 97b3f59b5cc4 — keep border-touching objects.

Each nonzero, same-color 4-connected component is an object.  The output keeps
an object unchanged iff at least one of its cells touches the outer grid frame;
objects wholly in the interior are erased.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97b3f59b5cc4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e3401b50999e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Treat each same-color 4-connected nonzero component independently. "
    "Keep it in place when any cell touches the top, bottom, left, or right "
    "grid border; erase components that remain strictly inside the grid."
)

INVARIANTS = [
    "background is color 0",
    "ordinary draws contain at least one border-touching and one interior component",
    "component colors and positions are preserved by the rule",
    "different disconnected components may share a color",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "7..14"},
    "n_border": {"type": "int", "default": "scheduled 3", "valid": "1..4"},
    "n_interior": {"type": "int", "default": "scheduled 2", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Mutation fixtures only; deliberately excluded from the ordinary AXES domain.
DEGENERATE_TEXTURES = ("all_border", "all_interior", "empty")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORHOOD = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)

# Every ordinary slot lands exactly on one canonical (height, width, palette)
# profile.  Slots 1 and 3 deliberately reuse one color across opposite fates,
# so every contiguous three-example lesson refutes the global-color shortcut.
_PROFILE_DEFAULTS = (
    # The first three slots reproduce the canonical height/width/palette
    # profiles without replaying canonical grids. Slots 1 and 3 reuse one
    # color across opposite fates, so every contiguous three-example lesson
    # refutes the global-color shortcut.
    (5, 7, 2, 1, False),
    (6, 7, 2, 1, True),
    (6, 8, 2, 1, False),
    (7, 9, 3, 2, True),
)
_PROFILE_BORDER_SIDES = (
    ("top", "right"),
    ("left", "bottom"),
    ("top", "right"),
    ("right", "bottom", "left"),
)
_PROFILE_SIZES = (
    {"border": (3, 1), "interior": (4,)},
    {"border": (2, 1), "interior": (8,)},
    {"border": (3, 2), "interior": (6,)},
    {"border": (4, 3, 2), "interior": (5, 2)},
)

_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
    6: (
        tuple((r, c) for r in range(2) for c in range(3)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        tuple((r, c) for r in range(2) for c in range(4)),
    ),
    9: (tuple((r, c) for r in range(3) for c in range(3)),),
    10: (
        tuple((r, c) for r in range(2) for c in range(5)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
    ),
    11: (
        tuple((r, c) for r in range(3) for c in range(4) if (r, c) != (2, 3)),
    ),
    12: (
        tuple((r, c) for r in range(3) for c in range(4)),
        tuple(
            (r, c)
            for r in range(4)
            for c in range(4)
            if r in (0, 3) or c in (0, 3)
        ),
    ),
}


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Stable four-slot schedule; any contiguous 3-demo window is disambiguating."""
    del seed, difficulty
    return int(sample_index) % len(_PROFILE_DEFAULTS)


SCHEDULE_PROFILES = tuple(range(len(_PROFILE_DEFAULTS)))


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    transformed = list(cells)
    if code & 4:
        transformed = [(row, -col) for row, col in transformed]
    for _ in range(code & 3):
        transformed = [(col, -row) for row, col in transformed]
    return _normalize(transformed)


def _shape_options(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    options: list[tuple[tuple[int, int], ...]] = []
    for base in _BASE_SHAPES[size]:
        for code in range(8):
            shape = _transform(base, code)
            if shape not in options:
                options.append(shape)
    return tuple(options)


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _touched_sides(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[str]:
    sides: set[str] = set()
    for row, col in cells:
        if row == 0:
            sides.add("top")
        if row == h - 1:
            sides.add("bottom")
        if col == 0:
            sides.add("left")
        if col == w - 1:
            sides.add("right")
    return sides


def _candidate_placements(
    shape: tuple[tuple[int, int], ...],
    h: int,
    w: int,
    *,
    role: str,
    desired_side: str | None,
) -> list[tuple[tuple[int, int], ...]]:
    sh, sw = _shape_dims(shape)
    if sh > h or sw > w:
        return []
    exact: list[tuple[tuple[int, int], ...]] = []
    fallback: list[tuple[tuple[int, int], ...]] = []
    for top in range(h - sh + 1):
        for left in range(w - sw + 1):
            cells = tuple((top + row, left + col) for row, col in shape)
            sides = _touched_sides(cells, h, w)
            if role == "interior":
                if not sides:
                    fallback.append(cells)
                continue
            if not sides:
                continue
            fallback.append(cells)
            if desired_side is not None and sides == {desired_side}:
                exact.append(cells)
    return exact or fallback


def _separated(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for row, col in cells:
        if (row, col) in occupied:
            return False
        if any((row + dr, col + dc) in occupied for dr, dc in _NEIGHBORHOOD):
            return False
    return True


def _planned_size(
    profile: int,
    role: str,
    index: int,
    *,
    total: int,
    h: int,
    w: int,
) -> int:
    if total >= 7:
        return 1
    if total == 6:
        return 1 + ((index + (0 if role == "border" else 1)) % 2)
    planned = _PROFILE_SIZES[profile][role]
    size = planned[index] if index < len(planned) else 1 + (index % 4)
    if min(h, w) <= 9 and total >= 5:
        return min(size, 2)
    return int(size)


def _try_place_components(
    h: int,
    w: int,
    specs: list[dict[str, object]],
    ctx,
    difficulty: str | None,
) -> list[list[int]] | None:
    occupied: set[tuple[int, int]] = set()
    candidates: list[list[tuple[tuple[int, int], ...]]] = []
    band = difficulty or "none"

    for index, spec in enumerate(specs):
        shapes = list(_shape_options(int(spec["size"])))
        ctx.draw_rng(f"shape-order:{band}:{index}").shuffle(shapes)
        placements: list[tuple[tuple[int, int], ...]] = []
        for shape in shapes:
            placements.extend(
                _candidate_placements(
                    shape,
                    h,
                    w,
                    role=str(spec["role"]),
                    desired_side=(
                        str(spec["side"]) if isinstance(spec.get("side"), str) else None
                    ),
                )
            )
        if spec.get("requires_interior_cell"):
            placements = [
                cells
                for cells in placements
                if any(0 < row < h - 1 and 0 < col < w - 1 for row, col in cells)
            ]
        # Different transformed bases can yield the same absolute placement.
        placements = list(dict.fromkeys(placements))
        ctx.draw_rng(f"placement-order:{band}:{index}").shuffle(placements)
        candidates.append(placements)

    order = sorted(range(len(specs)), key=lambda idx: len(candidates[idx]))
    chosen: dict[int, tuple[tuple[int, int], ...]] = {}

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in candidates[index]:
            if not _separated(cells, occupied):
                continue
            occupied.update(cells)
            chosen[index] = cells
            if search(depth + 1):
                return True
            del chosen[index]
            occupied.difference_update(cells)
        return False

    if not search(0):
        return None

    grid = full_grid(h, w, 0)
    for index, spec in enumerate(specs):
        for row, col in chosen[index]:
            grid[row][col] = int(spec["color"])
    return grid


def _place_components(
    h: int,
    w: int,
    specs: list[dict[str, object]],
    ctx,
    difficulty: str | None,
) -> list[list[int]]:
    grid = _try_place_components(h, w, specs, ctx, difficulty)
    if grid is not None:
        return grid

    # Exact override corners can request eight objects on an 8x9 grid.  A
    # deterministic singleton fallback preserves every requested semantic axis
    # rather than silently dropping an object as the old generator did.
    compact = [dict(spec, size=1) for spec in specs]
    grid = _try_place_components(h, w, compact, ctx, difficulty)
    if grid is None:
        raise ValueError("could not realize all requested border/interior components")
    return grid


def _place_exact_override_components(
    h: int,
    w: int,
    specs: list[dict[str, object]],
) -> list[list[int]]:
    """Realize exact semantic axes in O(component-count) time.

    The override checker evaluates a large Cartesian matrix.  Search is useful
    for rich ordinary morphology, but exact axis probes only need an honest,
    deterministic realization.  These eight mutually separated singleton
    slots cover every declared boundary combination down to 8x9.
    """
    border_slots = ((0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0))
    interior_slots = ((1, 1), (1, w - 2), (h - 2, w - 2), (h - 2, 1))
    grid = full_grid(h, w, 0)
    border_index = 0
    interior_index = 0
    for spec in specs:
        if spec["role"] == "border":
            row, col = border_slots[border_index]
            border_index += 1
        else:
            row, col = interior_slots[interior_index]
            interior_index += 1
        grid[row][col] = int(spec["color"])
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 9, 0)
    if name == "all_border":
        for row, col in ((0, 1), (0, 2), (1, 1)):
            grid[row][col] = 3
        for row, col in ((7, 5), (7, 6), (6, 6)):
            grid[row][col] = 7
    elif name == "all_interior":
        for row, col in ((2, 2), (2, 3), (3, 2)):
            grid[row][col] = 3
        for row, col in ((5, 5), (5, 6), (6, 5)):
            grid[row][col] = 7
    elif name != "empty":
        raise ValueError(f"unknown texture fixture: {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture fixture: {texture!r}")
        conflicting = sorted(set(overrides) & set(AXES))
        if conflicting:
            raise ValueError(
                "texture fixture is incompatible with exact axes: " + ", ".join(conflicting)
            )
        return _draw_from_degenerate(str(texture))

    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_border, default_interior, shared_color = (
        _PROFILE_DEFAULTS[profile]
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", default_h, 5, 12)
    w = _scheduled_int(ctx, overrides, "grid_w", default_w, 7, 14)
    n_border = _scheduled_int(ctx, overrides, "n_border", default_border, 1, 4)
    n_interior = _scheduled_int(ctx, overrides, "n_interior", default_interior, 1, 4)

    total = n_border + n_interior
    unique_count = total - (1 if shared_color else 0)
    band = difficulty or "none"
    colors = ctx.draw_rng(f"palette:{band}").sample(list(_COLORS), unique_count)
    border_colors = colors[:n_border]
    if shared_color:
        interior_colors = [border_colors[0], *colors[n_border:]]
    else:
        interior_colors = colors[n_border:]

    sides = _PROFILE_BORDER_SIDES[profile]
    specs: list[dict[str, object]] = []
    for index in range(n_border):
        specs.append(
            {
                "role": "border",
                "color": border_colors[index],
                "side": sides[index % len(sides)],
                "size": _planned_size(
                    profile, "border", index, total=total, h=h, w=w
                ),
                "requires_interior_cell": index == 0,
            }
        )
    for index in range(n_interior):
        specs.append(
            {
                "role": "interior",
                "color": interior_colors[index],
                "side": None,
                "size": _planned_size(
                    profile, "interior", index, total=total, h=h, w=w
                ),
            }
        )
    if any(name in overrides and overrides[name] is not None for name in AXES):
        return _place_exact_override_components(h, w, specs)
    return _place_components(h, w, specs, ctx, difficulty)


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 12 or not 7 <= width <= 14:
        return ["grid dimensions must be within 5..12 rows and 7..14 columns"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for row0 in range(h):
        for col0 in range(w):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            cells = {(row0, col0)}
            seen.add((row0, col0))
            stack = [(row0, col0)]
            while stack:
                row, col = stack.pop()
                for dr, dc in _CARDINAL:
                    nr, nc = row + dr, col + dc
                    nxt = (nr, nc)
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        cells.add(nxt)
                        stack.append(nxt)
            sides = _touched_sides(cells, h, w)
            components.append(
                {
                    "color": int(color),
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "sides": tuple(sorted(sides)),
                    "touches_border": bool(sides),
                    "bbox": (
                        min(row for row, _ in cells),
                        min(col for _, col in cells),
                        max(row for row, _ in cells),
                        max(col for _, col in cells),
                    ),
                }
            )
    return components


def semantic_observables(grid) -> dict[str, object]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    components = _components(grid)
    border = [component for component in components if component["touches_border"]]
    interior = [component for component in components if not component["touches_border"]]
    return {
        "errors": [],
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "components": components,
        "n_components": len(components),
        "n_border": len(border),
        "n_interior": len(interior),
        "border_colors": tuple(sorted(int(component["color"]) for component in border)),
        "interior_colors": tuple(
            sorted(int(component["color"]) for component in interior)
        ),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError(str(facts["errors"][0]))
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "n_border": int(facts["n_border"]),
        "n_interior": int(facts["n_interior"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    components = list(facts["components"])
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    if not 2 <= len(components) <= 8:
        errors.append("ordinary scenes must contain 2..8 nonzero components")
    if not facts["n_border"]:
        errors.append("no nonzero component touches the grid border")
    if not facts["n_interior"]:
        errors.append("no fully interior nonzero component found")
    if any(not 1 <= int(component["size"]) <= 12 for component in components):
        errors.append("component sizes must be within 1..12 cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if not 3 <= int(facts["palette_size"]) <= 9:
        reasons.append("canonical-like scenes use 3..9 colors including background")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Independent parity aid; the canonical Racket rule remains authoritative."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    out = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        if component["touches_border"]:
            color = int(component["color"])
            for row, col in component["cells"]:
                out[row][col] = color
    return out


def _blank_like(grid) -> list[list[int]]:
    return full_grid(len(grid), len(grid[0]), 0)


def _keep_selected(
    grid, predicate: Callable[[dict[str, object]], bool]
) -> list[list[int]]:
    out = _blank_like(grid)
    for component in _components(grid):
        if predicate(component):
            for row, col in component["cells"]:
                out[row][col] = int(component["color"])
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _erase_all(grid):
    return _blank_like(grid)


def _top_border_only(grid):
    return _keep_selected(grid, lambda component: "top" in component["sides"])


def _edge_cells_only(grid):
    h, w = len(grid), len(grid[0])
    return [
        [value if (row in (0, h - 1) or col in (0, w - 1)) else 0
         for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]


def _keep_border_colors_globally(grid):
    border_colors = {
        int(component["color"])
        for component in _components(grid)
        if component["touches_border"]
    }
    return [
        [value if value in border_colors else 0 for value in row]
        for row in grid
    ]


SEMANTIC_RIVALS = {
    "identity": _identity,
    "erase_all": _erase_all,
    "top_border_only": _top_border_only,
    "edge_cells_only": _edge_cells_only,
    "keep_border_colors_globally": _keep_border_colors_globally,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "keep_border_colors_globally": _keep_border_colors_globally,
}


def _has_keep_and_erase(grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and bool(facts["n_border"])
        and bool(facts["n_interior"])
    )


def _has_non_top_border_survivor(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return False
    return any(
        component["touches_border"] and "top" not in component["sides"]
        for component in facts["components"]
    )


def _has_shared_color_opposite_fates(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return False
    return bool(set(facts["border_colors"]) & set(facts["interior_colors"]))


def _has_border_component_extending_inward(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        component["touches_border"]
        and any(0 < row < h - 1 and 0 < col < w - 1
                for row, col in component["cells"])
        for component in facts["components"]
    )


SEMANTIC_WITNESSES = {
    "keep_and_erase_both_fire": _has_keep_and_erase,
    "non_top_border_survivor": _has_non_top_border_survivor,
    "border_component_extends_inward": _has_border_component_extending_inward,
    "shared_color_opposite_fates": _has_shared_color_opposite_fates,
}
WITNESS_RIVALS = {
    "keep_and_erase_both_fire": ["identity", "erase_all"],
    "non_top_border_survivor": ["top_border_only"],
    "border_component_extends_inward": ["edge_cells_only"],
    "shared_color_opposite_fates": ["keep_border_colors_globally"],
}
