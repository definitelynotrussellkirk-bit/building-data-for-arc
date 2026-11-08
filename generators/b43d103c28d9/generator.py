"""Generator for ARC task 3906de3d / content hash b43d103c28d9.

The authoritative rule packs each column's non-zero cells upward while
preserving their top-to-bottom order.  The official inputs are 10x10 scenes
with a color-1 histogram hanging from the top and color-2 bars rising from the
bottom.  This generator keeps that linked morphology as a scheduled prior and
adds two controlled witnesses that disambiguate the general rule from
canonical-only shortcuts:

* ``floating_histograms`` leaves empty rows above the upper layer, so moving
  only the lower object is wrong.
* ``interleaved_columns`` creates A-B-A column order, so sorting by color or
  treating the colors as fixed semantic roles is wrong.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b43d103c28d9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a2f07dce6b36"

SUMMARY = (
    "Pack every column's non-zero cells at the top in their original vertical "
    "order. Ordinary lessons retain the official two-layer histogram family: "
    "one foreground layer spans a contiguous set of columns above a second "
    "foreground layer, with empty vertical gaps that disappear in the output. "
    "A rolling four-sample schedule also includes a floating upper layer and "
    "an interleaved A-B-A column, refuting lower-object-only, fixed-color, and "
    "numeric-sort shortcuts."
)
INVARIANTS = [
    "square 8..14 grid with background 0 and exactly two distinct foreground colors",
    "the first non-zero color is consistent across occupied columns",
    "foreground support spans a contiguous interval of at least three columns",
    "some column contains multiple non-zero cells and at least one zero gap",
    "the authoritative gravity-up result differs from the input",
    "every four consecutive samples include canonical, floating, and interleaved witnesses",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SCENE_TYPES = (
    "canonical_histograms",
    "floating_histograms",
    "interleaved_columns",
)
PALETTE_MODES = ("canonical", "swapped", "random_pair")
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "floating_upper",
    "interleaved_order",
    "histogram_variant",
)

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_size": {
        "type": "int",
        "default": "10 for canonical anchors; otherwise difficulty-banded",
        "valid": "8..14",
    },
    "scene_type": {
        "type": "str",
        "default": "four-sample schedule",
        "valid": "|".join(SCENE_TYPES),
    },
    "palette_mode": {
        "type": "str",
        "default": "canonical/canonical/swapped/random_pair schedule",
        "valid": "|".join(PALETTE_MODES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Complete linked morphology signatures from every official train/test input.
# A signature stores the left edge of the upper histogram plus the multisets of
# upper and lower column heights.  Generation shuffles those heights across the
# lawful support instead of replaying literal coordinates.
_CANONICAL_PROFILES = (
    (2, (1, 2, 4, 4, 4, 5, 5), (1, 4)),
    (2, (2, 4, 4, 4, 4), (3,)),
    (1, (1, 2, 3, 3, 4, 4, 4, 4, 4), (2, 3, 3, 4)),
    (1, (1, 1, 2, 2, 3, 4, 4, 5, 5), (1, 2, 3, 4, 6)),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic four-sample teaching slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis_choice(ctx, overrides, label, options, default):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, list(options))
    return ctx.draw_choice(label, [default])


def _draw_grid_size(ctx, overrides, profile: str, band: str) -> int:
    if overrides.get("grid_size") is not None:
        return ctx.draw_int("grid_size", 8, 14)
    if profile == "canonical_anchor":
        return ctx.draw_choice("grid_size", [10])
    choices = {
        "easy": [8, 9, 10],
        "medium": [10, 11, 12],
        "hard": [10, 12, 13, 14],
    }[band]
    return ctx.draw_choice("grid_size", choices)


def _scheduled_scene(profile: str) -> str:
    return {
        "canonical_anchor": "canonical_histograms",
        "floating_upper": "floating_histograms",
        "interleaved_order": "interleaved_columns",
        "histogram_variant": "canonical_histograms",
    }[profile]


def _scheduled_palette(profile: str) -> str:
    return {
        "canonical_anchor": "canonical",
        "floating_upper": "canonical",
        "interleaved_order": "swapped",
        "histogram_variant": "random_pair",
    }[profile]


def _colors(ctx, palette_mode: str) -> tuple[int, int]:
    if palette_mode == "canonical":
        return 1, 2
    if palette_mode == "swapped":
        return 2, 1
    # Excluding 1 and 2 makes the mode recoverable from the returned grid.
    return tuple(ctx.draw_distinct_colors(
        "random_pair", n=2, exclude={0, 1, 2}
    ))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, difficulty=band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    size = _draw_grid_size(ctx, overrides, profile, band)
    scene_type = _draw_axis_choice(
        ctx, overrides, "scene_type", SCENE_TYPES, _scheduled_scene(profile)
    )
    palette_mode = _draw_axis_choice(
        ctx, overrides, "palette_mode", PALETTE_MODES,
        _scheduled_palette(profile),
    )
    upper_color, lower_color = _colors(ctx, palette_mode)
    rng = ctx.draw_rng("geometry")

    if (
        profile == "canonical_anchor"
        and size == 10
        and scene_type == "canonical_histograms"
        and palette_mode == "canonical"
    ):
        grid = _draw_strict_canonical_profile(
            size, upper_color, lower_color, rng
        )
    elif scene_type == "canonical_histograms":
        grid = _draw_histograms(
            size, upper_color, lower_color, rng, band=band, floating=False
        )
    elif scene_type == "floating_histograms":
        grid = _draw_histograms(
            size, upper_color, lower_color, rng, band=band, floating=True
        )
    elif scene_type == "interleaved_columns":
        grid = _draw_interleaved(size, upper_color, lower_color, rng, band=band)
    else:  # guarded by draw_choice, retained as a loud defensive branch
        raise ValueError(f"unsupported scene_type: {scene_type!r}")

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator produced invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_size": size,
        "scene_type": scene_type,
        "palette_mode": palette_mode,
    }
    if observed != expected:
        raise AssertionError(
            f"observable axis mismatch: expected {expected}, observed {observed}"
        )
    return grid


def _draw_strict_canonical_profile(size, upper_color, lower_color, rng):
    if size != 10 or (upper_color, lower_color) != (1, 2):
        raise ValueError("strict canonical profiles require 10x10 colors 1 above 2")
    start, upper_multiset, lower_multiset = rng.choice(_CANONICAL_PROFILES)
    upper_heights = list(upper_multiset)
    rng.shuffle(upper_heights)
    support = list(range(start, start + len(upper_heights)))

    # Assign the lower multiset only to columns with at least a three-row gap,
    # matching every official input.  The multisets remain linked even though
    # their horizontal assignment varies.
    lower_heights = list(lower_multiset)
    for _ in range(256):
        rng.shuffle(lower_heights)
        lower_cols = rng.sample(support, len(lower_heights))
        if all(
            upper_heights[c - start] + lh <= size - 3
            for c, lh in zip(lower_cols, lower_heights)
        ):
            break
    else:
        raise AssertionError("could not place linked canonical lower profile")

    grid = full_grid(size, size, 0)
    for c, height in zip(support, upper_heights):
        for r in range(height):
            grid[r][c] = upper_color
    for c, height in zip(lower_cols, lower_heights):
        for r in range(size - height, size):
            grid[r][c] = lower_color
    return grid


def _draw_histograms(size, upper_color, lower_color, rng, *, band, floating):
    grid = full_grid(size, size, 0)
    width_bounds = {
        "easy": (max(3, size // 2), max(4, size - 3)),
        "medium": (max(4, size // 2), max(5, size - 2)),
        "hard": (max(5, size - 5), size - 1),
    }[band]
    lo, hi = width_bounds
    hi = min(hi, size - 1)
    lo = min(lo, hi)
    width = rng.randint(lo, hi)
    start = rng.randint(0, size - width)
    support = list(range(start, start + width))

    top_offset = rng.randint(1, min(2, size // 4)) if floating else 0
    max_upper = max(2, size // 2 - top_offset)
    upper_heights = [rng.randint(1, max_upper) for _ in support]
    # Keep the upper color horizontally connected at its first row.
    upper_heights[0] = max(2, upper_heights[0])
    upper_heights[-1] = max(2, upper_heights[-1])

    max_lower_cols = min(width, {"easy": 2, "medium": 4, "hard": 5}[band])
    lower_count = rng.randint(1, max_lower_cols)
    candidates = [
        c for c in support
        if top_offset + upper_heights[c - start] <= size - 2
    ]
    if len(candidates) < lower_count:
        candidates = support[:]
        upper_heights = [min(h, size - top_offset - 2) for h in upper_heights]
    lower_cols = rng.sample(candidates, lower_count)

    lower_heights: dict[int, int] = {}
    for c in lower_cols:
        room = size - (top_offset + upper_heights[c - start]) - 1
        lower_heights[c] = rng.randint(1, max(1, min(room, size // 2 + 1)))

    for c, height in zip(support, upper_heights):
        for r in range(top_offset, top_offset + height):
            grid[r][c] = upper_color
    for c, height in lower_heights.items():
        for r in range(size - height, size):
            grid[r][c] = lower_color

    # Ensure two columns expose different gap sizes, distinguishing per-column
    # packing from deleting whole empty rows globally.
    if lower_count >= 2:
        c0, c1 = lower_cols[:2]
        gap0 = size - lower_heights[c0] - (
            top_offset + upper_heights[c0 - start]
        )
        gap1 = size - lower_heights[c1] - (
            top_offset + upper_heights[c1 - start]
        )
        if gap0 == gap1:
            idx = c1 - start
            if upper_heights[idx] > 1:
                upper_heights[idx] -= 1
            elif lower_heights[c1] > 1:
                lower_heights[c1] -= 1
            # Repaint after the deterministic adjustment.
            grid = full_grid(size, size, 0)
            for c, height in zip(support, upper_heights):
                for r in range(top_offset, top_offset + height):
                    grid[r][c] = upper_color
            for c, height in lower_heights.items():
                for r in range(size - height, size):
                    grid[r][c] = lower_color
    return grid


def _draw_interleaved(size, upper_color, lower_color, rng, *, band):
    grid = full_grid(size, size, 0)
    width = rng.randint(
        {"easy": 3, "medium": 4, "hard": 5}[band],
        min(size - 1, {"easy": 5, "medium": 7, "hard": size - 1}[band]),
    )
    start = rng.randint(0, size - width)
    support = list(range(start, start + width))
    anchor_row = rng.randint(1, min(2, size - 5))
    repeated_col = rng.choice(support)

    for c in support:
        grid[anchor_row][c] = upper_color
        middle = rng.randint(anchor_row + 2, size - 3)
        grid[middle][c] = lower_color
        if c == repeated_col or rng.random() < 0.45:
            bottom = rng.randint(middle + 2, size - 1)
            grid[bottom][c] = upper_color

    # At least one column must carry A-B-A, and at least one pair of columns
    # must use different vertical gaps so the operation is visibly columnwise.
    if grid[size - 1][repeated_col] == 0:
        grid[size - 1][repeated_col] = upper_color
    return grid


def _gravity_up(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def _compressed_nonzero_colors(grid, c):
    sequence: list[int] = []
    for row in grid:
        value = row[c]
        if value != 0 and (not sequence or sequence[-1] != value):
            sequence.append(value)
    return tuple(sequence)


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    info["grid_size"] = h
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if h != w:
        errors.append(f"grid must be square, got {h}x{w}")
    if not (8 <= h <= 14):
        errors.append(f"grid size must be 8..14, got {h}")
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("all cells must be integer colors 0..9")
        return info, errors

    palette = sorted({value for row in grid for value in row})
    info["palette"] = tuple(palette)
    if 0 not in palette:
        errors.append("background color 0 must be present")
    foreground = [value for value in palette if value != 0]
    if len(foreground) != 2:
        errors.append(
            f"expected exactly two foreground colors, found {foreground}"
        )
        return info, errors

    occupied = [
        c for c in range(w) if any(grid[r][c] != 0 for r in range(h))
    ]
    if len(occupied) < 3:
        errors.append("foreground must occupy at least three columns")
        return info, errors
    if occupied != list(range(min(occupied), max(occupied) + 1)):
        errors.append("foreground column support must be contiguous")

    first_colors = {
        next(grid[r][c] for r in range(h) if grid[r][c] != 0)
        for c in occupied
    }
    if len(first_colors) != 1:
        errors.append("occupied columns must share one first non-zero color")
        return info, errors
    upper_color = next(iter(first_colors))
    lower_color = next(value for value in foreground if value != upper_color)
    info.update({
        "upper_color": upper_color,
        "lower_color": lower_color,
        "occupied_columns": tuple(occupied),
    })
    if (upper_color, lower_color) == (1, 2):
        palette_mode = "canonical"
    elif (upper_color, lower_color) == (2, 1):
        palette_mode = "swapped"
    elif upper_color not in (1, 2) and lower_color not in (1, 2):
        palette_mode = "random_pair"
    else:
        errors.append("foreground colors do not encode a declared palette_mode")
        return info, errors
    info["palette_mode"] = palette_mode

    upper_support: list[int] = []
    lower_support: list[int] = []
    upper_heights: list[int] = []
    lower_heights: list[int] = []
    gaps: list[int] = []
    repeated = False
    upper_starts: list[int] = []
    lower_ends: list[int] = []
    max_nonzero = 0

    for c in occupied:
        positions = [r for r in range(h) if grid[r][c] != 0]
        max_nonzero = max(max_nonzero, len(positions))
        colors = _compressed_nonzero_colors(grid, c)
        if len(colors) >= 3 and colors[0] == colors[2]:
            repeated = True
        upper_rows = [r for r in positions if grid[r][c] == upper_color]
        lower_rows = [r for r in positions if grid[r][c] == lower_color]
        if upper_rows:
            upper_support.append(c)
            upper_heights.append(len(upper_rows))
            upper_starts.append(min(upper_rows))
        if lower_rows:
            lower_support.append(c)
            lower_heights.append(len(lower_rows))
            lower_ends.append(max(lower_rows))
        if lower_rows and not upper_rows:
            errors.append(f"column {c} contains lower color without upper color")
        if upper_rows and lower_rows:
            if min(lower_rows) <= min(upper_rows):
                errors.append(f"column {c} does not begin with the upper color")
            gaps.append(min(lower_rows) - max(upper_rows) - 1)

    if max_nonzero < 2:
        errors.append("no column contains multiple non-zero cells")
    if grid == _gravity_up(grid):
        errors.append("grid is already gravity-up packed (identity lesson)")

    if repeated:
        scene_type = "interleaved_columns"
    else:
        if not lower_support:
            errors.append("histogram scene has no lower-color bars")
            scene_type = "canonical_histograms"
        elif all(start == 0 for start in upper_starts) and all(
            end == h - 1 for end in lower_ends
        ):
            scene_type = "canonical_histograms"
        elif len(set(upper_starts)) == 1 and upper_starts[0] > 0 and all(
            end == h - 1 for end in lower_ends
        ):
            scene_type = "floating_histograms"
        else:
            errors.append("grid is not one of the declared scene grammars")
            scene_type = "unknown"

    if scene_type != "interleaved_columns":
        for c in occupied:
            for color in (upper_color, lower_color):
                rows = [r for r in range(h) if grid[r][c] == color]
                if rows and rows != list(range(min(rows), max(rows) + 1)):
                    errors.append(
                        f"color {color} in column {c} is not one contiguous run"
                    )
        if set(lower_support) - set(upper_support):
            errors.append("lower-color support must be a subset of upper support")
        if any(gap < 1 for gap in gaps):
            errors.append("upper and lower runs must have at least one zero gap")
    else:
        if not any(
            len(_compressed_nonzero_colors(grid, c)) >= 3
            for c in occupied
        ):
            errors.append("interleaved scene lacks an A-B-A column")

    info.update({
        "scene_type": scene_type,
        "upper_support": tuple(upper_support),
        "lower_support": tuple(lower_support),
        "upper_heights": tuple(upper_heights),
        "lower_heights": tuple(lower_heights),
        "gaps": tuple(gaps),
        "max_nonzero_per_column": max_nonzero,
    })
    return info, errors


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyse(grid)[1]


def _strict_signature(info: dict[str, Any]):
    occupied = info["occupied_columns"]
    return (
        occupied[0],
        tuple(sorted(info["upper_heights"])),
        tuple(sorted(info["lower_heights"])),
    )


def strict_canonical_like(grid) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if info["grid_size"] != 10:
        reasons.append("official grid size is 10x10")
    if info["palette_mode"] != "canonical":
        reasons.append("official roles use color 1 above color 2")
    if info["scene_type"] != "canonical_histograms":
        reasons.append("official inputs are top/bottom histogram scenes")
    if _strict_signature(info) not in set(_CANONICAL_PROFILES):
        reasons.append("linked upper/lower height profile is outside the official set")
    if info["gaps"] and min(info["gaps"]) < 3:
        reasons.append("official overlapping columns keep at least three blank rows")
    return reasons


def _witness_strict(grid):
    return strict_canonical_like(grid) == []


def _witness_floating(grid):
    info, errors = _analyse(grid)
    return not errors and info["scene_type"] == "floating_histograms"


def _witness_interleaved(grid):
    info, errors = _analyse(grid)
    return not errors and info["scene_type"] == "interleaved_columns"


def _witness_nonfixed_palette(grid):
    info, errors = _analyse(grid)
    return (
        not errors
        and info["palette_mode"] != "canonical"
        and _rival_sort_numeric(grid) != _gravity_up(grid)
    )


def _witness_multi_cell_column(grid):
    info, errors = _analyse(grid)
    return not errors and info["max_nonzero_per_column"] >= 3


def _witness_column_specific_gaps(grid):
    info, errors = _analyse(grid)
    return (
        not errors
        and len(set(info["gaps"])) >= 2
        and _rival_delete_empty_rows(grid) != _gravity_up(grid)
    )


SEMANTIC_WITNESSES = {
    "strict_official_linked_profile": _witness_strict,
    "floating_upper_layer_must_move": _witness_floating,
    "interleaved_order_must_be_preserved": _witness_interleaved,
    "foreground_colors_are_not_fixed_roles": _witness_nonfixed_palette,
    "multiple_cells_per_column_are_preserved": _witness_multi_cell_column,
    "gaps_are_removed_per_column_not_globally": _witness_column_specific_gaps,
}


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_sort_numeric(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        values = sorted(grid[r][c] for r in range(h) if grid[r][c] != 0)
        for r, value in enumerate(values):
            out[r][c] = value
    return out


def _rival_move_lower_only(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    lower = info["lower_color"]
    out = [list(row) for row in grid]
    for c in range(w):
        count = sum(grid[r][c] == lower for r in range(h))
        for r in range(h):
            if out[r][c] == lower:
                out[r][c] = 0
        free = [r for r in range(h) if out[r][c] == 0]
        for r in free[:count]:
            out[r][c] = lower
    return out


def _rival_one_cell_per_column(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        for r in range(h):
            if grid[r][c] != 0:
                out[0][c] = grid[r][c]
                break
    return out


def _rival_delete_empty_rows(grid):
    h, w = len(grid), len(grid[0])
    rows = [list(row) for row in grid if any(value != 0 for value in row)]
    rows.extend([[0 for _ in range(w)] for _ in range(h - len(rows))])
    return rows


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "sort_nonzeros_by_numeric_color": _rival_sort_numeric,
    "move_only_the_lower_layer": _rival_move_lower_only,
    "keep_only_one_cell_per_column": _rival_one_cell_per_column,
    "delete_globally_empty_rows": _rival_delete_empty_rows,
}
WITNESS_RIVALS = {
    "strict_official_linked_profile": ["identity"],
    "floating_upper_layer_must_move": ["move_only_the_lower_layer"],
    "interleaved_order_must_be_preserved": ["sort_nonzeros_by_numeric_color"],
    "foreground_colors_are_not_fixed_roles": ["sort_nonzeros_by_numeric_color"],
    "multiple_cells_per_column_are_preserved": ["keep_only_one_cell_per_column"],
    "gaps_are_removed_per_column_not_globally": ["delete_globally_empty_rows"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "sort_nonzeros_by_numeric_color": _rival_sort_numeric,
    "move_only_the_lower_layer": _rival_move_lower_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    scene_types: set[str] = set()
    canonical_seen = False
    sort_killed = False
    lower_only_killed = False
    global_rows_killed = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = _gravity_up(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not columnwise stable packing")
        scene_types.add(info["scene_type"])
        canonical_seen |= strict_canonical_like(pair["input"]) == []
        sort_killed |= _rival_sort_numeric(pair["input"]) != expected
        lower_only_killed |= _rival_move_lower_only(pair["input"]) != expected
        global_rows_killed |= _rival_delete_empty_rows(pair["input"]) != expected

    required_scenes = set(SCENE_TYPES)
    if scene_types != required_scenes:
        reasons.append(
            f"demonstrations cover scene types {sorted(scene_types)}, "
            f"need {sorted(required_scenes)}"
        )
    if not canonical_seen:
        reasons.append("demonstrations lack a strict official linked profile")
    if not sort_killed:
        reasons.append("numeric color sorting remains consistent with all demos")
    if not lower_only_killed:
        reasons.append("moving only the lower layer remains consistent with all demos")
    if not global_rows_killed:
        reasons.append("deleting globally empty rows remains consistent with all demos")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyse(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != _gravity_up(query["input"]):
            reasons.append("query output does not match the authoritative transform")
    return reasons
