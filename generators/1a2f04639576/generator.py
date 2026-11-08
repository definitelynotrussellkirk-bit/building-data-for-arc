"""Semantic generator for task 1a2f04639576: compact each row left.

Every row is interpreted independently.  Non-zero values keep their original
left-to-right order and slide to columns 0..n-1; zeros fill the row's suffix.

The three official linked dimension/row-count profiles are generated directly,
including the demonstrated empty-row and singleton-row branches.  A calibrated
generalized branch varies dimensions, row counts, gaps, colors, repetitions,
and locally already-compacted rows while requiring a visible whole-grid change
and an order witness that rules out color sorting.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette


GENERATOR_ID = "1a2f04639576"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8cd149b15ecf"

SUMMARY = (
    "Independently compact every row to the left: remove zero gaps, preserve "
    "the non-zero values' left-to-right order, then pad the right suffix with "
    "zeros.  Official 4x6/(3,2,0,3), 3x5/(2,2,2), and "
    "4x7/(3,1,3,0) row-count profiles are mixed with lawful generalized "
    "scenes that contain empty, singleton, repeated-color, gapped, and "
    "already-compacted row branches without allowing whole-grid no-ops."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "0 is the strict modal background and the only gap value",
    "each row contains at most four non-zero values and is compacted independently",
    "at least two rows are nonempty, at least one row has multiple values, and at least three foreground colors occur",
    "at least one row changes under left compaction, so the lesson is never a whole-grid identity",
    "generated scenes contain a descending color pair in reading order, disambiguating stable compaction from sorting",
    "the three official linked dimension/row-count signatures remain directly reachable",
]

PUBLIC_PROFILES = (
    "rows_3203_4x6",
    "rows_222_3x5",
    "rows_3130_4x7",
)
SCENE_PROFILES = PUBLIC_PROFILES + ("generalized",)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "30% official linked profile, 70% generalized",
        "valid": "rows_3203_4x6|rows_222_3x5|rows_3130_4x7|generalized",
        "doc": (
            "Exact linked (height, width, per-row non-zero counts) profile. "
            "Colors and legal column placements remain nuisance variables."
        ),
    },
}

_PROFILE_SPECS = {
    "rows_3203_4x6": (4, 6, (3, 2, 0, 3)),
    "rows_222_3x5": (3, 5, (2, 2, 2)),
    "rows_3130_4x7": (4, 7, (3, 1, 3, 0)),
}
_PUBLIC_SIGNATURES = {
    (height, width, row_counts): profile
    for profile, (height, width, row_counts) in _PROFILE_SPECS.items()
}

# Exact official inputs are accepted by self_check even when their colors are
# monotonically increasing.  All newly generated variants deliberately carry
# a descending pair so the teaching distribution itself cannot imply sorting.
_CANONICAL_INPUTS = {
    (
        (0, 2, 0, 3, 0, 4),
        (5, 0, 0, 0, 0, 6),
        (0, 0, 0, 0, 0, 0),
        (7, 0, 8, 0, 9, 0),
    ),
    (
        (0, 0, 1, 0, 2),
        (3, 0, 0, 4, 0),
        (0, 5, 0, 0, 6),
    ),
    (
        (0, 4, 0, 0, 7, 0, 1),
        (2, 0, 0, 0, 0, 0, 0),
        (0, 0, 3, 0, 5, 0, 6),
        (0, 0, 0, 0, 0, 0, 0),
    ),
}


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _compact_row(row: Sequence[int]) -> list[int]:
    values = [value for value in row if value != 0]
    return values + [0] * (len(row) - len(values))


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket rule remains authority."""
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    return [_compact_row(row) for row in converted]


def _row_counts(grid: Sequence[Sequence[int]]) -> tuple[int, ...]:
    return tuple(sum(value != 0 for value in row) for row in grid)


def canonical_profile_signature(grid) -> str | None:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        return None
    signature = (len(converted), len(converted[0]), _row_counts(converted))
    return _PUBLIC_SIGNATURES.get(signature)


def _has_order_descent(grid: Sequence[Sequence[int]]) -> bool:
    for row in grid:
        values = [value for value in row if value != 0]
        if any(left > right for left, right in zip(values, values[1:])):
            return True
    return False


def _analysis(grid) -> dict:
    converted, errors = _coerce_grid(grid)
    result = {
        "errors": errors,
        "scene_profile": None,
        "output": None,
    }
    if errors or converted is None:
        return result

    height, width = len(converted), len(converted[0])
    if not 3 <= height <= 5:
        errors.append(f"height must be in 3..5, found {height}")
    if not 5 <= width <= 7:
        errors.append(f"width must be in 5..7, found {width}")

    counts = _row_counts(converted)
    foreground = [value for row in converted for value in row if value != 0]
    foreground_counts = Counter(foreground)
    zero_count = sum(value == 0 for row in converted for value in row)
    nonempty_rows = sum(count > 0 for count in counts)
    multi_rows = sum(count >= 2 for count in counts)
    distinct_colors = len(foreground_counts)
    output = [_compact_row(row) for row in converted]
    changed_rows = sum(row != packed for row, packed in zip(converted, output))
    exact_canonical = tuple(map(tuple, converted)) in _CANONICAL_INPUTS
    public_profile = _PUBLIC_SIGNATURES.get((height, width, counts))
    scene_profile = public_profile or "generalized"

    if not foreground:
        errors.append("at least five foreground cells are required")
    elif len(foreground) < 5:
        errors.append(f"at least five foreground cells are required, found {len(foreground)}")
    if any(count > 4 for count in counts):
        errors.append(f"each row may contain at most four non-zero values, found {counts}")
    if nonempty_rows < 2:
        errors.append(f"at least two rows must be nonempty, found {nonempty_rows}")
    if multi_rows < 1:
        errors.append("at least one row must contain multiple non-zero values")
    if distinct_colors < 3:
        errors.append(f"at least three foreground colors are required, found {distinct_colors}")
    if foreground_counts and zero_count <= max(foreground_counts.values()):
        errors.append("0 must be the strict modal background")
    if changed_rows < 1:
        errors.append("whole-grid identity: no row changes under left compaction")
    if scene_profile == "generalized" and len(set(counts)) < 2:
        errors.append("generalized scenes must vary row counts")
    if not exact_canonical and not _has_order_descent(converted):
        errors.append("missing descending order witness; sorting remains a shortcut")

    result.update(
        {
            "errors": errors,
            "scene_profile": scene_profile,
            "public_profile": public_profile,
            "row_counts": counts,
            "foreground_total": len(foreground),
            "foreground_color_count": distinct_colors,
            "zero_count": zero_count,
            "changed_rows": changed_rows,
            "order_descent": _has_order_descent(converted),
            "exact_canonical": exact_canonical,
            "output": output,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject invalid, degenerate, no-op, and sorting-ambiguous lessons."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _difficulty_band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _generalized_spec(rng, band: str) -> tuple[int, int, tuple[int, ...]]:
    dimension_options = {
        "easy": ((3, 5), (3, 6), (4, 5), (4, 6)),
        "medium": tuple(
            (height, width)
            for height in range(3, 6)
            for width in range(5, 8)
        ),
        "hard": ((4, 6), (4, 7), (5, 6), (5, 7)),
    }
    max_count = 4 if band == "hard" else 3
    for _attempt in range(256):
        height, width = rng.choice(dimension_options[band])
        counts = [rng.randint(1, max_count) for _ in range(height)]
        if rng.random() < {"easy": 0.55, "medium": 0.50, "hard": 0.40}[band]:
            counts[rng.randrange(height)] = 0
        if not any(count == 1 for count in counts) and rng.random() < 0.65:
            counts[rng.randrange(height)] = 1
        if max(counts) < 2:
            counts[rng.randrange(height)] = 2
        if len(set(counts)) < 2:
            index = rng.randrange(height)
            counts[index] = 0 if counts[index] != 0 else 2
        signature = (height, width, tuple(counts))
        if signature in _PUBLIC_SIGNATURES:
            continue
        if sum(counts) < 5 or sum(count > 0 for count in counts) < 2:
            continue
        return height, width, tuple(counts)
    raise RuntimeError("unable to draw a lawful generalized row-count profile")


def _displaced_columns(width: int, count: int, rng) -> list[int]:
    if count <= 0:
        return []
    if count == 1:
        return [rng.randint(1, width - 1)]
    # Keep column 0 sometimes, but force at least one gap before the last value.
    if count < width - 1 and rng.random() < 0.6:
        return list(range(count - 1)) + [rng.randint(count, width - 1)]
    return sorted(rng.sample(range(1, width), count))


def _column_layout(width: int, counts: Sequence[int], rng) -> list[list[int]]:
    columns = [
        sorted(rng.sample(range(width), count)) if count else []
        for count in counts
    ]
    nonempty = [index for index, count in enumerate(counts) if count > 0]
    compact_row = rng.choice(nonempty)
    columns[compact_row] = list(range(counts[compact_row]))

    displaced_candidates = [
        index
        for index in nonempty
        if index != compact_row and counts[index] < width
    ]
    if not displaced_candidates:
        displaced_candidates = [
            index for index in nonempty if counts[index] < width
        ]
    displaced_row = rng.choice(displaced_candidates)
    columns[displaced_row] = _displaced_columns(
        width, counts[displaced_row], rng
    )
    return columns


def _paint_colors(
    grid: list[list[int]], columns: Sequence[Sequence[int]], rng, band: str
) -> None:
    slots = [
        (row_index, col)
        for row_index, row_columns in enumerate(columns)
        for col in row_columns
    ]
    total = len(slots)
    min_palette = 4 if band == "hard" and total >= 6 else 3
    max_palette = min(total - 1, {"easy": 5, "medium": 7, "hard": 8}[band], 9)
    palette_size = rng.randint(min_palette, max(min_palette, max_palette))
    palette = list(random_palette(rng, palette_size))
    colors = palette + [rng.choice(palette) for _ in range(total - palette_size)]
    rng.shuffle(colors)
    for (row, col), color in zip(slots, colors):
        grid[row][col] = color

    witness_rows = [index for index, row_columns in enumerate(columns) if len(row_columns) >= 2]
    witness_row = rng.choice(witness_rows)
    first_col, second_col = columns[witness_row][:2]
    grid[witness_row][first_col] = max(palette)
    grid[witness_row][second_col] = min(palette)

    # Preserve at least three distinct colors after forcing the descending pair.
    used = {value for row in grid for value in row if value != 0}
    if len(used) < 3:
        third_color = next(color for color in palette if color not in used)
        spare = next(slot for slot in slots if slot not in ((witness_row, first_col), (witness_row, second_col)))
        grid[spare[0]][spare[1]] = third_color


def _draw_scene(profile: str, band: str, rng) -> list[list[int]]:
    if profile in _PROFILE_SPECS:
        height, width, counts = _PROFILE_SPECS[profile]
    else:
        height, width, counts = _generalized_spec(rng, band)
    columns = _column_layout(width, counts, rng)
    grid = full_grid(height, width, 0)
    _paint_colors(grid, columns, rng, band)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")

    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        ("generalized",) * 7 + PUBLIC_PROFILES,
    )
    rng = ctx.draw_rng("layout")
    for _attempt in range(128):
        grid = _draw_scene(profile, band, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"unable to construct valid scene_profile={profile!r}")
