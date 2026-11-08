"""Inputs for Parallel Bars Become Solid, with unchanged Racket authority.

Bars are four-connected, same-color vertical components of height >= 2.
The authority groups by (color, top, bottom), then fills sorted disjoint
column pairs from the left; a final odd bar is left alone. This module
produces inputs and diagnostic rivals, never authoritative output labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "d65b2dd82d74"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "220859949b76"
SUMMARY = (
    "Pair vertical bars by color and exact row span, in left-to-right disjoint "
    "pairs. Includes multiple same-color pairs and unmatched span/odd-bar witnesses."
)
INVARIANTS = [
    "background is 0; foreground components are contiguous vertical bars of height >= 2",
    "bars pair only within an exact (color, first row, last row) key",
    "at least one pair is present; odd trailing and mismatched-span bars may remain unpaired",
    "generated pair rectangles are disjoint and never overwrite another color",
    "explicit counts are realized constructively, never shortened after placement retries",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical 9/10/11 or rng 6..20", "valid": "6..20"},
    "grid_w": {"type": "int", "default": "canonical 12/11/13 or rng 9..24", "valid": "9..24"},
    "n_pairs": {"type": "int", "default": "schedule 2,3,3", "valid": "1..4"},
    "n_distinct_colors": {"type": "int", "default": "2; at most n_pairs for explicit requests", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "exact synonym for n_distinct_colors", "valid": "1..4"},
}
_BOUNDS = {"grid_h": (6, 20), "grid_w": (9, 24), "n_pairs": (1, 4),
           "n_distinct_colors": (1, 4), "palette_size": (1, 4)}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # Conditional refusals carry exact axes.
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_anchor", "even_pairs_and_span", "odd_trailing_bar")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _incompatible(axes, reason):
    error = ValueError(f"incompatible_axes={tuple(axes)!r}: {reason}")
    error.incompatible_axes = tuple(axes)
    raise error


def _request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        lo, hi = _BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    aliases = ("n_distinct_colors", "palette_size")
    if all(name in overrides for name in aliases):
        if overrides[aliases[0]] != overrides[aliases[1]]:
            _incompatible(aliases, "both spellings must request the same color count")


def _axis(ctx, overrides, name, default):
    if name in overrides:
        return ctx.draw_int(name, *_BOUNDS[name])
    return ctx.draw_int(name, default, default)


def _partition(total, parts, minimum, rng):
    """Random allocation with exact total and no placement rejection."""
    values = [minimum] * parts
    for _ in range(total - minimum * parts):
        values[rng.randrange(parts)] += 1
    return values


def _columns(count, width, rng):
    """Distinct columns with at least one blank column between neighbors."""
    points = sorted(rng.sample(range(width - count + 1), count))
    return [point + index for index, point in enumerate(points)]


def _put_bars(grid, color, top, height, columns):
    for row in range(top, top + height):
        for column in columns:
            grid[row][column] = color


def _generic_grid(h, w, n_pairs, palette, rng):
    """Shelf packing supports every declared size and feasible count tuple.

    At the 6x9 minimum, two rows of two 2x3 pair boxes fit with blank
    separating rows/columns. Larger canvases vary slots, heights and margins.
    """
    grid = full_grid(h, w, 0)
    capacity = (w + 1) // 4
    min_bands = (n_pairs + capacity - 1) // capacity
    max_bands = min(n_pairs, (h + 1) // 3)
    band_count = rng.randint(min_bands, max_bands)
    counts = [1] * band_count
    for _ in range(n_pairs - band_count):
        candidates = [i for i, count in enumerate(counts) if count < capacity]
        counts[rng.choice(candidates)] += 1
    heights = _partition(h - (band_count - 1), band_count, 2, rng)
    colors = list(palette) + [rng.choice(palette) for _ in range(n_pairs - len(palette))]
    rng.shuffle(colors)
    row, color_index = 0, 0
    for band_height, count in zip(heights, counts):
        slots = _partition(w - (count - 1), count, 3, rng)
        height = rng.randint(2, band_height)
        top = row + rng.randint(0, band_height - height)
        col = 0
        for slot_width in slots:
            left, right = _columns(2, slot_width, rng)
            _put_bars(grid, colors[color_index], top, height, [col + left, col + right])
            color_index += 1
            col += slot_width + 1
        row += band_height + 1
    return grid


def _scheduled_grid(h, w, profile, palette, rng, difficulty):
    if profile == "canonical_anchor":
        return _generic_grid(h, w, 2, palette, rng)
    grid = full_grid(h, w, 0)
    stagger = 1 if profile == "even_pairs_and_span" else 0
    maximum = 3 if difficulty == "easy" else (5 if difficulty == "hard" else 4)
    first_height = rng.randint(2, min(maximum, h - 3 - stagger))
    second_height = rng.randint(2, min(maximum, h - first_height - 1 - stagger))
    slack = h - first_height - second_height - stagger - 1
    top_margin, extra_gap, _ = _partition(slack, 3, 0, rng)
    second_top = top_margin + first_height + 1 + extra_gap
    if profile == "even_pairs_and_span":
        # The closest gap is the middle, which is not a selected pair.
        middle = rng.randint(2, min(4, (w - 3) // 3))
        left_extra, right_extra, margin = _partition(w - 3 * middle - 3, 3, 0, rng)
        start = rng.randint(0, margin)
        columns = [start, start + middle + 1 + left_extra]
        columns += [columns[1] + middle,
                    columns[1] + 2 * middle + 1 + right_extra]
        _put_bars(grid, palette[0], top_margin, first_height, columns)
        left, middle, right = _columns(3, w, rng)
        # A matched outer pair and shifted middle bar share one color. The
        # authority extracts bars once, fills the pair, and preserves the
        # unmatched bar's protruding endpoint. Both reflections retain this
        # distinction; rejecting the entire mixed-span color is incorrect.
        _put_bars(grid, palette[1], second_top, second_height, [left, right])
        _put_bars(grid, palette[1], second_top + 1, second_height, [middle])
    else:
        _put_bars(grid, palette[0], top_margin, first_height, _columns(5, w, rng))
        _put_bars(grid, palette[1], second_top, second_height, _columns(2, w, rng))
    # Reflect inputs only. Racket labels left-to-right pairing on the resulting
    # input, including its odd key; no transformed reference output is assumed.
    if rng.choice((False, True)):
        grid.reverse()
    if rng.choice((False, True)):
        grid = [list(reversed(row)) for row in grid]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical_anchor":
        h_default, w_default = ((9, 12), (10, 11), (11, 13))[(sample_index // 3) % 3]
    else:
        h_default = ctx.draw_rng("canvas_height").randint(6, 20)
        w_default = ctx.draw_rng("canvas_width").randint(9, 24)
    h = _axis(ctx, overrides, "grid_h", h_default)
    w = _axis(ctx, overrides, "grid_w", w_default)
    default_pairs = 2 if profile == "canonical_anchor" else 3
    requested_colors = overrides.get("n_distinct_colors", overrides.get("palette_size"))
    default_pairs = max(default_pairs, requested_colors or 1)
    n_pairs = _axis(ctx, overrides, "n_pairs", default_pairs)
    color_default = requested_colors if requested_colors is not None else min(2, n_pairs)
    n_colors = _axis(ctx, overrides, "n_distinct_colors", color_default)
    alias_colors = _axis(ctx, overrides, "palette_size", n_colors)
    if n_colors != alias_colors:
        _incompatible(("n_distinct_colors", "palette_size"), "conflicting color counts")
    if n_colors > n_pairs:
        color_axes = [name for name in ("n_distinct_colors", "palette_size") if name in overrides]
        _incompatible(("n_pairs", *color_axes), "explicit paired layouts need colors <= pairs")
    palette = ctx.draw_rng("palette").sample(range(1, 10), n_colors)
    rng = ctx.draw_rng("layout")
    if overrides:
        return _generic_grid(h, w, n_pairs, palette, rng)
    return _scheduled_grid(h, w, profile, palette, rng, difficulty)


def _bars(grid):
    """Analyze generator-side four-connectivity using the shared helper."""
    bars, invalid = [], []
    for obj in find_objects(grid, univalued=True, diagonal=False, without_bg=True, bg=0):
        color = min(obj)[0]
        rows = [r for _, (r, c) in obj]
        columns = {c for _, (r, c) in obj}
        top, bottom = min(rows), max(rows)
        if len(columns) != 1 or len(obj) < 2 or len(obj) != bottom - top + 1:
            invalid.append(f"color {color} component at ({top}, {min(columns)}) is not a vertical bar")
        else:
            bars.append((color, top, bottom, min(columns)))
    bars.sort(key=lambda bar: (bar[1], bar[3], bar[0], bar[2]))
    return bars, invalid


def _groups(grid):
    groups = {}
    for color, top, bottom, column in _bars(grid)[0]:
        groups.setdefault((color, top, bottom), []).append(column)
    return {key: sorted(columns) for key, columns in groups.items()}


def observe_overrides(grid):
    groups = _groups(grid)
    colors = len({v for row in grid for v in row if v})
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pairs": sum(len(columns) // 2 for columns in groups.values()),
            "n_distinct_colors": colors, "palette_size": colors}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds 30x30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    _, errors = _bars(grid)
    if errors:
        return errors
    groups = _groups(grid)
    pair_count, painted = 0, {}
    for (color, top, bottom), columns in groups.items():
        for left, right in zip(columns[::2], columns[1::2]):
            pair_count += 1
            if right - left < 2:
                errors.append("bar pair has no interior gap")
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    if grid[r][c] not in (0, color):
                        errors.append("pair rectangle would overwrite a different color")
                    if (r, c) in painted:
                        errors.append("pair rectangles overlap outside this generator's domain")
                    painted[(r, c)] = color
    if not pair_count:
        errors.append("no fillable bar pair")
    return list(dict.fromkeys(errors))


def strict_canonical_like(grid):
    """Expanded bar-only authority manifold, not literal canonical color/counts."""
    return self_check(grid)


def _paint(out, color, top, bottom, left, right):
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            out[r][c] = color


def _color_bbox(grid):
    """Rival: fill one bounding rectangle for each nonzero color."""
    out = [list(row) for row in grid]
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        _paint(out, color, min(r for r, c in cells), max(r for r, c in cells),
               min(c for r, c in cells), max(c for r, c in cells))
    return out


def _span_hull(grid):
    """Rival: fill all gaps between the outermost bars of an exact-span key."""
    out = [list(row) for row in grid]
    for (color, top, bottom), columns in _groups(grid).items():
        _paint(out, color, top, bottom, columns[0], columns[-1])
    return out


def _row_hull(grid):
    """Rival: bridge same-colored row endpoints, without object/span matching."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}):
            columns = [c for c, value in enumerate(row) if value == color]
            _paint(out, color, r, r, columns[0], columns[-1])
    return out


