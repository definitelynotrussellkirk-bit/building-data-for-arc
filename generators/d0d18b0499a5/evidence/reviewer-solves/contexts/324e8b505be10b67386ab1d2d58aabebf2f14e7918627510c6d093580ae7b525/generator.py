"""Generator for ``d0d18b0499a5`` — close exactly-two-marker rows.

The canonical rule examines rows independently on a fresh zero canvas.  A row
contributes a cyan (8) interval exactly when it contains two nonzero cells; the
interval runs from the left marker through the right marker, inclusive.  Rows
with zero, one, or three-or-more markers contribute nothing, and input marker
colors never survive in the output.

The three-slot default schedule is lesson-level.  Every three consecutive
demonstrations contain (1) a strict canonical-manifold anchor, (2) a qualifying
row whose two markers have different colors, and (3) a non-color-2 qualifying
row plus singleton/four-marker decoys.  Together these refute the natural
shortcuts "only color 2 matters", "the two markers must match", and "close any
row with at least two markers" while retaining one-third canonical support in
every difficulty band.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Point = tuple[int, int]

GENERATOR_ID = "d0d18b0499a5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e70c66638e4c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "On a 0-background grid, inspect each row independently. If and only if a "
    "row has exactly two nonzero cells, paint the inclusive interval between "
    "them cyan (8) on a fresh same-size output; every other row remains zero. "
    "The default three-slot schedule includes strict canonical anchors, "
    "mixed-color qualifying pairs, and singleton/triple/four-marker decoys."
)

INVARIANTS = [
    "the input is a rectangular 5..18 by 8..22 ARC grid with background 0",
    "at least one row has exactly two nonzero markers separated by an interior cell",
    "at least one active row has a marker count other than two",
    "the output is a fresh same-size grid using only 0 and 8",
    "marker colors are nuisance variables; row-local nonzero count and horizontal span determine the answer",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-slot schedule with canonical anchors and difficulty scaling",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "three-slot schedule with canonical anchors and difficulty scaling",
        "valid": "8..22",
    },
    "n_active_rows": {
        "type": "int",
        "default": "three-slot schedule 3..5",
        "valid": "3..5",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "three-slot schedule 1..3",
        "valid": "1..3",
    },
}

# Every Cartesian combination is constructible because the minimum height is
# five, the maximum active-row request is five, and every scene has enough
# marker cells to realize three distinct nonzero colors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "mixed_color_pair",
    "decoy_boundary",
)

# Joint canonical signatures extracted executably from all two train inputs and
# the held-out test input.  The tuple is:
#   (height, width, sorted active-row marker counts, sorted qualifying spans,
#    sorted nonzero palette, all nonzero cells are isolated singletons).
_CANONICAL_SIGNATURES = {
    (8, 11, (1, 2, 2, 3), (5, 5), (2,), True),
    (9, 10, (2, 2, 3), (4, 6), (2,), True),
    (8, 12, (1, 2, 2, 3), (4, 6), (2,), True),
}

_CANONICAL_PROFILES = (
    {"grid_h": 8, "grid_w": 11, "row_counts": (2, 2, 3, 1), "spans": (5, 5)},
    {"grid_h": 9, "grid_w": 10, "row_counts": (2, 2, 3), "spans": (6, 4)},
    {"grid_h": 8, "grid_w": 12, "row_counts": (2, 2, 3, 1), "spans": (4, 6)},
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic slot for a draw; independent of band and seed."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _canonical_profile_index(seed: int, sample_index: int) -> int:
    return (int(seed) + int(sample_index) // len(SCHEDULE_PROFILES)) % len(
        _CANONICAL_PROFILES
    )


def _scheduled_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical_anchor":
        canonical = _CANONICAL_PROFILES[_canonical_profile_index(seed, sample_index)]
        return {
            "grid_h": int(canonical["grid_h"]),
            "grid_w": int(canonical["grid_w"]),
            "n_active_rows": len(canonical["row_counts"]),
            "n_distinct_colors": 1,
        }

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    if profile == "mixed_color_pair":
        return {
            "easy": {"grid_h": 7, "grid_w": 10, "n_active_rows": 3, "n_distinct_colors": 2},
            "medium": {"grid_h": 10, "grid_w": 14, "n_active_rows": 4, "n_distinct_colors": 3},
            "hard": {"grid_h": 14, "grid_w": 18, "n_active_rows": 5, "n_distinct_colors": 3},
        }[band]
    return {
        "easy": {"grid_h": 8, "grid_w": 12, "n_active_rows": 4, "n_distinct_colors": 1},
        "medium": {"grid_h": 11, "grid_w": 16, "n_active_rows": 5, "n_distinct_colors": 2},
        "hard": {"grid_h": 18, "grid_w": 22, "n_active_rows": 5, "n_distinct_colors": 3},
    }[band]


def _normalize_grid(grid: Any) -> tuple[Grid | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]

    normalized: Grid = []
    for row_index, row in enumerate(grid):
        normalized_row: list[int] = []
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [
                    f"cell ({row_index},{column_index}) is not a literal ARC color 0..9: {value!r}"
                ]
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized, []


def _row_columns(grid: Sequence[Sequence[int]], row: int) -> list[int]:
    return [column for column, value in enumerate(grid[row]) if value != 0]


def _row_counts(grid: Sequence[Sequence[int]]) -> list[int]:
    return [len(_row_columns(grid, row)) for row in range(len(grid))]


def _active_rows(grid: Sequence[Sequence[int]]) -> list[int]:
    return [row for row, count in enumerate(_row_counts(grid)) if count > 0]


def _qualifying_rows(grid: Sequence[Sequence[int]]) -> list[int]:
    return [row for row, count in enumerate(_row_counts(grid)) if count == 2]


def _qualifying_span_lengths(grid: Sequence[Sequence[int]]) -> tuple[int, ...]:
    spans = []
    for row in _qualifying_rows(grid):
        columns = _row_columns(grid, row)
        spans.append(columns[-1] - columns[0] + 1)
    return tuple(sorted(spans))


def _nonzero_palette(grid: Sequence[Sequence[int]]) -> tuple[int, ...]:
    return tuple(sorted({value for row in grid for value in row if value != 0}))


def _all_nonzero_singletons(grid: Sequence[Sequence[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, column + dc
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0:
                    return False
    return True


def canonical_profile_signature(grid: Any) -> tuple[Any, ...] | None:
    normalized, errors = _normalize_grid(grid)
    if errors:
        return None
    assert normalized is not None
    counts = tuple(sorted(count for count in _row_counts(normalized) if count > 0))
    return (
        len(normalized),
        len(normalized[0]),
        counts,
        _qualifying_span_lengths(normalized),
        _nonzero_palette(normalized),
        _all_nonzero_singletons(normalized),
    )


def observe_overrides(grid: Any) -> dict[str, int]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    assert normalized is not None
    return {
        "grid_h": len(normalized),
        "grid_w": len(normalized[0]),
        "n_active_rows": len(_active_rows(normalized)),
        "n_distinct_colors": len(_nonzero_palette(normalized)),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, rule-hiding, or override-mismatched scenes."""
    del difficulty
    normalized, errors = _normalize_grid(grid)
    if errors:
        return errors
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])

    if not 5 <= height <= 18:
        errors.append(f"height {height} outside declared envelope 5..18")
    if not 8 <= width <= 22:
        errors.append(f"width {width} outside declared envelope 8..22")
    palette = _nonzero_palette(normalized)
    if not palette:
        errors.append("expected at least one nonzero marker")
    if len(palette) > 3:
        errors.append(f"expected at most three nonzero colors, found {len(palette)}")

    active = _active_rows(normalized)
    qualifying = _qualifying_rows(normalized)
    decoys = [row for row in active if row not in qualifying]
    if not 3 <= len(active) <= 5:
        errors.append(f"expected 3..5 active rows, found {len(active)}")
    if not qualifying:
        errors.append("expected at least one row with exactly two nonzero markers")
    if not decoys:
        errors.append("expected at least one active decoy row whose marker count is not two")
    if qualifying and not any(
        _row_columns(normalized, row)[1] - _row_columns(normalized, row)[0] >= 2
        for row in qualifying
    ):
        errors.append("expected a qualifying pair with at least one interior span cell")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested:
        observed = observe_overrides(normalized)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(
                    f"override {key} requested {value!r}, observed {observed.get(key)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Require one of the three complete linked empirical canonical profiles."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        reasons.append(f"joint canonical signature not observed: {signature!r}")
    return reasons


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        columns = _row_columns(grid, row)
        if len(columns) == 2:
            for column in range(columns[0], columns[1] + 1):
                output[row][column] = 8
    return output


def _rival_at_least_two(grid: Sequence[Sequence[int]]) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        columns = _row_columns(grid, row)
        if len(columns) >= 2:
            for column in range(columns[0], columns[-1] + 1):
                output[row][column] = 8
    return output


def _rival_same_color_pairs_only(grid: Sequence[Sequence[int]]) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        columns = _row_columns(grid, row)
        if len(columns) == 2 and grid[row][columns[0]] == grid[row][columns[1]]:
            for column in range(columns[0], columns[1] + 1):
                output[row][column] = 8
    return output


def _rival_any_active_row(grid: Sequence[Sequence[int]]) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        columns = _row_columns(grid, row)
        if columns:
            for column in range(columns[0], columns[-1] + 1):
                output[row][column] = 8
    return output


def _rival_color_2_only(grid: Sequence[Sequence[int]]) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        columns = [column for column, value in enumerate(grid[row]) if value == 2]
        if len(columns) == 2:
            for column in range(columns[0], columns[1] + 1):
                output[row][column] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "at_least_two": _rival_at_least_two,
    "any_active_row": _rival_any_active_row,
    "same_color_pairs_only": _rival_same_color_pairs_only,
    "color_2_only": _rival_color_2_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "same_color_pairs_only": _rival_same_color_pairs_only,
    "color_2_only": _rival_color_2_only,
}


