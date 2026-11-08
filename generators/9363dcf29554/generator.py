"""Generator for ARC task fd096ab6 (template completion).

The blue background is color 1.  The unique largest foreground color is a
complete sparse template.  Every other foreground color is a proper fragment:
try all cells of that color together as one translated subset of the template;
when that fails, complete each 8-connected component independently.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9363dcf29554"
TASK_ID = "9363dcf29554"
RULE_HASH = "1f1739de6279"
VERSION = "4.0.0"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a blue (1) field, the unique most numerous foreground color is a "
    "complete sparse template. For each other color, first treat all of its "
    "cells as one translated fragment and complete that single template "
    "footprint. If the whole color cannot fit one footprint, split it into "
    "8-connected components and complete one footprint per component."
)

INVARIANTS = [
    "color 1 is the unique background and modal grid color",
    "the unique largest foreground color is a complete sparse template",
    "every other color is a proper translated subset of that template",
    "whole-color matching has priority over per-8-component fallback",
    "all inferred template footprints are in bounds and mutually unobstructed",
]

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]

BACKGROUND = 1
TEMPLATE_COLORS = tuple(range(2, 10))
BRANCH_MODES = ("merged", "fallback", "mixed")
TEMPLATE_FAMILIES = ("reference", "novel")
TEMPLATE_ZONES = ("top_left", "top_right", "center", "bottom_left", "bottom_right")

# The three exact canonical morphology profiles.  Keeping the profile linked
# avoids impossible independent dimension/palette/template-size overrides while
# still exposing every exact degree of freedom that is visible in the grid.
PROFILE_SPECS: dict[str, tuple[int, int, int]] = {
    "canonical_22": (22, 5, 6),
    "canonical_24": (24, 8, 6),
    "canonical_30": (30, 6, 9),
}
SCENE_PROFILES = ("canonical_22", "canonical_24", "canonical_30")
SCHEDULE_PROFILES = SCENE_PROFILES

# Exact shapes from the canonical 22x22, 24x24, and 30x30 examples.
REFERENCE_SHAPES: dict[int, Shape] = {
    5: ((0, 2), (0, 3), (1, 0), (1, 1), (2, 2)),
    6: ((0, 2), (1, 1), (1, 3), (2, 0), (2, 1), (2, 3)),
    8: ((0, 1), (0, 2), (0, 3), (1, 0), (1, 4), (2, 1), (3, 1), (3, 2)),
}

# Same task grammar, different sparse masks.  These are not rotations or
# reflections of the canonical masks, so a lesson cannot be solved by memorizing
# one fixed stencil.
NOVEL_SHAPES: dict[int, Shape] = {
    5: ((0, 0), (0, 1), (1, 2), (2, 2), (2, 3)),
    6: ((0, 0), (1, 0), (1, 1), (1, 3), (2, 2), (3, 2)),
    8: ((0, 0), (0, 1), (1, 1), (1, 3), (2, 2), (3, 0), (3, 1), (3, 2)),
}
SHAPES_BY_FAMILY = {
    "reference": REFERENCE_SHAPES,
    "novel": NOVEL_SHAPES,
}

_PROFILE_SCHEDULE = (
    "canonical_22",
    "canonical_24",
    "canonical_30",
    "canonical_22",
    "canonical_24",
)
_BRANCH_SCHEDULE = ("merged", "fallback", "mixed", "merged", "fallback")
_COLOR_SCHEDULE = (2, 3, 5, 6, 7, 8, 9, 4)
_ZONE_SCHEDULE = ("top_left", "bottom_right", "center", "top_right", "bottom_left")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-position schedule over all three canonical profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
    "template_color": {
        "type": "color",
        "default": "sample-index schedule over 2..9",
        "valid": "2..9",
    },
    "branch_mode": {
        "type": "str",
        "default": "five-position schedule covering merged, fallback, and mixed",
        "valid": "|".join(BRANCH_MODES),
    },
    "template_family": {
        "type": "str",
        "default": "alternates canonical reference and novel sparse masks",
        "valid": "|".join(TEMPLATE_FAMILIES),
    },
    "template_zone": {
        "type": "str",
        "default": "five-zone sample-index schedule",
        "valid": "|".join(TEMPLATE_ZONES),
    },
}

# Every Cartesian combination of the public axes is constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_ZONE_TO_SLOT = {
    "top_left": 0,
    "top_right": 2,
    "center": 4,
    "bottom_left": 6,
    "bottom_right": 8,
}


def _difficulty_offset(difficulty: Any) -> int:
    if difficulty is None:
        return 0
    if difficulty == "easy":
        return 0
    if difficulty == "medium":
        return 2
    if difficulty == "hard":
        return 4
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the declared profile residue used by the default curriculum."""
    del seed
    offset = _difficulty_offset(difficulty)
    return _PROFILE_SCHEDULE[(int(sample_index) + offset) % len(_PROFILE_SCHEDULE)]


