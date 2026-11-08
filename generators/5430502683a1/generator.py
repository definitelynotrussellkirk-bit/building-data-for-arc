"""Inputs for Longest Pair Wins; the unchanged Racket rule supplies labels.

The rule compares the NUMBER OF CELLS in aligned endpoint spans, not Euclidean
or Manhattan distance. An eight-example curriculum mixes two metric gap classes,
diagonal winners and unrestricted spans. Seven demos retain both gap witnesses
and every winning color after holding out any one pair. Palettes and pair
counts are stable within a seed; geometry and colors vary across seeds.

This sampler's manifold is 2..4 exact endpoint pairs, aligned horizontally,
vertically or at 45 degrees, with a unique longest span. The Racket rule has a
wider accidental execution domain; an output is not domain validation.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5430502683a1"
TASK_ID = GENERATOR_ID
RULE_HASH = "182c38f86c20"
VERSION = "4.0.1"
SUMMARY = (
    "On background 0, compare 2..4 same-color endpoint pairs by their aligned "
    "span's cell count. Keep only the unique longest span, painted 8. Lessons "
    "contrast geometric metrics, winning color ranks, and scan positions."
)
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "integer ARC grids with background 0 and 2..4 foreground colors",
    "each foreground color occurs exactly twice, on an H/V/45-degree span",
    "one pair has a unique longest span, whose endpoints and interior stay in bounds",
    "winner length, direction, scan position and numeric color rank vary",
    "input color 8 is legal; the output always paints only the winning span in 8",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted; broad sizes vary by band", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical-weighted; broad sizes vary by band", "valid": "9..18"},
    "pair_count": {"type": "int", "default": "seed-stable 2..4, weighted toward 3", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("gap_one", "diagonal", "gap_many", "free")
_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
_CANONICAL_SHAPES = ((10, 10), (9, 11))
_BROAD_SIZES = {
    "easy": ((8, 11), (9, 12)),
    "medium": ((9, 14), (10, 16)),
    "hard": ((12, 16), (13, 18)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four semantic profiles; full color/scan coverage repeats every eight."""
    return SCHEDULE_PROFILES[(sample_index + seed % 8) % 4]


def _draw_axis(ctx, name, default, domain):
    # Record scheduled defaults publicly. Overrides see the full domain in
    # EVERY difficulty, with no clipping or unrecorded post-draw correction.
    choices = domain if ctx.overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=1024)
def _placements(h, w, length, direction):
    """Immutable endpoint geometry only; no sampled grid is cached."""
    dr, dc = _DIRECTIONS[direction]
    return tuple(
        ((r, c), (r + dr * (length - 1), c + dc * (length - 1)))
        for r in range(h) for c in range(w)
        if 0 <= r + dr * (length - 1) < h
        and 0 <= c + dc * (length - 1) < w
    )


def _loser_options(h, w, length, metric, profile, rng):
    if metric and profile == "gap_one":
        options = [(length - 1, 2), (length - 1, 3)]
    elif metric:
        options = [(n, d) for n in range(2, min(h, w, length - 2) + 1)
                   for d in (2, 3) if 2 * (n - 1) ** 2 > (length - 1) ** 2]
    else:
        options = [(n, d) for n in range(2, length) for d in range(4)
                   if _placements(h, w, n, d)
                   and not (profile == "gap_many" and d in (2, 3) and n == length - 1)]
    rng.shuffle(options)
    return options


