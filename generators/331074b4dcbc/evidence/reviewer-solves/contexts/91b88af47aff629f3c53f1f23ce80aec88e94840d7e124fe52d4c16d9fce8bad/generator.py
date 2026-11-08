"""Semantic curriculum for ARC task 331074b4dcbc.

A nonzero prefix in row zero is a one-dimensional tile.  A solid cyan (8)
rectangle below that row is replaced, row by row, by the tile repeated from
the rectangle's left edge.  Everything outside the rectangle is preserved.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "331074b4dcbc"
TASK_ID = "331074b4dcbc"
VERSION = "2.0.0"
RULE_HASH = "663523cb8af9"
SUMMARY = "Repeat the top-row nonzero prefix independently across every row of the cyan rectangle."
INVARIANTS = [
    "literal zero is background",
    "row zero contains one contiguous nonzero prefix of two or three distinct colors",
    "below row zero, the only nonzero cells form one solid cyan-8 rectangle",
    "the tile may itself contain cyan 8; only rectangle cells below row zero are markers",
    "tiling starts at the rectangle's left edge and restarts on every rectangle row",
]

SCENE_PROFILES = (
    "short_left",
    "short_right",
    "short_bottom",
    "long_left",
    "long_center",
    "long_bottom",
    "marker_overlap_left",
    "marker_overlap_right",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted observable teaching profile",
        "valid": "|".join(SCENE_PROFILES),
    }
}

# (grid_h, grid_w, seed_len, seed_includes_8, rect_top, rect_left,
#  rect_height, rect_width).  Every profile has one of the exact canonical
# (height, width, palette-size) signatures.  Every profile also makes three
# otherwise-plausible shortcuts visibly wrong: tile period != rectangle
# height, rectangle-left phase != global-column phase, and row phase must reset.
_PROFILE_SPECS: dict[str, tuple[int, int, int, bool, int, int, int, int]] = {
    "short_left": (6, 12, 2, False, 1, 1, 3, 7),
    "short_right": (5, 13, 2, False, 2, 5, 3, 7),
    "short_bottom": (6, 12, 2, False, 3, 3, 3, 7),
    "long_left": (6, 12, 3, False, 1, 1, 2, 7),
    "long_center": (6, 12, 3, False, 2, 2, 2, 8),
    "long_bottom": (6, 12, 3, False, 4, 4, 2, 7),
    "marker_overlap_left": (5, 13, 3, True, 1, 1, 2, 8),
    "marker_overlap_right": (5, 13, 3, True, 3, 5, 2, 7),
}
_PROFILE_BY_SIGNATURE = {
    (height, width, seed_len, includes_8, top, left, rect_height, rect_width): name
    for name, (height, width, seed_len, includes_8, top, left, rect_height, rect_width)
    in _PROFILE_SPECS.items()
}
_PROFILE_POOLS = {
    None: SCENE_PROFILES,
    "easy": SCENE_PROFILES + ("short_left", "short_right", "marker_overlap_left") * 2,
    "medium": SCENE_PROFILES + ("long_left", "long_center", "marker_overlap_right") * 2,
    "hard": SCENE_PROFILES + ("short_bottom", "long_bottom", "marker_overlap_right") * 2,
}
_NON_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    row_zero = list(grid[0])
    prefix_end = next((index for index, value in enumerate(row_zero) if value == 0), width)
    seed = row_zero[:prefix_end]
    if any(row_zero[prefix_end:]):
        errors.append("row zero must be a contiguous nonzero prefix followed only by zeros")
    if not 2 <= len(seed) <= 3:
        errors.append("row-zero tile must contain two or three colors")
    if len(set(seed)) != len(seed):
        errors.append("row-zero tile colors must be distinct")

    below_nonzero = [
        (row_index, col_index, value)
        for row_index, row in enumerate(grid[1:], start=1)
        for col_index, value in enumerate(row)
        if value != 0
    ]
    if not below_nonzero:
        errors.append("a cyan rectangle is required below row zero")
        return result
    if any(value != 8 for _, _, value in below_nonzero):
        errors.append("every nonzero cell below row zero must be cyan 8")

    marker_cells = [(row, col) for row, col, value in below_nonzero if value == 8]
    if not marker_cells:
        errors.append("no cyan marker cells occur below row zero")
        return result
    top = min(row for row, _ in marker_cells)
    bottom = max(row for row, _ in marker_cells)
    left = min(col for _, col in marker_cells)
    right = max(col for _, col in marker_cells)
    rect_height = bottom - top + 1
    rect_width = right - left + 1
    if any(grid[row][col] != 8 for row in range(top, bottom + 1) for col in range(left, right + 1)):
        errors.append("cyan marker cells must form one solid rectangle")
    if not 2 <= rect_height <= 3:
        errors.append("teaching rectangles must be two or three rows tall")
    if not 5 <= rect_width <= 9:
        errors.append("teaching rectangles must be five through nine columns wide")
    if seed and rect_width <= len(seed):
        errors.append("rectangle width must expose at least one repeated tile color")

    signature = (
        height,
        width,
        len(seed),
        8 in seed,
        top,
        left,
        rect_height,
        rect_width,
    )
    profile = _PROFILE_BY_SIGNATURE.get(signature) if not errors else None
    facts = {
        "height": height,
        "width": width,
        "seed": tuple(seed),
        "rect": (top, left, rect_height, rect_width),
        "signature": signature,
    }
    result.update({"facts": facts, "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Fail closed on malformed or semantically ambiguous teaching scenes."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(
            f"scene profile drifted from {requested!r} to {analysis['scene_profile']!r}"
        )
    return errors


_CANONICAL_MORPHOLOGIES = {(6, 12, 4), (6, 12, 5), (5, 13, 4)}
MIN_STRICT_FRAC = 1.0


def strict_canonical_like(grid) -> list[str]:
    """Accept only lawful scenes on an exact canonical size/palette profile."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    morphology = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if morphology not in _CANONICAL_MORPHOLOGIES:
        return [f"size/palette morphology {morphology!r} is outside the canonical profiles"]
    return []


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    profile = analysis["scene_profile"]
    if profile not in SCENE_PROFILES:
        raise ValueError("grid is lawful but is not one declared scene_profile")
    return {"scene_profile": profile}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription, restricted to the teaching grammar."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    seed = analysis["facts"]["seed"]
    top, left, rect_height, rect_width = analysis["facts"]["rect"]
    out = [list(row) for row in grid]
    for row in range(top, top + rect_height):
        for col in range(left, left + rect_width):
            out[row][col] = seed[(col - left) % len(seed)]
    return out


