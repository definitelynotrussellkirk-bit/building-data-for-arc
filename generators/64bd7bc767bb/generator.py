"""Task-linked generator for ARC puzzle ``64bd7bc767bb``.

Canonical rule
--------------
Count input cells of colors 1, 2, 3, and 4 independently.  In the output,
column ``c`` (0 <= c < 4) is a bottom-aligned bar of color ``c + 1`` whose
height is that color's input count; every other output cell is 0.

The curriculum deliberately varies count ordering, ties, scale, placement,
and ignored colors 5..9.  Every declared axis is recoverable from the returned
input, so exact overrides and ordinary keyed draws share one auditable contract.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "64bd7bc767bb"
TASK_ID = "64bd7bc767bb"
VERSION = "2.0.0"
RULE_HASH = "47689caca367"

SUMMARY = (
    "Count colors 1..4 independently, then draw four same-color, "
    "bottom-aligned bars in output columns 0..3; colors 5..9 are ignored."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.05

INVARIANTS = [
    "rectangular input with height 5..18 and width 4..18",
    "each counted color 1, 2, 3, and 4 occurs at least once",
    "each counted-color total is strictly below the input height",
    "ordinary generated inputs encode a recoverable count-pattern and scale",
    "at most three distractor cells use colors 5..9 and do not affect output",
]

COUNT_DISTRIBUTIONS = (
    "ascending",
    "tight_spread",
    "shuffled",
    "wide_spread",
)
COUNT_MAX_KINDS = ("full", "capped")

# Normalized count vectors.  Their shapes are intentionally disjoint so the
# requested distribution is exactly observable from the returned grid.
_COUNT_OFFSETS = {
    "ascending": (0, 1, 2, 3),
    "tight_spread": (0, 1, 1, 2),
    "shuffled": (3, 0, 2, 1),
    "wide_spread": (0, 2, 4, 6),
}
_OFFSET_TO_DISTRIBUTION = {
    offsets: name for name, offsets in _COUNT_OFFSETS.items()
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng within the feasible 5..18 range",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 4..18",
        "valid": "4..18",
    },
    "count_distribution": {
        "type": "str",
        "default": "sequential four-pattern lesson schedule",
        "valid": "|".join(COUNT_DISTRIBUTIONS),
    },
    "count_max_kind": {
        "type": "str",
        "default": "sequential full|capped lesson schedule",
        "valid": "|".join(COUNT_MAX_KINDS),
    },
    "distractor_count": {
        "type": "int",
        "default": "sequential 0..3 lesson schedule",
        "valid": "0..3",
    },
}


def _minimum_height(distribution: str, max_kind: str) -> int:
    max_offset = max(_COUNT_OFFSETS[distribution])
    if max_kind == "full":
        return max(5, max_offset + 2)
    # floor(h/2) - max_offset >= 1
    return max(5, 2 * (max_offset + 1))


def _feasible_pairs(height: int) -> list[tuple[str, str]]:
    return [
        (distribution, max_kind)
        for distribution in COUNT_DISTRIBUTIONS
        for max_kind in COUNT_MAX_KINDS
        if _minimum_height(distribution, max_kind) <= height
    ]


def _scheduled_pair(sample_index: int, feasible: list[tuple[str, str]]) -> tuple[str, str]:
    """Choose a deterministic lesson branch while respecting a pinned height."""
    preferred = (
        COUNT_DISTRIBUTIONS[sample_index % len(COUNT_DISTRIBUTIONS)],
        COUNT_MAX_KINDS[sample_index % 2],
    )
    if preferred in feasible:
        return preferred
    return feasible[sample_index % len(feasible)]


def _consume_semantic_axes(ctx, sample_index: int, height: int | None):
    """Consume exact semantic axes and reject impossible combinations loudly."""
    dist_override = ctx.overrides.get("count_distribution")
    kind_override = ctx.overrides.get("count_max_kind")

    if height is None:
        # Height will be drawn after the requested/scheduled semantic pair, so
        # every single-axis override can select a feasible height automatically.
        if dist_override is None:
            distribution = COUNT_DISTRIBUTIONS[
                sample_index % len(COUNT_DISTRIBUTIONS)
            ]
            distribution = ctx.draw_choice(
                "count_distribution", [distribution]
            )
        else:
            distribution = ctx.draw_choice(
                "count_distribution", COUNT_DISTRIBUTIONS
            )

        if kind_override is None:
            max_kind = COUNT_MAX_KINDS[sample_index % 2]
            max_kind = ctx.draw_choice("count_max_kind", [max_kind])
        else:
            max_kind = ctx.draw_choice("count_max_kind", COUNT_MAX_KINDS)
        return distribution, max_kind

    feasible = _feasible_pairs(height)
    if not feasible:  # Defensive; height >= 5 always leaves full-scale pairs.
        raise ValueError(f"grid_h={height} has no feasible semantic branch")

    if dist_override is not None:
        distribution = ctx.draw_choice(
            "count_distribution", COUNT_DISTRIBUTIONS
        )
    else:
        candidates = [pair for pair in feasible if kind_override in (None, pair[1])]
        if not candidates:
            raise ValueError(
                f"grid_h={height} is incompatible with count_max_kind={kind_override!r}"
            )
        distribution = _scheduled_pair(sample_index, candidates)[0]
        distribution = ctx.draw_choice("count_distribution", [distribution])

    if kind_override is not None:
        max_kind = ctx.draw_choice("count_max_kind", COUNT_MAX_KINDS)
    else:
        candidates = [pair for pair in feasible if pair[0] == distribution]
        if not candidates:
            raise ValueError(
                f"grid_h={height} is incompatible with "
                f"count_distribution={distribution!r}"
            )
        max_kind = _scheduled_pair(sample_index, candidates)[1]
        max_kind = ctx.draw_choice("count_max_kind", [max_kind])

    if (distribution, max_kind) not in feasible:
        raise ValueError(
            f"grid_h={height} is incompatible with "
            f"count_distribution={distribution!r}, count_max_kind={max_kind!r}"
        )
    return distribution, max_kind


def _counts_for(height: int, distribution: str, max_kind: str) -> tuple[int, ...]:
    offsets = _COUNT_OFFSETS[distribution]
    target_max = height - 1 if max_kind == "full" else height // 2
    base = target_max - max(offsets)
    counts = tuple(base + offset for offset in offsets)
    if min(counts) < 1 or max(counts) >= height:
        raise ValueError(
            f"grid_h={height} cannot realize {distribution}/{max_kind}: {counts}"
        )
    return counts


def _scheduled_distractor_count(sample_index: int) -> int:
    # Every 5-pair lesson (indices 0..4) contains two distractor witnesses,
    # including one among the four demonstrations.  All values 0..3 vary.
    return (0, 1, 0, 3, 2)[sample_index % 5]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_anchor = (
        not overrides and sample_index % 3 == 0
    )

    # An explicit height is consumed first so default semantic branches can be
    # restricted to exactly the compatible set.  Without a height override,
    # choose the semantic branch first and then draw from its feasible range.
    if "grid_h" in overrides and overrides.get("grid_h") is not None:
        height = ctx.draw_int_diff("grid_h", 5, 18)
        distribution, max_kind = _consume_semantic_axes(
            ctx, sample_index, height
        )
    else:
        semantic_index = 0 if canonical_anchor else sample_index
        distribution, max_kind = _consume_semantic_axes(
            ctx, semantic_index, None
        )
        min_height = _minimum_height(distribution, max_kind)
        # Exact canonical-scale anchors in every band.  Anchor only when the
        # selected branch fits height 10; otherwise retain the full range.
        if canonical_anchor and min_height <= 10:
            height = ctx.draw_int_diff("grid_h", 10, 10)
        else:
            height = ctx.draw_int_diff("grid_h", min_height, 18)

    if canonical_anchor:
        width = ctx.draw_int_diff("grid_w", 10, 10)
    else:
        width = ctx.draw_int_diff("grid_w", 4, 18)
    if "distractor_count" in overrides and overrides.get("distractor_count") is not None:
        distractor_count = ctx.draw_int("distractor_count", 0, 3)
    else:
        scheduled = 0 if canonical_anchor else _scheduled_distractor_count(sample_index)
        distractor_count = ctx.draw_int(
            "distractor_count", scheduled, scheduled
        )

    counts = _counts_for(height, distribution, max_kind)
    grid = full_grid(height, width, 0)
    placement_rng = ctx.draw_rng("placement")
    cells = [(r, c) for r in range(height) for c in range(width)]
    placement_rng.shuffle(cells)

    cursor = 0
    for color, count in zip((1, 2, 3, 4), counts):
        for _ in range(count):
            r, c = cells[cursor]
            cursor += 1
            grid[r][c] = color

    # Distractors are deliberately separate colors and never share a cell with
    # counted objects.  The capacity proof is implicit in count construction:
    # even the densest full branch leaves at least ten background cells.
    for index in range(distractor_count):
        r, c = cells[cursor]
        cursor += 1
        grid[r][c] = 5 + (index % 5)

    return grid


def _counted_counts(grid) -> tuple[int, int, int, int]:
    counts = Counter(value for row in grid for value in row)
    return tuple(counts[color] for color in (1, 2, 3, 4))


def _distribution_from_counts(counts: tuple[int, ...]) -> str | None:
    minimum = min(counts)
    offsets = tuple(count - minimum for count in counts)
    return _OFFSET_TO_DISTRIBUTION.get(offsets)


def _max_kind_from_counts(height: int, counts: tuple[int, ...]) -> str | None:
    maximum = max(counts)
    if maximum == height - 1:
        return "full"
    if maximum == height // 2:
        return "capped"
    return None


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a returned input grid."""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    counts = _counted_counts(grid) if grid else (0, 0, 0, 0)
    return {
        "grid_h": height,
        "grid_w": width,
        "count_distribution": _distribution_from_counts(counts),
        "count_max_kind": _max_kind_from_counts(height, counts),
        "distractor_count": sum(
            1 for row in grid for value in row if 5 <= value <= 9
        ),
    }


