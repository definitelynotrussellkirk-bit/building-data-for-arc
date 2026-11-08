"""Generator for ``Fill Vertical Spans Between Matching Endpoints``.

The canonical rule examines each column independently.  It fills the inclusive
vertical interval only when that column contains exactly two non-zero cells and
their colours match; every other column is left unchanged.

A three-example schedule prevents the canonical-only shortcut "every active
column is a valid span": one clean scene is followed by two independently drawn
complete guard scenes.  Every guard scene contains a mismatched pair, singleton,
and same-colour triple, and reuses a colour across valid pairs.  Therefore every
three-of-four query rotation retains direct evidence against all declared
canonical-fitting shortcuts.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f93d8860778"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "abdf780ecbe7"  # normalized canonical program_solution
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "canonical_clean",
    "mismatched_guard",
    "multiplicity_guard",
)
CANONICAL_SHAPES = (
    (7, 11),
    (8, 10),
    (9, 8),
    (10, 9),
    (12, 8),
)

SUMMARY = (
    "On a zero-background 7..12 by 8..11 grid, 2..5 columns contain exactly "
    "two matching coloured endpoints separated by zero cells.  Fill only those "
    "inclusive vertical intervals.  A three-example schedule alternates one "
    "clean scene with two complete guard scenes containing mismatched, singleton, "
    "and three-marker columns that remain unchanged; valid-pair colours are "
    "reused so the rule must be inferred per column."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colours 0..9",
    "2..5 valid columns contain exactly two equal-colour endpoints with a zero gap",
    "valid columns include a border-anchored pair and an interior pair",
    "valid spans vary in length, including one no longer than 6 and one at least 5",
    "clean scenes contain no guard columns and use distinct valid-pair colours",
    "each guard scene contains one unequal-colour pair, one singleton, and one gapped same-colour triple",
    "guard scenes reuse a colour across valid pairs and reuse two guard colours",
    "only exact matching pairs are filled; guard columns remain unchanged",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over 8..11",
        "valid": "8..11",
    },
    "spans": {
        "type": "int",
        "default": "difficulty-aware draw over 2..5",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic teaching profile for schedule audits."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["empty or non-list grid"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-list first row"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged or non-list row"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or colour outside 0..9")
    return errors


def _empty_analysis(errors: list[str]) -> dict[str, Any]:
    return {
        "errors": errors,
        "height": 0,
        "width": 0,
        "pairs": [],
        "decoys": [],
        "span_lengths": [],
        "colours": [],
        "border_pairs": 0,
        "interior_pairs": 0,
        "full_height_pairs": 0,
        "top_anchored_pairs": 0,
        "bottom_anchored_pairs": 0,
    }


def _analysis(grid: Any) -> dict[str, Any]:
    """Classify valid span columns and lawful non-firing guard columns."""
    errors = _shape_errors(grid)
    if errors:
        return _empty_analysis(errors)

    height, width = len(grid), len(grid[0])
    pairs: list[dict[str, int]] = []
    decoys: list[dict[str, Any]] = []

    for column in range(width):
        cells = [
            (row, grid[row][column])
            for row in range(height)
            if grid[row][column] != 0
        ]
        if not cells:
            continue

        rows = [row for row, _ in cells]
        colours = [colour for _, colour in cells]
        top, bottom = rows[0], rows[-1]
        span_length = bottom - top + 1

        if len(cells) == 2 and colours[0] == colours[1]:
            if bottom - top < 2:
                errors.append(
                    f"active column {column} matching endpoints are adjacent; no zero gap"
                )
                continue
            pairs.append(
                {
                    "column": column,
                    "top": top,
                    "bottom": bottom,
                    "colour": colours[0],
                    "length": span_length,
                    "border": int(top == 0 or bottom == height - 1),
                    "interior": int(top > 0 and bottom < height - 1),
                    "full_height": int(top == 0 and bottom == height - 1),
                    "top_anchored": int(top == 0 and bottom < height - 1),
                    "bottom_anchored": int(top > 0 and bottom == height - 1),
                }
            )
            continue

        if len(cells) == 1:
            decoys.append(
                {
                    "kind": "singleton",
                    "column": column,
                    "rows": tuple(rows),
                    "colours": tuple(colours),
                }
            )
            continue

        if len(cells) == 2 and colours[0] != colours[1]:
            if bottom - top < 2:
                errors.append(
                    f"guard column {column} mismatched endpoints are adjacent; no zero gap"
                )
                continue
            decoys.append(
                {
                    "kind": "mismatched_pair",
                    "column": column,
                    "rows": tuple(rows),
                    "colours": tuple(colours),
                }
            )
            continue

        if len(cells) == 3 and len(set(colours)) == 1:
            if span_length <= len(cells):
                errors.append(
                    f"guard column {column} same-colour triple is contiguous; no zero gap"
                )
                continue
            decoys.append(
                {
                    "kind": "same_colour_triple",
                    "column": column,
                    "rows": tuple(rows),
                    "colours": tuple(colours),
                }
            )
            continue

        errors.append(
            f"active column {column} has unsupported non-zero pattern "
            f"rows={rows}, colours={colours}"
        )

    pair_colours = [pair["colour"] for pair in pairs]
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "pairs": pairs,
        "decoys": decoys,
        "span_lengths": [pair["length"] for pair in pairs],
        "colours": pair_colours,
        "border_pairs": sum(pair["border"] for pair in pairs),
        "interior_pairs": sum(pair["interior"] for pair in pairs),
        "full_height_pairs": sum(pair["full_height"] for pair in pairs),
        "top_anchored_pairs": sum(pair["top_anchored"] for pair in pairs),
        "bottom_anchored_pairs": sum(pair["bottom_anchored"] for pair in pairs),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete sampler grammar while retaining canonical inputs."""
    del difficulty
    info = _analysis(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    height, width = info["height"], info["width"]
    pairs = info["pairs"]
    decoys = info["decoys"]
    lengths = info["span_lengths"]

    if not 7 <= height <= 12:
        errors.append(f"height {height} outside teaching range 7..12")
    if not 8 <= width <= 11:
        errors.append(f"width {width} outside teaching range 8..11")
    if not 2 <= len(pairs) <= 5:
        errors.append(f"expected 2..5 valid span columns, found {len(pairs)}")
    if len(decoys) > 3:
        errors.append(f"expected at most 3 guard columns, found {len(decoys)}")
    if info["border_pairs"] < 1:
        errors.append("missing a border-anchored endpoint pair")
    if info["interior_pairs"] < 1:
        errors.append("missing an interior endpoint pair")
    if not any(length <= 6 for length in lengths):
        errors.append("missing an endpoint span of length at most 6")
    if not any(length >= 5 for length in lengths):
        errors.append("missing a long endpoint span of length at least 5")
    if len(set(lengths)) < 2:
        errors.append("all endpoint spans have one fixed length")

    # The sampler admits three complete teaching signatures, not arbitrary
    # mixtures of decoys.  This preserves the legacy validator contract: a
    # lone endpoint deletion, endpoint mismatch, inserted marker, or duplicated
    # pair colour remains an invalid structural impostor.
    kinds = Counter(decoy["kind"] for decoy in decoys)
    repeated_pair_colour = len(set(info["colours"])) < len(info["colours"])
    complete_guard = (
        ("mismatched_pair", 1),
        ("same_colour_triple", 1),
        ("singleton", 1),
    )
    allowed_signatures = {
        ((), False): "canonical_clean",
        (complete_guard, True): "complete_guard",
    }
    signature = (tuple(sorted(kinds.items())), repeated_pair_colour)
    if signature not in allowed_signatures:
        errors.append(
            "unsupported teaching signature: "
            f"guards={dict(kinds)}, repeated_pair_colour={repeated_pair_colour}"
        )

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def _short_interior_pair(rng, height: int) -> tuple[int, int]:
    gap = rng.choice((2, 3))  # inclusive length 3 or 4
    top = rng.randint(1, height - gap - 2)
    return top, top + gap


def _long_border_pair(
    rng, height: int, anchor_mode: str
) -> tuple[int, int]:
    if anchor_mode == "full":
        return 0, height - 1
    if anchor_mode == "top":
        return 0, rng.randint(4, height - 2)
    top = rng.randint(1, height - 5)
    return top, height - 1


def _random_pair(rng, height: int) -> tuple[int, int]:
    top = rng.randint(0, height - 3)
    bottom = rng.randint(top + 2, height - 1)
    return top, bottom


def _gapped_triple(rng, height: int) -> tuple[int, int, int]:
    candidates = [
        rows
        for rows in combinations(range(height), 3)
        if rows[-1] - rows[0] + 1 > len(rows)
    ]
    return rng.choice(candidates)


def _pair_colours(rng, count: int, profile: str) -> list[int]:
    if profile == "canonical_clean":
        return rng.sample(range(1, 10), count)
    unique = rng.sample(range(1, 10), count - 1)
    return [unique[0], unique[0], *unique[1:]]


def _profile_errors(info: dict[str, Any], profile: str) -> list[str]:
    kinds = Counter(decoy["kind"] for decoy in info["decoys"])
    pair_colours = info["colours"]
    repeated = len(set(pair_colours)) < len(pair_colours)

    if profile == "canonical_clean":
        errors = []
        if kinds:
            errors.append(f"clean profile unexpectedly has guards {dict(kinds)}")
        if repeated:
            errors.append("clean profile must use distinct valid-pair colours")
        return errors

    expected = Counter({
        "mismatched_pair": 1,
        "singleton": 1,
        "same_colour_triple": 1,
    })
    errors = []
    if kinds != expected:
        errors.append(
            f"{profile} expected guard kinds {dict(expected)}, observed {dict(kinds)}"
        )
    if not repeated:
        errors.append(f"{profile} must reuse a colour across valid pairs")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    # One default slot in five anchors an observed canonical height/width/palette
    # profile in every difficulty band.  Explicit overrides always take the full
    # advertised ranges and are never replaced by this curriculum branch.
    canonical_anchor = not overrides and sample_index % 5 == 0
    if canonical_anchor:
        target_h, target_w = CANONICAL_SHAPES[(seed + sample_index // 5) % len(CANONICAL_SHAPES)]
        target_spans = 3
        height = ctx.draw_int("grid_h", target_h, target_h)
        width = ctx.draw_int("grid_w", target_w, target_w)
        span_count = ctx.draw_int("spans", target_spans, target_spans)
    else:
        # Full advertised ranges remain legal in every difficulty band.
        # Difficulty changes only the default draw distribution.
        height = ctx.draw_int_diff("grid_h", 7, 12)
        width = ctx.draw_int_diff("grid_w", 8, 11)
        # Default guard lessons need both a repeated pair colour and a second
        # pair colour so the one-colour interval rival is always observable.
        # The exact ``spans=2`` override remains supported in every band.
        span_lo = 2 if profile == "canonical_clean" or "spans" in overrides else 3
        span_count = ctx.draw_int_diff("spans", span_lo, 5)

    decoy_count = 0 if profile == "canonical_clean" else 3
    if span_count + decoy_count > width:
        raise ValueError(
            f"{profile} needs {span_count + decoy_count} columns in width {width}"
        )

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    grid = full_grid(height, width, 0)
    columns = layout_rng.sample(range(width), span_count + decoy_count)
    pair_columns = columns[:span_count]
    decoy_columns = columns[span_count:]

    anchor_mode = ("full", "top", "bottom")[sample_index % 3]
    intervals: list[tuple[int, int]] = [
        _long_border_pair(layout_rng, height, anchor_mode),
        _short_interior_pair(layout_rng, height),
    ]
    intervals.extend(
        _random_pair(layout_rng, height) for _ in range(span_count - 2)
    )

    pair_colours = _pair_colours(palette_rng, span_count, profile)
    for column, colour, (top, bottom) in zip(
        pair_columns, pair_colours, intervals
    ):
        grid[top][column] = colour
        grid[bottom][column] = colour

    if profile != "canonical_clean":
        # Two guard colours are shared across all three non-firing patterns.
        # On canonical-profile anchors with two repeated-colour pairs this keeps
        # the total palette at exactly background + three foreground colours.
        if canonical_anchor:
            existing = next(
                colour for colour in pair_colours if colour != pair_colours[0]
            )
            novel = palette_rng.choice(
                [colour for colour in range(1, 10) if colour not in set(pair_colours)]
            )
            guard_colours = [existing, novel]
        else:
            guard_colours = palette_rng.sample(
                [colour for colour in range(1, 10) if colour != pair_colours[0]],
                2,
            )
        if profile == "multiplicity_guard":
            guard_colours.reverse()
        first, second = guard_colours

        top, bottom = _random_pair(layout_rng, height)
        mismatch_column, singleton_column, triple_column = decoy_columns
        grid[top][mismatch_column] = first
        grid[bottom][mismatch_column] = second

        singleton_row = layout_rng.randrange(height)
        grid[singleton_row][singleton_column] = first
        for row in _gapped_triple(layout_rng, height):
            grid[row][triple_column] = second

    info = _analysis(grid)
    errors = self_check(grid, difficulty=difficulty)
    errors.extend(_profile_errors(info, profile))
    if errors:
        raise AssertionError(
            "generator constructed invalid grid: " + "; ".join(errors)
        )
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError(
            "cannot observe malformed grid: " + "; ".join(info["errors"])
        )
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "spans": len(info["pairs"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-input predicate accepted by the semantic gate."""
    return self_check(grid)


def _lawful_info(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if self_check(grid) else info


def _witness(predicate: Callable[[dict[str, Any]], bool], grid) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror only; the canonical Racket program is authoritative."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        for row in range(pair["top"], pair["bottom"] + 1):
            out[row][pair["column"]] = pair["colour"]
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _fill_full_active_columns(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        for row in range(info["height"]):
            out[row][pair["column"]] = pair["colour"]
    return out


def _fill_border_pairs_only(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        if not pair["border"]:
            continue
        for row in range(pair["top"], pair["bottom"] + 1):
            out[row][pair["column"]] = pair["colour"]
    return out


def _fill_fixed_length_three(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        stop = min(pair["bottom"], pair["top"] + 2)
        for row in range(pair["top"], stop + 1):
            out[row][pair["column"]] = pair["colour"]
    return out


def _fill_with_one_colour(grid):
    info = _analysis(grid)
    if info["errors"] or not info["colours"]:
        return None
    colour = min(info["colours"])
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        for row in range(pair["top"], pair["bottom"] + 1):
            out[row][pair["column"]] = colour
    return out


def _fill_every_active_column(grid):
    """Wrong rule: fill between extrema in every column with >=2 marks."""
    out = [row[:] for row in grid]
    for column in range(len(grid[0])):
        cells = [
            (row, grid[row][column])
            for row in range(len(grid))
            if grid[row][column] != 0
        ]
        if len(cells) < 2:
            continue
        colour = cells[0][1]
        for row in range(cells[0][0], cells[-1][0] + 1):
            out[row][column] = colour
    return out


def _fill_matching_extrema(grid):
    """Wrong rule: ignore extra marks when a column's extrema match."""
    out = [row[:] for row in grid]
    for column in range(len(grid[0])):
        cells = [
            (row, grid[row][column])
            for row in range(len(grid))
            if grid[row][column] != 0
        ]
        if len(cells) < 2 or cells[0][1] != cells[-1][1]:
            continue
        for row in range(cells[0][0], cells[-1][0] + 1):
            out[row][column] = cells[0][1]
    return out


def _fill_singletons_to_bottom(grid):
    """Wrong rule: solve true pairs, then extend every singleton to a far edge."""
    info = _analysis(grid)
    if info["errors"]:
        return None
    out = rule_mirror(grid)
    for decoy in info["decoys"]:
        if decoy["kind"] != "singleton":
            continue
        row = decoy["rows"][0]
        colour = decoy["colours"][0]
        rows = range(row, info["height"]) if row < info["height"] - 1 else range(0, row + 1)
        for target in rows:
            out[target][decoy["column"]] = colour
    return out


def _global_exact_two_colours(grid):
    """Wrong rule: fill only colours occurring exactly twice globally."""
    info = _analysis(grid)
    if info["errors"]:
        return None
    counts = Counter(value for row in grid for value in row if value != 0)
    out = [row[:] for row in grid]
    for pair in info["pairs"]:
        if counts[pair["colour"]] != 2:
            continue
        for row in range(pair["top"], pair["bottom"] + 1):
            out[row][pair["column"]] = pair["colour"]
    return out


SEMANTIC_RIVALS = {
    "copy_input": _identity,
    "fill_active_columns_edge_to_edge": _fill_full_active_columns,
    "fill_only_border_pairs": _fill_border_pairs_only,
    "fill_fixed_three_cells": _fill_fixed_length_three,
    "paint_all_intervals_one_colour": _fill_with_one_colour,
    "fill_every_active_column": _fill_every_active_column,
    "fill_matching_extrema": _fill_matching_extrema,
    "global_exact_two_colours": _global_exact_two_colours,
    "fill_singletons_to_bottom": _fill_singletons_to_bottom,
}

CANONICAL_SHORTCUTS = {
    "fill_every_active_column": _fill_every_active_column,
    "fill_matching_extrema": _fill_matching_extrema,
    "global_exact_two_colours": _global_exact_two_colours,
    "fill_singletons_to_bottom": _fill_singletons_to_bottom,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "full_height_border_pair": lambda grid: _witness(
        lambda info: info["full_height_pairs"] >= 1, grid
    ),
    "top_only_border_pair": lambda grid: _witness(
        lambda info: info["top_anchored_pairs"] >= 1, grid
    ),
    "bottom_only_border_pair": lambda grid: _witness(
        lambda info: info["bottom_anchored_pairs"] >= 1, grid
    ),
    "interior_pair": lambda grid: _witness(
        lambda info: info["interior_pairs"] >= 1, grid
    ),
    "mixed_short_and_long_spans": lambda grid: _witness(
        lambda info: any(length <= 6 for length in info["span_lengths"])
        and any(length >= 5 for length in info["span_lengths"])
        and len(set(info["span_lengths"])) >= 2,
        grid,
    ),
    "distinct_pair_colours": lambda grid: _witness(
        lambda info: len(info["colours"]) == len(set(info["colours"])), grid
    ),
    "repeated_pair_colour": lambda grid: _witness(
        lambda info: len(info["colours"]) > len(set(info["colours"])), grid
    ),
    "mismatched_pair_guard": lambda grid: _witness(
        lambda info: any(
            decoy["kind"] == "mismatched_pair" for decoy in info["decoys"]
        ),
        grid,
    ),
    "singleton_guard": lambda grid: _witness(
        lambda info: any(
            decoy["kind"] == "singleton" for decoy in info["decoys"]
        ),
        grid,
    ),
    "same_colour_triple_guard": lambda grid: _witness(
        lambda info: any(
            decoy["kind"] == "same_colour_triple" for decoy in info["decoys"]
        ),
        grid,
    ),
}

WITNESS_RIVALS = {
    "full_height_border_pair": ["fill_only_border_pairs"],
    "top_only_border_pair": ["fill_active_columns_edge_to_edge"],
    "bottom_only_border_pair": ["fill_active_columns_edge_to_edge"],
    "interior_pair": ["fill_only_border_pairs"],
    "mixed_short_and_long_spans": ["copy_input", "fill_fixed_three_cells"],
    "distinct_pair_colours": ["paint_all_intervals_one_colour"],
    "repeated_pair_colour": ["global_exact_two_colours"],
    "mismatched_pair_guard": ["fill_every_active_column"],
    "singleton_guard": ["fill_singletons_to_bottom"],
    "same_colour_triple_guard": [
        "fill_every_active_column",
        "fill_matching_extrema",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every declared wrong rule to lose on a demonstration."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        findings = strict_canonical_like(grid)
        if findings:
            reasons.append(f"{role} is not lawful: {findings[:2]}")
            continue
        if rule_mirror(grid) != output:
            reasons.append(
                f"{role} output does not match vertical interval filling"
            )
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:  # pragma: no cover - retained as hook evidence
            reasons.append(f"shortcut '{name}' raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"shortcut '{name}' fits every demonstration")
    return reasons