def _ignore_span(grid):
    """Rival: pair column-sorted bars by color, filling their joint row bounds."""
    out = [list(row) for row in grid]
    by_color = {}
    for color, top, bottom, column in _bars(grid)[0]:
        by_color.setdefault(color, []).append((column, top, bottom))
    for color, bars in by_color.items():
        bars.sort()
        for a, b in zip(bars[::2], bars[1::2]):
            _paint(out, color, min(a[1], b[1]), max(a[2], b[2]), a[0], b[0])
    return out


def _nearest_gap(grid):
    """Rival: greedily consume the closest remaining pair in each exact key."""
    out = [list(row) for row in grid]
    for (color, top, bottom), columns in _groups(grid).items():
        remaining = list(columns)
        while len(remaining) >= 2:
            i = min(range(len(remaining)-1), key=lambda j: (remaining[j+1]-remaining[j], remaining[j]))
            left, right = remaining[i:i+2]
            del remaining[i:i+2]
            _paint(out, color, top, bottom, left, right)
    return out


def _from_right(grid):
    """Rival: disjoint pairs from the right; differs on odd-sized keys."""
    out = [list(row) for row in grid]
    for (color, top, bottom), columns in _groups(grid).items():
        reverse = list(reversed(columns))
        for right, left in zip(reverse[::2], reverse[1::2]):
            _paint(out, color, top, bottom, left, right)
    return out