def _has_triple_decoy(grid: Sequence[Sequence[int]]) -> bool:
    return 3 in _row_counts(grid)


def _has_singleton_decoy(grid: Sequence[Sequence[int]]) -> bool:
    return 1 in _row_counts(grid)


def _has_four_plus_decoy(grid: Sequence[Sequence[int]]) -> bool:
    return any(count >= 4 for count in _row_counts(grid))


def _has_mixed_color_pair(grid: Sequence[Sequence[int]]) -> bool:
    for row in _qualifying_rows(grid):
        columns = _row_columns(grid, row)
        if grid[row][columns[0]] != grid[row][columns[1]]:
            return True
    return False


def _has_non_color_2_pair(grid: Sequence[Sequence[int]]) -> bool:
    for row in _qualifying_rows(grid):
        columns = _row_columns(grid, row)
        if all(grid[row][column] != 2 for column in columns):
            return True
    return False


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "triple_decoy": _has_triple_decoy,
    "singleton_decoy": _has_singleton_decoy,
    "four_plus_decoy": _has_four_plus_decoy,
    "mixed_color_pair": _has_mixed_color_pair,
    "non_color_2_pair": _has_non_color_2_pair,
}
WITNESS_RIVALS = {
    "triple_decoy": ["at_least_two"],
    "singleton_decoy": ["any_active_row"],
    "four_plus_decoy": ["at_least_two"],
    "mixed_color_pair": ["same_color_pairs_only"],
    "non_color_2_pair": ["color_2_only"],
}


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Require a three-demo lesson to kill every named competitor."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}")
        return reasons
    for index, pair in enumerate(demos):
        if "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} lacks input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
    if "input" not in query:
        reasons.append("query lacks input")
    elif self_check(query["input"]):
        reasons.append("query input is outside the generator grammar")

    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def _choose_columns(
    rng, width: int, count: int, *, span: int | None = None, isolated: bool = False
) -> list[int]:
    if span is not None:
        if not 2 <= span <= width:
            raise ValueError(f"span {span} does not fit width {width}")
        left = rng.randint(0, width - span)
        return [left, left + span - 1]
    if count == 1:
        return [rng.randrange(width)]
    if count == 2:
        left = rng.randint(0, width - 3)
        right = rng.randint(left + 2, width - 1)
        return [left, right]
    if isolated:
        for _attempt in range(100):
            columns = sorted(rng.sample(range(width), count))
            if all(right - left >= 2 for left, right in zip(columns, columns[1:])):
                return columns
        raise ValueError(f"could not place {count} isolated columns in width {width}")
    return sorted(rng.sample(range(width), count))


