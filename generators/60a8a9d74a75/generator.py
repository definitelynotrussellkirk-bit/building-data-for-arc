"""Canonical-aligned input sampler for ``60a8a9d74a75``.

The unchanged Racket authority examines every 4-connected zero component.
It ignores adjacent 0 and 8 cells, and fills the component exactly when the
remaining cardinal-neighbour colours have one distinct value.

Two scheduled profiles reproduce the canonical 8-wall / one-seed chamber
idiom.  Two composite profiles retain that idiom's semantics while exposing
branches hidden by the canonical demonstrations: repeated same-colour seeds,
a mixed-colour no-fill chamber, an edge-connected positive region, and a
zero pocket bounded directly by a non-8 colour.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "60a8a9d74a75"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "49411595dc9e"

SUMMARY = (
    "Flood each 4-connected zero region only when its distinct cardinal "
    "neighbours, after ignoring 0 and wall colour 8, contain exactly one "
    "colour. Scheduled canonical profiles use 8-walled chambers with one "
    "seed; composite profiles additionally teach repeated same-colour seeds, "
    "mixed-colour no-fill regions, edge-connected fills, and coloured walls."
)

INVARIANTS = [
    "the canonical Racket program pinned by RULE_HASH is the label authority",
    "canonical profiles contain two 8-walled chambers and one seed per chamber",
    "each composite has exactly four zero regions covering all hidden rule branches",
    "all ordinary four-pair lessons contain both canonical and composite evidence",
]

SCHEDULE_PROFILES = (
    "canonical_rows",
    "composite_open_left",
    "canonical_cols",
    "composite_open_top",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

AXES = {
    "profile": {
        "type": "str",
        "default": "four-profile teaching schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
Region = dict[str, object]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NON_WALL_COLORS = tuple(c for c in range(1, 10) if c != 8)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic semantic profile for an ordinary draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_difficulty(difficulty: object) -> None:
    if difficulty is None or difficulty in {"easy", "medium", "hard"}:
        return
    if type(difficulty) in {int, float}:
        return
    raise ValueError("difficulty must be None, easy, medium, hard, or a numeric hint")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    if "profile" in overrides:
        value = overrides["profile"]
        if type(value) is not str:
            raise TypeError("profile override must be a string")
        if value not in SCHEDULE_PROFILES:
            raise ValueError(f"profile must be one of {SCHEDULE_PROFILES}, got {value!r}")


def _common_errors(grid: object) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9 (booleans are not colours)"]
    return []


def _zero_regions(grid: Grid) -> list[Region]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    regions: list[Region] = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    queue.append(point)
        colored: dict[Cell, int] = {}
        walls: set[Cell] = set()
        for r, c in cells:
            for dr, dc in _CARDINAL:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w):
                    continue
                value = grid[nr][nc]
                if value == 8:
                    walls.add((nr, nc))
                elif value != 0:
                    colored[(nr, nc)] = value
        regions.append({
            "cells": cells,
            "touches_edge": any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells),
            "edge_sides": frozenset(
                side
                for r, c in cells
                for side, hit in (
                    ("top", r == 0), ("bottom", r == h - 1),
                    ("left", c == 0), ("right", c == w - 1),
                )
                if hit
            ),
            "neighbor_cells": frozenset(colored),
            "neighbor_values": dict(colored),
            "colors": frozenset(colored.values()),
            "wall_cells": frozenset(walls),
        })
    return regions


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror of the pinned rule; Racket remains authority."""
    errors = _common_errors(grid)
    if errors:
        raise ValueError(errors[0])
    out = deepcopy(grid)
    for region in _zero_regions(grid):
        colors = region["colors"]
        if len(colors) == 1:
            color = next(iter(colors))
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def _canonical_errors(grid: Grid) -> list[str]:
    h, w = len(grid), len(grid[0])
    if h < 5 or w < 5:
        return ["canonical chamber grids must be at least 5x5"]
    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)):
        return ["canonical chamber grids require top and bottom 8 walls"]
    if any(grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)):
        return ["canonical chamber grids require left and right 8 walls"]
    regions = _zero_regions(grid)
    if len(regions) < 2:
        return ["canonical chamber grids require at least two zero chambers"]
    colored_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                     if value not in (0, 8)]
    if len(colored_cells) != len(regions):
        return ["canonical chambers require exactly one coloured seed per zero region"]
    for region in regions:
        if region["touches_edge"]:
            return ["canonical zero chambers may not touch the grid edge"]
        if len(region["colors"]) != 1 or len(region["neighbor_cells"]) != 1:
            return ["each canonical chamber must touch exactly one coloured seed cell"]
        if not region["wall_cells"]:
            return ["each canonical chamber must be partitioned by colour-8 walls"]
    return []


