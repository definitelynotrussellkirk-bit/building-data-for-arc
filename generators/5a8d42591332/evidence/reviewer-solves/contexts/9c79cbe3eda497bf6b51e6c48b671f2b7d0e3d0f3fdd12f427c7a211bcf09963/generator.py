"""Generate 11x11 count-comparison matrices with observable teaching axes.

Three 2x2 top headers (color 1) and three 2x2 left headers (color 2)
encode counts from one through four.  The oracle compares every top count with
every left count and fills the corresponding 2x2 body block: yellow (4) when
the top count is larger, green (3) when the left count is larger, and cyan (8)
when they are equal.

The sample-index schedule cycles total-count balance and header-layout styles.
Every ordinary draw contains all three comparison outcomes.  Counts two and
three also occur on opposite axes; the noncompact texture families deliberately
give those counts the same row-major-prefix score.  Consequently either
noncompact style independently refutes the strongest canonical-fitting shortcut
identified during review.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5a8d42591332"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "4c53ca03668e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 3**9

SUMMARY = (
    "An 11x11 input contains three color-1 count headers across the top and "
    "three color-2 count headers down the left. Compare each top count with "
    "each left count and fill the matching 2x2 body block with 4 when top is "
    "larger, 3 when left is larger, or 8 when the counts are equal."
)

INVARIANTS = [
    "the grid is exactly 11x11 with separator rows and columns 2, 5, and 8",
    "top 2x2 headers begin at columns 3, 6, and 9 and contain only 0/1",
    "left 2x2 headers begin at rows 3, 6, and 9 and contain only 0/2",
    "every header count is between one and four",
    "ordinary generated inputs exhibit top-greater, left-greater, and equality",
    "ordinary generated inputs include every count from min_count through four",
    "ordinary generated inputs compare counts two and three across opposite axes",
    "the 3x3 body is blank in the input and is filled only by the Racket oracle",
]

RELATION_BALANCES = ("equal_total", "top_heavy", "left_heavy")
HEADER_LAYOUTS = ("compact", "diagonal", "reverse")
SCHEDULE_PROFILES = RELATION_BALANCES

AXES = {
    "relation_balance": {
        "type": "str",
        "default": "three-step sample-index schedule",
        "valid": "equal_total|top_heavy|left_heavy",
    },
    "min_count": {
        "type": "int",
        "default": "scheduled 1|2",
        "valid": "1..2",
    },
    "header_layout": {
        "type": "str",
        "default": "three-step sample-index schedule",
        "valid": "compact|diagonal|reverse",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
_STARTS = (3, 6, 9)
_CELLS_2X2: tuple[Cell, ...] = ((0, 0), (0, 1), (1, 0), (1, 1))

# Pattern families are disjoint, so observe_overrides can recover the requested
# style.  In each noncompact family, counts two and three share the same
# row-major-prefix score; the count-vector constraint below places those counts
# on opposite axes, making true cell count necessary.
_LAYOUT_PATTERNS: dict[str, dict[int, tuple[tuple[Cell, ...], ...]]] = {
    "compact": {
        1: (((0, 0),),),
        2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
        3: (((0, 0), (0, 1), (1, 0)),),
        4: (_CELLS_2X2,),
    },
    "diagonal": {
        1: (((0, 1),),),
        2: (((0, 0), (1, 1)),),
        3: (((0, 0), (1, 0), (1, 1)),),
        4: (_CELLS_2X2,),
    },
    "reverse": {
        1: (((1, 1),),),
        2: (((1, 0), (1, 1)), ((0, 1), (1, 1))),
        3: (((0, 1), (1, 0), (1, 1)),),
        4: (_CELLS_2X2,),
    },
}

_PATTERN_TO_LAYOUT: dict[tuple[int, frozenset[Cell]], str] = {}
for _layout_name, _by_count in _LAYOUT_PATTERNS.items():
    for _count, _patterns in _by_count.items():
        if _count == 4:
            continue
        for _pattern in _patterns:
            _PATTERN_TO_LAYOUT[(_count, frozenset(_pattern))] = _layout_name


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every three consecutive examples cover all total-balance regimes."""
    del seed
    offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return RELATION_BALANCES[(int(sample_index) + offset) % len(RELATION_BALANCES)]


def _scheduled_min_count(sample_index: int, difficulty: Any) -> int:
    offset = {"easy": 1, "medium": 0, "hard": 2}.get(difficulty, 0)
    return (1, 2, 1)[(int(sample_index) + offset) % 3]


def _scheduled_layout(seed: int, sample_index: int, difficulty: Any) -> str:
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    seed_offset = int(seed) % len(HEADER_LAYOUTS)
    return HEADER_LAYOUTS[
        (int(sample_index) + band_offset + seed_offset) % len(HEADER_LAYOUTS)
    ]


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    choices = options if ctx.overrides.get(label) is not None else (scheduled,)
    return ctx.draw_choice(label, choices)


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    bounds = (lo, hi) if ctx.overrides.get(label) is not None else (scheduled, scheduled)
    return ctx.draw_int_strict(label, bounds[0], bounds[1])


def _validate_generate_call(sample_index: Any, overrides: dict[str, Any]) -> None:
    """Reject coercible controls before schedules or keyed draws consume them."""
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    min_count = overrides.get("min_count")
    if min_count is not None:
        if type(min_count) is not int:
            raise TypeError("min_count override must be a literal integer (not bool)")
        if min_count not in (1, 2):
            raise ValueError("min_count override must be 1 or 2")

    for name, options in (
        ("relation_balance", RELATION_BALANCES),
        ("header_layout", HEADER_LAYOUTS),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} override must be a string")
        if value not in options:
            raise ValueError(f"{name} override must be one of {options}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic input grid; the Racket rule remains the oracle."""
    _validate_generate_call(sample_index, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    relation_balance = _draw_scheduled_choice(
        ctx,
        "relation_balance",
        schedule_profile(seed, sample_index, difficulty),
        RELATION_BALANCES,
    )
    min_count = _draw_scheduled_int(
        ctx,
        "min_count",
        _scheduled_min_count(sample_index, difficulty),
        1,
        2,
    )
    header_layout = _draw_scheduled_choice(
        ctx,
        "header_layout",
        _scheduled_layout(seed, sample_index, difficulty),
        HEADER_LAYOUTS,
    )

    top_counts, left_counts = _draw_counts(
        ctx.draw_rng("count_vectors"), relation_balance, min_count
    )
    grid = full_grid(11, 11, 0)
    texture_rng = ctx.draw_rng("header_texture")
    for col0, count in zip(_STARTS, top_counts):
        _paint_header(grid, 0, col0, count, 1, header_layout, texture_rng)
    for row0, count in zip(_STARTS, left_counts):
        _paint_header(grid, row0, 0, count, 2, header_layout, texture_rng)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={
            "overrides": {
                "relation_balance": relation_balance,
                "min_count": min_count,
                "header_layout": header_layout,
            }
        },
    )
    if errors:
        raise RuntimeError(f"constructed invalid count matrix: {errors}")
    return grid


def _draw_counts(rng, relation_balance: str, min_count: int) -> tuple[list[int], list[int]]:
    """Draw branch-rich header counts with the requested observable signature."""
    for _ in range(2048):
        top = [rng.randint(min_count, 4) for _ in range(3)]
        left = [rng.randint(min_count, 4) for _ in range(3)]
        counts = top + left
        if set(counts) != set(range(min_count, 5)):
            continue
        if not ((2 in top and 3 in left) or (3 in top and 2 in left)):
            continue
        delta = sum(top) - sum(left)
        if relation_balance == "equal_total" and delta != 0:
            continue
        if relation_balance == "top_heavy" and delta <= 0:
            continue
        if relation_balance == "left_heavy" and delta >= 0:
            continue
        if _relation_symbols(top, left) != {3, 4, 8}:
            continue
        return top, left
    raise RuntimeError(
        f"unable to draw counts for balance={relation_balance!r}, min={min_count}"
    )


def _paint_header(
    grid: Grid,
    row0: int,
    col0: int,
    count: int,
    color: int,
    layout: str,
    rng,
) -> None:
    patterns = _LAYOUT_PATTERNS[layout][count]
    for dr, dc in rng.choice(patterns):
        grid[row0 + dr][col0 + dc] = color


def _relation_symbols(top_counts: list[int], left_counts: list[int]) -> set[int]:
    return {
        4 if top > left else 3 if top < left else 8
        for left in left_counts
        for top in top_counts
    }


def _analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid values must be integer ARC colors 0..9")

    h, w = len(grid), width
    top_counts: list[int] = []
    left_counts: list[int] = []
    patterns: list[tuple[int, frozenset[Cell]]] = []
    if h == 11 and w == 11:
        for col0 in _STARTS:
            cells = frozenset(
                (dr, dc)
                for dr, dc in _CELLS_2X2
                if grid[dr][col0 + dc] == 1
            )
            top_counts.append(len(cells))
            patterns.append((len(cells), cells))
        for row0 in _STARTS:
            cells = frozenset(
                (dr, dc)
                for dr, dc in _CELLS_2X2
                if grid[row0 + dr][dc] == 2
            )
            left_counts.append(len(cells))
            patterns.append((len(cells), cells))

    layout_votes = {
        _PATTERN_TO_LAYOUT[key]
        for key in patterns
        if key[0] != 4 and key in _PATTERN_TO_LAYOUT
    }
    layout = next(iter(layout_votes)) if len(layout_votes) == 1 else None
    delta = sum(top_counts) - sum(left_counts) if len(top_counts) == 3 else 0
    relation_balance = (
        "equal_total" if delta == 0 else "top_heavy" if delta > 0 else "left_heavy"
    )
    return {
        "height": h,
        "width": w,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "top_counts": top_counts,
        "left_counts": left_counts,
        "min_count": min(top_counts + left_counts) if top_counts and left_counts else None,
        "relation_balance": relation_balance,
        "relation_symbols": _relation_symbols(top_counts, left_counts)
        if len(top_counts) == len(left_counts) == 3
        else set(),
        "header_layout": layout,
        "layout_votes": layout_votes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the fixed header/body grammar without overfitting texture."""
    del difficulty
    try:
        facts = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    if (facts["height"], facts["width"]) != (11, 11):
        return [f"expected 11x11, got {facts['height']}x{facts['width']}"]
    if facts["palette"] != (0, 1, 2):
        errors.append(f"expected exact input palette (0, 1, 2), got {facts['palette']}")

    allowed_top = {
        (row, col)
        for row in range(2)
        for col0 in _STARTS
        for col in range(col0, col0 + 2)
    }
    allowed_left = {
        (row, col)
        for row0 in _STARTS
        for row in range(row0, row0 + 2)
        for col in range(2)
    }
    for row in range(11):
        for col in range(11):
            value = grid[row][col]
            if (row, col) in allowed_top:
                if value not in (0, 1):
                    errors.append(f"top header cell {(row, col)} must be 0/1, got {value}")
            elif (row, col) in allowed_left:
                if value not in (0, 2):
                    errors.append(f"left header cell {(row, col)} must be 0/2, got {value}")
            elif value != 0:
                errors.append(f"non-header cell {(row, col)} must be 0, got {value}")
            if len(errors) >= 8:
                break
        if len(errors) >= 8:
            break

    for index, count in enumerate(facts["top_counts"]):
        if not 1 <= count <= 4:
            errors.append(f"top header {index} has invalid count {count}; expected 1..4")
    for index, count in enumerate(facts["left_counts"]):
        if not 1 <= count <= 4:
            errors.append(f"left header {index} has invalid count {count}; expected 1..4")

    requested = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(requested, dict) and requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in AXES and observed.get(axis) != expected:
                errors.append(
                    f"requested {axis}={expected!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical grammar plus all three decisive output branches."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze(grid)
    if facts["relation_symbols"] != {3, 4, 8}:
        errors.append(
            "header counts do not expose all three outcomes: top>, left>, and equal"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact semantic axis from the returned input grid."""
    try:
        facts = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    if (facts["height"], facts["width"]) != (11, 11):
        return {}
    return {
        "relation_balance": facts["relation_balance"],
        "min_count": facts["min_count"],
        "header_layout": facts["header_layout"],
    }


def solve_python(grid: Grid) -> Grid:
    """Independent mirror used only for tests and semantic rival checks."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"invalid count-comparison input: {errors}")
    facts = _analyze(grid)
    output = [row[:] for row in grid]
    for row_index, row0 in enumerate(_STARTS):
        for col_index, col0 in enumerate(_STARTS):
            top = facts["top_counts"][col_index]
            left = facts["left_counts"][row_index]
            color = 4 if top > left else 3 if top < left else 8
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = color
    return output


def _rival_reverse_comparison(grid: Grid) -> Grid:
    output = solve_python(grid)
    return [[3 if v == 4 else 4 if v == 3 else v for v in row] for row in output]


def _rival_nonzero_presence(grid: Grid) -> Grid:
    output = [row[:] for row in grid]
    for row0 in _STARTS:
        for col0 in _STARTS:
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = 8
    return output


def _rival_global_total(grid: Grid) -> Grid:
    facts = _analyze(grid)
    top = sum(facts["top_counts"])
    left = sum(facts["left_counts"])
    color = 4 if top > left else 3 if top < left else 8
    output = [row[:] for row in grid]
    for row0 in _STARTS:
        for col0 in _STARTS:
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = color
    return output


def _row_major_prefix_count(
    grid: Grid, row0: int, col0: int, color: int
) -> int:
    """Count only the occupied row-major prefix of one 2x2 header."""
    count = 0
    for dr, dc in _CELLS_2X2:
        if grid[row0 + dr][col0 + dc] != color:
            break
        count += 1
    return count


def _rival_row_major_prefix_count(grid: Grid) -> Grid:
    """Canonical-fitting shortcut that mistakes compact prefixes for counts."""
    top_counts = [_row_major_prefix_count(grid, 0, col0, 1) for col0 in _STARTS]
    left_counts = [_row_major_prefix_count(grid, row0, 0, 2) for row0 in _STARTS]
    output = [row[:] for row in grid]
    for row_index, row0 in enumerate(_STARTS):
        for col_index, col0 in enumerate(_STARTS):
            top = top_counts[col_index]
            left = left_counts[row_index]
            color = 4 if top > left else 3 if top < left else 8
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = color
    return output


def _rival_fixed_first_demo(grid: Grid) -> Grid:
    # Canonical training example 0's relation matrix, independent of this input.
    fixed = ((3, 4, 4), (3, 8, 4), (8, 4, 4))
    output = [row[:] for row in grid]
    for row_index, row0 in enumerate(_STARTS):
        for col_index, col0 in enumerate(_STARTS):
            color = fixed[row_index][col_index]
            for row in range(row0, row0 + 2):
                for col in range(col0, col0 + 2):
                    output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "reverse_comparison": _rival_reverse_comparison,
    "nonzero_presence_only": _rival_nonzero_presence,
    "global_total_only": _rival_global_total,
    "fixed_first_demo_matrix": _rival_fixed_first_demo,
    "row_major_prefix_count": _rival_row_major_prefix_count,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "row_major_prefix_count": _rival_row_major_prefix_count,
}


def _rival_differs(grid: Grid, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != solve_python(grid)


SEMANTIC_WITNESSES = {
    "top_greater_branch": lambda grid: 4 in _analyze(grid)["relation_symbols"],
    "left_greater_branch": lambda grid: 3 in _analyze(grid)["relation_symbols"],
    "equal_branch": lambda grid: 8 in _analyze(grid)["relation_symbols"],
    "nonzero_presence_shortcut_killed": lambda grid: _rival_differs(
        grid, "nonzero_presence_only"
    ),
    "global_total_shortcut_killed": lambda grid: _rival_differs(
        grid, "global_total_only"
    ),
    "reverse_comparison_shortcut_killed": lambda grid: _rival_differs(
        grid, "reverse_comparison"
    ),
    "row_major_prefix_shortcut_killed": lambda grid: _rival_differs(
        grid, "row_major_prefix_count"
    ),
}

WITNESS_RIVALS = {
    "top_greater_branch": ["reverse_comparison"],
    "left_greater_branch": ["reverse_comparison"],
    "equal_branch": ["global_total_only"],
    "nonzero_presence_shortcut_killed": ["nonzero_presence_only"],
    "global_total_shortcut_killed": ["global_total_only"],
    "reverse_comparison_shortcut_killed": ["reverse_comparison"],
    "row_major_prefix_shortcut_killed": ["row_major_prefix_count"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any materialized lesson still compatible with a named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    errors: list[str] = []
    signatures: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} is missing input/output")
            continue
        structural = strict_canonical_like(demo["input"])
        if structural:
            errors.append(f"demo {index} is outside the teaching grammar: {structural}")
            continue
        truth = solve_python(demo["input"])
        if demo["output"] != truth:
            errors.append(f"demo {index} output disagrees with count comparison")
        facts = _analyze(demo["input"])
        signatures.add((tuple(facts["top_counts"]), tuple(facts["left_counts"])))

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        errors.append(f"query is outside the teaching grammar: {query_errors}")
    if len(signatures) < 2:
        errors.append("demonstrations repeat one fixed count layout")
    if errors:
        return errors

    query_truth = solve_python(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                errors.append(
                    f"demos remain compatible with competitor {name!r}, which "
                    "changes the query answer"
                )
            else:
                errors.append(f"competitor {name!r} survives demos and query")
    return errors


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-semantic near-misses that the structural checker must reject."""
    valid = generate(701, 0, difficulty="medium")

    wrong_size = [row[:] for row in valid] + [[0] * 11]

    body_leak = [row[:] for row in valid]
    body_leak[3][3] = 4

    missing_header = [row[:] for row in valid]
    for row in range(2):
        for col in range(3, 5):
            missing_header[row][col] = 0

    swapped_role_color = [row[:] for row in valid]
    for row in range(2):
        for col in range(3, 5):
            if swapped_role_color[row][col] == 1:
                swapped_role_color[row][col] = 2
                break
        else:
            continue
        break

    separator_leak = [row[:] for row in valid]
    separator_leak[2][2] = 1

    return [
        ("wrong_12x11_size", wrong_size),
        ("oracle_color_leaks_into_blank_body", body_leak),
        ("one_top_header_is_empty", missing_header),
        ("top_header_uses_left_role_color", swapped_role_color),
        ("separator_cell_is_nonzero", separator_leak),
    ]