def _layout(h, w, k, profile, scan_rank, rng):
    """Place exact pairs without overlap, shortening or a biased fallback.

    Only endpoints must be disjoint: a winner may cross another pair's span
    or endpoint, because the reference reads the original color groups.
    Failed geometric proposals are retried; failure never emits a partial grid.
    """
    for _ in range(256):
        metric_profile = profile in ("gap_one", "gap_many")
        directions = (0, 1) if metric_profile else (2, 3) if profile == "diagonal" else (0, 1, 2, 3)
        direction = rng.choice(directions)
        available = w if direction == 0 else h if direction == 1 else min(h, w)
        if profile == "gap_one":
            length = rng.randint(5, min(available, min(h, w) + 1))
        elif profile == "gap_many":
            lengths = [n for n in range(8, available + 1)
                       if any(2 * (d - 1) ** 2 > (n - 1) ** 2
                              for d in range(2, min(h, w, n - 2) + 1))]
            length = rng.choice(lengths)
        else:
            length = rng.randint(3, available)
        winner = rng.choice(_placements(h, w, length, direction))
        pairs, occupied = [winner], set(winner)
        sides = [-1] * scan_rank + [1] * (k - 1 - scan_rank)
        rng.shuffle(sides)
        for index, side in enumerate(sides):
            placed = False
            for n, d in _loser_options(h, w, length, metric_profile and index == 0, profile, rng):
                candidates = [pair for pair in _placements(h, w, n, d)
                              if not any(point in occupied for point in pair)
                              and ((pair[0] < winner[0]) if side < 0 else (pair[0] > winner[0]))]
                if candidates:
                    pair = rng.choice(candidates)
                    pairs.append(pair)
                    occupied.update(pair)
                    placed = True
                    break
            if not placed:
                break
        if len(pairs) == k:
            return pairs
    raise RuntimeError(f"could not place {k} exact pairs on {h}x{w}; no fallback emitted")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    # Family randomness deliberately excludes sample_index. Every member of
    # a lesson uses the same palette and count, making color preferences
    # directly testable while positions, dimensions and winning roles change.
    family = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID)
    palette = family.draw_rng("family_palette").sample(range(1, 10), 4)
    default_k = family.draw_choice("family_pair_count", (2, 3, 3, 3, 4))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    shape_rng = ctx.draw_rng("shape")
    if shape_rng.randrange(5) < 3:
        dh, dw = shape_rng.choice(_CANONICAL_SHAPES)
    else:
        hrange, wrange = _BROAD_SIZES[difficulty or "medium"]
        dh, dw = shape_rng.randint(*hrange), shape_rng.randint(*wrange)
    h = _draw_axis(ctx, "grid_h", dh, tuple(range(8, 17)))
    w = _draw_axis(ctx, "grid_w", dw, tuple(range(9, 19)))
    k = _draw_axis(ctx, "pair_count", default_k, (2, 3, 4))
    colors = sorted(palette[:k])
    slot = (sample_index + seed % 8) % 8
    profile = SCHEDULE_PROFILES[slot % 4]
    ranks = (0, (k - 1) // 2, k - 1, k // 2)
    rank = ranks[(slot // 2 + seed // 7) % 4]
    # Each numeric rank and scan rank appears twice for k=4, but a color's
    # two wins occupy different scan positions. Smaller palettes repeat roles.
    scan_rank = ranks[(slot + slot // 4 + seed // 11) % 4]
    rng = ctx.draw_rng("layout")
    pairs = _layout(h, w, k, profile, scan_rank, rng)
    winner = colors.pop(rank)
    rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for color, pair in zip([winner] + colors, pairs):
        for r, c in pair:
            grid[r][c] = color
    return grid


def _groups(grid):
    grouped = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                grouped.setdefault(value, []).append((r, c))
    return grouped


def _span_len(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) + 1


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9"]
    if not any(value == 0 for row in grid for value in row):
        return ["background 0 is required"]
    groups = _groups(grid)
    if not 2 <= len(groups) <= 4:
        return ["expected 2..4 endpoint colors"]
    errors, lengths = [], []
    for color, points in groups.items():
        if len(points) != 2:
            errors.append(f"color {color} must have exactly two endpoints, got {len(points)}")
            continue
        a, b = points
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        if dr and dc and dr != dc:
            errors.append(f"color {color} endpoints are not horizontal, vertical or 45-degree aligned")
        lengths.append(_span_len(a, b))
    if lengths and lengths.count(max(lengths)) != 1:
        errors.append("the longest span must be unique")
    return errors


def strict_canonical_like(grid):
    """The endpoint-pair manifold; canonical size is measured separately."""
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "pair_count": len(_groups(grid))}


def _pairs(grid):
    return [(color, points[0], points[1]) for color, points in sorted(_groups(grid).items())
            if len(points) == 2]


def _paint(grid, pair):
    out = full_grid(len(grid), len(grid[0]), 0)
    if pair is None:
        return out
    _, a, b = pair
    dr = (b[0] > a[0]) - (b[0] < a[0])
    dc = (b[1] > a[1]) - (b[1] < a[1])
    for i in range(_span_len(a, b)):
        r, c = a[0] + i * dr, a[1] + i * dc
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


def _longest(pairs):
    return max(pairs, key=lambda p: _span_len(p[1], p[2])) if pairs else None


def _rival_euclidean(grid):
    pairs = _pairs(grid)
    pair = max(pairs, key=lambda p: sum((a - b) ** 2 for a, b in zip(p[1], p[2]))) if pairs else None
    return _paint(grid, pair)


def _rival_manhattan(grid):
    pairs = _pairs(grid)
    pair = max(pairs, key=lambda p: sum(abs(a - b) for a, b in zip(p[1], p[2]))) if pairs else None
    return _paint(grid, pair)


def _rival_diagonal(grid):
    pairs = _pairs(grid)
    diagonals = [p for p in pairs if p[1][0] != p[2][0] and p[1][1] != p[2][1]]
    return _paint(grid, _longest(diagonals or pairs))


def _rival_color_rank(grid, rank):
    pairs = _pairs(grid)
    pair = pairs[rank] if -len(pairs) <= rank < len(pairs) else None
    return _paint(grid, pair)


def _rival_scan(grid, last=False):
    pairs = sorted(_pairs(grid), key=lambda p: p[1])
    return _paint(grid, pairs[-1 if last else 0] if pairs else None)


def _rival_prefer_color(grid, color):
    pairs = _pairs(grid)
    return _paint(grid, next((p for p in pairs if p[0] == color), _longest(pairs)))


def _rival_ignore_color(grid, color):
    return _paint(grid, _longest([p for p in _pairs(grid) if p[0] != color]))


def _rival_axis_gap(grid, many=False):
    pairs = _pairs(grid)
    axis = _longest([p for p in pairs if p[1][0] == p[2][0] or p[1][1] == p[2][1]])
    diagonal = _longest([p for p in pairs if p[1][0] != p[2][0] and p[1][1] != p[2][1]])
    if axis is None or diagonal is None:
        return _paint(grid, _longest(pairs))
    gap = _span_len(axis[1], axis[2]) - _span_len(diagonal[1], diagonal[2])
    allowed = gap >= 2 if many else gap == 1
    return _paint(grid, axis if allowed else diagonal)


SEMANTIC_RIVALS = {
    "longest_euclidean": _rival_euclidean,
    "longest_manhattan": _rival_manhattan,
    "prefer_diagonal": _rival_diagonal,
    "lowest_color": lambda grid: _rival_color_rank(grid, 0),
    "highest_color": lambda grid: _rival_color_rank(grid, -1),
    "second_lowest_color": lambda grid: _rival_color_rank(grid, 1),
    "second_highest_color": lambda grid: _rival_color_rank(grid, -2),
    "first_in_scan": _rival_scan,
    "last_in_scan": lambda grid: _rival_scan(grid, True),
    "axis_only_gap_one": _rival_axis_gap,
    "axis_only_gap_many": lambda grid: _rival_axis_gap(grid, True),
}
for _color in range(1, 10):
    SEMANTIC_RIVALS[f"prefer_color_{_color}"] = lambda grid, color=_color: _rival_prefer_color(grid, color)
    SEMANTIC_RIVALS[f"ignore_color_{_color}"] = lambda grid, color=_color: _rival_ignore_color(grid, color)


def _refutes(grid, rival):
    return rival(grid) != _paint(grid, _longest(_pairs(grid)))


# Predicates use task geometry. The shared gate independently verifies every
# rival claim against the actual Racket output, not this Python mirror.
SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: _refutes(grid, rival))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name] for name in (
        "longest_euclidean", "longest_manhattan", "prefer_diagonal",
        "axis_only_gap_one", "axis_only_gap_many",
        "prefer_color_4", "prefer_color_5", "prefer_color_6",
        "prefer_color_7", "prefer_color_8", "prefer_color_9",
        "ignore_color_2", "ignore_color_4", "ignore_color_5", "ignore_color_6",
        "ignore_color_7", "ignore_color_8", "ignore_color_9",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check, never a universal induction certificate."""
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"{name} fits every demonstration but disagrees on the query")
    return errors
