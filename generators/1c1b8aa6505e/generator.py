"""Generator for ARC task ``1c1b8aa6505e`` (legacy puzzle ``8597cfd7``).

The unique full-width gray (5) row divides the input into top and bottom
regions.  Count red (2) and yellow (4) independently above and below that row.
Whichever color has the larger *absolute* top-vs-bottom count difference wins;
the output is a solid 2x2 block of that color.

The curriculum is deliberately counter-shortcut.  Its four count profiles
alternate the true winner, include both top-heavy and bottom-heavy winners,
and include cases where the true winner has fewer total/top/bottom cells than
the loser.  Thus total-count, one-side-only, signed-difference, and constant
color rules are all falsified in every three-example lesson.  Placement is
randomized independently of the count profile so cell position is not an
answer key.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c1b8aa6505e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8976ac81fa5b"
EXPECTED_OUTPUT_CODOMAIN = 2
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "One full-width gray(5) divider splits a 0-background grid. Red(2) and "
    "yellow(4) occur on both sides. Compare each color's absolute difference "
    "between top and bottom counts; output a solid 2x2 block of the color "
    "with the larger imbalance."
)

INVARIANTS = [
    "exactly one interior full-width gray(5) divider row and no other gray cells",
    "red(2) and yellow(4) each occur at least once above and below the divider",
    "the red and yellow absolute top-bottom count differences are unequal",
    "all non-divider cells use only background 0, red 2, or yellow 4",
    "ordinary count profiles falsify total-count and one-side-only winner shortcuts",
]

DIVIDER_POSITIONS = ("upper", "center", "lower")

# Base counts are (red_top, red_bottom, yellow_top, yellow_bottom).  A common
# non-negative scale is added to all four entries, preserving both imbalances
# while varying density.  The profile order exposes all four semantic cases over a four-sample cycle;
# every three consecutive samples are already sufficient to kill all named rivals.
COUNT_PROFILES = {
    # red wins 3 vs 1 even though red has fewer total/top/bottom cells.
    "red_top_low_total": (4, 1, 5, 4),
    # yellow wins 3 vs 1 even though yellow has fewer total/top/bottom cells.
    "yellow_top_low_total": (5, 4, 4, 1),
    # yellow wins 4 vs 2; equal totals, but the winning imbalance points down.
    "yellow_bottom_equal_total": (4, 2, 1, 5),
    # red wins 4 vs 2; equal totals, but the winning imbalance points down.
    "red_bottom_equal_total": (1, 5, 4, 2),
}
PROFILE_SEQUENCE = tuple(COUNT_PROFILES)
COUNT_SCALES = (0, 1, 2)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "two-thirds canonical anchor (9 or 11), otherwise difficulty-aware 9..18",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "two-thirds canonical anchor width 9, otherwise difficulty-aware 9..18",
        "valid": "9..18",
    },
    "divider_position": {
        "type": "str",
        "default": "canonical anchors center; other draws cycle upper|center|lower",
        "valid": "upper|center|lower",
    },
    "count_profile": {
        "type": "str",
        "default": "four-profile semantic schedule",
        "valid": "red_top_low_total|yellow_top_low_total|yellow_bottom_equal_total|red_bottom_equal_total",
    },
    "count_scale": {
        "type": "int",
        "default": "cycles 0..2",
        "valid": "0..2",
    },
}

# Every declared exact-axis combination is constructible.  Even the smallest
# 9x9 upper/lower split has far more free cells than the densest profile.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
SCHEDULE_PROFILES = PROFILE_SEQUENCE


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-case semantic schedule used by the lesson gate."""
    del seed, difficulty
    return PROFILE_SEQUENCE[int(sample_index) % len(PROFILE_SEQUENCE)]


