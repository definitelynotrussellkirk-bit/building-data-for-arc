"""Generator for rows/columns -> Cartesian intersection mask.

Color 1 on the left border selects rows.  Color 2 on the top border selects
columns.  The selected Racket authority returns a blank grid with color 8 at
every selected-row x selected-column intersection.

Generated inputs deliberately include role-swapped border decoys (1s on the top
border and/or 2s on the left border).  They are ignored by the authority and
rule out the canonical-data shortcut "every nonzero border cell selects an
axis".  Correct marker sets are gapped, so bounding-box/rectangle-fill rules are
also visibly wrong.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f6a6ec3ae21"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ca6d5269f15c"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Color-1 markers on the left border select rows and color-2 markers on the "
    "top border select columns.  Return a zero grid with color 8 at every "
    "Cartesian-product intersection.  Generated boards use gapped selected "
    "coordinates and at least one role-swapped border decoy by default, so a "
    "solver must attend to both color and border role rather than treating all "
    "border marks alike or filling their bounding rectangle."
)

INVARIANTS = [
    "the origin is 0 and the interior is empty before transformation",
    "2..4 color-1 selectors occupy column 0 at gapped rows",
    "2..4 color-2 selectors occupy row 0 at gapped columns",
    "0..1 color-1 top-border decoy and 0..1 color-2 left-border decoy may appear",
    "the output clears every input marker and paints only selector intersections with 8",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchor every third sample; otherwise difficulty-weighted 6..10",
        "valid": "6..10",
        "doc": "Exact observable grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchor every third sample; otherwise difficulty-weighted 7..12",
        "valid": "7..12",
        "doc": "Exact observable grid width.",
    },
    "n_marks_1": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
        "doc": "Exact number of color-1 row selectors in column 0.",
    },
    "n_marks_2": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
        "doc": "Exact number of color-2 column selectors in row 0.",
    },
    "n_row_decoys": {
        "type": "int",
        "default": "0 or 1; paired schedule guarantees a default decoy on one border",
        "valid": "0..1",
        "doc": "Exact count of wrong-role color-1 decoys on row 0.",
    },
    "n_col_decoys": {
        "type": "int",
        "default": "0 or 1; paired schedule guarantees a default decoy on one border",
        "valid": "0..1",
        "doc": "Exact count of wrong-role color-2 decoys in column 0.",
    },
}

# Every cross-product combination is constructive, including h=6 with four
# row selectors plus one left-border decoy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_HEIGHTS = tuple(range(6, 11))
_WIDTHS = tuple(range(7, 13))
_MARK_COUNTS = (2, 3, 4)
_DECOY_COUNTS = (0, 1)
_CANONICAL_PROFILES = ((6, 8), (6, 9), (7, 9))


def _is_gapped(values) -> bool:
    values = sorted(values)
    return len(values) >= 2 and values[-1] - values[0] + 1 > len(values)


def _scheduled_choice(ctx, label: str, domain: tuple[int, ...], target: int) -> int:
    """Draw through GenCtx while deterministically realizing a scheduled value.

    ``draw_choice`` owns override validation/provenance.  With no override, the
    full legal domain is reordered so the keyed RNG's chosen index contains the
    scheduled target.  Thus schedule guarantees do not narrow the advertised
    override domain or bypass GenCtx.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, domain)
    options = list(domain)
    chosen_index = ctx.draw_rng(label).randrange(len(options))
    target_index = options.index(target)
    options[chosen_index], options[target_index] = options[target_index], options[chosen_index]
    return ctx.draw_choice(label, tuple(options))


def _weighted_options(domain: tuple[int, ...], difficulty, *, kind: str) -> tuple[int, ...]:
    """Full-domain options plus band-specific repeats; overrides stay universal."""
    options = list(domain)
    if kind == "height":
        favored = {
            "easy": (6, 6, 7),
            "medium": (7, 8, 8),
            "hard": (9, 10, 10),
        }.get(difficulty, (6, 7, 8, 9, 10))
    elif kind == "width":
        favored = {
            "easy": (7, 8, 8),
            "medium": (8, 9, 10),
            "hard": (10, 11, 12, 12),
        }.get(difficulty, (7, 8, 9, 10, 11, 12))
    else:
        favored = {
            "easy": (2, 2, 2, 3),
            "medium": (2, 3, 3, 3, 4),
            "hard": (3, 4, 4, 4),
        }.get(difficulty, (2, 3, 4))
    options.extend(favored)
    return tuple(options)


