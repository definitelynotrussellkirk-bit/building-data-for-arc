"""Generator for ARC task dc2aa30b / 3108da8bf9e8.

The 11x11 input contains a 3x3 macro-grid of 3x3 blocks separated by
all-zero rows and columns.  Each block uses colors 1 and 2 and has a unique
number of color-1 cells.  The rule sorts whole blocks by that count, placing
small counts across the bottom row and large counts across the top row while
preserving every block's internal texture.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from itertools import combinations, permutations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3108da8bf9e8"
TASK_ID = "3108da8bf9e8"
VERSION = "3.2.0"
RULE_HASH = "05977542b8d5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Create an 11x11 grid split by zero rows and columns at indices 3 and 7 "
    "into nine 3x3 blocks. Every block is filled only with colors 1 and 2, "
    "and the nine blocks have distinct color-1 counts chosen from 0..9, so "
    "exactly one count is omitted. The transformation moves whole blocks: "
    "sort them by ascending color-1 count, place the three smallest left-to-"
    "right on the bottom macro-row, the next three on the middle row, and "
    "the three largest on the top row. Preserve separators and every block's "
    "internal pattern exactly."
)

INVARIANTS = [
    "the grid is exactly 11x11",
    "rows 3 and 7 and columns 3 and 7 are entirely color 0",
    "all remaining cells are literal integer colors 1 or 2",
    "the nine 3x3 blocks have nine distinct color-1 counts from 0..9",
    "exactly one lawful count in 0..9 is omitted",
]

# The absent one-count is the only exact input-distribution control.  It is
# recoverable from every returned grid by observe_overrides().
AXES = {
    "omitted_count": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "0..9",
    },
}

BLOCK_ORIGINS = tuple((br * 4, bc * 4) for br in range(3) for bc in range(3))
TARGET_BLOCKS = (
    (2, 0),
    (2, 1),
    (2, 2),
    (1, 0),
    (1, 1),
    (1, 2),
    (0, 0),
    (0, 1),
    (0, 2),
)
ROW_MAJOR_BLOCKS = tuple((br, bc) for br in range(3) for bc in range(3))


def _difficulty_band(difficulty: Any) -> str:
    """Normalize the public difficulty hint to one of three deterministic bands."""
    if difficulty is None:
        return "medium"
    if isinstance(difficulty, str):
        if difficulty in {"easy", "medium", "hard"}:
            return difficulty
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)):
        raise TypeError(
            "difficulty must be None, a band name, or a numeric value in 0..1"
        )
    value = float(difficulty)
    if not 0.0 <= value <= 1.0:
        raise ValueError("numeric difficulty must be in 0..1")
    if value < 1.0 / 3.0:
        return "easy"
    if value < 2.0 / 3.0:
        return "medium"
    return "hard"


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override(s): {', '.join(unknown)}")
    if "omitted_count" in overrides:
        value = overrides["omitted_count"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("omitted_count override must be a literal integer in 0..9")
        if not 0 <= value <= 9:
            raise ValueError("omitted_count override must be in 0..9")


def _official_row_major_counts(sorted_counts: list[int]) -> list[int]:
    """Counts as they appear row-major after the official transformation."""
    return sorted_counts[6:9] + sorted_counts[3:6] + sorted_counts[0:3]


def _rowwise_sorted_counts(order: list[int]) -> list[int]:
    """Apply the tempting wrong rule that sorts only inside each macro-row."""
    return [
        count
        for start in (0, 3, 6)
        for count in sorted(order[start : start + 3])
    ]


def _columnwise_sorted_counts(order: list[int]) -> list[int]:
    """Sort each macro-column high-to-low without moving blocks across columns."""
    result = list(order)
    for column in range(3):
        values = sorted(
            (order[column], order[3 + column], order[6 + column]),
            reverse=True,
        )
        result[column], result[3 + column], result[6 + column] = values
    return result


def _reverse_macro_row_counts(order: list[int]) -> list[int]:
    """Apply the tempting wrong fixed transform that reverses the macro-rows."""
    return order[6:9] + order[3:6] + order[0:3]


def _position_map(order: list[int], official: list[int]) -> tuple[int, ...]:
    """Destination macro-position for every current macro-position."""
    destination = {value: index for index, value in enumerate(official)}
    return tuple(destination[value] for value in order)


def _cycle_lengths(position_map: tuple[int, ...]) -> tuple[int, ...]:
    """Cycle lengths of an input-position -> output-position permutation."""
    seen: set[int] = set()
    lengths: list[int] = []
    for start in range(len(position_map)):
        if start in seen:
            continue
        current = start
        length = 0
        while current not in seen:
            seen.add(current)
            length += 1
            current = position_map[current]
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def _cycles_pack_into_three_triples(lengths: tuple[int, ...]) -> bool:
    """Whether invariant cycles fit inside three independent groups of size three."""
    if any(length > 3 for length in lengths):
        return False
    bins = [0, 0, 0]

    def place(index: int) -> bool:
        if index == len(lengths):
            return bins == [3, 3, 3]
        length = lengths[index]
        tried: set[int] = set()
        for bin_index, used in enumerate(bins):
            if used in tried or used + length > 3:
                continue
            tried.add(used)
            bins[bin_index] += length
            if place(index + 1):
                return True
            bins[bin_index] -= length
        return False

    return place(0)


def _has_three_group_local_sort_shortcut(
    order: list[int], official: list[int]
) -> bool:
    """Whether some partition into three triples can sort the input locally."""
    return _cycles_pack_into_three_triples(_cycle_lengths(_position_map(order, official)))


def _easy_four_cycles() -> tuple[tuple[int, int, int, int], ...]:
    """Four-position cycles spanning all macro-rows and all macro-columns."""
    cycles: list[tuple[int, int, int, int]] = []
    for positions in combinations(range(9), 4):
        if len({index // 3 for index in positions}) != 3:
            continue
        if len({index % 3 for index in positions}) != 3:
            continue
        anchor = min(positions)
        remainder = tuple(index for index in positions if index != anchor)
        cycles.extend((anchor, *tail) for tail in permutations(remainder))
    return tuple(cycles)


EASY_FOUR_CYCLES = _easy_four_cycles()


def _apply_position_cycle(
    order: list[int], cycle: tuple[int, int, int, int]
) -> list[int]:
    """Move each value to the next position in ``cycle``."""
    result = list(order)
    values = [order[index] for index in cycle]
    for offset, value in enumerate(values):
        result[cycle[(offset + 1) % len(cycle)]] = value
    return result


def _reject_layout_shortcuts(
    order: list[int], official: list[int], sorted_counts: list[int]
) -> bool:
    """Return true when a candidate collapses to a simpler positional lesson."""
    return (
        order == official
        or order == sorted_counts
        or _rowwise_sorted_counts(order) == official
        or _columnwise_sorted_counts(order) == official
        or _reverse_macro_row_counts(order) == official
        or _has_three_group_local_sort_shortcut(order, official)
    )


def _input_count_order(counts: list[int], band: str, rng) -> list[int]:
    """Choose a varied arrangement whose difficulty is its rank displacement."""
    sorted_counts = sorted(counts)
    official = _official_row_major_counts(sorted_counts)

    if band == "easy":
        # Move four blocks in one cycle whose positions span every macro-row and
        # macro-column.  Only four blocks need repair, but no decomposition into
        # three independent triples can solve the example locally.
        cycle = rng.choice(EASY_FOUR_CYCLES)
        order = _apply_position_cycle(official, cycle)
        if _reject_layout_shortcuts(order, official, sorted_counts):
            raise AssertionError("easy four-cycle unexpectedly preserved a shortcut")
        return order

    # Medium and hard both use broad permutations.  Medium leaves one to four
    # positions already correct; hard is a full derangement.  Every draw rejects
    # named positional shortcuts and the complete 280-member class of local
    # three-groups-of-three sorting hypotheses.
    order = list(sorted_counts)
    for _ in range(1024):
        rng.shuffle(order)
        displaced = sum(a != b for a, b in zip(order, official))
        in_band = 5 <= displaced <= 8 if band == "medium" else displaced == 9
        if in_band and not _reject_layout_shortcuts(order, official, sorted_counts):
            return list(order)
    raise RuntimeError(
        f"could not draw a shortcut-resistant {band} block permutation"
    )


def _block_values(one_count: int, rng) -> list[int]:
    """Sample uniformly from the 3x3 textures with exactly ``one_count`` ones."""
    if one_count == 0:
        return [2] * 9
    if one_count == 9:
        return [1] * 9
    chosen = set(rng.sample(range(9), one_count))
    return [1 if index in chosen else 2 for index in range(9)]


def _is_row_major_prefix(values: list[int], one_count: int) -> bool:
    return values == [1] * one_count + [2] * (9 - one_count)


def _force_non_prefix_texture(values: list[int], one_count: int) -> list[int]:
    """Change one prefix texture without changing its occupancy."""
    if not 0 < one_count < 9 or not _is_row_major_prefix(values, one_count):
        return values
    repaired = list(values)
    repaired[one_count - 1], repaired[one_count] = (
        repaired[one_count],
        repaired[one_count - 1],
    )
    return repaired


def _write_block(grid: list[list[int]], br: int, bc: int, values: list[int]) -> None:
    for index, value in enumerate(values):
        dr, dc = divmod(index, 3)
        grid[br * 4 + dr][bc * 4 + dc] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, canonical-lawful input grid."""
    _validate_overrides(overrides)
    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    omitted_count = ctx.draw_int("omitted_count", 0, 9)
    counts = [count for count in range(10) if count != omitted_count]
    order_rng = ctx.draw_rng(f"macro_order_{band}")
    texture_rng = ctx.draw_rng(f"block_texture_{band}")
    count_order = _input_count_order(counts, band, order_rng)

    textures = {
        one_count: _block_values(one_count, texture_rng)
        for one_count in counts
    }
    # Uniform sampling may legitimately draw the row-major prefix for any one
    # block.  Only the all-prefix grid would make the wrong repaint-by-count
    # rule indistinguishable, so repair that vanishingly rare joint event rather
    # than permanently banning one texture location from every occupancy.
    if all(_is_row_major_prefix(textures[count], count) for count in counts):
        witness_count = next(count for count in counts if 0 < count < 9)
        textures[witness_count] = _force_non_prefix_texture(
            textures[witness_count], witness_count
        )

    grid = full_grid(11, 11, 0)
    for (br, bc), one_count in zip(ROW_MAJOR_BLOCKS, count_order):
        _write_block(grid, br, bc, textures[one_count])
    return grid


def _extract_blocks(grid: list[list[int]]) -> list[list[list[int]]]:
    return [
        [
            [grid[br * 4 + dr][bc * 4 + dc] for dc in range(3)]
            for dr in range(3)
        ]
        for br, bc in ROW_MAJOR_BLOCKS
    ]


def _block_count(block: list[list[int]]) -> int:
    return sum(value == 1 for row in block for value in row)


def _block_one_counts(grid) -> list[int]:
    return [_block_count(block) for block in _extract_blocks(grid)]


def _place_blocks(
    blocks: list[list[list[int]]],
    destinations: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> list[list[int]]:
    output = full_grid(11, 11, 0)
    for block, (br, bc) in zip(blocks, destinations):
        for dr in range(3):
            for dc in range(3):
                output[br * 4 + dr][bc * 4 + dc] = block[dr][dc]
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket rule."""
    blocks = _extract_blocks(grid)
    sorted_blocks = sorted(blocks, key=_block_count)
    return _place_blocks(sorted_blocks, TARGET_BLOCKS)


# Historical helper name used by some review probes.
_solve_grid = rule_mirror


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe overrides on invalid grid: {errors}")
    present = set(_block_one_counts(grid))
    missing = sorted(set(range(10)) - present)
    if len(missing) != 1:
        raise ValueError(f"expected exactly one omitted count, got {missing}")
    return {"omitted_count": missing[0]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed grids and sort-key shortcuts while accepting canonical data."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list):
        return ["grid must be a list of 11 rows"]
    if len(grid) != 11:
        return [f"grid must have 11 rows, got {len(grid)}"]
    if any(not isinstance(row, list) for row in grid):
        return ["every grid row must be a list"]
    widths = [len(row) for row in grid]
    if any(width != 11 for width in widths):
        return [f"grid rows must all have width 11, got {widths}"]

    non_integer = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int
    ]
    if non_integer:
        return [
            "all cells must be literal integers (bools are not colors); "
            f"first invalid cell is {non_integer[0]}"
        ]

    invalid_colors = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in {0, 1, 2}
    ]
    if invalid_colors:
        errors.append(
            "grid may use only separator color 0 and block colors {1, 2}; "
            f"first invalid cell is {invalid_colors[0]}"
        )

    for index in (3, 7):
        if any(grid[index][c] != 0 for c in range(11)):
            errors.append(f"separator row {index} must be entirely 0")
        if any(grid[r][index] != 0 for r in range(11)):
            errors.append(f"separator column {index} must be entirely 0")

    bad_block_cells = [
        (r, c, grid[r][c])
        for br, bc in ROW_MAJOR_BLOCKS
        for r in range(br * 4, br * 4 + 3)
        for c in range(bc * 4, bc * 4 + 3)
        if grid[r][c] not in {1, 2}
    ]
    if bad_block_cells:
        errors.append(
            "non-separator block cells must use only {1, 2}; "
            f"first invalid cell is {bad_block_cells[0]}"
        )

    counts = _block_one_counts(grid)
    if len(set(counts)) != 9:
        errors.append(f"block color-1 counts must be unique, got {counts}")
    missing = sorted(set(range(10)) - set(counts))
    if len(missing) != 1:
        errors.append(
            "block color-1 counts must select nine values from 0..9 and omit "
            f"exactly one, got counts={counts}, missing={missing}"
        )

    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict) and "omitted_count" in requested and not errors:
            observed = missing[0]
            if requested["omitted_count"] != observed:
                errors.append(
                    "omitted_count override mismatch: requested "
                    f"{requested['omitted_count']}, observed {observed}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """For this task the lawful generated manifold matches the canonical one."""
    return self_check(grid)


# ---------------------------------------------------------------------------
# Explicit shortcut rules and semantic witnesses
# ---------------------------------------------------------------------------


def _identity_rule(grid: list[list[int]]) -> list[list[int]]:
    return copy.deepcopy(grid)


def _top_left_ascending_rule(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: put ascending blocks row-major from the top-left."""
    blocks = sorted(_extract_blocks(grid), key=_block_count)
    return _place_blocks(blocks, ROW_MAJOR_BLOCKS)


def _repaint_by_count_rule(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: preserve counts but replace each block's texture."""
    blocks = sorted(_extract_blocks(grid), key=_block_count)
    repainted: list[list[list[int]]] = []
    for block in blocks:
        one_count = _block_count(block)
        values = [1] * one_count + [2] * (9 - one_count)
        repainted.append([values[0:3], values[3:6], values[6:9]])
    return _place_blocks(repainted, TARGET_BLOCKS)


def _sort_within_macro_rows_rule(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: sort each existing macro-row but never cross rows."""
    blocks = _extract_blocks(grid)
    reordered = [
        block
        for start in (0, 3, 6)
        for block in sorted(blocks[start : start + 3], key=_block_count)
    ]
    return _place_blocks(reordered, ROW_MAJOR_BLOCKS)


def _sort_within_macro_columns_rule(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: sort each macro-column but never cross columns."""
    blocks = _extract_blocks(grid)
    reordered: list[list[list[int]] | None] = [None] * 9
    for column in range(3):
        column_blocks = sorted(
            (blocks[column], blocks[3 + column], blocks[6 + column]),
            key=_block_count,
            reverse=True,
        )
        reordered[column], reordered[3 + column], reordered[6 + column] = column_blocks
    return _place_blocks(
        [block for block in reordered if block is not None],
        ROW_MAJOR_BLOCKS,
    )


def _reverse_macro_rows_rule(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: reverse the three macro-rows without reading counts."""
    blocks = _extract_blocks(grid)
    return _place_blocks(blocks[6:9] + blocks[3:6] + blocks[0:3], ROW_MAJOR_BLOCKS)


def _requires_reordering(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _identity_rule(grid)


def _bottom_first_target_order(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _top_left_ascending_rule(grid)


def _preserves_block_texture(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _repaint_by_count_rule(grid)


def _requires_cross_row_ranking(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _sort_within_macro_rows_rule(grid)


def _requires_cross_column_ranking(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _sort_within_macro_columns_rule(grid)


def _not_fixed_macro_row_reversal(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _reverse_macro_rows_rule(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity_rule,
    "ascending_from_top_left": _top_left_ascending_rule,
    "repaint_blocks_from_counts": _repaint_by_count_rule,
    "sort_within_macro_rows": _sort_within_macro_rows_rule,
    "sort_within_macro_columns": _sort_within_macro_columns_rule,
    "reverse_macro_rows": _reverse_macro_rows_rule,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "requires_reordering": _requires_reordering,
    "bottom_first_target_order": _bottom_first_target_order,
    "preserves_block_texture": _preserves_block_texture,
    "requires_cross_row_ranking": _requires_cross_row_ranking,
    "requires_cross_column_ranking": _requires_cross_column_ranking,
    "not_fixed_macro_row_reversal": _not_fixed_macro_row_reversal,
}
WITNESS_RIVALS = {
    "requires_reordering": ["identity"],
    "bottom_first_target_order": ["ascending_from_top_left"],
    "preserves_block_texture": ["repaint_blocks_from_counts"],
    "requires_cross_row_ranking": ["sort_within_macro_rows"],
    "requires_cross_column_ranking": ["sort_within_macro_columns"],
    "not_fixed_macro_row_reversal": ["reverse_macro_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named wrong rule that survives demos but changes the query."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives_demos = all(
            competitor(copy.deepcopy(demo["input"])) == demo["output"]
            for demo in demos
        )
        if not survives_demos:
            continue
        competitor_query = competitor(copy.deepcopy(query["input"]))
        if competitor_query != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons
