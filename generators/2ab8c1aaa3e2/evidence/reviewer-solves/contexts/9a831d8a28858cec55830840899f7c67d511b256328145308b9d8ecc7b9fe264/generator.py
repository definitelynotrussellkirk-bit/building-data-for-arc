"""Vertical exact-two-marker curriculum; labels belong to the unchanged Racket rule.

One third of ordinary draws retain the canonical monochrome-pair manifold.
The other two thirds add independent exact-count, same-color, mixed-column and
color-reuse contrasts. Any four consecutive default draws contain at least two
contrast draws, so holding out any one still leaves a complete contrast example.
The guarantee concerns three-demo default lessons and declared rivals, not all
possible rules or arbitrary override curricula. See notes.md and workspace/.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ab8c1aaa3e2"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ad1f1fa8669a"
SUMMARY = (
    "In each column, fill between the two occurrences of each nonzero color "
    "appearing exactly twice. Preserve other cells; triples are not pairs, "
    "unlike endpoints do not join, and a pair can overwrite an interior singleton."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular integer grid, 4..22 rows by 4..20 columns, colors 0..9; background 0",
    "at least one same-color exact-two column group has a nonempty vertical gap",
    "each column is empty, a singleton, a pair, a triple, two unlike singletons, or a pair with one unlike interior singleton",
    "distinct exact-two groups never overlap in a column; Racket is the only label authority",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile mixture; band-weighted", "valid": "4..22"},
    "grid_w": {"type": "int", "default": "canonical-profile mixture; enough motif columns", "valid": "4..20"},
    "pairs": {"type": "int", "default": "core 2..4 favored; contrast 2..12", "valid": "1..12"},
    "n_distinct_colors": {"type": "int", "default": "core 2..4 favored; contrast 2..9", "valid": "1..9"},
}
# Geometrically impossible joint settings raise an exception naming the minimal
# conflicting axes. There is no blanket exception that conceals unrelated bugs.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_LIMITS = {"grid_h": (4, 22), "grid_w": (4, 20), "pairs": (1, 12), "n_distinct_colors": (1, 9)}
# Dimensions and counts only, not copied example grids or their answers.
_CORE_PROFILES = ((10, 9, 4, 4), (7, 8, 4, 4), (9, 11, 3, 3), (10, 8, 2, 2), (9, 9, 4, 4))
SCHEDULE_PROFILES = ("core", "contrast")


class IncompatibleOverrides(ValueError):
    def __init__(self, axes):
        self.incompatible_axes = tuple(axes)
        super().__init__("incompatible override axes: " + ", ".join(axes) + "; not enough columns/color-bearing groups")


def schedule_profile(seed, sample_index, difficulty=None):
    return "core" if sample_index % 3 == 0 else "contrast"


def _feasible(mode, overrides):
    width = overrides.get("grid_w", 20)
    result = []
    for pairs in range(1, 13):
        if "pairs" in overrides and pairs != overrides["pairs"]:
            continue
        if mode == "contrast" and pairs == 1 and overrides.get("pairs") != 1:
            continue  # ordinary contrast draws always show color reuse
        cost = pairs + (2 if mode == "contrast" else 0)
        if cost > width:
            continue
        capacity = pairs if mode == "core" else (pairs + 3 if pairs >= 2 else 5)
        for colors in range(1 if mode == "core" else 2, min(9, capacity) + 1):
            if "n_distinct_colors" not in overrides or colors == overrides["n_distinct_colors"]:
                result.append((pairs, colors))
    return result


def _choose(ctx, axis, choices, preferred=(), weight=80):
    values = sorted(set(choices))
    favored = [v for v in preferred if v in values]
    return ctx.draw_choice(axis, values + favored * weight)


def _gap(rng, height, minimum_span=2):
    first = rng.randrange(height - minimum_span)
    last = rng.randint(first + minimum_span, height - 1)
    return first, last


def _contrast_colors(rng, palette, pairs):
    # Four named roles form two inequality edges: pair != interior singleton,
    # and the two unlike endpoints. All remaining roles are unconstrained.
    # Construct a surjection, without retrying or silently losing a color.
    k = len(palette)
    roles = [palette[0], palette[1], palette[0], palette[1]]
    if k == 3:
        roles[2] = palette[2]
        roles[3] = palette[0]
    elif k >= 4:
        roles = list(palette[:4])
    remaining_pairs = max(0, pairs - 2)
    free = list(palette[min(k, 4):])
    while len(free) < remaining_pairs + 1:
        free.append(rng.choice(palette))
    rng.shuffle(free)
    pair_colors = [roles[0]] * min(pairs, 2) + free[:remaining_pairs]
    return pair_colors, roles[1], (roles[2], roles[3]), free[-1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    supplied = {k: v for k, v in overrides.items() if v is not None}
    for key, value in supplied.items():
        lo, hi = _LIMITS[key]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{key} must be an integer in [{lo}, {hi}]")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    preferred_mode = schedule_profile(seed, sample_index, difficulty)
    mode = preferred_mode
    feasible = _feasible(mode, supplied)
    if not feasible:
        # Exact overrides take precedence over the default teaching schedule.
        mode = "contrast" if mode == "core" else "core"
        feasible = _feasible(mode, supplied)
    if not feasible:
        keys = sorted(set(supplied) - {"grid_h"})
        for size in range(2, len(keys) + 1):
            for axes in combinations(keys, size):
                sub = {k: supplied[k] for k in axes}
                if not _feasible("core", sub) and not _feasible("contrast", sub):
                    raise IncompatibleOverrides(axes)
        raise IncompatibleOverrides(keys)
    anchor = ctx.draw_rng("core_profile").choice(_CORE_PROFILES)
    band = difficulty or "medium"
    pair_favored = {"easy": (2, 3, 4), "medium": (3, 4, 5, 6), "hard": (6, 7, 8, 9, 10, 11, 12)}[band]
    pairs = _choose(ctx, "pairs", [p for p, k in feasible],
                    (anchor[2],) if mode == "core" else pair_favored)
    colors = _choose(ctx, "n_distinct_colors", [k for p, k in feasible if p == pairs],
                     (anchor[3],) if mode == "core" else (2, 3, 4))
    dims = {"easy": range(5, 10), "medium": range(8, 15), "hard": range(14, 23)}[band]
    h = _choose(ctx, "grid_h", range(4, 23), (anchor[0],) if mode == "core" else dims)
    cost = pairs + (2 if mode == "contrast" else 0)
    w = _choose(ctx, "grid_w", range(max(4, cost), 21), (anchor[1],) if mode == "core" else dims)
    rng = ctx.draw_rng("layout")
    palette = ctx.draw_rng("palette").sample(range(1, 10), colors)
    if mode == "core":
        pair_colors = list(palette) + [rng.choice(palette) for _ in range(pairs - colors)]
        rng.shuffle(pair_colors)
    else:
        pair_colors, noise_color, unlike, triple_color = _contrast_colors(rng, palette, pairs)
    grid = full_grid(h, w, 0)
    columns = rng.sample(range(w), cost)
    for i, (c, color) in enumerate(zip(columns, pair_colors)):
        if i == 0 or (mode == "contrast" and i == 1):
            first, last = _gap(rng, h)
        else:
            first, last = sorted(rng.sample(range(h), 2))
        grid[first][c] = grid[last][c] = color
        if mode == "contrast" and i == 0:
            grid[rng.randint(first + 1, last - 1)][c] = noise_color
    if mode == "contrast":
        c = columns[pairs]
        first, last = _gap(rng, h, minimum_span=3)
        middle = rng.randint(first + 1, last - 1)
        for r in (first, middle, last):
            grid[r][c] = triple_color
        first, last = _gap(rng, h)
        grid[first][columns[pairs + 1]] = unlike[0]
        grid[last][columns[pairs + 1]] = unlike[1]
    return grid


def _column_groups(grid):
    return [{color: [r for r, row in enumerate(grid) if row[c] == color]
             for color in dict.fromkeys(row[c] for row in grid if row[c])}
            for c in range(len(grid[0]))]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-sequence grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be sequences"]
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        return ["empty or ragged rows"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integers 0..9 (not booleans)"]
    if not 4 <= len(grid) <= 22 or not 4 <= width <= 20:
        return ["dimensions outside the documented 4..22 by 4..20 domain"]
    errors = []
    has_gap = False
    for c, groups in enumerate(_column_groups(grid)):
        sizes = sorted(len(rs) for rs in groups.values())
        if sizes not in ([], [1], [2], [3], [1, 1], [1, 2]):
            errors.append(f"column {c}: unsupported marker multiplicities {sizes}")
            continue
        if sizes == [1, 2]:
            endpoints = next(rs for rs in groups.values() if len(rs) == 2)
            singleton = next(rs[0] for rs in groups.values() if len(rs) == 1)
            if not endpoints[0] < singleton < endpoints[1]:
                errors.append(f"column {c}: singleton must lie inside the pair")
        has_gap |= any(len(rs) == 2 and rs[-1] - rs[0] >= 2 for rs in groups.values())
    if not has_gap:
        errors.append("no exact-two same-color pair with a nonempty gap")
    return errors


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "pairs": sum(len(rs) == 2 for col in _column_groups(grid) for rs in col.values()),
            "n_distinct_colors": len({v for row in grid for v in row} - {0})}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    return ([] if all(not col or (len(col) == 1 and len(next(iter(col.values()))) == 2)
                      for col in _column_groups(grid))
            else ["controlled exact-count/mixed-color contrast outside the canonical pair-only manifold"])


def _rival(grid, mode):
    """Deliberately wrong authoring rivals; never used by generate() for labels."""
    out = [list(row) for row in grid]
    global_counts = Counter(v for row in grid for v in row if v)
    for c, groups in enumerate(_column_groups(grid)):
        if mode == "any_two":
            hits = [(r, row[c]) for r, row in enumerate(grid) if row[c]]
            if len(hits) == 2:
                for r in range(hits[0][0], hits[-1][0] + 1):
                    out[r][c] = hits[0][1]
            continue
        for color, rs in groups.items():
            use = len(rs) >= 2 if mode == "at_least_two" else len(rs) == 2
            if mode == "monochrome_column":
                use &= len(groups) == 1
            if mode == "global_two":
                use &= global_counts[color] == 2
            if use:
                for r in range(rs[0], rs[-1] + 1):
                    out[r][c] = color
    return out


def _at_least_two(grid):
    return _rival(grid, "at_least_two")


def _any_two(grid):
    return _rival(grid, "any_two")


def _monochrome_column(grid):
    return _rival(grid, "monochrome_column")


def _global_two(grid):
    return _rival(grid, "global_two")


def _triple_gap(grid):
    return any(len(rs) == 3 and rs[-1] - rs[0] >= 3 for col in _column_groups(grid) for rs in col.values())


def _unlike_endpoints(grid):
    return any(sorted(map(len, col.values())) == [1, 1] for col in _column_groups(grid))


def _mixed_pair(grid):
    return any(sorted(map(len, col.values())) == [1, 2] for col in _column_groups(grid))


def _reused_pair_color(grid):
    counts = Counter(v for row in grid for v in row if v)
    return any(len(rs) == 2 and rs[-1] - rs[0] >= 2 and counts[color] != 2
               for col in _column_groups(grid) for color, rs in col.items())


SEMANTIC_WITNESSES = {"triple_gap": _triple_gap, "unlike_endpoints": _unlike_endpoints,
                      "mixed_pair": _mixed_pair, "reused_pair_color": _reused_pair_color}
SEMANTIC_RIVALS = {"at_least_two": _at_least_two, "any_two": _any_two,
                   "monochrome_column": _monochrome_column, "global_two": _global_two}
WITNESS_RIVALS = {"triple_gap": ["at_least_two"], "unlike_endpoints": ["any_two"],
                  "mixed_pair": ["monochrome_column"], "reused_pair_color": ["global_two"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
