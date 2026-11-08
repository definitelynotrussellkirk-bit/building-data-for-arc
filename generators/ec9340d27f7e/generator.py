"""Generator for ARC task ``ec9340d27f7e``.

Intended rule
-------------
Read the input grid without mutation.  In every row, replace a zero with the
matching non-zero color exactly when its immediate left and right neighbours
are equal.  Orientation, equality, adjacency, zero-centre, and exhaustive
application are all semantically relevant.

The ordinary curriculum alternates canonical-profile anchors with complete
contrast bundles.  A contrast bundle includes an unequal horizontal sandwich,
a vertical equal-color sandwich, a same-color gap wider than one cell, and a
blocked midpoint, while still containing several lawful targets.  Those cases
refute the strongest shortcuts left ambiguous by the canonical demonstrations.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ec9340d27f7e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "80ec61287499"

SUMMARY = (
    "On a zero background, fill every zero whose immediate horizontal "
    "neighbours are the same non-zero color. Read all matches from the original "
    "input. Unequal horizontal neighbours, vertical matches, wider gaps, and "
    "already occupied midpoints remain unchanged."
)

INVARIANTS = [
    "the input is a rectangular 5..8 by 7..10 ARC grid",
    "the palette is zero plus exactly three non-zero colors",
    "there are exactly 3..5 horizontal equal-color one-zero targets",
    "at least two colors occur as target colors",
    "ordinary contrast scenes contain the complete negative-control bundle",
]

# These are the only caller-controlled semantic axes.  Each one is exact,
# recorded through gen_ctx, and recovered from the returned grid by
# observe_overrides().  Every Cartesian combination fits, including 5x7 with
# five target gaps.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "7..10",
    },
    "n_gaps": {
        "type": "int",
        "default": "scheduled 3..5",
        "valid": "3..5",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

# A,A,C,C pattern never occurs: across the cyclic boundary the longest run of
# anchors is two, so every three-demo lesson contains a complete contrast
# bundle.  All four canonical dimension/target profiles are emitted.
_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "name": "canonical_6x8_3",
        "kind": "anchor",
        "grid_h": 6,
        "grid_w": 8,
        "n_gaps": 3,
    },
    {
        "name": "contrast_7x10_4",
        "kind": "contrast",
        "grid_h": 7,
        "grid_w": 10,
        "n_gaps": 4,
    },
    {
        "name": "contrast_7x10_5",
        "kind": "contrast",
        "grid_h": 7,
        "grid_w": 10,
        "n_gaps": 5,
    },
    {
        "name": "canonical_5x9_5",
        "kind": "anchor",
        "grid_h": 5,
        "grid_w": 9,
        "n_gaps": 5,
    },
    {
        "name": "canonical_7x7_3",
        "kind": "anchor",
        "grid_h": 7,
        "grid_w": 7,
        "n_gaps": 3,
    },
    {
        "name": "contrast_8x10_4",
        "kind": "contrast",
        "grid_h": 8,
        "grid_w": 10,
        "n_gaps": 4,
    },
    {
        "name": "contrast_6x9_5",
        "kind": "contrast",
        "grid_h": 6,
        "grid_w": 9,
        "n_gaps": 5,
    },
    {
        "name": "canonical_6x10_4",
        "kind": "anchor",
        "grid_h": 6,
        "grid_w": 10,
        "n_gaps": 4,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_PROFILE_BY_NAME = {profile["name"]: profile for profile in _PROFILES}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BOUNDS = {"grid_h": (5, 8), "grid_w": (7, 10), "n_gaps": (3, 5)}
_CANONICAL_PROFILES = {
    (6, 8): {"n_gaps": 3, "row_counts": [1, 1, 1], "nonzero": 6},
    (5, 9): {"n_gaps": 5, "row_counts": [1, 1, 3], "nonzero": 8},
    (7, 7): {"n_gaps": 3, "row_counts": [1, 1, 1], "nonzero": 6},
    (6, 10): {"n_gaps": 4, "row_counts": [1, 1, 2], "nonzero": 8},
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile audited by the gate."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    offset = {None: 1, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(_PROFILES)]


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    return _PROFILE_BY_NAME[schedule_profile(0, sample_index, difficulty)]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _BOUNDS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_exact_int(ctx, overrides, name: str, default: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row.strip()]
            except ValueError as exc:
                raise ValueError("string rows must contain ARC digits") from exc
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid cells must be integer ARC colors in 0..9")
        rows.append(values)
    return rows


def _analysis(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    colors = {value for row in values for value in row}
    nonzero_cells = {
        (r, c)
        for r, row in enumerate(values)
        for c, value in enumerate(row)
        if value != 0
    }

    targets: list[tuple[int, int]] = []
    target_endpoints: set[tuple[int, int]] = set()
    target_colors: list[int] = []
    row_target_counts: list[int] = []
    unequal_gaps: list[tuple[int, int, int, int]] = []
    blocked_midpoints: list[tuple[int, int, int, int]] = []

    for r, row in enumerate(values):
        count = 0
        for c in range(1, w - 1):
            left, center, right = row[c - 1], row[c], row[c + 1]
            if center == 0 and left != 0 and left == right:
                targets.append((r, c))
                target_endpoints.update(((r, c - 1), (r, c + 1)))
                target_colors.append(left)
                count += 1
            elif center == 0 and left != 0 and right != 0 and left != right:
                unequal_gaps.append((r, c, left, right))
            elif center != 0 and left != 0 and left == right:
                blocked_midpoints.append((r, c, left, center))
        row_target_counts.append(count)

    vertical_equal_gaps: list[tuple[int, int, int]] = []
    for r in range(1, h - 1):
        for c in range(w):
            above, center, below = values[r - 1][c], values[r][c], values[r + 1][c]
            if center == 0 and above != 0 and above == below:
                vertical_equal_gaps.append((r, c, above))

    long_equal_gaps: list[tuple[int, int, int, int]] = []
    for r, row in enumerate(values):
        occupied = [c for c, value in enumerate(row) if value != 0]
        for left, right in zip(occupied, occupied[1:]):
            if right - left - 1 >= 2 and row[left] == row[right]:
                long_equal_gaps.append((r, left, right, row[left]))

    control_cells: set[tuple[int, int]] = set()
    control_colors: set[int] = set()
    for r, c, left, right in unequal_gaps:
        control_cells.update(((r, c - 1), (r, c + 1)))
        control_colors.update((left, right))
    for r, c, color in vertical_equal_gaps:
        control_cells.update(((r - 1, c), (r + 1, c)))
        control_colors.add(color)
    for r, left, right, color in long_equal_gaps:
        control_cells.update(((r, left), (r, right)))
        control_colors.add(color)
    for r, c, endpoint, midpoint in blocked_midpoints:
        control_cells.update(((r, c - 1), (r, c), (r, c + 1)))
        control_colors.update((endpoint, midpoint))

    explained_nonzero = target_endpoints | control_cells
    unexplained_nonzero = sorted(nonzero_cells - explained_nonzero)
    non_target_control_cells = control_cells - target_endpoints
    target_color_set = set(target_colors)
    same_color_opposite_fate = bool(target_color_set & control_colors) and bool(
        non_target_control_cells
    )
    complete_contrast_bundle = all(
        (
            unequal_gaps,
            vertical_equal_gaps,
            long_equal_gaps,
            blocked_midpoints,
        )
    ) and same_color_opposite_fate

    return {
        "errors": [],
        "grid": values,
        "height": h,
        "width": w,
        "colors": colors,
        "nonzero_cells": nonzero_cells,
        "nonzero_count": len(nonzero_cells),
        "targets": targets,
        "target_count": len(targets),
        "target_endpoints": target_endpoints,
        "target_colors": target_colors,
        "target_color_set": target_color_set,
        "row_target_counts": row_target_counts,
        "target_row_count": sum(count > 0 for count in row_target_counts),
        "unequal_gaps": unequal_gaps,
        "vertical_equal_gaps": vertical_equal_gaps,
        "long_equal_gaps": long_equal_gaps,
        "blocked_midpoints": blocked_midpoints,
        "control_cells": control_cells,
        "non_target_control_cells": non_target_control_cells,
        "unexplained_nonzero": unexplained_nonzero,
        "same_color_opposite_fate": same_color_opposite_fate,
        "complete_contrast_bundle": complete_contrast_bundle,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    return analysis


def _place_symbolic(
    grid: list[list[int]],
    cells: dict[tuple[int, int], int],
    *,
    row_offset: int,
    col_offset: int,
    flip_vertical: bool,
    flip_horizontal: bool,
) -> None:
    for (base_r, base_c), color in cells.items():
        r = 5 - base_r if flip_vertical else base_r
        c = 8 - base_c if flip_horizontal else base_c
        grid[row_offset + r][col_offset + c] = color


def _build_contrast(
    h: int,
    w: int,
    n_gaps: int,
    colors: tuple[int, int, int],
    rng,
) -> list[list[int]]:
    """Build one complete contrast bundle inside a 6x9 footprint."""
    if h < 6 or w < 9 or n_gaps not in (4, 5):
        raise ValueError("contrast profiles require h>=6, w>=9, n_gaps in {4,5}")
    a, b, c = colors
    cells: dict[tuple[int, int], int] = {
        # Two A targets in one row.
        (0, 0): a,
        (0, 2): a,
        (0, 4): a,
        # B target row.  The second target is included for n_gaps=5.
        (2, 0): b,
        (2, 2): b,
        # Repeated A target in another row.
        (4, 0): a,
        (4, 2): a,
        # Unequal A-0-B sandwich plus the upper vertical-C endpoint.
        (1, 5): c,
        (1, 6): a,
        (1, 8): b,
        # C-0-0-C is both the lower vertical endpoint and a wider-gap control.
        (3, 5): c,
        (3, 8): c,
        # Occupied midpoint C-B-C.
        (5, 5): c,
        (5, 6): b,
        (5, 7): c,
    }
    if n_gaps == 5:
        cells[(2, 4)] = b

    grid = full_grid(h, w, 0)
    row_offset = rng.randint(0, h - 6)
    col_offset = rng.randint(0, w - 9)
    _place_symbolic(
        grid,
        cells,
        row_offset=row_offset,
        col_offset=col_offset,
        flip_vertical=bool(rng.getrandbits(1)),
        flip_horizontal=bool(rng.getrandbits(1)),
    )
    return grid


def _build_anchor(
    h: int,
    w: int,
    n_gaps: int,
    colors: tuple[int, int, int],
    rng,
) -> list[list[int]]:
    """Build a randomized member of one of the four empirical profiles."""
    profile = _CANONICAL_PROFILES.get((h, w))
    if profile is None or profile["n_gaps"] != n_gaps:
        raise ValueError(f"{h}x{w}/{n_gaps} is not a canonical anchor profile")
    a, b, c = colors
    if n_gaps == 3:
        patterns = ((a, (0, 2)), (b, (0, 2)), (c, (0, 2)))
    elif n_gaps == 4:
        # The final row mirrors the test profile: two disjoint C-0-C pairs.
        patterns = ((a, (0, 2)), (b, (0, 2)), (c, (0, 2, 5, 7)))
    else:
        # Three adjacent gaps in the final row, as in the 5x9 training profile.
        patterns = ((a, (0, 2)), (b, (0, 2)), (c, (0, 2, 4, 6)))

    grid = full_grid(h, w, 0)
    rows = rng.sample(range(h), 3)
    for row, (color, offsets) in zip(rows, patterns):
        span = max(offsets) + 1
        start = rng.randint(0, w - span)
        for offset in offsets:
            grid[row][start + offset] = color
    return grid


def _build_positive_override(
    h: int,
    w: int,
    n_gaps: int,
    colors: tuple[int, int, int],
    rng,
) -> list[list[int]]:
    """Honor every exact-axis Cartesian combination with target-only scenes."""
    grid = full_grid(h, w, 0)
    rows = rng.sample(range(h), n_gaps)
    for index, row in enumerate(rows):
        color = colors[index % len(colors)]
        start = rng.randint(0, w - 3)
        grid[row][start] = color
        grid[row][start + 2] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = _profile_for(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", profile["grid_h"])
    w = _draw_exact_int(ctx, overrides, "grid_w", profile["grid_w"])
    n_gaps = _draw_exact_int(ctx, overrides, "n_gaps", profile["n_gaps"])
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    rng = ctx.draw_rng("layout")

    if overrides:
        grid = _build_positive_override(h, w, n_gaps, colors, rng)
    elif profile["kind"] == "anchor":
        grid = _build_anchor(h, w, n_gaps, colors, rng)
    else:
        grid = _build_contrast(h, w, n_gaps, colors, rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced invalid teaching grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {"grid_h": h, "grid_w": w, "n_gaps": n_gaps}
    if observed != requested:
        raise AssertionError(f"exact-axis mismatch: requested={requested}, observed={observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    if not 5 <= h <= 8:
        errors.append(f"grid height {h} must be in 5..8")
    if not 7 <= w <= 10:
        errors.append(f"grid width {w} must be in 7..10")
    if 0 not in analysis["colors"] or len(analysis["colors"]) != 4:
        errors.append(
            "palette must be background 0 plus exactly three non-zero colors; "
            f"found {sorted(analysis['colors'])}"
        )
    if not 3 <= analysis["target_count"] <= 5:
        errors.append(f"expected 3..5 horizontal target gaps, found {analysis['target_count']}")
    if len(analysis["target_color_set"]) < 2:
        errors.append("expected at least two distinct target colors")
    if analysis["target_row_count"] < 3:
        errors.append("expected targets in at least three rows")
    if analysis["unexplained_nonzero"]:
        preview = analysis["unexplained_nonzero"][:5]
        errors.append(f"found non-zero cells outside targets/declared controls: {preview}")

    if analysis["non_target_control_cells"]:
        if analysis["target_count"] < 4:
            errors.append("contrast scenes must retain at least four lawful targets")
        if not analysis["complete_contrast_bundle"]:
            errors.append(
                "partial contrast scene: require unequal-horizontal, vertical-equal, "
                "wider-gap, blocked-midpoint, and same-color opposite-fate controls"
            )

    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid) if not errors else {}
        for axis, requested in meta["overrides"].items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"meta {axis} requested {requested!r}, observed {observed[axis]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_gaps": analysis["target_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    grammar_errors = self_check(analysis["grid"])
    if grammar_errors:
        return grammar_errors

    reasons: list[str] = []
    dims = (analysis["height"], analysis["width"])
    profile = _CANONICAL_PROFILES.get(dims)
    if profile is None:
        reasons.append(f"dimensions {dims} are outside the four canonical profiles")
        return reasons
    if analysis["target_count"] != profile["n_gaps"]:
        reasons.append(
            f"canonical profile {dims} has {profile['n_gaps']} gaps, "
            f"found {analysis['target_count']}"
        )
    row_counts = sorted(count for count in analysis["row_target_counts"] if count)
    if row_counts != profile["row_counts"]:
        reasons.append(
            f"canonical profile {dims} has target-row counts {profile['row_counts']}, "
            f"found {row_counts}"
        )
    if analysis["nonzero_count"] != profile["nonzero"]:
        reasons.append(
            f"canonical profile {dims} has {profile['nonzero']} non-zero cells, "
            f"found {analysis['nonzero_count']}"
        )
    if len(analysis["target_color_set"]) != 3:
        reasons.append("canonical inputs use exactly three target colors")
    if analysis["nonzero_cells"] != analysis["target_endpoints"]:
        reasons.append("canonical anchors contain only target endpoints as non-zero cells")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    for r, row in enumerate(values):
        for c in range(1, len(row) - 1):
            if row[c] == 0 and row[c - 1] != 0 and row[c - 1] == row[c + 1]:
                out[r][c] = row[c - 1]
    return out


def _rival_identity(grid):
    return [row[:] for row in _coerce_grid(grid)]


def _rival_first_target_only(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    targets = _analysis_or_raise(values)["targets"]
    if targets:
        r, c = targets[0]
        out[r][c] = values[r][c - 1]
    return out


def _rival_one_target_color_only(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    analysis = _analysis_or_raise(values)
    if not analysis["targets"]:
        return out
    first_r, first_c = analysis["targets"][0]
    chosen = values[first_r][first_c - 1]
    for r, c in analysis["targets"]:
        if values[r][c - 1] == chosen:
            out[r][c] = chosen
    return out


def _rival_fill_any_horizontal_sandwich(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    for r, row in enumerate(values):
        for c in range(1, len(row) - 1):
            if row[c] == 0 and row[c - 1] != 0 and row[c + 1] != 0:
                out[r][c] = row[c - 1]
    return out


def _rival_fill_horizontal_and_vertical(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    h, w = len(values), len(values[0])
    for r in range(1, h - 1):
        for c in range(w):
            if (
                values[r][c] == 0
                and values[r - 1][c] != 0
                and values[r - 1][c] == values[r + 1][c]
            ):
                out[r][c] = values[r - 1][c]
    return out


def _rival_fill_long_equal_gaps(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    for r, left, right, color in _analysis_or_raise(values)["long_equal_gaps"]:
        for c in range(left + 1, right):
            out[r][c] = color
    return out


def _rival_overwrite_blocked_midpoints(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    for r, c, endpoint, _ in _analysis_or_raise(values)["blocked_midpoints"]:
        out[r][c] = endpoint
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "first_target_only": _rival_first_target_only,
    "one_target_color_only": _rival_one_target_color_only,
    "fill_any_horizontal_sandwich": _rival_fill_any_horizontal_sandwich,
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "fill_long_equal_gaps": _rival_fill_long_equal_gaps,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked_midpoints,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These three wrong rules reproduce every canonical train+test pair.  Their
# names intentionally match SEMANTIC_RIVALS so the semantic gate can require a
# generated, oracle-verified counterexample.
CANONICAL_SHORTCUTS = {
    "fill_any_horizontal_sandwich": _rival_fill_any_horizontal_sandwich,
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked_midpoints,
}


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return None if analysis.get("errors") else analysis


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: strict_canonical_like(grid) == [],
    "multiple_targets": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["target_count"] >= 3
    ),
    "multiple_target_colors": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and len(analysis["target_color_set"]) >= 2
    ),
    "unequal_horizontal_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["unequal_gaps"])
    ),
    "vertical_equal_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["vertical_equal_gaps"])
    ),
    "long_equal_gap_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["long_equal_gaps"])
    ),
    "blocked_midpoint_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["blocked_midpoints"])
    ),
    "same_color_opposite_fate": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["same_color_opposite_fate"]
    ),
    "complete_contrast_bundle": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["complete_contrast_bundle"]
    ),
}

WITNESS_RIVALS = {
    "strict_canonical_profile": ["first_target_only"],
    "multiple_targets": ["identity", "first_target_only"],
    "multiple_target_colors": ["one_target_color_only"],
    "unequal_horizontal_control": ["fill_any_horizontal_sandwich"],
    "vertical_equal_control": ["fill_horizontal_and_vertical"],
    "long_equal_gap_control": ["fill_long_equal_gaps"],
    "blocked_midpoint_control": ["overwrite_blocked_midpoints"],
    "same_color_opposite_fate": [
        "fill_any_horizontal_sandwich",
        "fill_horizontal_and_vertical",
        "fill_long_equal_gaps",
        "overwrite_blocked_midpoints",
    ],
    "complete_contrast_bundle": [
        "fill_any_horizontal_sandwich",
        "fill_horizontal_and_vertical",
        "fill_long_equal_gaps",
        "overwrite_blocked_midpoints",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, item in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"{label} is not an input/output pair")
            continue
        grammar_errors = self_check(item["input"])
        if grammar_errors:
            reasons.append(f"{label} input violates teaching grammar: {grammar_errors[0]}")
            continue
        try:
            expected = rule_mirror(item["input"])
            actual = _coerce_grid(item["output"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"{label} could not be checked: {exc}")
            continue
        if expected != actual:
            reasons.append(f"{label} output disagrees with the intended horizontal rule")
    if reasons:
        return reasons

    normalized_demos = [
        {"input": _coerce_grid(item["input"]), "output": _coerce_grid(item["output"])}
        for item in demos
    ]
    normalized_query = {
        "input": _coerce_grid(query["input"]),
        "output": _coerce_grid(query["output"]),
    }
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(item["input"]) == item["output"] for item in normalized_demos
        )
        if survives:
            if competitor(normalized_query["input"]) != normalized_query["output"]:
                reasons.append(
                    f"competing rule {name!r} fits every demo but answers the query differently"
                )
            else:
                reasons.append(f"competing rule {name!r} survives every demo and query")
    return reasons
