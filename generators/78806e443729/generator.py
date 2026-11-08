"""Generator for horizontal beams emitted by one or two seeds per active row.

Every nonzero seed paints horizontally through cells that were zero in the
original input.  Original nonzero cells stop a ray.  When two seeds share a
row, both rays cover the gap and row-major application makes the right seed's
color win there, matching the canonical Racket rule.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78806e443729"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "65a855ce11f7"
SUMMARY = (
    "A 0-background grid with two to five active rows. Each active row has "
    "one or two separated interior singleton seeds; the canonical rule casts "
    "their colors horizontally until an original seed or grid edge."
)
INVARIANTS = [
    "background is 0",
    "there are exactly 2..5 active rows",
    "each active row contains one or two interior single-cell seeds",
    "two seeds in one row have different colors and at least one zero between them",
    "same-color seeds are never orthogonally adjacent across active rows",
]

BRANCH_PROFILES = ("mixed", "single_only", "double_only")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 5..14",
        "valid": "5..14",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 8..18",
        "valid": "8..18",
        "doc": "Grid width; all seeds remain interior.",
    },
    "row_count": {
        "type": "int",
        "default": "difficulty-weighted 2..5",
        "valid": "2..5",
        "doc": "Exact number of active rows.",
    },
    "branch_profile": {
        "type": "enum",
        "default": "weighted toward mixed",
        "valid": "mixed|single_only|double_only",
        "doc": "Whether active rows use both seed-count branches or only one.",
    },
}


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _seed_counts(row_count: int, profile: str, rng) -> list[int]:
    if profile == "single_only":
        return [1] * row_count
    if profile == "double_only":
        return [2] * row_count
    if profile != "mixed":
        raise ValueError(f"unknown branch_profile: {profile!r}")
    counts = [1, 2] + [rng.choice((1, 2)) for _ in range(row_count - 2)]
    rng.shuffle(counts)
    return counts


def _sample_seed_cols(rng, width: int, seed_count: int) -> list[int]:
    """Choose one or two interior columns, separating a pair by a zero cell."""
    choices = list(range(1, width - 1))
    if seed_count == 1:
        return [rng.choice(choices)]
    if seed_count != 2:
        raise ValueError(f"unsupported seed_count: {seed_count}")
    legal_pairs = [
        (left, right)
        for left in choices
        for right in choices
        if left < right - 1
    ]
    if not legal_pairs:
        raise ValueError(f"width {width} cannot hold two separated interior seeds")
    return list(rng.choice(legal_pairs))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 5, 14)
    width = ctx.draw_int_diff("grid_w", 8, 18)
    row_count = ctx.draw_int_diff("row_count", 2, 5)
    profile = ctx.draw_choice(
        "branch_profile",
        ("mixed", "mixed", "mixed", "single_only", "double_only"),
    )

    layout_rng = ctx.draw_rng("layout")
    active_rows = sorted(layout_rng.sample(range(height), row_count))
    counts = _seed_counts(row_count, profile, layout_rng)
    grid = full_grid(height, width, 0)

    previous_row = -2
    previous_colors_by_col: dict[int, int] = {}
    for slot, (row, seed_count) in enumerate(zip(active_rows, counts)):
        cols = _sample_seed_cols(layout_rng, width, seed_count)
        blocked_colors = (
            {previous_colors_by_col[col] for col in cols if col in previous_colors_by_col}
            if row == previous_row + 1
            else set()
        )
        colors = ctx.draw_distinct_colors(
            f"row_{slot}_colors",
            n=seed_count,
            exclude={0, *blocked_colors},
        )
        for col, color in zip(cols, colors):
            grid[row][col] = color
        previous_row = row
        previous_colors_by_col = dict(zip(cols, colors))

    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"errors": errors}
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a nonempty list of rows")
        return result
    if not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid rows must be nonempty lists")
        return result
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
        return result

    height = len(grid)
    if not 5 <= height <= 14:
        errors.append(f"grid height {height} outside 5..14")
    if not 8 <= width <= 18:
        errors.append(f"grid width {width} outside 8..18")

    active_rows: list[tuple[int, list[int]]] = []
    for row_index, row in enumerate(grid):
        cols = [col for col, value in enumerate(row) if value != 0]
        if not cols:
            continue
        active_rows.append((row_index, cols))
        if len(cols) not in (1, 2):
            errors.append(
                f"row {row_index} should have one or two seeds, found {len(cols)}"
            )
            continue
        if any(col in (0, width - 1) for col in cols):
            errors.append(f"row {row_index} has an edge seed at {cols}")
        if len(cols) == 2:
            if cols[1] - cols[0] <= 1:
                errors.append(
                    f"row {row_index} has adjacent seeds {cols}; the gap branch is hidden"
                )
            colors = [row[col] for col in cols]
            if colors[0] == colors[1]:
                errors.append(
                    f"row {row_index} reuses color {colors[0]} for both seeds"
                )

    if not 2 <= len(active_rows) <= 5:
        errors.append(f"expected 2..5 active rows, found {len(active_rows)}")

    for row in range(height - 1):
        for col in range(width):
            value = grid[row][col]
            if value != 0 and grid[row + 1][col] == value:
                errors.append(
                    f"same-color seeds touch vertically at ({row},{col}) and ({row + 1},{col})"
                )

    counts = [len(cols) for _, cols in active_rows if len(cols) in (1, 2)]
    if counts and all(count == 1 for count in counts):
        profile = "single_only"
    elif counts and all(count == 2 for count in counts):
        profile = "double_only"
    elif counts and {1, 2}.issubset(counts):
        profile = "mixed"
    else:
        profile = None
    result.update(
        {
            "height": height,
            "width": width,
            "active_rows": active_rows,
            "row_count": len(active_rows),
            "branch_profile": profile,
        }
    )
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    """Return exact semantic-axis values recoverable from a generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "row_count": analysis["row_count"],
        "branch_profile": analysis["branch_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject layouts that hide or contradict the horizontal-beam grammar."""
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    """Independent test oracle; generation never uses this Python mirror."""
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = original[row][col]
            if color == 0:
                continue
            left = col - 1
            while left >= 0 and original[row][left] == 0:
                output[row][left] = color
                left -= 1
            right = col + 1
            while right < width and original[row][right] == 0:
                output[row][right] = color
                right += 1
    return output
