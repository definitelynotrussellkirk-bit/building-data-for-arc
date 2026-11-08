"""Generator for row/column submatrix extraction (c1ee27b39d13).

Color-4 cells in the top row select payload columns.  Color-5 cells in the
left column select payload rows.  The answer is their ordered intersection.
Normal lessons include non-marker selector distractors and payload 4/5 cells,
so neither "all nonzero border cells" nor "globally unique marker colors" is a
valid shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c1ee27b39d13"
TASK_ID = "c1ee27b39d13"
VERSION = "2.0.0"
RULE_HASH = "6a46c5a9b416"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Top-row color-4 markers select payload columns and left-column color-5 "
    "markers select payload rows. Return the ordered submatrix at their "
    "intersections. Nonselected left-border cells include colored distractors, "
    "and colors 4/5 also occur as ordinary payload values."
)

INVARIANTS = [
    "the top-left cell is 0 and the top selector row contains only 0/4",
    "at least two but not all payload columns are selected by top-row 4s",
    "at least two but not all payload rows are selected by left-column 5s",
    "a nonselected left-border row carries a nonzero non-5 distractor",
    "colors 4 and 5 also occur inside the payload, so marker colors are not globally unique",
    "the selected submatrix contains both zero and nonzero payload values",
]

HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over 6..16",
        "valid": "6..16",
    },
    "n_row_marks": {
        "type": "int",
        "default": "difficulty-aware draw over 2..4",
        "valid": "2..4",
    },
    "n_col_marks": {
        "type": "int",
        "default": "difficulty-aware draw over 2..4",
        "valid": "2..4",
    },
    "texture": {
        "type": "str",
        "default": "keyed draw over helpful payload textures",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_TEXTURE_PALETTES = {
    "default": (0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (0, 0, 2, 4, 5, 7, 9),
    "cool": (0, 0, 1, 3, 4, 5, 6, 8),
}
_NONZERO_NON5 = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "n_row_marks", "n_col_marks"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer")
    texture = overrides.get("texture")
    if texture is not None and type(texture) is not str:
        raise ValueError("texture must be a string")


def _coerce_grid(grid):
    """Return an integer list-of-lists when the input is ARC-grid shaped."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    result = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(char not in "0123456789" for char in row):
                raise ValueError("string rows must contain ARC digits only")
            result.append([int(char) for char in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("each row must be a sequence or digit string")
    return result


def _selector_facts(grid):
    g = _coerce_grid(grid)
    width = len(g[0])
    if width == 0 or any(len(row) != width for row in g):
        raise ValueError("grid must be rectangular and non-empty")
    selected_cols = tuple(
        col for col in range(1, width) if g[0][col] == 4
    )
    selected_rows = tuple(
        row for row in range(1, len(g)) if g[row][0] == 5
    )
    return g, selected_rows, selected_cols


def rule_mirror(grid):
    """Input-pure Python mirror used only for audits; Racket remains authority."""
    g, selected_rows, selected_cols = _selector_facts(grid)
    return [
        [g[row][col] for col in selected_cols]
        for row in selected_rows
    ]


def observe_overrides(grid) -> dict[str, int]:
    """Expose exact semantic counts recoverable from the returned grid."""
    _, selected_rows, selected_cols = _selector_facts(grid)
    return {
        "n_row_marks": len(selected_rows),
        "n_col_marks": len(selected_cols),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone lessons while accepting canonicals."""
    del difficulty, meta
    try:
        g = _coerce_grid(grid)
    except ValueError as exc:
        return [str(exc)]

    errors = []
    width = len(g[0]) if g and g[0] else 0
    if width == 0 or any(len(row) != width for row in g):
        return ["grid must be rectangular and non-empty"]
    height = len(g)
    if not (6 <= height <= 30 and 6 <= width <= 30):
        errors.append(f"expected dimensions within 6..30; got {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    if g[0][0] != 0:
        errors.append("top-left selector corner must be 0")
    illegal_top = [
        col for col, value in enumerate(g[0]) if value not in (0, 4)
    ]
    if illegal_top:
        errors.append(
            "top selector row may contain only 0/4; illegal columns "
            + ",".join(map(str, illegal_top))
        )

    selected_cols = [
        col for col in range(1, width) if g[0][col] == 4
    ]
    selected_rows = [
        row for row in range(1, height) if g[row][0] == 5
    ]
    if not (2 <= len(selected_cols) <= width - 2):
        errors.append(
            "expected at least two but not all payload columns selected; "
            f"found {len(selected_cols)}"
        )
    if not (2 <= len(selected_rows) <= height - 2):
        errors.append(
            "expected at least two but not all payload rows selected; "
            f"found {len(selected_rows)}"
        )

    unselected_rows = [
        row for row in range(1, height) if row not in selected_rows
    ]
    if not any(g[row][0] not in (0, 5) for row in unselected_rows):
        errors.append(
            "need a nonzero non-5 distractor on an unselected left-border row"
        )

    payload = [
        g[row][col]
        for row in range(1, height)
        for col in range(1, width)
    ]
    for marker_color in (4, 5):
        if marker_color not in payload:
            errors.append(
                f"payload must contain marker color {marker_color} as ordinary data"
            )

    if selected_rows and selected_cols:
        answer_values = [
            g[row][col]
            for row in selected_rows
            for col in selected_cols
        ]
        if 0 not in answer_values:
            errors.append("selected submatrix must contain at least one zero")
        if not any(value != 0 for value in answer_values):
            errors.append("selected submatrix must contain a nonzero value")
        if len(set(answer_values)) < 2:
            errors.append("selected submatrix must not be uniform")
    return errors


def _fill_payload(grid, *, texture, rng) -> None:
    height, width = len(grid), len(grid[0])
    if texture == "varied":
        palette = list(range(10))
        rng.shuffle(palette)
        offset = rng.randrange(len(palette))
        for row in range(1, height):
            for col in range(1, width):
                grid[row][col] = palette[
                    (offset + row * (width - 1) + col - 1) % len(palette)
                ]
        return

    palette = _TEXTURE_PALETTES[texture]
    for row in range(1, height):
        for col in range(1, width):
            grid[row][col] = rng.choice(palette)


def _place_payload_cues(grid, selected_rows, selected_cols, rng) -> None:
    """Balance whether payload 4/5 values do or do not enter the answer."""
    selected = [
        (row, col) for row in selected_rows for col in selected_cols
    ]
    selected_set = set(selected)
    outside = [
        (row, col)
        for row in range(1, len(grid))
        for col in range(1, len(grid[0]))
        if (row, col) not in selected_set
    ]
    rng.shuffle(selected)
    rng.shuffle(outside)
    profile = rng.choice(("both", "only4", "only5", "neither"))
    selected_markers = {
        "both": {4, 5},
        "only4": {4},
        "only5": {5},
        "neither": set(),
    }[profile]

    # Make marker-color membership in the answer exact for this profile rather
    # than hoping an iid payload draw happens not to reintroduce the color.
    replacement_values = (0, 1, 2, 3, 6, 7, 8, 9)
    for row, col in selected:
        if grid[row][col] in (4, 5) and grid[row][col] not in selected_markers:
            grid[row][col] = rng.choice(replacement_values)

    selected_cursor = 0
    outside_cursor = 0

    def place_selected(value):
        nonlocal selected_cursor
        row, col = selected[selected_cursor]
        selected_cursor += 1
        grid[row][col] = value

    def place_outside(value):
        nonlocal outside_cursor
        row, col = outside[outside_cursor]
        outside_cursor += 1
        grid[row][col] = value

    for marker_color in (4, 5):
        if marker_color in selected_markers:
            place_selected(marker_color)
        else:
            place_outside(marker_color)

    protected = set(selected[:selected_cursor])
    zero_cell = next(
        ((row, col) for row, col in selected if grid[row][col] == 0),
        None,
    )
    if zero_cell is None:
        zero_cell = next(cell for cell in selected if cell not in protected)
        grid[zero_cell[0]][zero_cell[1]] = 0
    protected.add(zero_cell)

    nonzero_cell = next(
        (
            (row, col)
            for row, col in selected
            if grid[row][col] != 0
        ),
        None,
    )
    if nonzero_cell is None:
        nonzero_cell = next(cell for cell in selected if cell not in protected)
        grid[nonzero_cell[0]][nonzero_cell[1]] = rng.choice(_NONZERO_NON5)
    protected.add(nonzero_cell)

    # Keep the selected payload informative even on an unlucky repeated-color
    # draw without overwriting the marker/zero/nonzero witnesses above.
    used = {grid[row][col] for row, col in selected}
    candidates = tuple(
        value
        for value in range(10)
        if value not in (4, 5) or value in selected_markers
    )
    for row, col in selected:
        if len(used) >= 3:
            break
        if (row, col) in protected:
            continue
        candidate = next(value for value in candidates if value not in used)
        grid[row][col] = candidate
        used.add(candidate)
        protected.add((row, col))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 6, 14)
    width = ctx.draw_int_diff("grid_w", 6, 16)
    n_row_marks = ctx.draw_int_diff("n_row_marks", 2, 4)
    n_col_marks = ctx.draw_int_diff("n_col_marks", 2, 4)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    row_rng = ctx.draw_rng("selected_rows")
    col_rng = ctx.draw_rng("selected_cols")
    payload_rng = ctx.draw_rng("payload")
    border_rng = ctx.draw_rng("left_border")
    cue_rng = ctx.draw_rng("payload_cues")

    selected_rows = sorted(row_rng.sample(range(1, height), n_row_marks))
    selected_cols = sorted(col_rng.sample(range(1, width), n_col_marks))

    grid = full_grid(height, width, 0)
    _fill_payload(grid, texture=texture, rng=payload_rng)
    _place_payload_cues(grid, selected_rows, selected_cols, cue_rng)

    for col in selected_cols:
        grid[0][col] = 4
    for row in selected_rows:
        grid[row][0] = 5

    unselected_rows = [
        row for row in range(1, height) if row not in selected_rows
    ]
    for row in unselected_rows:
        grid[row][0] = border_rng.choice((0, 0) + _NONZERO_NON5)
    # Make the canonical nonzero-left-border distractor structural rather than
    # probabilistic, including the tight 4-of-5 marker boundary.
    if not any(grid[row][0] not in (0, 5) for row in unselected_rows):
        row = border_rng.choice(unselected_rows)
        grid[row][0] = border_rng.choice(_NONZERO_NON5)

    return grid
