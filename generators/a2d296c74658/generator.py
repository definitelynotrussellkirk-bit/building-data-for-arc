"""Teaching generator for ARC task ``a2d296c74658``.

Intended rule
-------------
Read the input grid without mutation.  Recolor a zero to yellow (4) exactly
when its immediate vertical neighbours are both orange (7).  Orientation,
adjacency, endpoint color, an empty midpoint, shared endpoints, and exhaustive
application are all semantically relevant.

The ordinary curriculum alternates canonical-profile anchors with complete
contrast bundles.  Every three-example lesson therefore contains a grid that
separates the intended rule from the strongest shortcuts that fit all four
canonical pairs.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a2d296c74658"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "75c6c8a07b85"

SUMMARY = (
    "On a zero background, recolor every zero to 4 exactly when its immediate "
    "vertical neighbours are both 7.  Horizontal 7-0-7 patterns, wider "
    "vertical gaps, occupied midpoints, and matching endpoints of any other "
    "color remain unchanged."
)

INVARIANTS = [
    "the input is a rectangular 7..10 by 6..9 ARC grid",
    "there are exactly 2..4 vertical 7-0-7 targets in at least two columns",
    "ordinary contrast scenes contain the complete negative-control bundle",
    "all target centers are computed from the original input and changed to 4",
]

# These are the only caller-controlled axes.  Each is exact, is recorded by
# gen_ctx, and can be recovered from the returned grid by observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "6..9",
    },
    "num_triplets": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

# The cyclic kind sequence A,C,C,A,A,C,C,A has no run of three anchors, even
# across the boundary.  Thus every three consecutive examples contain a full
# contrast bundle, while exactly half of ordinary draws retain canonical form.
_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "name": "canonical_7x6_2",
        "kind": "anchor",
        "grid_h": 7,
        "grid_w": 6,
        "num_triplets": 2,
    },
    {
        "name": "contrast_9x9_3",
        "kind": "contrast",
        "grid_h": 9,
        "grid_w": 9,
        "num_triplets": 3,
    },
    {
        "name": "contrast_9x9_4",
        "kind": "contrast",
        "grid_h": 9,
        "grid_w": 9,
        "num_triplets": 4,
    },
    {
        "name": "canonical_8x8_2",
        "kind": "anchor",
        "grid_h": 8,
        "grid_w": 8,
        "num_triplets": 2,
    },
    {
        "name": "canonical_9x9_2",
        "kind": "anchor",
        "grid_h": 9,
        "grid_w": 9,
        "num_triplets": 2,
    },
    {
        "name": "contrast_10x9_3",
        "kind": "contrast",
        "grid_h": 10,
        "grid_w": 9,
        "num_triplets": 3,
    },
    {
        "name": "contrast_10x9_4",
        "kind": "contrast",
        "grid_h": 10,
        "grid_w": 9,
        "num_triplets": 4,
    },
    {
        "name": "canonical_10x9_3",
        "kind": "anchor",
        "grid_h": 10,
        "grid_w": 9,
        "num_triplets": 3,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_PROFILE_BY_NAME = {profile["name"]: profile for profile in _PROFILES}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_BOUNDS = {"grid_h": (7, 10), "grid_w": (6, 9), "num_triplets": (2, 4)}
_CANONICAL_PROFILES = {
    (7, 6): {"num_triplets": 2, "column_counts": [1, 1], "nonzero": 4},
    (8, 8): {"num_triplets": 2, "column_counts": [1, 1], "nonzero": 4},
    (9, 9): {"num_triplets": 2, "column_counts": [1, 1], "nonzero": 4},
    (10, 9): {"num_triplets": 3, "column_counts": [1, 1, 1], "nonzero": 6},
}
_CONTROL_COLORS = (1, 2, 3, 5, 6, 8, 9)


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
    """Return one structural account used by validation and semantic probes."""
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
    column_target_counts = [0 for _ in range(w)]
    blocked_midpoints: list[tuple[int, int, int]] = []
    wrong_color_vertical_gaps: list[tuple[int, int, int]] = []

    for r in range(1, h - 1):
        for c in range(w):
            above, center, below = values[r - 1][c], values[r][c], values[r + 1][c]
            if center == 0 and above == 7 and below == 7:
                targets.append((r, c))
                target_endpoints.update(((r - 1, c), (r + 1, c)))
                column_target_counts[c] += 1
            elif center != 0 and above == 7 and below == 7:
                blocked_midpoints.append((r, c, center))
            elif center == 0 and above != 0 and above == below and above != 7:
                wrong_color_vertical_gaps.append((r, c, above))

    horizontal_7_gaps: list[tuple[int, int]] = []
    for r, row in enumerate(values):
        for c in range(1, w - 1):
            if row[c] == 0 and row[c - 1] == 7 and row[c + 1] == 7:
                horizontal_7_gaps.append((r, c))

    # Consecutive occupied cells with at least two zeros between them form a
    # wider-gap control.  Restricting to consecutive occupied cells avoids
    # counting a shared-endpoint target chain as one wide span.
    long_vertical_gaps: list[tuple[int, int, int]] = []
    for c in range(w):
        occupied = [r for r in range(h) if values[r][c] != 0]
        for top, bottom in zip(occupied, occupied[1:]):
            if bottom - top >= 3 and values[top][c] == values[bottom][c] == 7:
                long_vertical_gaps.append((top, bottom, c))

    shared_endpoint_chains: list[tuple[int, int]] = []
    for r in range(h - 4):
        for c in range(w):
            if (
                values[r][c] == 7
                and values[r + 1][c] == 0
                and values[r + 2][c] == 7
                and values[r + 3][c] == 0
                and values[r + 4][c] == 7
            ):
                shared_endpoint_chains.append((r, c))

    control_cells: set[tuple[int, int]] = set()
    for r, c in horizontal_7_gaps:
        control_cells.update(((r, c - 1), (r, c + 1)))
    for top, bottom, c in long_vertical_gaps:
        control_cells.update(((top, c), (bottom, c)))
    for r, c, _ in blocked_midpoints:
        control_cells.update(((r - 1, c), (r, c), (r + 1, c)))
    for r, c, _ in wrong_color_vertical_gaps:
        control_cells.update(((r - 1, c), (r + 1, c)))

    explained_nonzero = target_endpoints | control_cells
    unexplained_nonzero = sorted(nonzero_cells - explained_nonzero)
    non_target_control_cells = control_cells - target_endpoints
    complete_contrast_bundle = all(
        (
            horizontal_7_gaps,
            long_vertical_gaps,
            blocked_midpoints,
            wrong_color_vertical_gaps,
            shared_endpoint_chains,
        )
    )

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
        "column_target_counts": column_target_counts,
        "target_column_count": sum(count > 0 for count in column_target_counts),
        "horizontal_7_gaps": horizontal_7_gaps,
        "long_vertical_gaps": long_vertical_gaps,
        "blocked_midpoints": blocked_midpoints,
        "wrong_color_vertical_gaps": wrong_color_vertical_gaps,
        "shared_endpoint_chains": shared_endpoint_chains,
        "control_cells": control_cells,
        "non_target_control_cells": non_target_control_cells,
        "unexplained_nonzero": unexplained_nonzero,
        "complete_contrast_bundle": complete_contrast_bundle,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    return analysis


def _build_anchor(h: int, w: int, num_triplets: int, rng) -> list[list[int]]:
    """Build a randomized target-only member of a canonical shape profile."""
    profile = _CANONICAL_PROFILES.get((h, w))
    if profile is None or profile["num_triplets"] != num_triplets:
        raise ValueError(f"{h}x{w}/{num_triplets} is not a canonical anchor profile")
    grid = full_grid(h, w, 0)
    columns = rng.sample(range(w), num_triplets)
    for c in columns:
        top = rng.randint(0, h - 3)
        grid[top][c] = 7
        grid[top + 2][c] = 7
    return grid


def _build_positive_override(
    h: int, w: int, num_triplets: int, rng
) -> list[list[int]]:
    """Honor every exact-axis Cartesian combination with target-only scenes."""
    grid = full_grid(h, w, 0)
    columns = rng.sample(range(w), num_triplets)
    for c in columns:
        top = rng.randint(0, h - 3)
        grid[top][c] = 7
        grid[top + 2][c] = 7
    return grid


def _place_symbolic(
    grid: list[list[int]],
    cells: dict[tuple[int, int], int],
    *,
    row_offset: int,
    flip_vertical: bool,
    flip_horizontal: bool,
) -> None:
    """Place a 9x9 symbolic footprint with optional reflections."""
    for (base_r, base_c), color in cells.items():
        r = 8 - base_r if flip_vertical else base_r
        c = 8 - base_c if flip_horizontal else base_c
        grid[row_offset + r][c] = color


def _build_contrast(
    h: int, w: int, num_triplets: int, blocked_color: int, wrong_color: int, rng
) -> list[list[int]]:
    """Build a complete shortcut-refuting bundle in a 9x9 footprint."""
    if h not in (9, 10) or w != 9 or num_triplets not in (3, 4):
        raise ValueError("contrast profiles require h in {9,10}, w=9, targets in {3,4}")
    cells: dict[tuple[int, int], int] = {
        # A shared-endpoint chain: two vertical targets, both of which a
        # disjoint-only shortcut incorrectly skips.
        (0, 0): 7,
        (2, 0): 7,
        (4, 0): 7,
        # One independent lawful target.  Its top endpoint and the chain's top
        # endpoint simultaneously form the horizontal 7-0-7 control.
        (0, 2): 7,
        (2, 2): 7,
        # One extra endpoint makes rows 2 and 5 a wider vertical 7-0-0-7
        # control, reusing a lawful target endpoint instead of adding a second
        # isolated pair.
        (5, 2): 7,
        # An occupied vertical midpoint: 7-X-7 must remain X.
        (0, 8): 7,
        (1, 8): blocked_color,
        (2, 8): 7,
        # Matching non-orange endpoints: C-0-C must remain unchanged.
        (5, 8): wrong_color,
        (7, 8): wrong_color,
    }
    if num_triplets == 4:
        # Extend the shared chain by one endpoint.  This contributes one new
        # target with one new component rather than stamping a separate pair.
        cells[(6, 0)] = 7

    grid = full_grid(h, w, 0)
    _place_symbolic(
        grid,
        cells,
        row_offset=rng.randint(0, h - 9),
        flip_vertical=bool(rng.getrandbits(1)),
        flip_horizontal=bool(rng.getrandbits(1)),
    )
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
    num_triplets = _draw_exact_int(
        ctx, overrides, "num_triplets", profile["num_triplets"]
    )
    rng = ctx.draw_rng("layout")

    if overrides:
        grid = _build_positive_override(h, w, num_triplets, rng)
    elif profile["kind"] == "anchor":
        grid = _build_anchor(h, w, num_triplets, rng)
    else:
        blocked_color, wrong_color = rng.sample(_CONTROL_COLORS, 2)
        grid = _build_contrast(
            h, w, num_triplets, blocked_color, wrong_color, rng
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced invalid teaching grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": h,
        "grid_w": w,
        "num_triplets": num_triplets,
    }
    if observed != requested:
        raise AssertionError(f"exact-axis mismatch: requested={requested}, observed={observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    h, w = analysis["height"], analysis["width"]
    if not 7 <= h <= 10:
        errors.append(f"grid height {h} must be in 7..10")
    if not 6 <= w <= 9:
        errors.append(f"grid width {w} must be in 6..9")
    if 0 not in analysis["colors"]:
        errors.append("palette must contain background color 0")
    if not 2 <= analysis["target_count"] <= 4:
        errors.append(
            f"expected 2..4 vertical 7-0-7 targets, found {analysis['target_count']}"
        )
    if analysis["target_column_count"] < 2:
        errors.append("expected lawful targets in at least two columns")
    if analysis["unexplained_nonzero"]:
        preview = analysis["unexplained_nonzero"][:5]
        errors.append(f"found non-zero cells outside targets/declared controls: {preview}")

    if analysis["non_target_control_cells"]:
        if analysis["target_count"] < 3:
            errors.append("contrast scenes must retain at least three lawful targets")
        expected_nonzero = analysis["target_count"] + 8
        if analysis["nonzero_count"] != expected_nonzero:
            errors.append(
                "contrast scene has a damaged target/control footprint: "
                f"expected {expected_nonzero} non-zero cells for "
                f"{analysis['target_count']} targets, found {analysis['nonzero_count']}"
            )
        if not analysis["complete_contrast_bundle"]:
            errors.append(
                "partial contrast scene: require horizontal, wider-gap, occupied-"
                "midpoint, wrong-color, and shared-endpoint controls"
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
        "num_triplets": analysis["target_count"],
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
    if analysis["target_count"] != profile["num_triplets"]:
        reasons.append(
            f"canonical profile {dims} has {profile['num_triplets']} triplets, "
            f"found {analysis['target_count']}"
        )
    column_counts = sorted(
        count for count in analysis["column_target_counts"] if count
    )
    if column_counts != profile["column_counts"]:
        reasons.append(
            f"canonical profile {dims} has target-column counts "
            f"{profile['column_counts']}, found {column_counts}"
        )
    if analysis["nonzero_count"] != profile["nonzero"]:
        reasons.append(
            f"canonical profile {dims} has {profile['nonzero']} non-zero cells, "
            f"found {analysis['nonzero_count']}"
        )
    if analysis["colors"] != {0, 7}:
        reasons.append("canonical inputs use exactly colors 0 and 7")
    if analysis["nonzero_cells"] != analysis["target_endpoints"]:
        reasons.append("canonical anchors contain only target endpoints as non-zero cells")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    h, w = len(values), len(values[0])
    for r in range(1, h - 1):
        for c in range(w):
            if values[r][c] == 0 and values[r - 1][c] == values[r + 1][c] == 7:
                out[r][c] = 4
    return out


def _rival_identity(grid):
    return [row[:] for row in _coerce_grid(grid)]


def _rival_first_target_only(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    targets = _analysis_or_raise(values)["targets"]
    if targets:
        r, c = targets[0]
        out[r][c] = 4
    return out


def _rival_fill_horizontal_and_vertical(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    h, w = len(values), len(values[0])
    for r in range(h):
        for c in range(1, w - 1):
            if values[r][c] == 0 and values[r][c - 1] == values[r][c + 1] == 7:
                out[r][c] = 4
    return out


def _rival_fill_long_vertical_spans(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    for top, bottom, c in _analysis_or_raise(values)["long_vertical_gaps"]:
        for r in range(top + 1, bottom):
            out[r][c] = 4
    return out


def _rival_overwrite_blocked_midpoints(grid):
    values = _coerce_grid(grid)
    out = rule_mirror(values)
    for r, c, _ in _analysis_or_raise(values)["blocked_midpoints"]:
        out[r][c] = 4
    return out


def _rival_fill_any_color_vertical(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    h, w = len(values), len(values[0])
    for r in range(1, h - 1):
        for c in range(w):
            if (
                values[r][c] == 0
                and values[r - 1][c] != 0
                and values[r - 1][c] == values[r + 1][c]
            ):
                out[r][c] = 4
    return out


def _rival_disjoint_targets_only(grid):
    values = _coerce_grid(grid)
    out = [row[:] for row in values]
    targets = _analysis_or_raise(values)["targets"]
    endpoint_use: dict[tuple[int, int], int] = {}
    for r, c in targets:
        for endpoint in ((r - 1, c), (r + 1, c)):
            endpoint_use[endpoint] = endpoint_use.get(endpoint, 0) + 1
    for r, c in targets:
        if endpoint_use[(r - 1, c)] == endpoint_use[(r + 1, c)] == 1:
            out[r][c] = 4
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "first_target_only": _rival_first_target_only,
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "fill_long_vertical_spans": _rival_fill_long_vertical_spans,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked_midpoints,
    "fill_any_color_vertical": _rival_fill_any_color_vertical,
    "disjoint_targets_only": _rival_disjoint_targets_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every shortcut below reproduces all four canonical train/test pairs.  Their
# names match SEMANTIC_RIVALS so the semantic gate requires generated,
# oracle-verified counterexamples rather than trusting prose claims.
CANONICAL_SHORTCUTS = {
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "fill_long_vertical_spans": _rival_fill_long_vertical_spans,
    "overwrite_blocked_midpoints": _rival_overwrite_blocked_midpoints,
    "fill_any_color_vertical": _rival_fill_any_color_vertical,
    "disjoint_targets_only": _rival_disjoint_targets_only,
}


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return None if analysis.get("errors") else analysis


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: strict_canonical_like(grid) == [],
    "multiple_targets": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["target_count"] >= 2
    ),
    "horizontal_7_gap_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["horizontal_7_gaps"])
    ),
    "long_vertical_gap_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["long_vertical_gaps"])
    ),
    "blocked_midpoint_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["blocked_midpoints"])
    ),
    "wrong_color_vertical_control": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["wrong_color_vertical_gaps"])
    ),
    "shared_endpoint_chain": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and bool(analysis["shared_endpoint_chains"])
    ),
    "complete_contrast_bundle": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["complete_contrast_bundle"]
    ),
}

WITNESS_RIVALS = {
    "strict_canonical_profile": ["first_target_only"],
    "multiple_targets": ["identity", "first_target_only"],
    "horizontal_7_gap_control": ["fill_horizontal_and_vertical"],
    "long_vertical_gap_control": ["fill_long_vertical_spans"],
    "blocked_midpoint_control": ["overwrite_blocked_midpoints"],
    "wrong_color_vertical_control": ["fill_any_color_vertical"],
    "shared_endpoint_chain": ["disjoint_targets_only"],
    "complete_contrast_bundle": [
        "fill_horizontal_and_vertical",
        "fill_long_vertical_spans",
        "overwrite_blocked_midpoints",
        "fill_any_color_vertical",
        "disjoint_targets_only",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return [] only when examples validate and refute every named rival."""
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
            reasons.append(f"{label} output disagrees with the intended vertical rule")
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