def _composite_errors(grid: Grid) -> list[str]:
    regions = _zero_regions(grid)
    if len(regions) != 4:
        return [f"composite profiles require exactly four zero regions, found {len(regions)}"]
    repeated = [x for x in regions if not x["touches_edge"] and len(x["colors"]) == 1
                and len(x["neighbor_cells"]) == 2]
    mixed = [x for x in regions if len(x["colors"]) == 2 and len(x["neighbor_cells"]) == 2]
    open_positive = [x for x in regions if x["touches_edge"] and len(x["colors"]) == 1
                     and len(x["neighbor_cells"]) == 1]
    colored_boundary = [x for x in regions if not x["touches_edge"] and len(x["colors"]) == 1
                        and len(x["neighbor_cells"]) >= 12]
    if len(repeated) != 1:
        return ["composite requires one enclosed region with two same-colour seed cells"]
    if len(mixed) != 1:
        return ["composite requires one region touched by two different colours"]
    if len(open_positive) != 1:
        return ["composite requires one edge-connected region with one coloured seed"]
    if len(colored_boundary) != 1:
        return ["composite requires one zero pocket bounded by a non-8 colour"]
    if open_positive[0]["edge_sides"] not in (frozenset({"left"}), frozenset({"top"})):
        return ["composite open region must touch exactly the left or top edge"]
    non_wall = {value for row in grid for value in row if value not in (0, 8)}
    if len(non_wall) != 5:
        return [f"composite requires five distinct non-wall colours, found {len(non_wall)}"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical chamber grids and the two explicit composite profiles."""
    del difficulty, meta
    common = _common_errors(grid)
    if common:
        return common
    canonical = _canonical_errors(grid)
    if not canonical:
        return []
    composite = _composite_errors(grid)
    if not composite:
        return []
    return [
        "grid is outside both supported manifolds",
        f"canonical: {canonical[0]}",
        f"composite: {composite[0]}",
    ]


def strict_canonical_like(grid) -> list[str]:
    common = _common_errors(grid)
    if common:
        return common
    return _canonical_errors(grid)


def _blank(h: int, w: int, value: int = 8) -> Grid:
    return [[value for _ in range(w)] for _ in range(h)]


def _carve(grid: Grid, r0: int, r1: int, c0: int, c1: int) -> None:
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = 0


def _choose_seed(rng, cells: list[Cell], count: int) -> list[Cell]:
    return rng.sample(cells, count)


def _canonical_rows(ctx) -> Grid:
    grid = _blank(10, 10)
    _carve(grid, 1, 4, 1, 8)
    _carve(grid, 6, 8, 1, 8)
    colors = ctx.draw_distinct_colors("canonical_rows_colors", n=2, exclude=(0, 8))
    top = ctx.draw_rng("canonical_rows_top_seed").choice([(r, c) for r in range(1, 5) for c in range(1, 9)])
    bottom = ctx.draw_rng("canonical_rows_bottom_seed").choice([(r, c) for r in range(6, 9) for c in range(1, 9)])
    grid[top[0]][top[1]] = colors[0]
    grid[bottom[0]][bottom[1]] = colors[1]
    return grid


def _canonical_cols(ctx) -> Grid:
    grid = _blank(9, 11)
    _carve(grid, 1, 7, 1, 4)
    _carve(grid, 1, 7, 6, 9)
    colors = ctx.draw_distinct_colors("canonical_cols_colors", n=2, exclude=(0, 8))
    left = ctx.draw_rng("canonical_cols_left_seed").choice([(r, c) for r in range(1, 8) for c in range(1, 5)])
    right = ctx.draw_rng("canonical_cols_right_seed").choice([(r, c) for r in range(1, 8) for c in range(6, 10)])
    grid[left[0]][left[1]] = colors[0]
    grid[right[0]][right[1]] = colors[1]
    return grid


def _pad_limit(difficulty: object) -> tuple[int, int]:
    if difficulty == "easy":
        return 0, 1
    if difficulty == "medium":
        return 1, 3
    if difficulty == "hard":
        return 2, 4
    return 0, 4


def _composite_open_left(ctx, difficulty: object) -> Grid:
    lo, hi = _pad_limit(difficulty)
    pad_bottom = ctx.draw_rng("composite_pad_bottom").randint(lo, hi)
    pad_right = ctx.draw_rng("composite_pad_right").randint(lo, hi)
    grid = _blank(17 + pad_bottom, 22 + pad_right)
    colors = ctx.draw_distinct_colors("composite_colors", n=5, exclude=(0, 8))

    # A: two same-colour seeds; distinct neighbour colour set still has size one.
    # Seeds stay one cell away from the chamber wall so two draws cannot pinch
    # off a corner zero cell into an accidental fifth component.
    _carve(grid, 1, 7, 1, 8)
    candidates_a = [(r, c) for r in range(2, 7) for c in range(2, 8)]
    for r, c in _choose_seed(ctx.draw_rng("same_color_seeds"), candidates_a, 2):
        grid[r][c] = colors[0]

    # B: two different colours touch one zero component, so it must stay zero.
    _carve(grid, 1, 7, 12, 20)
    candidates_b = [(r, c) for r in range(2, 7) for c in range(13, 20)]
    mixed_points = _choose_seed(ctx.draw_rng("mixed_color_seeds"), candidates_b, 2)
    grid[mixed_points[0][0]][mixed_points[0][1]] = colors[1]
    grid[mixed_points[1][0]][mixed_points[1][1]] = colors[2]

    # C: a positive region connected to the left edge; enclosure is irrelevant.
    _carve(grid, 9, 15, 0, 8)
    open_seed = ctx.draw_rng("open_region_seed").choice(
        [(r, c) for r in range(10, 15) for c in range(1, 8)]
    )
    grid[open_seed[0]][open_seed[1]] = colors[3]

    # D: a coloured frame is itself the only non-8 neighbour; no interior seed.
    frame_color = colors[4]
    for r in range(9, 16):
        for c in range(12, 21):
            grid[r][c] = frame_color if r in (9, 15) or c in (12, 20) else 0
    return grid


def _rotate_clockwise(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _profile_from_grid(grid: Grid) -> str:
    if not _canonical_errors(grid):
        h, w = len(grid), len(grid[0])
        if (h, w) == (10, 10) and all(value == 8 for value in grid[5]):
            return "canonical_rows"
        if (h, w) == (9, 11) and all(row[5] == 8 for row in grid):
            return "canonical_cols"
        raise ValueError("canonical-like grid is not one of the generated exact profiles")
    if not _composite_errors(grid):
        open_region = next(x for x in _zero_regions(grid) if x["touches_edge"])
        if open_region["edge_sides"] == frozenset({"left"}):
            return "composite_open_left"
        if open_region["edge_sides"] == frozenset({"top"}):
            return "composite_open_top"
    raise ValueError("grid is outside the generated profile domain")


def observe_overrides(grid: Grid) -> dict[str, object]:
    return {"profile": _profile_from_grid(grid)}


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = ctx.draw_choice("profile", SCHEDULE_PROFILES if "profile" in overrides else (scheduled,))
    if profile == "canonical_rows":
        grid = _canonical_rows(ctx)
    elif profile == "canonical_cols":
        grid = _canonical_cols(ctx)
    else:
        grid = _composite_open_left(ctx, difficulty)
        if profile == "composite_open_top":
            grid = _rotate_clockwise(grid)
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    observed = observe_overrides(grid)
    if observed != {"profile": profile}:
        raise RuntimeError(f"observable axis mismatch: expected {profile!r}, observed {observed}")
    return grid


def _rival_apply(grid: Grid, predicate: Callable[[Region], bool], choose: Callable[[Region], int]) -> Grid:
    out = deepcopy(grid)
    for region in _zero_regions(grid):
        if predicate(region):
            color = choose(region)
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def _single_seed_8_chambers(grid: Grid) -> Grid:
    return _rival_apply(
        grid,
        lambda x: (not x["touches_edge"] and len(x["neighbor_cells"]) == 1 and bool(x["wall_cells"])),
        lambda x: next(iter(x["colors"])),
    )


def _exactly_one_colored_cell(grid: Grid) -> Grid:
    return _rival_apply(
        grid,
        lambda x: len(x["neighbor_cells"]) == 1,
        lambda x: next(iter(x["colors"])),
    )


def _enclosed_only(grid: Grid) -> Grid:
    return _rival_apply(
        grid,
        lambda x: not x["touches_edge"] and len(x["colors"]) == 1,
        lambda x: next(iter(x["colors"])),
    )


def _first_color_wins(grid: Grid) -> Grid:
    return _rival_apply(
        grid,
        lambda x: bool(x["colors"]),
        lambda x: min(x["colors"]),
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "single_seed_8_chambers": _single_seed_8_chambers,
    "exactly_one_colored_cell": _exactly_one_colored_cell,
    "enclosed_only": _enclosed_only,
    "first_color_wins": _first_color_wins,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_and(predicate: Callable[[list[Region]], bool], grid: Grid) -> bool:
    return not self_check(grid) and predicate(_zero_regions(grid))


SEMANTIC_WITNESSES = {
    "same_color_multiple_seeds": lambda grid: _valid_and(
        lambda regions: any(not x["touches_edge"] and len(x["colors"]) == 1
                            and len(x["neighbor_cells"]) == 2 for x in regions), grid),
    "edge_connected_positive": lambda grid: _valid_and(
        lambda regions: any(x["touches_edge"] and len(x["colors"]) == 1 for x in regions), grid),
    "mixed_color_no_fill": lambda grid: _valid_and(
        lambda regions: any(len(x["colors"]) > 1 for x in regions), grid),
    "colored_boundary_positive": lambda grid: _valid_and(
        lambda regions: any(len(x["colors"]) == 1 and len(x["neighbor_cells"]) >= 12
                            for x in regions), grid),
}
WITNESS_RIVALS = {
    "same_color_multiple_seeds": ["single_seed_8_chambers", "exactly_one_colored_cell"],
    "edge_connected_positive": ["single_seed_8_chambers", "enclosed_only"],
    "mixed_color_no_fill": ["first_color_wins"],
    "colored_boundary_positive": ["single_seed_8_chambers", "exactly_one_colored_cell"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to falsify every declared canonical shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the supported domain")
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output does not match the pinned rule")
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != truth
    for name, value in refuted.items():
        if not value:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
