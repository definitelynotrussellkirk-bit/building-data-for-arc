"""Inputs for d2acf2cb: paired 4 endpoints gate one involutive palette swap.

The unchanged Racket rule swaps 0<->8 and 6<->7 on the UNION of complete
anchored rows and columns. Crossings swap once; a lone endpoint is inactive.
Outputs always come from the reference runtime. Default draws alternate exact
canonical profiles and diagnostic scenes with both axes, both swap directions,
and incomplete endpoints on all four sides. Four consecutive draws contain two
diagnostics, so every 3-demo/1-query holdout retains one. This finite-rival
contract applies to unoverridden defaults, not arbitrary filtered assemblies.
"""
from __future__ import annotations

import math
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "832404dc8a5c"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "bce3d4596195"
SUMMARY = ("Paired 4 endpoints activate rows/columns; swap 0<->8 and 6<->7 "
           "once on their union. Canonical profiles alternate with mixed-palette, "
           "crossing and incomplete-endpoint teaching scenes, up to 30x30.")
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = ("canonical_0", "canonical_1", "canonical_2", "canonical_3", "diagnostic")
MIN_STRICT_FRAC = 0.25
INVARIANTS = [
    "rectangular integer grid, height 6..30 and width 8..30, colors {0,4,6,7,8}",
    "4 markers occur only on non-corner boundary endpoints; incomplete pairs are distractors",
    "7/8 occur only in complete anchored lanes; other non-marker cells use 0/6",
    "crossings receive one swap; processing order has no semantic role",
    "lane-free identity cases contain at least five cells of each field color",
]
DEGENERATE_TEXTURES = ("no_anchors", "all_anchored", "single_anchor")
# Deliberate lawful identity/extreme cases, not negative fixtures.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
_PALETTES = ("mixed", "swapped", "base")
AXES = {
    "grid_h": {"type": "int", "default": "canonical profile or band 8..30", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "canonical 9 or band 8..30", "valid": "8..30"},
    "n_anchored_rows": {"type": "int", "default": "scheduled 0..3", "valid": "0..4"},
    "n_anchored_cols": {"type": "int", "default": "scheduled 0..3", "valid": "0..4"},
    "zero_density": {"type": "float", "default": "rng 0.35..0.55", "valid": "0.1..0.7"},
    "lane_palette": {"type": "str", "default": "canonical base/swapped; diagnostic mixed within lanes", "valid": "mixed|swapped|base"},
    "texture": {"type": "str", "default": "none", "valid": "none|no_anchors|all_anchored|single_anchor"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_anchored_rows": 0, "n_anchored_cols": 0},
    {"texture": "no_anchors", "n_anchored_rows": None},
    {"texture": "no_anchors", "n_anchored_cols": None},
    {"texture": "no_anchors", "lane_palette": None},
    {"texture": "all_anchored", "n_anchored_rows": None},
    {"texture": "all_anchored", "n_anchored_cols": None},
    {"texture": "single_anchor", "n_anchored_rows": None},
    {"texture": "single_anchor", "n_anchored_cols": None},
]
_SWAP = {0: 8, 8: 0, 6: 7, 7: 6}
# h, w, row count, column count, lane style. Cells/positions are resampled.
_CANONICAL_PROFILES = ((9, 9, 3, 0, "swapped"), (7, 9, 1, 0, "base"),
                       (6, 9, 0, 2, "base"), (10, 9, 0, 3, "base"))


def _lanes(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(1, h - 1) if grid[r][0] == grid[r][-1] == 4]
    cols = [c for c in range(1, w - 1) if grid[0][c] == grid[-1][c] == 4]
    return rows, cols


def observe_overrides(grid):
    rows, cols = _lanes(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_anchored_rows": len(rows), "n_anchored_cols": len(cols)}


def self_check(grid, *, difficulty=None, meta=None):
    """Input grammar, including a bounded dense identity edge case."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty first row"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (6 <= h <= 30 and 8 <= w <= 30):
        return ["grid outside declared 6..30 by 8..30 envelope"]
    if any(type(v) is not int or v not in (0, 4, 6, 7, 8) for row in grid for v in row):
        return ["cells must be integer colors from {0,4,6,7,8}; bool is not a color"]
    rows, cols = _lanes(grid)
    rs, cs, errors = set(rows), set(cols), []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 4 and not ((0 < r < h - 1 and c in (0, w - 1))
                               or (0 < c < w - 1 and r in (0, h - 1))):
                errors.append(f"marker 4 at ({r},{c}) is not a non-corner boundary endpoint")
            elif v in (7, 8) and r not in rs and c not in cs:
                errors.append(f"value {v} at ({r},{c}) outside complete anchored lanes")
    if not rows and not cols:
        flat = [v for row in grid for v in row]
        if 4 in flat or flat.count(0) < 5 or flat.count(6) < 5:
            errors.append("lane-free identity grammar requires no markers and at least five 0s and five 6s")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    rows, cols = _lanes(grid)
    if w != 9 or not 6 <= h <= 10 or bool(rows) == bool(cols):
        return ["canonical manifold has width 9, height 6..10, exactly one lane orientation"]
    if not 1 <= len(rows) + len(cols) <= 3:
        return ["canonical manifold has one to three lanes"]
    if sum(v == 4 for row in grid for v in row) != 2 * (len(rows) + len(cols)):
        return ["canonical manifold has no incomplete endpoint distractors"]
    values = {grid[r][c] for r in range(h) for c in range(w)
              if (r in rows or c in cols) and grid[r][c] != 4}
    if not (values <= {0, 6} or values <= {7, 8}):
        return ["canonical lanes use one palette direction per grid"]
    return []


def schedule_profile(seed, sample_index, difficulty=None):
    return "diagnostic" if sample_index % 2 else f"canonical_{(sample_index // 2) % 4}"


def _present(overrides, name):
    return name in overrides and overrides[name] is not None


def _int_control(ctx, overrides, name, default, low, high):
    if _present(overrides, name):
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_int_strict(name, default, default)


def _choice_control(ctx, overrides, name, default, values):
    return ctx.draw_choice(name, values if _present(overrides, name) else (default,))


def _fill_field(grid, rng, density):
    for row in grid:
        for c in range(len(row)):
            row[c] = 0 if rng.random() < density else 6


def _paint_lane(grid, rng, density, style, *, row=None, col=None):
    h, w = len(grid), len(grid[0])
    if row is not None:
        grid[row][0] = grid[row][-1] = 4
        cells = [(row, c) for c in range(1, w - 1)]
    else:
        grid[0][col] = grid[-1][col] = 4
        cells = [(r, col) for r in range(1, h - 1)]
    for r, c in cells:
        value = 0 if rng.random() < density else 6
        reverse = style == "swapped" or (style == "mixed" and rng.random() < 0.5)
        grid[r][c] = _SWAP[value] if reverse else value


def _ensure_values(grid, cells, values, rng):
    """Choose witness positions afresh, avoiding fixed positional cues."""
    if len(cells) >= len(values):
        for (r, c), value in zip(rng.sample(cells, len(values)), values):
            grid[r][c] = value


def _complete_palette_support(grid, rows, cols, style, rng):
    h, w = len(grid), len(grid[0])
    active = [(r, c) for r in range(h) for c in range(w)
              if (r in rows or c in cols) and grid[r][c] != 4]
    values = (0, 6, 7, 8) if style == "mixed" else ((7, 8) if style == "swapped" else (0, 6))
    _ensure_values(grid, active, values, rng)
    if style == "mixed":
        _ensure_values(grid, [(r, c) for r in rows for c in range(1, w - 1) if c not in cols], values, rng)
        _ensure_values(grid, [(r, c) for c in cols for r in range(1, h - 1) if r not in rows], values, rng)
    outside = [(r, c) for r in range(h) for c in range(w)
               if r not in rows and c not in cols and grid[r][c] != 4]
    _ensure_values(grid, outside, (0, 6), rng)


def _add_incomplete_endpoints(grid, rows, cols, rng):
    h, w = len(grid), len(grid[0])
    free_rows = [r for r in range(1, h - 1) if r not in rows]
    free_cols = [c for c in range(1, w - 1) if c not in cols]
    # Restricted overrides may remove witness room; their counts remain exact.
    for r, c in zip(rng.sample(free_rows, min(2, len(free_rows))), (0, w - 1)):
        grid[r][c] = 4
    for c, r in zip(rng.sample(free_cols, min(2, len(free_cols))), (0, h - 1)):
        grid[r][c] = 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers, not bool/float/string")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override keys: {unknown}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    diagnostic, band = sample_index % 2 == 1, difficulty or "medium"
    if not diagnostic:
        h0, w0, nr0, nc0, style0 = _CANONICAL_PROFILES[(sample_index // 2) % 4]
    else:
        if band == "easy":
            h0, w0 = rng.randint(8, 13), rng.randint(8, 12)
        elif band == "medium":
            h0, w0 = rng.randint(14, 22), rng.randint(12, 22)
        elif sample_index % 4 == 1:
            h0, w0 = 30, 30
        else:
            h0, w0 = rng.randint(21, 30), rng.randint(18, 29)
        nr0, nc0, style0 = rng.randint(1, 2), rng.randint(1, 2), "mixed"
    h = _int_control(ctx, overrides, "grid_h", h0, 6, 30)
    w = _int_control(ctx, overrides, "grid_w", w0, 8, 30)
    texture = _choice_control(ctx, overrides, "texture", "none", ("none", *DEGENERATE_TEXTURES))
    style = _choice_control(ctx, overrides, "lane_palette", style0, _PALETTES)
    density = overrides.get("zero_density")
    if density is None:
        density = ctx.draw_rng("zero_density").uniform(0.35, 0.55)
    if type(density) not in (int, float) or not 0.1 <= density <= 0.7 or not math.isfinite(density):
        raise ValueError("zero_density must be a finite number in [0.1, 0.7], not bool/string")
    has_rows, has_cols = _present(overrides, "n_anchored_rows"), _present(overrides, "n_anchored_cols")
    if texture in DEGENERATE_TEXTURES:
        if has_rows or has_cols:
            raise ValueError(f"texture={texture!r} fixes layout; lane-count overrides are incompatible")
        if texture == "no_anchors" and _present(overrides, "lane_palette"):
            raise ValueError("texture='no_anchors' has no lane palette; override is incompatible")
        rows = list(range(1, h - 1)) if texture == "all_anchored" else ([h // 2] if texture == "single_anchor" else [])
        cols = []
    else:
        nr = _int_control(ctx, overrides, "n_anchored_rows", nr0, 0, 4)
        if has_rows and not has_cols and nr == 0:
            nc0 = max(1, nc0)
        nc = _int_control(ctx, overrides, "n_anchored_cols", nc0, 0, 4)
        if has_cols and not has_rows and nc == 0 and nr == 0:
            nr = ctx.draw_int_strict("n_anchored_rows", 1, 1)
        if nr == nc == 0:
            raise ValueError("zero row and column counts are incompatible; use texture='no_anchors'")
        rows = rng.sample(list(range(1, h - 1)), nr)
        cols = rng.sample(list(range(1, w - 1)), nc)
    grid = full_grid(h, w, 0)
    _fill_field(grid, rng, density)
    for row in rows:
        _paint_lane(grid, rng, density, style, row=row)
    for col in cols:
        _paint_lane(grid, rng, density, style, col=col)
    if rows or cols:
        _complete_palette_support(grid, rows, cols, style, rng)
        if diagnostic and texture == "none":
            _add_incomplete_endpoints(grid, rows, cols, rng)
    else:
        cells = [(r, c) for r in range(h) for c in range(w)]
        _ensure_values(grid, cells, (0,) * 5 + (6,) * 5, rng)
    return grid


def _rival(grid, mode):
    """Alternative rules ONLY; never authoritative training labels."""
    h, w = len(grid), len(grid[0])
    rows, cols = map(set, _lanes(grid))
    if mode in ("either_endpoint", "left_top", "right_bottom"):
        rows = {r for r in range(h) if ((grid[r][0] == 4 or grid[r][-1] == 4) if mode == "either_endpoint"
                else grid[r][0 if mode == "left_top" else -1] == 4)}
        cols = {c for c in range(w) if ((grid[0][c] == 4 or grid[-1][c] == 4) if mode == "either_endpoint"
                else grid[0 if mode == "left_top" else -1][c] == 4)}
    reverse = any(v in (7, 8) for row in grid for v in row)
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            active = r in rows or c in cols
            if mode == "double_swap": active = (r in rows) != (c in cols)
            elif mode == "rows_only": active = r in rows
            elif mode == "cols_only": active = c in cols
            elif mode == "swap_everywhere": active = True
            value = grid[r][c]
            if mode == "forward_only" and value in (7, 8): active = False
            if mode == "reverse_only" and value in (0, 6): active = False
            if mode == "reverse_rows_only" and value in (7, 8) and r not in rows: active = False
            if mode == "grid_wide_direction" and ((reverse and value in (0, 6)) or (not reverse and value in (7, 8))): active = False
            if mode == "identity": active = False
            if active: out[r][c] = _SWAP.get(value, value)
    return out


def _double_swap(g): return _rival(g, "double_swap")
def _either_endpoint(g): return _rival(g, "either_endpoint")
def _left_top(g): return _rival(g, "left_top")
def _right_bottom(g): return _rival(g, "right_bottom")
def _grid_wide_direction(g): return _rival(g, "grid_wide_direction")
def _reverse_rows_only(g): return _rival(g, "reverse_rows_only")
def _rows_only(g): return _rival(g, "rows_only")
def _cols_only(g): return _rival(g, "cols_only")
def _forward_only(g): return _rival(g, "forward_only")
def _reverse_only(g): return _rival(g, "reverse_only")
def _swap_everywhere(g): return _rival(g, "swap_everywhere")
def _identity(g): return _rival(g, "identity")

CANONICAL_SHORTCUTS = {
    "double_swap_intersections": _double_swap,
    "either_endpoint_activates": _either_endpoint,
    "left_top_endpoint_only": _left_top,
    "right_bottom_endpoint_only": _right_bottom,
    "grid_wide_swap_direction": _grid_wide_direction,
    "reverse_swap_rows_only": _reverse_rows_only,
}
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS,
    "rows_only": _rows_only, "columns_only": _cols_only,
    "forward_only": _forward_only, "reverse_only": _reverse_only,
    "swap_everywhere": _swap_everywhere, "identity": _identity,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS


def _has_crossing(grid):
    rows, cols = _lanes(grid)
    return bool(rows and cols)


def _has_incomplete_endpoint(grid):
    return any((row[0] == 4) != (row[-1] == 4) for row in grid) or any(
        (grid[0][c] == 4) != (grid[-1][c] == 4) for c in range(len(grid[0])))


def _has_both_directions(grid):
    rows, cols = _lanes(grid)
    active = {v for r, row in enumerate(grid) for c, v in enumerate(row) if r in rows or c in cols}
    return bool(active & {0, 6}) and bool(active & {7, 8})


def _has_left_top_unpaired(grid):
    return any(row[0] == 4 and row[-1] != 4 for row in grid) or any(
        grid[0][c] == 4 and grid[-1][c] != 4 for c in range(len(grid[0])))


def _has_right_bottom_unpaired(grid):
    return any(row[-1] == 4 and row[0] != 4 for row in grid) or any(
        grid[-1][c] == 4 and grid[0][c] != 4 for c in range(len(grid[0])))


def _has_reverse_column_only(grid):
    rows, cols = _lanes(grid)
    return any(grid[r][c] in (7, 8) for c in cols
               for r in range(1, len(grid) - 1) if r not in rows)

SEMANTIC_WITNESSES = {"crossing_swaps_once": _has_crossing,
                      "paired_endpoints_required": _has_incomplete_endpoint,
                      "cellwise_swap_direction": _has_both_directions,
                      "left_top_requires_partner": _has_left_top_unpaired,
                      "right_bottom_requires_partner": _has_right_bottom_unpaired,
                      "column_reverse_swap": _has_reverse_column_only}
WITNESS_RIVALS = {"crossing_swaps_once": ["double_swap_intersections"],
                  "paired_endpoints_required": ["either_endpoint_activates"],
                  "cellwise_swap_direction": ["grid_wide_swap_direction"],
                  "left_top_requires_partner": ["left_top_endpoint_only"],
                  "right_bottom_requires_partner": ["right_bottom_endpoint_only"],
                  "column_reverse_swap": ["reverse_swap_rows_only"]}


def lesson_identifiable(demos, query):
    """Finite declared-rival test using the actual authoritative labels."""
    reasons = []
    for name, solve in LESSON_COMPETITORS.items():
        if all(solve(pair["input"]) == pair["output"] for pair in demos):
            if solve(query["input"]) != query["output"]:
                reasons.append(f"{name} fits demonstrations but changes query")
    return reasons
