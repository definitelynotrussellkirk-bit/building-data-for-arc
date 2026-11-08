"""Generator for ARC task 40e85135fbf8: equality matrix from headers.

The first row (excluding the top-left zero) contains column headers and the
first column (excluding the top-left zero) contains row headers.  The Racket
oracle drops those headers and emits the row-header color exactly where it is
equal to the corresponding column-header color; every mismatch is zero.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40e85135fbf8"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "5d3d67439533"

SUMMARY = (
    "Read row headers from column 0 and column headers from row 0, discard the "
    "header row/column, and build their colored equality matrix: output[r][c] "
    "is the shared nonzero header color when the two headers are equal, else 0."
)

INVARIANTS = [
    "0 is the background and the top-left cell is 0",
    "all remaining cells in row 0 and column 0 are nonzero headers",
    "the input interior is entirely 0",
    "ordinary draws use one of the three canonical input/output shapes",
    "ordinary draws use exactly three nonzero colors and at least two shared colors",
    "every ordinary draw has both equality matches and inequality mismatches",
    "each header axis repeats a shared color, exposing cross-product multiplicity",
    "every three consecutive samples contain canonical, row-gap, and column-gap scenes",
    "every six consecutive samples expose a nonmaximum private color on each axis",
]

EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0

SHAPE_PROFILES = {
    "r4_c5": (4, 5),
    "r5_c4": (5, 4),
    "r6_c5": (6, 5),
}
SCENE_PROFILES = ("canonical", "row_gap", "col_gap")
PALETTE_KINDS = ("low", "high", "mixed")
PALETTES = {
    "low": (1, 2, 3),
    "high": (7, 8, 9),
}
MIXED_PALETTES = tuple(
    palette for palette in combinations(range(1, 10), 3)
    if palette not in PALETTES.values()
)
PALETTE_SCHEDULE = ("low", "mixed", "high", "mixed")
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "shape_profile": {
        "type": "str",
        "default": "sample-index schedule over all canonical shapes",
        "valid": "r4_c5|r5_c4|r6_c5",
    },
    "scene_profile": {
        "type": "str",
        "default": "canonical|row_gap|col_gap sliding-window schedule",
        "valid": "canonical|row_gap|col_gap",
    },
    "palette_kind": {
        "type": "str",
        "default": "low|mixed|high|mixed sliding-window schedule",
        "valid": "low|high|mixed",
    },
}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the three-step lesson schedule exposed to the semantic gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str,
                      overrides: dict[str, Any]) -> str:
    """Record a scheduled ordinary value while preserving exact overrides."""
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _structural_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid is not a non-empty list"]
    if not all(isinstance(row, list) for row in grid):
        return ["grid rows must be lists"]
    width = len(grid[0])
    if width == 0:
        return ["grid has zero columns"]
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]

    height = len(grid)
    errors: list[str] = []
    if height < 2 or width < 2:
        errors.append(f"grid too small for two header axes: {height}x{width}")
        return errors
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")

    bad_values = [
        (row, col, value)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append(f"{len(bad_values)} cell(s) are not integer colors in 0..9")
        return errors

    if grid[0][0] != 0:
        errors.append("top-left corner must be background 0")
    zero_columns = [col for col in range(1, width) if grid[0][col] == 0]
    if zero_columns:
        errors.append(f"{len(zero_columns)} zero column-header(s)")
    zero_rows = [row for row in range(1, height) if grid[row][0] == 0]
    if zero_rows:
        errors.append(f"{len(zero_rows)} zero row-header(s)")
    interior = [
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if grid[row][col] != 0
    ]
    if interior:
        errors.append(f"{len(interior)} nonzero interior cell(s)")
    return errors


def _profile_from_sets(row_colors: set[int], col_colors: set[int]) -> str | None:
    row_only = row_colors - col_colors
    col_only = col_colors - row_colors
    if not row_only and not col_only:
        return "canonical"
    if row_only and not col_only:
        return "row_gap"
    if col_only and not row_only:
        return "col_gap"
    return None


def _palette_kind(colors: set[int]) -> str | None:
    for name, palette in PALETTES.items():
        if colors == set(palette):
            return name
    return "mixed" if len(colors) == 3 else None


def _shape_profile(height: int, width: int) -> str | None:
    dims = (height - 1, width - 1)
    for name, expected in SHAPE_PROFILES.items():
        if dims == expected:
            return name
    return None


def _analysis(grid) -> dict[str, Any]:
    errors = _structural_errors(grid)
    if errors:
        return {"errors": errors}

    row_headers = tuple(grid[row][0] for row in range(1, len(grid)))
    col_headers = tuple(grid[0][col] for col in range(1, len(grid[0])))
    row_counts = Counter(row_headers)
    col_counts = Counter(col_headers)
    row_colors = set(row_headers)
    col_colors = set(col_headers)
    shared = row_colors & col_colors
    row_only = row_colors - col_colors
    col_only = col_colors - row_colors
    match_cells = sum(row_counts[color] * col_counts[color] for color in shared)
    total_cells = len(row_headers) * len(col_headers)

    return {
        "errors": [],
        "row_headers": row_headers,
        "col_headers": col_headers,
        "row_counts": row_counts,
        "col_counts": col_counts,
        "row_colors": row_colors,
        "col_colors": col_colors,
        "colors": row_colors | col_colors,
        "shared": shared,
        "row_only": row_only,
        "col_only": col_only,
        "match_cells": match_cells,
        "mismatch_cells": total_cells - match_cells,
        "scene_profile": _profile_from_sets(row_colors, col_colors),
        "palette_kind": _palette_kind(row_colors | col_colors),
        "shape_profile": _shape_profile(len(grid), len(grid[0])),
        "repeated_shared_rows": any(row_counts[color] >= 2 for color in shared),
        "repeated_shared_cols": any(col_counts[color] >= 2 for color in shared),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority grammar without imposing curriculum-only gaps."""
    del difficulty, meta
    return _structural_errors(grid)