def _first_pair(grid):
    """Rival: handle only the first two bars of each exact-span key."""
    out = [list(row) for row in grid]
    for (color, top, bottom), columns in _groups(grid).items():
        if len(columns) >= 2:
            _paint(out, color, top, bottom, columns[0], columns[1])
    return out


def _reject_mixed_spans(grid):
    """Rival: discard an entire color if its eligible bars have unequal spans."""
    out = [list(row) for row in grid]
    groups = _groups(grid)
    span_counts = {}
    for color, top, bottom in groups:
        span_counts[color] = span_counts.get(color, 0) + 1
    for (color, top, bottom), columns in groups.items():
        if span_counts[color] == 1:
            for left, right in zip(columns[::2], columns[1::2]):
                _paint(out, color, top, bottom, left, right)
    return out


def _has_multiple_pairs(grid):
    return any(len(columns) >= 4 for columns in _groups(grid).values())


def _has_odd_key(grid):
    return any(len(columns) >= 3 and len(columns) % 2 == 1 for columns in _groups(grid).values())


def _has_closer_middle(grid):
    return any(len(cols) == 4 and cols[2]-cols[1] < min(cols[1]-cols[0], cols[3]-cols[2])
               for cols in _groups(grid).values())


def _has_mismatched_spans(grid):
    groups = _groups(grid)
    colors = {key[0] for key in groups}
    return any(sum(1 for key in groups if key[0] == color) >= 2
               and any(len(cols) >= 2 for key, cols in groups.items() if key[0] == color)
               and any(len(cols) % 2 for key, cols in groups.items() if key[0] == color)
               for color in colors)