@lru_cache(maxsize=128)
def _axis_layouts(axis_length: int, n_correct: int, n_decoy: int):
    """All gapped correct-marker sets with disjoint optional decoys."""
    positions = tuple(range(1, axis_length))
    layouts = []
    for correct in combinations(positions, n_correct):
        if not _is_gapped(correct):
            continue
        remaining = tuple(value for value in positions if value not in correct)
        for decoys in combinations(remaining, n_decoy):
            layouts.append((correct, decoys))
    return tuple(layouts)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (6, 10),
        "grid_w": (7, 12),
        "n_marks_1": (2, 4),
        "n_marks_2": (2, 4),
        "n_row_decoys": (0, 1),
        "n_col_decoys": (0, 1),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # One third of default draws are exact canonical-size anchors; the other
    # draws broaden scale in every band.  Explicit dimensions always win.
    if sample_index % 3 == 0:
        target_h, target_w = _CANONICAL_PROFILES[(seed + sample_index) % len(_CANONICAL_PROFILES)]
        h = _scheduled_choice(ctx, "grid_h", _HEIGHTS, target_h)
        w = _scheduled_choice(ctx, "grid_w", _WIDTHS, target_w)
    else:
        h = ctx.draw_choice("grid_h", _weighted_options(_HEIGHTS, difficulty, kind="height"))
        w = ctx.draw_choice("grid_w", _weighted_options(_WIDTHS, difficulty, kind="width"))

    n_marks_1 = ctx.draw_choice(
        "n_marks_1", _weighted_options(_MARK_COUNTS, difficulty, kind="marks")
    )
    n_marks_2 = ctx.draw_choice(
        "n_marks_2", _weighted_options(_MARK_COUNTS, difficulty, kind="marks")
    )

    row_explicit = overrides.get("n_row_decoys") is not None
    col_explicit = overrides.get("n_col_decoys") is not None
    if row_explicit and col_explicit:
        row_target = int(overrides["n_row_decoys"])
        col_target = int(overrides["n_col_decoys"])
    elif row_explicit:
        row_target = int(overrides["n_row_decoys"])
        col_target = 0 if row_target else 1
    elif col_explicit:
        col_target = int(overrides["n_col_decoys"])
        row_target = 0 if col_target else 1
    else:
        row_target = sample_index % 2
        col_target = 1 - row_target
    n_row_decoys = _scheduled_choice(ctx, "n_row_decoys", _DECOY_COUNTS, row_target)
    n_col_decoys = _scheduled_choice(ctx, "n_col_decoys", _DECOY_COUNTS, col_target)

    row_layouts = _axis_layouts(w, n_marks_2, n_row_decoys)
    col_layouts = _axis_layouts(h, n_marks_1, n_col_decoys)
    if not row_layouts or not col_layouts:
        raise ValueError(
            "override combination cannot realize gapped selectors and disjoint decoys"
        )
    selected_cols, row_decoy_cols = ctx.draw_rng("row_axis_layout").choice(row_layouts)
    selected_rows, col_decoy_rows = ctx.draw_rng("column_axis_layout").choice(col_layouts)

    grid = full_grid(h, w, 0)
    for col in selected_cols:
        grid[0][col] = 2
    for col in row_decoy_cols:
        grid[0][col] = 1
    for row in selected_rows:
        grid[row][0] = 1
    for row in col_decoy_rows:
        grid[row][0] = 2
    return grid


def _grid_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _selectors(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if grid[r][0] == 1]
    cols = [c for c in range(w) if grid[0][c] == 2]
    return rows, cols


def rule_mirror(grid):
    """Independent Python mirror used only for diagnostics and parity checks."""
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = shape
    rows, cols = _selectors(grid)
    out = full_grid(h, w, 0)
    for row in rows:
        for col in cols:
            out[row][col] = 8
    return out


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    return {
        "grid_h": h,
        "grid_w": w,
        "n_marks_1": sum(grid[r][0] == 1 for r in range(1, h)),
        "n_marks_2": sum(grid[0][c] == 2 for c in range(1, w)),
        "n_row_decoys": sum(grid[0][c] == 1 for c in range(1, w)),
        "n_col_decoys": sum(grid[r][0] == 2 for r in range(1, h)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a nonempty rectangular sequence of nonempty rows"]
    h, w = shape
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9"]

    errors = []
    if not 6 <= h <= 10:
        errors.append(f"grid height {h} outside 6..10")
    if not 7 <= w <= 12:
        errors.append(f"grid width {w} outside 7..12")
    if grid[0][0] != 0:
        errors.append("origin must stay background 0")
    if any(value not in (0, 1, 2) for row in grid for value in row):
        errors.append("input may contain only colors 0, 1, and 2")
    if any(grid[r][c] != 0 for r in range(1, h) for c in range(1, w)):
        errors.append("interior must be empty before transformation")

    selected_rows = [r for r in range(1, h) if grid[r][0] == 1]
    selected_cols = [c for c in range(1, w) if grid[0][c] == 2]
    row_decoys = [c for c in range(1, w) if grid[0][c] == 1]
    col_decoys = [r for r in range(1, h) if grid[r][0] == 2]

    if not 2 <= len(selected_rows) <= 4:
        errors.append(f"column 0 must contain 2..4 color-1 selectors, found {len(selected_rows)}")
    elif not _is_gapped(selected_rows):
        errors.append("color-1 selector rows must contain at least one gap")
    if not 2 <= len(selected_cols) <= 4:
        errors.append(f"row 0 must contain 2..4 color-2 selectors, found {len(selected_cols)}")
    elif not _is_gapped(selected_cols):
        errors.append("color-2 selector columns must contain at least one gap")
    if not 0 <= len(row_decoys) <= 1:
        errors.append(f"row 0 may contain at most one color-1 decoy, found {len(row_decoys)}")
    if not 0 <= len(col_decoys) <= 1:
        errors.append(f"column 0 may contain at most one color-2 decoy, found {len(col_decoys)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All generated instances and every canonical input lie in this manifold."""
    return self_check(grid)


def _rival_paired_only(grid):
    """Wrong rule: pair sorted row/column markers one-to-one instead of product."""
    h, w = len(grid), len(grid[0])
    rows, cols = _selectors(grid)
    out = full_grid(h, w, 0)
    for row, col in zip(rows, cols):
        out[row][col] = 8
    return out


def _rival_bounding_box_fill(grid):
    """Wrong rule: fill the entire selector bounding rectangle."""
    h, w = len(grid), len(grid[0])
    rows, cols = _selectors(grid)
    out = full_grid(h, w, 0)
    if rows and cols:
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                out[row][col] = 8
    return out


def _rival_preserve_markers(grid):
    """Wrong rule: paint intersections without clearing input markers."""
    out = [list(row) for row in grid]
    rows, cols = _selectors(grid)
    for row in rows:
        for col in cols:
            out[row][col] = 8
    return out


def _rival_any_nonzero_axes(grid):
    """Canonical-fitting shortcut: every nonzero border marker selects an axis."""
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if grid[r][0] != 0]
    cols = [c for c in range(w) if grid[0][c] != 0]
    out = full_grid(h, w, 0)
    for row in rows:
        for col in cols:
            out[row][col] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "paired_only": _rival_paired_only,
    "bounding_box_fill": _rival_bounding_box_fill,
    "preserve_markers": _rival_preserve_markers,
    "any_nonzero_axes": _rival_any_nonzero_axes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Public canonical pairs contain no role-swapped border marks, so this shortcut
# agrees with every canonical label and needs generated counterexamples.
CANONICAL_SHORTCUTS = {"any_nonzero_axes": _rival_any_nonzero_axes}


def _witness_cartesian_product(grid) -> bool:
    rows, cols = _selectors(grid)
    return len(rows) >= 2 and len(cols) >= 2 and rule_mirror(grid) != _rival_paired_only(grid)


def _witness_gapped_axes(grid) -> bool:
    rows, cols = _selectors(grid)
    return _is_gapped(rows) and _is_gapped(cols) and rule_mirror(grid) != _rival_bounding_box_fill(grid)


def _witness_clear_markers(grid) -> bool:
    return rule_mirror(grid) != _rival_preserve_markers(grid)


def _witness_role_specific_markers(grid) -> bool:
    observed = observe_overrides(grid)
    return (
        observed["n_row_decoys"] + observed["n_col_decoys"] > 0
        and rule_mirror(grid) != _rival_any_nonzero_axes(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "cartesian_product": _witness_cartesian_product,
    "gapped_axes": _witness_gapped_axes,
    "clear_markers": _witness_clear_markers,
    "role_specific_markers": _witness_role_specific_markers,
}
WITNESS_RIVALS = {
    "cartesian_product": ["paired_only"],
    "gapped_axes": ["bounding_box_fill"],
    "clear_markers": ["preserve_markers"],
    "role_specific_markers": ["any_nonzero_axes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named rival that fits demos but disagrees on the query."""
    official_query = rule_mirror(query["input"])
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != official_query:
                errors.append(f"demos do not rule out rival operation {name}")
    return errors
