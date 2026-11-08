"""Generator for ARC task 9de4ae27d0d0 — Border Survivors.

Every nonzero color forms a 4-connected component.  The output keeps exactly
those components touching at least one outer grid border and erases every
component wholly inside the grid.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9de4ae27d0d0"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e3401b50999e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Treat each same-color 4-connected nonzero component independently. Keep "
    "a component unchanged when any of its cells touches the top, bottom, "
    "left, or right grid border; erase every component wholly in the interior."
)

INVARIANTS = [
    "background is color 0 and every ordinary draw contains background cells",
    "ordinary draws contain at least one border-touching component and at least one interior component",
    "ordinary components are 4-connected, use distinct nonzero colors, and do not touch one another",
    "the output preserves all cells of every border-touching component and clears all interior-component cells",
]

# Every declared axis is exact and recoverable from the returned grid.  The
# sequential profile controls ordinary defaults, but overrides retain the full
# declared domain in every difficulty band.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8 or extended", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "scheduled 8 or extended", "valid": "8..12"},
    "n_border": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
    "n_interior": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# These are mutation fixtures only.  They are intentionally excluded from the
# ordinary AXES domain because they hide the keep-versus-erase contrast.
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_motifs")
HELPFUL_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORHOOD = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
_PROFILE_DEFAULTS = (
    (8, 8, 2, 2),
    (8, 8, 1, 2),
    (8, 8, 2, 2),
    (10, 11, 2, 1),
)
_PROFILE_BORDER_SIDES = (
    ("left", "bottom"),
    ("right", "left"),
    ("top", "bottom"),
    ("left", "right"),
)
_PROFILE_SIZES = (
    {"border": (2, 3), "interior": (4, 2)},
    {"border": (4, 2), "interior": (1, 3)},
    {"border": (1, 4), "interior": (3, 2)},
    {"border": (3, 2), "interior": (4, 1)},
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Stable four-slot lesson schedule; every 3-demo window sees 3 profiles."""
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
    bases = {
        1: (((0, 0),),),
        2: (((0, 0), (0, 1)),),
        3: (
            ((0, 0), (0, 1), (0, 2)),
            ((0, 0), (1, 0), (1, 1)),
        ),
        4: (
            ((0, 0), (0, 1), (1, 0), (1, 1)),
            ((0, 0), (1, 0), (2, 0), (2, 1)),
            ((0, 0), (0, 1), (1, 1), (1, 2)),
        ),
    }
    options: list[tuple[tuple[int, int], ...]] = []
    for base in bases[size]:
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
    exact_side: list[tuple[tuple[int, int], ...]] = []
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
                exact_side.append(cells)
    return exact_side or fallback


