"""Semantic generator for ARC task ``2078c29581a4``.

The authoritative rule deletes every all-zero row and preserves every remaining
row exactly, including its width, cell positions, colors, and top-to-bottom
order.  The four-sample schedule deliberately alternates canonical-looking odd
rows with adjacent rows, multi-row gaps, and occupied edge rows.  Any four
consecutive demonstrations therefore refute the canonical-compatible shortcuts
"keep odd-indexed rows", "always return three rows", "sort rows by density",
and "assume every kept row is monochrome".
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2078c29581a4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ed6dfa957511"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 5..16 by 4..16 zero-background grid has 2..4 distinct, sparse nonempty "
    "rows and at least one all-zero row. Delete every all-zero row. Preserve "
    "the remaining rows exactly and in their original top-to-bottom order; "
    "the output width is unchanged and its height is the number of nonempty rows."
)

INVARIANTS = [
    "background is 0",
    "there are 2..4 distinct nonempty rows and at least one all-zero row",
    "every nonempty row is sparse and the scene uses at least two foreground colors",
    "ordinary four-example windows include odd-row, adjacent-row, multi-gap, and edge-row layouts",
    "the output consists of the nonempty input rows unchanged and in original order",
]

COUNTER_HYPOTHESES = [
    "keep only odd-indexed rows (fits every canonical pair)",
    "return only the first three nonempty rows (fits every canonical pair)",
    "sort nonempty rows by nonzero-cell count (fits every canonical pair)",
    "replace each kept row by a monochrome version using its first foreground color",
    "crop the nonzero bounding box or compress cells horizontally",
    "memorize canonical heights, widths, colors, or output height three",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 6/7 every fourth sample; otherwise difficulty-aware 5..16",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 6/7/8 every fourth sample; otherwise difficulty-aware 4..16",
        "valid": "4..16",
    },
    "n_nonempty_rows": {
        "type": "int",
        "default": "profile schedule uses 2, 3, or 4 rows",
        "valid": "2..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "canonical_odd_rows",
    "adjacent_rows",
    "multi_row_gap",
    "occupied_edges",
)

_BANDS = ("easy", "medium", "hard")
_GLOBAL_BOUNDS = {
    "grid_h": (5, 16),
    "grid_w": (4, 16),
    "n_nonempty_rows": (2, 4),
}
_CANONICAL_DIMS = ((6, 6), (7, 7), (6, 8))


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BANDS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        lo, hi = _GLOBAL_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive sample indexes cover all decisive layouts."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, name: str, choices: list[int], overrides: dict[str, Any]) -> int:
    lo, hi = _GLOBAL_BOUNDS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, choices)


def _default_dimensions(profile: str, band: str) -> tuple[list[int], list[int]]:
    if profile == "canonical_odd_rows":
        return [h for h, _ in _CANONICAL_DIMS], [w for _, w in _CANONICAL_DIMS]
    heights = {
        "easy": list(range(6, 9)),
        "medium": list(range(8, 13)),
        "hard": list(range(11, 17)),
    }[band]
    widths = {
        "easy": list(range(4, 9)),
        "medium": list(range(6, 13)),
        "hard": list(range(9, 17)),
    }[band]
    if profile == "multi_row_gap":
        heights = [h for h in heights if h >= 7]
    return heights, widths


def _default_row_count(profile: str) -> int:
    return {
        "canonical_odd_rows": 3,
        "adjacent_rows": 3,
        "multi_row_gap": 2,
        "occupied_edges": 4,
    }[profile]


def _choose_positions(profile: str, h: int, n: int, rng) -> list[int]:
    """Choose exact row locations, falling back lawfully for tight overrides."""
    if profile == "canonical_odd_rows" and h >= 6 and n == 3:
        return [1, 3, 5]

    if profile == "adjacent_rows" and h >= n + 1:
        run = min(2, n)
        start = rng.randint(0, max(0, h - n - 1))
        positions = list(range(start, start + run))
        available = [r for r in range(h) if r not in positions]
        while len(positions) < n:
            candidates = [r for r in available if r not in positions]
            positions.append(rng.choice(candidates))
        positions = sorted(set(positions))
        if len(positions) == n and any(b == a + 1 for a, b in zip(positions, positions[1:])):
            return positions

    if profile == "multi_row_gap" and h >= n + 2:
        if n == 2:
            left = rng.randint(0, h - 4)
            return [left, rng.randint(left + 3, h - 1)]
        positions = [0, 3]
        candidates = [r for r in range(4, h) if r not in positions]
        while len(positions) < n:
            positions.append(rng.choice(candidates))
            candidates = [r for r in candidates if r not in positions]
        return sorted(positions)

    if profile == "occupied_edges" and n >= 2:
        positions = [0, h - 1]
        available = list(range(1, h - 1))
        while len(positions) < n:
            positions.append(rng.choice(available))
            available = [r for r in available if r not in positions]
        return sorted(positions)

    # Every declared override combination is legal: choose any n rows while
    # reserving at least one all-zero row. This fallback is used only when an
    # exact dimension/count override cannot realize the scheduled relation.
    return sorted(rng.sample(range(h), n))


def _row_counts(profile: str, n: int, width: int) -> list[int]:
    patterns = {
        "canonical_odd_rows": [1, 2, 3, 2],
        "adjacent_rows": [3, 1, 2, 3],
        "multi_row_gap": [2, 1, 3, 2],
        "occupied_edges": [2, 1, 3, 2],
    }[profile]
    # Every kept row must retain at least one zero, so cap at width - 1.
    return [max(1, min(patterns[i], width - 1)) for i in range(n)]


def _paint_rows(grid, positions: list[int], profile: str, rng) -> None:
    width = len(grid[0])
    n = len(positions)
    palette = rng.sample(range(1, 10), min(4, max(2, n)))
    counts = _row_counts(profile, n, width)
    for index, (row_index, count) in enumerate(zip(positions, counts)):
        columns = sorted(rng.sample(range(width), count))
        primary = palette[index % len(palette)]
        secondary = palette[(index + 1) % len(palette)]
        multicolor = profile != "canonical_odd_rows" and index == 0 and count >= 2
        for offset, column in enumerate(columns):
            grid[row_index][column] = secondary if multicolor and offset == 1 else primary

    # Canonical-profile rows must use three distinct monochrome colors so the
    # generated (h, w, palette-size) exactly anchors the real task profiles.
    if profile == "canonical_odd_rows" and n == 3:
        for index, row_index in enumerate(positions):
            color = palette[index]
            for column, value in enumerate(grid[row_index]):
                if value != 0:
                    grid[row_index][column] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    if profile == "canonical_odd_rows" and not any(
        overrides.get(name) is not None for name in ("grid_h", "grid_w")
    ):
        h, w = _CANONICAL_DIMS[rng.randrange(len(_CANONICAL_DIMS))]
        h = ctx.draw_choice("grid_h", [h])
        w = ctx.draw_choice("grid_w", [w])
    else:
        height_choices, width_choices = _default_dimensions(profile, band)
        h = _draw_axis(ctx, "grid_h", height_choices, overrides)
        w = _draw_axis(ctx, "grid_w", width_choices, overrides)

    default_n = _default_row_count(profile)
    n = _draw_axis(ctx, "n_nonempty_rows", [default_n], overrides)
    if n >= h:
        # This cannot occur within declared bounds (h>=5, n<=4), retained as a
        # loud invariant guard against future metadata drift.
        raise ValueError(f"n_nonempty_rows={n} requires grid_h>{n}, got {h}")

    grid = full_grid(h, w, 0)
    positions = _choose_positions(profile, h, n, rng)
    _paint_rows(grid, positions, profile, rng)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced invalid scene: " + "; ".join(errors))
    return grid


def _analyse(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not 5 <= height <= 16:
        errors.append(f"grid_h must be 5..16, got {height}")
    if not 4 <= width <= 16:
        errors.append(f"grid_w must be 4..16, got {width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return {"errors": errors, "grid_h": height, "grid_w": width}

    nonempty_indices = [
        r for r, row in enumerate(grid) if any(value != 0 for value in row)
    ]
    empty_indices = [
        r for r, row in enumerate(grid) if all(value == 0 for value in row)
    ]
    kept_rows = [tuple(grid[r]) for r in nonempty_indices]
    fg_colors = sorted({value for row in grid for value in row if value != 0})
    nonzero_counts = [sum(value != 0 for value in row) for row in kept_rows]
    row_color_counts = [len({value for value in row if value != 0}) for row in kept_rows]

    if not 2 <= len(nonempty_indices) <= 4:
        errors.append(f"expected 2..4 nonempty rows, got {len(nonempty_indices)}")
    if not empty_indices:
        errors.append("expected at least one all-zero row")
    if len(fg_colors) < 2:
        errors.append(f"expected at least two foreground colors, got {len(fg_colors)}")
    if kept_rows and len(set(kept_rows)) != len(kept_rows):
        errors.append("nonempty rows must be distinct so order is observable")
    if kept_rows and any(count >= width for count in nonzero_counts):
        errors.append("every nonempty row must retain at least one background cell")
    if kept_rows and max(nonzero_counts, default=0) < 2:
        errors.append("at least one nonempty row must contain two or more cells")

    internal_gap_lengths: list[int] = []
    if nonempty_indices:
        run = 0
        occupied = set(nonempty_indices)
        for r in range(nonempty_indices[0] + 1, nonempty_indices[-1]):
            if r not in occupied:
                run += 1
            elif run:
                internal_gap_lengths.append(run)
                run = 0
        if run:
            internal_gap_lengths.append(run)

    facts = {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "n_nonempty_rows": len(nonempty_indices),
        "nonempty_indices": tuple(nonempty_indices),
        "empty_indices": tuple(empty_indices),
        "kept_rows": tuple(kept_rows),
        "fg_colors": tuple(fg_colors),
        "nonzero_counts": tuple(nonzero_counts),
        "row_color_counts": tuple(row_color_counts),
        "has_adjacent_nonempty": any(
            b == a + 1 for a, b in zip(nonempty_indices, nonempty_indices[1:])
        ),
        "has_multi_row_gap": any(length >= 2 for length in internal_gap_lengths),
        "has_occupied_edge": bool(nonempty_indices) and (
            nonempty_indices[0] == 0 or nonempty_indices[-1] == height - 1
        ),
        "has_multicolor_row": any(count >= 2 for count in row_color_counts),
        "density_nonmonotonic": any(
            left > right for left, right in zip(nonzero_counts, nonzero_counts[1:])
        ),
        "canonical_odd_profile": (
            (height, width, len(fg_colors) + 1)
            in {(6, 6, 4), (7, 7, 4), (6, 8, 4)}
            and tuple(nonempty_indices) == (1, 3, 5)
            and all(count == 1 for count in row_color_counts)
        ),
    }
    return facts


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    facts = _analyse(grid)
    if facts["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(facts["errors"]))
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Strict recognizer for the lawful teaching distribution."""
    del difficulty
    facts = _analyse(grid)
    errors = list(facts["errors"])
    if isinstance(meta, dict):
        requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
        if isinstance(requested, dict) and not errors:
            observed = observe_overrides(grid)
            for axis in AXES:
                if requested.get(axis) is not None and observed[axis] != requested[axis]:
                    errors.append(
                        f"{axis} requested {requested[axis]!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """All ordinary draws and every canonical input satisfy this task manifold."""
    return _analyse(grid)["errors"]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror used only for focused tests and rival audits."""
    facts = _analyse(grid)
    if facts["errors"]:
        raise ValueError("invalid lesson: " + "; ".join(facts["errors"]))
    return [list(row) for row in facts["kept_rows"]]


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = _analyse(grid)
    if facts["errors"]:
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["grid_h"],
        facts["grid_w"],
        facts["n_nonempty_rows"],
        facts["nonempty_indices"],
        facts["nonzero_counts"],
        facts["row_color_counts"],
        facts["fg_colors"],
    )


