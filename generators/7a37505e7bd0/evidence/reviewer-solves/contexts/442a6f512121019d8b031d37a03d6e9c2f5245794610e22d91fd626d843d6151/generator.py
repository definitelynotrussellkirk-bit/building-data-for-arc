"""Generator for ARC task d4b1c2b1.

Count every distinct grid color, including zero when it appears.  A one-color
input is unchanged.  Otherwise each input cell becomes an ``n x n`` block,
where ``n`` is the number of distinct colors.

The canonical task contains only 3x3 inputs.  This generator stays on that
profile and uses a five-sample schedule so every consecutive lesson covers all
five scale factors.  Two scheduled samples include zero alongside nonzero
colors, explicitly separating the true rule from the tempting but wrong
"count nonzero colors" shortcut.  Exactly two multicolor samples per lesson
also contain canonical identity color 3 or 8, preventing those colors from
becoming an accidental identity-only cue.  Those witness colors occupy
non-modal template labels so modal-background collapses remain rejectable.
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7a37505e7bd0"
TASK_ID = "7a37505e7bd0"
VERSION = "3.2.0"
RULE_HASH = "f6f5abe21d6a"
ALLOW_IDENTITY_OUTPUT = True
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Generate a canonical-profile 3x3 grid containing exactly n distinct ARC "
    "colors, where n cycles through 1, 2, 3, 4, 5 in every five consecutive "
    "samples. Count ALL distinct colors, including zero. If n=1, return the "
    "input unchanged. Otherwise upscale the grid by n in both dimensions: "
    "each input cell becomes an n-by-n block of the same color. Scheduled "
    "zero-containing examples refute the incorrect nonzero-color-count rule, "
    "and two multicolor 3/8 witnesses per lesson refute an identity-color shortcut."
)

INVARIANTS = [
    "every generated input is exactly 3x3, matching every canonical input",
    "the input contains exactly 1..5 distinct colors",
    "zero is a counted color whenever it is present",
    "each five-sample window contains color counts 1, 2, 3, 4, and 5",
    "one-color examples are nonzero monochrome identity cases",
    "each five-sample window has exactly two multicolor examples containing 3 or 8",
    "the multicolor 3/8 witness pair rotates across color counts 3..5 by seed",
    "a multicolor 3/8 witness is never the modal background color",
    "multi-color examples use at least two distinct rows and columns",
    "the authoritative output is 3n by 3n and repeats each cell in an n-by-n block",
]

# One exact semantic axis.  Shape is deliberately fixed at the canonical 3x3
# profile; palette and layout are nuisance variation, not claimed exact axes.
AXES = {
    "color_count": {
        "type": "int",
        "default": "scheduled 1..5 by sample_index",
        "valid": "1..5",
    },
}

# These profiles include every canonical input while excluding low-information
# impostors such as 8+1 two-color grids.  Profiles are sorted frequencies.
_MIN_COLOR_FREQUENCY = {1: 9, 2: 3, 3: 2, 4: 2, 5: 1}
_MAX_COLOR_FREQUENCY = {1: 9, 2: 6, 3: 5, 4: 3, 5: 2}

# Cell labels before palette substitution.  Their frequency profiles are:
# n=1 [9], n=2 [4,5], n=3 [2,3,4], n=4 [2,2,2,3], n=5 [1,2,2,2,2].
_TEMPLATES: dict[int, tuple[int, ...]] = {
    1: (0, 0, 0, 0, 0, 0, 0, 0, 0),
    2: (0, 0, 1, 1, 1, 1, 0, 1, 0),
    3: (0, 0, 1, 0, 2, 1, 0, 2, 1),
    4: (0, 0, 1, 0, 2, 1, 3, 2, 3),
    5: (0, 0, 1, 2, 3, 1, 4, 2, 3),
}

# Reserve the canonical identity-color witness for a non-modal label in every
# multicolor template.  This matters because defect-lint replaces a scene with
# its modal background: if 3/8 were modal, that mutation would collapse to a
# lawful canonical identity input and self_check could not reject it.
_IDENTITY_WITNESS_LABEL = {3: 2, 4: 1, 5: 4}


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_color_count(seed: int, sample_index: int) -> int:
    # The seed-dependent phase keeps seed-only probes diverse while every five
    # consecutive sample indices still contain all five counts exactly once.
    return (sample_index + seed) % 5 + 1


def _include_zero(color_count: int) -> bool:
    # Counts two and four always include zero. Every complete five-demo lesson
    # therefore contains two direct nonzero-count shortcut counterexamples.
    return color_count in {2, 4}


def _identity_palette_witness_counts(seed: int) -> set[int]:
    # Every lesson contains all counts 1..5. Two witnesses guarantee that any
    # one-pair query rotation still leaves a counterexample to the identity-color
    # shortcut. Counts 3..5 admit a second, lower-valued non-modal foreground,
    # which keeps the generic monochrome-collapse probes genuinely invalid.
    pairs = ((3, 4), (4, 5), (3, 5))
    return set(pairs[seed % len(pairs)])


def _draw_palette(
    ctx, *, n: int, include_zero: bool, include_identity_color: bool
) -> list[int]:
    if n == 1:
        # The two public identity examples use 3 and 8. Keeping the generated
        # identity branch on those colors lets self_check reject arbitrary
        # monochrome collapses without rejecting any canonical input.
        return [ctx.draw_choice("identity_color", (3, 8))]

    if not include_identity_color:
        palette: list[int] = [0] if include_zero else []
        remaining = n - len(palette)
        if remaining:
            palette.extend(
                ctx.draw_distinct_colors(
                    "palette_other", n=remaining, exclude={0, 3, 8}
                )
            )
        ctx.draw_rng("palette_order").shuffle(palette)
        return palette

    witness_color = ctx.draw_choice("multicolor_identity_color", (3, 8))
    witness_label = _IDENTITY_WITNESS_LABEL[n]

    if n == 3:
        # Label frequencies are 4,3,2. Keep a low-valued color on the second
        # non-modal label so defect-lint's foreground collapse is not 3/8.
        low_color = ctx.draw_choice("witness_low_color", (1, 2))
        modal_color = ctx.draw_distinct_colors(
            "palette_other", n=1, exclude={0, 3, 8, low_color}
        )[0]
        return [modal_color, low_color, witness_color]

    if n == 4:
        # Label frequencies are 3,2,2,2. Put zero on a non-modal label so it is
        # the linter's smallest foreground, while 3/8 remains another witness.
        other = list(
            ctx.draw_distinct_colors(
                "palette_other", n=2, exclude={0, 3, 8}
            )
        )
        ctx.draw_rng("palette_order").shuffle(other)
        return [other[0], witness_color, 0, other[1]]

    if n == 5:
        # Four labels tie at frequency two and the witness occurs once. Two low
        # colors guarantee that one remains a non-modal foreground regardless
        # of which tied label Counter selects as the modal color.
        other = [1, 2]
        other.extend(
            ctx.draw_distinct_colors(
                "palette_other", n=2, exclude={0, 1, 2, 3, 8}
            )
        )
        ctx.draw_rng("palette_order").shuffle(other)
        return [*other, witness_color]

    raise RuntimeError(f"identity-color witness unsupported for n={n}")


def _rotate(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid: list[list[int]], variant: int) -> list[list[int]]:
    out = copy.deepcopy(grid)
    if variant >= 4:
        out = [row[::-1] for row in out]
    for _ in range(variant % 4):
        out = _rotate(out)
    return out


def _has_row_col_variation(grid: list[list[int]]) -> bool:
    rows = {tuple(row) for row in grid}
    cols = {tuple(grid[r][c] for r in range(3)) for c in range(3)}
    return len(rows) >= 2 and len(cols) >= 2


def _layout_for_band(
    labels: tuple[int, ...], *, difficulty: str, rng
) -> list[list[int]]:
    cells = list(labels)
    if difficulty == "hard" and len(set(cells)) > 1:
        # Hard examples randomize cell positions while preserving the exact
        # color-frequency profile. Retry only to retain row/column variation.
        for _ in range(32):
            rng.shuffle(cells)
            candidate = [cells[i : i + 3] for i in range(0, 9, 3)]
            if _has_row_col_variation(candidate) and not _is_solid_2x2_partition(candidate):
                return candidate
        raise RuntimeError("failed to realize a varied 3x3 hard layout")

    base = [cells[i : i + 3] for i in range(0, 9, 3)]
    variant = rng.randrange(4 if difficulty == "easy" else 8)
    return _transform(base, variant)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic canonical-profile input grid."""
    _validate_override_keys(overrides)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if "color_count" in overrides and overrides["color_count"] is not None:
        n = ctx.draw_int("color_count", 1, 5)
    else:
        scheduled = _scheduled_color_count(seed, sample_index)
        n = ctx.draw_int("color_count", scheduled, scheduled)

    palette = _draw_palette(
        ctx,
        n=n,
        include_zero=_include_zero(n),
        include_identity_color=(
            n > 1 and n in _identity_palette_witness_counts(seed)
        ),
    )
    labels = _TEMPLATES[n]
    layout = _layout_for_band(labels, difficulty=band, rng=ctx.draw_rng(f"layout_{band}"))
    grid = [[palette[label] for label in row] for row in layout]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _colors(grid: list[list[int]]) -> set[int]:
    return {value for row in grid for value in row}




def _is_solid_2x2_partition(grid: list[list[int]]) -> bool:
    colors = _colors(grid)
    if len(colors) != 2 or _grid_shape(grid) != (3, 3):
        return False
    for color in colors:
        cells = {(r, c) for r in range(3) for c in range(3) if grid[r][c] == color}
        for top in (0, 1):
            for left in (0, 1):
                block = {(r, c) for r in range(top, top + 2) for c in range(left, left + 2)}
                if cells == block:
                    return True
    return False


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    shape = _grid_shape(grid)
    if shape is None:
        return {"color_count": -1}
    return {"color_count": len(_colors(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject inputs outside the canonical-profile teaching distribution."""
    del difficulty, meta
    errors: list[str] = []
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of rows"]
    h, w = shape
    if (h, w) != (3, 3):
        errors.append(f"teaching inputs must be canonical-profile 3x3, got {h}x{w}")

    bad_values = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    counts = Counter(value for row in grid for value in row)
    n = len(counts)
    if not 1 <= n <= 5:
        errors.append(f"expected 1..5 distinct colors, got {n}")
        return errors

    if n == 1 and next(iter(counts)) not in {3, 8}:
        errors.append("the one-color identity branch must use canonical color 3 or 8")

    minimum = min(counts.values())
    maximum = max(counts.values())
    if minimum < _MIN_COLOR_FREQUENCY[n]:
        errors.append(
            f"color frequency {minimum} is below the n={n} teaching floor "
            f"{_MIN_COLOR_FREQUENCY[n]}"
        )
    if maximum > _MAX_COLOR_FREQUENCY[n]:
        errors.append(
            f"color frequency {maximum} exceeds the n={n} teaching ceiling "
            f"{_MAX_COLOR_FREQUENCY[n]}"
        )

    if n > 1 and shape == (3, 3) and not _has_row_col_variation(grid):
        errors.append("multi-color inputs must vary across both rows and columns")
    if n == 2 and _is_solid_2x2_partition(grid) and set(counts) != {3, 6}:
        errors.append(
            "solid 2x2 two-color collapse is outside the teaching distribution; "
            "the canonical {3,6} instance is the explicit lawful exception"
        )
    return errors



def mutation_fixtures():
    """Task-linked must-reject teaching-distribution impostors."""
    return [
        ("all_zero_identity", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        ("arbitrary_monochrome", [[5, 5, 5], [5, 5, 5], [5, 5, 5]]),
        ("solid_two_by_two_collapse", [[1, 1, 2], [1, 1, 2], [2, 2, 2]]),
        ("singleton_color_leak", [[1, 1, 1], [1, 2, 1], [1, 1, 1]]),
    ]

def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for tests and semantic rival analysis."""
    n = len(_colors(grid))
    if n <= 1:
        return copy.deepcopy(grid)
    return [
        [grid[r // n][c // n] for c in range(len(grid[0]) * n)]
        for r in range(len(grid) * n)
    ]


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    counts = Counter(value for row in grid for value in row)
    n = len(counts)
    return {
        "errors": [],
        "color_count": n,
        "includes_zero": 0 in counts,
        "identity_palette_in_multicolor": (
            n > 1 and bool(set(counts) & {3, 8})
        ),
        "frequency_profile": sorted(counts.values()),
        "modal_frequency": max(counts.values()),
        "identity_branch": n == 1,
        "output_shape": [3 * n, 3 * n] if n > 1 else [3, 3],
    }


def strict_canonical_like(grid) -> list[str]:
    """All emitted scenes stay inside the public task's 3x3 grammar."""
    return self_check(grid)


def _upscale_with_factor(grid: list[list[int]], factor: int) -> list[list[int]]:
    if factor <= 1:
        return copy.deepcopy(grid)
    return [
        [grid[r // factor][c // factor] for c in range(len(grid[0]) * factor)]
        for r in range(len(grid) * factor)
    ]


def _rival_nonzero_color_count(grid):
    factor = len({value for row in grid for value in row if value != 0})
    return _upscale_with_factor(grid, factor)


def _rival_fixed_three(grid):
    return grid if len(_colors(grid)) == 1 else _upscale_with_factor(grid, 3)


def _rival_modal_frequency(grid):
    counts = Counter(value for row in grid for value in row)
    return _upscale_with_factor(grid, max(counts.values()))


def _rival_number_of_nonzero_cells_mod_five(grid):
    nonzero = sum(value != 0 for row in grid for value in row)
    factor = nonzero % 5 or 5
    return _upscale_with_factor(grid, factor)


def _rival_identity_color_means_identity(grid):
    # Wrong but tempting under the old palette distribution: colors 3 and 8
    # appeared only in monochrome identity examples.
    if _colors(grid) & {3, 8}:
        return copy.deepcopy(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "count_nonzero_colors": _rival_nonzero_color_count,
    "fixed_three_for_multicolor": _rival_fixed_three,
    "scale_by_modal_frequency": _rival_modal_frequency,
    "scale_by_nonzero_cell_count_mod_five": _rival_number_of_nonzero_cells_mod_five,
    "identity_color_means_identity": _rival_identity_color_means_identity,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Public examples never contain zero, so this rival is answer-equivalent on
    # canonical data and must be killed by generated zero-containing lessons.
    "count_nonzero_colors": _rival_nonzero_color_count,
}


def _witness_count(expected: int):
    return lambda grid: len(_colors(grid)) == expected


SEMANTIC_WITNESSES = {
    "identity_one_color": _witness_count(1),
    "scale_two": _witness_count(2),
    "scale_three": _witness_count(3),
    "scale_four": _witness_count(4),
    "scale_five": _witness_count(5),
    "zero_is_a_counted_color": lambda grid: 0 in _colors(grid) and len(_colors(grid)) > 1,
    "nonzero_only_multicolor": lambda grid: 0 not in _colors(grid) and len(_colors(grid)) > 1,
    "identity_palette_in_multicolor": lambda grid: (
        len(_colors(grid)) > 1 and bool(_colors(grid) & {3, 8})
    ),
    "modal_frequency_differs_from_scale": lambda grid: (
        len(_colors(grid)) > 1
        and max(Counter(value for row in grid for value in row).values())
        != len(_colors(grid))
    ),
}
WITNESS_RIVALS = {
    "identity_one_color": ["fixed_three_for_multicolor", "scale_by_modal_frequency"],
    "scale_two": ["fixed_three_for_multicolor"],
    "scale_three": ["scale_by_modal_frequency"],
    "scale_four": ["fixed_three_for_multicolor"],
    "scale_five": ["fixed_three_for_multicolor"],
    "zero_is_a_counted_color": ["count_nonzero_colors"],
    "nonzero_only_multicolor": ["scale_by_modal_frequency"],
    "identity_palette_in_multicolor": ["identity_color_means_identity"],
    "modal_frequency_differs_from_scale": ["scale_by_modal_frequency"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to identify the true scale-factor rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    zero_multicolor = False
    identity_palette_multicolor = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} disagrees with distinct-color upscaling")
        colors = _colors(pair["input"])
        zero_multicolor |= 0 in colors and len(colors) > 1
        identity_palette_multicolor |= (
            len(colors) > 1 and bool(colors & {3, 8})
        )

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is unlawful: " + "; ".join(query_errors))
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query disagrees with distinct-color upscaling")

    if not zero_multicolor:
        reasons.append("demonstrations need a multicolor input containing zero")
    if not identity_palette_multicolor:
        reasons.append(
            "demonstrations need a multicolor input containing identity color 3 or 8"
        )
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