SEMANTIC_RIVALS = {
    "per_color_bbox": _color_bbox, "per_span_hull": _span_hull,
    "rowwise_fill": _row_hull, "ignore_exact_span": _ignore_span,
    "nearest_gap_pairing": _nearest_gap, "pair_from_right": _from_right,
    "first_pair_only": _first_pair,
    "reject_color_with_mixed_spans": _reject_mixed_spans,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "multiple_same_key_pairs": _has_multiple_pairs,
    "separate_pairs_not_color_bbox": _has_multiple_pairs,
    "separate_pairs_not_row_hull": _has_multiple_pairs,
    "every_pair_is_filled": _has_multiple_pairs,
    "odd_trailing_bar": _has_odd_key,
    "closest_gap_is_not_a_pair": _has_closer_middle,
    "same_color_different_spans": _has_mismatched_spans,
    "valid_pair_with_unmatched_same_color_bar": _has_mismatched_spans,
}
WITNESS_RIVALS = {
    "multiple_same_key_pairs": "per_span_hull",
    "separate_pairs_not_color_bbox": "per_color_bbox",
    "separate_pairs_not_row_hull": "rowwise_fill",
    "every_pair_is_filled": "first_pair_only",
    "odd_trailing_bar": "pair_from_right",
    "closest_gap_is_not_a_pair": "nearest_gap_pairing",
    "same_color_different_spans": "ignore_exact_span",
    "valid_pair_with_unmatched_same_color_bar": "reject_color_with_mixed_spans",
}


def lesson_identifiable(demos, query):
    """Finite checks against declared rivals, using supplied Racket labels."""
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"{name} fits all demonstrations but changes the query")
    return errors
