"""Input sampler for vertical reflection across a full color-5 divider.

The unchanged Racket authority copies every nonzero cell above the divider to
its vertically reflected location below the divider.  This module generates
only lawful input grids; it does not label outputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "774e0d59a5ff"
TASK_ID = GENERATOR_ID
RULE_HASH = "73a966cdbca0"
VERSION = "2.0.0"
SUMMARY = (
    "An odd-height grid contains a sparse colored motif above a full color-5 "
    "divider and an empty panel below. Reflect every nonzero motif cell "
    "vertically across the divider, preserving its column and color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is 9 or 11 rows high and 8..11 columns wide",
    "the center row is entirely color 5 and color 5 appears nowhere else",
    "the top panel contains 4..8 marks in 1..4 non-divider colors",
    "the bottom panel is empty before transformation",
    "the top motif is not vertically symmetric, so reflection changes the grid",
]

AXES = {
    "panel_h": {"type": "int", "default": "weighted 4..5", "valid": "4..5"},
    "grid_w": {"type": "int", "default": "weighted 8..11", "valid": "8..11"},
    "marks": {"type": "int", "default": "difficulty-weighted 4..8", "valid": "4..8"},
    "n_colors": {"type": "int", "default": "weighted 1..4", "valid": "1..4"},
    "motif_style": {"type": "str", "default": "keyed random", "valid": "points|mixed"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_MARK_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_DIFFICULTIES = (None, "easy", "medium", "hard")
_STYLES = ("points", "mixed")


def _genuine_int(name: str, value: Any, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _genuine_int("seed", seed, minimum=0)
    _genuine_int("sample_index", sample_index, minimum=0)
    if difficulty not in _DIFFICULTIES or (difficulty is not None and type(difficulty) is not str):
        raise ValueError(f"difficulty must be one of {_DIFFICULTIES!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_ranges = {
        "panel_h": (4, 5),
        "grid_w": (8, 11),
        "marks": (4, 8),
        "n_colors": (1, 4),
    }
    for name, (lo, hi) in integer_ranges.items():
        value = overrides.get(name)
        if value is None:
            continue
        _genuine_int(name, value)
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    style = overrides.get("motif_style")
    if style is not None:
        if type(style) is not str:
            raise TypeError("motif_style must be a string")
        if style not in _STYLES:
            raise ValueError(f"motif_style must be one of {_STYLES!r}")


def _weighted_options(domain: tuple[Any, ...], favored: tuple[Any, ...]) -> tuple[Any, ...]:
    """Retain the full override domain while biasing ordinary keyed draws."""
    return domain + favored


def _draw_axes(ctx, difficulty: str | None) -> tuple[int, int, int, int, str]:
    # The shape/color weights preserve substantial support for the five
    # canonical size/palette profiles without replaying any canonical grid.
    panel_h = ctx.draw_choice("panel_h", _weighted_options((4, 5), (4, 5)))
    grid_w = ctx.draw_choice("grid_w", _weighted_options((8, 9, 10, 11), (9, 10, 11)))

    if difficulty == "easy":
        mark_favored = (4, 4, 5)
        color_favored = (1, 2, 4, 4)
    elif difficulty == "hard":
        mark_favored = (7, 8, 8)
        color_favored = (3, 4, 4, 4)
    else:
        mark_favored = (4, 6, 8)
        color_favored = (2, 3, 4, 4)

    marks = ctx.draw_choice("marks", _weighted_options((4, 5, 6, 7, 8), mark_favored))
    n_colors = ctx.draw_choice("n_colors", _weighted_options((1, 2, 3, 4), color_favored))
    motif_style = ctx.draw_choice("motif_style", _weighted_options(_STYLES, _STYLES))
    return panel_h, grid_w, marks, n_colors, motif_style


def _positions(panel_h: int, grid_w: int, marks: int, style: str, rng) -> list[tuple[int, int]]:
    """Construct exact mark count/style and a visible vertical-order witness."""
    anchor_col = rng.randrange(grid_w)
    anchor = (0, anchor_col)
    mirror_anchor = (panel_h - 1, anchor_col)

    if style == "points":
        # One checkerboard parity is an orthogonally independent set.  Choose
        # the anchor parity and explicitly reserve its mirror in odd-height
        # panels so vertical reversal cannot reproduce the same top panel.
        parity = anchor_col % 2
        pool = [
            (row, col)
            for row in range(panel_h)
            for col in range(grid_w)
            if (row + col) % 2 == parity and (row, col) != mirror_anchor
        ]
        if anchor not in pool or len(pool) < marks:
            raise RuntimeError("point-style construction unexpectedly lacks capacity")
        remainder = [cell for cell in pool if cell != anchor]
        return [anchor, *rng.sample(remainder, marks - 1)]

    # A forced horizontal pair makes the mixed style observable.  Reserving
    # both reflected cells makes the top panel provably non-symmetric.
    pair_col = anchor_col + 1 if anchor_col + 1 < grid_w else anchor_col - 1
    pair = (0, pair_col)
    forbidden = {mirror_anchor, (panel_h - 1, pair_col)}
    pool = [
        (row, col)
        for row in range(panel_h)
        for col in range(grid_w)
        if (row, col) not in forbidden and (row, col) not in {anchor, pair}
    ]
    return [anchor, pair, *rng.sample(pool, marks - 2)]


def _assign_colors(grid: list[list[int]], positions: list[tuple[int, int]], n_colors: int, rng) -> None:
    palette = rng.sample(_MARK_COLORS, n_colors)
    shuffled_positions = list(positions)
    rng.shuffle(shuffled_positions)
    for index, (row, col) in enumerate(shuffled_positions):
        # Seed each requested color once, then use the same keyed RNG freely.
        grid[row][col] = palette[index] if index < n_colors else rng.choice(palette)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    panel_h, grid_w, marks, n_colors, motif_style = _draw_axes(ctx, difficulty)
    height = 2 * panel_h + 1
    grid = full_grid(height, grid_w, 0)
    for col in range(grid_w):
        grid[panel_h][col] = 5

    positions = _positions(
        panel_h,
        grid_w,
        marks,
        motif_style,
        ctx.draw_rng("layout"),
    )
    _assign_colors(grid, positions, n_colors, ctx.draw_rng("colors"))
    return grid


def _valid_arc_color(value: Any) -> bool:
    return type(value) is int and 0 <= value <= 9


def _shape_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], 0, 0
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"], 0, 0
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], 0, 0
    if any(not _valid_arc_color(value) for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"], 0, 0
    return [], len(grid), width


def _top_marks(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    divider = len(grid) // 2
    return [
        (row, col, value)
        for row in range(divider)
        for col, value in enumerate(grid[row])
        if value != 0
    ]


def _motif_style(grid: list[list[int]]) -> str:
    divider = len(grid) // 2
    occupied = {(row, col) for row, col, _ in _top_marks(grid)}
    for row, col in occupied:
        if any(
            (row + dr, col + dc) in occupied
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            return "mixed"
    return "points"


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every advertised exact axis from returned pixels."""
    errors, height, width = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    divider = height // 2
    marks = _top_marks(grid)
    return {
        "panel_h": divider,
        "grid_w": width,
        "marks": len(marks),
        "n_colors": len({value for _, _, value in marks}),
        "motif_style": _motif_style(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input grammar and requested exact axes."""
    del difficulty
    shape_errors, height, width = _shape_errors(grid)
    if shape_errors:
        return shape_errors

    errors: list[str] = []
    if height not in (9, 11):
        errors.append(f"expected height 9 or 11; got {height}")
    if not 8 <= width <= 11:
        errors.append(f"expected width 8..11; got {width}")
    if height % 2 == 0:
        errors.append("height must be odd")
        return errors

    divider = height // 2
    if any(value != 5 for value in grid[divider]):
        errors.append("center divider row must be entirely color 5")
    extra_fives = [
        (row, col)
        for row, values in enumerate(grid)
        if row != divider
        for col, value in enumerate(values)
        if value == 5
    ]
    if extra_fives:
        errors.append(f"color 5 may appear only in the divider row; found {len(extra_fives)} extra cells")
    if any(value != 0 for row in grid[divider + 1 :] for value in row):
        errors.append("bottom panel must be empty")

    marks = _top_marks(grid)
    if not 4 <= len(marks) <= 8:
        errors.append(f"top panel must contain 4..8 marks; got {len(marks)}")
    mark_colors = {value for _, _, value in marks}
    if not 1 <= len(mark_colors) <= 4:
        errors.append(f"top motif must use 1..4 colors; got {len(mark_colors)}")
    if any(value not in _MARK_COLORS for _, _, value in marks):
        errors.append("top marks must use nonzero non-divider ARC colors")

    top = grid[:divider]
    if top == list(reversed(top)):
        errors.append("top motif must not be vertically symmetric")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict) and not errors:
        observed = observe_overrides(grid)
        for name, requested in overrides.items():
            if requested is not None and name in observed and observed[name] != requested:
                errors.append(
                    f"override {name} requested {requested!r}, observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for semantic diagnostics; Racket is authority."""
    reasons = self_check(grid)
    if reasons:
        raise ValueError("rule_mirror input is outside the task grammar: " + "; ".join(reasons))
    output = deepcopy(grid)
    divider = len(grid) // 2
    for row in range(divider):
        target_row = 2 * divider - row
        for col, value in enumerate(grid[row]):
            if value != 0:
                output[target_row][col] = value
    return output


def _copy_without_reflection(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: copy top rows below in the same row order."""
    output = deepcopy(grid)
    divider = len(grid) // 2
    for row in range(divider):
        target_row = divider + 1 + row
        for col, value in enumerate(grid[row]):
            if value != 0:
                output[target_row][col] = value
    return output


def _vertical_order_witness(grid: list[list[int]]) -> bool:
    if self_check(grid):
        return False
    divider = len(grid) // 2
    return grid[:divider] != list(reversed(grid[:divider]))


SEMANTIC_WITNESSES = {"vertical_order": _vertical_order_witness}
SEMANTIC_RIVALS = {"copy_without_reflection": _copy_without_reflection}
WITNESS_RIVALS = {"vertical_order": ["copy_without_reflection"]}
LESSON_COMPETITORS = {"copy_without_reflection": _copy_without_reflection}


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and one demonstrated vertical-order counterexample."""
    reasons: list[str] = []
    rival_refuted = False
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
            if expected != demo["output"]:
                reasons.append(f"demo {index} output disagrees with vertical reflection")
            if _copy_without_reflection(demo["input"]) != expected:
                rival_refuted = True
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is invalid: {exc}")
    try:
        expected_query = rule_mirror(query["input"])
        if "output" in query and query["output"] != expected_query:
            reasons.append("query output disagrees with vertical reflection")
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is invalid: {exc}")
    if not rival_refuted:
        reasons.append("demonstrations do not refute copying rows without reflection")
    return reasons