def strict_canonical_like(grid) -> list[str]:
    """Validate the task-linked teaching manifold used by ordinary draws."""
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["shape_profile"] is None:
        errors.append("shape is outside the three canonical input/output profiles")
    if len(analysis["colors"]) != 3:
        errors.append("strict scenes must use exactly three nonzero header colors")
    if analysis["scene_profile"] is None:
        errors.append("both header axes contain private colors (unsupported dual-gap scene)")
    if len(analysis["shared"]) < 2:
        errors.append("fewer than two shared header colors")
    if analysis["match_cells"] == 0:
        errors.append("no equality match cells")
    if analysis["mismatch_cells"] == 0:
        errors.append("no inequality mismatch cells")
    if not analysis["repeated_shared_rows"]:
        errors.append("no shared color repeats on the row-header axis")
    if not analysis["repeated_shared_cols"]:
        errors.append("no shared color repeats on the column-header axis")
    return errors


def _fill_and_shuffle(base: Iterable[int], length: int, choices: tuple[int, ...], rng) -> list[int]:
    values = list(base)
    if len(values) > length:
        raise ValueError(f"header basis of {len(values)} cells does not fit length {length}")
    while len(values) < length:
        values.append(rng.choice(choices))
    rng.shuffle(values)
    return values


def _build_headers(scene_profile: str, colors: tuple[int, int, int],
                   n_rows: int, n_cols: int, rng) -> tuple[list[int], list[int]]:
    first, second, third = colors
    if scene_profile == "canonical":
        # Every color is shared; the extra copy on each axis makes multiplicity
        # observable rather than reducing the task to a set-membership lookup.
        row_base = (first, second, third, first)
        col_base = (first, second, third, second)
        row_choices = col_choices = colors
    elif scene_profile == "row_gap":
        # `third` has no column-header counterpart, so its output row is zero.
        row_base = (first, second, third, first)
        col_base = (first, second, first, second)
        row_choices = colors
        col_choices = (first, second)
    elif scene_profile == "col_gap":
        # `third` has no row-header counterpart, so its output column is zero.
        row_base = (first, second, first, second)
        col_base = (first, second, third, second)
        row_choices = (first, second)
        col_choices = colors
    else:  # guarded by draw_choice, retained as a loud local invariant
        raise ValueError(f"unknown scene_profile: {scene_profile!r}")

    return (
        _fill_and_shuffle(row_base, n_rows, row_choices, rng),
        _fill_and_shuffle(col_base, n_cols, col_choices, rng),
    )


