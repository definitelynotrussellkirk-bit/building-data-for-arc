"""Generator for arc_puzzle_bank_twentythird21:E155.

Each non-zero cell in the leftmost column is a row key.  The oracle starts from
an empty grid and paints that entire row with the key color; rows whose key is
zero remain empty.

The teaching distribution deliberately keeps every body cell blank, uses at
least two distinct row keys, and leaves at least one unmarked row.  Consequently
each individual demonstration refutes the most plausible shortcuts: identity,
painting only one marked row, using one color for every marked row, painting
all rows, and reading the opposite edge.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Pair = dict[str, Grid]

GENERATOR_ID = "252c3df06496"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ea4fd12284e3"

SUMMARY = (
    "Read each row's leftmost cell as an independent color key. For every "
    "non-zero key, paint the complete row with that key color; leave rows "
    "whose leftmost cell is zero completely blank."
)

INVARIANTS = [
    "background is 0 and every body cell (column > 0) is initially 0",
    "two to five distinct non-zero row keys occur in column 0",
    "at least one row is unmarked, so paint-all-rows is visibly wrong",
    "the returned shape is one of the declared scene profiles",
]

# Every generated demonstration independently kills all named rivals, so every
# consecutive lesson window is identifiable without relying on aggregate
# schedule coverage.
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.10

# Profiles are encoded by the exact observable tuple (height, width, key count).
# The first three shapes reproduce every canonical (h, w) profile; the larger
# profiles broaden scale while preserving the same sparse left-edge grammar.
_SCENE_PROFILES: dict[str, tuple[int, int, int]] = {
    "canonical_5x6_k3": (5, 6, 3),
    "canonical_6x7_k3": (6, 7, 3),
    "canonical_6x8_k3": (6, 8, 3),
    "compact_5x7_k2": (5, 7, 2),
    "expanded_7x9_k4": (7, 9, 4),
    "expanded_8x10_k5": (8, 10, 5),
}
_PROFILE_BY_GEOMETRY = {value: name for name, value in _SCENE_PROFILES.items()}
_PROFILE_NAMES = tuple(_SCENE_PROFILES)
_PALETTE_KINDS = ("canonical", "includes_nine")
_CANONICAL_COLORS = tuple(range(1, 9))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted keyed draw; all values legal in every band",
        "valid": "canonical_5x6_k3|canonical_6x7_k3|canonical_6x8_k3|compact_5x7_k2|expanded_7x9_k4|expanded_8x10_k5",
    },
    "palette_kind": {
        "type": "str",
        "default": "difficulty-weighted keyed draw",
        "valid": "canonical|includes_nine",
    },
}


def _profile_options(difficulty: Any) -> tuple[str, ...]:
    """Weighted options that retain the full exact override domain."""
    canonical = _PROFILE_NAMES[:3]
    compact = (_PROFILE_NAMES[3],)
    expanded = _PROFILE_NAMES[4:]
    if difficulty == "easy":
        return canonical + canonical + compact + expanded
    if difficulty == "hard":
        return canonical + compact + expanded + expanded
    return canonical + compact + expanded


def _palette_options(difficulty: Any) -> tuple[str, ...]:
    """Keep canonical palettes common while exercising color 9 in every band."""
    if difficulty == "hard":
        return ("canonical", "includes_nine", "includes_nine")
    return ("canonical", "canonical", "includes_nine")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _marked_rows(grid: Grid) -> list[tuple[int, int]]:
    return [(row, values[0]) for row, values in enumerate(grid) if values[0] != 0]


def _analyze(grid: Any) -> dict[str, Any]:
    """Pure structural analysis shared by checks and observers."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty or non-list grid"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list first row"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged or non-list row"]}
    height = len(grid)
    bad_values = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append(f"grid values must be integer ARC colors 0..9: {bad_values[:3]}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "marked": [],
            "scene_profile": None,
            "palette_kind": None,
        }

    marked = _marked_rows(grid)
    colors = [color for _, color in marked]
    body_nonzero = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(1, width)
        if grid[row][col] != 0
    ]
    profile = _PROFILE_BY_GEOMETRY.get((height, width, len(marked)))
    if colors and 9 in colors and all(color in (*_CANONICAL_COLORS, 9) for color in colors):
        palette_kind = "includes_nine"
    elif colors and all(color in _CANONICAL_COLORS for color in colors):
        palette_kind = "canonical"
    else:
        palette_kind = None

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "marked": marked,
        "colors": colors,
        "body_nonzero": body_nonzero,
        "scene_profile": profile,
        "palette_kind": palette_kind,
    }


