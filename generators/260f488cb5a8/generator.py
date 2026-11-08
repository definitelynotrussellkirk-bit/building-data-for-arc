"""Semantic generator for ARC task 260f488cb5a8 — stable row compaction.

Every row is transformed independently: remove its zero cells, preserve the
left-to-right order of the remaining colors, place that sequence at the left
edge, and fill the rest of the row with zeros.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "260f488cb5a8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "70d01868db22"
SUMMARY = (
    "Compact every row independently: preserve the original order of all "
    "nonzero cells, move that sequence flush left, and fill the remaining "
    "row cells with zero."
)
INVARIANTS = [
    "zero is the background and separator value",
    "rows are independent; values never cross a row boundary",
    "the multiplicity and left-to-right order of every row's nonzero values matter",
    "ordinary lessons contain empty rows and changed rows so global or identity shortcuts fail",
    "ordinary lessons include repeated colors, four-or-more-value rows, and multiple gaps",
]

SCENE_PROFILES = (
    "p5_both_edges",
    "p9_both_edges",
    "p5_left_edge",
    "p9_left_edge",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical height",
        "valid": "4..9",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical width",
        "valid": "6..10",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-profile cycle covering both canonical palette bands",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_PROFILE_DEFAULT_DIMS = {
    "p5_both_edges": (4, 7),
    "p9_both_edges": (5, 8),
    "p5_left_edge": (5, 6),
    "p9_left_edge": (4, 9),
}
_PROFILE_PALETTE_SIZE = {
    "p5_both_edges": 5,
    "p9_both_edges": 9,
    "p5_left_edge": 5,
    "p9_left_edge": 9,
}
_STRICT_CANONICAL_PROFILES = {
    (4, 7, 5),
    (5, 8, 9),
    (5, 6, 5),
    (4, 9, 9),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-residue lesson profile."""
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _candidate_positions(
    width: int,
    count: int,
    *,
    include_left: bool = False,
    include_right: bool = False,
    exclude_left: bool = False,
    exclude_right: bool = False,
    min_zeros_before_last: int = 1,
) -> list[tuple[int, ...]]:
    legal = list(range(width))
    if exclude_left:
        legal.remove(0)
    if exclude_right:
        legal.remove(width - 1)
    candidates: list[tuple[int, ...]] = []
    for cols in combinations(legal, count):
        if include_left and 0 not in cols:
            continue
        if include_right and width - 1 not in cols:
            continue
        last = cols[-1]
        zeros_before_last = (last + 1) - len(cols)
        if zeros_before_last < min_zeros_before_last:
            continue
        candidates.append(cols)
    return candidates


def _choose_positions(ctx, label: str, width: int, count: int, **constraints) -> tuple[int, ...]:
    candidates = _candidate_positions(width, count, **constraints)
    if not candidates:
        raise ValueError(
            f"no legal {label} positions for width={width}, count={count}, "
            f"constraints={constraints}"
        )
    return ctx.draw_rng(label).choice(candidates)