def _color_roles(ctx, palette_kind: str, scene_profile: str,
                 seed: int, sample_index: int) -> tuple[int, int, int]:
    """Vary color identity and ensure both gap directions teach literal equality.

    Each axis's private rank cycles through min/middle/max on successive scene
    cycles. Six consecutive draws include two of each gap, hence at least one
    nonmaximum private color on each axis. Shared-color order is independent.
    """
    palette = (ctx.draw_rng("mixed_palette").choice(MIXED_PALETTES)
               if palette_kind == "mixed" else PALETTES[palette_kind])
    rng = ctx.draw_rng("color_roles")
    if scene_profile == "canonical":
        colors = list(palette)
        rng.shuffle(colors)
        return tuple(colors)
    offset = 0 if scene_profile == "row_gap" else 2
    private_rank = (int(seed) + int(sample_index) // 3 + offset) % 3
    private_color = sorted(palette)[private_rank]
    shared = [color for color in palette if color != private_color]
    rng.shuffle(shared)
    return shared[0], shared[1], private_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket rule owns output."""
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    shape_names = tuple(SHAPE_PROFILES)
    shape_scheduled = shape_names[(int(sample_index) + int(seed) % 3) % len(shape_names)]
    scene_scheduled = schedule_profile(seed, sample_index, band)
    palette_scheduled = PALETTE_SCHEDULE[
        (int(sample_index) + int(seed)) % len(PALETTE_SCHEDULE)
    ]

    shape_profile = _scheduled_choice(
        ctx, "shape_profile", shape_names, shape_scheduled, overrides
    )
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, scene_scheduled, overrides
    )
    palette_kind = _scheduled_choice(
        ctx, "palette_kind", PALETTE_KINDS, palette_scheduled, overrides
    )

    n_rows, n_cols = SHAPE_PROFILES[shape_profile]
    colors = _color_roles(ctx, palette_kind, scene_profile, seed, sample_index)
    row_headers, col_headers = _build_headers(
        scene_profile,
        colors,
        n_rows,
        n_cols,
        ctx.draw_rng(f"headers:{band}"),
    )

    grid = full_grid(n_rows + 1, n_cols + 1, 0)
    for col, color in enumerate(col_headers, start=1):
        grid[0][col] = color
    for row, color in enumerate(row_headers, start=1):
        grid[row][0] = color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("constructed invalid equality-header scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "shape_profile": shape_profile,
        "scene_profile": scene_profile,
        "palette_kind": palette_kind,
    }
    if observed != requested:
        raise AssertionError(f"axis observation mismatch: requested={requested}, observed={observed}")
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact generated axis from the returned grid alone."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    result = {
        "shape_profile": analysis["shape_profile"],
        "scene_profile": analysis["scene_profile"],
        "palette_kind": analysis["palette_kind"],
    }
    missing = [name for name, value in result.items() if value is None]
    if missing:
        raise ValueError(f"grid does not expose declared axis/axes: {missing}")
    return result


def rule_mirror(grid) -> list[list[int]]:
    """Test-only semantic mirror; the selected Racket program remains authority."""
    errors = _structural_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    row_headers = [grid[row][0] for row in range(1, len(grid))]
    col_headers = list(grid[0][1:])
    return [
        [row_color if row_color == col_color and row_color != 0 else 0
         for col_color in col_headers]
        for row_color in row_headers
    ]


# Plausible wrong extensions.  The first two fit every public canonical pair
# because all public row/column colors are shared; generated gap scenes kill
# those assumptions.  The latter two expose multiplicity shortcuts.
def _rival_row_headers_must_match(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    col_colors = set(grid[0][1:])
    width = len(output[0])
    row_headers = [grid[index][0] for index in range(1, len(grid))]
    for row, color in enumerate(row_headers):
        if color not in col_colors:
            output[row][row % width] = color
    return output


def _rival_col_headers_must_match(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    row_colors = {grid[row][0] for row in range(1, len(grid))}
    height = len(output)
    for col, color in enumerate(grid[0][1:]):
        if color not in row_colors:
            output[col % height][col] = color
    return output


def _rival_first_matching_column_only(grid) -> list[list[int]]:
    row_headers = [grid[row][0] for row in range(1, len(grid))]
    col_headers = list(grid[0][1:])
    output = [[0 for _ in col_headers] for _ in row_headers]
    for row, color in enumerate(row_headers):
        if color in col_headers:
            output[row][col_headers.index(color)] = color
    return output


def _rival_first_row_of_each_color_only(grid) -> list[list[int]]:
    row_headers = [grid[row][0] for row in range(1, len(grid))]
    col_headers = list(grid[0][1:])
    output = [[0 for _ in col_headers] for _ in row_headers]
    seen: set[int] = set()
    for row, color in enumerate(row_headers):
        if color in seen:
            continue
        seen.add(color)
        for col, top in enumerate(col_headers):
            if color == top:
                output[row][col] = color
    return output


def _header_ranks(grid):
    rows = [row[0] for row in grid[1:]]
    cols = list(grid[0][1:])
    row_ranks = {color: rank for rank, color in enumerate(sorted(set(rows)))}
    col_ranks = {color: rank for rank, color in enumerate(sorted(set(cols)))}
    return rows, cols, row_ranks, col_ranks


def _rival_ordinal_header_rank(grid) -> list[list[int]]:
    """Match each axis's sorted color ranks instead of literal color identity."""
    rows, cols, row_ranks, col_ranks = _header_ranks(grid)
    return [[row if row_ranks[row] == col_ranks[col] else 0 for col in cols]
            for row in rows]


def _rival_row_rank_fallback(grid) -> list[list[int]]:
    """For an unmatched row color, invent an ordinal column counterpart."""
    rows, cols, row_ranks, col_ranks = _header_ranks(grid)
    return [[row if row == col or (row not in col_ranks and
                                  row_ranks[row] == col_ranks[col]) else 0
             for col in cols] for row in rows]


def _rival_col_rank_fallback(grid) -> list[list[int]]:
    """For an unmatched column color, invent an ordinal row counterpart."""
    rows, cols, row_ranks, col_ranks = _header_ranks(grid)
    return [[row if row == col or (col not in row_ranks and
                                  row_ranks[row] == col_ranks[col]) else 0
             for col in cols] for row in rows]


SEMANTIC_RIVALS = {
    "row_headers_must_match": _rival_row_headers_must_match,
    "col_headers_must_match": _rival_col_headers_must_match,
    "first_matching_column_only": _rival_first_matching_column_only,
    "first_row_of_each_color_only": _rival_first_row_of_each_color_only,
    "ordinal_header_rank": _rival_ordinal_header_rank,
    "row_rank_fallback": _rival_row_rank_fallback,
    "col_rank_fallback": _rival_col_rank_fallback,
}
CANONICAL_SHORTCUTS = {
    "row_headers_must_match": _rival_row_headers_must_match,
    "col_headers_must_match": _rival_col_headers_must_match,
    "ordinal_header_rank": _rival_ordinal_header_rank,
    "row_rank_fallback": _rival_row_rank_fallback,
    "col_rank_fallback": _rival_col_rank_fallback,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_row_gap(grid) -> bool:
    return bool(_analysis(grid).get("row_only"))


def _has_col_gap(grid) -> bool:
    return bool(_analysis(grid).get("col_only"))


def _has_repeated_shared_column(grid) -> bool:
    return bool(_analysis(grid).get("repeated_shared_cols"))


def _has_repeated_shared_row(grid) -> bool:
    return bool(_analysis(grid).get("repeated_shared_rows"))


def _has_nonmax_row_gap(grid) -> bool:
    analysis = _analysis(grid)
    return bool(analysis.get("row_only") and
                min(analysis["row_only"]) < max(analysis["col_colors"]))


def _has_nonmax_col_gap(grid) -> bool:
    analysis = _analysis(grid)
    return bool(analysis.get("col_only") and
                min(analysis["col_only"]) < max(analysis["row_colors"]))


SEMANTIC_WITNESSES = {
    "row_only_header_produces_zero_row": _has_row_gap,
    "col_only_header_produces_zero_column": _has_col_gap,
    "repeated_shared_column_repeats_match": _has_repeated_shared_column,
    "repeated_shared_row_repeats_match": _has_repeated_shared_row,
    "nonmaximum_private_row_color": _has_nonmax_row_gap,
    "nonmaximum_private_column_color": _has_nonmax_col_gap,
}
WITNESS_RIVALS = {
    "row_only_header_produces_zero_row": ["row_headers_must_match"],
    "col_only_header_produces_zero_column": ["col_headers_must_match"],
    "repeated_shared_column_repeats_match": ["first_matching_column_only"],
    "repeated_shared_row_repeats_match": ["first_row_of_each_color_only"],
    "nonmaximum_private_row_color": ["ordinal_header_rank", "row_rank_fallback"],
    "nonmaximum_private_column_color": ["ordinal_header_rank", "col_rank_fallback"],
}


def lesson_identifiable(demos, query=None) -> list[str]:
    """Check six ordered demos; arbitrary query rotations are diagnostic only."""
    del query
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    scene_profiles: set[str] = set()
    shape_profiles: set[str] = set()
    palette_kinds: set[str] = set()
    rival_refuted = {name: False for name in LESSON_COMPETITORS}

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        grid = pair["input"]
        expected = pair["output"]
        strict_errors = strict_canonical_like(grid)
        if strict_errors:
            reasons.append(f"demo {index} is outside strict manifold: {strict_errors[0]}")
            continue
        official = rule_mirror(grid)
        if official != expected:
            reasons.append(f"demo {index} output disagrees with selected rule")
            continue
        observed = observe_overrides(grid)
        scene_profiles.add(observed["scene_profile"])
        shape_profiles.add(observed["shape_profile"])
        palette_kinds.add(observed["palette_kind"])
        for name, rival in LESSON_COMPETITORS.items():
            if rival(grid) != expected:
                rival_refuted[name] = True

    missing_profiles = sorted(set(SCENE_PROFILES) - scene_profiles)
    if missing_profiles:
        reasons.append(f"missing scene profile(s): {missing_profiles}")
    if len(shape_profiles) < 2:
        reasons.append("lesson does not vary the matrix shape")
    if len(palette_kinds) < 2:
        reasons.append("lesson does not vary the header palette")
    surviving = sorted(name for name, refuted in rival_refuted.items() if not refuted)
    if surviving:
        reasons.append(f"named rival(s) survive every demo: {surviving}")
    return reasons
