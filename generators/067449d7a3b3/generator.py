"""Input generator for ARC task 067449d7a3b3.

The selected rule finds every 8-connected nonzero object and uses its bounding
box.  For a box of height ``rh`` and width ``rw``, ``border=max(rh,rw)//2``.
All blue (1) stems are painted first beneath the box, beginning one row below
its halo.  Green (3) bounding-box rings are then painted, clipped to the canvas;
rings overwrite stems but do not overwrite cells that were maroon (9) in the
input.  The rule is color-agnostic when it chooses objects, and a singleton has
border zero, so it receives a stem but no ring.

The canonical examples contain only solid maroon rectangles, which leaves three
strong wrong rules unfalsified: process only maroon objects, process only solid
rectangles, and ignore singletons.  The four-position schedule C-X-X-C retains
canonical size/palette anchors while putting two source-bound counterexamples in
every four generated pairs.  Therefore any three demonstrations obtained by
holding out one pair still refute all three shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "067449d7a3b3"
TASK_ID = GENERATOR_ID
RULE_HASH = "fb156b8e3aee"
VERSION = "4.0.2"
SUMMARY = (
    "Every 8-connected nonzero object grows a clipped green bbox halo of "
    "thickness max(bbox side)//2 and a blue vertical stem below that halo."
)

INVARIANTS = [
    "10..30 rectangular input with background 0 and exactly 2..4 separated 8-connected objects",
    "canonical profile: solid maroon(9) rectangles; counterexample profile: one non-maroon irregular object plus one maroon singleton",
    "all object bounding boxes are at most 6x6 and every returned input changes under the selected rule",
    "every four scheduled pairs contain two counterexamples, so any one-pair query rotation leaves a shortcut-refuting demonstration",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/profile anchor in 10..30",
        "valid": "10..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/profile anchor in 10..30",
        "valid": "10..30",
    },
    "n_objects": {
        "type": "int",
        "default": "2 easy, 3 medium/default, 4 hard",
        "valid": "2..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "C-X-X-C schedule",
        "valid": "canonical|counterexample",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical", "counterexample")
_SCHEDULE = ("canonical", "counterexample", "counterexample", "canonical")
_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_BOUNDS = {
    "grid_h": (10, 30),
    "grid_w": (10, 30),
    "n_objects": (2, 4),
}
_PROFILE_VALUES = ("canonical", "counterexample")
_COUNTER_COLORS = (2, 4, 5, 6, 7, 8)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the source-bound four-pair teaching schedule profile."""
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]