def _analysis(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {}, ["cells must be literal ARC integers 0..9"]

    height = len(grid)
    rows = []
    for index, row in enumerate(grid):
        positions = tuple(col for col, value in enumerate(row) if value != 0)
        values = tuple(row[col] for col in positions)
        rows.append(
            {
                "index": index,
                "positions": positions,
                "values": values,
                "count": len(values),
                "changed": positions != tuple(range(len(values))),
                "zeros_before_last": (
                    (positions[-1] + 1) - len(positions) if positions else 0
                ),
            }
        )

    active = tuple(item for item in rows if item["count"])
    empty = tuple(item["index"] for item in rows if not item["count"])
    palette = tuple(sorted({value for row in grid for value in row if value != 0}))
    info = {
        "height": height,
        "width": width,
        "rows": tuple(rows),
        "active_rows": active,
        "empty_rows": empty,
        "palette": palette,
        "total_nonzero": sum(item["count"] for item in active),
        "left_edge": any(row[0] != 0 for row in grid),
        "right_edge": any(row[-1] != 0 for row in grid),
    }

    if not 4 <= height <= 9:
        errors.append(f"height {height} outside 4..9")
    if not 6 <= width <= 10:
        errors.append(f"width {width} outside 6..10")
    if len(active) < 3:
        errors.append("need at least three active rows to establish row independence")
    if not empty:
        errors.append("need at least one empty row as a row-boundary control")
    if info["total_nonzero"] < 6:
        errors.append("need at least six nonzero cells for a teaching scene")
    if len(palette) < 3:
        errors.append("need at least three distinct nonzero colors")
    if any(item["count"] == width for item in active):
        errors.append("every active row must retain at least one zero cell")
    if not any(item["count"] >= 2 and item["changed"] for item in active):
        errors.append("need a row whose nonzero sequence actually compacts left")
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-local teaching grammar without mutating ``grid``."""
    del difficulty, meta
    return _analysis(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analysis(grid)
    if errors:
        return errors
    signature = (info["height"], info["width"], len(info["palette"]))
    if signature not in _STRICT_CANONICAL_PROFILES:
        return [
            f"profile {signature} is outside the four canonical (h,w,palette) signatures"
        ]
    return []


def _profile_from_info(info: dict[str, Any]) -> str:
    palette_size = len(info["palette"])
    if not info["left_edge"]:
        raise ValueError("generated profile must expose the left edge")
    if palette_size == 5:
        return "p5_both_edges" if info["right_edge"] else "p5_left_edge"
    if palette_size == 9:
        return "p9_both_edges" if info["right_edge"] else "p9_left_edge"
    raise ValueError(f"generated profile has unsupported palette size {palette_size}")


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analysis(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "scene_profile": _profile_from_info(info),
    }


def _filler_values(
    ctx, palette: list[int], count: int, missing: list[int], band: str
) -> list[int]:
    values = list(missing)
    rng = ctx.draw_rng(f"filler_values_{band}")
    while len(values) < count:
        cycle = list(palette)
        rng.shuffle(cycle)
        values.extend(cycle)
    return values[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = _band(difficulty)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = _scheduled_choice(ctx, "scene_profile", SCENE_PROFILES, scheduled)
    default_h, default_w = _PROFILE_DEFAULT_DIMS[profile]
    height = _scheduled_int(ctx, "grid_h", default_h, 4, 9)
    width = _scheduled_int(ctx, "grid_w", default_w, 6, 10)

    palette_size = _PROFILE_PALETTE_SIZE[profile]
    palette = sorted(ctx.draw_distinct_colors("palette", n=palette_size, exclude=(0,)))
    right_edge = profile.endswith("both_edges")

    # Keep the empty control row internal so a row-major global-pack shortcut
    # visibly crosses a boundary.  The remaining rows are shuffled so no row
    # index becomes answer-bearing.
    empty_row = ctx.draw_int(f"empty_row_{band}", 1, height - 2)
    active_rows = [row for row in range(height) if row != empty_row]
    ctx.draw_rng(f"active_row_order_{band}").shuffle(active_rows)
    primary, secondary, tertiary = active_rows[:3]

    primary_count = 5 if right_edge else 4
    positions: dict[int, tuple[int, ...]] = {
        primary: _choose_positions(
            ctx,
            f"primary_positions_{band}",
            width,
            primary_count,
            include_left=True,
            include_right=right_edge,
            exclude_right=not right_edge,
            min_zeros_before_last=1,
        ),
        secondary: _choose_positions(
            ctx,
            f"secondary_positions_{band}",
            width,
            4,
            exclude_left=True,
            exclude_right=not right_edge,
            min_zeros_before_last=1,
        ),
        tertiary: _choose_positions(
            ctx,
            f"tertiary_positions_{band}",
            width,
            3,
            exclude_left=True,
            exclude_right=not right_edge,
            min_zeros_before_last=2,
        ),
    }
    for row in active_rows[3:]:
        max_col_count = width - (1 if not right_edge else 0)
        count = ctx.draw_int(
            f"row_{row}_count_{band}", 1, min(4, max_col_count - 1)
        )
        positions[row] = _choose_positions(
            ctx,
            f"row_{row}_positions_{band}",
            width,
            count,
            exclude_right=not right_edge,
            min_zeros_before_last=1,
        )

    high, low = palette[-1], palette[0]
    primary_values = [high, low, high, palette[1]]
    if primary_count == 5:
        primary_values.append(palette[-2])
    used = set(primary_values)
    missing = [color for color in palette if color not in used]
    remaining_slots = sum(len(positions[row]) for row in active_rows if row != primary)
    filler = _filler_values(ctx, palette, remaining_slots, missing, band)

    values_by_row: dict[int, list[int]] = {primary: primary_values}
    cursor = 0
    for row in active_rows:
        if row == primary:
            continue
        count = len(positions[row])
        values = filler[cursor : cursor + count]
        cursor += count
        ctx.draw_rng(f"row_{row}_value_order_{band}").shuffle(values)
        values_by_row[row] = values

    grid = full_grid(height, width, 0)
    for row in active_rows:
        for col, value in zip(positions[row], values_by_row[row]):
            grid[row][col] = value

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid teaching scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["scene_profile"] != profile:
        raise AssertionError(
            f"scene profile drifted: requested {profile}, observed {observed['scene_profile']}"
        )
    return grid


def rule_mirror(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        output.append(values + [0] * (len(row) - len(values)))
    return output


def _identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _sort_rows(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = sorted(value for value in row if value != 0)
        output.append(values + [0] * (len(row) - len(values)))
    return output


def _reverse_rows(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = [value for value in row if value != 0][::-1]
        output.append(values + [0] * (len(row) - len(values)))
    return output


def _global_pack(grid: Any) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    values = [value for row in grid for value in row if value != 0]
    flat = values + [0] * (height * width - len(values))
    return [flat[start : start + width] for start in range(0, len(flat), width)]


def _first_three_per_row(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = [value for value in row if value != 0][:3]
        output.append(values + [0] * (len(row) - len(values)))
    return output


def _deduplicate_rows(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = []
        for value in row:
            if value != 0 and value not in values:
                values.append(value)
        output.append(values + [0] * (len(row) - len(values)))
    return output


def _close_one_gap(grid: Any) -> list[list[int]]:
    output = []
    for source in grid:
        row = list(source)
        last = max((index for index, value in enumerate(row) if value != 0), default=-1)
        gap = next((index for index in range(last) if row[index] == 0), None)
        if gap is not None:
            del row[gap]
            row.append(0)
        output.append(row)
    return output


def _repeat_first_color(grid: Any) -> list[list[int]]:
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        packed = ([values[0]] * len(values)) if values else []
        output.append(packed + [0] * (len(row) - len(packed)))
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "sort_nonzeros": _sort_rows,
    "reverse_nonzeros": _reverse_rows,
    "global_row_major_pack": _global_pack,
    "keep_only_first_three": _first_three_per_row,
    "deduplicate_each_row": _deduplicate_rows,
    "close_only_one_gap": _close_one_gap,
    "repeat_first_color_by_count": _repeat_first_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _facts(grid: Any) -> tuple[dict[str, Any], bool]:
    info, errors = _analysis(grid)
    return info, not errors


def _witness_changed(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(item["changed"] for item in info["active_rows"])


def _witness_nonmonotone(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(list(item["values"]) != sorted(item["values"]) for item in info["active_rows"])


def _witness_order_asymmetric(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(
        len(item["values"]) >= 2 and item["values"] != item["values"][::-1]
        for item in info["active_rows"]
    )


def _witness_internal_empty_row(grid: Any) -> bool:
    info, ok = _facts(grid)
    if not ok:
        return False
    active_indices = {item["index"] for item in info["active_rows"]}
    return any(
        any(later > row for later in active_indices)
        for row in info["empty_rows"]
    )


def _witness_long_row(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(item["count"] >= 4 for item in info["active_rows"])


def _witness_duplicate(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(len(item["values"]) != len(set(item["values"])) for item in info["active_rows"])


def _witness_multiple_gaps(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(item["zeros_before_last"] >= 2 for item in info["active_rows"])


def _witness_multicolor_row(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and any(len(set(item["values"])) >= 2 for item in info["active_rows"])


SEMANTIC_WITNESSES = {
    "actual_compaction": _witness_changed,
    "nonmonotone_order": _witness_nonmonotone,
    "asymmetric_order": _witness_order_asymmetric,
    "row_boundary_control": _witness_internal_empty_row,
    "four_or_more_values": _witness_long_row,
    "repeated_color_multiplicity": _witness_duplicate,
    "multiple_zero_gaps": _witness_multiple_gaps,
    "multicolor_row": _witness_multicolor_row,
}
WITNESS_RIVALS = {
    "actual_compaction": ["identity"],
    "nonmonotone_order": ["sort_nonzeros"],
    "asymmetric_order": ["reverse_nonzeros"],
    "row_boundary_control": ["global_row_major_pack"],
    "four_or_more_values": ["keep_only_first_three"],
    "repeated_color_multiplicity": ["deduplicate_each_row"],
    "multiple_zero_gaps": ["close_only_one_gap"],
    "multicolor_row": ["repeat_first_color_by_count"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    observed_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output is not stable row compaction")
        try:
            observed_profiles.add(observe_overrides(pair["input"])["scene_profile"])
        except ValueError as exc:
            reasons.append(f"demo {index} profile is not observable: {exc}")

    if observed_profiles != set(SCENE_PROFILES):
        reasons.append(
            "four consecutive demonstrations do not cover all scheduled profiles: "
            f"{sorted(observed_profiles)}"
        )
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival survives every demonstration: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output is not stable row compaction")
    return reasons
