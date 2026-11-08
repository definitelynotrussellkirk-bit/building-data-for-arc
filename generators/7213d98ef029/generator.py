"""Generator for ARC task 7213d98ef029 — marker equality matrix.

The top row (after the zero corner) is a column-header sequence and the left
column (after the corner) is a row-header sequence.  The Racket authority drops
those headers and writes the shared nonzero color exactly where a row header
equals a column header.  This module generates inputs only; ``rule_mirror`` is
an independent Python parity helper for tests and semantic probes.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations, product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7213d98ef029"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e5bbb5dc0c42"

SUMMARY = (
    "A zero-corner grid carries nonzero column headers across row 0 and row "
    "headers down column 0; the zero interior is replaced by the colored "
    "row-by-column equality matrix after both header axes are removed."
)

INVARIANTS = [
    "0 is background and the top-left cell is 0",
    "all other cells on the top and left header axes are nonzero",
    "the input interior is entirely 0",
    "ordinary draws use one of the canonical row/column dimension profiles",
    "ordinary draws contain both equality matches and inequality mismatches",
    "ordinary draws expose an off-diagonal match and a diagonal mismatch",
    "every four consecutive samples cover all four header-set relationships",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# Dimensions exclude the discarded header row and column.  These are exactly
# the four distinct canonical output shapes.
SHAPE_PROFILES = {
    "r4_c5": (4, 5),
    "r5_c4": (5, 4),
    "r4_c6": (4, 6),
    "r5_c5": (5, 5),
}

# Set relationships between row-header and column-header colors.
SCENE_PROFILES = ("all_shared", "row_gap", "col_gap", "dual_gap")

# Four-color palettes keep every override combination constructive on the
# shortest four-cell axis.  ``wide`` reproduces the second canonical palette
# cardinality (five nonzero colors, six colors including background).
PALETTES = {
    "classic": (2, 3, 4, 5),
    "split": (1, 2, 6, 7),
    "bright": (2, 4, 6, 9),
    "mixed": (1, 3, 5, 8),
    "wide": (1, 3, 4, 5, 8),
}
PALETTE_KINDS = tuple(PALETTES)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "shape_profile": {
        "type": "str",
        "default": "sample-index schedule over canonical shapes",
        "valid": "r4_c5|r5_c4|r4_c6|r5_c5",
    },
    "scene_profile": {
        "type": "str",
        "default": "all_shared|row_gap|col_gap|dual_gap sliding schedule",
        "valid": "all_shared|row_gap|col_gap|dual_gap",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule over five canonical-like palettes",
        "valid": "classic|split|bright|mixed|wide",
    },
}

# The five-color palette needs enough header capacity *and* a repeated shared
# color, which is an ordinary-scene teaching invariant.  These are the only
# impossible exact triples; every single-axis and two-axis request remains
# constructive because the unpinned axis is selected around it.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = [
    {"shape_profile": "r4_c5", "scene_profile": "all_shared", "palette_kind": "wide"},
    {"shape_profile": "r5_c4", "scene_profile": "all_shared", "palette_kind": "wide"},
    {"shape_profile": "r4_c6", "scene_profile": "all_shared", "palette_kind": "wide"},
    {"shape_profile": "r5_c5", "scene_profile": "all_shared", "palette_kind": "wide"},
    {"shape_profile": "r4_c5", "scene_profile": "row_gap", "palette_kind": "wide"},
    {"shape_profile": "r5_c4", "scene_profile": "row_gap", "palette_kind": "wide"},
    {"shape_profile": "r4_c6", "scene_profile": "row_gap", "palette_kind": "wide"},
    {"shape_profile": "r4_c5", "scene_profile": "col_gap", "palette_kind": "wide"},
    {"shape_profile": "r5_c4", "scene_profile": "col_gap", "palette_kind": "wide"},
]


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-step semantic schedule to the shared gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str,
                      overrides: dict[str, Any]) -> str:
    """Record a scheduled value while preserving exact caller overrides."""
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

    invalid = [
        (row, col, value)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"{len(invalid)} cell(s) are not integer ARC colors in 0..9")
        return errors

    if grid[0][0] != 0:
        errors.append("top-left corner must be background 0")
    zero_top = [col for col in range(1, width) if grid[0][col] == 0]
    if zero_top:
        errors.append(f"{len(zero_top)} zero column-header cell(s)")
    zero_left = [row for row in range(1, height) if grid[row][0] == 0]
    if zero_left:
        errors.append(f"{len(zero_left)} zero row-header cell(s)")
    painted = [
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if grid[row][col] != 0
    ]
    if painted:
        errors.append(f"{len(painted)} nonzero interior cell(s)")
    return errors


def _shape_profile(height: int, width: int) -> str | None:
    dimensions = (height - 1, width - 1)
    for name, expected in SHAPE_PROFILES.items():
        if dimensions == expected:
            return name
    return None


def _palette_kind(colors: set[int]) -> str | None:
    for name, palette in PALETTES.items():
        if colors == set(palette):
            return name
    return None


def _scene_profile(row_colors: set[int], col_colors: set[int]) -> str | None:
    row_only = row_colors - col_colors
    col_only = col_colors - row_colors
    if not row_only and not col_only:
        return "all_shared"
    if row_only and not col_only:
        return "row_gap"
    if col_only and not row_only:
        return "col_gap"
    if row_only and col_only:
        return "dual_gap"
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
    matches = [
        (row, col)
        for row, row_color in enumerate(row_headers)
        for col, col_color in enumerate(col_headers)
        if row_color == col_color
    ]
    total = len(row_headers) * len(col_headers)

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
        "row_only": row_colors - col_colors,
        "col_only": col_colors - row_colors,
        "matches": matches,
        "match_cells": len(matches),
        "mismatch_cells": total - len(matches),
        "off_diagonal_match": any(row != col for row, col in matches),
        "diagonal_mismatch": any(
            row_headers[index] != col_headers[index]
            for index in range(min(len(row_headers), len(col_headers)))
        ),
        "repeated_shared_rows": any(row_counts[color] >= 2 for color in shared),
        "repeated_shared_cols": any(col_counts[color] >= 2 for color in shared),
        "shape_profile": _shape_profile(len(grid), len(grid[0])),
        "scene_profile": _scene_profile(row_colors, col_colors),
        "palette_kind": _palette_kind(row_colors | col_colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar and reject signal-free header matrices."""
    del difficulty, meta
    errors = _structural_errors(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["match_cells"] == 0:
        errors.append("header axes must contain at least one equality match")
    if analysis["mismatch_cells"] == 0:
        errors.append("header axes must contain at least one inequality mismatch")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Validate canonical support plus the ordinary teaching witnesses."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    analysis = _analysis(grid)
    if analysis["shape_profile"] is None:
        errors.append("shape is outside the four canonical output profiles")
    if len(analysis["colors"]) not in (4, 5):
        errors.append("canonical-like scenes use four or five nonzero header colors")
    if analysis["scene_profile"] is None:
        errors.append("header-set relationship is not recognized")
    if not analysis["off_diagonal_match"]:
        errors.append("scene has no off-diagonal equality witness")
    if not analysis["diagonal_mismatch"]:
        errors.append("scene has no diagonal inequality witness")
    if not (analysis["repeated_shared_rows"] or analysis["repeated_shared_cols"]):
        errors.append("no shared color repeats on either header axis")
    return errors


def _fill_values(base: Iterable[int], length: int, choices: tuple[int, ...], rng) -> list[int]:
    values = list(base)
    if len(values) > length:
        raise ValueError(f"header basis of {len(values)} cells does not fit length {length}")
    while len(values) < length:
        values.append(rng.choice(choices))
    rng.shuffle(values)
    return values


def _choose_column_order(row_headers: list[int], col_values: list[int], rng) -> list[int]:
    """Choose a varied ordering with explicit off-diagonal/diagonal evidence."""
    candidates = sorted(set(permutations(col_values)))
    valid = []
    for candidate in candidates:
        off_diagonal = any(
            row != col and row_color == col_color
            for row, row_color in enumerate(row_headers)
            for col, col_color in enumerate(candidate)
        )
        diagonal_mismatch = any(
            row_headers[index] != candidate[index]
            for index in range(min(len(row_headers), len(candidate)))
        )
        if off_diagonal and diagonal_mismatch:
            valid.append(candidate)
    if not valid:
        raise AssertionError("no column ordering exposes required equality witnesses")
    return list(rng.choice(valid))


def _build_headers(scene_profile: str, palette: tuple[int, ...],
                   n_rows: int, n_cols: int, rng) -> tuple[list[int], list[int]]:
    roles = list(palette)
    rng.shuffle(roles)
    if len(roles) == 4:
        first, second, third, fourth = roles
        if scene_profile == "all_shared":
            row_base = (first, second, third, fourth)
            col_base = (first, second, third, fourth)
            row_choices = col_choices = tuple(roles)
        elif scene_profile == "row_gap":
            row_base = (first, second, third, fourth)
            col_base = (first, second, third)
            row_choices = tuple(roles)
            col_choices = (first, second, third)
        elif scene_profile == "col_gap":
            row_base = (first, second, third)
            col_base = (first, second, third, fourth)
            row_choices = (first, second, third)
            col_choices = tuple(roles)
        elif scene_profile == "dual_gap":
            row_base = (first, second, third)
            col_base = (first, second, fourth)
            # Fill only from shared colors so duplicate cross-products remain
            # observable even on the shortest four-cell axes.
            row_choices = (first, second)
            col_choices = (first, second)
        else:
            raise ValueError(f"unknown scene_profile: {scene_profile!r}")
    elif len(roles) == 5:
        first, second, third, fourth, fifth = roles
        if scene_profile == "all_shared":
            row_base = col_base = (first, second, third, fourth, fifth)
            row_choices = col_choices = tuple(roles)
        elif scene_profile == "row_gap":
            row_base = (first, second, third, fourth, fifth)
            col_base = (first, second, third, fourth)
            row_choices = tuple(roles)
            col_choices = (first, second, third, fourth)
        elif scene_profile == "col_gap":
            row_base = (first, second, third, fourth)
            col_base = (first, second, third, fourth, fifth)
            row_choices = (first, second, third, fourth)
            # Any required duplicate must be a shared color, not the
            # column-only fifth role.
            col_choices = (first, second, third, fourth)
        elif scene_profile == "dual_gap":
            row_base = (first, second, third, fourth)
            col_base = (first, second, third, fifth)
            row_choices = col_choices = (first, second, third)
        else:
            raise ValueError(f"unknown scene_profile: {scene_profile!r}")
    else:
        raise ValueError(f"unsupported palette cardinality: {len(roles)}")

    row_headers = _fill_values(row_base, n_rows, row_choices, rng)
    col_values = _fill_values(col_base, n_cols, col_choices, rng)
    col_headers = _choose_column_order(row_headers, col_values, rng)
    return row_headers, col_headers


def _combination_is_compatible(
    shape_profile: str, scene_profile: str, palette_kind: str
) -> bool:
    requested = {
        "shape_profile": shape_profile,
        "scene_profile": scene_profile,
        "palette_kind": palette_kind,
    }
    return not any(
        all(requested[axis] == expected for axis, expected in declaration.items())
        for declaration in INCOMPATIBLE_OVERRIDE_COMBINATIONS
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the selected Racket rule owns output."""
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    domains = {
        "shape_profile": tuple(SHAPE_PROFILES),
        "scene_profile": SCENE_PROFILES,
        "palette_kind": PALETTE_KINDS,
    }
    for axis, options in domains.items():
        value = overrides.get(axis)
        if value is not None and value not in options:
            raise ValueError(f"unknown {axis}: {value!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    shape_names = tuple(SHAPE_PROFILES)
    band_offset = ("easy", "medium", "hard").index(band)
    shape_scheduled = shape_names[
        (int(sample_index) + int(seed) % len(shape_names) + band_offset)
        % len(shape_names)
    ]
    scene_scheduled = schedule_profile(seed, sample_index, band)
    palette_scheduled = PALETTE_KINDS[
        (int(sample_index) + (int(seed) // 7) % len(PALETTE_KINDS) + 2 * band_offset)
        % len(PALETTE_KINDS)
    ]

    compatible = [
        candidate
        for candidate in product(shape_names, SCENE_PROFILES, PALETTE_KINDS)
        if _combination_is_compatible(*candidate)
        and all(
            overrides.get(axis) is None or overrides[axis] == value
            for axis, value in zip(
                ("shape_profile", "scene_profile", "palette_kind"), candidate
            )
        )
    ]
    if not compatible:
        pinned = ", ".join(
            f"{axis}={overrides[axis]!r}"
            for axis in ("shape_profile", "scene_profile", "palette_kind")
            if overrides.get(axis) is not None
        )
        raise ValueError(
            "incompatible overrides shape_profile/scene_profile/palette_kind: " + pinned
        )

    shape_default, scene_default, palette_default = min(
        compatible,
        key=lambda candidate: (
            candidate[1] != scene_scheduled,
            candidate[2] != palette_scheduled,
            candidate[0] != shape_scheduled,
            candidate,
        ),
    )

    shape_profile = _scheduled_choice(
        ctx, "shape_profile", shape_names, shape_default, overrides
    )
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, scene_default, overrides
    )
    palette_kind = _scheduled_choice(
        ctx, "palette_kind", PALETTE_KINDS, palette_default, overrides
    )

    n_rows, n_cols = SHAPE_PROFILES[shape_profile]
    row_headers, col_headers = _build_headers(
        scene_profile,
        PALETTES[palette_kind],
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
        raise AssertionError("constructed invalid equality scene: " + "; ".join(errors))
    requested = {
        "shape_profile": shape_profile,
        "scene_profile": scene_profile,
        "palette_kind": palette_kind,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise AssertionError(f"axis observation mismatch: requested={requested}, observed={observed}")
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, str]:
    """Recover all exact advertised axes from pixels, not RNG bookkeeping."""
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
    """Independent Python mirror of the selected Racket equality rule."""
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


# Plausible wrong rules used by the semantic gate.
def _rival_row_headers_must_match(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    top_colors = set(grid[0][1:])
    width = len(output[0])
    for row, color in enumerate(grid[index][0] for index in range(1, len(grid))):
        if color not in top_colors:
            output[row][row % width] = color
    return output


def _rival_col_headers_must_match(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    left_colors = {grid[row][0] for row in range(1, len(grid))}
    height = len(output)
    for col, color in enumerate(grid[0][1:]):
        if color not in left_colors:
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


def _rival_diagonal_only(grid) -> list[list[int]]:
    row_headers = [grid[row][0] for row in range(1, len(grid))]
    col_headers = list(grid[0][1:])
    output = [[0 for _ in col_headers] for _ in row_headers]
    for index in range(min(len(row_headers), len(col_headers))):
        if row_headers[index] == col_headers[index]:
            output[index][index] = row_headers[index]
    return output


SEMANTIC_RIVALS = {
    "row_headers_must_match": _rival_row_headers_must_match,
    "col_headers_must_match": _rival_col_headers_must_match,
    "first_matching_column_only": _rival_first_matching_column_only,
    "first_row_of_each_color_only": _rival_first_row_of_each_color_only,
    "diagonal_only": _rival_diagonal_only,
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


def _has_off_diagonal_match(grid) -> bool:
    return bool(_analysis(grid).get("off_diagonal_match"))


SEMANTIC_WITNESSES = {
    "row_only_header_produces_zero_row": _has_row_gap,
    "col_only_header_produces_zero_column": _has_col_gap,
    "repeated_shared_column_repeats_match": _has_repeated_shared_column,
    "repeated_shared_row_repeats_match": _has_repeated_shared_row,
    "off_diagonal_equality": _has_off_diagonal_match,
}
WITNESS_RIVALS = {
    "row_only_header_produces_zero_row": ["row_headers_must_match"],
    "col_only_header_produces_zero_column": ["col_headers_must_match"],
    "repeated_shared_column_repeats_match": ["first_matching_column_only"],
    "repeated_shared_row_repeats_match": ["first_row_of_each_color_only"],
    "off_diagonal_equality": ["diagonal_only"],
}


def lesson_identifiable(demos, query=None) -> list[str]:
    """Require every four-demo lesson to refute all named equality shortcuts."""
    del query
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
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

    missing = sorted(set(SCENE_PROFILES) - scene_profiles)
    if missing:
        reasons.append(f"missing scene profile(s): {missing}")
    if len(shape_profiles) < 2:
        reasons.append("lesson does not vary matrix shape")
    if len(palette_kinds) < 2:
        reasons.append("lesson does not vary header palette")
    surviving = sorted(name for name, refuted in rival_refuted.items() if not refuted)
    if surviving:
        reasons.append(f"named rival(s) survive every demo: {surviving}")
    return reasons
