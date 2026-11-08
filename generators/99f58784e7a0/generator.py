"""Generator for 99f58784e7a0 — fill each walled chamber from its seed.

Color-8 full rows and columns form two to four rectangular chambers.  Every
chamber contains exactly one nonzero, non-8 seed.  The output preserves the
walls and fills each chamber with its own seed color.

The sampler intentionally includes repeated seed colors across different
chambers.  Canonical examples use globally distinct seed colors, so those
lessons refute the plausible but wrong shortcut "only fill when chamber colors
are globally unique".
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99f58784e7a0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5f0096488100"

SUMMARY = (
    "Full color-8 wall rows and columns partition a 0-background grid into "
    "two to four rectangular chambers. Each chamber contains exactly one "
    "nonzero, non-8 seed cell; fill every non-wall cell in that chamber with "
    "its seed color. The curriculum covers vertical, horizontal, and 2x2 wall "
    "layouts at canonical and expanded scales, and alternates globally "
    "distinct versus deliberately reused seed colors."
)

INVARIANTS = [
    "background is color 0; walls are color 8; all cells are ARC colors 0..9",
    "the outer border and every divider are complete color-8 rows or columns",
    "wall lines enclose 2..4 rectangular chambers, each at least 2x2",
    "each chamber contains exactly one nonzero, non-8 seed and at least one background cell",
    "the output fills each chamber independently; equal seed colors may occur in multiple chambers",
]

LAYOUT_PROFILES = (
    "vertical_unequal",
    "vertical_equal",
    "horizontal_three",
    "grid_2x2",
)
SCALES = ("canonical", "expanded")
COLOR_PATTERNS = ("distinct", "reused")

# Interior row spans, interior column spans.  Canonical entries exactly cover
# all public morphologies; expanded entries add one cell to every chamber side.
_LAYOUT_SPANS: dict[tuple[str, str], tuple[tuple[int, ...], tuple[int, ...]]] = {
    ("vertical_unequal", "canonical"): ((2, 3), (8,)),
    ("vertical_unequal", "expanded"): ((3, 4), (9,)),
    ("vertical_equal", "canonical"): ((3, 3), (7,)),
    ("vertical_equal", "expanded"): ((4, 4), (8,)),
    ("horizontal_three", "canonical"): ((8,), (3, 3, 2)),
    ("horizontal_three", "expanded"): ((9,), (4, 4, 3)),
    ("grid_2x2", "canonical"): ((3, 3), (4, 4)),
    ("grid_2x2", "expanded"): ((4, 4), (5, 5)),
}

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "eight-sample schedule covering all four canonical layout families",
        "valid": "|".join(LAYOUT_PROFILES),
    },
    "scale": {
        "type": "str",
        "default": "scheduled canonical|expanded",
        "valid": "|".join(SCALES),
    },
    "color_pattern": {
        "type": "str",
        "default": "alternating distinct|reused",
        "valid": "|".join(COLOR_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# Alternation guarantees every three-demo window contains a repeated-color
# witness.  Canonical-scale/distinct entries guarantee exact profile-floor hits
# in every 20-draw band check.
_PROFILES = (
    {"layout_profile": "vertical_unequal", "scale": "canonical", "color_pattern": "distinct"},
    {"layout_profile": "vertical_equal", "scale": "expanded", "color_pattern": "reused"},
    {"layout_profile": "horizontal_three", "scale": "canonical", "color_pattern": "distinct"},
    {"layout_profile": "grid_2x2", "scale": "expanded", "color_pattern": "reused"},
    {"layout_profile": "vertical_equal", "scale": "canonical", "color_pattern": "distinct"},
    {"layout_profile": "horizontal_three", "scale": "expanded", "color_pattern": "reused"},
    {"layout_profile": "grid_2x2", "scale": "canonical", "color_pattern": "distinct"},
    {"layout_profile": "vertical_unequal", "scale": "expanded", "color_pattern": "reused"},
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))
_SEED_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic curriculum profile used for this sample."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    # Keep the same complete eight-profile cycle in every band while shifting
    # its phase so named difficulty bands are not byte-identical.
    offset = {None: 0, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    return (sample_index + offset) % len(_PROFILES)


def _draw_scheduled_choice(ctx, overrides, label: str, default: str, options):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _wall_indices(spans: tuple[int, ...]) -> tuple[int, ...]:
    indices = [0]
    cursor = 0
    for span in spans:
        cursor += span + 1
        indices.append(cursor)
    return tuple(indices)


def _build_grid(row_spans: tuple[int, ...], col_spans: tuple[int, ...]) -> tuple[list[list[int]], tuple[int, ...], tuple[int, ...]]:
    wall_rows = _wall_indices(row_spans)
    wall_cols = _wall_indices(col_spans)
    height = wall_rows[-1] + 1
    width = wall_cols[-1] + 1
    grid = full_grid(height, width, 0)
    for r in wall_rows:
        for c in range(width):
            grid[r][c] = 8
    for c in wall_cols:
        for r in range(height):
            grid[r][c] = 8
    return grid, wall_rows, wall_cols


def _chamber_cells(wall_rows: tuple[int, ...], wall_cols: tuple[int, ...]):
    for ra, rb in zip(wall_rows, wall_rows[1:]):
        for ca, cb in zip(wall_cols, wall_cols[1:]):
            yield tuple((r, c) for r in range(ra + 1, rb) for c in range(ca + 1, cb))


def _seed_colors(rng, count: int, pattern: str) -> list[int]:
    if pattern == "distinct":
        return rng.sample(list(_SEED_PALETTE), count)
    if pattern != "reused":
        raise ValueError(f"unknown color pattern: {pattern!r}")
    if count == 2:
        color = rng.choice(_SEED_PALETTE)
        return [color, color]
    colors = rng.sample(list(_SEED_PALETTE), count - 1)
    colors.append(rng.choice(colors))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not str:
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")

    profile = _PROFILES[schedule_profile(seed, sample_index, difficulty)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_profile = _draw_scheduled_choice(
        ctx, overrides, "layout_profile", profile["layout_profile"], LAYOUT_PROFILES
    )
    scale = _draw_scheduled_choice(ctx, overrides, "scale", profile["scale"], SCALES)
    color_pattern = _draw_scheduled_choice(
        ctx, overrides, "color_pattern", profile["color_pattern"], COLOR_PATTERNS
    )

    row_spans, col_spans = _LAYOUT_SPANS[(layout_profile, scale)]
    grid, wall_rows, wall_cols = _build_grid(row_spans, col_spans)
    chambers = list(_chamber_cells(wall_rows, wall_cols))
    colors = _seed_colors(ctx.draw_rng("seed_colors"), len(chambers), color_pattern)
    position_rng = ctx.draw_rng("seed_positions")
    for cells, color in zip(chambers, colors):
        r, c = position_rng.choice(cells)
        grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid chamber lesson: " + "; ".join(errors))
    requested = ctx.recorded_draws()
    observed = observe_overrides(grid)
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "height": 0,
        "width": 0,
        "wall_rows": (),
        "wall_cols": (),
        "row_spans": (),
        "col_spans": (),
        "chambers": (),
        "seed_colors": (),
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("expected a nonempty rectangular grid")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("expected nonempty rows")
        return result
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("ragged grid")
        return result
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return result

    height = len(grid)
    wall_rows = tuple(r for r in range(height) if all(grid[r][c] == 8 for c in range(width)))
    wall_cols = tuple(c for c in range(width) if all(grid[r][c] == 8 for r in range(height)))
    result.update(height=height, width=width, wall_rows=wall_rows, wall_cols=wall_cols)

    if not wall_rows or wall_rows[0] != 0 or wall_rows[-1] != height - 1:
        errors.append("top and bottom borders must be complete color-8 rows")
    if not wall_cols or wall_cols[0] != 0 or wall_cols[-1] != width - 1:
        errors.append("left and right borders must be complete color-8 columns")
    if errors:
        return result

    expected_walls = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in wall_rows or c in wall_cols
    }
    actual_walls = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 8}
    if actual_walls != expected_walls:
        errors.append("every color-8 cell must belong to a complete wall row or column")

    row_spans = tuple(b - a - 1 for a, b in zip(wall_rows, wall_rows[1:]))
    col_spans = tuple(b - a - 1 for a, b in zip(wall_cols, wall_cols[1:]))
    result.update(row_spans=row_spans, col_spans=col_spans)
    if not row_spans or not col_spans:
        errors.append("walls must enclose at least one chamber")
        return result
    if min(row_spans + col_spans) < 2:
        errors.append("every chamber must be at least 2x2")

    chamber_count = len(row_spans) * len(col_spans)
    if not 2 <= chamber_count <= 4:
        errors.append(f"expected 2..4 chambers, found {chamber_count}")

    chambers = []
    seed_colors = []
    for ra, rb in zip(wall_rows, wall_rows[1:]):
        for ca, cb in zip(wall_cols, wall_cols[1:]):
            cells = tuple((r, c) for r in range(ra + 1, rb) for c in range(ca + 1, cb))
            seeds = tuple((r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 8))
            if len(seeds) != 1:
                errors.append(f"chamber {(ra, ca, rb, cb)} must contain exactly one seed; found {len(seeds)}")
            elif not any(grid[r][c] == 0 for r, c in cells):
                errors.append(f"chamber {(ra, ca, rb, cb)} has no background cell to fill")
            chambers.append({"bounds": (ra, ca, rb, cb), "cells": cells, "seeds": seeds})
            if len(seeds) == 1:
                seed_colors.append(seeds[0][2])

    result.update(chambers=tuple(chambers), seed_colors=tuple(seed_colors))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Return domain-lawfulness errors for strict-profile accounting."""
    return self_check(grid)


