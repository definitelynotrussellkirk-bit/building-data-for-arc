"""Three-panel voting with an explicit lesson and override contract.

The reference counts nonzero votes first, then color frequency, and only
then numeric rank to break a frequency tie. See notes.md for the visual
domain, the ordinary curriculum, and the deliberately weaker edge draws.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ca05c7eef24"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "92b2f8e4de94"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Three h-by-pw panels (h=3..7, pw=2..6) separated by two gray-5 columns. "
    "At each local position, fewer than two nonzero votes produce zero; "
    "otherwise select the most frequent nonzero color, with larger color "
    "winning a frequency tie. Ordinary draws cycle through 1,2,3,3,1,1,3,3 foreground "
    "colors and construct voting counterexamples. Exact count, geometry and "
    "palette controls use a separate feasible constructor."
)
INVARIANTS = [
    "integer grid h by (3*pw+2), h=3..7 and pw=2..6",
    "only divider columns pw and 2*pw+1 contain color 5",
    "panel cells are zero or colors 1,2,3,4,6,7,8,9",
    "ordinary draws have singleton, two-vote and three-vote positions",
]
PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_overlap", "all_overlap")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
AXES = {
    "h": {"type": "int", "default": "curriculum 3..7", "valid": "3..7"},
    "pw": {"type": "int", "default": "curriculum 3..6", "valid": "2..6"},
    "n_cells": {"type": "int", "default": "variable by panel; common count or None", "valid": "1..18"},
    "palette_size": {"type": "int", "default": "cycle 1,2,3,3,1,1,3,3 foreground colors", "valid": "1..8"},
    "palette_kind": {"type": "str", "default": "default", "valid": "default", "probe": "diagnostic"},
    "position_bias": {"type": "str", "default": "three_panels_5col_split", "valid": "three_panels_5col_split", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "default", "valid": "default|no_overlap|all_overlap"},
}
# Preserve the old caller name without advertising a second independent axis.
COMPATIBILITY_ALIASES = {"n_distinct_colors": "palette_size"}
_INT_BOUNDS = {"h": (3, 7), "pw": (2, 6), "n_cells": (1, 18),
               "palette_size": (1, 8), "n_distinct_colors": (1, 8)}
_STR_VALUES = {"palette_kind": PALETTE_KINDS,
               "position_bias": ("three_panels_5col_split",),
               "texture": ("default",) + DEGENERATE_TEXTURES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the visual domain without trusting caller metadata."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["rows must be nonempty lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integers 0..9, excluding booleans"]
    pw, remainder = divmod(w - 2, 3)
    if not 3 <= h <= 7 or remainder or not 2 <= pw <= 6:
        return ["expected h=3..7 and width=3*pw+2 with pw=2..6"]
    dividers = {pw, 2 * pw + 1}
    if any((value == 5) != (col in dividers)
           for row in grid for col, value in enumerate(row)):
        return ["color 5 must fill exactly the two equal-panel divider columns"]
    return []


def strict_canonical_like(grid):
    """The documented visual manifold; mixed colors are reference-lawful."""
    return self_check(grid)


def _votes(grid):
    pw = (len(grid[0]) - 2) // 3
    for row in grid:
        for c in range(pw):
            yield tuple(row[c + p * (pw + 1)] for p in range(3))


def _winner(values):
    active = [v for v in values if v]
    return max(active, key=lambda v: (active.count(v), v)) if len(active) >= 2 else 0


def _map_votes(grid, fn):
    reasons = self_check(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    pw = (len(grid[0]) - 2) // 3
    values = iter(_votes(grid))
    return [[fn(next(values)) for _ in range(pw)] for _ in grid]


def apply_rule(grid):
    """Pure Python authoring mirror, independently checked against Racket."""
    return _map_votes(grid, _winner)


def observe_overrides(grid):
    reasons = self_check(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    votes = list(_votes(grid))
    counts = [sum(v[p] != 0 for v in votes) for p in range(3)]
    active_counts = {sum(x != 0 for x in v) for v in votes if any(v)}
    texture = ("no_overlap" if active_counts == {1} else
               "all_overlap" if active_counts == {3} else "default")
    palette = len({v for row in grid for v in row} - {0, 5})
    return {"h": len(grid), "pw": (len(grid[0]) - 2) // 3,
            "n_cells": counts[0] if len(set(counts)) == 1 else None,
            "palette_size": palette, "n_distinct_colors": palette,
            "palette_kind": "default", "position_bias": "three_panels_5col_split",
            "texture": texture}


def _validate(overrides):
    unknown = set(overrides) - set(AXES) - set(COMPATIBILITY_ALIASES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    supplied = {k: v for k, v in overrides.items() if v is not None}
    for key, value in supplied.items():
        if key in _INT_BOUNDS:
            lo, hi = _INT_BOUNDS[key]
            if type(value) is not int:
                raise TypeError(f"{key} must be an integer, not bool/float/string")
            if not lo <= value <= hi:
                raise ValueError(f"{key} must be in {lo}..{hi}")
        elif type(value) is not str or value not in _STR_VALUES[key]:
            raise ValueError(f"unsupported {key}: {value!r}")
    return supplied


def _incompatible(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(axes))
    raise error


def schedule_profile(seed, sample_index, difficulty=None):
    """Eight slots with two three-color examples in every four draws."""
    return (seed + sample_index) % 8


SCHEDULE_PROFILES = tuple(range(8))
LESSON_SCHEDULE_PERIOD = 8


def _preferred(seed, sample_index, band):
    phase = schedule_profile(seed, sample_index)
    slot = phase % 4
    palette = (1, 2, 3, 3, 1, 1, 3, 3)[phase]
    if palette == 1:
        h, pw = (3, 3) if phase == 0 else (4, 4)
    else:
        h, pw = {"easy": ((3, 3), (3, 4), (4, 3)),
                 "medium": ((4, 4), (5, 4), (5, 5)),
                 "hard": ((5, 5), (6, 5), (7, 6))}[band][slot - 1]
    return h, pw, palette


def _record_int(ctx, supplied, key, chosen):
    if key in supplied:
        return ctx.draw_int_strict(key, *_INT_BOUNDS[key])
    return ctx.draw_choice(key, (chosen,))


def _frame(h, pw):
    grid = full_grid(h, 3 * pw + 2, 0)
    for row in grid:
        row[pw] = row[2 * pw + 1] = 5
    return grid


def _render_motifs(h, pw, motifs, positions, order):
    grid = _frame(h, pw)
    for pos, values in zip(positions, motifs):
        row, col = divmod(pos, pw)
        for panel, source in enumerate(order):
            grid[row][col + panel * (pw + 1)] = values[source]
    return grid


def _refutes_declared_rivals(grid):
    expected = apply_rule(grid)
    return all(rival(grid) != expected for rival in LESSON_COMPETITORS.values())


def _ordinary(ctx, h, pw, palette, band):
    rng = ctx.draw_rng("voting_layout")
    colors = sorted(ctx.draw_distinct_colors("foreground_colors", n=palette, exclude=(0, 5)))
    a, b, c = colors[0], colors[min(1, palette - 1)], colors[-1]
    core = [(a, 0, 0), (a, b, 0), (b, 0, a), (0, b, b),
            (a, a, b), (a, b, c), (b, b, a)]
    extra = min(h * pw - len(core) - 1, {"easy": 0, "medium": 3, "hard": 12}[band])
    # Randomize the layout and clutter, but do not export a three-color
    # lesson witness if a declared global color-priority shortcut survives.
    for _attempt in range(64):
        positions = rng.sample(range(h * pw), h * pw)
        order = rng.sample(range(3), 3)
        motifs = list(core)
        for _ in range(max(0, extra)):
            motifs.append(tuple(rng.choice((0,) + tuple(colors)) for _ in range(3)))
        grid = _render_motifs(h, pw, motifs, positions, order)
        if palette < 3 or _refutes_declared_rivals(grid):
            return grid
    # Bounded deterministic fallback: a7,b8,c1 globally, with a first and
    # last in row-major scanning. Each global tie-priority rival is refuted.
    grid = _render_motifs(h, pw, core, range(len(core)), range(3))
    if not _refutes_declared_rivals(grid):
        raise ValueError("the deterministic lesson fallback no longer refutes the declared rivals")
    return grid


def _feasible(supplied, preferred, palette, texture, band):
    h0, pw0 = preferred
    heights = [supplied["h"]] if "h" in supplied else range(3, 8)
    widths = [supplied["pw"]] if "pw" in supplied else range(2, 7)
    dimensions = sorted(((h, pw) for h in heights for pw in widths),
                        key=lambda x: (abs(x[0] - h0) + abs(x[1] - pw0), x))
    preferred_count = {"easy": 2, "medium": 3, "hard": 4}[band]
    counts = ([supplied["n_cells"]] if "n_cells" in supplied else
              sorted(range(1, 19), key=lambda n: (abs(n - preferred_count), n)))
    for h, pw in dimensions:
        area = h * pw
        for n in counts:
            if 3 * n < palette:
                continue
            if texture == "no_overlap" and 3 * n > area:
                continue
            if n > area - (texture == "default"):
                continue
            return h, pw, n
    relevant = set(supplied) & {"h", "pw", "n_cells", "palette_size", "n_distinct_colors", "texture"}
    _incompatible("joint geometry/count/palette/texture request is infeasible", relevant)


def _controlled(ctx, h, pw, n, palette, texture):
    rng = ctx.draw_rng("controlled_layout")
    area = h * pw
    positions = list(range(area))
    if texture == "no_overlap":
        chosen = rng.sample(positions, 3 * n)
        occupied = [chosen[p * n:(p + 1) * n] for p in range(3)]
    elif texture == "all_overlap":
        chosen = rng.sample(positions, n)
        occupied = [list(chosen) for _ in range(3)]
    else:
        pair, singleton = rng.sample(positions, 2)
        rest = [p for p in positions if p not in (pair, singleton)]
        occupied = [[pair] + rng.sample(rest, n - 1),
                    [pair] + rng.sample(rest, n - 1),
                    [singleton] + rng.sample(rest, n - 1)]
    colors = ctx.draw_distinct_colors("foreground_colors", n=palette, exclude=(0, 5))
    cells = [(p, pos) for p, group in enumerate(occupied) for pos in group]
    rng.shuffle(cells)
    grid = _frame(h, pw)
    for i, (panel, pos) in enumerate(cells):
        row, col = divmod(pos, pw)
        grid[row][col + panel * (pw + 1)] = colors[i] if i < palette else rng.choice(colors)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    supplied = _validate(overrides)
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    for key in ("palette_kind", "position_bias"):
        ctx.draw_choice(key, _STR_VALUES[key])
    texture = ctx.draw_choice("texture", (supplied.get("texture", "default"),))
    h, pw, palette = _preferred(seed, sample_index, band)
    if "palette_size" in supplied and "n_distinct_colors" in supplied:
        if supplied["palette_size"] != supplied["n_distinct_colors"]:
            _incompatible("palette_size and n_distinct_colors are exact aliases",
                          ("palette_size", "n_distinct_colors"))
    palette = supplied.get("palette_size", supplied.get("n_distinct_colors", palette))
    constraints = set(supplied) - {"palette_kind", "position_bias"}
    if supplied.get("texture") == "default":
        constraints.discard("texture")
    controlled = bool(constraints)
    if controlled:
        h, pw, n = _feasible(supplied, (h, pw), palette, texture, band)
        n = _record_int(ctx, supplied, "n_cells", n)
    h = _record_int(ctx, supplied, "h", h)
    pw = _record_int(ctx, supplied, "pw", pw)
    palette = _record_int(ctx, supplied, "palette_size", palette)
    _record_int(ctx, supplied, "n_distinct_colors", palette)
    if controlled:
        return _controlled(ctx, h, pw, n, palette, texture)
    grid = _ordinary(ctx, h, pw, palette, band)
    # The unconstrained constructor does not choose a uniform panel count.
    # Record the realized common count (or None) without inventing one.
    ctx.draw_choice("n_cells", (observe_overrides(grid)["n_cells"],))
    return grid


def _rival_vote(values, mode):
    active = [v for v in values if v]
    if mode == "union_max":
        return max(active, default=0)
    if len(active) < 2:
        return 0
    if mode == "exactly_two":
        return max(active) if len(active) == 2 else 0
    if mode == "threshold_max":
        return max(active)
    if mode == "first_nonzero":
        return active[0]
    if mode == "last_nonzero":
        return active[-1]
    if mode == "repeated_color_only":
        return next((v for v in active if active.count(v) >= 2), 0)
    if mode == "tie_min":
        return max(active, key=lambda v: (active.count(v), -v))
    if mode == "three_way_min":
        return min(active) if len(set(active)) == 3 else _winner(values)
    raise ValueError(f"unknown rival: {mode}")


def _rival(mode):
    def solve(grid):
        return _map_votes(grid, lambda values: _rival_vote(values, mode))
    return solve


def _global_tie_rival(mode):
    def solve(grid):
        counts, first, last = {}, {}, {}
        for index, value in enumerate(v for row in grid for v in row):
            if value not in (0, 5):
                counts[value] = counts.get(value, 0) + 1
                first.setdefault(value, index)
                last[value] = index
        priority = ({v: -n for v, n in counts.items()} if mode == "global_rarity_tie" else
                    counts if mode == "global_commonness_tie" else
                    {v: -n for v, n in first.items()} if mode == "first_seen_tie" else last)

        def vote(values):
            active = [v for v in values if v]
            return (max(active, key=lambda v: (active.count(v), priority[v], v))
                    if len(active) >= 2 else 0)

        return _map_votes(grid, vote)
    return solve


LESSON_COMPETITORS = {name: _rival(name) for name in (
    "union_max", "exactly_two", "threshold_max", "first_nonzero",
    "last_nonzero", "repeated_color_only", "tie_min", "three_way_min")}
_GLOBAL_TIE_RIVALS = ("global_rarity_tie", "global_commonness_tie", "first_seen_tie", "last_seen_tie")
LESSON_COMPETITORS.update({name: _global_tie_rival(name) for name in _GLOBAL_TIE_RIVALS})
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _has(grid, predicate):
    return not self_check(grid) and any(predicate(v) for v in _votes(grid))


SEMANTIC_WITNESSES = {
    "singleton": lambda g: _has(g, lambda v: sum(x != 0 for x in v) == 1),
    "double_distinct": lambda g: _has(g, lambda v: 0 in v and len(set(v) - {0}) == 2),
    "majority_over_larger": lambda g: _has(g, lambda v: 0 not in v and len(set(v)) == 2 and _winner(v) < max(v)),
    "three_way_tie": lambda g: _has(g, lambda v: 0 not in v and len(set(v)) == 3),
    "unanimous_three": lambda g: _has(g, lambda v: 0 not in v and len(set(v)) == 1),
    "first_disagrees": lambda g: _has(g, lambda v: _rival_vote(v, "first_nonzero") != _winner(v)),
    "last_disagrees": lambda g: _has(g, lambda v: _rival_vote(v, "last_nonzero") != _winner(v)),
}
WITNESS_RIVALS = {
    "singleton": ["union_max"], "double_distinct": ["repeated_color_only", "tie_min"],
    "majority_over_larger": ["threshold_max"], "three_way_tie": ["three_way_min"],
    "unanimous_three": ["exactly_two"], "first_disagrees": ["first_nonzero"],
    "last_disagrees": ["last_nonzero"],
}
SEMANTIC_WITNESSES.update({
    name + "_counterexample": lambda g, rival=name: (
        not self_check(g) and SEMANTIC_RIVALS[rival](g) != apply_rule(g))
    for name in _GLOBAL_TIE_RIVALS
})
WITNESS_RIVALS.update({name + "_counterexample": [name] for name in _GLOBAL_TIE_RIVALS})


def lesson_identifiable(demos, query):
    """Query identifiability against declared rivals, not universal induction."""
    grid = query["input"] if isinstance(query, dict) else query
    intended = apply_rule(grid)
    return [f"{name} fits all demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(grid) != intended]
