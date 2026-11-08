"""Generator for arc_puzzle_bank_seventh21:E43.

Rule: in every row, fill the single zero between equal nonzero endpoints
(`C 0 C -> C C C`).  Longer horizontal gaps, unequal endpoints, and vertical
`C 0 C` patterns are deliberate negative witnesses and remain unchanged.

Exact observable axes: grid_h, grid_w, motifs, color_mode.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b219c71180a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4b8e01e6e875"
SUMMARY = (
    "Horizontal equal-color endpoints exactly two columns apart have their "
    "zero midpoint filled; longer gaps, unequal endpoints, and vertical pairs "
    "are unchanged distractors."
)

INVARIANTS = [
    "background is 0",
    "every target is a horizontal nonzero-zero-same-nonzero triplet",
    "each generated grid includes longer-gap, unequal-endpoint, and vertical distractors",
    "all nonzero cells belong to a target or a declared distractor",
    "at least two midpoint cells change under the canonical rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed rng 7..9",
        "valid": "7..9",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed rng 7..9",
        "valid": "7..9",
    },
    "motifs": {
        "type": "int",
        "default": "difficulty-skewed rng 2..4",
        "valid": "2..4",
    },
    "color_mode": {
        "type": "str",
        "default": "rng distinct|shared",
        "valid": "distinct|shared",
    },
}

# Every declared boundary combination is constructible.  Keeping the explicit
# empty declaration makes accidental future ValueError rejections visible to
# the override checker instead of falling back to its legacy warning policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests and semantic-rival scoring."""
    out = _copy_grid(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w - 2):
            color = grid[r][c]
            if color != 0 and grid[r][c + 1] == 0 and grid[r][c + 2] == color:
                out[r][c + 1] = color
    return out