def _rival_odd_indexed_rows(grid):
    return [list(row) for index, row in enumerate(grid) if index % 2 == 1]


def _rival_first_three_nonempty(grid):
    rows = [list(row) for row in grid if any(value != 0 for value in row)]
    return rows[:3]


def _rival_sort_by_density(grid):
    rows = [list(row) for row in grid if any(value != 0 for value in row)]
    return sorted(rows, key=lambda row: sum(value != 0 for value in row))


def _rival_monochrome_rows(grid):
    rows = [list(row) for row in grid if any(value != 0 for value in row)]
    out = []
    for row in rows:
        color = next(value for value in row if value != 0)
        out.append([color if value != 0 else 0 for value in row])
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "keep_odd_indexed_rows": _rival_odd_indexed_rows,
    "keep_first_three_nonempty": _rival_first_three_nonempty,
    "sort_nonempty_rows_by_density": _rival_sort_by_density,
    "force_each_kept_row_monochrome": _rival_monochrome_rows,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_adjacent(grid):
    facts = _analyse(grid)
    return not facts["errors"] and facts["has_adjacent_nonempty"]


def _witness_multi_gap(grid):
    facts = _analyse(grid)
    return not facts["errors"] and facts["has_multi_row_gap"]


def _witness_four_rows(grid):
    facts = _analyse(grid)
    return not facts["errors"] and facts["n_nonempty_rows"] == 4


