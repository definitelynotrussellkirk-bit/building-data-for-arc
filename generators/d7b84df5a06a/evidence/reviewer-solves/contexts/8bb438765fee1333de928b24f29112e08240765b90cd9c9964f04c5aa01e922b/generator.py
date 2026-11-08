"""Generator for arc_additional_puzzle_bank_volume23:H159.

Gray (5) full wall lines divide the input into four rectangular chambers.
For each chamber independently, count seed colors 2, 3, and 4.  Preserve the
walls and seeds, and replace only the chamber's zero cells with the mapped
unique plurality color (2 -> 6, 3 -> 7, 4 -> 8); use 9 whenever the largest
seed count is tied.

Every ordinary draw contains four deliberately different vote profiles: all
three unique winners, a top-count tie, a unique plurality without a strict
majority, and a lower-count tie beneath a unique winner.  One demonstration
therefore refutes the canonical majority-only and any-positive-tie shortcuts
instead of merely producing clean-looking chamber grids.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import permutations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d7b84df5a06a"
TASK_ID = "d7b84df5a06a"
VERSION = "3.0.0"
RULE_HASH = "8ba1dc91d063"
SUMMARY = (
    "A 0-background grid is split into four rectangular chambers by one full "
    "horizontal and one full vertical color-5 wall.  Each chamber contains "
    "sparse 2/3/4 seeds.  Preserve walls and seeds; fill only zeros with "
    "6/7/8 for the chamber-local unique plurality of 2/3/4, or 9 when the "
    "largest count is tied.  Every normal draw includes all winner mappings, "
    "a tie, and a plurality-without-majority counterexample."
)
INVARIANTS = [
    "the input palette is exactly {0,2,3,4,5}",
    "one interior full row and one interior full column of 5 form four rectangular chambers",
    "every chamber has at least one seed and at least one zero",
    "all three unique plurality winners and a top-count tie occur in every ordinary draw",
    "one chamber has a unique plurality without a strict majority and tied lower counts",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_H_LO, _H_HI = 11, 19
_W_LO, _W_HI = 13, 21
_ALLOWED_OVERRIDES = frozenset({"grid_h", "grid_w"})
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (2, 3, 4)
_FILL_BY_SEED = {2: 6, 3: 7, 4: 8}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "25% canonical 11; otherwise banded 11..19",
        "valid": "11..19",
    },
    "grid_w": {
        "type": "int",
        "default": "25% canonical 13; otherwise banded 13..21",
        "valid": "13..21",
    },
}

# Every fourth sample is pinned to the one canonical input profile
# (11 rows, 13 columns, five input colors), independently in every difficulty
# band.  The semantic gate verifies the declared schedule.
SCHEDULE_PROFILES = ("canonical_scale", "general_scale")
EXAMPLES_NEEDED = 1
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return "canonical_scale" if sample_index % 4 == 0 else "general_scale"


def _valid_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["input must be a non-empty 2D grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["input must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    bad = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2, 3, 4, 5)
    ]
    if bad:
        return [f"input palette must be a subset of {{0,2,3,4,5}}, found {sorted(set(bad), key=repr)}"]
    return []


def _full_wall_lines(grid):
    height, width = len(grid), len(grid[0])
    rows = [row for row in range(height) if all(value == 5 for value in grid[row])]
    cols = [col for col in range(width) if all(grid[row][col] == 5 for row in range(height))]
    return rows, cols


def _chambers(grid):
    """4-connected non-wall components in reading order."""
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        component = []
        for row, col in queue:
            component.append((row, col))
            for drow, dcol in _DIRS4:
                other = (row + drow, col + dcol)
                if other in unseen:
                    unseen.remove(other)
                    queue.append(other)
        out.append(sorted(component))
    return out


def _counts(grid, chamber) -> Counter:
    return Counter(
        grid[row][col]
        for row, col in chamber
        if grid[row][col] in _SEED_COLORS
    )


def _decision(counts: Counter, *, tie_value=9, majority_only=False, any_positive_tie=False):
    ranked = sorted(
        ((counts[color], color) for color in _SEED_COLORS),
        key=lambda item: (-item[0], item[1]),
    )
    top_count, top_color = ranked[0]
    if top_count == 0:
        return None
    positive_counts = [counts[color] for color in _SEED_COLORS if counts[color] > 0]
    if any_positive_tie and len(positive_counts) != len(set(positive_counts)):
        return tie_value
    if ranked[1][0] == top_count:
        return tie_value
    if majority_only and top_count * 2 <= sum(positive_counts):
        return tie_value
    return _FILL_BY_SEED[top_color]


def _apply_with_decider(grid, decider: Callable[[Counter], int | None]):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    result = [list(row) for row in grid]
    for chamber in _chambers(grid):
        fill = decider(_counts(grid, chamber))
        if fill is None:
            continue
        for row, col in chamber:
            if grid[row][col] == 0:
                result[row][col] = fill
    return result


def rule_mirror(grid):
    """Independent, input-pure Python mirror of the selected Racket rule."""
    return _apply_with_decider(grid, _decision)


def _marker_identity(grid):
    def decide(counts):
        fill = _decision(counts)
        if fill in (6, 7, 8):
            return fill - 4
        return fill
    return _apply_with_decider(grid, decide)


def _numeric_tie_break(grid):
    def decide(counts):
        ranked = sorted(
            ((counts[color], color) for color in _SEED_COLORS),
            key=lambda item: (-item[0], item[1]),
        )
        if ranked[0][0] == 0:
            return None
        return _FILL_BY_SEED[ranked[0][1]]
    return _apply_with_decider(grid, decide)


def _majority_only(grid):
    return _apply_with_decider(
        grid, lambda counts: _decision(counts, majority_only=True)
    )


def _any_positive_tie(grid):
    return _apply_with_decider(
        grid, lambda counts: _decision(counts, any_positive_tie=True)
    )


def _global_plurality(grid):
    global_counts = Counter(
        value for row in grid for value in row if value in _SEED_COLORS
    )
    fill = _decision(global_counts)
    result = [list(row) for row in grid]
    if fill is None:
        return result
    for chamber in _chambers(grid):
        for row, col in chamber:
            if grid[row][col] == 0:
                result[row][col] = fill
    return result


SEMANTIC_RIVALS = {
    "marker_identity": _marker_identity,
    "numeric_tie_break": _numeric_tie_break,
    "majority_only": _majority_only,
    "any_positive_tie": _any_positive_tie,
    "global_plurality": _global_plurality,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Both shortcuts fit all five canonical pairs.  Every generated scene
    # contains a chamber that separates each shortcut from the true rule.
    "majority_only": _majority_only,
    "any_positive_tie": _any_positive_tie,
}


def _chamber_facts(grid):
    facts = []
    for chamber in _chambers(grid):
        counts = _counts(grid, chamber)
        positive_total = sum(counts.values())
        ranked = sorted(
            ((counts[color], color) for color in _SEED_COLORS),
            key=lambda item: (-item[0], item[1]),
        )
        top_count = ranked[0][0]
        winners = [color for color in _SEED_COLORS if counts[color] == top_count and top_count > 0]
        facts.append({
            "counts": counts,
            "total": positive_total,
            "winners": winners,
            "fill": _decision(counts),
            "has_zero": any(grid[row][col] == 0 for row, col in chamber),
        })
    return facts


def _has_winner(grid, color):
    return any(fact["winners"] == [color] for fact in _chamber_facts(grid))


def _has_top_tie(grid):
    return any(len(fact["winners"]) >= 2 for fact in _chamber_facts(grid))


def _has_plurality_without_majority(grid):
    return any(
        len(fact["winners"]) == 1
        and fact["counts"][fact["winners"][0]] * 2 <= fact["total"]
        for fact in _chamber_facts(grid)
    )


def _has_lower_count_tie(grid):
    for fact in _chamber_facts(grid):
        if len(fact["winners"]) != 1:
            continue
        winner = fact["winners"][0]
        lower = [fact["counts"][color] for color in _SEED_COLORS if color != winner]
        if lower[0] == lower[1] > 0:
            return True
    return False


def _has_three_way_tie(grid):
    return any(len(fact["winners"]) == 3 for fact in _chamber_facts(grid))


def _has_independent_outcomes(grid):
    fills = {fact["fill"] for fact in _chamber_facts(grid) if fact["fill"] is not None}
    return len(fills) >= 3


SEMANTIC_WITNESSES = {
    "mapped_winner_2": lambda grid: _has_winner(grid, 2),
    "mapped_winner_3": lambda grid: _has_winner(grid, 3),
    "mapped_winner_4": lambda grid: _has_winner(grid, 4),
    "top_count_tie": _has_top_tie,
    "plurality_without_majority": _has_plurality_without_majority,
    "lower_count_tie": _has_lower_count_tie,
    "three_way_tie": _has_three_way_tie,
    "independent_chamber_outcomes": _has_independent_outcomes,
}
WITNESS_RIVALS = {
    "mapped_winner_2": ["marker_identity"],
    "mapped_winner_3": ["marker_identity"],
    "mapped_winner_4": ["marker_identity"],
    "top_count_tie": ["numeric_tie_break"],
    "plurality_without_majority": ["majority_only"],
    "lower_count_tie": ["any_positive_tie"],
    "three_way_tie": ["numeric_tie_break"],
    "independent_chamber_outcomes": ["global_plurality"],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/non-task scenes without requiring teaching witnesses."""
    del difficulty, meta
    errors = _valid_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (_H_LO <= height <= _H_HI and _W_LO <= width <= _W_HI):
        errors.append(
            f"dimensions {height}x{width} outside {_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}"
        )
    wall_rows, wall_cols = _full_wall_lines(grid)
    if len(wall_rows) != 1 or len(wall_cols) != 1:
        errors.append(
            f"expected exactly one full wall row and one full wall column, got {len(wall_rows)} and {len(wall_cols)}"
        )
        return errors
    wall_row, wall_col = wall_rows[0], wall_cols[0]
    if wall_row in (0, height - 1) or wall_col in (0, width - 1):
        errors.append("full wall lines must be interior")
    expected_walls = {
        (wall_row, col) for col in range(width)
    } | {
        (row, wall_col) for row in range(height)
    }
    actual_walls = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    }
    if actual_walls != expected_walls:
        errors.append("all color-5 cells must belong to the two complete wall lines")
    chambers = _chambers(grid)
    if len(chambers) != 4:
        errors.append(f"wall cross must create four chambers, got {len(chambers)}")
    for index, chamber in enumerate(chambers):
        marker_count = sum(_counts(grid, chamber).values())
        zero_count = sum(grid[row][col] == 0 for row, col in chamber)
        if not 1 <= marker_count <= 6:
            errors.append(f"chamber {index} must contain 1..6 seed markers, got {marker_count}")
        if zero_count < 1:
            errors.append(f"chamber {index} has no zero cell to fill")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact task-manifold grammar shared by canonical and generated inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _wall_position(rng, size):
    # Each side receives at least four cells, enough for the largest five-seed
    # profile plus at least one zero even at the smallest declared canvas.
    return rng.randint(4, size - 5)