def _horizontal_targets(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    return [
        (r, c + 1, grid[r][c])
        for r in range(h)
        for c in range(w - 2)
        if grid[r][c] != 0
        and grid[r][c + 1] == 0
        and grid[r][c + 2] == grid[r][c]
    ]


def _long_gap_pairs(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    return [
        (r, c, c + 3, grid[r][c])
        for r in range(h)
        for c in range(w - 3)
        if grid[r][c] != 0
        and grid[r][c + 1] == 0
        and grid[r][c + 2] == 0
        and grid[r][c + 3] == grid[r][c]
    ]


def _mismatched_pairs(grid: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    return [
        (r, c, c + 2, grid[r][c], grid[r][c + 2])
        for r in range(h)
        for c in range(w - 2)
        if grid[r][c] != 0
        and grid[r][c + 1] == 0
        and grid[r][c + 2] != 0
        and grid[r][c + 2] != grid[r][c]
    ]


def _vertical_pairs(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    return [
        (r + 1, c, grid[r][c])
        for r in range(h - 2)
        for c in range(w)
        if grid[r][c] != 0
        and grid[r + 1][c] == 0
        and grid[r + 2][c] == grid[r][c]
    ]


def _recognized_nonzero_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for r, center, _ in _horizontal_targets(grid):
        cells.update(((r, center - 1), (r, center + 1)))
    for r, left, right, _ in _long_gap_pairs(grid):
        cells.update(((r, left), (r, right)))
    for r, left, right, _, _ in _mismatched_pairs(grid):
        cells.update(((r, left), (r, right)))
    for center_r, c, _ in _vertical_pairs(grid):
        cells.update(((center_r - 1, c), (center_r + 1, c)))
    return cells


def _base_errors(grid: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (7 <= h <= 9 and 7 <= w <= 9):
        errors.append(f"grid dimensions {(h, w)} outside declared 7..9 envelope")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")

    targets = _horizontal_targets(grid)
    if not (2 <= len(targets) <= 4):
        errors.append(f"found {len(targets)} target midpoints; expected 2..4")
    row_counts: dict[int, int] = {}
    for r, _, _ in targets:
        row_counts[r] = row_counts.get(r, 0) + 1
    if any(count != 1 for count in row_counts.values()):
        errors.append("a row contains overlapping or multiple target motifs")

    target_colors = [color for _, _, color in targets]
    distinct = len(set(target_colors))
    if target_colors and distinct not in (1, len(target_colors)):
        errors.append("target colors must be either all shared or all distinct")

    nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    stray = sorted(nonzero - _recognized_nonzero_cells(grid))
    if stray:
        errors.append(f"nonzero cells outside target/distractor grammar: {stray[:8]}")

    changed = sum(
        rule_mirror(grid)[r][c] != grid[r][c]
        for r in range(h)
        for c in range(w)
    )
    if changed != len(targets):
        errors.append(
            f"canonical mirror changes {changed} cells but {len(targets)} target centers were found"
        )
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact teaching grammar while accepting official examples.

    The official three canonical inputs contain only positive motifs.  Ordinary
    generated draws add all three negative witnesses; a canonical-shaped grid
    with no distractors remains lawful because self_check must accept the real
    task inputs as well as the richer teaching distribution.
    """
    errors = _base_errors(grid)
    if errors:
        return errors

    long_gaps = _long_gap_pairs(grid)
    mismatches = _mismatched_pairs(grid)
    vertical = _vertical_pairs(grid)
    has_any_distractor = bool(long_gaps or mismatches or vertical)
    canonical_shape = (
        len(_horizontal_targets(grid)) == 3
        and len({value for row in grid for value in row}) == 4
    )
    if not has_any_distractor and canonical_shape:
        return []
    if not long_gaps:
        errors.append("missing same-color longer-gap negative witness")
    if not mismatches:
        errors.append("missing unequal-endpoint negative witness")
    if not vertical:
        errors.append("missing vertical distance-2 negative witness")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful task manifold: exact targets plus only rule-relevant distractors."""
    return _base_errors(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    targets = _horizontal_targets(grid)
    colors = [color for _, _, color in targets]
    color_mode = "shared" if len(set(colors)) == 1 else "distinct"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motifs": len(targets),
        "color_mode": color_mode,
    }


def _choose_positive_centers(rng, *, width: int, count: int, blocked_col: int) -> list[int]:
    allowed = [
        center
        for center in range(1, width - 1)
        if blocked_col not in (center - 1, center, center + 1)
    ]
    if not allowed:
        raise ValueError("no legal horizontal target center for vertical distractor column")
    return [rng.choice(allowed) for _ in range(count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 7, 9)
    w = ctx.draw_int_diff("grid_w", 7, 9)
    motif_count = ctx.draw_int_diff("motifs", 2, 4)
    color_mode = ctx.draw_choice("color_mode", ("distinct", "shared"))
    rng = ctx.draw_rng("layout-colors-and-nuisance")

    grid = full_grid(h, w, 0)
    row_offset = rng.randint(0, h - 7)
    role_rows = [row_offset + index for index in range(7)]
    if rng.choice((False, True)):
        role_rows.reverse()
    positive_rows = role_rows[:motif_count]
    long_row = role_rows[4]
    mismatch_row = role_rows[5]
    vertical_rows = (role_rows[0], role_rows[1], role_rows[2])

    # Three nonzero colors are enough for every motif_count <= 3 and preserve
    # the canonical palette-size profile. A fourth is added only when four
    # distinct target colors are explicitly requested.
    palette_size = 4 if color_mode == "distinct" and motif_count == 4 else 3
    colors = rng.sample(range(1, 10), palette_size)
    if color_mode == "shared":
        positive_colors = [colors[0]] * motif_count
    else:
        positive_colors = colors[:motif_count]

    vertical_col = rng.randrange(w)
    centers = _choose_positive_centers(
        rng, width=w, count=motif_count, blocked_col=vertical_col
    )
    for row, center, color in zip(positive_rows, centers, positive_colors):
        grid[row][center - 1] = color
        grid[row][center + 1] = color

    # Same-color endpoints with TWO zeros between them: a tempting "fill every
    # span" rule would alter this row, while the canonical one-cell-gap rule
    # must leave it unchanged.
    long_start = rng.randint(0, w - 4)
    grid[long_row][long_start] = colors[0]
    grid[long_row][long_start + 3] = colors[0]

    # Distance-2 endpoints with unequal colors: refutes a color-blind midpoint
    # filler while keeping the visual geometry identical to a positive motif.
    mismatch_center = rng.randint(1, w - 2)
    grid[mismatch_row][mismatch_center - 1] = colors[1]
    grid[mismatch_row][mismatch_center + 1] = colors[2]

    # Vertical same-color pair: refutes an orientation-blind distance-2 bridge.
    # The blocked column was kept zero in all three role rows before this write.
    vertical_color = colors[1] if color_mode == "distinct" and motif_count >= 3 else colors[2]
    top_row, middle_row, bottom_row = vertical_rows
    grid[top_row][vertical_col] = vertical_color
    if grid[middle_row][vertical_col] != 0:
        raise AssertionError("vertical distractor midpoint was unexpectedly occupied")
    grid[bottom_row][vertical_col] = vertical_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"constructed invalid grid: {errors}")
    return grid


# ---------------------------------------------------------------------------
# Semantic rivals and lesson-identifiability contract
# ---------------------------------------------------------------------------

def _rival_identity(grid):
    return _copy_grid(grid)


def _rival_fill_all_matching_row_spans(grid):
    out = _copy_grid(grid)
    for r, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(c)
        for color, cols in positions.items():
            for left, right in zip(cols, cols[1:]):
                if right > left + 1 and all(row[c] == 0 for c in range(left + 1, right)):
                    for c in range(left + 1, right):
                        out[r][c] = color
    return out


def _rival_fill_any_horizontal_distance2(grid):
    out = _copy_grid(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h):
        for c in range(w - 2):
            left, middle, right = grid[r][c : c + 3]
            if left != 0 and middle == 0 and right != 0:
                out[r][c + 1] = left
    return out


def _rival_fill_axis_aligned_distance2(grid):
    out = rule_mirror(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color != 0 and grid[r + 1][c] == 0 and grid[r + 2][c] == color:
                out[r + 1][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "fill_all_matching_row_spans": _rival_fill_all_matching_row_spans,
    "fill_any_horizontal_distance2": _rival_fill_any_horizontal_distance2,
    "fill_axis_aligned_distance2": _rival_fill_axis_aligned_distance2,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    name: rival
    for name, rival in SEMANTIC_RIVALS.items()
    if name != "identity"
}


def _w_positive_target(grid) -> bool:
    return bool(_horizontal_targets(grid))


def _w_long_gap(grid) -> bool:
    return bool(_long_gap_pairs(grid))


def _w_mismatch(grid) -> bool:
    return bool(_mismatched_pairs(grid))


def _w_vertical(grid) -> bool:
    return bool(_vertical_pairs(grid))


SEMANTIC_WITNESSES = {
    "positive_target_changes": _w_positive_target,
    "long_gap_stays_unchanged": _w_long_gap,
    "unequal_endpoints_stay_unchanged": _w_mismatch,
    "vertical_pair_stays_unchanged": _w_vertical,
}
WITNESS_RIVALS = {
    "positive_target_changes": ["identity"],
    "long_gap_stays_unchanged": ["fill_all_matching_row_spans"],
    "unequal_endpoints_stay_unchanged": ["fill_any_horizontal_distance2"],
    "vertical_pair_stays_unchanged": ["fill_axis_aligned_distance2"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives every demo."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration pair is required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")
    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    expected = rule_mirror(query["input"])
    if "output" in query and query["output"] != expected:
        reasons.append("query output does not match the canonical rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != expected:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Named malformed scenes that self_check must reject."""
    base = generate(991, 17, difficulty="medium", motifs=3, color_mode="distinct")
    target = _horizontal_targets(base)[0]
    long_gap = _long_gap_pairs(base)[0]
    mismatch = _mismatched_pairs(base)[0]
    vertical = _vertical_pairs(base)[0]

    blank = full_grid(len(base), len(base[0]), 0)

    filled_midpoint = deepcopy(base)
    tr, tc, color = target
    filled_midpoint[tr][tc] = color

    missing_long_gap = deepcopy(base)
    lr, left, right, _ = long_gap
    missing_long_gap[lr][left] = 0
    missing_long_gap[lr][right] = 0

    missing_mismatch = deepcopy(base)
    mr, left, right, _, _ = mismatch
    missing_mismatch[mr][left] = 0
    missing_mismatch[mr][right] = 0

    missing_vertical = deepcopy(base)
    vr, vc, _ = vertical
    missing_vertical[vr - 1][vc] = 0
    missing_vertical[vr + 1][vc] = 0

    stray_cell = deepcopy(base)
    for r, row in enumerate(stray_cell):
        for c, value in enumerate(row):
            if value == 0 and all(
                not (r == tr and c == tc) for tr, tc, _ in _horizontal_targets(stray_cell)
            ):
                stray_cell[r][c] = 9
                if self_check(stray_cell):
                    break
                stray_cell[r][c] = 0
        else:
            continue
        break

    return [
        ("all_background", blank),
        ("target_midpoint_already_filled", filled_midpoint),
        ("missing_long_gap_witness", missing_long_gap),
        ("missing_mismatch_witness", missing_mismatch),
        ("missing_vertical_witness", missing_vertical),
        ("unclassified_stray_cell", stray_cell),
    ]
