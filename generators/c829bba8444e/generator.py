"""Generator for 11b:hard_71 — library lookup transform gallery.

Canonical rule
--------------
Three 5x5 color-9 frames form a left-to-right library.  The meaningful
payload of each frame is the cropped non-zero content of its 3x3 interior.
Rows 0 and 1 form a command strip: row 0 is a 1-indexed library selector and
row 1 is a rotation code (1=id, 2=90 CW, 3=180, 4=90 CCW).  Execute commands
from left to right, then hstack the transformed payloads with one zero column
between them and center each payload vertically.

The canonical examples are much tighter than the previous generator: height 9,
width 18..21, three row-4 frames, 3..4 commands, and palette size 8..9.  Color
9 has two roles: it is the frame color *and can also be payload inside a frame*.
The teaching distribution intentionally preserves that dual role and rejects
several tempting shortcuts (ignore selector, ignore transform, reverse quarter
turns, sort by selector, or strip payload 9s).
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c829bba8444e"
TASK_ID = "c829bba8444e"
RULE_HASH = "b2e3e52d885e"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Canonical-scale 9x18..21 zero-background input. Three hollow 5x5 "
    "color-9 frames occupy rows 4..8 and form a left-to-right library; each "
    "3x3 interior is a full-bbox 5..7-cell colored payload, and color 9 may "
    "also be payload. Rows 0/1 contain 3..4 aligned command pairs: row 0 is "
    "selector 1..3 and row 1 is rotation code 1=id, 2=90CW, 3=180, 4=90CCW. "
    "Execute commands left-to-right and hstack the transformed cropped "
    "payloads with a one-column zero gap, vertically centered."
)

INVARIANTS = [
    "background is 0; canonical input height is 9 and width is 18..21",
    "exactly three hollow 5x5 color-9 frames occupy rows 4..8, with left margin 1 and the final frame flush right",
    "each frame interior is 3x3, has 5..7 nonzero cells, spans the full 3x3 bbox, and uses only colors 6..9",
    "rows 0 and 1 contain exactly 3 or 4 aligned commands; selectors are 1..3 and transform codes are 1..4",
    "ordinary lessons select all three library entries and contain a payload-9 witness so frame color cannot be discarded",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "rng 18..21",
        "valid": "18..21",
        "doc": "Canonical input width. Height is fixed at 9.",
    },
    "n_pairs": {
        "type": "int",
        "default": "rng 3..4",
        "valid": "3..4",
        "doc": "Number of aligned selector/rotation commands in rows 0 and 1.",
    },
}

# Template symbols 10/11 are replaced with high payload colors at generation
# time.  Literal 9 is deliberate payload: in the 9-bearing templates it is
# edge-connected, so after any dihedral transform it remains connected to the
# outer color-9 frame and does not become a spurious fourth 9-object.
_A = 10
_B = 11
_TEMPLATES: dict[str, tuple[tuple[int, ...], ...]] = {
    "mono_L": ((_A, 0, 0), (_A, 0, 0), (_A, _A, _A)),
    "two_color_T": ((_A, _A, _A), (0, _B, 0), (0, _B, 0)),
    "corner_9": ((_A, _A, 0), (0, _A, 9), (0, 9, 9)),
    "hook_9": ((_A, 0, 0), (_A, 9, 0), (_A, 9, 9)),
    "diamond": ((0, _A, 0), (_A, _B, _A), (0, _A, 0)),
    "woven": ((_A, _A, _B), (0, _A, 0), (_B, _A, _A)),
}
_ASYMMETRIC_TEMPLATE_NAMES = ("mono_L", "two_color_T", "corner_9", "hook_9")
_NINE_TEMPLATE_NAMES = ("corner_9", "hook_9")


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return _rotate_cw(grid)
    if code == 3:
        return _rotate_180(grid)
    if code == 4:
        return _rotate_ccw(grid)
    return [row[:] for row in grid]


def _transform_reverse_quarters(grid: list[list[int]], code: int) -> list[list[int]]:
    """Wrong mapping used as a semantic rival: swap CW and CCW."""
    if code == 2:
        return _rotate_ccw(grid)
    if code == 4:
        return _rotate_cw(grid)
    return _transform(grid, code)


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _hstack_center(grids: list[list[list[int]]], gap: int = 1) -> list[list[int]]:
    if not grids:
        return [[]]
    height = max(len(grid) for grid in grids)
    width = sum(len(grid[0]) for grid in grids) + gap * (len(grids) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for grid in grids:
        top = (height - len(grid)) // 2
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(grid[0]) + gap
    return out


def _is_frame_border(grid: list[list[int]], row: int, col: int) -> bool:
    if row < 0 or col < 0 or row + 4 >= len(grid) or col + 4 >= len(grid[0]):
        return False
    return (
        all(grid[row][c] == 9 and grid[row + 4][c] == 9 for c in range(col, col + 5))
        and all(grid[r][col] == 9 and grid[r][col + 4] == 9 for r in range(row, row + 5))
    )


def _find_frame_starts(grid: list[list[int]]) -> list[int]:
    if len(grid) < 9 or not grid or len(grid[0]) < 5:
        return []
    # Canonical frames all have their top border on row 4.
    return [c for c in range(len(grid[0]) - 4) if _is_frame_border(grid, 4, c)]


def _scene_parts(grid: list[list[int]]):
    frame_starts = _find_frame_starts(grid)
    library = [
        _crop_nonzero([row[c + 1 : c + 4] for row in grid[5:8]])
        for c in frame_starts
    ]
    commands = [
        (c, grid[0][c], grid[1][c])
        for c in range(len(grid[0]))
        if grid[0][c] != 0
    ]
    return frame_starts, library, commands


def _oracle_output(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python spelling of the selected canonical Racket rule."""
    _, library, commands = _scene_parts(grid)
    pieces: list[list[list[int]]] = []
    for _, selector, code in commands:
        if 1 <= selector <= len(library) and code in (1, 2, 3, 4):
            pieces.append(_transform(library[selector - 1], code))
    return _hstack_center(pieces, 1)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Audit-only Python mirror; selected Racket ``program_solution`` remains authority."""
    return _oracle_output(grid)


def _rival_library_order(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: command i takes library entry i instead of reading selector."""
    _, library, commands = _scene_parts(grid)
    pieces = [
        _transform(library[i % len(library)], code)
        for i, (_, _selector, code) in enumerate(commands)
    ] if library else []
    return _hstack_center(pieces, 1)


def _rival_no_rotation(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: selector is honored but row-1 transform codes are ignored."""
    _, library, commands = _scene_parts(grid)
    pieces = [library[selector - 1] for _, selector, _ in commands if 1 <= selector <= len(library)]
    return _hstack_center(pieces, 1)


def _rival_reverse_quarter_turns(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: code 2 means CCW and code 4 means CW."""
    _, library, commands = _scene_parts(grid)
    pieces = [
        _transform_reverse_quarters(library[selector - 1], code)
        for _, selector, code in commands
        if 1 <= selector <= len(library) and code in (1, 2, 3, 4)
    ]
    return _hstack_center(pieces, 1)


def _rival_sort_by_selector(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: output pieces are ordered by selector rather than command column."""
    _, library, commands = _scene_parts(grid)
    ordered = sorted(commands, key=lambda item: (item[1], item[0]))
    pieces = [
        _transform(library[selector - 1], code)
        for _, selector, code in ordered
        if 1 <= selector <= len(library) and code in (1, 2, 3, 4)
    ]
    return _hstack_center(pieces, 1)


def _rival_strip_payload_9(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: treats every color-9 cell as disposable frame scaffolding."""
    true = _oracle_output(grid)
    return [[0 if value == 9 else value for value in row] for row in true]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_selector_use_library_order": _rival_library_order,
    "ignore_transform_codes": _rival_no_rotation,
    "reverse_cw_ccw_codes": _rival_reverse_quarter_turns,
    "sort_output_by_selector": _rival_sort_by_selector,
    "strip_frame_color_from_payload": _rival_strip_payload_9,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _refutes(rival_name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != _oracle_output(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "selector_controls_library_lookup": lambda grid: _refutes("ignore_selector_use_library_order", grid),
    "transform_code_changes_orientation": lambda grid: _refutes("ignore_transform_codes", grid),
    "quarter_turn_direction_is_ordered": lambda grid: _refutes("reverse_cw_ccw_codes", grid),
    "command_column_controls_output_order": lambda grid: _refutes("sort_output_by_selector", grid),
    "color_9_can_survive_as_payload": lambda grid: _refutes("strip_frame_color_from_payload", grid),
}
WITNESS_RIVALS = {
    "selector_controls_library_lookup": ["ignore_selector_use_library_order"],
    "transform_code_changes_orientation": ["ignore_transform_codes"],
    "quarter_turn_direction_is_ordered": ["reverse_cw_ccw_codes"],
    "command_column_controls_output_order": ["sort_output_by_selector"],
    "color_9_can_survive_as_payload": ["strip_frame_color_from_payload"],
}


def _instantiate_template(
    pattern: tuple[tuple[int, ...], ...],
    color_a: int,
    color_b: int,
) -> list[list[int]]:
    return [
        [color_a if value == _A else color_b if value == _B else value for value in row]
        for row in pattern
    ]


def _dihedral_template(grid: list[list[int]], rng) -> list[list[int]]:
    out = [row[:] for row in grid]
    for _ in range(rng.randrange(4)):
        out = _rotate_cw(out)
    if rng.randrange(2):
        out = _flip_lr(out)
    return out


def _quarter_asymmetric(grid: list[list[int]]) -> bool:
    return _rotate_cw(grid) != _rotate_ccw(grid)


def _build_library(palette_size: int, rng) -> list[list[list[int]]]:
    # At least one 9-bearing template and at least two orientation-asymmetric
    # templates. This keeps both the frame/payload-9 distinction and direction
    # of quarter turns observable on every ordinary lesson.
    first = rng.choice(_NINE_TEMPLATE_NAMES)
    second = rng.choice([name for name in _ASYMMETRIC_TEMPLATE_NAMES if name != first])
    third = rng.choice([name for name in _TEMPLATES if name not in {first, second}])
    names = [first, second, third]
    rng.shuffle(names)

    high_colors = [7, 8] if palette_size == 8 else [6, 7, 8]
    assigned_a = high_colors[:]
    while len(assigned_a) < 3:
        assigned_a.append(rng.choice(high_colors))
    rng.shuffle(assigned_a)

    library: list[list[list[int]]] = []
    for index, name in enumerate(names):
        color_a = assigned_a[index]
        other = [color for color in high_colors if color != color_a]
        color_b = rng.choice(other or [color_a])
        piece = _instantiate_template(_TEMPLATES[name], color_a, color_b)
        library.append(_dihedral_template(piece, rng))

    # The A assignments guarantee every high color appears. Literal template 9
    # supplies the frame-color-as-payload witness.
    return library


def _frame_starts(width: int, rng) -> list[int]:
    # Canonical layout: one zero column on the left, no right margin, positive
    # inter-frame gaps whose sum is exactly width - 16.
    gap_total = width - 16
    gap_1 = rng.randint(1, gap_total - 1)
    gap_2 = gap_total - gap_1
    c1 = 1
    c2 = c1 + 5 + gap_1
    c3 = c2 + 5 + gap_2
    return [c1, c2, c3]


def _command_columns(width: int, n_pairs: int, rng) -> list[int]:
    if n_pairs == 3:
        candidates = [
            (1, 5, 9),
            (2, 6, 10),
            (2, 7, 12),
            (3, 7, 11),
        ]
    else:
        candidates = [
            (1, 5, 9, 13),
            (2, 6, 10, 14),
            (2, 7, 12, 17),
            (3, 8, 13, 17),
        ]
    legal = [cols for cols in candidates if cols[-1] < width]
    return list(rng.choice(legal))


def _selector_sequence(n_pairs: int, rng) -> list[int]:
    if n_pairs == 3:
        candidates = [list(p) for p in ((1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1))]
        return rng.choice(candidates)
    repeated = rng.choice((1, 2, 3))
    values = [1, 2, 3, repeated]
    for _ in range(32):
        rng.shuffle(values)
        if values != sorted(values):
            return values[:]
    return [3, 1, 2, repeated]


def _transform_sequence(selectors: list[int], library: list[list[list[int]]], rng) -> list[int]:
    asymmetric_selectors = [i + 1 for i, piece in enumerate(library) if _quarter_asymmetric(piece)]
    if len(asymmetric_selectors) < 2:
        raise RuntimeError("library unexpectedly lacks two quarter-turn-asymmetric entries")

    # Give codes 2 and 4 to two distinct asymmetric library entries. Remaining
    # commands use 1/3, so code direction and non-identity behavior are always
    # observable while the 3-command case still looks like canonical examples.
    idx2 = next(i for i, selector in enumerate(selectors) if selector == asymmetric_selectors[0])
    idx4 = next(i for i, selector in enumerate(selectors) if selector == asymmetric_selectors[1])
    codes = [0] * len(selectors)
    codes[idx2] = 2
    codes[idx4] = 4
    remaining = [i for i, value in enumerate(codes) if value == 0]
    fillers = [1, 3] if len(remaining) == 2 else [rng.choice((1, 3))]
    rng.shuffle(fillers)
    for index, code in zip(remaining, fillers):
        codes[index] = code
    return codes


def _paint_scene(
    width: int,
    frame_starts: list[int],
    library: list[list[list[int]]],
    command_cols: list[int],
    selectors: list[int],
    transforms: list[int],
) -> list[list[int]]:
    grid = full_grid(9, width, 0)
    for col, piece in zip(frame_starts, library):
        for c in range(col, col + 5):
            grid[4][c] = 9
            grid[8][c] = 9
        for r in range(4, 9):
            grid[r][col] = 9
            grid[r][col + 4] = 9
        for r in range(3):
            for c in range(3):
                grid[5 + r][col + 1 + c] = piece[r][c]
    for col, selector, code in zip(command_cols, selectors, transforms):
        grid[0][col] = selector
        grid[1][col] = code
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    width = ctx.draw_int("grid_w", 18, 21)
    n_pairs = ctx.draw_int("n_pairs", 3, 4)
    rng = ctx.draw_rng(f"content:{difficulty or 'default'}")

    # Match the measured canonical (width, palette-size) support exactly:
    # width 18 only appears with palette 8; widths 20/21 with palette 9; width
    # 19 appears with both. Palette size is derived, not a separately declared
    # axis, so there are no impossible cross-axis override combinations.
    if width == 18:
        palette_size = 8
    elif width in (20, 21):
        palette_size = 9
    else:
        palette_size = 8 if rng.randrange(2) == 0 else 9

    starts = _frame_starts(width, rng)
    cols = _command_columns(width, n_pairs, rng)
    for _ in range(64):
        library = _build_library(palette_size, rng)
        selectors = _selector_sequence(n_pairs, rng)
        transforms = _transform_sequence(selectors, library, rng)
        grid = _paint_scene(width, starts, library, cols, selectors, transforms)
        if self_check(grid, difficulty=difficulty):
            continue
        if strict_canonical_like(grid):
            continue
        if not all(_refutes(name, grid) for name in SEMANTIC_RIVALS):
            continue
        return grid
    raise RuntimeError("could not construct a shortcut-refuting canonical-like lesson after 64 attempts")


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared axis exactly from the returned grid."""
    return {
        "grid_w": len(grid[0]) if grid else 0,
        "n_pairs": sum(value != 0 for value in grid[0]) if grid else 0,
    }


def _rectangular_arc_grid(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"], 0, 0
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be rectangular"], len(grid), width
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors, len(grid), width


def _all_nines_connected_in_frame(grid: list[list[int]], col: int) -> bool:
    cells = {
        (r, c)
        for r in range(4, 9)
        for c in range(col, col + 5)
        if grid[r][c] == 9
    }
    if not cells:
        return False
    start = (4, col)
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible structural input grammar.

    This checker deliberately validates structure rather than curriculum
    scheduling: all canonical inputs are accepted, while branch/rival coverage
    stays in ``strict_canonical_like`` / semantic witnesses.
    """
    del difficulty, meta
    errors, height, width = _rectangular_arc_grid(grid)
    if errors:
        return errors
    if height != 9:
        errors.append(f"expected canonical input height 9, got {height}")
    if not 18 <= width <= 21:
        errors.append(f"expected canonical input width 18..21, got {width}")
    if errors:
        return errors

    command_cols = [c for c in range(width) if grid[0][c] != 0]
    transform_cols = [c for c in range(width) if grid[1][c] != 0]
    if command_cols != transform_cols:
        errors.append("rows 0 and 1 must contain commands in exactly the same columns")
    if len(command_cols) not in (3, 4):
        errors.append(f"expected 3 or 4 command pairs, got {len(command_cols)}")
    for col in command_cols:
        if grid[0][col] not in (1, 2, 3):
            errors.append(f"selector at column {col} is {grid[0][col]!r}, expected 1..3")
        if grid[1][col] not in (1, 2, 3, 4):
            errors.append(f"transform at column {col} is {grid[1][col]!r}, expected 1..4")
    if any(grid[r][c] != 0 for r in (2, 3) for c in range(width)):
        errors.append("rows 2 and 3 must be zero separators between commands and library")

    starts = _find_frame_starts(grid)
    if len(starts) != 3:
        errors.append(f"expected exactly three 5x5 row-4 color-9 frames, found {len(starts)} at {starts}")
        return errors
    if starts[0] != 1:
        errors.append(f"first frame must start at column 1, got {starts[0]}")
    if starts[-1] + 4 != width - 1:
        errors.append("final frame must be flush with the right edge")
    if any(b - a < 6 for a, b in zip(starts, starts[1:])):
        errors.append("frames must have at least one zero column between them")

    covered = {
        (r, c)
        for start in starts
        for r in range(4, 9)
        for c in range(start, start + 5)
    }
    stray = [
        (r, c, grid[r][c])
        for r in range(4, 9)
        for c in range(width)
        if grid[r][c] != 0 and (r, c) not in covered
    ]
    if stray:
        errors.append(f"nonzero cell outside library frames: {stray[0]}")

    for index, start in enumerate(starts, 1):
        if not _is_frame_border(grid, 4, start):
            errors.append(f"frame {index} border is not a complete hollow color-9 rectangle")
            continue
        inner = [row[start + 1 : start + 4] for row in grid[5:8]]
        bad = [value for row in inner for value in row if value not in (0, 6, 7, 8, 9)]
        if bad:
            errors.append(f"frame {index} interior uses noncanonical payload color {bad[0]}")
        nonzero = [(r, c) for r, row in enumerate(inner) for c, value in enumerate(row) if value != 0]
        if not 5 <= len(nonzero) <= 7:
            errors.append(f"frame {index} interior has {len(nonzero)} nonzero cells; expected 5..7")
        if nonzero:
            rows = {r for r, _ in nonzero}
            cols = {c for _, c in nonzero}
            if rows != {0, 1, 2} or cols != {0, 1, 2}:
                errors.append(f"frame {index} payload must span the full 3x3 interior bbox")
        if not any(value in (6, 7, 8) for row in inner for value in row):
            errors.append(f"frame {index} payload must contain a non-9 high color")
        if not _all_nines_connected_in_frame(grid, start):
            errors.append(f"frame {index} has a disconnected interior 9 component that would look like an extra library object")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Pin generated lessons to the measured c829bba8444e canonical manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    width = len(grid[0])
    palette_size = len({value for row in grid for value in row})
    allowed_palette = {18: {8}, 19: {8, 9}, 20: {9}, 21: {9}}[width]
    if palette_size not in allowed_palette:
        errors.append(
            f"width {width} has palette size {palette_size}; canonical support is {sorted(allowed_palette)}"
        )

    command_cols = [c for c in range(width) if grid[0][c] != 0]
    if any(b - a < 4 for a, b in zip(command_cols, command_cols[1:])):
        errors.append("canonical command markers are separated by at least three zero columns")
    selectors = [grid[0][c] for c in command_cols]
    if set(selectors) != {1, 2, 3}:
        errors.append(f"canonical-like lessons expose all three selectors, got {selectors}")

    starts = _find_frame_starts(grid)
    inners = [[row[start + 1 : start + 4] for row in grid[5:8]] for start in starts]
    if not any(9 in row for inner in inners for row in inner):
        errors.append("canonical-like lesson needs at least one interior payload 9")
    if not any(len({value for row in inner for value in row if value != 0}) >= 2 for inner in inners):
        errors.append("canonical-like lesson needs at least one multicolor library payload")
    return errors


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        if pair["output"] != _oracle_output(pair["input"]):
            reasons.append(f"pair {index} output disagrees with library lookup + transform rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        except Exception as exc:
            reasons.append(f"rival {name} raised {exc!r}")
            continue
        if survives:
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(f"rival remains answer-equivalent on query: {name}")
    return reasons


def mutation_fixtures():
    """Task-local malformed scenes that ``self_check`` must reject."""
    base = generate(20260816, 0, grid_w=19, n_pairs=4)
    starts = _find_frame_starts(base)
    command_cols = [c for c, value in enumerate(base[0]) if value != 0]

    broken_frame = [row[:] for row in base]
    broken_frame[4][starts[0] + 2] = 0

    unpaired_command = [row[:] for row in base]
    extra_col = next(c for c in range(len(base[0])) if base[0][c] == base[1][c] == 0)
    unpaired_command[0][extra_col] = 1

    selector_oob = [row[:] for row in base]
    selector_oob[0][command_cols[0]] = 5

    detached_nine = [row[:] for row in base]
    start = starts[0]
    for r in range(5, 8):
        for c in range(start + 1, start + 4):
            if detached_nine[r][c] == 9:
                detached_nine[r][c] = 7
    detached_nine[6][start + 2] = 9
    detached_nine[5][start + 2] = 0
    detached_nine[6][start + 1] = 0
    detached_nine[6][start + 3] = 0
    detached_nine[7][start + 2] = 0

    sparse_payload = [row[:] for row in base]
    start = starts[1]
    for r in range(5, 8):
        for c in range(start + 1, start + 4):
            sparse_payload[r][c] = 0
    sparse_payload[5][start + 1] = 7
    sparse_payload[6][start + 2] = 8
    sparse_payload[7][start + 3] = 7

    stray_library_cell = [row[:] for row in base]
    stray_library_cell[6][0] = 8

    too_few_commands = [row[:] for row in base]
    for r in (0, 1):
        too_few_commands[r][command_cols[-1]] = 0
        too_few_commands[r][command_cols[-2]] = 0

    return [
        ("broken_frame_border", broken_frame),
        ("selector_without_transform", unpaired_command),
        ("selector_out_of_range", selector_oob),
        ("detached_inner_9_component", detached_nine),
        ("sparse_payload", sparse_payload),
        ("stray_lower_cell", stray_library_cell),
        ("too_few_commands", too_few_commands),
    ]