def _core_vote_profiles(rng, sample_index):
    """Four profiles covering every decisive branch in one scene."""
    colors = list(_SEED_COLORS)
    perm = list(permutations(colors))[rng.randrange(6)]
    first, second, third = perm
    nonmajority = {first: 2, second: 1, third: 1}
    winner_second = {second: 2, first: 1, third: 0}
    winner_third = {third: 2, first: 1, second: 0}
    if sample_index % 3 == 0:
        tie = {first: 1, second: 1, third: 1}
    else:
        tie = {first: 2, second: 2, third: 1}
    profiles = [nonmajority, winner_second, winner_third, tie]
    rng.shuffle(profiles)
    return profiles


def _paint_markers(grid, chamber, counts, rng):
    cells = list(chamber)
    rng.shuffle(cells)
    colors = []
    for color in _SEED_COLORS:
        colors.extend([color] * counts.get(color, 0))
    rng.shuffle(colors)
    if len(colors) >= len(cells):
        raise ValueError("vote profile leaves no zero cell in chamber")
    for (row, col), color in zip(cells, colors):
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(
            f"unknown override key(s) {unknown}; valid keys are {sorted(_ALLOWED_OVERRIDES)}"
        )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")
    marker_rng = ctx.draw_rng("markers")
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile == "canonical_scale" and not overrides:
        height = ctx.draw_int("grid_h", 11, 11)
        width = ctx.draw_int("grid_w", 13, 13)
    else:
        band = difficulty or "medium"
        if band == "easy":
            h_range, w_range = (11, 13), (13, 15)
        elif band == "hard":
            h_range, w_range = (16, 19), (18, 21)
        else:
            h_range, w_range = (13, 16), (15, 18)
        height = _banded_int(ctx, overrides, "grid_h", *h_range, _H_LO, _H_HI)
        width = _banded_int(ctx, overrides, "grid_w", *w_range, _W_LO, _W_HI)

    wall_row = _wall_position(layout_rng, height)
    wall_col = _wall_position(layout_rng, width)
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[wall_row][col] = 5
    for row in range(height):
        grid[row][wall_col] = 5

    chambers = _chambers(grid)
    profiles = _core_vote_profiles(marker_rng, sample_index)
    for chamber, counts in zip(chambers, profiles):
        _paint_markers(grid, chamber, counts, marker_rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def lesson_identifiable(demos, query) -> list[str]:
    """One generated demonstration must identify the query against all rivals."""
    reasons = []
    if not demos:
        return ["need at least one demonstration"]
    required = {
        "mapped_winner_2",
        "mapped_winner_3",
        "mapped_winner_4",
        "top_count_tie",
        "plurality_without_majority",
        "lower_count_tie",
        "independent_chamber_outcomes",
    }
    fired = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = strict_canonical_like(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with chamber plurality rule")
        for name, witness in SEMANTIC_WITNESSES.items():
            if witness(grid):
                fired.add(name)
    missing = sorted(required - fired)
    if missing:
        reasons.append(f"demonstrations omit decisive witness(es): {missing}")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"rival rule remains consistent: {name}")

    query_grid = query.get("input")
    query_output = query.get("output")
    query_errors = strict_canonical_like(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query answer disagrees with chamber plurality rule")
    return reasons


def mutation_fixtures():
    """Task-local near misses that the structural contract must reject."""
    valid = generate(seed=7, sample_index=1, difficulty="medium")

    ragged = deepcopy(valid)
    ragged[0] = ragged[0][:-1]

    bad_color = deepcopy(valid)
    bad_color[0][0] = 1

    missing_wall = deepcopy(valid)
    wall_rows, _ = _full_wall_lines(missing_wall)
    missing_wall[wall_rows[0]][0] = 0

    partial_extra_wall = deepcopy(valid)
    partial_extra_wall[0][1] = 5

    seedless = deepcopy(valid)
    chamber = _chambers(seedless)[0]
    for row, col in chamber:
        if seedless[row][col] in _SEED_COLORS:
            seedless[row][col] = 0

    zero_less = deepcopy(valid)
    chamber = _chambers(zero_less)[1]
    for row, col in chamber:
        if zero_less[row][col] == 0:
            zero_less[row][col] = 2

    return [
        ("ragged_grid", ragged),
        ("unknown_palette_color", bad_color),
        ("broken_full_wall", missing_wall),
        ("partial_extra_wall", partial_extra_wall),
        ("seedless_chamber", seedless),
        ("zero_less_chamber", zero_less),
    ]