def _profile_from_spans(row_spans, col_spans) -> tuple[str, str] | None:
    matches = [key for key, spans in _LAYOUT_SPANS.items() if spans == (row_spans, col_spans)]
    return matches[0] if len(matches) == 1 else None


def observe_overrides(grid) -> dict[str, str]:
    """Recover every advertised exact axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    profile = _profile_from_spans(analysis["row_spans"], analysis["col_spans"])
    if profile is None:
        return {}
    layout_profile, scale = profile
    colors = analysis["seed_colors"]
    color_pattern = "distinct" if len(set(colors)) == len(colors) else "reused"
    return {
        "layout_profile": layout_profile,
        "scale": scale,
        "color_pattern": color_pattern,
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the canonical connected-chamber fill rule."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = deepcopy(grid)
    for chamber in analysis["chambers"]:
        color = chamber["seeds"][0][2]
        for r, c in chamber["cells"]:
            out[r][c] = color
    return out


def _distinct_colors_only(grid) -> list[list[int]]:
    """Rival: incorrectly requires globally unique chamber seed colors."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    colors = analysis["seed_colors"]
    if len(set(colors)) != len(colors):
        return deepcopy(grid)
    return rule_mirror(grid)


def _has_reused_seed_color(grid) -> bool:
    analysis = _analyze(grid)
    colors = analysis["seed_colors"]
    return not analysis["errors"] and len(set(colors)) < len(colors)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "reused_seed_color": _has_reused_seed_color,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "distinct_colors_only": _distinct_colors_only,
}
WITNESS_RIVALS = {"reused_seed_color": ["distinct_colors_only"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Check labels and whether a competitor fits demos but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        demos = demos if isinstance(demos, (list, tuple)) else []

    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the chamber-fill rule")
            continue
        valid_demos.append(pair)

    query_input = None
    query_output = None
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        else:
            query_input = query["input"]
            query_output = rule_mirror(query_input)
            if "output" in query and query["output"] != query_output:
                reasons.append("query output disagrees with the chamber-fill rule")

    for name, rival in LESSON_COMPETITORS.items():
        if (
            valid_demos
            and query_input is not None
            and all(rival(pair["input"]) == pair["output"] for pair in valid_demos)
            and rival(query_input) != query_output
        ):
            reasons.append(
                f"declared competitor {name!r} fits every valid demonstration "
                "and changes the query answer"
            )
    return reasons