def _witness_nonmonotonic_density(grid):
    facts = _analyse(grid)
    return not facts["errors"] and facts["density_nonmonotonic"]


def _witness_multicolor_row(grid):
    facts = _analyse(grid)
    return not facts["errors"] and facts["has_multicolor_row"]


SEMANTIC_WITNESSES = {
    "adjacent_nonempty_refutes_odd_rows": _witness_adjacent,
    "multi_gap_shifts_row_parity": _witness_multi_gap,
    "four_rows_refute_fixed_output_height": _witness_four_rows,
    "nonmonotonic_density_refutes_sorting": _witness_nonmonotonic_density,
    "multicolor_row_refutes_monochrome_shortcut": _witness_multicolor_row,
}
WITNESS_RIVALS = {
    "adjacent_nonempty_refutes_odd_rows": ["keep_odd_indexed_rows"],
    "multi_gap_shifts_row_parity": ["keep_odd_indexed_rows"],
    "four_rows_refute_fixed_output_height": ["keep_first_three_nonempty"],
    "nonmonotonic_density_refutes_sorting": ["sort_nonempty_rows_by_density"],
    "multicolor_row_refutes_monochrome_shortcut": ["force_each_kept_row_monochrome"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to refute every named canonical shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    facts_by_demo: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts = _analyse(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} malformed: {facts['errors'][0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not delete exactly the empty rows")
        facts_by_demo.append(facts)

    required_features = {
        "canonical odd-row anchor": lambda facts: facts["canonical_odd_profile"],
        "adjacent nonempty rows": lambda facts: facts["has_adjacent_nonempty"],
        "multi-row empty gap": lambda facts: facts["has_multi_row_gap"],
        "occupied first or last row": lambda facts: facts["has_occupied_edge"],
        "four-row output": lambda facts: facts["n_nonempty_rows"] == 4,
        "nonmonotonic row density": lambda facts: facts["density_nonmonotonic"],
        "multicolor kept row": lambda facts: facts["has_multicolor_row"],
    }
    for label, predicate in required_features.items():
        if not any(predicate(facts) for facts in facts_by_demo):
            reasons.append(f"demonstrations lack {label}")

    for name, competitor in LESSON_COMPETITORS.items():
        if facts_by_demo and all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_facts = _analyse(query["input"])
        if query_facts["errors"]:
            reasons.append(f"query malformed: {query_facts['errors'][0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative transform")
    return reasons


def negative_recombination_fixture(grid: Any) -> list[list[int]]:
    """Remove the empty-row cue using a foreground color absent elsewhere."""
    out = deepcopy(grid)
    used = {value for row in out for value in row if value != 0}
    replacement = next(color for color in range(1, 10) if color not in used)
    for row in out:
        if all(value == 0 for value in row):
            row[0] = replacement
    return out