def _default_axes(seed: int, sample_index: int, difficulty: Any) -> dict[str, Any]:
    offset = _difficulty_offset(difficulty)
    index = int(sample_index) + offset
    return {
        "scene_profile": schedule_profile(seed, sample_index, difficulty),
        "template_color": _COLOR_SCHEDULE[index % len(_COLOR_SCHEDULE)],
        "branch_mode": _BRANCH_SCHEDULE[index % len(_BRANCH_SCHEDULE)],
        "template_family": TEMPLATE_FAMILIES[index % len(TEMPLATE_FAMILIES)],
        "template_zone": _ZONE_SCHEDULE[(index + int(seed)) % len(_ZONE_SCHEDULE)],
    }


def _shape_bbox(shape: Iterable[Cell]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _normalize(cells: Iterable[Cell]) -> Shape:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _components8(cells: Iterable[Cell]) -> list[Shape]:
    remaining = set(cells)
    result: list[Shape] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in _DIRS8:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    result.sort(key=lambda component: component[0])
    return result


def _relative_origins(fragment: Iterable[Cell], template: Iterable[Cell]) -> tuple[Cell, ...]:
    fragment_cells = tuple(fragment)
    template_cells = tuple(template)
    template_set = set(template_cells)
    origins: set[Cell] = set()
    for fr, fc in fragment_cells:
        for tr, tc in template_cells:
            origin = (fr - tr, fc - tc)
            if all((r - origin[0], c - origin[1]) in template_set for r, c in fragment_cells):
                origins.add(origin)
    return tuple(sorted(origins))


@lru_cache(maxsize=None)
def _fragment_candidates(template: Shape, kind: str) -> tuple[Shape, ...]:
    candidates: list[Shape] = []
    n_cells = len(template)
    for size in range(2, n_cells):
        if kind == "fallback" and 2 * size >= n_cells:
            continue
        for subset in combinations(template, size):
            normalized = tuple(sorted(subset))
            if _relative_origins(normalized, template) != ((0, 0),):
                continue
            component_count = len(_components8(normalized))
            if kind in {"single", "fallback"} and component_count != 1:
                continue
            if kind == "merged" and component_count < 2:
                continue
            candidates.append(normalized)
    candidates.sort(key=lambda cells: (len(cells), cells))
    return tuple(candidates)


def _paint(grid: Grid, origin: Cell, cells: Iterable[Cell], color: int) -> None:
    row0, col0 = origin
    for dr, dc in cells:
        grid[row0 + dr][col0 + dc] = color


def _slot_anchors(size: int, shape: Shape) -> tuple[Cell, ...]:
    box_h, box_w = _shape_bbox(shape)
    row_starts = (1, (size - box_h) // 2, size - box_h - 1)
    col_starts = (1, (size - box_w) // 2, size - box_w - 1)
    anchors = tuple((row, col) for row in row_starts for col in col_starts)
    if len(set(anchors)) != 9:
        raise ValueError(f"profile {size} cannot provide nine distinct template slots")
    return anchors


def _partial_colors(rng: Any, template_color: int, palette_size: int) -> list[int]:
    count = palette_size - 2
    pool = [color for color in TEMPLATE_COLORS if color != template_color]
    chosen: list[int] = []
    # A non-yellow template always retains yellow as a fragment.  This makes
    # the canonical-fitting "yellow is always the template" shortcut visibly
    # false in generated lessons.
    if template_color != 4:
        chosen.append(4)
        pool.remove(4)
    chosen.extend(rng.sample(pool, count - len(chosen)))
    rng.shuffle(chosen)
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, override-exact template-completion input."""
    _difficulty_offset(difficulty)  # validate before any generation side effect
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    requested = {key: value for key, value in overrides.items() if value is not None}
    defaults = _default_axes(int(seed), int(sample_index), difficulty)
    effective = dict(defaults)
    effective.update(requested)
    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    template_color = ctx.draw_color("template_color", exclude=(0, 1))
    branch_mode = ctx.draw_choice("branch_mode", BRANCH_MODES)
    template_family = ctx.draw_choice("template_family", TEMPLATE_FAMILIES)
    template_zone = ctx.draw_choice("template_zone", TEMPLATE_ZONES)

    size, template_size, palette_size = PROFILE_SPECS[scene_profile]
    template = SHAPES_BY_FAMILY[template_family][template_size]
    rng = ctx.draw_rng("layout")
    partial_colors = _partial_colors(rng, template_color, palette_size)

    roles = ["single"] * len(partial_colors)
    if branch_mode == "merged":
        roles[0] = "merged"
    elif branch_mode == "fallback":
        roles[0] = "fallback"
    else:
        roles[0] = "merged"
        roles[1] = "fallback"

    candidates = {
        kind: _fragment_candidates(template, kind)
        for kind in ("single", "merged", "fallback")
    }
    missing = [kind for kind, values in candidates.items() if not values]
    if missing:
        raise ValueError(
            f"template family {template_family!r} size {template_size} has no "
            f"constructive fragment candidate(s) for {missing}"
        )

    anchors = _slot_anchors(size, template)
    template_slot = _ZONE_TO_SLOT[template_zone]
    available_slots = [slot for slot in range(9) if slot != template_slot]
    rng.shuffle(available_slots)

    needed_slots = 1 + len(partial_colors) + (1 if "fallback" in roles else 0)
    if needed_slots > len(anchors):
        raise ValueError(
            f"profile {scene_profile!r} needs {needed_slots} footprints but only 9 slots exist"
        )

    grid = full_grid(size, size, BACKGROUND)
    _paint(grid, anchors[template_slot], template, template_color)

    slot_cursor = 0
    for color, role in zip(partial_colors, roles):
        fragment = rng.choice(candidates[role])
        first_anchor = anchors[available_slots[slot_cursor]]
        slot_cursor += 1
        _paint(grid, first_anchor, fragment, color)
        if role == "fallback":
            second_fragment = rng.choice(candidates["fallback"])
            second_anchor = anchors[available_slots[slot_cursor]]
            slot_cursor += 1
            _paint(grid, second_anchor, second_fragment, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid template-completion scene: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": scene_profile,
        "template_color": template_color,
        "branch_mode": branch_mode,
        "template_family": template_family,
        "template_zone": template_zone,
    }
    if observed != expected:
        raise ValueError(f"override realization mismatch: expected {expected}, observed {observed}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) != width or len(grid) not in {22, 24, 30}:
        return [f"expected a canonical square size 22, 24, or 30; got {len(grid)}x{width}"]
    bad = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 1 <= value <= 9
    ]
    if bad:
        return [f"grid values must be integer ARC colors 1..9; found {bad[0]!r}"]
    return []


def _present_colors(grid: Grid) -> list[int]:
    result: list[int] = []
    for row in grid:
        for value in row:
            if value != BACKGROUND and value not in result:
                result.append(value)
    return result


def _positions_of(grid: Grid, color: int, *, reverse: bool = False) -> list[Cell]:
    positions = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    return list(reversed(positions)) if reverse else positions


def _ordered_origins(
    cells: Iterable[Cell], template_rel: Iterable[Cell], height: int, width: int
) -> list[Cell]:
    cell_list = list(cells)
    template_list = list(template_rel)
    template_set = set(template_list)
    origins: list[Cell] = []
    for cell_row, cell_col in cell_list:
        for temp_row, temp_col in template_list:
            origin = (cell_row - temp_row, cell_col - temp_col)
            if origin in origins:
                continue
            if not all(
                (row - origin[0], col - origin[1]) in template_set
                for row, col in cell_list
            ):
                continue
            if not all(
                0 <= origin[0] + dr < height and 0 <= origin[1] + dc < width
                for dr, dc in template_list
            ):
                continue
            origins.append(origin)
    return origins


def _family_for_shape(shape: Shape) -> str | None:
    for family, by_size in SHAPES_BY_FAMILY.items():
        if shape == by_size.get(len(shape)):
            return family
    return None


def _profile_for_signature(size: int, template_size: int, palette_size: int) -> str | None:
    for name, spec in PROFILE_SPECS.items():
        if spec == (size, template_size, palette_size):
            return name
    return None


def _zone_for_template(size: int, shape: Shape, origin: Cell) -> str | None:
    anchors = _slot_anchors(size, shape)
    for zone, slot in _ZONE_TO_SLOT.items():
        if anchors[slot] == origin:
            return zone
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    assert isinstance(grid, list)
    size = len(grid)
    colors = _present_colors(grid)
    if len(colors) < 3:
        return {"errors": [f"expected at least three foreground colors; found {colors}"]}

    counts = {color: len(_positions_of(grid, color)) for color in colors}
    background_count = sum(value == BACKGROUND for row in grid for value in row)
    if background_count <= max(counts.values()):
        errors.append("color 1 must be the unique modal background")

    largest = max(counts.values())
    largest_colors = [color for color in colors if counts[color] == largest]
    if len(largest_colors) != 1:
        errors.append(f"foreground template must have a unique largest color; tied {largest_colors}")
        return {"errors": errors}
    template_color = largest_colors[0]
    template_positions = _positions_of(grid, template_color, reverse=True)
    template_shape = _normalize(template_positions)
    template_size = len(template_shape)
    if template_size not in {5, 6, 8}:
        errors.append(f"template must contain 5, 6, or 8 cells; found {template_size}")
    template_family = _family_for_shape(template_shape)
    if template_family is None:
        errors.append(f"template mask is outside the reference/novel sparse-mask grammar: {template_shape}")

    palette_size = len(colors) + 1
    scene_profile = _profile_for_signature(size, template_size, palette_size)
    if scene_profile is None:
        errors.append(
            "dimensions/template-size/palette signature is not one of the three "
            f"canonical profiles: {(size, template_size, palette_size)}"
        )

    min_row = min(row for row, _ in template_positions)
    min_col = min(col for _, col in template_positions)
    template_origin = (min_row, min_col)
    template_zone = (
        _zone_for_template(size, template_shape, template_origin)
        if template_family is not None
        else None
    )

    # Match the canonical source's ordering: cells-of is reverse row-major and
    # tmpl-rel preserves that order after normalization.
    template_rel_ordered = tuple(
        (row - min_row, col - min_col) for row, col in template_positions
    )
    color_facts: dict[int, dict[str, Any]] = {}
    has_merged = False
    has_fallback = False
    max_missing = 0
    for color in colors:
        if color == template_color:
            continue
        cells = _positions_of(grid, color, reverse=True)
        if not 2 <= len(cells) < template_size:
            errors.append(
                f"fragment color {color} must have 2..{template_size - 1} cells; found {len(cells)}"
            )
            continue
        components = _components8(cells)
        whole_origins = _ordered_origins(cells, template_rel_ordered, size, size)
        selected: list[Cell] = []
        mode = "single"
        component_origin_counts: list[int] = []
        if whole_origins:
            selected = [whole_origins[0]]
            if len(components) > 1:
                mode = "merged"
                has_merged = True
        else:
            mode = "fallback"
            has_fallback = True
            if len(components) < 2:
                errors.append(
                    f"fragment color {color} fits no whole template and has only one 8-component"
                )
            for component in components:
                ordered_component = sorted(component, reverse=True)
                origins = _ordered_origins(
                    ordered_component, template_rel_ordered, size, size
                )
                component_origin_counts.append(len(origins))
                if not origins:
                    errors.append(
                        f"8-component {component} of color {color} fits no in-bounds template footprint"
                    )
                else:
                    selected.append(origins[0])

        for origin in selected:
            missing_here = 0
            for dr, dc in template_shape:
                value = grid[origin[0] + dr][origin[1] + dc]
                if value == BACKGROUND:
                    missing_here += 1
                elif value != color:
                    errors.append(
                        f"color {color} footprint at {origin} is obstructed by color {value}"
                    )
            if missing_here == 0:
                errors.append(f"color {color} footprint at {origin} is already complete")
            max_missing = max(max_missing, missing_here)

        color_facts[color] = {
            "cell_count": len(cells),
            "component_count": len(components),
            "whole_origin_count": len(whole_origins),
            "component_origin_counts": component_origin_counts,
            "selected_origins": selected,
            "mode": mode,
        }

    if has_merged and has_fallback:
        branch_mode = "mixed"
    elif has_merged:
        branch_mode = "merged"
    elif has_fallback:
        branch_mode = "fallback"
    else:
        branch_mode = "single_only"

    return {
        "errors": errors,
        "grid_size": size,
        "palette_size": palette_size,
        "colors": colors,
        "counts": counts,
        "background_count": background_count,
        "scene_profile": scene_profile,
        "template_color": template_color,
        "template_shape": template_shape,
        "template_size": template_size,
        "template_family": template_family,
        "template_origin": template_origin,
        "template_zone": template_zone,
        "template_sparse": _shape_bbox(template_shape)[0] * _shape_bbox(template_shape)[1] > template_size,
        "color_facts": color_facts,
        "branch_mode": branch_mode,
        "has_merged": has_merged,
        "has_fallback": has_fallback,
        "max_missing": max_missing,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the task grammar and reject shortcut-friendly impostors."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """All generated draws lie on one of the three exact canonical profiles."""
    facts = _analyze(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    if facts.get("scene_profile") not in SCENE_PROFILES:
        return [f"unlinked scene profile: {facts.get('scene_profile')!r}"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every public exact axis from the returned grid."""
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts["branch_mode"] not in BRANCH_MODES:
        raise ValueError(
            f"generated override grammar requires a merged/fallback branch, found {facts['branch_mode']!r}"
        )
    if facts["template_zone"] not in TEMPLATE_ZONES:
        raise ValueError("template is not in one of the five generated slot zones")
    return {
        "scene_profile": facts["scene_profile"],
        "template_color": facts["template_color"],
        "branch_mode": facts["branch_mode"],
        "template_family": facts["template_family"],
        "template_zone": facts["template_zone"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts.get("errors"):
        return {"errors": list(facts["errors"])}
    return {
        "errors": [],
        "scene_profile": facts["scene_profile"],
        "template_color": facts["template_color"],
        "branch_mode": facts["branch_mode"],
        "template_family": facts["template_family"],
        "template_zone": facts["template_zone"],
        "template_sparse": facts["template_sparse"],
        "has_merged": facts["has_merged"],
        "has_fallback": facts["has_fallback"],
        "max_missing": facts["max_missing"],
        "yellow_is_fragment": facts["template_color"] != 4 and 4 in facts["colors"],
    }


def _fill_template(
    out: Grid,
    origin: Cell,
    template_shape: Shape,
    color: int,
    *,
    mode: str = "shape",
) -> None:
    row0, col0 = origin
    if mode == "bbox":
        box_h, box_w = _shape_bbox(template_shape)
        cells: Iterable[Cell] = (
            (row, col) for row in range(box_h) for col in range(box_w)
        )
    else:
        cells = template_shape
    for dr, dc in cells:
        if out[row0 + dr][col0 + dc] == BACKGROUND:
            out[row0 + dr][col0 + dc] = color
            if mode == "one_missing":
                return


def _solve_with_template_color(
    grid: Grid,
    template_color: int,
    *,
    policy: str = "authoritative",
) -> Grid:
    out = [list(row) for row in grid]
    colors = _present_colors(grid)
    if template_color not in colors:
        return out
    height, width = len(grid), len(grid[0])
    template_positions = _positions_of(grid, template_color, reverse=True)
    if not template_positions:
        return out
    min_row = min(row for row, _ in template_positions)
    min_col = min(col for _, col in template_positions)
    template_rel_ordered = tuple(
        (row - min_row, col - min_col) for row, col in template_positions
    )
    template_shape = tuple(sorted(template_rel_ordered))

    for color in colors:
        if color == template_color:
            continue
        cells = _positions_of(grid, color, reverse=True)
        components = _components8(cells)
        if policy == "connected_only" and len(components) > 1:
            continue
        whole_origins = _ordered_origins(cells, template_rel_ordered, height, width)
        origins: list[Cell] = []
        if whole_origins:
            origins = [whole_origins[0]]
        elif policy not in {"merge_only", "connected_only"}:
            for component in components:
                component_origins = _ordered_origins(
                    sorted(component, reverse=True), template_rel_ordered, height, width
                )
                if component_origins:
                    origins.append(component_origins[0])
        for origin in origins:
            fill_mode = "shape"
            if policy == "bbox":
                fill_mode = "bbox"
            elif policy == "one_missing":
                fill_mode = "one_missing"
            _fill_template(out, origin, template_shape, color, mode=fill_mode)
    return out


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror for tests/rival audits; canonical Racket owns output."""
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("invalid template-completion input: " + "; ".join(facts["errors"]))
    return _solve_with_template_color(grid, int(facts["template_color"]))


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _rival_connected_fragments_only(grid: Grid) -> Grid:
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return _solve_with_template_color(
        grid, int(facts["template_color"]), policy="connected_only"
    )


def _rival_whole_color_only(grid: Grid) -> Grid:
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return _solve_with_template_color(
        grid, int(facts["template_color"]), policy="merge_only"
    )


def _rival_fixed_yellow_template(grid: Grid) -> Grid:
    return _solve_with_template_color(grid, 4)


def _rival_fill_bounding_box(grid: Grid) -> Grid:
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return _solve_with_template_color(grid, int(facts["template_color"]), policy="bbox")


def _rival_add_one_missing_cell(grid: Grid) -> Grid:
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return _solve_with_template_color(
        grid, int(facts["template_color"]), policy="one_missing"
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "connected fragments only": _rival_connected_fragments_only,
    "whole color only": _rival_whole_color_only,
    "yellow is always the template": _rival_fixed_yellow_template,
    "fill template bounding box": _rival_fill_bounding_box,
    "add only one missing cell": _rival_add_one_missing_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every real canonical pair uses yellow (4) as the largest template, so this
# shortcut exactly fits the visible source task. Generated non-yellow examples
# are necessary causal evidence that "largest" is the role, not "yellow".
CANONICAL_SHORTCUTS = {
    "yellow is always the template": _rival_fixed_yellow_template,
}


def _rival_differs(grid: Grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


def _witness_merged(grid: Grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and bool(facts.get("has_merged"))
        and _rival_differs(grid, "connected fragments only")
    )


def _witness_fallback(grid: Grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and bool(facts.get("has_fallback"))
        and _rival_differs(grid, "whole color only")
    )


def _witness_non_yellow(grid: Grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and bool(facts.get("yellow_is_fragment"))
        and _rival_differs(grid, "yellow is always the template")
    )


def _witness_sparse(grid: Grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and bool(facts.get("template_sparse"))
        and _rival_differs(grid, "fill template bounding box")
    )


def _witness_multi_missing(grid: Grid) -> bool:
    facts = semantic_observables(grid)
    return (
        not facts.get("errors")
        and int(facts.get("max_missing", 0)) >= 2
        and _rival_differs(grid, "add only one missing cell")
    )


SEMANTIC_WITNESSES = {
    "whole_color_precedes_components": _witness_merged,
    "component_fallback_after_whole_failure": _witness_fallback,
    "largest_color_not_fixed_yellow": _witness_non_yellow,
    "sparse_mask_not_bounding_box": _witness_sparse,
    "complete_all_missing_cells": _witness_multi_missing,
}
BRANCH_WITNESSES = {
    "whole_color_precedes_components",
    "component_fallback_after_whole_failure",
}
WITNESS_RIVALS = {
    "whole_color_precedes_components": ["connected fragments only"],
    "component_fallback_after_whole_failure": ["whole color only"],
    "largest_color_not_fixed_yellow": ["yellow is always the template"],
    "sparse_mask_not_bounding_box": ["fill template bounding box"],
    "complete_all_missing_cells": ["add only one missing cell"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a five-demo lesson to eliminate every named shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    profiles: set[str] = set()
    families: set[str] = set()
    saw_merged = False
    saw_fallback = False
    saw_non_yellow = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_grid = demo["input"]
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"demo {index} is outside the task grammar: {errors[0]}")
            continue
        truth = rule_mirror(input_grid)
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with whole-first template completion")
            continue
        facts = semantic_observables(input_grid)
        profiles.add(str(facts["scene_profile"]))
        families.add(str(facts["template_family"]))
        saw_merged = saw_merged or bool(facts["has_merged"])
        saw_fallback = saw_fallback or bool(facts["has_fallback"])
        saw_non_yellow = saw_non_yellow or bool(facts["yellow_is_fragment"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task grammar: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with whole-first template completion")
    if reasons:
        return reasons

    if profiles != set(SCENE_PROFILES):
        reasons.append(f"demonstrations omit canonical scale profiles: saw {sorted(profiles)}")
    if families != set(TEMPLATE_FAMILIES):
        reasons.append(f"demonstrations do not vary the sparse template mask: saw {sorted(families)}")
    if not saw_merged:
        reasons.append("demonstrations omit the disconnected-whole-color merge branch")
    if not saw_fallback:
        reasons.append("demonstrations omit per-component fallback")
    if not saw_non_yellow:
        reasons.append("demonstrations do not refute the fixed-yellow template shortcut")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_all = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            alternate = competitor(query["input"])
        except Exception as exc:  # pragma: no cover - gate reports this path loudly
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits_all and alternate != query_truth:
            reasons.append(
                f"demos remain compatible with competitor {name!r}, which changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Named negative fixtures for the task-local recognizer."""
    base = generate(91, 2, difficulty="medium")
    facts = _analyze(base)
    template_color = int(facts["template_color"])
    partial_color = next(color for color in facts["colors"] if color != template_color)

    missing_palette = [
        [BACKGROUND if value == partial_color else value for value in row]
        for row in base
    ]
    singleton_intruder = [list(row) for row in base]
    absent = next(color for color in TEMPLATE_COLORS if color not in facts["colors"])
    for row in range(len(singleton_intruder)):
        for col in range(len(singleton_intruder[0])):
            if singleton_intruder[row][col] == BACKGROUND:
                singleton_intruder[row][col] = absent
                break
        else:
            continue
        break
    damaged_template = [list(row) for row in base]
    tr, tc = _positions_of(base, template_color)[0]
    damaged_template[tr][tc] = BACKGROUND
    all_blue = full_grid(22, 22, BACKGROUND)
    return [
        ("all_blue", all_blue),
        ("dropped_fragment_color", missing_palette),
        ("singleton_absent_color", singleton_intruder),
        ("damaged_largest_template", damaged_template),
    ]
