"""Generator for f812a7b32f47 — fill marked frame intersections.

The authoritative rule takes the bbox of all nonzero cells.  Color 2 on the
bbox's left edge marks rows; color 3 on its top edge marks columns; their
interior Cartesian intersections become color 7.

Ordinary examples also put marker-colored distractors on the *bottom* and
*right* edges.  Those cells do not affect the rule, but they falsify the
canonical shortcut "use every non-corner row containing 2 and every
non-corner column containing 3".
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f812a7b32f47"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6fdb2408e34a"

SUMMARY = (
    "A hollow nonzero frame floats on a 0 background. Color-2 cells on the "
    "left bbox edge mark rows and color-3 cells on the top bbox edge mark "
    "columns; the rule paints color 7 at every marked interior crossing. "
    "Bottom-edge 2s and right-edge 3s are lawful distractors: they preserve "
    "the bbox rule while refuting an anywhere-marker shortcut."
)

INVARIANTS = [
    "background is 0",
    "the nonzero bbox is one hollow rectangular frame",
    "top-edge interior color-3 cells are the only column markers",
    "left-edge interior color-2 cells are the only row markers",
    "bottom-edge color-2 and right-edge color-3 cells are inert distractors",
    "the frame interior starts empty",
]

FRAME_COLORS = (1, 4, 5, 6, 8, 9)
FRAME_HEIGHTS = tuple(range(5, 14))
FRAME_WIDTHS = tuple(range(6, 16))
TOP_COUNTS = (1, 2, 3, 4)
LEFT_COUNTS = (1, 2, 3)
DISTRACTOR_COUNTS = (1, 2, 3, 4)
CANONICAL_CANVASES = ((7, 11), (8, 10), (9, 12), (10, 13), (11, 11))

AXES = {
    "frame_h": {
        "type": "int",
        "default": "difficulty-weighted exact draw",
        "valid": "5..13",
    },
    "frame_w": {
        "type": "int",
        "default": "difficulty-weighted exact draw",
        "valid": "6..15",
    },
    "frame_color": {
        "type": "int",
        "default": "uniform legal frame color",
        "valid": "1|4|5|6|8|9",
    },
    "n_top": {
        "type": "int",
        "default": "difficulty-weighted exact draw",
        "valid": "1..4",
    },
    "n_left": {
        "type": "int",
        "default": "difficulty-weighted exact draw",
        "valid": "1..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "1..4 inert bottom/right markers",
        "valid": "1..4",
    },
}

_AXIS_DOMAINS = {
    "frame_h": FRAME_HEIGHTS,
    "frame_w": FRAME_WIDTHS,
    "frame_color": FRAME_COLORS,
    "n_top": TOP_COUNTS,
    "n_left": LEFT_COUNTS,
    "n_distractors": DISTRACTOR_COUNTS,
}

_BAND_PREFERENCES = {
    "easy": {
        "frame_h": (5, 5, 6, 6, 7, 7, 8),
        "frame_w": (6, 6, 7, 7, 8, 8, 9),
        "n_top": (1, 1, 2, 2, 3),
        "n_left": (1, 1, 2, 2),
        "n_distractors": (1, 1, 2),
    },
    "medium": {
        "frame_h": (6, 7, 7, 8, 8, 9, 10),
        "frame_w": (7, 8, 8, 9, 9, 10, 11),
        "n_top": (2, 2, 3, 3, 4),
        "n_left": (1, 2, 2, 3),
        "n_distractors": (1, 2, 2, 3),
    },
    "hard": {
        # Keep canonical-scale support while increasing the large-frame tail.
        "frame_h": (5, 6, 7, 8, 9, 10, 11, 11, 12, 12, 13, 13),
        "frame_w": (6, 7, 8, 9, 10, 11, 12, 13, 13, 14, 14, 15, 15),
        "n_top": (2, 3, 3, 4, 4),
        "n_left": (2, 2, 3, 3),
        "n_distractors": (2, 3, 3, 4, 4),
    },
}


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = "medium" if difficulty is None else difficulty
    if band not in _BAND_PREFERENCES:
        raise ValueError(f"difficulty must be one of easy|medium|hard, got {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"override {name!r} must be an integer, got {value!r}")
        if value not in _AXIS_DOMAINS[name]:
            raise ValueError(
                f"override {name!r}={value!r} outside legal domain "
                f"{_AXIS_DOMAINS[name]!r}"
            )
    return str(band)


def _draw_axis(ctx, name: str, band: str) -> int:
    domain = _AXIS_DOMAINS[name]
    if name in ctx.overrides:
        options = domain
    elif name == "frame_color":
        options = domain
    else:
        # Every call still exposes the complete legal domain; repetitions only
        # shape the default curriculum and do not invent hidden constraints.
        options = tuple(domain) + tuple(_BAND_PREFERENCES[band][name])
    return int(ctx.draw_choice(name, options))


def _canvas_and_origin(ctx, frame_h: int, frame_w: int) -> tuple[int, int, int, int]:
    rng = ctx.draw_rng("canvas_layout")
    fitting = [
        (height, width)
        for height, width in CANONICAL_CANVASES
        if height >= frame_h and width >= frame_w
    ]
    if fitting:
        height, width = rng.choice(fitting)
    else:
        height = frame_h + rng.randint(0, 3) + rng.randint(0, 3)
        width = frame_w + rng.randint(0, 3) + rng.randint(0, 3)
    top = rng.randint(0, height - frame_h)
    left = rng.randint(0, width - frame_w)
    return height, width, top, left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid.

    Every advertised axis is exact and recoverable from the returned pixels.
    Unknown, mistyped, and out-of-domain overrides fail loudly.
    """
    band = _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    frame_h = _draw_axis(ctx, "frame_h", band)
    frame_w = _draw_axis(ctx, "frame_w", band)
    frame_color = _draw_axis(ctx, "frame_color", band)
    n_top = _draw_axis(ctx, "n_top", band)
    n_left = _draw_axis(ctx, "n_left", band)
    n_distractors = _draw_axis(ctx, "n_distractors", band)

    height, width, row0, col0 = _canvas_and_origin(ctx, frame_h, frame_w)
    row1 = row0 + frame_h - 1
    col1 = col0 + frame_w - 1
    grid = full_grid(height, width, 0)

    for col in range(col0, col1 + 1):
        grid[row0][col] = frame_color
        grid[row1][col] = frame_color
    for row in range(row0, row1 + 1):
        grid[row][col0] = frame_color
        grid[row][col1] = frame_color

    marker_rng = ctx.draw_rng("marker_positions")
    top_cols = marker_rng.sample(list(range(col0 + 1, col1)), n_top)
    left_rows = marker_rng.sample(list(range(row0 + 1, row1)), n_left)
    for col in top_cols:
        grid[row0][col] = 3
    for row in left_rows:
        grid[row][col0] = 2

    # These marker-colored cells are deliberately on the *wrong* bbox edges.
    # The authority ignores them; the declared anywhere-marker rival does not.
    candidates = [
        (row1, col, 2) for col in range(col0 + 1, col1)
    ] + [
        (row, col1, 3) for row in range(row0 + 1, row1)
    ]
    distractor_rng = ctx.draw_rng("distractor_positions")
    for row, col, color in distractor_rng.sample(candidates, n_distractors):
        grid[row][col] = color

    return grid


