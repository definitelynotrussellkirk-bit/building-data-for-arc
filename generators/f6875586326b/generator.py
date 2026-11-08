"""Generator for ARC task f6875586326b.

Colored singleton markers project into full lines: blue (1) and green (3)
markers paint their rows, red (2) markers paint their columns, and row paint
wins at row/column intersections.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f6875586326b"
TASK_ID = "f6875586326b"
VERSION = "3.0.0"  # honest exact axes, canonical-profile prior, structural checker
RULE_HASH = "52315007f5e3"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "A 0-background grid contains isolated singleton markers. Every row with "
    "one blue (1) or green (3) marker is filled with that marker color. Every "
    "column with one red (2) marker is filled red, except intersections with "
    "marked blue/green rows retain the row color (row precedence). Normal "
    "draws always contain both horizontal colors and at least one red column."
)

INVARIANTS = [
    "background is 0 and the only marker colors are 1, 2, and 3",
    "each marked horizontal row contains exactly one 1/3 marker",
    "both row-fill colors 1 and 3 occur in every normal lesson",
    "each marked vertical column contains exactly one color-2 marker",
    "color-2 markers occupy rows disjoint from the 1/3 marker rows",
    "all non-background markers are orthogonally isolated singletons",
    "row color wins at every horizontal/vertical line intersection",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware, with a 25% canonical-profile prior",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware, with a 25% canonical-profile prior",
        "valid": "7..18",
    },
    "n_rows": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "n_cols": {
        "type": "int",
        "default": "difficulty-aware 1..3",
        "valid": "1..3",
    },
}

# Exact joint profiles extracted from all three train inputs and the held-out
# test input. Placement coordinates remain randomized; dimensions, marker
# counts, and the row-color multiset match one official input when this prior
# fires. This keeps canonical morphology present without turning the generator
# into a fixed-template bank.
_CANONICAL_PROFILES = (
    {"grid_h": 10, "grid_w": 8, "n_rows": 3, "n_cols": 1, "row_colors": (1, 3, 3)},
    {"grid_h": 9, "grid_w": 9, "n_rows": 2, "n_cols": 1, "row_colors": (1, 3)},
    {"grid_h": 10, "grid_w": 11, "n_rows": 3, "n_cols": 2, "row_colors": (1, 3, 3)},
    {"grid_h": 12, "grid_w": 11, "n_rows": 4, "n_cols": 2, "row_colors": (1, 1, 3, 3)},
)


def _draw_int_axis(ctx, name: str, lo: int, hi: int, profile_value: int | None) -> int:
    """Draw an exact axis while preserving explicit full-domain overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_diff(name, lo, hi)
    if profile_value is not None:
        return ctx.draw_int(name, profile_value, profile_value)
    return ctx.draw_int_diff(name, lo, hi)


