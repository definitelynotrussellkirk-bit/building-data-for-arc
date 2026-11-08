"""Top-row blue cell count selects a green component's descending size rank.

The selected Racket rule is the label authority. Python predictions below are
finite diagnostic mirrors only. Default lessons use a period-two semantic
schedule: each even draw refutes all eight canonical-fitting rivals, and each
odd draw is a varied lawful layout. A period-ten subcycle anchors strict
canonical support. Exact overrides use the general lawful sampler and do not
promise the default lesson curriculum.
"""
from __future__ import annotations

from copy import deepcopy
from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = TASK_ID = "c7070676c606"
VERSION = "3.0.0"
RULE_HASH = "53d5f7ffc079"
SUMMARY = (
    "Count color-1 cells in row 0, rank eligible color-3 four-connected "
    "components by descending cell count then first occupied cell, and "
    "recolor rank k to 2. Default lessons interleave joint counterexamples "
    "with varied lawful shapes, including ties, singleton and endpoint ranks."
)
INVARIANTS = [
    "ARC integer colors 0..9; fixed semantic colors: blue 1, green 3, red 2",
    "eligible green components lie entirely below row 0",
    "1 <= row-0 blue cell count <= eligible green component count",
    "ties rank by earliest occupied (row, column), not bounding-box corner",
]
AXES = {
    "grid_h": {"type": "int", "default": "varies", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "varies", "valid": "11..24"},
    "n_shapes": {"type": "int", "default": "varies", "valid": "1..5"},
    "k_select": {"type": "int", "default": "1..n_shapes", "valid": "1..5"},
}
EXAMPLES_NEEDED = 3
# Parity supplies the teaching guarantee; phase 1 supplies strict anchors.
LESSON_SCHEDULE_PERIOD = 10
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))
MIN_STRICT_FRAC = 0.05
_CANONICAL_PROFILES = ((10, 11), (12, 12), (13, 13))
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_LIMITS = {"grid_h": (10, 24), "grid_w": (11, 24),
           "n_shapes": (1, 5), "k_select": (1, 5)}


def schedule_profile(seed, sample_index, difficulty=None):
    return sample_index % LESSON_SCHEDULE_PERIOD


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty grid of row lists"]
    if any(not isinstance(row, list) for row in grid):
        return ["expected row lists"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["expected integer ARC colors 0..9 (not bool)"]
    return []


def _candidates(grid, *, diagonal=False):
    objects = find_objects(grid, univalued=True, diagonal=diagonal, bg=0)
    candidates = [frozenset(cell for color, cell in obj) for obj in objects
                  if all(color == 3 and cell[0] > 0 for color, cell in obj)]
    return sorted(candidates, key=lambda cells: (-len(cells), min(cells)))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    k = grid[0].count(1)
    n = len(_candidates(grid))
    if not 1 <= k <= n:
        return [f"rank undefined: row 0 has {k} blue cells, but {n} eligible green components"]
    return []


def observe_overrides(grid):
    """Measure exact controls from pixels, including full-component eligibility."""
    if _grid_errors(grid):
        raise ValueError("observe_overrides requires an integer rectangular ARC grid")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_shapes": len(_candidates(grid)), "k_select": grid[0].count(1)}


def strict_canonical_like(grid):
    """Canonical scale/palette/rank manifold, separate from broad lawful inputs.

    This deliberately excludes rich witnesses' extra blue cells, ties and
    singleton endpoints. It does not claim exact canonical shape templates.
    """
    errors = self_check(grid)
    if errors:
        return errors
    reasons = []
    if (len(grid), len(grid[0])) not in _CANONICAL_PROFILES:
        reasons.append("outside exact canonical dimension profiles")
    if {v for row in grid for v in row} != {0, 1, 3}:
        reasons.append("outside canonical input palette")
    if any(1 in row for row in grid[1:]):
        reasons.append("canonical blue cells are confined to row 0")
    objects = _candidates(grid)
    sizes = [len(obj) for obj in objects]
    if len(objects) not in (3, 4) or grid[0].count(1) not in (2, 3):
        reasons.append("outside canonical component-count/rank envelope")
    if min(sizes) < 2 or len(set(sizes)) != len(sizes):
        reasons.append("canonical components have distinct sizes of at least two")
    return reasons


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or removed override axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _LIMITS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi} (not bool, float or string)")
    n, k = overrides.get("n_shapes"), overrides.get("k_select")
    if n is not None and k is not None and k > n:
        error = ValueError("k_select cannot exceed n_shapes")
        error.axes = ("n_shapes", "k_select")
        raise error