def _separated(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for row, col in cells:
        if (row, col) in occupied:
            return False
        if any((row + dr, col + dc) in occupied for dr, dc in _NEIGHBORHOOD):
            return False
    return True


def _component_size(profile: int, role: str, index: int, rng) -> int:
    planned = _PROFILE_SIZES[profile][role]
    if index < len(planned):
        return planned[index]
    return rng.randint(1, 4)


def _place_components(
    h: int,
    w: int,
    specs: list[dict[str, object]],
    ctx,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()

    candidates: list[list[tuple[tuple[int, int], ...]]] = []
    for index, spec in enumerate(specs):
        shape_rng = ctx.draw_rng(f"shape:{index}")
        shapes = list(_shape_options(int(spec["size"])))
        shape_rng.shuffle(shapes)
        placements: list[tuple[tuple[int, int], ...]] = []
        for shape in shapes:
            placements.extend(
                _candidate_placements(
                    shape,
                    h,
                    w,
                    role=str(spec["role"]),
                    desired_side=spec.get("side") if isinstance(spec.get("side"), str) else None,
                )
            )
        placement_rng = ctx.draw_rng(f"placement:{index}")
        placement_rng.shuffle(placements)
        candidates.append(placements)

    order = sorted(range(len(specs)), key=lambda index: len(candidates[index]))
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
        raise ValueError("could not realize a separated border/interior component layout")

    for index, spec in enumerate(specs):
        color = int(spec["color"])
        for row, col in chosen[index]:
            grid[row][col] = color
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 8, 0)
    if name == "all_border":
        for row, col in ((0, 1), (0, 2), (1, 1)):
            grid[row][col] = 4
        for row, col in ((7, 5), (7, 6)):
            grid[row][col] = 6
    elif name == "all_interior":
        for row, col in ((2, 2), (2, 3), (3, 2)):
            grid[row][col] = 4
        for row, col in ((5, 5), (5, 6), (6, 5)):
            grid[row][col] = 6
    elif name == "no_motifs":
        pass
    else:
        raise ValueError(f"unknown texture fixture: {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture fixture: {texture!r}")
        conflicting = sorted(set(overrides) & set(AXES))
        if conflicting:
            raise ValueError(
                "texture fixture is incompatible with exact axes: " + ", ".join(conflicting)
            )
        return _draw_from_degenerate(texture)

    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_border, default_interior = _PROFILE_DEFAULTS[profile]
    if profile == 3 and difficulty == "easy":
        default_h, default_w = 8, 8
    elif profile == 3 and difficulty == "hard":
        default_h, default_w = 12, 12

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _scheduled_int(ctx, overrides, "grid_h", default_h, 8, 12)
    w = _scheduled_int(ctx, overrides, "grid_w", default_w, 8, 12)
    n_border = _scheduled_int(ctx, overrides, "n_border", default_border, 1, 2)
    n_interior = _scheduled_int(ctx, overrides, "n_interior", default_interior, 1, 2)

    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(list(_COLORS), n_border + n_interior)
    size_rng = ctx.draw_rng("sizes")
    sides = _PROFILE_BORDER_SIDES[profile]
    specs: list[dict[str, object]] = []
    for index in range(n_border):
        specs.append(
            {
                "role": "border",
                "color": colors[index],
                "size": _component_size(profile, "border", index, size_rng),
                "side": sides[index % len(sides)],
            }
        )
    for index in range(n_interior):
        specs.append(
            {
                "role": "interior",
                "color": colors[n_border + index],
                "size": _component_size(profile, "interior", index, size_rng),
                "side": None,
            }
        )
    return _place_components(h, w, specs, ctx)


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed ARC 30x30"]
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
                    nxt = (row + dr, col + dc)
                    nr, nc = nxt
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
                    "color": color,
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
        "components": components,
        "n_components": len(components),
        "n_border": len(border),
        "n_interior": len(interior),
        "border_colors": tuple(sorted(int(component["color"]) for component in border)),
        "interior_colors": tuple(sorted(int(component["color"]) for component in interior)),
        "border_sizes": tuple(sorted(int(component["size"]) for component in border)),
        "interior_sizes": tuple(sorted(int(component["size"]) for component in interior)),
        "side_only_survivor": any(
            set(component["sides"]) in ({"left"}, {"right"}) for component in border
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
    if len(components) < 2:
        errors.append("at least two nonzero components are required")
    if not facts["n_border"]:
        errors.append("no nonzero component touches the grid border")
    if not facts["n_interior"]:
        errors.append("no fully interior nonzero component found")
    if len({component["color"] for component in components}) != len(components):
        errors.append("each component must use a distinct nonzero color")
    occupied = {
        cell: int(component["color"])
        for component in components
        for cell in component["cells"]
    }
    for (row, col), color in occupied.items():
        for dr, dc in _NEIGHBORHOOD:
            other = occupied.get((row + dr, col + dc))
            if other is not None and other != color:
                errors.append("different-color components must be spatially separated")
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if not 2 <= facts["n_components"] <= 4:
        reasons.append("canonical-like scenes contain 2..4 components")
    if not 8 <= len(grid) <= 12 or not 8 <= len(grid[0]) <= 12:
        reasons.append("lawful generated dimensions are 8..12")
    if not all(1 <= int(component["size"]) <= 5 for component in facts["components"]):
        reasons.append("canonical-like component sizes are 1..5")
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


def _keep_selected(grid, predicate: Callable[[dict[str, object]], bool]) -> list[list[int]]:
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


def _keep_largest(grid):
    components = _components(grid)
    largest = max(int(component["size"]) for component in components)
    return _keep_selected(grid, lambda component: int(component["size"]) == largest)


def _keep_smallest(grid):
    components = _components(grid)
    smallest = min(int(component["size"]) for component in components)
    return _keep_selected(grid, lambda component: int(component["size"]) == smallest)


def _keep_lowest_color(grid):
    components = _components(grid)
    lowest = min(int(component["color"]) for component in components)
    return _keep_selected(grid, lambda component: int(component["color"]) == lowest)


def _keep_top_half(grid):
    cutoff = len(grid) / 2
    return _keep_selected(grid, lambda component: int(component["bbox"][0]) < cutoff)


def _horizontal_borders_only(grid):
    return _keep_selected(
        grid,
        lambda component: bool(set(component["sides"]) & {"top", "bottom"}),
    )


SEMANTIC_RIVALS = {
    "identity": _identity,
    "erase_all": _erase_all,
    "keep_largest_component": _keep_largest,
    "keep_smallest_component": _keep_smallest,
    "keep_lowest_color": _keep_lowest_color,
    "keep_top_half": _keep_top_half,
    "horizontal_borders_only": _horizontal_borders_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "horizontal_borders_only": _horizontal_borders_only,
}


def _has_keep_and_erase(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and bool(facts["n_border"]) and bool(facts["n_interior"])


def _interior_largest(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors") or not facts["border_sizes"] or not facts["interior_sizes"]:
        return False
    return max(facts["interior_sizes"]) > max(facts["border_sizes"])


def _interior_smallest(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors") or not facts["border_sizes"] or not facts["interior_sizes"]:
        return False
    return min(facts["interior_sizes"]) < min(facts["border_sizes"])


def _multiple_survivor_colors(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and len(facts["border_colors"]) >= 2


def _side_only_survivor(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and bool(facts["side_only_survivor"])


def _survivor_below_midline(grid) -> bool:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return False
    return any(
        bool(component["touches_border"])
        and int(component["bbox"][0]) >= len(grid) / 2
        for component in facts["components"]
    )


SEMANTIC_WITNESSES = {
    "keep_and_erase_both_fire": _has_keep_and_erase,
    "largest_component_can_be_erased": _interior_largest,
    "smallest_component_can_be_erased": _interior_smallest,
    "multiple_survivor_colors": _multiple_survivor_colors,
    "left_or_right_only_survivor": _side_only_survivor,
    "survivor_below_midline": _survivor_below_midline,
}
WITNESS_RIVALS = {
    "keep_and_erase_both_fire": ["identity", "erase_all"],
    "largest_component_can_be_erased": ["keep_largest_component"],
    "smallest_component_can_be_erased": ["keep_smallest_component"],
    "multiple_survivor_colors": ["keep_lowest_color"],
    "left_or_right_only_survivor": ["horizontal_borders_only"],
    "survivor_below_midline": ["keep_top_half"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    validated: list[dict] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        malformed = self_check(pair["input"])
        if malformed:
            reasons.append(f"demo {index} malformed: {malformed[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with border filtering")
            continue
        validated.append(pair)

    malformed_query = self_check(query["input"])
    if malformed_query:
        reasons.append(f"query malformed: {malformed_query[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with border filtering")

    if reasons or len(validated) != len(demos):
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in validated):
            reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons
