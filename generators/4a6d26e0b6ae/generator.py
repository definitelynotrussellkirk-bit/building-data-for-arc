"""Separated, distinct-color one-cell orthogonal bridge motifs.

Four real axes replace six inert legacy controls. Requested motif counts are
exact; geometry reserves the zero center AND a Chebyshev one-cell moat. Labels
remain exclusively the responsibility of the unchanged canonical Racket rule.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a6d26e0b6ae"
TASK_ID = "4a6d26e0b6ae"
VERSION = "3.0.0"
RULE_HASH = "980e1ed5540b"
SUMMARY = (
    "Zero-background grids containing distinct-color, axis-aligned (C,0,C) "
    "triples, separated by at least one zero cell in all directions. The "
    "unchanged rule fills each zero middle with C. Defaults mix canonical-scale "
    "scenes and difficulty-scaled scenes; overrides support dimensions 5..14 "
    "and 1..8 exact motifs subject to declared packing feasibility."
)
INVARIANTS = [
    "integer ARC colors 0..9 on a rectangular 5..14 by 5..14 grid",
    "each default nonzero color occurs exactly twice, at distance two on one axis",
    "every default pair has a zero center; all motif spans have a one-cell moat",
    "requested gap_count is exact, never silently truncated",
    "identity textures are explicit-only and validated separately",
]
HELPFUL_TEXTURES = ("default", "horizontal", "vertical", "edge")
DEGENERATE_TEXTURES = ("no_gaps", "gap_already_filled", "mismatched_endpoints")
AXES = {
    "grid_h": {"type": "int", "default": "canonical/difficulty mixture", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "canonical/difficulty mixture", "valid": "5..14"},
    "gap_count": {"type": "int", "default": "2..8 by difficulty and capacity", "valid": "1..8"},
    "texture": {"type": "str", "default": "rng helpful", "valid": "|".join(HELPFUL_TEXTURES)},
}
# Opt into strict classification. Only the precise failures below carry axes;
# no blanket tuple declaration can disguise an unrelated programming error.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


class IncompatibleOverrides(ValueError):
    """A requested combination exceeds this sampler's constructive domain."""

    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _integer(ctx, name, defaults, bounds):
    """Difficulty narrows random draws, never the valid explicit domain."""
    value = ctx.overrides.get(name)
    if value is not None and type(value) is not int:
        raise ValueError(f"{name} must be an integer, not {value!r}")
    lo, hi = bounds if value is not None else defaults
    return ctx.draw_int(name, lo, hi)


def _touches_edge(cells, h, w):
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)


@lru_cache(maxsize=200)
def _candidates(h, w, direction):
    """Immutable span/mask/moat records; cached values contain no random state."""
    candidates = []
    for vertical in (False, True):
        if direction == "horizontal" and vertical:
            continue
        if direction == "vertical" and not vertical:
            continue
        for r in range(h - 2 if vertical else h):
            for c in range(w if vertical else w - 2):
                cells = tuple((r + (k if vertical else 0), c + (0 if vertical else k)) for k in range(3))
                mask = sum(1 << (y * w + x) for y, x in cells)
                moat = 0
                for y, x in cells:
                    for yy in range(max(0, y - 1), min(h, y + 2)):
                        for xx in range(max(0, x - 1), min(w, x + 2)):
                            moat |= 1 << (yy * w + xx)
                candidates.append((cells, mask, moat))
    return tuple(candidates)


def _capacity(h, w, texture):
    horizontal = ((h + 1) // 2) * ((w + 1) // 4)
    vertical = ((w + 1) // 2) * ((h + 1) // 4)
    return horizontal if texture == "horizontal" else vertical if texture == "vertical" else max(horizontal, vertical)


def _lattice_fallback(h, w, count, texture, rng):
    """Guaranteed completion within _capacity, not a theorem of maximal packing.

    Try both directions and all offsets. A random reflection and slot subset
    retain variation when a crowded request defeats the free-position sampler.
    """
    layouts = []
    for vertical in (False, True):
        if texture == "horizontal" and vertical or texture == "vertical" and not vertical:
            continue
        row_step, col_step = (4, 2) if vertical else (2, 4)
        for r0 in range(row_step):
            for c0 in range(col_step):
                slots = [tuple((r + (k if vertical else 0), c + (0 if vertical else k)) for k in range(3))
                         for r in range(r0, h - 2 if vertical else h, row_step)
                         for c in range(c0, w if vertical else w - 2, col_step)]
                if len(slots) >= count and (texture != "edge" or any(_touches_edge(s, h, w) for s in slots)):
                    layouts.append(slots)
    if not layouts:
        # An internal error: caller validated constructive capacity already.
        raise RuntimeError("validated motif packing had no fallback")
    slots = list(rng.choice(layouts))
    chosen = []
    if texture == "edge":
        edge = rng.choice([s for s in slots if _touches_edge(s, h, w)])
        chosen.append(edge)
        slots.remove(edge)
    chosen.extend(rng.sample(slots, count - len(chosen)))
    flip_r, flip_c = rng.choice((False, True)), rng.choice((False, True))
    return [tuple((h - 1 - r if flip_r else r, w - 1 - c if flip_c else c) for r, c in span)
            for span in chosen]


def _place(h, w, count, texture, rng):
    """Free-position sampling with bounded effort and exact constructive fallback."""
    candidates = _candidates(h, w, texture if texture in ("horizontal", "vertical") else "default")
    for _ in range(8):
        order = list(candidates)
        rng.shuffle(order)
        if texture == "edge":
            # Stable partition: the first accepted motif must touch a boundary.
            order.sort(key=lambda item: not _touches_edge(item[0], h, w))
        chosen, reserved = [], 0
        for cells, mask, moat in order:
            if not (mask & reserved):
                chosen.append(cells)
                reserved |= moat
                if len(chosen) == count:
                    return chosen
    return _lattice_fallback(h, w, count, texture, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"colors"}
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(sorted(unknown))}; supported axes: {', '.join(AXES)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Keep canonical morphology in EACH difficulty band, not just pooled data.
    anchor = ctx.draw_choice("canonical_scale", (True, False))
    if anchor:
        hd, wd, nd = (7, 9), (8, 10), (3, 3)
    elif difficulty == "easy":
        hd, wd, nd = (7, 8), (8, 9), (2, 3)
    elif difficulty == "hard":
        hd, wd, nd = (9, 14), (10, 14), (4, 8)
    else:
        hd, wd, nd = (7, 10), (8, 12), (3, 5)
    h = _integer(ctx, "grid_h", hd, (5, 14))
    w = _integer(ctx, "grid_w", wd, (5, 14))
    choices = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") in DEGENERATE_TEXTURES else HELPFUL_TEXTURES
    texture = ctx.draw_choice("texture", choices)
    g = full_grid(h, w, 0)
    if texture == "no_gaps":
        conflicts = [k for k in ("gap_count", "colors") if overrides.get(k) is not None]
        if conflicts:
            raise IncompatibleOverrides("no_gaps cannot honor a nonzero motif count or explicit colors", ["texture", *conflicts])
        return g
    capacity = min(8, _capacity(h, w, texture))
    if texture == "mismatched_endpoints":
        capacity = min(capacity, 4)  # Two globally unique endpoint colors per motif.
    count = _integer(ctx, "gap_count", (min(nd[0], capacity), min(nd[1], capacity)), (1, 8))
    if count > capacity:
        axes = [k for k in ("grid_h", "grid_w", "gap_count", "texture") if overrides.get(k) is not None]
        raise IncompatibleOverrides(f"gap_count={count} exceeds supported separated packing capacity={capacity} for {h}x{w}, texture={texture}", axes)
    ncolors = 2 * count if texture == "mismatched_endpoints" else count
    if overrides.get("colors") is not None:
        colors = overrides["colors"]
        if not isinstance(colors, (tuple, list)) or any(type(c) is not int for c in colors):
            raise ValueError("colors must be a sequence of distinct integer ARC colors")
    colors = ctx.draw_distinct_colors("colors", n=ncolors, exclude={0})
    spans = _place(h, w, count, texture, ctx.draw_rng(f"layout:{difficulty}"))
    for i, cells in enumerate(spans):
        a, middle, b = cells
        color = colors[2 * i] if texture == "mismatched_endpoints" else colors[i]
        g[a[0]][a[1]] = color
        g[b[0]][b[1]] = colors[2 * i + 1] if texture == "mismatched_endpoints" else color
        if texture == "gap_already_filled":
            g[middle[0]][middle[1]] = color
    return g


def _points(grid):
    result = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                result[color].append((r, c))
    return result


def observe_overrides(grid):
    """Measure counts from pixels, never from requested/drawn metadata."""
    points = _points(grid)
    counts = [len(p) for p in points.values()]
    count = len(points) // 2 if counts and all(n == 1 for n in counts) else len(points)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "gap_count": count}


def _mismatched_spans(grid, points):
    """Find a complete separated pairing; at most eight singleton endpoints.

    Endpoint colors deliberately differ, so color grouping cannot recover the
    motifs. Extra candidate edges can occur across the blank cell between two
    valid motifs. Accept a full geometric pairing, not a greedy or degree test.
    This validator does not consult the sampler's masks, candidates or RNG.
    """
    locations = tuple(sorted(cells[0] for cells in points.values()))

    def pair(remaining, spans):
        if not remaining:
            return spans
        a = remaining[0]
        for i, b in enumerate(remaining[1:], 1):
            if not (a[0] == b[0] or a[1] == b[1]) or abs(a[0]-b[0]) + abs(a[1]-b[1]) != 2:
                continue
            middle = ((a[0]+b[0])//2, (a[1]+b[1])//2)
            if grid[middle[0]][middle[1]] != 0:
                continue
            span = (a, middle, b)
            if any(max(abs(r-y), abs(c-x)) <= 1 for other in spans for r, c in span for y, x in other):
                continue
            result = pair(remaining[1:i] + remaining[i+1:], spans + [span])
            if result is not None:
                return result
        return None

    return pair(locations, [])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the whole declared domain, including explicit negative fixtures.

    VERSION still keys sampler 3.0.0: this validator-only revision intentionally
    leaves seed-to-input behavior unchanged. Full source hashes bind the checks.
    """
    if not isinstance(grid, (list, tuple)) or not grid or not all(isinstance(row, (list, tuple)) for row in grid):
        return ["empty or malformed grid"]
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 14 or not 5 <= w <= 14 or any(len(row) != w for row in grid):
        return ["grid must be rectangular with dimensions 5..14"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid cells must be integer ARC colors 0..9"]
    if meta is None:
        meta = {}
    if not isinstance(meta, dict) or not isinstance(meta.get("overrides", {}), dict):
        return ["metadata and nested overrides must be dictionaries"]
    requested = {**meta.get("overrides", {}), **meta}
    texture = requested.get("texture")
    if texture is None:
        texture = "default"
    if texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        return [f"unsupported texture: {texture!r}"]
    points = _points(grid)
    problems, spans = [], []
    # Shared metadata checks must run even for a blank explicit negative.
    observed = observe_overrides(grid)
    for axis in ("gap_count", "grid_h", "grid_w"):
        value = requested.get(axis)
        if value is not None and (type(value) is not int or observed[axis] != value):
            problems.append(f"{axis}: expected {value!r}, observed {observed[axis]}")
    colors = requested.get("colors")
    if colors is not None:
        if (not isinstance(colors, (list, tuple))
                or any(type(c) is not int or not 1 <= c <= 9 for c in colors)
                or len(set(colors)) != len(colors)):
            problems.append("colors must be distinct nonzero integer ARC colors")
        elif set(colors) != set(points):
            problems.append(f"colors: expected {sorted(colors)}, observed {sorted(points)}")
    if texture == "no_gaps":
        if points:
            problems.append("no_gaps must be blank")
        if requested.get("gap_count") is not None or colors is not None:
            problems.append("no_gaps cannot honor an explicit motif count or colors")
        return problems
    if not points:
        return problems + ["missing motifs"]
    if texture == "mismatched_endpoints":
        if not 2 <= len(points) <= 8 or len(points) % 2 or any(len(p) != 1 for p in points.values()):
            problems.append("mismatched endpoints require one to four globally unique color pairs")
        elif _mismatched_spans(grid, points) is None:
            problems.append("mismatched endpoints cannot form complete separated one-cell-gap motifs")
    else:
        if not 1 <= len(points) <= 8:
            problems.append("ordinary and filled scenes require one to eight motifs")
        for color, cells in points.items():
            expected = 3 if texture == "gap_already_filled" else 2
            if len(cells) != expected:
                problems.append(f"color {color}: expected {expected} cells, got {len(cells)}")
                continue
            a, b = cells[0], cells[-1]
            if not (a[0] == b[0] or a[1] == b[1]) or abs(a[0]-b[0]) + abs(a[1]-b[1]) != 2:
                problems.append(f"color {color}: endpoints must be axis-aligned at distance two")
                continue
            middle = ((a[0]+b[0])//2, (a[1]+b[1])//2)
            if grid[middle[0]][middle[1]] != (color if texture == "gap_already_filled" else 0):
                problems.append(f"color {color}: center is not the required {'same color' if expected == 3 else 'zero'}")
                continue
            span = (a, middle, b)
            if any(max(abs(r-y), abs(c-x)) <= 1 for other in spans for r, c in span for y, x in other):
                problems.append(f"color {color}: motif violates the one-cell moat")
            spans.append(span)
        if texture == "horizontal" and any(len({r for r, _ in s}) != 1 for s in spans):
            problems.append("horizontal texture contains a vertical motif")
        if texture == "vertical" and any(len({c for _, c in s}) != 1 for s in spans):
            problems.append("vertical texture contains a horizontal motif")
        if texture == "edge" and not any(_touches_edge(s, h, w) for s in spans):
            problems.append("edge texture lacks a boundary motif")
    return problems


def strict_canonical_like(grid):
    """The same non-vacuous structural contract, without explicit degenerates."""
    return self_check(grid)