def _is_canonical_profile(grid) -> bool:
    return bool(
        grid
        and len(grid) == 10
        and len(grid[0]) == 10
        and all(len(row) == 10 for row in grid)
        and all(isinstance(value, int) and 0 <= value <= 4
                for row in grid for value in row)
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, mutation-sensitive validity predicate for teaching inputs."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is empty or not a list of rows"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows have inconsistent widths"]
    if not (5 <= height <= 18):
        errors.append(f"height {height} is outside 5..18")
    if not (4 <= width <= 18):
        errors.append(f"width {width} is outside 4..18")

    invalid = [
        value for row in grid for value in row
        if not isinstance(value, int) or isinstance(value, bool)
        or not (0 <= value <= 9)
    ]
    if invalid:
        errors.append("grid contains non-integer or out-of-palette values")
        return errors

    counts = _counted_counts(grid)
    for color, count in zip((1, 2, 3, 4), counts):
        if count < 1:
            errors.append(f"missing counted color {color}")
        if count >= height:
            errors.append(
                f"count for color {color} ({count}) must be below height {height}"
            )
    if len(set(counts)) == 1:
        errors.append("all four counted colors have equal totals")

    distractor_count = sum(
        1 for row in grid for value in row if 5 <= value <= 9
    )
    if distractor_count > 3:
        errors.append(
            f"distractor count {distractor_count} exceeds the teaching limit 3"
        )

    canonical_meta = bool(isinstance(meta, dict) and meta.get("canonical"))
    if not canonical_meta and not _is_canonical_profile(grid):
        distribution = _distribution_from_counts(counts)
        max_kind = _max_kind_from_counts(height, counts)
        if distribution is None:
            errors.append("count totals do not encode a declared distribution")
        if max_kind is None:
            errors.append("maximum count is neither full nor capped scale")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold: 10x10, palette 0..4, and lawful count bars."""
    reasons: list[str] = []
    if not _is_canonical_profile(grid):
        reasons.append("not a 10x10 input using only canonical colors 0..4")
        return reasons
    # Canonical source rows use arbitrary lawful count combinations, so only
    # universal structural constraints apply here—not generator scheduling.
    counts = _counted_counts(grid)
    if any(count < 1 for count in counts):
        reasons.append("one or more canonical counted colors are absent")
    if any(count >= 10 for count in counts):
        reasons.append("one or more canonical counts do not fit the output")
    if len(set(counts)) == 1:
        reasons.append("all-equal counts hide color-specific height mapping")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python test mirror; the Racket rule remains output authority."""
    if self_check(grid, meta={"canonical": _is_canonical_profile(grid)}):
        raise ValueError("input is outside the generator's rule domain")
    height, width = len(grid), len(grid[0])
    counts = _counted_counts(grid)
    output = full_grid(height, width, 0)
    for column, (color, count) in enumerate(zip((1, 2, 3, 4), counts)):
        for row in range(height - count, height):
            output[row][column] = color
    return output


def _witness_ascending(grid) -> bool:
    return _distribution_from_counts(_counted_counts(grid)) == "ascending"


def _witness_tight_tie(grid) -> bool:
    return _distribution_from_counts(_counted_counts(grid)) == "tight_spread"


def _witness_shuffled_identity(grid) -> bool:
    return _distribution_from_counts(_counted_counts(grid)) == "shuffled"


def _witness_wide_spread(grid) -> bool:
    return _distribution_from_counts(_counted_counts(grid)) == "wide_spread"


def _witness_full_scale(grid) -> bool:
    return _max_kind_from_counts(len(grid), _counted_counts(grid)) == "full"


def _witness_capped_scale(grid) -> bool:
    return _max_kind_from_counts(len(grid), _counted_counts(grid)) == "capped"


def _witness_ignored_distractor(grid) -> bool:
    return any(5 <= value <= 9 for row in grid for value in row)


def _witness_no_distractor(grid) -> bool:
    return not _witness_ignored_distractor(grid)


SEMANTIC_WITNESSES = {
    "ascending_count_order": _witness_ascending,
    "tied_counts": _witness_tight_tie,
    "nonmonotone_color_identity": _witness_shuffled_identity,
    "wide_count_spread": _witness_wide_spread,
    "near_full_bar": _witness_full_scale,
    "capped_bar": _witness_capped_scale,
    "ignored_color_distractor": _witness_ignored_distractor,
    "no_distractor_control": _witness_no_distractor,
}


def _output_from_counts(grid, counts: tuple[int, ...], *, top_aligned=False):
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for column, (color, count) in enumerate(zip((1, 2, 3, 4), counts)):
        rows = range(0, count) if top_aligned else range(height - count, height)
        for row in rows:
            output[row][column] = color
    return output


def _competitor_rank_sorted(grid):
    return _output_from_counts(grid, tuple(sorted(_counted_counts(grid))))


def _competitor_rotated_color_mapping(grid):
    counts = _counted_counts(grid)
    return _output_from_counts(grid, counts[1:] + counts[:1])


def _competitor_top_aligned(grid):
    return _output_from_counts(grid, _counted_counts(grid), top_aligned=True)


def _competitor_input_column_counts(grid):
    counts = tuple(
        sum(1 for row in grid if row[column] == column + 1)
        for column in range(4)
    )
    return _output_from_counts(grid, counts)


def _competitor_presence_only(grid):
    return _output_from_counts(
        grid,
        tuple(1 if count else 0 for count in _counted_counts(grid)),
    )


def _competitor_include_distractors_in_fourth(grid):
    counts = list(_counted_counts(grid))
    counts[3] += sum(1 for row in grid for value in row if 5 <= value <= 9)
    if counts[3] >= len(grid):
        counts[3] = len(grid) - 1
    return _output_from_counts(grid, tuple(counts))


_LESSON_COMPETITORS: dict[str, Callable] = {
    "sort bar heights and ignore color identity": _competitor_rank_sorted,
    "rotate color-to-column mapping": _competitor_rotated_color_mapping,
    "top-align bars": _competitor_top_aligned,
    "count only same-color cells already in output columns":
        _competitor_input_column_counts,
    "presence-only one-cell bars": _competitor_presence_only,
    "include colors 5..9 in the fourth bar":
        _competitor_include_distractors_in_fourth,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons only when a named rival fits every demo and differs."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} input is outside rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(
                f"demo {index} output does not match independent color counts"
            )

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query"
            )
    return reasons