def _profile_axes(ctx):
    h = ctx.draw_choice("grid_h", (10, 12, 13))
    w = ctx.draw_choice("grid_w", ({10: 11, 12: 12, 13: 13}[h],))
    return h, w


def _rich(ctx, sample_index):
    """Construct joint witnesses; all variations preserve eight disagreements."""
    h, w = _profile_axes(ctx)
    n = ctx.draw_int_strict("n_shapes", 3, 5)
    ctx.draw_int_strict("k_select", 2, 2)
    rng = ctx.draw_rng("rich_layout")
    arm = rng.randint(2, 4)
    solid_width = 2 if arm == 2 else 3
    dr, dc = rng.randint(0, h - 10), rng.randint(0, w - 11)
    mirror = rng.choice((False, True))
    g = full_grid(h, w, 0)
    shapes = [([(2, c) for c in range(1, arm + 1)] + [(3, arm)]),
              [(4, arm + 1), (4, arm + 2)],
              [(r, c) for r in (7, 8) for c in range(7, 7 + solid_width)]]
    shapes += [[(6, 0)], [(8, 3)]][:n - 3]
    for shape in shapes:
        for r, c in shape:
            col = c + dc
            g[r + dr][w - 1 - col if mirror else col] = 3
    extra_col = w - 1 - dc if mirror else dc
    g[9 + dr][extra_col] = 1
    # If two even inputs share dimensions, adjacent starts differ. Generic
    # draws have no below-row blue, so they cannot duplicate a rich input.
    start = (sample_index // 2) % (w - 1)
    g[0][start] = g[0][start + 1] = 1
    return g


def _sections(start, length, count):
    """Balanced chambers with a guaranteed one-cell blank separator."""
    usable = length - count + 1
    base, extra = divmod(usable, count)
    sections = []
    for i in range(count):
        size = base + (i < extra)
        sections.append((start, size))
        start += size + 1
    return sections


def _poly(rng, size, height, width):
    """Connected growth in a finite chamber; sorted frontier avoids hash order."""
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _CARD
                           if 0 <= r + dr < height and 0 <= c + dc < width}
                          - cells)
        cells.add(rng.choice(frontier))
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return [(r - r0, c - c0) for r, c in sorted(cells)]


