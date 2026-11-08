"""Semantic generator for ARC task f06d31332595.

A full-height gray (5) divider separates a populated source panel on the left
from a blank destination panel on the right.  The output preserves the input
and reflects every non-zero, non-gray source cell across the divider while
preserving its color.

Version 3 replaces a loose ten-axis surface with four exact observable axes.
A three-example schedule supplies one canonical-profile anchor, one centered
connected motif, and one off-center connected motif.  The latter two are
purpose-built counterexamples to the strongest shortcuts left open by the
canonical demonstrations: reflecting around the geometric center regardless
of the gray guide, and reflecting only isolated singleton markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f06d31332595"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2739381bfcfd"

SUMMARY = (
    "Find the full-height gray divider. Preserve the input and reflect every "
    "non-zero, non-gray cell from its left source panel to the equal-distance "
    "cell on the right, preserving color. The divider may be centered or may "
    "have one to three extra blank columns beyond the reflected right panel."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is color 0",
    "exactly one full-height divider column is color 5",
    "all colored source cells lie left of the divider",
    "the complete right side is blank before reflection",
    "the right side is at least as wide as the source panel",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 6..16 with canonical anchors",
        "valid": "6..16",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-skewed 3..8 with canonical anchors",
        "valid": "3..8",
    },
    "extra_right": {
        "type": "int",
        "default": "scheduled 0 for two profiles, 1..3 for off-center profile",
        "valid": "0..3",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-skewed 2..6 with canonical anchors",
        "valid": "2..6",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

# (height, left/source-panel width, source mark count, source palette size).
# Adding background 0 and divider 5 gives the exact canonical (h, w, palette)
# profiles: (8,9,4), (8,9,6), (9,11,5), (9,11,7), (10,13,5).
_CANONICAL_PROFILES = (
    (8, 4, 4, 2),
    (8, 4, 4, 4),
    (9, 5, 4, 3),
    (9, 5, 5, 5),
    (10, 6, 5, 3),
)
_CANONICAL_GRID_PROFILES = {
    (height, 2 * panel_w + 1, palette_size + 2)
    for height, panel_w, _mark_count, palette_size in _CANONICAL_PROFILES
}

_PROFILE_SCHEDULE = (
    "canonical_anchor",
    "connected_centered",
    "connected_offcenter",
)
SCHEDULE_PROFILES = _PROFILE_SCHEDULE


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the exact three-example curriculum to the semantic gate."""
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    bounds = {
        "grid_h": (6, 16),
        "panel_w": (3, 8),
        "extra_right": (0, 3),
        "palette_size": (2, 6),
    }
    for name, (lo, hi) in bounds.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _orthogonally_adjacent(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def _canonical_positions(
    height: int, panel_w: int, mark_count: int, rng
) -> list[tuple[int, int]]:
    """Place isolated canonical-style markers, including the far source edge."""
    rows = list(range(height))
    rng.shuffle(rows)
    chosen: list[tuple[int, int]] = [(rows.pop(), 0)]

    # Canonical examples sometimes reach the divider-adjacent column and always
    # use more than one source column.  Keep the anchor cells isolated.
    near = (rows.pop(), panel_w - 1)
    chosen.append(near)

    candidates = [(row, col) for row in range(height) for col in range(panel_w)]
    rng.shuffle(candidates)
    for spot in candidates:
        if len(chosen) >= mark_count:
            break
        if spot in chosen:
            continue
        if spot[0] in {row for row, _ in chosen}:
            continue
        if any(_orthogonally_adjacent(spot, other) for other in chosen):
            continue
        chosen.append(spot)

    if len(chosen) != mark_count:
        raise RuntimeError("could not place canonical anchor markers")
    return sorted(chosen)


def _general_positions(
    height: int, panel_w: int, mark_count: int, rng
) -> list[tuple[int, int]]:
    """Place one connected pair plus far/near and repeated-column witnesses."""
    rows = rng.sample(list(range(height)), 4)
    pair_row, far_row, near_row, repeat_row = rows
    pair_col = rng.randrange(panel_w - 1)

    chosen: set[tuple[int, int]] = {
        (pair_row, pair_col),
        (pair_row, pair_col + 1),
        (far_row, 0),
        (near_row, panel_w - 1),
        (repeat_row, pair_col),
    }

    candidates = [
        (row, col)
        for row in range(height)
        for col in range(panel_w)
        if (row, col) not in chosen
    ]
    rng.shuffle(candidates)
    for spot in candidates:
        if len(chosen) >= mark_count:
            break
        chosen.add(spot)

    if len(chosen) != mark_count:
        raise RuntimeError("could not place general source markers")
    return sorted(chosen)


def _paint_positions(
    grid: list[list[int]],
    positions: list[tuple[int, int]],
    palette: list[int],
    rng,
    *, connected_pair: bool,
) -> None:
    if connected_pair:
        # Find the first horizontal adjacent pair and give it one shared color.
        pair: tuple[tuple[int, int], tuple[int, int]] | None = None
        position_set = set(positions)
        for row, col in positions:
            if (row, col + 1) in position_set:
                pair = ((row, col), (row, col + 1))
                break
        if pair is None:
            raise RuntimeError("general profile lacks its connected pair")

        remaining = [spot for spot in positions if spot not in pair]
        values = list(palette[1:])
        values.extend(rng.choice(palette) for _ in range(len(remaining) - len(values)))
        rng.shuffle(values)
        grid[pair[0][0]][pair[0][1]] = palette[0]
        grid[pair[1][0]][pair[1][1]] = palette[0]
        for (row, col), value in zip(remaining, values):
            grid[row][col] = value
        return

    values = list(palette)
    values.extend(rng.choice(palette) for _ in range(len(positions) - len(values)))
    rng.shuffle(values)
    for (row, col), value in zip(positions, values):
        grid[row][col] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_override = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile == "canonical_anchor" and not has_override:
        # Keep anchors inside the exact canonical profile set while ensuring
        # the three difficulty streams are not duplicate curricula.  The
        # offset makes the profile distinct for the same seed/sample pair;
        # the keyed layout label independently varies positions and colors.
        base_profile = ctx.draw_rng("canonical_profile").randrange(
            len(_CANONICAL_PROFILES)
        )
        band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
        height, panel_w, mark_count, palette_size = _CANONICAL_PROFILES[
            (base_profile + band_offset) % len(_CANONICAL_PROFILES)
        ]
        rng = ctx.draw_rng(f"layout_{difficulty or 'all'}")
        height = ctx.draw_int("grid_h", height, height)
        panel_w = ctx.draw_int("panel_w", panel_w, panel_w)
        extra_right = ctx.draw_int("extra_right", 0, 0)
        palette_size = ctx.draw_int("palette_size", palette_size, palette_size)
        positions = _canonical_positions(height, panel_w, mark_count, rng)
        connected_pair = False
    else:
        rng = ctx.draw_rng("layout")
        height = ctx.draw_int_diff("grid_h", 6, 16)
        panel_w = ctx.draw_int_diff("panel_w", 3, 8)
        palette_size = ctx.draw_int_diff("palette_size", 2, 6)

        if has_override:
            extra_right = ctx.draw_int("extra_right", 0, 3)
        elif profile == "connected_offcenter":
            extra_right = ctx.draw_int("extra_right", 1, 3)
        else:
            extra_right = ctx.draw_int("extra_right", 0, 0)

        capacity = height * panel_w
        lower = max(7, palette_size + 1)
        target_hi = {"easy": 9, "medium": 12, "hard": 15}.get(difficulty, 12)
        upper = min(capacity, target_hi)
        if upper < lower:
            upper = lower
        mark_count = ctx.draw_rng("mark_count").randint(lower, upper)
        positions = _general_positions(height, panel_w, mark_count, rng)
        connected_pair = True

    width = 2 * panel_w + 1 + extra_right
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][panel_w] = 5

    palette = rng.sample(list(_COLORS), palette_size)
    _paint_positions(
        grid, positions, palette, rng, connected_pair=connected_pair
    )
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _divider_or_raise(grid) -> int:
    errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(dividers) != 1:
        raise ValueError(
            f"expected exactly one full-height color-5 divider; got {dividers}"
        )
    return dividers[0]


