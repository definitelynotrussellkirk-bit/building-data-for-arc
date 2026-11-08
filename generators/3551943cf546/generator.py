"""Generator for ARC task ``3551943cf546`` (``Fill the Gap``).

Canonical rule
--------------
Process each row independently.  For every non-background color that occurs
*exactly twice in that row*, fill the inclusive horizontal interval between
those two cells with the same color.  Other colors and rows are unchanged.

The public examples are intentionally simple: every active row contains one
same-color pair and every foreground color occurs exactly twice globally.  A
model can therefore fit all five canonical pairs with several wrong rules.
The four-sample schedule below keeps canonical-looking examples but also adds
three decisive controls: a mismatched two-cell row, two independent pairs in
one row (with one pair color reused in another row), and a triple-occurrence
near miss.  Every cyclic window of four demos contains all four profiles.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3551943cf546"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Updated after the comment-preserving selected-source synchronization.
RULE_HASH = "746ef1c8f9ee"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On each row independently, every nonzero color that occurs exactly twice "
    "defines a horizontal endpoint pair. Fill the whole interval between those "
    "two occurrences with that color. Colors occurring once or three times do "
    "not define a span. Multiple non-overlapping color pairs in one row are all "
    "processed."
)

INVARIANTS = [
    "background is color 0 and all cells are integer ARC colors 0..9",
    "every generated input contains at least two actionable same-row color pairs",
    "each actionable pair has a visible zero gap, so applying the rule changes the grid",
    "multiple same-row pair spans are disjoint and separated by background",
    "mismatch and triple controls are lawful near-misses that the oracle leaves unchanged",
    "all declared exact axes are recoverable from the returned input grid",
]

PROFILES = ("clean", "mismatch", "multi_pair", "triple")
SCHEDULE_PROFILES = PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile schedule with canonical 5..8 anchors",
        "valid": "5..8",
        "doc": "Exact grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile schedule with canonical 8..12 anchors",
        "valid": "8..12",
        "doc": "Exact grid width.",
    },
    "n_pairs": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
        "doc": "Exact number of (row,color) groups that occur exactly twice.",
    },
    "profile": {
        "type": "enum",
        "default": "cyclic clean/mismatch/multi_pair/triple teaching schedule",
        "valid": "|".join(PROFILES),
        "doc": (
            "clean has only one-pair rows; mismatch adds one row with two different "
            "singletons; multi_pair has two pair colors in one row; triple adds one "
            "row where one color occurs exactly three times."
        ),
    },
}

# Every Cartesian product of the four exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every four consecutive sample indexes contain every decisive profile."""
    del seed, difficulty
    return PROFILES[int(sample_index) % len(PROFILES)]


def _scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _scheduled_choice(
    ctx, label: str, options: tuple[str, ...], value: str
) -> str:
    available = (
        options
        if label in ctx.overrides and ctx.overrides[label] is not None
        else (value,)
    )
    return str(ctx.draw_choice(label, available))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(
            f"unknown override axis/axes: {unknown}; valid axes: {sorted(AXES)}"
        )


def _scheduled_defaults(profile: str, difficulty: Any) -> tuple[int, int, int]:
    """Canonical-scale anchor plus profile/band variation.

    ``clean`` is deliberately 6x10 with two pair colors in every band, exactly
    matching a public (height,width,palette-size) profile.  The other profiles
    expand scale and pair count without removing that anchor.
    """
    if profile == "clean":
        return 6, 10, 2
    by_band = {
        "easy": {
            "mismatch": (5, 11, 2),
            "multi_pair": (7, 9, 3),
            "triple": (8, 8, 2),
        },
        "medium": {
            "mismatch": (7, 12, 3),
            "multi_pair": (7, 10, 3),
            "triple": (6, 11, 3),
        },
        "hard": {
            "mismatch": (8, 12, 4),
            "multi_pair": (8, 11, 4),
            "triple": (7, 12, 4),
        },
    }
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    return by_band[band][profile]


def _pair_candidates(width: int) -> list[tuple[int, int]]:
    # At least one background cell lies strictly between the endpoints.
    return [
        (left, right)
        for left in range(width)
        for right in range(left + 2, width)
    ]


def _draw_pair(width: int, rng) -> tuple[int, int]:
    candidates = _pair_candidates(width)
    return candidates[rng.randrange(len(candidates))]


def _draw_two_disjoint_pairs(
    width: int, rng
) -> tuple[tuple[int, int], tuple[int, int]]:
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    pairs = _pair_candidates(width)
    for first in pairs:
        for second in pairs:
            if first >= second:
                continue
            left, right = sorted((first, second))
            # Require at least one untouched background cell between spans.
            if left[1] + 1 < right[0]:
                candidates.append((left, right))
    if not candidates:
        raise ValueError(f"grid_w={width} is too narrow for two disjoint pair spans")
    return candidates[rng.randrange(len(candidates))]


def _draw_triple(width: int, rng) -> tuple[int, int, int]:
    triples = [
        (a, b, c)
        for a in range(width)
        for b in range(a + 1, width)
        for c in range(b + 1, width)
        if c - a >= 4 and (b > a + 1 or c > b + 1)
    ]
    if not triples:
        raise ValueError(f"grid_w={width} is too narrow for the triple control")
    return triples[rng.randrange(len(triples))]


def _paint_pair(grid: list[list[int]], row: int, color: int, pair: tuple[int, int]) -> None:
    left, right = pair
    grid[row][left] = color
    grid[row][right] = color


def _row_kind(row: list[int]) -> tuple[str, dict[str, Any]]:
    nonzero_positions = [(c, value) for c, value in enumerate(row) if value != 0]
    if not nonzero_positions:
        return "empty", {"pairs": [], "counts": {}}

    counts: dict[int, list[int]] = {}
    for col, value in nonzero_positions:
        counts.setdefault(value, []).append(col)

    pair_items = sorted(
        (color, tuple(cols)) for color, cols in counts.items() if len(cols) == 2
    )
    singletons = sorted(color for color, cols in counts.items() if len(cols) == 1)
    triples = sorted((color, tuple(cols)) for color, cols in counts.items() if len(cols) == 3)
    other = sorted((color, len(cols)) for color, cols in counts.items() if len(cols) > 3)

    if other:
        return "invalid", {"reason": f"colors occur more than three times: {other}", "counts": counts}

    if pair_items and not singletons and not triples:
        intervals: list[tuple[int, int, int]] = []
        for color, (left, right) in pair_items:
            if right - left < 2:
                return "invalid", {"reason": "pair endpoints must expose a zero gap", "counts": counts}
            if any(row[col] != 0 for col in range(left + 1, right)):
                return "invalid", {"reason": "pair interior must be background in the input", "counts": counts}
            intervals.append((left, right, color))
        intervals.sort()
        for (_, prev_right, _), (next_left, _, _) in zip(intervals, intervals[1:]):
            if prev_right + 1 >= next_left:
                return "invalid", {"reason": "same-row pair spans must be background-separated", "counts": counts}
        return "pairs", {"pairs": pair_items, "counts": counts, "intervals": intervals}

    if not pair_items and not triples and len(singletons) == 2 and len(nonzero_positions) == 2:
        return "mismatch", {"pairs": [], "counts": counts}

    if not pair_items and not singletons and len(triples) == 1 and len(nonzero_positions) == 3:
        color, cols = triples[0]
        if cols[-1] - cols[0] < 4 or all(
            row[col] != 0 for col in range(cols[0], cols[-1] + 1)
        ):
            return "invalid", {"reason": "triple control must contain an unfilled interior gap", "counts": counts}
        return "triple", {"pairs": [], "counts": counts, "triple": (color, cols)}

    return "invalid", {
        "reason": "row mixes pair/singleton/triple roles or has the wrong special-row shape",
        "counts": counts,
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a nonempty list of row lists"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and nonempty"]}
    height = len(grid)
    if not 5 <= height <= 8:
        errors.append(f"grid height {height} is outside 5..8")
    if not 8 <= width <= 12:
        errors.append(f"grid width {width} is outside 8..12")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid values must be integer colors in 0..9")
                return {"errors": errors}
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    kinds: list[str] = []
    row_details: list[dict[str, Any]] = []
    pair_groups: list[tuple[int, int, tuple[int, int]]] = []
    mismatch_rows: list[int] = []
    triple_rows: list[int] = []
    for row_index, row in enumerate(grid):
        kind, detail = _row_kind(row)
        kinds.append(kind)
        row_details.append(detail)
        if kind == "invalid":
            errors.append(f"row {row_index}: {detail['reason']}")
        elif kind == "pairs":
            for color, cols in detail["pairs"]:
                pair_groups.append((row_index, color, cols))
        elif kind == "mismatch":
            mismatch_rows.append(row_index)
        elif kind == "triple":
            triple_rows.append(row_index)

    if len(pair_groups) < 2:
        errors.append("expected at least two actionable same-row color pairs")
    if len(mismatch_rows) > 1:
        errors.append("at most one mismatch-control row is allowed")
    if len(triple_rows) > 1:
        errors.append("at most one triple-control row is allowed")
    if mismatch_rows and triple_rows:
        errors.append("mismatch and triple controls are separate teaching profiles")

    multi_pair_rows = [
        row_index for row_index, kind in enumerate(kinds)
        if kind == "pairs" and len(row_details[row_index]["pairs"]) >= 2
    ]
    if len(multi_pair_rows) > 1:
        errors.append("at most one row may carry multiple pair colors")

    if triple_rows:
        profile = "triple"
    elif mismatch_rows:
        profile = "mismatch"
    elif multi_pair_rows:
        profile = "multi_pair"
    else:
        profile = "clean"

    global_pair_rows_by_color: dict[int, set[int]] = {}
    for row_index, color, _ in pair_groups:
        global_pair_rows_by_color.setdefault(color, set()).add(row_index)
    reused_pair_colors = sorted(
        color for color, rows in global_pair_rows_by_color.items() if len(rows) >= 2
    )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "kinds": kinds,
        "row_details": row_details,
        "pair_groups": pair_groups,
        "n_pairs": len(pair_groups),
        "mismatch_rows": mismatch_rows,
        "triple_rows": triple_rows,
        "multi_pair_rows": multi_pair_rows,
        "reused_pair_colors": reused_pair_colors,
        "profile": profile,
    }


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

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_pairs = _scheduled_defaults(
        scheduled_profile, difficulty
    )
    height = _scheduled_int(ctx, "grid_h", 5, 8, scheduled_h)
    width = _scheduled_int(ctx, "grid_w", 8, 12, scheduled_w)
    n_pairs = _scheduled_int(ctx, "n_pairs", 2, 4, scheduled_pairs)
    profile = _scheduled_choice(ctx, "profile", PROFILES, scheduled_profile)

    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)
    rows = list(range(height))
    rng.shuffle(rows)
    colors = list(range(1, 10))
    rng.shuffle(colors)

    if profile == "clean":
        for index in range(n_pairs):
            _paint_pair(grid, rows[index], colors[index], _draw_pair(width, rng))

    elif profile == "mismatch":
        for index in range(n_pairs):
            _paint_pair(grid, rows[index], colors[index], _draw_pair(width, rng))
        mismatch_row = rows[n_pairs]
        c1, c2 = rng.sample(range(width), 2)
        grid[mismatch_row][c1] = colors[n_pairs]
        grid[mismatch_row][c2] = colors[n_pairs + 1]

    elif profile == "triple":
        for index in range(n_pairs):
            _paint_pair(grid, rows[index], colors[index], _draw_pair(width, rng))
        triple_row = rows[n_pairs]
        triple_color = colors[n_pairs]
        for col in _draw_triple(width, rng):
            grid[triple_row][col] = triple_color

    elif profile == "multi_pair":
        first_pair, second_pair = _draw_two_disjoint_pairs(width, rng)
        multi_row = rows[0]
        _paint_pair(grid, multi_row, colors[0], first_pair)
        _paint_pair(grid, multi_row, colors[1], second_pair)
        for index in range(2, n_pairs):
            row_index = rows[index - 1]
            # On ordinary scheduled multi_pair draws n_pairs>=3, so reusing
            # colors[0] here creates the global-count counterexample. Explicit
            # n_pairs=2 remains a lawful multi-pair scene without that extra cue.
            color = colors[0] if index == 2 else colors[index]
            _paint_pair(grid, row_index, color, _draw_pair(width, rng))

    else:  # protected by draw_choice, retained for defensive clarity
        raise AssertionError(f"unknown profile {profile!r}")

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": n_pairs,
        "profile": profile,
    }
    if observed != expected:
        raise AssertionError(f"observable axis drift: expected {expected}, got {observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_pairs": analysis["n_pairs"],
        "profile": analysis["profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for semantic tests; Racket remains authority."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            cols = [col for col, value in enumerate(row) if value == color]
            if len(cols) == 2:
                for col in range(cols[0], cols[1] + 1):
                    output[row_index][col] = color
    return output


def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis is not None and predicate(analysis))


def _has_wide_pair(analysis: dict[str, Any]) -> bool:
    return any(cols[1] - cols[0] >= 5 for _, _, cols in analysis["pair_groups"])


SEMANTIC_WITNESSES = {
    "actionable_pair": lambda grid: _witness(grid, lambda a: a["n_pairs"] >= 2),
    "wide_pair": lambda grid: _witness(grid, _has_wide_pair),
    "mismatched_two_cell_row": lambda grid: _witness(grid, lambda a: bool(a["mismatch_rows"])),
    "multiple_pairs_same_row": lambda grid: _witness(grid, lambda a: bool(a["multi_pair_rows"])),
    "pair_color_reused_across_rows": lambda grid: _witness(grid, lambda a: bool(a["reused_pair_colors"])),
    "triple_occurrence_near_miss": lambda grid: _witness(grid, lambda a: bool(a["triple_rows"])),
}

BRANCH_WITNESSES = ("actionable_pair", "wide_pair")


def _rival_any_two_nonzero(grid):
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        cells = [(col, value) for col, value in enumerate(row) if value != 0]
        if len(cells) == 2:
            left, color = cells[0]
            right = cells[1][0]
            for col in range(left, right + 1):
                out[row_index][col] = color
    return out


def _rival_first_pair_only(grid):
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        colors = sorted({value for value in row if value != 0})
        for color in colors:
            cols = [col for col, value in enumerate(row) if value == color]
            if len(cols) == 2:
                for col in range(cols[0], cols[1] + 1):
                    out[row_index][col] = color
                break
    return out


def _rival_global_exact_twice(grid):
    out = deepcopy(grid)
    global_counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value:
                global_counts[value] = global_counts.get(value, 0) + 1
    for row_index, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            cols = [col for col, value in enumerate(row) if value == color]
            if len(cols) == 2 and global_counts.get(color) == 2:
                for col in range(cols[0], cols[1] + 1):
                    out[row_index][col] = color
    return out


def _rival_at_least_two(grid):
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            cols = [col for col, value in enumerate(row) if value == color]
            if len(cols) >= 2:
                for col in range(cols[0], cols[-1] + 1):
                    out[row_index][col] = color
    return out


SEMANTIC_RIVALS = {
    "connect_any_two_nonzero_cells_in_a_row": _rival_any_two_nonzero,
    "fill_only_first_pair_in_each_row": _rival_first_pair_only,
    "require_color_to_occur_exactly_twice_globally": _rival_global_exact_twice,
    "fill_any_color_occurring_at_least_twice_in_a_row": _rival_at_least_two,
}

WITNESS_RIVALS = {
    "mismatched_two_cell_row": ["connect_any_two_nonzero_cells_in_a_row"],
    "multiple_pairs_same_row": ["fill_only_first_pair_in_each_row"],
    "pair_color_reused_across_rows": ["require_color_to_occur_exactly_twice_globally"],
    "triple_occurrence_near_miss": ["fill_any_color_occurring_at_least_twice_in_a_row"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the per-row exact-pair rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the per-row exact-pair rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Four task-specific malformed scenes that structural self_check must reject."""
    blank = full_grid(6, 10, 0)

    adjacent_pair = full_grid(6, 10, 0)
    adjacent_pair[0][1] = adjacent_pair[0][2] = 2
    adjacent_pair[2][1] = 4
    adjacent_pair[2][4] = 4

    occupied_pair_interior = full_grid(6, 10, 0)
    occupied_pair_interior[0][1] = occupied_pair_interior[0][5] = 2
    occupied_pair_interior[0][3] = 7
    occupied_pair_interior[2][1] = occupied_pair_interior[2][4] = 4

    mixed_special_profiles = full_grid(6, 10, 0)
    mixed_special_profiles[0][1] = mixed_special_profiles[0][4] = 2
    mixed_special_profiles[2][2] = mixed_special_profiles[2][6] = 4
    mixed_special_profiles[3][1] = 5
    mixed_special_profiles[3][7] = 6
    mixed_special_profiles[5][0] = mixed_special_profiles[5][3] = mixed_special_profiles[5][8] = 8

    overlapping_pair_spans = full_grid(6, 10, 0)
    overlapping_pair_spans[0][0] = overlapping_pair_spans[0][5] = 2
    overlapping_pair_spans[0][2] = overlapping_pair_spans[0][7] = 3
    overlapping_pair_spans[3][1] = overlapping_pair_spans[3][4] = 4

    return [
        ("blank_no_rule_signal", blank),
        ("adjacent_identity_pair", adjacent_pair),
        ("occupied_pair_interior", occupied_pair_interior),
        ("mixed_mismatch_and_triple_profiles", mixed_special_profiles),
        ("overlapping_pair_spans", overlapping_pair_spans),
    ]