def observe_overrides(grid: Grid) -> dict[str, str]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    profile = analysis.get("scene_profile")
    palette_kind = analysis.get("palette_kind")
    if profile is None or palette_kind is None:
        return {}
    return {"scene_profile": profile, "palette_kind": palette_kind}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the sparse left-edge teaching grammar and exact axis support."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    height = analysis["height"]
    marked = analysis["marked"]
    colors = analysis["colors"]
    if analysis["scene_profile"] is None:
        errors.append(
            "shape/key-count tuple is outside the declared scene-profile domain: "
            f"{height}x{analysis['width']} with {len(marked)} keys"
        )
    if len(marked) < 2:
        errors.append("need at least two non-zero row keys")
    if len(marked) >= height:
        errors.append("need at least one unmarked row")
    if len(colors) != len(set(colors)):
        errors.append("row-key colors must be distinct")
    if analysis["palette_kind"] is None:
        errors.append("row-key palette is outside the declared palette domain")
    if analysis["body_nonzero"]:
        errors.append(
            "non-zero cells outside column 0: "
            f"{analysis['body_nonzero'][:3]}"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the exact public shape/key-count/palette envelope."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    analysis = _analyze(grid)
    reasons: list[str] = []
    if (analysis["height"], analysis["width"]) not in {(5, 6), (6, 7), (6, 8)}:
        reasons.append(
            f"shape {analysis['height']}x{analysis['width']} is outside canonical profiles"
        )
    if len(analysis["marked"]) != 3:
        reasons.append(f"canonical inputs have 3 row keys, found {len(analysis['marked'])}")
    if analysis["palette_kind"] != "canonical":
        reasons.append("canonical inputs use colors 1..8 and never color 9")
    return reasons


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    """Generate one deterministic sparse left-edge row-key scene."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", _profile_options(difficulty))
    palette_kind = ctx.draw_choice("palette_kind", _palette_options(difficulty))
    height, width, n_keys = _SCENE_PROFILES[profile_name]

    layout_rng = ctx.draw_rng("row_layout")
    color_rng = ctx.draw_rng("row_colors")
    rows = layout_rng.sample(range(height), n_keys)
    if palette_kind == "canonical":
        colors = color_rng.sample(_CANONICAL_COLORS, n_keys)
    else:
        colors = [9, *color_rng.sample(_CANONICAL_COLORS, n_keys - 1)]
        color_rng.shuffle(colors)

    grid = full_grid(height, width, 0)
    for row, color in zip(rows, colors):
        grid[row][0] = color

    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r} but materialized "
                f"as {observed.get(axis)!r}"
            )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def rule_mirror(grid: Grid) -> Grid:
    """Python mirror used only for tests and rival discrimination."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for row in range(height):
        color = grid[row][0]
        if color != 0:
            output[row] = [color] * width
    return output


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _rival_identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _rival_first_marked_only(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, color in _marked_rows(grid)[:1]:
        output[row] = [color] * len(grid[0])
    return output


def _rival_one_color_for_marked_rows(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    marked = _marked_rows(grid)
    if not marked:
        return output
    color = marked[0][1]
    for row, _ in marked:
        output[row] = [color] * len(grid[0])
    return output


def _rival_paint_every_row(grid: Grid) -> Grid:
    marked = _marked_rows(grid)
    color = marked[0][1] if marked else 0
    return [[color] * len(grid[0]) for _ in grid]


def _rival_right_edge_keys(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    last_col = len(grid[0]) - 1
    for row in range(len(grid)):
        color = grid[row][last_col]
        if color != 0:
            output[row] = [color] * len(grid[0])
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity_marker_only": _rival_identity,
    "paint_first_marked_row_only": _rival_first_marked_only,
    "single_color_for_all_marked_rows": _rival_one_color_for_marked_rows,
    "paint_every_row": _rival_paint_every_row,
    "read_rightmost_column": _rival_right_edge_keys,
}


def _lawful(grid: Grid) -> bool:
    return not self_check(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "multiple_marked_rows": lambda grid: _lawful(grid) and len(_marked_rows(grid)) >= 2,
    "distinct_row_colors": lambda grid: _lawful(grid)
    and len({color for _, color in _marked_rows(grid)}) >= 2,
    "unmarked_rows_stay_blank": lambda grid: _lawful(grid)
    and len(_marked_rows(grid)) < len(grid),
    "left_edge_is_the_only_key_column": lambda grid: _lawful(grid)
    and all(value == 0 for row in grid for value in row[1:]),
}

WITNESS_RIVALS = {
    "multiple_marked_rows": [
        "identity_marker_only",
        "paint_first_marked_row_only",
    ],
    "distinct_row_colors": ["single_color_for_all_marked_rows"],
    "unmarked_rows_stay_blank": ["paint_every_row"],
    "left_edge_is_the_only_key_column": ["read_rightmost_column"],
}


def _pair_grid(pair: Any, key: str) -> Grid | None:
    if not isinstance(pair, dict):
        return None
    value = pair.get(key)
    return value if isinstance(value, list) else None


def _same_grid(left: Grid, right: Grid) -> bool:
    return left == right


def lesson_identifiable(demos: Sequence[Pair], query: Pair) -> list[str]:
    """Reject malformed lessons or any lesson where a named rival survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        input_grid = _pair_grid(pair, "input")
        output_grid = _pair_grid(pair, "output")
        label = "query" if index == len(demos) else f"demo {index}"
        if input_grid is None or output_grid is None:
            reasons.append(f"{label} must contain list-valued input and output grids")
            continue
        grammar_errors = self_check(input_grid)
        if grammar_errors:
            reasons.append(f"{label} input violates teaching grammar: {'; '.join(grammar_errors)}")
            continue
        truth = rule_mirror(input_grid)
        if not _same_grid(output_grid, truth):
            reasons.append(f"{label} output does not match the row-paint rule")

    valid_demos = [
        pair
        for pair in demos
        if _pair_grid(pair, "input") is not None
        and _pair_grid(pair, "output") is not None
        and not self_check(pair["input"])
        and _same_grid(pair["output"], rule_mirror(pair["input"]))
    ]
    if len(valid_demos) == len(demos):
        for name, rival in SEMANTIC_RIVALS.items():
            if all(_same_grid(rival(pair["input"]), pair["output"]) for pair in valid_demos):
                reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons
