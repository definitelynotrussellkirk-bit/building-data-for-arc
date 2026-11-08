"""Constructive sampler for ``Recolor the Outermost Layer``.

The selected Racket rule finds 4-connected components of every occupied cell
(colors other than 0 and 9), then recolors exactly each component's depth-one
4-neighbor boundary to cyan (8).  This module generates inputs only; the
independent ``rule_mirror`` is a regression oracle and semantic-rival helper,
not the label authority.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b3bfd59c2c43"
TASK_ID = GENERATOR_ID
RULE_HASH = "28b8cf49f820"
VERSION = "2.0.0"
SUMMARY = (
    "Two separated thick 4-connected components on a zero background. "
    "The output recolors every cell on each component's outermost cardinal "
    "layer to 8, including boundary cells exposed only beyond the grid edge; "
    "deeper cells retain their input color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the canvas is one of the three canonical input profiles and uses exactly two colors besides 0",
    "there are exactly two 4-connected occupied components separated by a one-cell Chebyshev moat",
    "both components are thick enough to contain at least one depth-two interior cell",
    "consecutive samples cycle through canonical, edge-touching, and multicolor-component witnesses",
]

CANVAS_PROFILES = {
    "11x15": (11, 15),
    "12x12": (12, 12),
    "13x15": (13, 15),
}
AXES = {
    "canvas_profile": {
        "type": "enum",
        "default": "keyed choice over the three canonical profiles",
        "valid": "11x15|12x12|13x15",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = ("canonical", "edge", "multicolor")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIFFICULTIES = {None, "easy", "medium", "hard"}
_INPUT_COLORS = tuple(range(1, 8))


def _solid(h: int, w: int) -> tuple[tuple[int, int], ...]:
    return tuple((r, c) for r in range(h) for c in range(w))


def _diamond(radius: int) -> tuple[tuple[int, int], ...]:
    side = 2 * radius + 1
    return tuple(
        (r, c)
        for r in range(side)
        for c in range(side)
        if abs(r - radius) + abs(c - radius) <= radius
    )


def _chamfered(side: int) -> tuple[tuple[int, int], ...]:
    corners = {(0, 0), (0, side - 1), (side - 1, 0), (side - 1, side - 1)}
    return tuple(
        (r, c)
        for r in range(side)
        for c in range(side)
        if (r, c) not in corners
    )


def _thick_cross(side: int = 7, thickness: int = 3) -> tuple[tuple[int, int], ...]:
    lo = (side - thickness) // 2
    hi = lo + thickness
    return tuple(
        (r, c)
        for r in range(side)
        for c in range(side)
        if lo <= r < hi or lo <= c < hi
    )


_SHAPES = {
    "square3": _solid(3, 3),
    "rect4": _solid(4, 4),
    "rect4x5": _solid(4, 5),
    "rect5x4": _solid(5, 4),
    "rect5": _solid(5, 5),
    "diamond5": _diamond(2),
    "chamfer5": _chamfered(5),
    "cross7": _thick_cross(),
}

_CANONICAL_SHAPE_PAIRS = (
    ("rect5", "square3"),
    ("diamond5", "rect4"),
    ("chamfer5", "square3"),
    ("rect4x5", "diamond5"),
    ("cross7", "square3"),
    ("diamond5", "chamfer5"),
)
_EDGE_SHAPE_PAIRS = (
    ("rect4", "square3"),
    ("rect4x5", "diamond5"),
    ("rect5x4", "square3"),
    ("rect5", "chamfer5"),
)
_MULTICOLOR_SHAPE_PAIRS = (
    ("rect5", "square3"),
    ("rect5", "diamond5"),
    ("rect5", "chamfer5"),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic lesson branch for semantic-gate accounting."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _shape_extent(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


@lru_cache(maxsize=256)
def _placements(
    shape_name: str,
    h: int,
    w: int,
    edge: str | None = None,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    shape = _SHAPES[shape_name]
    sh, sw = _shape_extent(shape)
    result = []
    for r0 in range(h - sh + 1):
        for c0 in range(w - sw + 1):
            if edge == "top" and r0 != 0:
                continue
            if edge == "bottom" and r0 + sh != h:
                continue
            if edge == "left" and c0 != 0:
                continue
            if edge == "right" and c0 + sw != w:
                continue
            result.append(tuple((r0 + r, c0 + c) for r, c in shape))
    return tuple(result)


def _moat_separated(
    first: tuple[tuple[int, int], ...],
    second: tuple[tuple[int, int], ...],
) -> bool:
    second_set = set(second)
    return not any(
        (r + dr, c + dc) in second_set
        for r, c in first
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


@lru_cache(maxsize=512)
def _placement_pairs(
    first_shape: str,
    second_shape: str,
    h: int,
    w: int,
    edge: str | None,
) -> tuple[tuple[int, int], ...]:
    first = _placements(first_shape, h, w, edge)
    second = _placements(second_shape, h, w, None)
    pairs = []
    for first_index, first_cells in enumerate(first):
        for second_index, second_cells in enumerate(second):
            if _moat_separated(first_cells, second_cells):
                pairs.append((first_index, second_index))
    return tuple(pairs)


def _choose_components(ctx, h: int, w: int, profile_name: str, band: str):
    rng = ctx.draw_rng(f"scene:{profile_name}:{band}")
    edge = None
    if profile_name == "canonical":
        shape_pair = rng.choice(_CANONICAL_SHAPE_PAIRS)
    elif profile_name == "edge":
        shape_pair = rng.choice(_EDGE_SHAPE_PAIRS)
        edge = rng.choice(("top", "bottom", "left", "right"))
    elif profile_name == "multicolor":
        shape_pair = rng.choice(_MULTICOLOR_SHAPE_PAIRS)
    else:  # pragma: no cover - schedule_profile owns this closed enum
        raise ValueError(f"unknown schedule profile: {profile_name!r}")

    pair_indexes = _placement_pairs(*shape_pair, h, w, edge)
    if not pair_indexes:
        raise RuntimeError(
            f"no constructive placement for {shape_pair!r} on {h}x{w} edge={edge!r}"
        )
    first_index, second_index = rng.choice(pair_indexes)
    first = _placements(shape_pair[0], h, w, edge)[first_index]
    second = _placements(shape_pair[1], h, w, None)[second_index]
    return first, second


def _paint_scene(ctx, grid, first, second, profile_name: str, band: str) -> None:
    color_rng = ctx.draw_rng(f"colors:{profile_name}:{band}")
    color_a, color_b = color_rng.sample(_INPUT_COLORS, 2)
    if profile_name != "multicolor":
        for r, c in first:
            grid[r][c] = color_a
        for r, c in second:
            grid[r][c] = color_b
        return

    # A solid 5x5 component split across two colors.  The color interface is
    # internal to the occupancy component, so a per-color-component shortcut
    # incorrectly recolors interface cells that the selected rule preserves.
    min_r = min(r for r, _ in first)
    min_c = min(c for _, c in first)
    orientation = color_rng.choice(("vertical", "horizontal"))
    for r, c in first:
        if orientation == "vertical":
            grid[r][c] = color_a if c - min_c < 2 else color_b
        else:
            grid[r][c] = color_a if r - min_r < 2 else color_b
    second_color = color_rng.choice((color_a, color_b))
    for r, c in second:
        grid[r][c] = second_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canvas_profile = ctx.draw_choice("canvas_profile", tuple(CANVAS_PROFILES))
    h, w = CANVAS_PROFILES[canvas_profile]
    profile_name = schedule_profile(seed, sample_index, difficulty=difficulty)
    band = difficulty or "medium"
    first, second = _choose_components(ctx, h, w, profile_name, band)
    grid = full_grid(h, w, 0)
    _paint_scene(ctx, grid, first, second, profile_name, band)
    return grid


def _valid_grid_shape(grid) -> tuple[int, int] | None:
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _occupied(value) -> bool:
    return type(value) is int and value not in (0, 9)


def _components(grid, *, per_color: bool = False):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if _occupied(grid[r][c])
    }
    result = []
    while unseen:
        start = min(unseen)
        start_color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point not in unseen:
                    continue
                if per_color and grid[point[0]][point[1]] != start_color:
                    continue
                unseen.remove(point)
                component.add(point)
                queue.append(point)
        result.append(frozenset(component))
    return tuple(sorted(result, key=lambda comp: min(comp)))


def _boundary_cells(component, h: int, w: int, *, count_offgrid: bool = True):
    boundary = set()
    for r, c in component:
        for dr, dc in _CARDINAL:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w):
                if count_offgrid:
                    boundary.add((r, c))
                    break
            elif (rr, cc) not in component:
                boundary.add((r, c))
                break
    return boundary


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    shape = _valid_grid_shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    h, w = shape
    errors = []
    if difficulty not in _DIFFICULTIES:
        errors.append("difficulty must be None/easy/medium/hard")
    if (h, w) not in set(CANVAS_PROFILES.values()):
        errors.append(
            f"canvas {h}x{w} is not one of {sorted(CANVAS_PROFILES.values())}"
        )
    if any(
        type(value) is not int or value < 0 or value > 7
        for row in grid
        for value in row
    ):
        errors.append("input cells must be integer colors 0..7 (8 and 9 are reserved)")
        return errors

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 2:
        errors.append(f"expected exactly two non-background colors, found {sorted(colors)}")

    components = _components(grid)
    if len(components) != 2:
        errors.append(f"expected exactly two occupied components, found {len(components)}")
        return errors

    for index, component in enumerate(components):
        boundary = _boundary_cells(component, h, w)
        interior = set(component) - boundary
        if not boundary:
            errors.append(f"component {index} has no outer layer")
        if not interior:
            errors.append(f"component {index} has no depth-two interior cell")

    first, second = components
    if not _moat_separated(tuple(sorted(first)), tuple(sorted(second))):
        errors.append("occupied components must have a one-cell Chebyshev moat")
    return errors


def strict_canonical_like(grid):
    """The generated manifold is intentionally a strict canonical subset."""
    return self_check(grid)


def observe_overrides(grid):
    shape = _valid_grid_shape(grid)
    if shape is None:
        raise ValueError("cannot observe overrides from a malformed grid")
    for name, dims in CANVAS_PROFILES.items():
        if shape == dims:
            return {"canvas_profile": name}
    raise ValueError(f"unrecognized canvas dimensions: {shape[0]}x{shape[1]}")


def _apply_boundary_rule(grid, components, *, count_offgrid: bool = True):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for component in components:
        for r, c in _boundary_cells(
            component, h, w, count_offgrid=count_offgrid
        ):
            out[r][c] = 8
    return out


def rule_mirror(grid):
    """Independent Python mirror used only by tests and semantic contracts."""
    return _apply_boundary_rule(grid, _components(grid))


def _edge_blind(grid):
    """Rival: ignores off-grid exposure when deciding whether a cell is outer."""
    return _apply_boundary_rule(grid, _components(grid), count_offgrid=False)


def _per_color(grid):
    """Rival: peels each input color separately instead of occupancy components."""
    return _apply_boundary_rule(grid, _components(grid, per_color=True))


def _recolor_all(grid):
    """Rival: mistakes the outermost layer for the whole component."""
    return [
        [8 if _occupied(value) else value for value in row]
        for row in grid
    ]


def _largest_only(grid):
    """Rival: peels only the largest occupied component."""
    components = _components(grid)
    largest = min(components, key=lambda comp: (-len(comp), min(comp)))
    return _apply_boundary_rule(grid, (largest,))


def _differs(rival, grid) -> bool:
    return rival(grid) != rule_mirror(grid)


def _edge_exposure(grid) -> bool:
    return _differs(_edge_blind, grid)


def _multicolor_component(grid) -> bool:
    return any(
        len({grid[r][c] for r, c in component}) > 1
        for component in _components(grid)
    ) and _differs(_per_color, grid)


def _interior_core(grid) -> bool:
    return _differs(_recolor_all, grid)


def _multiple_components(grid) -> bool:
    return len(_components(grid)) > 1 and _differs(_largest_only, grid)


SEMANTIC_WITNESSES = {
    "edge_exposure": _edge_exposure,
    "multicolor_component": _multicolor_component,
    "interior_core": _interior_core,
    "multiple_components": _multiple_components,
}
SEMANTIC_RIVALS = {
    "edge_blind": _edge_blind,
    "per_color": _per_color,
    "recolor_all": _recolor_all,
    "largest_only": _largest_only,
}
WITNESS_RIVALS = {
    "edge_exposure": ["edge_blind"],
    "multicolor_component": ["per_color"],
    "interior_core": ["recolor_all"],
    "multiple_components": ["largest_only"],
}
# Both shortcuts reproduce every canonical pair: the canonical edge-touching
# component has ordinary in-grid exposure, and every canonical component is
# monochrome. Generated edge and multicolor witnesses are therefore required.
CANONICAL_SHORTCUTS = {
    "edge_blind": _edge_blind,
    "per_color": _per_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report any named rival left consistent with the demos but not the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo["output"]
                for demo in demos
            )
            disagrees = rival(query["input"]) != query["output"]
        except Exception as exc:  # contract violations must be loud
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives and disagrees:
            reasons.append(f"competitor {name} survives every demonstration")
    return reasons
