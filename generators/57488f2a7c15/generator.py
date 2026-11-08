"""Constructive, color-preserving main-diagonal completion inputs.

The unchanged Racket authority is (overlay g (transpose g)). Each unordered
transpose orbit is empty, a singleton, or a same-colored pair, so reflection
never overwrites a different source color. Outputs are supplied only by Racket.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57488f2a7c15"
TASK_ID = GENERATOR_ID
RULE_HASH = "2b970065d6a3"
VERSION = "2.0.0"
SUMMARY = "Complete conflict-free partial main-diagonal symmetry while preserving all source colors."

INVARIANTS = [
    "a square list-of-lists of integer colors 0..9, with background 0 and side 4..16",
    "2..12 occupied cells, with at least two nonzero colors to teach color preservation",
    "0..3 diagonal cells and 0..3 already-complete, same-colored transpose pairs",
    "each incomplete transpose orbit has exactly one source; at least one orbit is incomplete",
    "the two occupied sides of a transpose orbit never have different colors",
]
AXES = {
    "side": {"type": "int", "default": "weighted 4..16; canonical sizes favored in every band", "valid": "4..16"},
    "n_cells": {"type": "int", "default": "weighted feasible 2..12; 4 and 5 favored", "valid": "2..12"},
    "n_distinct_colors": {"type": "int", "default": "weighted feasible 2..9", "valid": "2..9"},
    "n_diagonal": {"type": "int", "default": "scheduled feasible 0..3", "valid": "0..3"},
    "n_pairs": {"type": "int", "default": "weighted feasible 0..3; 0 favored", "valid": "0..3"},
    "source_triangle": {"type": "str", "default": "scheduled orientation of incomplete orbits", "valid": "lower|upper|mixed"},
}
# Refusals carry their actual requested axis names on the exception. An empty
# declaration selects strict checking rather than the legacy catch-all policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5

_DIAGONAL_MODES = ("shared", "unique", "none")


def _profile_at(index):
    block, position = divmod(index % 18, 6)
    if position == 0:
        return "lower", _DIAGONAL_MODES[block % 3]
    triangle = "upper" if position == 3 else "mixed"
    return triangle, _DIAGONAL_MODES[(5 * block + position - 1) % 3]


# Five ORDERED demonstrations. Every such window includes upper- and lower-
# completion witnesses and every diagonal context. Arbitrary query rotations
# are diagnostic: a holdout can remove the sole witness for one context.
SCHEDULE_PROFILES = tuple(":".join(_profile_at(i)) for i in range(18))
_LIMITS = {"side": (4, 16), "n_cells": (2, 12), "n_distinct_colors": (2, 9),
           "n_diagonal": (0, 3), "n_pairs": (0, 3)}
_LAYOUT_AXES = ("side", "n_cells", "n_diagonal", "n_pairs", "source_triangle")


class IncompatibleOverrides(ValueError):
    def __init__(self, names):
        self.incompatible_axes = tuple(sorted(names))
        super().__init__(
            "incompatible overrides " + ", ".join(self.incompatible_axes)
            + ": require an incomplete orbit, room for every cell/color, and two "
              "incomplete orientations when source_triangle='mixed'"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _LIMITS:
            lo, hi = _LIMITS[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be a Python int in {lo}..{hi}")
        elif type(value) is not str or value not in ("lower", "upper", "mixed"):
            raise ValueError("source_triangle must be lower, upper, or mixed")
    return tuple(sorted((name, value) for name, value in overrides.items() if value is not None))


@lru_cache(maxsize=256)
def _layouts(pinned, triangle, diagonal_mode):
    """Finite feasible geometry, cached independently of random draws/grids."""
    fixed = dict(pinned)
    domains = {name: (fixed[name],) if name in fixed else range(lo, hi + 1)
               for name, (lo, hi) in _LIMITS.items()}
    triangles = ((fixed["source_triangle"],) if "source_triangle" in fixed else
                 ((triangle,) if triangle is not None else ("lower", "upper", "mixed")))
    layouts = []
    for side in domains["side"]:
        capacity = side * (side - 1) // 2
        for cells in domains["n_cells"]:
            for diagonal in domains["n_diagonal"]:
                if (diagonal_mode == "none" and diagonal != 0) or (
                        diagonal_mode in ("shared", "unique") and diagonal == 0):
                    continue
                for pairs in domains["n_pairs"]:
                    singles = cells - diagonal - 2 * pairs
                    if singles < 1 or singles + pairs > capacity:
                        continue
                    maximum_colors = min(9, cells - pairs - (diagonal_mode == "shared"))
                    if maximum_colors < 2 or fixed.get("n_distinct_colors", 2) > maximum_colors:
                        continue
                    for region in triangles:
                        if region != "mixed" or singles >= 2:
                            layouts.append((side, cells, diagonal, pairs, region, maximum_colors))
    return tuple(layouts)


def _weighted_choice(ctx, name, choices, favored):
    choices = sorted(set(choices))
    return ctx.draw_choice(name, choices + [value for value in favored if value in choices])


def _choose_configuration(ctx, pinned, sample_index, difficulty):
    triangle, diagonal_mode = _profile_at(sample_index)
    layouts = _layouts(pinned, triangle, diagonal_mode)
    # Explicit controls have priority over the unoverridden teaching schedule.
    # Relax only implicit choices; never clip a requested count or drop a cell.
    if not layouts and pinned:
        diagonal_mode = "any"
        layouts = _layouts(pinned, triangle, diagonal_mode)
    if not layouts and pinned:
        layouts = _layouts(pinned, None, diagonal_mode)
    if not layouts:
        raise IncompatibleOverrides(dict(pinned))
    favored = {
        "side": [5, 6, 7] * 12,
        "n_cells": [4, 5] * 12,
        "n_diagonal": [0, 1] * 12,
        "n_pairs": [0] * 16 + [1] * 3,
        "source_triangle": [],
    }
    if difficulty == "easy":
        favored["side"] += [4, 5, 6] * 4
        favored["n_cells"] += [3, 4] * 4
    elif difficulty == "hard":
        favored["side"] += [9, 10, 11, 12] * 4
        favored["n_cells"] += [8, 9, 10, 11, 12] * 4
        favored["n_pairs"] += [1, 2, 3] * 2
    selected = {}
    for index, name in enumerate(_LAYOUT_AXES):
        value = _weighted_choice(ctx, name, [row[index] for row in layouts], favored[name])
        selected[name] = value
        layouts = [row for row in layouts if row[index] == value]
    selected["n_distinct_colors"] = _weighted_choice(
        ctx, "n_distinct_colors", range(2, layouts[0][-1] + 1), [3, 4, 5] * 6)
    return selected, diagonal_mode


def _color_groups(grid, groups, colors, rng):
    groups = list(groups)
    rng.shuffle(groups)
    for index, group in enumerate(groups):
        color = colors[index] if index < len(colors) else rng.choice(colors)
        for r, c in group:
            grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    pinned = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    config, diagonal_mode = _choose_configuration(ctx, pinned, sample_index, difficulty)
    side, cells = config["side"], config["n_cells"]
    diagonal, pair_count = config["n_diagonal"], config["n_pairs"]
    single_count = cells - diagonal - 2 * pair_count
    geometry = ctx.draw_rng("transpose_orbits")
    orbits = geometry.sample([(r, c) for r in range(side) for c in range(r + 1, side)],
                             single_count + pair_count)
    paired_groups = [[(r, c), (c, r)] for r, c in orbits[:pair_count]]
    region = config["source_triangle"]
    upper = ([True, False] + [geometry.choice((True, False)) for _ in range(single_count - 2)]
             if region == "mixed" else [region == "upper"] * single_count)
    geometry.shuffle(upper)
    singleton_groups = [[(r, c) if direction else (c, r)]
                        for (r, c), direction in zip(orbits[pair_count:], upper, strict=True)]
    diagonal_groups = [[(r, r)] for r in ctx.draw_rng("diagonal_positions").sample(range(side), diagonal)]
    colors = ctx.draw_distinct_colors("palette", n=config["n_distinct_colors"], exclude={0})
    color_rng = ctx.draw_rng("color_assignment")
    grid = full_grid(side, side, 0)
    off_groups = singleton_groups + paired_groups
    if diagonal_mode == "shared":
        # Share with an INCOMPLETE source, so the witness requires an actual
        # added cell; a prefilled pair would not refute ignore-diagonal-colors.
        for group in (diagonal_groups[0], singleton_groups[0]):
            for r, c in group:
                grid[r][c] = colors[0]
        remaining = singleton_groups[1:] + paired_groups + diagonal_groups[1:]
        _color_groups(grid, remaining, colors[1:], color_rng)
    elif diagonal_groups:
        # Keep diagonal-only and off-diagonal palettes disjoint, including
        # dense exact-control cases where more than one diagonal color is used.
        lo = max(1, len(colors) - len(off_groups))
        hi = min(len(diagonal_groups), len(colors) - 1)
        diagonal_colors = color_rng.randint(lo, hi)
        _color_groups(grid, diagonal_groups, colors[:diagonal_colors], color_rng)
        _color_groups(grid, off_groups, colors[diagonal_colors:], color_rng)
    else:
        _color_groups(grid, off_groups, colors, color_rng)
    return grid


def observe_overrides(grid):
    n = len(grid)
    lower = upper = pairs = 0
    for r in range(n):
        for c in range(r + 1, n):
            if grid[r][c] and grid[c][r]:
                pairs += 1
            elif grid[r][c]:
                upper += 1
            elif grid[c][r]:
                lower += 1
    return {
        "side": n,
        "n_cells": sum(value != 0 for row in grid for value in row),
        "n_distinct_colors": len({value for row in grid for value in row if value != 0}),
        "n_diagonal": sum(grid[r][r] != 0 for r in range(n)),
        "n_pairs": pairs,
        "source_triangle": "mixed" if lower and upper else ("lower" if lower else "upper"),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) for row in grid):
        return ["expected a nonempty list-of-lists grid"]
    n = len(grid)
    if any(len(row) != n for row in grid):
        return ["expected a square, non-ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be Python integer colors 0..9 (not booleans)"]
    errors = []
    if any(grid[r][c] and grid[c][r] and grid[r][c] != grid[c][r]
           for r in range(n) for c in range(r + 1, n)):
        errors.append("conflicting nonzero colors occupy a transpose orbit")
    if not any(bool(grid[r][c]) != bool(grid[c][r])
               for r in range(n) for c in range(r + 1, n)):
        errors.append("at least one incomplete off-diagonal orbit is required")
    observed = observe_overrides(grid)
    for name, (lo, hi) in _LIMITS.items():
        if not lo <= observed[name] <= hi:
            errors.append(f"{name}={observed[name]} outside selected training domain {lo}..{hi}")
    return errors


def strict_canonical_like(grid):
    """Selected multicolor task manifold, including every canonical input."""
    return self_check(grid)


def _copy_selected(grid, predicate):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and predicate(r, c, value):
                out[c][r] = value
    return out


def _lower_only(grid):
    return _copy_selected(grid, lambda r, c, value: r > c)


def _upper_only(grid):
    return _copy_selected(grid, lambda r, c, value: r < c)


def _ignore_diagonal_colors(grid):
    diagonal = {grid[r][r] for r in range(len(grid)) if grid[r][r]}
    return _copy_selected(grid, lambda r, c, value: value not in diagonal)


def _has_shared_diagonal_color(grid):
    diagonal = {grid[r][r] for r in range(len(grid)) if grid[r][r]}
    return any(value in diagonal and grid[c][r] == 0
               for r, row in enumerate(grid) for c, value in enumerate(row) if r != c and value)


def _diagonal_context(grid):
    if not any(grid[r][r] for r in range(len(grid))):
        return "none"
    return "shared" if _has_shared_diagonal_color(grid) else "unique"


def _context_rival(grid, context, full_only):
    matches = _diagonal_context(grid) == context
    complete = matches if full_only else not matches
    return _copy_selected(grid, lambda r, c, value: complete or r > c)


def _erase_diagonal(grid):
    out = _copy_selected(grid, lambda r, c, value: True)
    for r in range(len(grid)):
        out[r][r] = 0
    return out


def _transpose_only(grid):
    return [list(row) for row in zip(*grid)]


def _has_upper_source(grid):
    return any(grid[r][c] and not grid[c][r]
               for r in range(len(grid)) for c in range(r + 1, len(grid)))


def _has_lower_source(grid):
    return any(grid[c][r] and not grid[r][c]
               for r in range(len(grid)) for c in range(r + 1, len(grid)))


SEMANTIC_RIVALS = {
    "lower_only": _lower_only,
    "upper_only": _upper_only,
    "ignore_diagonal_colors": _ignore_diagonal_colors,
    "erase_diagonal": _erase_diagonal,
    "transpose_only": _transpose_only,
}
for _context in _DIAGONAL_MODES:
    SEMANTIC_RIVALS[f"lower_only_when_{_context}"] = (
        lambda grid, context=_context: _context_rival(grid, context, False))
    SEMANTIC_RIVALS[f"full_only_when_{_context}"] = (
        lambda grid, context=_context: _context_rival(grid, context, True))
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: rival for name, rival in SEMANTIC_RIVALS.items()
                       if name not in ("upper_only", "erase_diagonal", "transpose_only")}
SEMANTIC_WITNESSES = {
    "upper_incomplete_source": _has_upper_source,
    "lower_incomplete_source": _has_lower_source,
    "shared_diagonal_source_color": _has_shared_diagonal_color,
    "unshared_upper_source": lambda grid: _has_upper_source(grid) and not _has_shared_diagonal_color(grid),
    "shared_upper_source": lambda grid: _has_upper_source(grid) and _has_shared_diagonal_color(grid),
    "no_diagonal_upper_source": lambda grid: _has_upper_source(grid) and not any(grid[r][r] for r in range(len(grid))),
    "unique_diagonal_upper_source": lambda grid: _has_upper_source(grid) and _diagonal_context(grid) == "unique",
    "active_diagonal": lambda grid: any(grid[r][r] != 0 for r in range(len(grid))),
}
WITNESS_RIVALS = {
    "upper_incomplete_source": ["lower_only"],
    "lower_incomplete_source": ["upper_only"],
    "shared_diagonal_source_color": ["ignore_diagonal_colors"],
    "unshared_upper_source": ["full_only_when_shared"],
    "shared_upper_source": ["lower_only_when_shared", "full_only_when_unique", "full_only_when_none"],
    "no_diagonal_upper_source": ["lower_only_when_none", "full_only_when_shared", "full_only_when_unique"],
    "unique_diagonal_upper_source": ["lower_only_when_unique", "full_only_when_shared", "full_only_when_none"],
    "active_diagonal": ["erase_diagonal"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check against the supplied Racket-labeled pairs."""
    return [f"{name} fits every demonstration and changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def mutation_fixtures():
    conflict = full_grid(5, 5, 0)
    conflict[0][1], conflict[1][0], conflict[4][2] = 2, 3, 7
    return [("conflicting_transpose_colors", conflict),
            ("empty_grid", full_grid(5, 5, 0)),
            ("bool_cell", [[False] * 5 for _ in range(5)])]