def semantic_observables(grid) -> dict:
    """Recover exact axes and task-linked witnesses from an input grid."""
    errors = _grid_shape_errors(grid)
    if errors:
        return {
            "grid_h": 0,
            "grid_w": 0,
            "panel_w": None,
            "extra_right": None,
            "palette_size": 0,
            "mark_count": 0,
            "mark_rows": 0,
            "mark_columns": 0,
            "has_far_edge_mark": False,
            "has_near_divider_mark": False,
            "has_connected_source": False,
            "right_nonzero": None,
            "divider_columns": [],
        }

    height, width = len(grid), len(grid[0])
    divider_columns = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    divider = divider_columns[0] if len(divider_columns) == 1 else None
    marks: list[tuple[int, int, int]] = []
    if divider is not None:
        marks = [
            (row, col, grid[row][col])
            for row in range(height)
            for col in range(divider)
            if grid[row][col] not in (0, 5)
        ]
    mark_cells = {(row, col) for row, col, _value in marks}
    has_connected = any(
        (row + dr, col + dc) in mark_cells
        for row, col in mark_cells
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )
    right_nonzero = None
    extra_right = None
    if divider is not None:
        right_nonzero = sum(
            grid[row][col] != 0
            for row in range(height)
            for col in range(divider + 1, width)
        )
        extra_right = width - (2 * divider + 1)
    return {
        "grid_h": height,
        "grid_w": width,
        "panel_w": divider,
        "extra_right": extra_right,
        "palette_size": len({value for _row, _col, value in marks}),
        "mark_count": len(marks),
        "mark_rows": len({row for row, _col, _value in marks}),
        "mark_columns": len({col for _row, col, _value in marks}),
        "has_far_edge_mark": bool(marks) and any(col == 0 for _row, col, _ in marks),
        "has_near_divider_mark": (
            bool(marks)
            and divider is not None
            and any(col == divider - 1 for _row, col, _ in marks)
        ),
        "has_connected_source": has_connected,
        "right_nonzero": right_nonzero,
        "divider_columns": divider_columns,
    }