def _bbox(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("nonzero bbox is undefined")
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _frame_color(grid: Sequence[Sequence[int]], box: tuple[int, int, int, int]) -> int:
    row0, col0, row1, col1 = box
    border = (
        list(grid[row0][col0:col1 + 1])
        + list(grid[row1][col0:col1 + 1])
        + [grid[row][col0] for row in range(row0 + 1, row1)]
        + [grid[row][col1] for row in range(row0 + 1, row1)]
    )
    candidates = [value for value in border if value not in (0, 2, 3, 7)]
    if not candidates:
        raise ValueError("frame color is missing")
    return int(Counter(candidates).most_common(1)[0][0])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact advertised axis from a lawful returned grid."""
    box = _bbox(grid)
    row0, col0, row1, col1 = box
    frame_color = _frame_color(grid, box)
    n_top = sum(grid[row0][col] == 3 for col in range(col0 + 1, col1))
    n_left = sum(grid[row][col0] == 2 for row in range(row0 + 1, row1))
    n_distractors = 0
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 2 and not (col == col0 and row0 < row < row1):
                n_distractors += 1
            elif value == 3 and not (row == row0 and col0 < col < col1):
                n_distractors += 1
    return {
        "frame_h": row1 - row0 + 1,
        "frame_w": col1 - col0 + 1,
        "frame_color": frame_color,
        "n_top": n_top,
        "n_left": n_left,
        "n_distractors": n_distractors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input-side contract, including canonical quirks."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["grid colors must be integer ARC colors 0..9"]
    try:
        box = _bbox(grid)
        frame_color = _frame_color(grid, box)
    except ValueError as exc:
        return [str(exc)]
    row0, col0, row1, col1 = box
    frame_h = row1 - row0 + 1
    frame_w = col1 - col0 + 1
    errors: list[str] = []
    if frame_h not in FRAME_HEIGHTS or frame_w not in FRAME_WIDTHS:
        errors.append("nonzero bbox dimensions are outside frame_h 5..13 / frame_w 6..15")
    if frame_color not in FRAME_COLORS:
        errors.append("frame color must be one of 1|4|5|6|8|9")

    palette = {value for row in grid for value in row}
    if not palette <= {0, frame_color, 2, 3}:
        errors.append("input may contain only background, frame, and marker colors")

    if grid[row0][col0] != frame_color or grid[row0][col1] != frame_color:
        errors.append("top frame corners must retain the frame color")
    if grid[row1][col1] != frame_color:
        errors.append("bottom-right frame corner must retain the frame color")
    # Canonical train pair 2 uses a color-2 bottom-left corner.  The authority
    # excludes corners from its row scan, so this is a lawful frame quirk.
    if grid[row1][col0] not in (frame_color, 2):
        errors.append("bottom-left corner must be frame color or inert color 2")

    for col in range(col0 + 1, col1):
        if grid[row0][col] not in (frame_color, 3):
            errors.append("top edge may contain only frame color and color-3 markers")
            break
    for row in range(row0 + 1, row1):
        if grid[row][col0] not in (frame_color, 2):
            errors.append("left edge may contain only frame color and color-2 markers")
            break
    for col in range(col0 + 1, col1):
        if grid[row1][col] not in (frame_color, 2):
            errors.append("bottom edge may contain only frame color and inert color-2 distractors")
            break
    for row in range(row0 + 1, row1):
        if grid[row][col1] not in (frame_color, 3):
            errors.append("right edge may contain only frame color and inert color-3 distractors")
            break

    if not any(grid[row0][col] == 3 for col in range(col0 + 1, col1)):
        errors.append("missing top-edge color-3 column marker")
    if not any(grid[row][col0] == 2 for row in range(row0 + 1, row1)):
        errors.append("missing left-edge color-2 row marker")
    for row in range(row0 + 1, row1):
        for col in range(col0 + 1, col1):
            if grid[row][col] != 0:
                errors.append("frame interior must be empty in the input")
                return errors
    return errors


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python statement used only for semantic tests and rival checks."""
    row0, col0, row1, col1 = _bbox(grid)
    rows = [row for row in range(row0 + 1, row1) if grid[row][col0] == 2]
    cols = [col for col in range(col0 + 1, col1) if grid[row0][col] == 3]
    output = deepcopy(grid)
    for row in rows:
        for col in cols:
            output[row][col] = 7
    return output


def _markers_anywhere_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Wrong but canonical-consistent: ignore edge roles, except bbox corners."""
    row0, col0, row1, col1 = _bbox(grid)
    corners = {(row0, col0), (row0, col1), (row1, col0), (row1, col1)}
    rows = sorted({
        row
        for row, values in enumerate(grid)
        if any(value == 2 and (row, col) not in corners
               for col, value in enumerate(values))
    })
    cols = sorted({
        col
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3 and (row, col) not in corners
    })
    output = deepcopy(grid)
    for row in rows:
        for col in cols:
            output[row][col] = 7
    return output


def _off_axis_witness(grid: Sequence[Sequence[int]]) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _markers_anywhere_rival(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "markers_anywhere": _markers_anywhere_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "off_axis_marker": _off_axis_witness,
}
WITNESS_RIVALS = {
    "off_axis_marker": ["markers_anywhere"],
}
EXAMPLES_NEEDED = 2


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is valid when outputs obey authority and kill the named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"demo {index} input invalid: {findings[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the bbox-edge rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
    else:
        findings = self_check(query["input"])
        if findings:
            reasons.append(f"query input invalid: {findings[0]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the bbox-edge rule")
    if reasons:
        return reasons
    if all(_markers_anywhere_rival(pair["input"]) == pair["output"] for pair in demos):
        reasons.append("the markers-anywhere rival survives every demonstration")
    return reasons
