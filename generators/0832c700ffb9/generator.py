"""Generator for canonical task ``0832c700ffb9`` (legacy ``f35d900a``).

Each nonzero input cell is a dot.  The authoritative rule rebuilds the output:

* every dot becomes the centre of a clipped 3x3 block;
* its ring uses the colour of the first other dot in the same row, or vanishes
  when no row partner exists;
* every same-row and same-column pair is joined by colour-5 dots at stride two.

The ordinary curriculum keeps rows/columns unambiguous (at most one partner),
uses a period-three teaching schedule repeated across five demonstrations, and
includes explicit counterexamples to plausible own-colour, one-rectangle, and
interior-only shortcuts. Unpaired dots are excluded because the canonical
Racket implementation emits ``#f`` rather than an ARC colour for their rings.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0832c700ffb9"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "781d2d53fe4d"

SUMMARY = (
    "Two-colour rectangle-corner dots expand into clipped 3x3 blocks; each "
    "ring copies the dot's same-row partner and colour-5 guides join aligned "
    "dots. A three-profile schedule teaches partner colour, multiple rectangles, "
    "and border clipping while preserving canonical shapes and integer outputs."
)

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

DOT_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
TEXTURES = ("plain", "same_rows", "two_rects", "border_rect", "two_rects_border")
SCHEDULE_PROFILES = ("two_rects", "border_rect", "two_rects_border")
CANONICAL_SHAPES = ((17, 16), (17, 14), (14, 14), (17, 18))
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES = TEXTURES
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

INVARIANTS = [
    "input uses exactly two nonzero colours, neither colour 5",
    "each rectangle is four complete corners on two rows and two columns",
    "rectangle row/column gaps are at least four cells",
    "a row or column contains at most two dots",
    "every dot has exactly one same-row partner, so outputs stay integer ARC grids",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "periodic canonical-shape anchor",
        "valid": "14..18",
    },
    "grid_w": {
        "type": "int",
        "default": "periodic canonical-shape anchor",
        "valid": "14..18",
    },
    "texture": {
        "type": "str",
        "default": "period-3 two_rects|border_rect|two_rects_border schedule",
        "valid": "plain|same_rows|two_rects|border_rect|two_rects_border",
        "doc": (
            "plain: one diagonal-colour rectangle; same_rows: one rectangle "
            "whose row partners match; two_rects: one of each arrangement; "
            "border_rect: one diagonal rectangle with a corner at (0,0); "
            "two_rects_border: one border diagonal rectangle plus one interior "
            "same-row rectangle."
        ),
    },
}


def _validate_replay_args(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject scalar aliases before schedule arithmetic or RNG construction."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Public deterministic profile schedule used by lesson audits."""
    _validate_replay_args(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _dots(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _render(
    grid: Sequence[Sequence[int]],
    *,
    ring_color: Callable[[tuple[int, int, int], list[tuple[int, int, int]]], int],
    include_guides: bool = True,
    dot_filter: Callable[[tuple[int, int, int], int, int], bool] | None = None,
) -> list[list[int]]:
    """Shared exact renderer used by the mirror and named rival rules."""
    h, w = len(grid), len(grid[0])
    all_dots = _dots(grid)
    dots = [
        dot for dot in all_dots
        if dot_filter is None or dot_filter(dot, h, w)
    ]
    result: dict[tuple[int, int], int] = {}

    for dr, dc, color in dots:
        ring = ring_color((dr, dc, color), dots)
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = dr + ddr, dc + ddc
                if 0 <= nr < h and 0 <= nc < w:
                    result[(nr, nc)] = color if ddr == ddc == 0 else ring

    if include_guides:
        for d1 in dots:
            for d2 in dots:
                if d1[0] == d2[0] and d1[1] < d2[1]:
                    row, left, right = d1[0], d1[1], d2[1]
                    midpoint = (left + right) / 2.0
                    col = left + 2
                    while col <= midpoint:
                        result[(row, col)] = 5
                        col += 2
                    col = right - 2
                    while col >= midpoint:
                        result[(row, col)] = 5
                        col -= 2
                if d1[1] == d2[1] and d1[0] < d2[0]:
                    col, top, bottom = d1[1], d1[0], d2[0]
                    midpoint = (top + bottom) / 2.0
                    row = top + 2
                    while row <= midpoint:
                        result[(row, col)] = 5
                        row += 2
                    row = bottom - 2
                    while row >= midpoint:
                        result[(row, col)] = 5
                        row -= 2

    return [[result.get((r, c), 0) for c in range(w)] for r in range(h)]


def _official_ring(dot, dots) -> int:
    row, col, _ = dot
    partner = next((other[2] for other in dots if other[0] == row and other[1] != col), None)
    return 0 if partner is None else partner


def _own_ring(dot, dots) -> int:
    del dots
    return dot[2]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket rule for lawful ARC grids."""
    return _render(grid, ring_color=_official_ring)


# Backward-compatible private name used by earlier review notes.
_mirror = rule_mirror


def _components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int, int]]]:
    """Components in the graph whose edges mean shared row or shared column."""
    dots = _dots(grid)
    unseen = set(range(len(dots)))
    components: list[list[tuple[int, int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        indexes = [start]
        while queue:
            index = queue.popleft()
            row, col, _ = dots[index]
            linked = [
                other for other in sorted(unseen)
                if dots[other][0] == row or dots[other][1] == col
            ]
            for other in linked:
                unseen.remove(other)
                queue.append(other)
                indexes.append(other)
        components.append([dots[index] for index in indexes])
    return components


def _rectangle_kind(component: Sequence[tuple[int, int, int]]) -> str | None:
    if len(component) != 4:
        return None
    rows = sorted({row for row, _, _ in component})
    cols = sorted({col for _, col, _ in component})
    if len(rows) != 2 or len(cols) != 2:
        return None
    by_pos = {(row, col): color for row, col, color in component}
    if set(by_pos) != {(row, col) for row in rows for col in cols}:
        return None
    if rows[1] - rows[0] < 4 or cols[1] - cols[0] < 4:
        return None
    top = (by_pos[(rows[0], cols[0])], by_pos[(rows[0], cols[1])])
    bottom = (by_pos[(rows[1], cols[0])], by_pos[(rows[1], cols[1])])
    if top[0] == bottom[1] and top[1] == bottom[0] and top[0] != top[1]:
        return "diagonal"
    if top[0] == top[1] and bottom[0] == bottom[1] and top[0] != bottom[0]:
        return "same_rows"
    return None


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colours 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared two-colour rectangle input manifold."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    h, w = len(grid), len(grid[0])
    if not (14 <= h <= 18 and 14 <= w <= 18):
        errors.append(f"grid shape {h}x{w} is outside the declared 14..18 domain")

    dots = _dots(grid)
    if len(dots) not in (4, 8):
        errors.append(f"grid has {len(dots)} dots; expected 4 or 8")
    colors = {color for _, _, color in dots}
    if 5 in colors:
        errors.append("colour 5 is reserved for output guides")
    if len(colors) != 2:
        errors.append(f"grid uses {len(colors)} nonzero colours; expected exactly 2")

    for row in range(h):
        count = sum(1 for dot_row, _, _ in dots if dot_row == row)
        if count > 2:
            errors.append(f"row {row} contains {count} dots; at most 2 are lawful")
    for col in range(w):
        count = sum(1 for _, dot_col, _ in dots if dot_col == col)
        if count > 2:
            errors.append(f"column {col} contains {count} dots; at most 2 are lawful")

    rectangles: list[str] = []
    for component in _components(grid):
        kind = _rectangle_kind(component)
        if kind is None:
            errors.append(
                "every aligned component must be a complete two-colour rectangle "
                "with diagonal or same-row colouring"
            )
        else:
            rectangles.append(kind)

    expected_rectangles = {4: 1, 8: 2}.get(len(dots))
    if expected_rectangles is not None and len(rectangles) != expected_rectangles:
        errors.append(
            f"found {len(rectangles)} legal rectangles; expected {expected_rectangles}"
        )
    if len(dots) == 8 and set(rectangles) != {"diagonal", "same_rows"}:
        errors.append("two-rectangle scenes must include one diagonal and one same-row rectangle")

    return errors


def strict_canonical_like(grid) -> list[str]:
    """The selected ordinary curriculum is exactly the validated manifold."""
    return self_check(grid)


def _single_rect_candidates(length: int, *, border: bool = False) -> list[tuple[int, int]]:
    if border:
        return [(0, end) for end in range(4, length)]
    return [
        (start, end)
        for start in range(1, length - 1)
        for end in range(start + 4, length - 1)
    ]


def _two_pair_candidates(length: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    pairs = _single_rect_candidates(length)
    result = []
    for index, first in enumerate(pairs):
        for second in pairs[index + 1:]:
            if all(abs(left - right) >= 3 for left in first for right in second):
                result.append((first, second))
    return result


def _border_and_inner_candidates(
    length: int,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """One border pair and one interior pair with non-overlapping 3x3 blocks."""
    result = []
    for border in _single_rect_candidates(length, border=True):
        for inner in _single_rect_candidates(length):
            if all(abs(left - right) >= 3 for left in border for right in inner):
                result.append((border, inner))
    return result


def _paint_rectangle(
    grid: list[list[int]],
    rows: tuple[int, int],
    cols: tuple[int, int],
    colors: tuple[int, int],
    arrangement: str,
) -> None:
    top, bottom = rows
    left, right = cols
    first, second = colors
    if arrangement == "diagonal":
        grid[top][left] = first
        grid[top][right] = second
        grid[bottom][left] = second
        grid[bottom][right] = first
    elif arrangement == "same_rows":
        grid[top][left] = first
        grid[top][right] = first
        grid[bottom][left] = second
        grid[bottom][right] = second
    else:  # internal programming error, not caller input
        raise ValueError(f"unknown rectangle arrangement {arrangement!r}")


def _draw_dimension(ctx, overrides: dict[str, Any], label: str, scheduled: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, 14, 18)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_replay_args(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_texture = schedule_profile(seed, sample_index, difficulty)
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str:
            raise TypeError("texture override must be a string")
        texture = ctx.draw_choice("texture", TEXTURES)
    else:
        texture = ctx.draw_choice("texture", (scheduled_texture,))

    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 3)
    shape = CANONICAL_SHAPES[
        (seed + sample_index + band_offset) % len(CANONICAL_SHAPES)
    ]
    height = _draw_dimension(ctx, overrides, "grid_h", shape[0])
    width = _draw_dimension(ctx, overrides, "grid_w", shape[1])
    rng = ctx.draw_rng(f"layout:{difficulty or 'mixed'}")
    colors = tuple(rng.sample(DOT_COLORS, 2))
    grid = full_grid(height, width, 0)

    if texture == "two_rects":
        row_sets = rng.choice(_two_pair_candidates(height))
        col_sets = rng.choice(_two_pair_candidates(width))
        _paint_rectangle(grid, row_sets[0], col_sets[0], colors, "diagonal")
        _paint_rectangle(grid, row_sets[1], col_sets[1], colors, "same_rows")
    elif texture == "two_rects_border":
        row_sets = rng.choice(_border_and_inner_candidates(height))
        col_sets = rng.choice(_border_and_inner_candidates(width))
        _paint_rectangle(grid, row_sets[0], col_sets[0], colors, "diagonal")
        _paint_rectangle(grid, row_sets[1], col_sets[1], colors, "same_rows")
    elif texture == "border_rect":
        rows = rng.choice(_single_rect_candidates(height, border=True))
        cols = rng.choice(_single_rect_candidates(width, border=True))
        _paint_rectangle(grid, rows, cols, colors, "diagonal")
    else:
        rows = rng.choice(_single_rect_candidates(height))
        cols = rng.choice(_single_rect_candidates(width))
        arrangement = "same_rows" if texture == "same_rows" else "diagonal"
        _paint_rectangle(grid, rows, cols, colors, arrangement)

    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal construction violated contract: {errors[0]}")
    return grid


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised public axis from a lawful returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors[0]}")
    components = _components(grid)
    rectangles = [component for component in components if len(component) == 4]
    has_border = any(
        row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1)
        for component in rectangles
        for row, col, _ in component
    )
    if len(rectangles) == 2:
        texture = "two_rects_border" if has_border else "two_rects"
    elif any(
        row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1)
        for row, col, _ in rectangles[0]
    ):
        texture = "border_rect"
    elif _rectangle_kind(rectangles[0]) == "same_rows":
        texture = "same_rows"
    else:
        texture = "plain"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "texture": texture}


def _rival_own_color_rings(grid):
    return _render(grid, ring_color=_own_ring)


def _first_component_filter(grid):
    components = _components(grid)
    keep = {(row, col) for row, col, _ in components[0]} if components else set()
    return lambda dot, _h, _w: (dot[0], dot[1]) in keep


def _rival_first_rectangle_only(grid):
    return _render(
        grid,
        ring_color=_official_ring,
        dot_filter=_first_component_filter(grid),
    )


def _rival_skip_border_dots(grid):
    return _render(
        grid,
        ring_color=_official_ring,
        dot_filter=lambda dot, h, w: dot[0] not in (0, h - 1) and dot[1] not in (0, w - 1),
    )


def _rival_no_guides(grid):
    return _render(grid, ring_color=_official_ring, include_guides=False)


def _has_different_row_partners(grid) -> bool:
    for row in range(len(grid)):
        values = [value for value in grid[row] if value != 0]
        if len(values) == 2 and values[0] != values[1]:
            return True
    return False


def _has_multiple_rectangles(grid) -> bool:
    return sum(len(component) == 4 for component in _components(grid)) >= 2


def _has_border_dot(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(row in (0, h - 1) or col in (0, w - 1) for row, col, _ in _dots(grid))


def _has_visible_guide(grid) -> bool:
    return any(5 in row for row in rule_mirror(grid))


SEMANTIC_RIVALS = {
    "own_color_rings": _rival_own_color_rings,
    "first_rectangle_only": _rival_first_rectangle_only,
    "skip_border_dots": _rival_skip_border_dots,
    "no_guides": _rival_no_guides,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("first_rectangle_only", "skip_border_dots")
}
SEMANTIC_WITNESSES = {
    "different_row_partner_color": _has_different_row_partners,
    "multiple_rectangles": _has_multiple_rectangles,
    "border_dot": _has_border_dot,
    "visible_guides": _has_visible_guide,
}
WITNESS_RIVALS = {
    "different_row_partner_color": ["own_color_rings"],
    "multiple_rectangles": ["first_rectangle_only"],
    "border_dot": ["skip_border_dots"],
    "visible_guides": ["no_guides"],
}


def _validate_lesson_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    issues = self_check(pair["input"])
    if issues:
        return [f"{label} input is outside the declared manifold: {issues[0]}"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output disagrees with the pinned rule mirror"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible competitor to be refuted by the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_lesson_pair(demo, f"demo {index}"))
    reasons.extend(_validate_lesson_pair(query, "query"))
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
