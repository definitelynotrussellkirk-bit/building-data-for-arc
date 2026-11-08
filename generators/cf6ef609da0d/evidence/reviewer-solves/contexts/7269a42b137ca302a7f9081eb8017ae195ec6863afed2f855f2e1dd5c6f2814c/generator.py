"""Construct lessons for selecting components that touch the main diagonal.

The authoritative rule examines each 4-connected color-6 component in the
*input*.  A component is kept exactly when one of its occupied cells lies on
the main diagonal ``row == column``; kept cells are recolored 2 and every other
cell becomes 0.

Ordinary examples follow a five-slot teaching schedule over two explicit profiles.  ``mixed_bbox``
contains a true cell touch plus an off-diagonal component whose *bounding box*
intersects the diagonal.  ``none_on_diagonal`` contains no true touch at all.
Together they refute both the bounding-box shortcut and the shortcut that keeps
the component nearest the diagonal even when no component actually touches it.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf6ef609da0d"
TASK_ID = GENERATOR_ID
RULE_HASH = "5deda141503d"
VERSION = "2.3.0"
SUMMARY = (
    "Keep each color-6 4-connected component only when an occupied cell, not "
    "merely its bounding box, lies on the main diagonal; recolor kept cells 2."
)
SOLID_OUTPUT_JUSTIFICATION = (
    "The none_on_diagonal teaching profile deliberately has no qualifying "
    "component, so the authoritative selection rule must return an all-zero "
    "grid; this negative branch is paired with positive examples in every lesson."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
SCENE_PATTERNS = ("mixed_bbox", "none_on_diagonal")
SCHEDULE_PROFILES = (
    "mixed_bbox",
    "none_on_diagonal",
    "mixed_bbox",
    "none_on_diagonal",
    "mixed_bbox",
)
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "grid dimensions are 8..14 in each direction",
    "background is 0 and every object cell is color 6",
    "there are exactly 2..5 separated 4-connected components",
    "component sizes span the canonical 1..4-cell morphology",
    "mixed_bbox has a real diagonal touch and a bbox-only trap",
    "none_on_diagonal has a bbox-only trap but no occupied diagonal cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9/10 anchor every fifth draw; otherwise band-shaped 8..14",
        "valid": "8..14",
        "doc": "Returned grid height; every endpoint supports every profile.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9/10 anchor every fifth draw; otherwise band-shaped 8..14",
        "valid": "8..14",
        "doc": "Returned grid width; every endpoint supports every profile.",
    },
    "n_components": {
        "type": "int",
        "default": "keyed uniform 2..5",
        "valid": "2..5",
        "doc": "Exact number of 4-connected color-6 components.",
    },
    "scene_pattern": {
        "type": "str",
        "default": "five-slot 3:2 teaching schedule",
        "valid": "|".join(SCENE_PATTERNS),
        "doc": "Mixed true/bbox touch or the all-no-touch negative branch.",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared five-slot teaching schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_components"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    scene = overrides.get("scene_pattern")
    if scene is not None and scene not in SCENE_PATTERNS:
        raise ValueError(
            f"scene_pattern must be one of {SCENE_PATTERNS}, got {scene!r}"
        )


_BAND_BOUNDS = {
    "easy": {"grid_h": (8, 9), "grid_w": (8, 9), "n_components": (2, 3)},
    "medium": {"grid_h": (10, 11), "grid_w": (10, 11), "n_components": (3, 4)},
    "hard": {"grid_h": (12, 14), "grid_w": (12, 14), "n_components": (4, 5)},
}
_FULL_BOUNDS = {"grid_h": (8, 14), "grid_w": (8, 14), "n_components": (2, 5)}


def _draw_int_axis(ctx, name, scheduled=None):
    """Draw a scheduled/band default while preserving the full exact domain."""
    if ctx.overrides.get(name) is not None:
        lo, hi = _FULL_BOUNDS[name]
    elif scheduled is not None:
        lo = hi = scheduled
    else:
        lo, hi = _BAND_BOUNDS.get(ctx.difficulty, _FULL_BOUNDS)[name]
    return ctx.draw_int_strict(name, lo, hi)


def _draw_scene(ctx, scheduled):
    options = SCENE_PATTERNS if ctx.overrides.get("scene_pattern") is not None else (scheduled,)
    return ctx.draw_choice("scene_pattern", options)


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


@lru_cache(maxsize=None)
def _polyominoes(size):
    """All fixed 4-connected polyominoes of ``size`` up to translation."""
    shapes = {((0, 0),)}
    for _ in range(1, size):
        grown = set()
        for shape in shapes:
            cells = set(shape)
            for r, c in shape:
                for dr, dc in _CARDINAL:
                    point = (r + dr, c + dc)
                    if point not in cells:
                        grown.add(_normalize(cells | {point}))
        shapes = grown
    return tuple(sorted(shapes))


def _touches_diagonal(cells):
    return any(r == c for r, c in cells)


def _bbox_intersects_diagonal(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return max(min(rows), min(cols)) <= min(max(rows), max(cols))


@lru_cache(maxsize=None)
def _placements(h, w, size, relation):
    placements = set()
    for shape in _polyominoes(size):
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        for r0 in range(h - shape_h + 1):
            for c0 in range(w - shape_w + 1):
                cells = tuple(sorted((r0 + r, c0 + c) for r, c in shape))
                touches = _touches_diagonal(cells)
                bbox_hit = _bbox_intersects_diagonal(cells)
                if relation == "touch" and touches:
                    placements.add(cells)
                elif relation == "bbox_trap" and bbox_hit and not touches:
                    placements.add(cells)
                elif relation == "off" and not touches:
                    placements.add(cells)
    return tuple(sorted(placements))


def _component_specs(sample_index, n_components, scene_pattern):
    """Deterministic morphology curriculum with exact semantic roles."""
    sizes = [1 + ((sample_index + index) % 4) for index in range(n_components)]
    if scene_pattern == "mixed_bbox":
        roles = ["touch", "bbox_trap"] + ["off"] * (n_components - 2)
        if sizes[1] < 3:
            sizes[1] += 2
    else:
        roles = ["bbox_trap"] + ["off"] * (n_components - 1)
        if sizes[0] < 3:
            sizes[0] += 2
    return list(zip(roles, sizes))


def _blocked_by(cells, h, w):
    blocked = set(cells)
    for r, c in cells:
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                blocked.add((nr, nc))
    return blocked


def _choose_components(h, w, specs, rng):
    """Backtrack over rare roles first while preserving component separation."""
    prepared = []
    for original_index, (relation, size) in enumerate(specs):
        candidates = list(_placements(h, w, size, relation))
        if not candidates:
            raise ValueError(
                f"no {relation} placement of size {size} fits grid {h}x{w}"
            )
        rng.shuffle(candidates)
        prepared.append((len(candidates), original_index, candidates))
    prepared.sort(key=lambda item: item[0])

    selected = [None] * len(specs)
    node_budget = 200_000
    nodes = 0

    def search(index, blocked):
        nonlocal nodes
        if index == len(prepared):
            return True
        _count, original_index, candidates = prepared[index]
        for cells in candidates:
            nodes += 1
            if nodes > node_budget:
                return False
            if any(point in blocked for point in cells):
                continue
            selected[original_index] = cells
            if search(index + 1, blocked | _blocked_by(cells, h, w)):
                return True
            selected[original_index] = None
        return False

    if not search(0, set()):
        raise ValueError(
            f"could not place {specs!r} as separated components in {h}x{w}"
        )
    return [cells for cells in selected if cells is not None]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_size = None
    if sample_index % LESSON_SCHEDULE_PERIOD == 0:
        canonical_size = 9 + ctx.draw_rng("canonical_size").randrange(2)
    h = _draw_int_axis(ctx, "grid_h", canonical_size)
    w = _draw_int_axis(ctx, "grid_w", canonical_size)
    n_components = _draw_int_axis(ctx, "n_components")
    scene_pattern = _draw_scene(
        ctx, schedule_profile(seed, sample_index, difficulty)
    )
    specs = _component_specs(sample_index, n_components, scene_pattern)
    components = _choose_components(h, w, specs, ctx.draw_rng("layout"))
    grid = full_grid(h, w, 0)
    for component in components:
        for r, c in component:
            grid[r][c] = 6
    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid grid: {'; '.join(errors)}")
    return grid


def _components(grid, color=6):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return result


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["empty grid"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return [], ["rows must be sequences"]
    if not grid[0]:
        return [], ["empty grid row"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return [], ["ragged grid"]
    height = len(grid)
    if not (8 <= height <= 14 and 8 <= width <= 14):
        errors.append(f"grid dimensions {height}x{width} outside 8..14")
    invalid = sorted(
        {value for row in grid for value in row if type(value) is not int or value not in (0, 6)},
        key=repr,
    )
    if invalid:
        errors.append(f"cells must be integer colors 0 or 6; found {invalid[:5]}")
        return [], errors
    components = _components(grid)
    if not (2 <= len(components) <= 5):
        errors.append(f"expected 2..5 color-6 components, got {len(components)}")
    bad_sizes = sorted(len(component) for component in components if not 1 <= len(component) <= 4)
    if bad_sizes:
        errors.append(f"component sizes must be 1..4; found {bad_sizes}")
    return components, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _components_found, errors = _analysis(grid)
    return errors


def strict_canonical_like(grid):
    """All generated draws stay inside the linked canonical input grammar."""
    return self_check(grid)


def observe_overrides(grid):
    components, errors = _analysis(grid)
    if errors:
        raise ValueError("; ".join(errors))
    scene_pattern = (
        "mixed_bbox"
        if any(_touches_diagonal(component) for component in components)
        else "none_on_diagonal"
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_components": len(components),
        "scene_pattern": scene_pattern,
    }


def _paint_selected(grid, predicate):
    out = full_grid(len(grid), len(grid[0]), 0)
    for component in _components(grid):
        if predicate(component):
            for r, c in component:
                out[r][c] = 2
    return out


def rule_mirror(grid):
    """Independent Python transcription of the immutable Racket authority."""
    return _paint_selected(grid, _touches_diagonal)


def _rival_bbox_diagonal(grid):
    """Wrong rule: bounding-box intersection counts as a component touch."""
    return _paint_selected(grid, _bbox_intersects_diagonal)


def _rival_nearest_diagonal(grid):
    """Wrong rule: keep globally nearest components even when distance > 0."""
    components = _components(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    if not components:
        return out
    distances = [min(abs(r - c) for r, c in component) for component in components]
    nearest = min(distances)
    for component, distance in zip(components, distances):
        if distance == nearest:
            for r, c in component:
                out[r][c] = 2
    return out


def _witness_bbox_without_cell_touch(grid):
    return any(
        _bbox_intersects_diagonal(component) and not _touches_diagonal(component)
        for component in _components(grid)
    )


def _witness_no_component_touches(grid):
    components = _components(grid)
    return bool(components) and not any(
        _touches_diagonal(component) for component in components
    )


SEMANTIC_RIVALS = {
    "bbox_diagonal": _rival_bbox_diagonal,
    "nearest_diagonal": _rival_nearest_diagonal,
}

SEMANTIC_WITNESSES = {
    "bbox_without_cell_touch": _witness_bbox_without_cell_touch,
    "no_component_touches_diagonal": _witness_no_component_touches,
}

WITNESS_RIVALS = {
    "bbox_without_cell_touch": ["bbox_diagonal"],
    "no_component_touches_diagonal": ["nearest_diagonal"],
}

CANONICAL_SHORTCUTS = {
    "bbox_diagonal": _rival_bbox_diagonal,
    "nearest_diagonal": _rival_nearest_diagonal,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require lawful labels and reject any named rival that survives demos."""
    errors = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(demos):
        try:
            grid, output = pair["input"], pair["output"]
        except (KeyError, TypeError):
            errors.append(f"demo {index} is not an input/output pair")
            continue
        grid_errors = self_check(grid)
        if grid_errors:
            errors.append(f"demo {index} malformed: {grid_errors[0]}")
        elif rule_mirror(grid) != output:
            errors.append(f"demo {index} output disagrees with diagonal-cell rule")
    try:
        query_grid, query_output = query["input"], query["output"]
    except (KeyError, TypeError):
        errors.append("query is not an input/output pair")
        return errors
    query_errors = self_check(query_grid)
    if query_errors:
        errors.append(f"query malformed: {query_errors[0]}")
    elif rule_mirror(query_grid) != query_output:
        errors.append("query output disagrees with diagonal-cell rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            disagrees = rival(query_grid) != query_output
        except (KeyError, TypeError, IndexError, ValueError) as exc:
            errors.append(f"{name} could not score lesson: {exc}")
            continue
        if survives and disagrees:
            errors.append(f"{name} fits every demo but predicts the query incorrectly")
    return errors
