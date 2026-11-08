"""Generator for 7f2dafa2bee4 — recolor objects by contact-graph degree.

The canonical rule treats each same-color 4-connected object as a node. Two
nodes are adjacent when any cells touch cardinally. Recolor every object by its
degree: 0→1, 1→2, 2→3, and 3+→4.

Default samples follow a period-three semantic schedule. Two residues contain a
degree-zero object, so every four consecutive pairs retain at least one degree-0
witness after any one pair is held out as the query.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]
Component = list[Cell]

GENERATOR_ID = "7f2dafa2bee4"
VERSION = "1.3.0"
TASK_ID = GENERATOR_ID
RULE_HASH = "c4e5aa9ad5fd"

SUMMARY = "3-5 distinct-color components arranged as contact graphs with visible 4-neighbor touch degrees."

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("degree_zero_chain", "degree_zero_star", "connected")

INVARIANTS = [
    "background is 0",
    "3-5 distinct-color objects may touch cardinally without merging",
    "the contact graph has at least two touch degrees so the output uses multiple rule colors",
    "every four consecutive default samples include at least two degree-zero witnesses",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_isolated", "all_touching", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "n_components": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "palette_size": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias": {"type": "str", "default": "varied_touch_degrees", "valid": "varied_touch_degrees"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _paint(g: Grid, cells: Component, color: int, r0: int, c0: int) -> None:
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def _normalize_components(components: list[Component]) -> list[Component]:
    min_r = min(r for comp in components for r, _ in comp)
    min_c = min(c for comp in components for _, c in comp)
    return [[(r - min_r, c - min_c) for r, c in comp] for comp in components]


def _transform_components(components: list[Component], rng) -> list[Component]:
    comps = [[(r, c) for r, c in comp] for comp in components]
    if rng.random() < 0.5:
        comps = [[(c, r) for r, c in comp] for comp in comps]
    max_r = max(r for comp in comps for r, _ in comp)
    max_c = max(c for comp in comps for _, c in comp)
    if rng.random() < 0.5:
        comps = [[(max_r - r, c) for r, c in comp] for comp in comps]
    if rng.random() < 0.5:
        comps = [[(r, max_c - c) for r, c in comp] for comp in comps]
    return _normalize_components(comps)


def schedule_profile(seed: Any, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic semantic profile; seed/band vary only pixels."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _contact_components(n: int, rng, profile: str) -> list[Component]:
    """Build a small graph with the scheduled degree support.

    All objects use different colors, so direct contact creates graph edges but
    never merges nodes under the canonical same-color object segmentation.
    """
    if profile == "connected":
        if n == 3:
            comps: list[Component] = [[(0, 0)], [(0, 1)], [(0, 2)]]
        elif n == 4:
            comps = [[(0, 0)], [(0, 1)], [(0, 2)], [(0, 3)]]
        else:
            # Four leaves around a two-cell center expose degree >=3.
            comps = [
                [(1, 1), (2, 1)],
                [(0, 1)],
                [(3, 1)],
                [(1, 0)],
                [(2, 2)],
            ]
    elif profile == "degree_zero_star":
        if n == 3:
            comps = [[(0, 0)], [(0, 1)], [(3, 3), (3, 4)]]
        elif n == 4:
            comps = [[(1, 1)], [(0, 1)], [(1, 0)], [(4, 4), (4, 5)]]
        else:
            comps = [
                [(1, 1), (2, 1)],
                [(0, 1)],
                [(3, 1)],
                [(1, 0)],
                [(5, 4), (5, 5)],
            ]
    else:  # degree_zero_chain
        if n == 3:
            comps = [[(0, 0)], [(0, 1)], [(3, 0), (3, 1)]]
        elif n == 4:
            comps = [[(0, 0)], [(0, 1)], [(0, 2)], [(3, 0), (3, 1)]]
        else:
            comps = [[(0, i)] for i in range(4)] + [[(3, 0), (3, 1)]]
    return _transform_components(comps, rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the broad canonical grammar without relying on generation metadata."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer colors 0..9"]
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) < 3:
        return [f"expected at least 3 distinct nonzero colors; found {len(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        height = ctx.draw_int("grid_h", 9, 10)
        width = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_components", 3, 4)
    elif difficulty == "hard":
        height = ctx.draw_int("grid_h", 11, 14)
        width = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        height = ctx.draw_int("grid_h", 9, 11)
        width = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_components", 3, 5)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    profile = schedule_profile(seed, sample_index, difficulty)
    comps = _contact_components(n, rng, profile)
    template_h = max(r for comp in comps for r, _ in comp) + 1
    template_w = max(c for comp in comps for _, c in comp) + 1
    grid = full_grid(height, width, 0)
    r0 = rng.randint(1, max(1, height - template_h - 1)) if height > template_h + 1 else 0
    c0 = rng.randint(1, max(1, width - template_w - 1)) if width > template_w + 1 else 0
    for comp, color in zip(comps, palette):
        _paint(grid, comp, color, r0, c0)
    return grid


def _components(grid: Grid) -> list[Component]:
    """Return same-color four-connected nonzero components deterministically."""
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    found: list[Component] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        pending = [start]
        cells: Component = []
        while pending:
            point = pending.pop()
            cells.append(point)
            r, c = point
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    pending.append(nxt)
        found.append(sorted(cells))
    return sorted(found, key=lambda cells: cells[0])


def _touching(first: Component, second: Component) -> bool:
    other = set(second)
    return any((r + dr, c + dc) in other for r, c in first for dr, dc in _CARDINAL)


def contact_degrees(grid: Grid) -> list[int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid contact-degree grid: " + "; ".join(errors))
    comps = _components(grid)
    return [
        sum(index != other and _touching(comp, comps[other]) for other in range(len(comps)))
        for index, comp in enumerate(comps)
    ]


def _apply_degree_map(grid: Grid, degree_zero_color: int = 1) -> Grid:
    comps = _components(grid)
    degrees = [
        sum(index != other and _touching(comp, comps[other]) for other in range(len(comps)))
        for index, comp in enumerate(comps)
    ]
    out = full_grid(len(grid), len(grid[0]), 0)
    for comp, degree in zip(comps, degrees):
        color = degree_zero_color if degree == 0 else 2 if degree == 1 else 3 if degree == 2 else 4
        for row, col in comp:
            out[row][col] = color
    return out


def rule_mirror(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot apply canonical rule: " + "; ".join(errors))
    return _apply_degree_map(grid, 1)


def _degree_zero_as_two(grid: Grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot apply rival rule: " + "; ".join(errors))
    return _apply_degree_map(grid, 2)


def _has_degree_zero(grid: Grid) -> bool:
    return 0 in contact_degrees(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "has_degree_zero": _has_degree_zero,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "degree_zero_as_two": _degree_zero_as_two,
}
WITNESS_RIVALS = {"has_degree_zero": ["degree_zero_as_two"]}
# This rival exposed a generated-lesson hole, but canonical examples already
# refute it; only declare it at the lesson-assembly layer.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def semantic_observables(grid: Grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    degrees = contact_degrees(grid)
    return {
        "errors": [],
        "component_count": len(degrees),
        "degree_sequence": degrees,
        "has_degree_zero": 0 in degrees,
        "profile_colors": sorted({value for row in grid for value in row if value}),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject bad labels and lessons on which a declared shortcut survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output does not match contact-degree recoloring")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name} fits every demonstration")
    return sorted(set(reasons))


def _draw_from_degenerate(name, rng):
    del rng
    height, width = 10, 14
    grid = full_grid(height, width, 0)
    if name == "all_isolated":
        for cells, color, base in [
            ([(0, 0), (0, 1)], 1, (1, 1)),
            ([(0, 0), (1, 0)], 3, (5, 6)),
            ([(0, 0), (0, 1)], 5, (8, 11)),
        ]:
            for dr, dc in cells:
                grid[base[0] + dr][base[1] + dc] = color
        return grid
    if name == "all_touching":
        # Retained legacy degenerate: three isolated points; only color 1 appears.
        for cells, color, base in [
            ([(0, 0)], 1, (3, 4)),
            ([(0, 0)], 3, (3, 7)),
            ([(0, 0)], 5, (5, 5)),
        ]:
            for dr, dc in cells:
                grid[base[0] + dr][base[1] + dc] = color
        return grid
    if name == "single_component":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            grid[3 + dr][6 + dc] = 4
        return grid
    return grid