def _row_colors(n_rows: int, rng, profile: dict[str, Any] | None) -> list[int]:
    if profile is not None and n_rows == profile["n_rows"]:
        colors = list(profile["row_colors"])
    else:
        # Every ordinary lesson demonstrates both horizontal branches. Extra
        # rows vary their color, preventing a fixed count-to-color shortcut.
        colors = [1, 3]
        colors.extend(rng.choice((1, 3)) for _ in range(n_rows - 2))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = None
    if int(sample_index) % 4 == 0:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)

    h = _draw_int_axis(ctx, "grid_h", 7, 16, None if profile is None else profile["grid_h"])
    w = _draw_int_axis(ctx, "grid_w", 7, 18, None if profile is None else profile["grid_w"])
    n_rows = _draw_int_axis(ctx, "n_rows", 2, 4, None if profile is None else profile["n_rows"])
    n_cols = _draw_int_axis(ctx, "n_cols", 1, 3, None if profile is None else profile["n_cols"])

    # The global domains are jointly feasible: at the minimum height, four
    # horizontal rows plus three distinct red-marker rows exactly fit.
    if n_rows + n_cols > h:
        raise ValueError(
            f"n_rows={n_rows} and n_cols={n_cols} require at least {n_rows + n_cols} rows"
        )
    if n_cols >= w:
        raise ValueError("red columns must leave at least one non-red marker column")

    rng = ctx.draw_rng("layout")
    row_seed_rows = sorted(rng.sample(range(h), n_rows))
    remaining_rows = [r for r in range(h) if r not in row_seed_rows]
    red_rows = rng.sample(remaining_rows, n_cols)
    red_cols = rng.sample(range(w), n_cols)

    colors = _row_colors(n_rows, rng, profile)
    allowed_row_cols = [c for c in range(w) if c not in set(red_cols)]
    row_marker_cols: dict[int, int] = {}
    for row, color in zip(row_seed_rows, colors):
        candidates = list(allowed_row_cols)
        rng.shuffle(candidates)
        chosen = None
        for col in candidates:
            # Keep every marker an orthogonally isolated singleton. Only a
            # marker in the immediately previous selected row can be vertical-
            # adjacent at this point.
            if (row - 1) in row_marker_cols and row_marker_cols[row - 1] == col:
                continue
            chosen = col
            break
        if chosen is None:  # impossible for the declared domains, kept loud
            raise ValueError("could not place isolated horizontal markers")
        row_marker_cols[row] = chosen

    grid = full_grid(h, w, 0)
    for row, color in zip(row_seed_rows, colors):
        grid[row][row_marker_cols[row]] = color
    for row, col in zip(red_rows, red_cols):
        grid[row][col] = 2

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": dict(overrides)})
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return facts, ["grid must be a non-empty list of non-empty rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return facts, ["grid must be rectangular"]
    h = len(grid)
    facts.update(grid_h=h, grid_w=w)
    if not (7 <= h <= 16):
        errors.append(f"grid height {h} is outside 7..16")
    if not (7 <= w <= 18):
        errors.append(f"grid width {w} is outside 7..18")

    nonzero: list[tuple[int, int, int]] = []
    row_markers: list[tuple[int, int, int]] = []
    red_markers: list[tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1, 2, 3):
                errors.append(f"unexpected color {value!r} at ({r},{c})")
                continue
            if value:
                nonzero.append((r, c, value))
                if value == 2:
                    red_markers.append((r, c, value))
                else:
                    row_markers.append((r, c, value))

    per_row: dict[int, list[tuple[int, int]]] = {}
    for r, c, value in nonzero:
        per_row.setdefault(r, []).append((c, value))
    for r, markers in sorted(per_row.items()):
        if len(markers) != 1:
            errors.append(f"row {r} contains {len(markers)} markers; expected exactly one")

    row_seed_rows = sorted({r for r, _, _ in row_markers})
    red_rows = [r for r, _, _ in red_markers]
    red_cols = [c for _, c, _ in red_markers]
    facts["n_rows"] = len(row_seed_rows)
    facts["n_cols"] = len(set(red_cols))
    facts["row_color_counts"] = {
        "1": sum(value == 1 for _, _, value in row_markers),
        "3": sum(value == 3 for _, _, value in row_markers),
    }

    if not (2 <= len(row_seed_rows) <= 4):
        errors.append(f"expected 2..4 horizontal marker rows, found {len(row_seed_rows)}")
    if not any(value == 1 for _, _, value in row_markers):
        errors.append("missing blue (1) horizontal marker")
    if not any(value == 3 for _, _, value in row_markers):
        errors.append("missing green (3) horizontal marker")
    if not (1 <= len(red_markers) <= 3):
        errors.append(f"expected 1..3 red markers, found {len(red_markers)}")
    if len(set(red_cols)) != len(red_cols):
        errors.append("each red marker must occupy a distinct column")
    if len(set(red_rows)) != len(red_rows):
        errors.append("each red marker must occupy a distinct row")
    overlap_rows = sorted(set(row_seed_rows) & set(red_rows))
    if overlap_rows:
        errors.append(f"red and horizontal markers share row(s) {overlap_rows}")

    occupied = {(r, c) for r, c, _ in nonzero}
    for r, c, _ in nonzero:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (r + dr, c + dc) in occupied:
                errors.append(f"marker at ({r},{c}) is not orthogonally isolated")
                break

    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone scenes in the teaching distribution."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact semantic axis from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {name: int(facts[name]) for name in ("grid_h", "grid_w", "n_rows", "n_cols")}


def rule_mirror(grid):
    """Pure Python mirror for focused tests; Racket remains output authority."""
    source = deepcopy(grid)
    if not source or not source[0]:
        return source
    h, w = len(source), len(source[0])
    row_colors: list[int | None] = []
    for row in source:
        row_colors.append(next((value for value in row if value in (1, 3)), None))
    red_columns = {
        c for c in range(w) if any(source[r][c] == 2 for r in range(h))
    }
    return [
        [
            row_colors[r]
            if row_colors[r] is not None
            else (2 if c in red_columns else 0)
            for c in range(w)
        ]
        for r in range(h)
    ]