def _canonical_row_plan(seed: int, sample_index: int) -> tuple[list[int], list[int]]:
    profile = _CANONICAL_PROFILES[_canonical_profile_index(seed, sample_index)]
    return list(profile["row_counts"]), list(profile["spans"])


def _general_row_plan(profile: str, n_active_rows: int) -> tuple[list[int], list[int]]:
    if profile == "mixed_color_pair":
        qualifying_count = 2
        decoys = [3] + [1] * max(0, n_active_rows - qualifying_count - 1)
    else:
        qualifying_count = 2
        remaining = n_active_rows - qualifying_count
        decoys = ([1, 4, 3] * 2)[:remaining]
    return [2] * qualifying_count + decoys, []


def _palette_for(profile: str, n_colors: int, rng) -> list[int]:
    if profile == "canonical_anchor" and n_colors == 1:
        return [2]
    if profile == "decoy_boundary" and n_colors == 1:
        return [4]
    candidates = [1, 3, 4, 5, 6, 7, 8, 9, 2]
    chosen = rng.sample(candidates, n_colors)
    if profile == "mixed_color_pair" and n_colors >= 2 and chosen[0] == chosen[1]:
        raise AssertionError("distinct-color draw unexpectedly repeated")
    return chosen


def _paint_markers(
    grid: Grid,
    rows: list[int],
    row_counts: list[int],
    spans: list[int],
    colors: list[int],
    profile: str,
    rng,
) -> None:
    positions: list[Point] = []
    qualifying_index = 0
    row_positions: list[list[Point]] = []
    for row, count in zip(rows, row_counts):
        span = spans[qualifying_index] if count == 2 and qualifying_index < len(spans) else None
        columns = _choose_columns(
            rng,
            len(grid[0]),
            count,
            span=span,
            isolated=profile == "canonical_anchor" and colors == [2],
        )
        if count == 2:
            qualifying_index += 1
        current = [(row, column) for column in columns]
        row_positions.append(current)
        positions.extend(current)

    assignments = [colors[index % len(colors)] for index in range(len(positions))]
    rng.shuffle(assignments)

    if profile == "canonical_anchor" and colors == [2]:
        assignments = [2] * len(positions)
    elif profile == "mixed_color_pair" and len(colors) >= 2:
        first_pair = next(cells for cells in row_positions if len(cells) == 2)
        first_indices = [positions.index(cell) for cell in first_pair]
        assignments[first_indices[0]] = colors[0]
        assignments[first_indices[1]] = colors[1]
    elif profile == "decoy_boundary":
        first_pair = next(cells for cells in row_positions if len(cells) == 2)
        for cell in first_pair:
            assignments[positions.index(cell)] = next(color for color in colors if color != 2)

    # Repair coverage after profile-specific assignments so every requested
    # palette color is visible in the returned grid.
    protected = set()
    if profile == "mixed_color_pair" and len(colors) >= 2:
        protected.update(positions.index(cell) for cell in next(c for c in row_positions if len(c) == 2))
    if profile == "decoy_boundary":
        protected.update(positions.index(cell) for cell in next(c for c in row_positions if len(c) == 2))

    # Introduce each missing requested color without deleting the last occurrence
    # of another requested color.  This makes palette cardinality exact even
    # after profile-specific protected-pair assignments.
    from collections import Counter

    counts = Counter(assignments)
    for color in colors:
        if counts[color] > 0:
            continue
        candidates = [
            index
            for index, current in enumerate(assignments)
            if index not in protected and counts[current] > 1
        ]
        if not candidates:
            raise AssertionError("could not realize requested distinct-color count")
        index = candidates[0]
        counts[assignments[index]] -= 1
        assignments[index] = color
        counts[color] += 1

    for (row, column), color in zip(positions, assignments):
        grid[row][column] = color


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile = schedule_profile(seed, sample_index, difficulty)
    effective = dict(overrides)
    for key, value in _scheduled_defaults(seed, sample_index, difficulty).items():
        effective.setdefault(key, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 5, 18)
    width = ctx.draw_int("grid_w", 8, 22)
    n_active_rows = ctx.draw_int("n_active_rows", 3, 5)
    n_colors = ctx.draw_int("n_distinct_colors", 1, 3)
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")

    if profile == "canonical_anchor" and not overrides:
        row_counts, spans = _canonical_row_plan(seed, sample_index)
    else:
        row_counts, spans = _general_row_plan(profile, n_active_rows)
        if len(row_counts) != n_active_rows:
            raise AssertionError("row plan does not realize n_active_rows")

    if profile == "canonical_anchor" and not overrides:
        parity = layout_rng.randrange(2)
        candidates = list(range(parity, height, 2))
        if len(candidates) < n_active_rows:
            candidates = list(range(1 - parity, height, 2))
        rows = sorted(layout_rng.sample(candidates, n_active_rows))
    else:
        rows = sorted(layout_rng.sample(range(height), n_active_rows))
    layout_rng.shuffle(rows)
    colors = _palette_for(profile, n_colors, palette_rng)
    grid = full_grid(height, width, 0)
    _paint_markers(grid, rows, row_counts, spans, colors, profile, layout_rng)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator produced invalid scene: " + "; ".join(errors))
    return grid