def _paint_rectangle(grid, pattern, *, absolute_columns=False, continuous_rows=False):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    top, left, rect_height, rect_width = analysis["facts"]["rect"]
    out = [list(row) for row in grid]
    for row in range(top, top + rect_height):
        for col in range(left, left + rect_width):
            if absolute_columns:
                phase = col
            elif continuous_rows:
                phase = (row - top) * rect_width + (col - left)
            else:
                phase = col - left
            out[row][col] = pattern[phase % len(pattern)]
    return out


def _rival_rectangle_height_is_tile_period(grid):
    """Shortcut fitting canonical data: force tile period to rectangle height."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    seed = list(analysis["facts"]["seed"])
    rect_height = analysis["facts"]["rect"][2]
    period = [seed[index % len(seed)] for index in range(rect_height)]
    return _paint_rectangle(grid, period)


def _rival_global_column_phase(grid):
    """Wrong rule: phase the tile from canvas column zero, not rectangle left."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_rectangle(grid, analysis["facts"]["seed"], absolute_columns=True)


def _rival_continuous_phase_across_rows(grid):
    """Wrong rule: continue tile phase through row boundaries instead of resetting."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_rectangle(grid, analysis["facts"]["seed"], continuous_rows=True)


def _witness_seed_height_decoupling(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["facts"]["seed"]) != analysis["facts"]["rect"][2]


def _witness_local_left_phase(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    seed_len = len(analysis["facts"]["seed"])
    rect_left = analysis["facts"]["rect"][1]
    return rect_left % seed_len != 0


def _witness_row_phase_reset(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    seed_len = len(analysis["facts"]["seed"])
    _, _, rect_height, rect_width = analysis["facts"]["rect"]
    return rect_height > 1 and rect_width % seed_len != 0


SEMANTIC_RIVALS = {
    "rectangle_height_is_tile_period": _rival_rectangle_height_is_tile_period,
    "global_column_phase": _rival_global_column_phase,
    "continuous_phase_across_rows": _rival_continuous_phase_across_rows,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "rectangle_height_is_tile_period": _rival_rectangle_height_is_tile_period,
}
SEMANTIC_WITNESSES = {
    "seed_length_decoupled_from_rectangle_height": _witness_seed_height_decoupling,
    "rectangle_phase_starts_at_its_left_edge": _witness_local_left_phase,
    "each_rectangle_row_restarts_phase": _witness_row_phase_reset,
}
WITNESS_RIVALS = {
    "seed_length_decoupled_from_rectangle_height": "rectangle_height_is_tile_period",
    "rectangle_phase_starts_at_its_left_edge": "global_column_phase",
    "each_rectangle_row_restarts_phase": "continuous_phase_across_rows",
}


EXAMPLES_NEEDED = 2


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named plausible rival survives its demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the selected tiling rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons
    if "output" in query and query.get("output") != query_answer:
        reasons.append("query output disagrees with the selected tiling rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output")
            for demo in demos
            if "input" in demo
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _PROFILE_POOLS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
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
    profile = ctx.draw_choice("scene_profile", _PROFILE_POOLS[difficulty])
    height, width, seed_len, includes_8, top, left, rect_height, rect_width = _PROFILE_SPECS[profile]

    palette_rng = ctx.draw_rng("seed_palette")
    if includes_8:
        seed_colors = [8, *palette_rng.sample(_NON_MARKER_COLORS, seed_len - 1)]
        palette_rng.shuffle(seed_colors)
    else:
        seed_colors = palette_rng.sample(_NON_MARKER_COLORS, seed_len)

    grid = full_grid(height, width, 0)
    for col, color in enumerate(seed_colors):
        grid[0][col] = color
    for row in range(top, top + rect_height):
        for col in range(left, left + rect_width):
            grid[row][col] = 8

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile!r} -> {analysis}")
    return grid
