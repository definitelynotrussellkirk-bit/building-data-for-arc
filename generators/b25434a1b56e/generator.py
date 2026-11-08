"""Generator for b25434a1b56e — summarize quadrant modes.

Split an even rectangular input into four equal quadrants.  The canonical
Racket rule writes the most frequent non-zero color from each quadrant into a
2x2 output; an empty quadrant contributes 0.  Generated scenes deliberately
include competing colors so a lesson cannot be solved by merely copying the
first, only, or numerically largest foreground color.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b25434a1b56e"
TASK_ID = "b25434a1b56e"
VERSION = "3.0.0"
RULE_HASH = "d994ac093631"

SUMMARY = (
    "Split an even grid into top-left, top-right, bottom-left, and "
    "bottom-right quadrants. For each quadrant output its most frequent "
    "non-zero color, or 0 when the quadrant is empty. Ordinary lessons mix "
    "single-color, empty, and multi-color quadrants, including count winners "
    "that are neither the first nor the numerically largest visible color."
)

INVARIANTS = [
    "the input height and width are even and each lies in {6, 8, 10, 12}",
    "zero is background and exactly four non-zero colors occur globally",
    "each non-empty quadrant has one unique most-frequent non-zero color",
    "ordinary draws contain at least one multi-color quadrant that refutes first/highest-color shortcuts",
    "sample-index scheduling alternates one-empty and all-nonempty scenes",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_GRID_DIMS = (6, 8, 10, 12)
_BANDS = ("easy", "medium", "hard")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled even dimension with frequent canonical 6x6 anchors",
        "valid": "6|8|10|12",
        "doc": "Full returned-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled even dimension with frequent canonical 6x6 anchors",
        "valid": "6|8|10|12",
        "doc": "Full returned-grid width.",
    },
}


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _band_name(difficulty: Any) -> str:
    return difficulty if difficulty in _BANDS else "medium"


def _scheduled_dimensions(sample_index: int, band: str) -> tuple[int, int]:
    """Keep canonical 6x6 support in every band while varying larger scales."""
    index = int(sample_index)
    if index % 4 in (0, 1):
        return 6, 6
    larger = {
        "easy": ((8, 8), (8, 6)),
        "medium": ((8, 10), (10, 8)),
        "hard": ((10, 12), (12, 10)),
    }[band]
    return larger[(index // 2) % len(larger)]


def _draw_scheduled_dimension(ctx, label: str, scheduled: int) -> int:
    # Explicit overrides are checked against the complete lawful domain.  The
    # default path records the exact scheduled value as a keyed draw so the
    # override checker can compare provenance with the returned dimensions.
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, _GRID_DIMS)
    return ctx.draw_choice(label, (scheduled,))


def _quadrant_bounds(h: int, w: int) -> tuple[tuple[int, int, int, int], ...]:
    half_h, half_w = h // 2, w // 2
    return (
        (0, 0, half_h, half_w),
        (0, half_w, half_h, w),
        (half_h, 0, h, half_w),
        (half_h, half_w, h, w),
    )


def _quadrant_values(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    h, w = len(grid), len(grid[0])
    return tuple(
        tuple(grid[r][c] for r in range(r1, r2) for c in range(c1, c2))
        for r1, c1, r2, c2 in _quadrant_bounds(h, w)
    )


def _mode_nonzero(values: tuple[int, ...] | list[int]) -> int:
    """Exact Python mirror of the selected Racket reducer, including ties."""
    counts = Counter(value for value in values if value != 0)
    if not counts:
        return 0
    return max(counts, key=lambda color: (counts[color], color))


def _strict_mode(values: tuple[int, ...] | list[int]) -> tuple[int, bool]:
    counts = Counter(value for value in values if value != 0)
    if not counts:
        return 0, True
    top = max(counts.values())
    winners = [color for color, count in counts.items() if count == top]
    return max(winners), len(winners) == 1


def _major_and_minor_counts(area: int, band: str) -> tuple[int, int, int]:
    """Return a strict mode plus two visible competitors, leaving some zero."""
    if band == "easy":
        major = max(3, area // 3)
    elif band == "hard":
        major = max(4, (3 * area) // 5)
    else:
        major = max(4, area // 2)

    # Preserve at least one background cell and strict count dominance.
    major = min(major, area - 3)
    minor_a = max(1, min(major - 1, area // 5))
    minor_b = max(1, min(major - 1, area // 7))
    while major + minor_a + minor_b >= area:
        if minor_a > 1:
            minor_a -= 1
        elif major > 3:
            major -= 1
        else:
            break
    return major, minor_a, minor_b


def _paint_quadrant(
    grid: list[list[int]],
    bounds: tuple[int, int, int, int],
    *,
    major: int,
    minorities: tuple[int, int],
    band: str,
    rng,
    single_color: bool,
    discriminator: bool,
) -> None:
    r1, c1, r2, c2 = bounds
    cells = [(r, c) for r in range(r1, r2) for c in range(c1, c2)]
    area = len(cells)

    if single_color:
        count = min(area - 1, max(3, area // 3))
        chosen = list(cells)
        rng.shuffle(chosen)
        for r, c in chosen[:count]:
            grid[r][c] = major
        return

    major_count, minor_a_count, minor_b_count = _major_and_minor_counts(area, band)
    first_minor, second_minor = minorities

    if discriminator:
        # The first row-major non-zero cell is a HIGHER-valued minority.  The
        # actual answer is the lower-valued color because it occurs more often,
        # simultaneously killing first-nonzero and highest-color shortcuts.
        first_cell = (r1, c1)
        grid[first_cell[0]][first_cell[1]] = first_minor
        remaining = [cell for cell in cells if cell != first_cell]
        rng.shuffle(remaining)
        cursor = 0
        for r, c in remaining[cursor:cursor + major_count]:
            grid[r][c] = major
        cursor += major_count
        for r, c in remaining[cursor:cursor + max(0, minor_a_count - 1)]:
            grid[r][c] = first_minor
        cursor += max(0, minor_a_count - 1)
        for r, c in remaining[cursor:cursor + minor_b_count]:
            grid[r][c] = second_minor
        return

    shuffled = list(cells)
    rng.shuffle(shuffled)
    cursor = 0
    for r, c in shuffled[cursor:cursor + major_count]:
        grid[r][c] = major
    cursor += major_count
    for r, c in shuffled[cursor:cursor + minor_a_count]:
        grid[r][c] = first_minor
    cursor += minor_a_count
    for r, c in shuffled[cursor:cursor + minor_b_count]:
        grid[r][c] = second_minor


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    band = _band_name(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _scheduled_dimensions(sample_index, band)
    h = _draw_scheduled_dimension(ctx, "grid_h", scheduled_h)
    w = _draw_scheduled_dimension(ctx, "grid_w", scheduled_w)
    grid = full_grid(h, w, 0)

    palette = tuple(sorted(ctx.draw_distinct_colors(
        "foreground_colors", n=4, exclude={0}
    )))
    low, mid_a, mid_b, high = palette
    bounds = _quadrant_bounds(h, w)

    # Every three consecutive sample indexes contain both branches, which is
    # the lesson window used by EXAMPLES_NEEDED=3.
    empty_index = int(sample_index) % 4 if int(sample_index) % 2 == 0 else None
    nonempty = [index for index in range(4) if index != empty_index]
    discriminator_index = nonempty[int(sample_index) % len(nonempty)]

    singleton_index = None
    if int(sample_index) % 3 == 0:
        candidates = [index for index in nonempty if index != discriminator_index]
        singleton_index = candidates[(int(sample_index) // 3) % len(candidates)]

    # Rotate which quadrant gets which answer.  Every grid has at least two
    # distinct answers; every fifth grid repeats one answer to prevent an
    # accidental "four distinct quadrant colors" lesson.
    other_indices = [index for index in nonempty if index != discriminator_index]
    other_majors = [mid_a, mid_b, high]
    ctx.draw_rng("major_order").shuffle(other_majors)
    major_by_index = {discriminator_index: low}
    for index, major in zip(other_indices, other_majors):
        major_by_index[index] = major
    if empty_index is None and int(sample_index) % 5 == 0 and len(other_indices) >= 2:
        major_by_index[other_indices[-1]] = major_by_index[other_indices[0]]

    missing_from_majors = [color for color in palette if color not in major_by_index.values()]
    discriminator_minors = [high]
    discriminator_minors.extend(
        color for color in missing_from_majors
        if color != high and color != low
    )
    discriminator_minors.extend(color for color in (mid_a, mid_b) if color not in discriminator_minors)
    discriminator_minors = discriminator_minors[:2]

    for index in nonempty:
        major = major_by_index[index]
        if index == discriminator_index:
            minorities = (discriminator_minors[0], discriminator_minors[1])
        else:
            pool = [color for color in palette if color != major]
            rng = ctx.draw_rng(f"minority_order_{index}")
            rng.shuffle(pool)
            minorities = (pool[0], pool[1])
        _paint_quadrant(
            grid,
            bounds[index],
            major=major,
            minorities=minorities,
            band=band,
            rng=ctx.draw_rng(f"quadrant_layout_{index}"),
            single_color=index == singleton_index,
            discriminator=index == discriminator_index,
        )

    facts = _analyze(grid)
    if facts["errors"]:
        raise AssertionError("generated invalid quadrant-mode scene: " + "; ".join(facts["errors"]))
    strict_errors = strict_canonical_like(grid)
    if strict_errors:
        raise AssertionError("generated non-canonical-like scene: " + "; ".join(strict_errors))
    if set(value for row in grid for value in row if value != 0) != set(palette):
        raise AssertionError("generated scene failed to expose all four foreground colors")
    if not _witness_majority_not_highest(grid) or not _witness_minority_first(grid):
        raise AssertionError("generated scene failed to refute first/highest-color shortcuts")
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a non-empty list")
        return facts
    if not all(isinstance(row, list) for row in grid):
        errors.append("grid rows must be lists")
        return facts
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        errors.append("grid must be non-empty and rectangular")
        return facts
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integer values in 0..9")
        return facts

    height = len(grid)
    facts["height"] = height
    facts["width"] = width
    if height % 2 or width % 2:
        errors.append(f"grid dimensions must be even, got {height}x{width}")
        return facts

    quadrant_facts: list[dict[str, Any]] = []
    for index, values in enumerate(_quadrant_values(grid)):
        counts = Counter(value for value in values if value != 0)
        mode, unique = _strict_mode(values)
        if counts and not unique:
            top = max(counts.values())
            tied = sorted(color for color, count in counts.items() if count == top)
            errors.append(f"quadrant {index} has tied top colors {tied} at count {top}")
        quadrant_facts.append({
            "values": values,
            "counts": counts,
            "colors": tuple(sorted(counts)),
            "mode": mode,
            "unique_mode": unique,
            "nonzero_count": sum(counts.values()),
            "first_nonzero": next((value for value in values if value != 0), 0),
            "highest_nonzero": max(counts, default=0),
        })

    facts["quadrants"] = quadrant_facts
    facts["modes"] = tuple(q["mode"] for q in quadrant_facts)
    facts["empty_count"] = sum(not q["counts"] for q in quadrant_facts)
    facts["foreground_colors"] = tuple(sorted({
        value for row in grid for value in row if value != 0
    }))
    facts["palette_size"] = len(set(value for row in grid for value in row))
    return facts


def _teaching_grammar_errors(facts: dict[str, Any]) -> list[str]:
    """Reject rule-hiding scenes while preserving every canonical input."""
    if facts["errors"]:
        return list(facts["errors"])
    errors: list[str] = []
    if facts["height"] not in _GRID_DIMS or facts["width"] not in _GRID_DIMS:
        errors.append(
            f"dimensions {facts['height']}x{facts['width']} outside {_GRID_DIMS}"
        )
    n_foreground = len(facts["foreground_colors"])
    if not 3 <= n_foreground <= 4:
        errors.append(
            "expected three or four foreground colors, found "
            f"{n_foreground}"
        )
    nonempty = 0
    for index, quadrant in enumerate(facts["quadrants"]):
        if not quadrant["counts"]:
            continue
        nonempty += 1
        if quadrant["nonzero_count"] < 3:
            errors.append(f"quadrant {index} has fewer than three non-zero cells")
    if nonempty < 3:
        errors.append(f"expected at least three non-empty quadrants, found {nonempty}")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical teaching grammar, including one empty quadrant."""
    return _teaching_grammar_errors(_analyze(grid))


def strict_canonical_like(grid) -> list[str]:
    """Task-linked manifold: canonical scale and unique quadrant modes."""
    return _teaching_grammar_errors(_analyze(grid))


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python test mirror; the Racket program remains output authority."""
    facts = _analyze(grid)
    # The selected Racket rule can execute ties, but ordinary teaching grammar
    # excludes them.  For hidden boundary probes, still mirror the exact Racket
    # high-color tie break directly from the raw quadrant values.
    values = _quadrant_values(grid)
    modes = [_mode_nonzero(quadrant) for quadrant in values]
    return [modes[:2], modes[2:]]


def semantic_signature(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "height": facts["height"],
        "width": facts["width"],
        "palette_size": facts["palette_size"],
        "foreground_colors": facts["foreground_colors"],
        "modes": facts["modes"],
        "empty_quadrants": facts["empty_count"],
        "multicolor_quadrants": sum(len(q["colors"]) >= 2 for q in facts["quadrants"]),
        "single_color_quadrants": sum(len(q["colors"]) == 1 for q in facts["quadrants"]),
        "majority_not_highest": _witness_majority_not_highest(grid),
        "minority_first": _witness_minority_first(grid),
    }


def _map_quadrants(grid, reducer: Callable[[tuple[int, ...]], int]) -> list[list[int]]:
    answers = [reducer(values) for values in _quadrant_values(grid)]
    return [answers[:2], answers[2:]]


def _rival_first_nonzero(grid) -> list[list[int]]:
    return _map_quadrants(grid, lambda values: next((value for value in values if value), 0))


def _rival_highest_nonzero(grid) -> list[list[int]]:
    return _map_quadrants(grid, lambda values: max((value for value in values if value), default=0))


def _global_mode(grid) -> int:
    return _mode_nonzero(tuple(value for row in grid for value in row))


def _rival_global_mode_broadcast(grid) -> list[list[int]]:
    color = _global_mode(grid)
    return [[color, color], [color, color]]


def _rival_fill_empty_with_global_mode(grid) -> list[list[int]]:
    global_color = _global_mode(grid)
    answers = []
    for values in _quadrant_values(grid):
        local = _mode_nonzero(values)
        answers.append(local if local != 0 else global_color)
    return [answers[:2], answers[2:]]


def _facts_or_none(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _witness_empty_quadrant(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and facts["empty_count"] > 0)


def _witness_all_quadrants_nonempty(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and facts["empty_count"] == 0)


def _witness_single_color_quadrant(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and any(len(q["colors"]) == 1 for q in facts["quadrants"]))


def _witness_competing_colors(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and any(len(q["colors"]) >= 2 for q in facts["quadrants"]))


def _witness_majority_not_highest(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and any(
        q["counts"] and q["mode"] != q["highest_nonzero"]
        for q in facts["quadrants"]
    ))


def _witness_minority_first(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(facts and any(
        q["counts"] and q["mode"] != q["first_nonzero"]
        for q in facts["quadrants"]
    ))


def _witness_multiple_quadrant_modes(grid) -> bool:
    facts = _facts_or_none(grid)
    if not facts:
        return False
    nonzero_modes = {mode for mode in facts["modes"] if mode != 0}
    return len(nonzero_modes) >= 2


def _witness_canonical_profile(grid) -> bool:
    facts = _facts_or_none(grid)
    return bool(
        facts
        and facts["height"] == 6
        and facts["width"] == 6
        and facts["palette_size"] == 5
    )


SEMANTIC_WITNESSES = {
    "empty_quadrant_to_zero": _witness_empty_quadrant,
    "all_quadrants_nonempty": _witness_all_quadrants_nonempty,
    "single_color_quadrant": _witness_single_color_quadrant,
    "competing_colors_in_quadrant": _witness_competing_colors,
    "majority_not_highest_color": _witness_majority_not_highest,
    "minority_appears_first": _witness_minority_first,
    "multiple_quadrant_modes": _witness_multiple_quadrant_modes,
    "canonical_6x6_palette5_anchor": _witness_canonical_profile,
}

SEMANTIC_RIVALS = {
    "first_nonzero": _rival_first_nonzero,
    "highest_nonzero": _rival_highest_nonzero,
    "global_mode_broadcast": _rival_global_mode_broadcast,
    "fill_empty_with_global_mode": _rival_fill_empty_with_global_mode,
}

WITNESS_RIVALS = {
    "empty_quadrant_to_zero": ["fill_empty_with_global_mode"],
    "all_quadrants_nonempty": ["highest_nonzero"],
    "single_color_quadrant": ["highest_nonzero"],
    "competing_colors_in_quadrant": ["highest_nonzero"],
    "majority_not_highest_color": ["highest_nonzero"],
    "minority_appears_first": ["first_nonzero"],
    "multiple_quadrant_modes": ["global_mode_broadcast"],
    "canonical_6x6_palette5_anchor": ["highest_nonzero"],
}

# Both shortcuts fit every public pair because each public non-empty quadrant
# contains only one color.  Generated count-discriminator scenes are therefore
# the only available proof that these are wrong rules.
CANONICAL_SHORTCUTS = {
    "first_nonzero": _rival_first_nonzero,
    "highest_nonzero": _rival_highest_nonzero,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible shortcut to be refuted by demonstrations."""
    errors: list[str] = []
    for label, pair in [
        *( (f"demo {index}", pair) for index, pair in enumerate(demos) ),
        ("query", query),
    ]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"{label} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.extend(f"{label}: {reason}" for reason in structural)
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            errors.append(f"{label} output does not match quadrant-mode rule")
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives every demonstration")
    return errors