def _general(ctx, sample_index, *, anchor=False):
    if anchor:
        h, w = _profile_axes(ctx)
        n = ctx.draw_int_strict("n_shapes", 3, 4)
        k = ctx.draw_int_strict("k_select", 2, min(3, n))
    else:
        h = ctx.draw_int_strict("grid_h", 10, 24)
        w = ctx.draw_int_strict("grid_w", 11, 24)
        n = ctx.draw_int_strict("n_shapes", ctx.overrides.get("k_select") or 1, 5)
        k = ctx.draw_int_strict("k_select", 1, n)
    rng = ctx.draw_rng("general_layout")
    g = full_grid(h, w, 0)
    # Anchor chambers have at least 4x5 cells even on the minimum profile;
    # distinct sizes 2..8 therefore always fit. Other layouts may be narrow.
    layouts = [(2, 2)] if anchor else [(rows, (n + rows - 1) // rows)
                                      for rows in range(1, n + 1)]
    nr, nc = rng.choice(layouts)
    chambers = [(r, c, rh, cw) for r, rh in _sections(1, h - 1, nr)
                for c, cw in _sections(0, w, nc)]
    rng.shuffle(chambers)
    used_sizes = set()
    max_size = {"easy": 8, "medium": 16, "hard": 30}.get(ctx.difficulty, 16)
    for top, left, rh, cw in chambers[:n]:
        cap = min(rh * cw, max_size)
        choices = [size for size in range(2 if anchor else 1, cap + 1)
                   if not anchor or size not in used_sizes]
        size = rng.choice(choices)
        used_sizes.add(size)
        shape = _poly(rng, size, rh, cw)
        sh = max(r for r, c in shape) + 1
        sw = max(c for r, c in shape) + 1
        r0, c0 = top + rng.randint(0, rh - sh), left + rng.randint(0, cw - sw)
        for r, c in shape:
            g[r0 + r][c0 + c] = 3
    # Fixed cyclic patterns guarantee adjacent odd draws have different marker
    # sets whenever dimensions and k coincide. Anchor patterns are separated;
    # generic patterns are contiguous, including lawful boundary-wrapping runs.
    start = (sample_index // 2) % w
    stride = 2 if anchor else 1
    for i in range(k):
        g[0][(start + stride * i) % w] = 1
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if any(value is not None for value in overrides.values()):
        return _general(ctx, sample_index)
    if sample_index % 2 == 0:
        return _rich(ctx, sample_index)
    return _general(ctx, sample_index, anchor=sample_index % 10 == 1)


_RIVAL_NAMES = ("top_to_bottom", "bbox_area", "bbox_width", "bbox_height",
                "perimeter", "eight_connected", "global_blue_count", "blue_runs")


def _prediction(grid, *, rival="intended"):
    """Pure diagnostic prediction; undefined ranks/invalid grids stay unchanged.

    The Racket rule raises on undefined ranks. Unchanged-output behavior here
    makes finite rivals total without presenting it as authoritative behavior.
    """
    out = deepcopy(grid)
    if _grid_errors(grid):
        return out
    k = grid[0].count(1)
    if rival == "global_blue_count":
        k = sum(row.count(1) for row in grid)
    elif rival == "blue_runs":
        k = sum(value == 1 and (c == 0 or grid[0][c - 1] != 1)
                for c, value in enumerate(grid[0]))
    objects = _candidates(grid, diagonal=rival == "eight_connected")
    if not 1 <= k <= len(objects):
        return out

    def key(cells):
        first = min(cells)
        if rival == "top_to_bottom":
            return first
        height = max(r for r, c in cells) - min(r for r, c in cells) + 1
        width = max(c for r, c in cells) - min(c for r, c in cells) + 1
        scores = {"bbox_area": height * width, "bbox_width": width,
                  "bbox_height": height,
                  "perimeter": sum((r + dr, c + dc) not in cells
                                   for r, c in cells for dr, dc in _CARD)}
        return -scores.get(rival, len(cells)), first

    target = sorted(objects, key=key)[k - 1]
    for r, c in target:
        out[r][c] = 2
    return out


SEMANTIC_RIVALS = {name: partial(_prediction, rival=name) for name in _RIVAL_NAMES}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, *, rival):
    return not self_check(grid) and _prediction(grid) != SEMANTIC_RIVALS[rival](grid)


SEMANTIC_WITNESSES = {name: partial(_refutes, rival=name) for name in _RIVAL_NAMES}
WITNESS_RIVALS = {name: [name] for name in _RIVAL_NAMES}


def lesson_identifiable(demos, query):
    """Diagnose finite rival ambiguity from labels, never from phase metadata.

    The declared competitors are a finite diagnostic family, not a proof that
    the intended rule is uniquely identifiable among all conceivable programs.
    """
    pairs = list(demos) + [query]
    for pair in pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["expected labeled demonstration/query pairs"]
        errors = self_check(pair["input"])
        if errors:
            return ["lesson contains an undefined input rank: " + errors[0]]
        if pair["output"] != _prediction(pair["input"]):
            return ["lesson label disagrees with diagnostic selected-rule mirror"]
    return [f"{name} fits demonstrations but changes query"
            for name, solve in LESSON_COMPETITORS.items()
            if all(solve(pair["input"]) == pair["output"] for pair in demos)
            and solve(query["input"]) != query["output"]]
