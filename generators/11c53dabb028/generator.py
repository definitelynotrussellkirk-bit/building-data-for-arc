"""Inputs for canonical 48131b3c: row-major color selection and negative tiling.

The unchanged Racket authority takes the FIRST nonzero input color and tiles
the zero-mask complement 2 by 2. Python predictions below are named diagnostic
rivals, never generation labels. Default lessons alternate canonical-scale
monochrome inputs with randomized multicolor witnesses; explicit overrides
request the general lawful domain and do not promise the default curriculum.
"""
from __future__ import annotations

from collections import Counter
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import fill_texture

GENERATOR_ID = "11c53dabb028"
TASK_ID = GENERATOR_ID
RULE_HASH = "573d7b5ea64c"
VERSION = "2.0.0"
SUMMARY = "Select the first row-major nonzero color, invert the zero mask, and tile 2 by 2."
EXAMPLES_NEEDED = 5
INVARIANTS = [
    "rectangular integer ARC grid with each dimension in 1..15 and area at least 2",
    "at least one zero and one nonzero cell; doubled output fits in 30 by 30",
    "fg_color denotes the first row-major nonzero, including multicolor inputs",
    "default six-profile lessons retain middle and extreme color-order witnesses",
]
HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes", "gradient", "checkerboard",
    "frame", "ring", "plus",
)
# Negative examples are tested explicitly, not advertised as valid generation modes.
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "profile and difficulty weighted 2..15", "valid": "1..15"},
    "grid_w": {"type": "int", "default": "profile and difficulty weighted 2..15", "valid": "1..15"},
    "fg_color": {"type": "color", "default": "profile-dependent 1..9", "valid": "1..9"},
    "fg_density": {
        "type": "float", "default": "profile-dependent occupied count",
        "valid": "0..1",
        "meaning": "final occupied cells = min(area-1, max(1, round(area*value)))",
    },
    "texture": {
        "type": "str", "default": "rng helpful structural prior",
        "valid": "noise|sparse|blob|stripes|gradient|checkerboard|frame|ring|plus",
        "meaning": "mask preference before exact occupancy; not a guaranteed final shape",
    },
    "multi_color": {"type": "bool", "default": "false in core; true in witnesses", "valid": "true|false"},
}
# Rejections carry the precise axes involved; no blanket pairwise exemption.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [{"grid_h": 1, "grid_w": 1}]
SCHEDULE_PROFILES = (
    "core_2", "middle_wide", "minimum", "core_3_4", "middle_tall", "maximum",
)


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _invalid_combination(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(name for name in axes
                                    if name in ("grid_h", "grid_w", "fg_density", "multi_color"))
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}; bg_density/noise_overlay were removed")
    for name in ("grid_h", "grid_w", "fg_color"):
        if name in overrides:
            value = overrides[name]
            upper = 9 if name == "fg_color" else 15
            if type(value) is not int or not 1 <= value <= upper:
                raise ValueError(f"{name} must be an integer in 1..{upper}")
    if "multi_color" in overrides and type(overrides["multi_color"]) is not bool:
        raise ValueError("multi_color must be a bool")
    if "fg_density" in overrides:
        value = overrides["fg_density"]
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("fg_density must be a finite number in 0..1")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES:
        raise ValueError("texture must be a helpful structural prior; all_zero/all_filled/monochrome are invalid modes")


def _size_choices(difficulty, lo=2, hi=15):
    # A broad tail remains in every band; weighting changes difficulty without
    # narrowing the advertised override range or excluding canonical profiles.
    favored = {"easy": range(2, 5), "medium": range(3, 8), "hard": range(5, 10)}.get(
        difficulty, range(3, 8))
    return list(range(lo, hi + 1)) + [v for v in favored if lo <= v <= hi] * 6


def _dimensions(ctx, profile, difficulty, overrides):
    if profile == "core_2":
        h = ctx.draw_choice("grid_h", [2])
        w = ctx.draw_choice("grid_w", [h])
    elif profile == "core_3_4":
        h = ctx.draw_choice("grid_h", [3, 4])
        w = ctx.draw_choice("grid_w", [h])
    elif profile == "middle_wide":
        h = ctx.draw_choice("grid_h", _size_choices(difficulty, 2, 14))
        w = ctx.draw_choice("grid_w", _size_choices(difficulty, h + 1, 15))
    elif profile == "middle_tall":
        w = ctx.draw_choice("grid_w", _size_choices(difficulty, 2, 14))
        h = ctx.draw_choice("grid_h", _size_choices(difficulty, w + 1, 15))
    elif profile in ("minimum", "maximum"):
        h = ctx.draw_choice("grid_h", _size_choices(difficulty))
        w = ctx.draw_choice("grid_w", _size_choices(difficulty, 3 if h == 2 else 2))
    else:
        # Condition free dimensions on the caller's complete request. A valid
        # partial request must not fail merely because we drew a small canvas.
        h_options = list(range(1, 16)) if "grid_h" in overrides else _size_choices(difficulty)
        w_options = list(range(1, 16)) if "grid_w" in overrides else _size_choices(difficulty)
        hs = [overrides["grid_h"]] if "grid_h" in overrides else sorted(set(h_options))
        ws = [overrides["grid_w"]] if "grid_w" in overrides else sorted(set(w_options))
        feasible = set()
        for ch in hs:
            for cw in ws:
                area = ch * cw
                if area < 2:
                    continue
                if overrides.get("multi_color") is True:
                    count = (min(area - 1, max(1, round(area * overrides["fg_density"])))
                             if "fg_density" in overrides else area - 1)
                    if count < 2:
                        continue
                feasible.add((ch, cw))
        if not feasible:
            _invalid_combination("no legal grid dimensions can realize the requested controls", tuple(overrides))
        possible_h = {ch for ch, _ in feasible}
        h = ctx.draw_choice("grid_h", [ch for ch in h_options if ch in possible_h])
        w = ctx.draw_choice("grid_w", [cw for cw in w_options if (h, cw) in feasible])
    if h * w < 2:
        _invalid_combination("a 1 by 1 grid cannot contain both zero and nonzero", ("grid_h", "grid_w"))
    return h, w


def _mask(ctx, h, w, count, texture, *, witness=False):
    prior = fill_texture(texture, h, w, [0, 1], ctx.draw_rng("texture_cells"))
    rng = ctx.draw_rng("mask_selection")
    ranking = {r * w + c: (prior[r][c] != 0, rng.random()) for r in range(h) for c in range(w)}
    if not witness:
        return sorted(sorted(ranking, key=ranking.get, reverse=True)[:count]), None
    # Choose a movable row-major first cell and a later cell in an earlier
    # column. This distinguishes row-major from column-major selection.
    candidates = [p for p in ranking if p // w < h - 1 and p % w > 0 and h * w - p >= count]
    first = rng.choice(candidates)
    fr, fc = divmod(first, w)
    column_first = rng.randrange(fr + 1, h) * w  # column 0, below first
    remaining = [p for p in ranking if p > first and p != column_first]
    chosen = [first, column_first] + sorted(remaining, key=ranking.get, reverse=True)[:count - 2]
    # A different selected column-0 point can precede the originally reserved
    # one. Reserve the actual column-major first before assigning any colors.
    actual_column_first = min(chosen, key=lambda p: (p % w, p // w))
    return sorted(chosen), actual_column_first


def _witness_palette(ctx, profile):
    rank = 0 if profile == "minimum" else (2 if profile == "maximum" else 1)
    options = list(range(1, 8)) if rank == 0 else (list(range(3, 10)) if rank == 2 else list(range(2, 9)))
    first = ctx.draw_choice("fg_color", options)
    rng = ctx.draw_rng("other_colors")
    if rank == 0:
        others = rng.sample(list(range(first + 1, 10)), 2)
    elif rank == 2:
        others = rng.sample(list(range(1, first)), 2)
    else:
        others = [rng.randrange(1, first), rng.randrange(first + 1, 10)]
    rng.shuffle(others)
    return first, others[0], others[1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty) if not overrides else "explicit"
    witness = profile in ("middle_wide", "middle_tall", "minimum", "maximum")
    h, w = _dimensions(ctx, profile, difficulty, overrides)
    area = h * w
    texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES))
    if "fg_density" in overrides:
        count = min(area - 1, max(1, round(area * overrides["fg_density"])))
    elif witness:
        count = ctx.draw_rng("occupied_count").randint(5, area - 1)
    else:
        lower = 2 if overrides.get("multi_color") is True else 1
        if lower >= area:
            _invalid_combination("multicolor needs two occupied cells and a zero", tuple(overrides))
        count = ctx.draw_rng("occupied_count").randint(lower, area - 1)
    if profile == "explicit":
        options = [False, True] if count >= 2 else [False]
        if overrides.get("multi_color") is True and count < 2:
            _invalid_combination("requested density cannot realize two nonzero colors", tuple(overrides))
        multi = ctx.draw_choice("multi_color", options)
    else:
        multi = ctx.draw_choice("multi_color", [witness])
    cells, column_first = _mask(ctx, h, w, count, texture, witness=witness)
    grid = full_grid(h, w, 0)
    if witness:
        first, secondary, dominant = _witness_palette(ctx, profile)
        rng = ctx.draw_rng("color_placements")
        if profile in ("minimum", "maximum"):
            # Two majority-first examples per six refute the second-frequency
            # shortcut; two minority-first examples below refute the mode.
            first_count = rng.randint(count // 2 + 1, count - 2)
            other_cells = [column_first]
            last = cells[-1]
            other_cells.append(last if last != column_first else rng.choice(
                [p for p in cells[1:] if p != column_first]))
            other_cells.extend(rng.sample([p for p in cells[1:] if p not in other_cells],
                                          count - first_count - 2))
            for p in cells:
                grid[p // w][p % w] = first
            grid[other_cells[0] // w][other_cells[0] % w] = secondary
            grid[other_cells[1] // w][other_cells[1] % w] = dominant
            for p in other_cells[2:]:
                grid[p // w][p % w] = rng.choice((secondary, dominant))
        else:
            # Middle-rank first colors are minority selectors. Its count can
            # exceed one, preventing a unique-singleton selector shortcut.
            first_count = rng.randint(1, (count - 2) // 2)
            movable = [p for p in cells[1:] if p not in (column_first, cells[-1])]
            secondary_cell = rng.choice(movable)
            first_extras = rng.sample([p for p in movable if p != secondary_cell], first_count - 1)
            for p in cells:
                grid[p // w][p % w] = dominant
            for p in [cells[0]] + first_extras:
                grid[p // w][p % w] = first
            grid[secondary_cell // w][secondary_cell % w] = secondary
    else:
        first = ctx.draw_color("fg_color", exclude={0})
        for p in cells:
            grid[p // w][p % w] = first
        if multi:
            rng = ctx.draw_rng("other_colors")
            other = rng.choice([color for color in range(1, 10) if color != first])
            # Always realize the requested boolean, without moving the first.
            for p in rng.sample(cells[1:], rng.randint(1, count - 1)):
                grid[p // w][p % w] = other
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= h <= 15 or not 1 <= w <= 15 or h * w < 2:
        return ["input dimensions must be 1..15 with area at least 2"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9 (not bools)"]
    values = [v for row in grid for v in row]
    errors = []
    if not any(values):
        errors.append("at least one nonzero cell is needed to select an output color")
    if 0 not in values:
        errors.append("at least one zero is needed for a nonempty output foreground")
    return errors


def strict_canonical_like(grid):
    """Lawful zero-mask/selector domain; exact canonical geometry is a separate floor.

    Permutations, sparse masks and short lines remain lawful under the selected
    rule. Rejecting them to satisfy a generic mutation heuristic would remove
    real task support. Multicolor extends the examples using the explicit rule.
    """
    return self_check(grid)


def observe_overrides(grid):
    values = [v for row in grid for v in row if v != 0]
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "fg_color": values[0],
        "multi_color": len(set(values)) > 1,
        "occupied_cells": len(values), "realized_density": len(values) / (len(grid) * len(grid[0])),
    }


def mutation_fixtures():
    return [("all_zero", [[0, 0]]), ("all_nonzero", [[1, 2]]),
            ("invalid_color", [[10, 0]]), ("bool_color", [[True, 0]]),
            ("too_wide", [[1] + [0] * 15]), ("ragged", [[1, 0], [0]])]


def _selected_color(grid, selector):
    colors = [v for row in grid for v in row if v]
    if selector == "first":
        return colors[0]
    if selector == "last":
        return colors[-1]
    if selector == "minimum":
        return min(colors)
    if selector == "maximum":
        return max(colors)
    if selector == "mode":
        counts = Counter(colors)
        return min(counts, key=lambda c: (-counts[c], c))
    if selector == "second_frequency":
        counts = Counter(colors)
        # Counter insertion order is first appearance; stable sorting retains
        # that order at equal counts, making this rival fully reproducible.
        ordered = sorted(counts, key=lambda c: -counts[c])
        return ordered[min(1, len(ordered) - 1)]
    if selector == "median":
        distinct = sorted(set(colors))
        return distinct[len(distinct) // 2]
    if selector == "column_major":
        return next(grid[r][c] for c in range(len(grid[0])) for r in range(len(grid)) if grid[r][c])
    raise ValueError(selector)


def _prediction(grid, selector="first", layout="tile"):
    """Diagnostic predictions only. Labels are always executed through Racket."""
    h, w = len(grid), len(grid[0])
    color = _selected_color(grid, selector)
    oh, ow = (2 * h, 2 * h) if layout == "square" else (2 * h, 2 * w)
    out = []
    for r in range(oh):
        row = []
        for c in range(ow):
            rr, cc = r % h, c % w
            if layout == "scale":
                rr, cc = r // 2, c // 2
            elif layout == "reflect":
                rr = h - 1 - rr if r >= h else rr
                cc = w - 1 - cc if c >= w else cc
            row.append(color if grid[rr][cc] == 0 else 0)
        out.append(row)
    return out


def _selector_rival(selector):
    def rival(grid):
        return _prediction(grid, selector)
    return rival


def _square_period(grid):
    return _prediction(grid, layout="square")


def _scale_instead_of_tile(grid):
    return _prediction(grid, layout="scale")


def _mirror_quadrants(grid):
    return _prediction(grid, layout="reflect")


CANONICAL_SHORTCUTS = {name: _selector_rival(name) for name in (
    "last", "minimum", "maximum", "mode", "median", "column_major", "second_frequency")}
CANONICAL_SHORTCUTS["square_period"] = _square_period
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS.update(scale_instead_of_tile=_scale_instead_of_tile, mirror_quadrants=_mirror_quadrants)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _refutes(rival):
    def witness(grid):
        return not self_check(grid) and rival(grid) != _prediction(grid)
    return witness


SEMANTIC_WITNESSES = {"refutes_" + name: _refutes(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {"refutes_" + name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival ambiguity, not a claim about arbitrary induction."""
    reasons = []
    # The public lesson hook receives a labeled query pair, just like demos.
    # Its output is supplied by the reference executor, not this diagnostic.
    query_input, expected = query["input"], query["output"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query_input) != expected:
            reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