def _divider_row(position: str, height: int) -> int:
    """Deterministic, observable divider row for an exact semantic position."""
    if position == "upper":
        return max(2, height // 3)
    if position == "center":
        return height // 2
    if position == "lower":
        return min(height - 3, (2 * height) // 3)
    raise ValueError(f"unknown divider_position {position!r}")


def _scaled_counts(profile: str, scale: int) -> tuple[int, int, int, int]:
    try:
        base = COUNT_PROFILES[profile]
    except KeyError as exc:
        raise ValueError(f"unknown count_profile {profile!r}") from exc
    if scale not in COUNT_SCALES:
        raise ValueError(f"count_scale {scale!r} outside {COUNT_SCALES}")
    return tuple(value + scale for value in base)


_COUNT_SIGNATURE_TO_AXES = {
    _scaled_counts(profile, scale): (profile, scale)
    for profile in PROFILE_SEQUENCE
    for scale in COUNT_SCALES
}


def _canonical_anchor(seed: int, sample_index: int, overrides: dict) -> bool:
    """Two-thirds of ordinary draws use a real canonical (h,w,palette) profile.

    Explicit overrides disable the anchor so every declared axis can be tested
    independently across its full advertised domain.  Anchor membership depends
    only on sample-index parity, while anchor height depends on seed/block parity;
    neither canonical height is tied to one output color.
    """
    del seed
    return not overrides and int(sample_index) % 3 != 0


def _draw_axis_values(ctx, seed: int, sample_index: int, overrides: dict):
    anchor = _canonical_anchor(seed, sample_index, overrides)

    if "grid_h" in overrides and overrides.get("grid_h") is not None:
        height = ctx.draw_int_diff("grid_h", 9, 18)
    elif anchor:
        # Alternate both canonical heights independently of winner profile.
        anchor_height = (9, 11)[(int(seed) + int(sample_index) // 4) % 2]
        height = ctx.draw_int("grid_h", anchor_height, anchor_height)
    else:
        height = ctx.draw_int_diff("grid_h", 9, 18)

    if "grid_w" in overrides and overrides.get("grid_w") is not None:
        width = ctx.draw_int_diff("grid_w", 9, 18)
    elif anchor:
        width = ctx.draw_int("grid_w", 9, 9)
    else:
        width = ctx.draw_int_diff("grid_w", 9, 18)

    if "divider_position" in overrides and overrides.get("divider_position") is not None:
        position = ctx.draw_choice("divider_position", DIVIDER_POSITIONS)
    else:
        scheduled_position = (
            "center" if anchor
            else DIVIDER_POSITIONS[int(sample_index) % len(DIVIDER_POSITIONS)]
        )
        position = ctx.draw_choice("divider_position", (scheduled_position,))

    if "count_profile" in overrides and overrides.get("count_profile") is not None:
        profile = ctx.draw_choice("count_profile", PROFILE_SEQUENCE)
    else:
        profile = ctx.draw_choice(
            "count_profile", (schedule_profile(seed, sample_index, ctx.difficulty),)
        )

    if "count_scale" in overrides and overrides.get("count_scale") is not None:
        scale = ctx.draw_int("count_scale", 0, 2)
    else:
        scheduled_scale = (int(sample_index) // len(PROFILE_SEQUENCE)) % 3
        scale = ctx.draw_int("count_scale", scheduled_scale, scheduled_scale)

    return height, width, position, profile, scale



def _grow_connected(cells, count: int, rng):
    """Choose ``count`` 4-connected cells inside one rectangular region."""
    available = set(cells)
    if count > len(available):
        raise ValueError(f"connected placement needs {count} cells, only {len(available)} available")
    start = rng.choice(sorted(available))
    chosen = {start}
    while len(chosen) < count:
        frontier = sorted({
            (row + dr, col + dc)
            for row, col in chosen
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (row + dr, col + dc) in available and (row + dr, col + dc) not in chosen
        })
        if not frontier:
            raise ValueError("connected placement unexpectedly exhausted its frontier")
        chosen.add(rng.choice(frontier))
    return chosen


def _place_canonical_like_components(
    grid, divider: int, red_top: int, red_bottom: int,
    yellow_top: int, yellow_bottom: int, ctx
) -> None:
    """Keep canonical-scale anchors near the real five-object morphology.

    Each color forms one connected component in each half, plus the divider.
    Which color occupies the left/right region is independently randomized so
    the canonical-like layout cannot serve as a fixed positional answer key.
    """
    height, width = len(grid), len(grid[0])
    split = width // 2
    left_cols = range(0, split)
    right_cols = range(split + 1, width)
    top_rows = range(0, divider)
    bottom_rows = range(divider + 1, height)
    side_rng = ctx.draw_rng("canonical_side_swap")
    red_left = bool(side_rng.randint(0, 1))
    red_cols = left_cols if red_left else right_cols
    yellow_cols = right_cols if red_left else left_cols

    specs = (
        (2, top_rows, red_cols, red_top, "canonical_red_top"),
        (2, bottom_rows, red_cols, red_bottom, "canonical_red_bottom"),
        (4, top_rows, yellow_cols, yellow_top, "canonical_yellow_top"),
        (4, bottom_rows, yellow_cols, yellow_bottom, "canonical_yellow_bottom"),
    )
    for color, rows, cols, count, label in specs:
        candidates = [(row, col) for row in rows for col in cols]
        for row, col in _grow_connected(candidates, count, ctx.draw_rng(label)):
            if grid[row][col] != 0:
                raise ValueError("canonical-like component placement collided")
            grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, position, profile, scale = _draw_axis_values(
        ctx, seed, sample_index, overrides
    )
    divider = _divider_row(position, height)
    red_top, red_bottom, yellow_top, yellow_bottom = _scaled_counts(profile, scale)

    grid = full_grid(height, width, 0)
    grid[divider] = [5] * width

    if _canonical_anchor(seed, sample_index, overrides):
        _place_canonical_like_components(
            grid, divider, red_top, red_bottom, yellow_top, yellow_bottom, ctx
        )
    else:
        # Broad lessons scatter cells without replacement. Counts are exact:
        # there are no placement collisions that can silently alter the rule.
        rng_top = ctx.draw_rng("placement_top")
        rng_bottom = ctx.draw_rng("placement_bottom")
        top_cells = [(row, col) for row in range(divider) for col in range(width)]
        bottom_cells = [
            (row, col)
            for row in range(divider + 1, height)
            for col in range(width)
        ]
        rng_top.shuffle(top_cells)
        rng_bottom.shuffle(bottom_cells)

        top_need = red_top + yellow_top
        bottom_need = red_bottom + yellow_bottom
        if top_need > len(top_cells) or bottom_need > len(bottom_cells):
            raise ValueError(
                "requested count profile does not fit divider geometry: "
                f"top {top_need}/{len(top_cells)}, bottom {bottom_need}/{len(bottom_cells)}"
            )

        for row, col in top_cells[:red_top]:
            grid[row][col] = 2
        for row, col in top_cells[red_top:top_need]:
            grid[row][col] = 4
        for row, col in bottom_cells[:red_bottom]:
            grid[row][col] = 2
        for row, col in bottom_cells[red_bottom:bottom_need]:
            grid[row][col] = 4
    return grid


def _analyze(grid) -> dict[str, object]:
    """Return structural facts without assuming generator scheduling."""
    result: dict[str, object] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "divider": None,
        "counts": (0, 0, 0, 0),
    }
    errors: list[str] = result["errors"]  # type: ignore[assignment]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid is empty or not a list of non-empty rows")
        return result
    height, width = len(grid), len(grid[0])
    result["height"], result["width"] = height, width
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid rows have inconsistent widths")
        return result

    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or value not in {0, 2, 4, 5}
    ]
    if bad_values:
        errors.append("grid uses values outside the task palette {0,2,4,5}")
        return result

    gray_rows = [
        row for row in range(height)
        if all(grid[row][col] == 5 for col in range(width))
    ]
    if len(gray_rows) != 1:
        errors.append(f"expected exactly one full gray divider row, found {len(gray_rows)}")
        return result
    divider = gray_rows[0]
    result["divider"] = divider
    if divider in (0, height - 1):
        errors.append("gray divider row must be interior")
    if any(
        grid[row][col] == 5
        for row in range(height)
        if row != divider
        for col in range(width)
    ):
        errors.append("gray cells may appear only in the full divider row")

    def count(color: int, top: bool) -> int:
        rows = range(divider) if top else range(divider + 1, height)
        return sum(1 for row in rows for value in grid[row] if value == color)

    counts = (
        count(2, True), count(2, False),
        count(4, True), count(4, False),
    )
    result["counts"] = counts
    red_top, red_bottom, yellow_top, yellow_bottom = counts
    if red_top == 0 or red_bottom == 0:
        errors.append("red(2) must occur above and below the divider")
    if yellow_top == 0 or yellow_bottom == 0:
        errors.append("yellow(4) must occur above and below the divider")
    if abs(red_top - red_bottom) == abs(yellow_top - yellow_bottom):
        errors.append("red and yellow absolute top-bottom differences are tied")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background 0 must remain present")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mutation-sensitive validity predicate for the broad teaching grammar."""
    del difficulty, meta
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    height, width = int(info["height"]), int(info["width"])
    if not (9 <= height <= 18):
        errors.append(f"height {height} outside generated/canonical envelope 9..18")
    if not (9 <= width <= 18):
        errors.append(f"width {width} outside generated/canonical envelope 9..18")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold without baking in the examples' column layout.

    The public examples happen to place each color in a vertical column, but
    the authoritative rule ignores columns completely.  Treating column
    alignment as semantic would teach the very fixed-position shortcut this
    generator is meant to refute, so strictness is based on canonical size,
    palette/divider roles, and the real count relation instead.
    """
    reasons = self_check(grid)
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    if (height, width) not in {(9, 9), (11, 9)}:
        reasons.append("dimensions are not one of the two canonical profiles 9x9 or 11x9")
    info = _analyze(grid)
    if info["divider"] != height // 2:
        reasons.append("canonical divider is the center row")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 4, 5}:
        reasons.append(f"canonical palette must be exactly {{0,2,4,5}}, got {sorted(palette)}")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned grid."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    height = int(info["height"])
    divider = int(info["divider"])
    positions = {
        name: _divider_row(name, height)
        for name in DIVIDER_POSITIONS
    }
    matches = [name for name, row in positions.items() if row == divider]
    position = matches[0] if len(matches) == 1 else None
    profile_scale = _COUNT_SIGNATURE_TO_AXES.get(tuple(info["counts"]))
    profile, scale = profile_scale if profile_scale is not None else (None, None)
    return {
        "grid_h": height,
        "grid_w": int(info["width"]),
        "divider_position": position,
        "count_profile": profile,
        "count_scale": scale,
    }


def _winner(grid) -> int:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("malformed lesson: " + "; ".join(info["errors"]))
    red_top, red_bottom, yellow_top, yellow_bottom = info["counts"]
    red_diff = abs(red_top - red_bottom)
    yellow_diff = abs(yellow_top - yellow_bottom)
    if red_diff == yellow_diff:
        raise ValueError("ambiguous tied imbalance")
    return 2 if red_diff > yellow_diff else 4


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror; canonical Racket remains output authority."""
    return full_grid(2, 2, _winner(grid))


def _constant(color: int):
    return lambda grid: full_grid(2, 2, color)


def _winner_by_score(grid, score: Callable[[tuple[int, int, int, int]], tuple[int, int]]):
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("malformed lesson")
    red_score, yellow_score = score(tuple(info["counts"]))
    return full_grid(2, 2, 2 if red_score > yellow_score else 4)


def _larger_total(grid):
    return _winner_by_score(
        grid, lambda c: (c[0] + c[1], c[2] + c[3])
    )


def _larger_top_count(grid):
    return _winner_by_score(grid, lambda c: (c[0], c[2]))


def _larger_bottom_count(grid):
    return _winner_by_score(grid, lambda c: (c[1], c[3]))


def _signed_top_minus_bottom(grid):
    return _winner_by_score(grid, lambda c: (c[0] - c[1], c[2] - c[3]))


SEMANTIC_RIVALS = {
    "always_red": _constant(2),
    "always_yellow": _constant(4),
    "larger_total_count": _larger_total,
    "larger_top_count": _larger_top_count,
    "larger_bottom_count": _larger_bottom_count,
    "signed_top_minus_bottom": _signed_top_minus_bottom,
}


def _lawful_counts(grid):
    info = _analyze(grid)
    return None if info["errors"] else tuple(info["counts"])


def _red_wins(grid) -> bool:
    counts = _lawful_counts(grid)
    return counts is not None and abs(counts[0] - counts[1]) > abs(counts[2] - counts[3])


def _yellow_wins(grid) -> bool:
    counts = _lawful_counts(grid)
    return counts is not None and abs(counts[2] - counts[3]) > abs(counts[0] - counts[1])


def _winner_has_smaller_total(grid) -> bool:
    counts = _lawful_counts(grid)
    if counts is None:
        return False
    r_total, y_total = counts[0] + counts[1], counts[2] + counts[3]
    return (_red_wins(grid) and r_total < y_total) or (_yellow_wins(grid) and y_total < r_total)


def _winner_has_smaller_top(grid) -> bool:
    counts = _lawful_counts(grid)
    if counts is None:
        return False
    return (_red_wins(grid) and counts[0] < counts[2]) or (_yellow_wins(grid) and counts[2] < counts[0])


def _winner_has_smaller_bottom(grid) -> bool:
    counts = _lawful_counts(grid)
    if counts is None:
        return False
    return (_red_wins(grid) and counts[1] < counts[3]) or (_yellow_wins(grid) and counts[3] < counts[1])


def _winner_is_bottom_heavy(grid) -> bool:
    counts = _lawful_counts(grid)
    if counts is None:
        return False
    return (_red_wins(grid) and counts[1] > counts[0]) or (_yellow_wins(grid) and counts[3] > counts[2])


SEMANTIC_WITNESSES = {
    "red_wins": _red_wins,
    "yellow_wins": _yellow_wins,
    "winner_has_smaller_total": _winner_has_smaller_total,
    "winner_has_smaller_top_count": _winner_has_smaller_top,
    "winner_has_smaller_bottom_count": _winner_has_smaller_bottom,
    "bottom_heavy_winner_requires_absolute_difference": _winner_is_bottom_heavy,
}

WITNESS_RIVALS = {
    "red_wins": ["always_yellow"],
    "yellow_wins": ["always_red"],
    "winner_has_smaller_total": ["larger_total_count"],
    "winner_has_smaller_top_count": ["larger_top_count"],
    "winner_has_smaller_bottom_count": ["larger_bottom_count"],
    "bottom_heavy_winner_requires_absolute_difference": ["signed_top_minus_bottom"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if any named plausible shortcut survives its demos."""
    reasons: list[str] = []
    for index, episode in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{role} input malformed: {findings[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with absolute-imbalance rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"demos do not falsify shortcut {name!r}")
        except Exception as exc:
            reasons.append(f"shortcut {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
