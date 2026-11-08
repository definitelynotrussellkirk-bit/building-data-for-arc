"""Semantic generator for ARC task 9041346d2bb8.

Every nonzero input cell is a color-coded seed.  Red (2) grows to a five-cell
orthogonal plus, green (3) grows to a five-cell diagonal X, and yellow (4)
grows to a filled 3x3 square.  Generated seeds are interior and their 3x3
footprints do not overlap, so every color-to-stencil branch remains visible.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9041346d2bb8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7bdc4b24da02"

SUMMARY = (
    "Expand every red seed into an orthogonal plus, every green seed into a "
    "diagonal X, and every yellow seed into a filled 3x3 square; combine all "
    "independent color-specific stencils on the original canvas."
)

INVARIANTS = [
    "the background is color 0 and the only seed colors are 2, 3, and 4",
    "every lawful lesson contains at least one seed of each color",
    "red 2 seeds use the five-cell orthogonal-plus stencil",
    "green 3 seeds use the five-cell diagonal-X stencil",
    "yellow 4 seeds use the filled 3x3-square stencil",
    "seed centers are interior and pairwise Chebyshev distance at least 3, so stencils do not overlap",
    "the returned grid belongs to one exact observable scene profile",
]

# The canonical profiles reproduce all public input dimensions and seed counts.
# The three generalized profiles rebut fixed-size, fixed-count, and fixed-layout
# shortcuts while keeping every color branch visible.
SCENE_SPECS = {
    "canonical_9x9_free3": (9, 9, 3, "free"),
    "wide_free5": (10, 13, 5, "free"),
    "canonical_9x10_free3": (9, 10, 3, "free"),
    "shared_row5": (9, 12, 5, "shared_row"),
    "canonical_10x10_free4": (10, 10, 4, "free"),
    "shared_column6": (12, 9, 6, "shared_column"),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
CANONICAL_PROFILES = frozenset(
    {
        "canonical_9x9_free3",
        "canonical_9x10_free3",
        "canonical_10x10_free4",
    }
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic sample-index cycle over all six profiles",
        "valid": "canonical_9x9_free3|wide_free5|canonical_9x10_free3|shared_row5|canonical_10x10_free4|shared_column6",
    }
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
MIN_STRICT_FRAC = 0.40
EXAMPLES_NEEDED = 4

_PLUS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_X_OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
_SQUARE_OFFSETS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
_OFFSETS_BY_COLOR = {2: _PLUS_OFFSETS, 3: _X_OFFSETS, 4: _SQUARE_OFFSETS}


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _seed_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _shared_axes(cells: Iterable[tuple[int, int, int]]):
    rows: dict[int, set[int]] = {}
    cols: dict[int, set[int]] = {}
    for r, c, color in cells:
        rows.setdefault(r, set()).add(color)
        cols.setdefault(c, set()).add(color)
    shared_rows = tuple(sorted(r for r, colors in rows.items() if colors == {2, 3, 4}))
    shared_cols = tuple(sorted(c for c, colors in cols.items() if colors == {2, 3, 4}))
    return shared_rows, shared_cols


def _layout_kind(cells: Iterable[tuple[int, int, int]]) -> str | None:
    shared_rows, shared_cols = _shared_axes(cells)
    if len(shared_rows) == 1 and not shared_cols:
        return "shared_row"
    if len(shared_cols) == 1 and not shared_rows:
        return "shared_column"
    if not shared_rows and not shared_cols:
        return "free"
    return None


def _profile_of(grid) -> str | None:
    if _grid_errors(grid):
        return None
    cells = _seed_cells(grid)
    signature = (len(grid), len(grid[0]), len(cells), _layout_kind(cells))
    for name, spec in SCENE_SPECS.items():
        if signature == spec:
            return name
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding seed scenes."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    cells = _seed_cells(grid)
    colors = {color for _, _, color in cells}

    if colors != {2, 3, 4}:
        errors.append(
            f"seed palette must contain exactly colors {{2,3,4}}, found {sorted(colors)}"
        )
    if not 3 <= len(cells) <= 6:
        errors.append(f"expected 3..6 seed cells, found {len(cells)}")
    if any(r in (0, height - 1) or c in (0, width - 1) for r, c, _ in cells):
        errors.append("every seed must have a one-cell margin so its full stencil is visible")

    positions = [(r, c) for r, c, _ in cells]
    for (r1, c1), (r2, c2) in combinations(positions, 2):
        if max(abs(r1 - r2), abs(c1 - c2)) < 3:
            errors.append(
                f"seed footprints overlap or touch ambiguously at {(r1, c1)} and {(r2, c2)}"
            )
            break

    layout = _layout_kind(cells)
    if layout is None:
        errors.append("scene must have either no all-color row/column or exactly one such axis")
    profile = _profile_of(grid)
    if profile is None:
        errors.append(
            f"grid signature {(height, width, len(cells), layout)!r} is not a declared scene profile"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] exactly on the public-size/public-count canonical manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = _profile_of(grid)
    if profile not in CANONICAL_PROFILES:
        reasons.append(f"scene profile {profile!r} is generalized rather than canonical")
    return reasons


def canonical_profile_signature(grid):
    profile = _profile_of(grid)
    return profile if profile in CANONICAL_PROFILES else None


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    assert profile is not None
    return {"scene_profile": profile}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket rule remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for r, c, color in sorted(_seed_cells(grid)):
        for dr, dc in _OFFSETS_BY_COLOR[color]:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = color
    return output


def _witness_red_plus(grid) -> bool:
    return not self_check(grid) and any(color == 2 for _, _, color in _seed_cells(grid))


def _witness_green_x(grid) -> bool:
    return not self_check(grid) and any(color == 3 for _, _, color in _seed_cells(grid))


def _witness_yellow_square(grid) -> bool:
    return not self_check(grid) and any(color == 4 for _, _, color in _seed_cells(grid))


def _witness_repeated_color(grid) -> bool:
    if self_check(grid):
        return False
    counts = {color: 0 for color in (2, 3, 4)}
    for _, _, color in _seed_cells(grid):
        counts[color] += 1
    return max(counts.values()) >= 2


def _witness_layout(expected: str):
    return lambda grid: not self_check(grid) and _layout_kind(_seed_cells(grid)) == expected


SEMANTIC_WITNESSES = {
    "red_plus_branch": _witness_red_plus,
    "green_diagonal_x_branch": _witness_green_x,
    "yellow_filled_square_branch": _witness_yellow_square,
    "repeated_color_independent_growth": _witness_repeated_color,
    "free_placement": _witness_layout("free"),
    "same_row_color_contrast": _witness_layout("shared_row"),
    "same_column_color_contrast": _witness_layout("shared_column"),
}


def _competitor_output(grid, offsets_by_color) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for r, c, color in sorted(_seed_cells(grid)):
        offsets = offsets_by_color[color]
        for dr, dc in offsets:
            output[r + dr][c + dc] = color
    return output


def _all_stencil(offsets):
    return {2: offsets, 3: offsets, 4: offsets}


_LESSON_COMPETITORS = {
    "all colors grow as pluses": _all_stencil(_PLUS_OFFSETS),
    "all colors grow as diagonal Xs": _all_stencil(_X_OFFSETS),
    "all colors grow as filled squares": _all_stencil(_SQUARE_OFFSETS),
    "red and green stencil meanings are swapped": {
        2: _X_OFFSETS,
        3: _PLUS_OFFSETS,
        4: _SQUARE_OFFSETS,
    },
    "green and yellow stencil meanings are swapped": {
        2: _PLUS_OFFSETS,
        3: _SQUARE_OFFSETS,
        4: _X_OFFSETS,
    },
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named plausible color/stencil rival alive."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    demo_profiles: set[str] = set()
    demo_layouts: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the color-coded stencil rule")
        profile = _profile_of(demo["input"])
        assert profile is not None
        demo_profiles.add(profile)
        demo_layouts.add(SCENE_SPECS[profile][3])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])

    for name, mapping in _LESSON_COMPETITORS.items():
        survives = all(
            _competitor_output(demo["input"], mapping) == demo["output"]
            for demo in demos
            if isinstance(demo, dict) and "input" in demo and "output" in demo
        )
        if survives and _competitor_output(query["input"], mapping) != query_answer:
            reasons.append(
                f"competing rule '{name}' matches every demo but answers the query differently"
            )

    if len(demo_profiles) < 3:
        reasons.append("demonstrations do not vary grid size and seed-count profiles enough")
    if len(demo_layouts) < 2:
        reasons.append("demonstrations do not vary seed layout enough to rebut fixed-position rules")
    return reasons


def _separated(position: tuple[int, int], chosen: list[tuple[int, int]]) -> bool:
    r, c = position
    return all(max(abs(r - rr), abs(c - cc)) >= 3 for rr, cc in chosen)


def _shared_anchor_options(height: int, width: int, layout: str):
    if layout == "shared_row":
        triples = [
            cols
            for cols in combinations(range(1, width - 1), 3)
            if all(abs(a - b) >= 3 for a, b in combinations(cols, 2))
        ]
        return [tuple((row, col) for col in cols) for row in range(1, height - 1) for cols in triples]
    if layout == "shared_column":
        triples = [
            rows
            for rows in combinations(range(1, height - 1), 3)
            if all(abs(a - b) >= 3 for a, b in combinations(rows, 2))
        ]
        return [tuple((row, col) for row in rows) for col in range(1, width - 1) for rows in triples]
    return []


def _choose_positions(rng, height: int, width: int, count: int, layout: str):
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    for _ in range(512):
        chosen: list[tuple[int, int]] = []
        if layout in ("shared_row", "shared_column"):
            anchors = rng.choice(_shared_anchor_options(height, width, layout))
            chosen.extend(anchors)
        candidates = interior[:]
        rng.shuffle(candidates)
        for position in candidates:
            if position in chosen or not _separated(position, chosen):
                continue
            if layout == "free":
                r, c = position
                if sum(rr == r for rr, _ in chosen) >= 2:
                    continue
                if sum(cc == c for _, cc in chosen) >= 2:
                    continue
            chosen.append(position)
            if len(chosen) == count:
                return chosen
    raise RuntimeError(
        f"could not place {count} separated seeds in {height}x{width} for {layout}"
    )


def _choose_colored_cells(rng, positions, layout: str):
    for _ in range(256):
        colors = [2, 3, 4]
        rng.shuffle(colors)
        colors.extend(rng.choice((2, 3, 4)) for _ in positions[3:])
        if max(colors.count(color) for color in (2, 3, 4)) > 3:
            continue
        cells = [(r, c, color) for (r, c), color in zip(positions, colors)]
        if _layout_kind(cells) == layout:
            return cells
    raise RuntimeError(f"could not assign colors for observable layout {layout}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket owns every output label."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    height, width, count, layout = SCENE_SPECS[profile]

    rng = ctx.draw_rng(f"layout:{band}:{profile}")
    positions = _choose_positions(rng, height, width, count, layout)
    cells = _choose_colored_cells(rng, positions, layout)
    grid = full_grid(height, width, 0)
    for r, c, color in cells:
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid scene: {errors}")
    return [row[:] for row in grid]