def observe_overrides(grid) -> dict:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful teaching grammar and all canonical inputs."""
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 16:
        errors.append(f"height {height} outside 6..16")

    divider_columns = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        errors.append(
            f"expected exactly one full-height color-5 divider; got {divider_columns}"
        )
        return errors
    divider = divider_columns[0]
    if not 3 <= divider <= 8:
        errors.append(f"source panel width {divider} outside 3..8")

    extra_right = width - (2 * divider + 1)
    if not 0 <= extra_right <= 3:
        errors.append(
            "right panel must equal the source width plus 0..3 extra blank columns"
        )

    if any(
        grid[row][col] == 5
        for row in range(height)
        for col in range(width)
        if col != divider
    ):
        errors.append("color 5 may occur only in the divider column")

    if any(
        grid[row][col] != 0
        for row in range(height)
        for col in range(divider + 1, width)
    ):
        errors.append("right side must be entirely background before reflection")

    marks = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(divider)
        if grid[row][col] not in (0, 5)
    ]
    colors = {value for _row, _col, value in marks}
    if not 4 <= len(marks) <= 15:
        errors.append(f"expected 4..15 source marks; found {len(marks)}")
    if not 2 <= len(colors) <= 6:
        errors.append(f"expected 2..6 source colors; found {len(colors)}")
    if len({row for row, _col, _value in marks}) < 2:
        errors.append("source marks must span at least two rows")
    if len({col for _row, col, _value in marks}) < 2:
        errors.append("source marks must span at least two columns")
    if marks and not any(col == 0 for _row, col, _value in marks):
        errors.append("source marks must include the far edge column 0")
    return errors


def strict_canonical_like(grid) -> bool:
    """True only for isolated, exact-profile canonical-scale inputs."""
    if self_check(grid):
        return False
    facts = semantic_observables(grid)
    profile = (
        facts["grid_h"],
        facts["grid_w"],
        facts["palette_size"] + 2,
    )
    return (
        facts["extra_right"] == 0
        and profile in _CANONICAL_GRID_PROFILES
        and facts["mark_count"] in (4, 5)
        and not facts["has_connected_source"]
    )


def rule_mirror(grid):
    """Independent Python mirror; the unchanged canonical Racket is authority."""
    divider = _divider_or_raise(grid)
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(divider + 1, width):
            source_col = 2 * divider - col
            if not 0 <= source_col < width:
                continue
            value = grid[row][source_col]
            if value not in (0, 5):
                output[row][col] = value
    return output


def _rival_grid_center_axis(grid):
    """Wrong rule fitting canonical pairs: reflect around the grid center."""
    divider = _divider_or_raise(grid)
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            if value in (0, 5):
                continue
            mirror_col = width - 1 - col
            if 0 <= mirror_col < width:
                output[row][mirror_col] = value
    return output


def _rival_isolated_markers_only(grid):
    """Wrong rule fitting canonical pairs: mirror singleton markers only."""
    divider = _divider_or_raise(grid)
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    source_cells = {
        (row, col)
        for row in range(height)
        for col in range(divider)
        if grid[row][col] not in (0, 5)
    }
    for row, col in source_cells:
        connected = any(
            (row + dr, col + dc) in source_cells
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
        if connected:
            continue
        mirror_col = 2 * divider - col
        if 0 <= mirror_col < width:
            output[row][mirror_col] = grid[row][col]
    return output


SEMANTIC_RIVALS = {
    "grid_center_axis": _rival_grid_center_axis,
    "isolated_markers_only": _rival_isolated_markers_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "off_center_divider": (
        lambda grid: semantic_observables(grid)["extra_right"] not in (None, 0)
    ),
    "connected_source_motif": (
        lambda grid: semantic_observables(grid)["has_connected_source"]
    ),
}
WITNESS_RIVALS = {
    "off_center_divider": ["grid_center_axis"],
    "connected_source_motif": ["isolated_markers_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a query-changing rival alive."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(
                f"demo {index} input is invalid: {type(exc).__name__}: {exc}"
            )
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the canonical rule")

    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    try:
        query_truth = rule_mirror(query["input"])
    except Exception as exc:
        return reasons + [f"query input is invalid: {type(exc).__name__}: {exc}"]
    if "output" in query and query["output"] != query_truth:
        reasons.append("query output disagrees with the canonical rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query_truth
        except Exception as exc:
            reasons.append(
                f"competitor {name!r} raised {type(exc).__name__}: {exc}"
            )
            continue
        if survives and changes_query:
            reasons.append(
                f"demos do not refute query-changing competitor {name!r}"
            )
    return reasons