def _validate_request(difficulty, overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_BOUNDS:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_BOUNDS[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "scene_profile":
            if type(value) is not str:
                raise ValueError(
                    f"scene_profile must be a string, not {type(value).__name__}"
                )
            if value not in _PROFILE_VALUES:
                raise ValueError(
                    f"scene_profile={value!r} must be one of {_PROFILE_VALUES}"
                )


def _draw_profiled_int(ctx, name, default, overrides):
    lo, hi = _INT_BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _default_shape(profile, difficulty):
    if profile == "canonical":
        return {
            None: (15, 15, 3),
            "easy": (10, 10, 2),
            "medium": (20, 20, 3),
            "hard": (30, 30, 4),
        }[difficulty]
    return {
        None: (18, 18, 3),
        "easy": (12, 12, 2),
        "medium": (18, 18, 3),
        "hard": (24, 24, 4),
    }[difficulty]


def _axis_zones(h, w):
    """Four disjoint zones with a two-cell cross-gap, valid at the 10x10 floor."""
    top = (0, h // 2 - 1)
    bottom = (h // 2 + 1, h)
    left = (0, w // 2 - 1)
    right = (w // 2 + 1, w)
    zones = (
        (top[0], top[1], left[0], left[1]),
        (top[0], top[1], right[0], right[1]),
        (bottom[0], bottom[1], left[0], left[1]),
        (bottom[0], bottom[1], right[0], right[1]),
    )
    if any(r2 - r1 < 2 or c2 - c1 < 2 for r1, r2, c1, c2 in zones):
        raise RuntimeError("internal zone construction failed at a supported size")
    return zones


def _mask_size(mask):
    return len(mask), len(mask[0])


def _solid_mask(height, width):
    return tuple(tuple(1 for _ in range(width)) for _ in range(height))


def _fit_mask(mask, zone):
    """Clamp only internal defaults; advertised overrides never change."""
    r1, r2, c1, c2 = zone
    zh, zw = r2 - r1, c2 - c1
    mh, mw = _mask_size(mask)
    if mh <= zh and mw <= zw:
        return mask
    return _solid_mask(min(mh, zh), min(mw, zw))


def _candidate_origins(zone, mask):
    r1, r2, c1, c2 = zone
    mh, mw = _mask_size(mask)
    return [
        (r, c)
        for r in range(r1, r2 - mh + 1)
        for c in range(c1, c2 - mw + 1)
    ]


def _edge_candidates(zone, mask, edge):
    candidates = _candidate_origins(zone, mask)
    r1, r2, c1, c2 = zone
    mh, mw = _mask_size(mask)
    if edge == "top":
        return [point for point in candidates if point[0] == r1]
    if edge == "bottom":
        return [point for point in candidates if point[0] + mh == r2]
    if edge == "left":
        return [point for point in candidates if point[1] == c1]
    if edge == "right":
        return [point for point in candidates if point[1] + mw == c2]
    return candidates


def _paint_mask(grid, zone, mask, color, rng, *, edge=None, prefer=None):
    mask = _fit_mask(mask, zone)
    candidates = _edge_candidates(zone, mask, edge)
    if not candidates:
        raise RuntimeError("no constructive placement candidate")
    if prefer == "first":
        origin = candidates[0]
    elif prefer == "last":
        origin = candidates[-1]
    else:
        origin = rng.choice(candidates)
    r0, c0 = origin
    for dr, row in enumerate(mask):
        for dc, occupied in enumerate(row):
            if occupied:
                grid[r0 + dr][c0 + dc] = color


def _canonical_masks(h, w, n_objects):
    short = min(h, w)
    if short >= 18:
        first = (6, 6)
    elif short >= 14:
        first = (4, 4)
    else:
        first = (2, 2)
    sizes = [first, (4, 4) if short >= 18 else (2, 2), (2, 4), (2, 2)]
    return [_solid_mask(*size) for size in sizes[:n_objects]]


def _draw_canonical(ctx, h, w, n_objects, sample_index):
    grid = full_grid(h, w, 0)
    zones = _axis_zones(h, w)
    masks = _canonical_masks(h, w, n_objects)

    # The schedule has a C|C boundary between slots 3 and 0.  Anchor the first
    # rectangle at a different corner in every modulo-four slot so adjacent
    # canonical pairs can never collapse to the same byte-level lesson pair.
    corner_modes = (
        ("top", "first"),
        ("top", "last"),
        ("bottom", "last"),
        ("bottom", "first"),
    )
    first_edge, first_prefer = corner_modes[sample_index % len(corner_modes)]
    for index, mask in enumerate(masks):
        _paint_mask(
            grid,
            zones[index],
            mask,
            9,
            ctx.draw_rng(f"canonical_object_{index}"),
            edge=first_edge if index == 0 else None,
            prefer=first_prefer if index == 0 else None,
        )
    return grid


def _draw_counterexample(ctx, h, w, n_objects, sample_index):
    grid = full_grid(h, w, 0)
    zones = _axis_zones(h, w)
    color = ctx.draw_choice("counterexample_color", _COUNTER_COLORS)

    # A clipped, non-maroon, non-rectangular object refutes both canonical
    # object-selection shortcuts.  A separate maroon singleton has border zero
    # and a visible stem, refuting the singleton-ignoring shortcut.
    variant = sample_index % 2
    irregular = (((1, 1), (1, 0)), ((1, 1), (0, 1)))[variant]
    placement = ("first", "last")[variant]
    _paint_mask(
        grid,
        zones[0],
        irregular,
        color,
        ctx.draw_rng("counter_irregular"),
        edge="top",
        prefer=placement,
    )
    _paint_mask(
        grid,
        zones[1],
        ((1,),),
        9,
        ctx.draw_rng("counter_singleton"),
        prefer=placement,
    )

    extras = (_solid_mask(2, 2), _solid_mask(2, 3))
    for offset in range(n_objects - 2):
        _paint_mask(
            grid,
            zones[offset + 2],
            extras[offset],
            9,
            ctx.draw_rng(f"counter_extra_{offset}"),
            prefer="last",
        )
    return grid


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

    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", _PROFILE_VALUES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))

    default_h, default_w, default_count = _default_shape(profile, difficulty)
    h = _draw_profiled_int(ctx, "grid_h", default_h, overrides)
    w = _draw_profiled_int(ctx, "grid_w", default_w, overrides)
    n_objects = _draw_profiled_int(ctx, "n_objects", default_count, overrides)

    grid = (
        _draw_canonical(ctx, h, w, n_objects, sample_index)
        if profile == "canonical"
        else _draw_counterexample(ctx, h, w, n_objects, sample_index)
    )
    findings = self_check(grid)
    if findings:
        raise RuntimeError("constructive generator emitted invalid input: " + "; ".join(findings))
    return grid


def _shape_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if not (10 <= len(grid) <= 30 and 10 <= width <= 30):
        return [f"grid dimensions must both be in 10..30; found {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            todo = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        point = (r + dr, c + dc)
                        if (
                            0 <= point[0] < h
                            and 0 <= point[1] < w
                            and point not in seen
                            and grid[point[0]][point[1]] != 0
                        ):
                            seen.add(point)
                            todo.append(point)
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            colors = {grid[r][c] for r, c in cells}
            components.append(
                {
                    "cells": tuple(cells),
                    "cell_set": frozenset(cells),
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                    "colors": frozenset(colors),
                    "solid": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
                }
            )
    return components


def _classify_components(components):
    canonical = bool(components) and all(
        component["colors"] == frozenset({9})
        and component["solid"]
        and len(component["cells"]) >= 4
        for component in components
    )
    if canonical:
        return "canonical"

    irregular = [
        component
        for component in components
        if component["colors"] != frozenset({9}) and not component["solid"]
    ]
    singletons = [
        component
        for component in components
        if component["colors"] == frozenset({9}) and len(component["cells"]) == 1
    ]
    remaining = [
        component
        for component in components
        if component not in irregular and component not in singletons
    ]
    if (
        len(irregular) == 1
        and len(irregular[0]["colors"]) == 1
        and not (irregular[0]["colors"] & {1, 3, 9})
        and len(singletons) == 1
        and all(
            component["colors"] == frozenset({9})
            and component["solid"]
            and len(component["cells"]) >= 4
            for component in remaining
        )
    ):
        return "counterexample"
    return None


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    if any(value in (1, 3) for row in grid for value in row):
        errors.append("input colors may not use output-only blue(1) or green(3)")

    components = _components8(grid)
    if not 2 <= len(components) <= 4:
        errors.append(
            f"expected 2..4 nonzero 8-connected objects; found {len(components)}"
        )
        return errors
    for index, component in enumerate(components):
        if component["height"] > 6 or component["width"] > 6:
            errors.append(f"object {index} bbox exceeds the canonical 6x6 maximum")
        if len(component["colors"]) != 1:
            errors.append(f"object {index} must use exactly one input color")

    profile = _classify_components(components)
    if profile is None:
        errors.append("grid does not match the canonical or counterexample profile")
    if not errors and _mirror(grid) == [list(row) for row in grid]:
        errors.append("task input must change under the selected rule")
    return errors


def strict_canonical_like(grid):
    """Recognize the strict generated/canonical task manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    components = _components8(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(components),
        "scene_profile": _classify_components(components),
    }


def _apply_to_objects(grid, include: Callable[[dict], bool]):
    """Apply the selected painting law to only the components a rival selects."""
    h, w = len(grid), len(grid[0])
    selected = []
    for component in _components8(grid):
        if include(component):
            r1, c1, r2, c2 = component["bbox"]
            border = max(component["height"], component["width"]) // 2
            selected.append((r1, c1, r2, c2, border))

    out = [list(row) for row in grid]
    for r1, c1, r2, c2, border in selected:
        for r in range(r2 + border + 1, h):
            for c in range(c1, c2 + 1):
                out[r][c] = 1
    for r1, c1, r2, c2, border in selected:
        for r in range(r1 - border, r2 + border + 1):
            for c in range(c1 - border, c2 + border + 1):
                if r1 <= r <= r2 and c1 <= c <= c2:
                    continue
                if 0 <= r < h and 0 <= c < w and grid[r][c] != 9:
                    out[r][c] = 3
    return out


def _mirror(grid):
    """Independent Python mirror of the unchanged selected Racket authority."""
    return _apply_to_objects(grid, lambda component: True)


def _maroon_only_rival(grid):
    return _apply_to_objects(grid, lambda component: component["colors"] == {9})


def _solid_rectangles_only_rival(grid):
    return _apply_to_objects(grid, lambda component: bool(component["solid"]))


def _ignore_singletons_rival(grid):
    return _apply_to_objects(grid, lambda component: len(component["cells"]) > 1)


def _has_nonmaroon_irregular(grid):
    return any(
        component["colors"] != frozenset({9}) and not component["solid"]
        for component in _components8(grid)
    )


def _has_maroon_singleton(grid):
    return any(
        component["colors"] == frozenset({9}) and len(component["cells"]) == 1
        for component in _components8(grid)
    )


def lesson_identifiable(demos, query):
    """Require demonstrations to reject every declared canonical-fitting rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(pair["input"])
        if errors:
            return [f"demo {index} is outside the strict manifold: {errors[0]}"]
        if pair["output"] != _mirror(pair["input"]):
            return [f"demo {index} output disagrees with the intended rule"]
    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in demos):
            return [f"{name} shortcut survives every demonstration"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]
    errors = self_check(query["input"])
    if errors:
        return [f"query is outside the strict manifold: {errors[0]}"]
    if "output" in query and query["output"] != _mirror(query["input"]):
        return ["query output disagrees with the intended rule"]
    return []


SEMANTIC_WITNESSES = {
    "nonmaroon_irregular": _has_nonmaroon_irregular,
    "maroon_singleton": _has_maroon_singleton,
}
SEMANTIC_RIVALS = {
    "maroon_only": _maroon_only_rival,
    "solid_rectangles_only": _solid_rectangles_only_rival,
    "ignore_singletons": _ignore_singletons_rival,
}
WITNESS_RIVALS = {
    "nonmaroon_irregular": ["maroon_only", "solid_rectangles_only"],
    "maroon_singleton": ["ignore_singletons"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
