"""Inputs for odd-area, same-color FOUR-connected object filtering.

The unchanged canonical Racket rule supplies labels. Default lessons alternate
fresh canonical-scale scenes and richer component-identity witnesses. Every
three consecutive default draws include a witness; every four include two.
Exact overrides produce lawful research scenes, without that lesson guarantee.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ceef568b1cd4"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "8abfb7183f00"
SUMMARY = (
    "Preserve odd-area same-color 4-connected components; erase even-area "
    "components on background 0. Inputs include singletons, areas 1..9, "
    "repeated colors, same-color diagonal contact and cross-color edge contact."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular 7..20 by 7..20 integer-color canvas with background 0",
    "2..6 same-color 4-connected objects, each with 1..9 cells, in 1..6 nonzero colors",
    "at least one odd and one even object; repeated colors remain separate objects",
    "default lessons alternate canonical-scale scenes and rich rival counterexamples",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profile or 7..20", "valid": "7..20"},
    "grid_w": {"type": "int", "default": "canonical profile or 7..20", "valid": "7..20"},
    "n": {"type": "int", "default": "3..5; witness scenes use 5", "valid": "2..6"},
    "n_distinct_colors": {"type": "int", "default": "3..4; witness scenes use 3", "valid": "1..6"},
}
# Only impossible color-count/object-count pairs are incompatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n": n, "n_distinct_colors": colors}
    for n in range(2, 7) for colors in range(n + 1, 7)
]
SCHEDULE_PROFILES = ("canonical_scale", "component_identity")
MIN_STRICT_FRAC = 0.4
_CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CANONICAL_PROFILES = ((7, 8, 4), (8, 8, 3), (7, 7, 3), (8, 9, 4))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _components(grid, *, diagonal=False, colorblind=False):
    """Extract components from pixels; placement records are never authority."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    steps = _CARDINAL + _DIAGONAL if diagonal else _CARDINAL
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for y, x in cells:
                for dy, dx in steps:
                    point = y + dy, x + dx
                    ny, nx = point
                    if (0 <= ny < h and 0 <= nx < w and point not in seen
                            and grid[ny][nx] != 0
                            and (colorblind or grid[ny][nx] == color)):
                        seen.add(point)
                        cells.append(point)
            result.append((color, tuple(cells)))
    return result


def observe_overrides(grid):
    components = _components(grid)
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n": len(components),
        "n_distinct_colors": len({color for color, _ in components}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9, not booleans"]
    errors = []
    if not (7 <= h <= 20 and 7 <= w <= 20):
        errors.append("canvas dimensions must each be 7..20")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background 0 must be present")
    components = _components(grid)
    if not 2 <= len(components) <= 6:
        errors.append("expected 2..6 same-color 4-connected objects")
    colors = {color for color, _ in components}
    if not 1 <= len(colors) <= 6:
        errors.append("expected 1..6 nonzero colors")
    sizes = [len(cells) for _, cells in components]
    if any(not 1 <= size <= 9 for size in sizes):
        errors.append("object areas must be 1..9")
    if not any(size % 2 for size in sizes) or not any(size % 2 == 0 for size in sizes):
        errors.append("a teaching scene needs both odd and even objects")
    return errors


def strict_canonical_like(grid):
    """Original-scale, distinct-color small-object family; rich witnesses are broader."""
    errors = self_check(grid)
    if errors:
        return errors
    components = _components(grid)
    if not (7 <= len(grid) <= 8 and 7 <= len(grid[0]) <= 9):
        errors.append("outside canonical dimension envelope")
    if not 3 <= len(components) <= 4:
        errors.append("canonical family has 3..4 objects")
    if len({color for color, _ in components}) != len(components):
        errors.append("canonical family has one distinct color per object")
    if any(len(cells) > 4 for _, cells in components):
        errors.append("canonical object areas are 1..4")
    return errors


def _axis(ctx, name, lo, hi, preferred):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # This is an honest scheduled default, not a clipped random draw. All legal
    # exact values use the same explicit bounds above and are observed in pixels.
    return ctx.draw_choice(name, (preferred,))


def _grow(rng, size, height, width, start=None):
    start = start if start is not None else (rng.randrange(height), rng.randrange(width))
    cells = {start}
    frontier = set()
    while len(cells) < size:
        for r, c in sorted(cells):
            for dr, dc in _CARDINAL:
                point = r + dr, c + dc
                if (0 <= point[0] < height and 0 <= point[1] < width
                        and point not in cells):
                    frontier.add(point)
        point = rng.choice(sorted(frontier))
        cells.add(point)
        frontier.remove(point)
    return sorted(cells)


def _normalized(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def _put(grid, cells, color):
    for r, c in cells:
        grid[r][c] = color


def _place(grid, shape, color, rng, *, anchor=(), contact=None):
    shape = _normalized(shape)
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if contact is None:
        origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    else:
        steps = _DIAGONAL if contact == "diagonal" else _CARDINAL
        origins = sorted({(ar + dr - r, ac + dc - c)
                          for ar, ac in anchor for dr, dc in steps for r, c in shape
                          if 0 <= ar + dr - r <= h - sh
                          and 0 <= ac + dc - c <= w - sw})
    rng.shuffle(origins)
    for r0, c0 in origins:
        cells = [(r + r0, c + c0) for r, c in shape]
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == color
               for r, c in cells for dr, dc in _CARDINAL):
            continue
        _put(grid, cells, color)
        return cells
    return None


def _draw_witness(ctx, h, w):
    """Five objects refute color/connectivity shortcuts AND their odd-area gates."""
    rng = ctx.draw_rng("witness_geometry")
    colors = ctx.draw_rng("witness_colors").sample(range(1, 10), 3)
    sizes = (rng.choice((7, 9)), rng.choice((6, 8)), rng.choice((1, 3, 5)),
             rng.choice((2, 4)), rng.choice((1, 3, 5)))
    for _ in range(24):
        grid = full_grid(h, w, 0)
        a = _place(grid, _grow(rng, sizes[0], 3, 3), colors[0], rng)
        b = _place(grid, _grow(rng, sizes[1], 3, 3), colors[0], rng,
                   anchor=a, contact="diagonal")
        if b is None:
            continue
        c = _place(grid, _grow(rng, sizes[2], 3, 3), colors[1], rng,
                   anchor=b, contact="edge")
        if c is None:
            continue
        e = _place(grid, _grow(rng, sizes[4], 3, 3), colors[1], rng,
                   anchor=c, contact="diagonal")
        if e is None:
            continue
        d = _place(grid, _grow(rng, sizes[3], 3, 3), colors[2], rng)
        if d is not None:
            return grid

    # Total constructive fallback, with the SAME counts and rival witnesses.
    # Random connected shapes, an arbitrary D4 orientation, and translation
    # avoid replaying a fixed grid. No components or requested axes are dropped.
    block = full_grid(7, 7, 0)
    a = _grow(rng, sizes[0], 3, 3, (2, 2))
    b = [(r + 3, c + 3) for r, c in _grow(rng, sizes[1], 3, 3, (0, 0))]
    c = [(r, c + 3) for r, c in _grow(rng, sizes[2], 3, 3, (2, 0))]
    e = [(r + 3, c) for r, c in _grow(rng, sizes[4], 3, 3, (0, 2))]
    d = [(6, col) for col in range(sizes[3])]
    for cells, color in zip((a, b, c, d, e),
                           (colors[0], colors[0], colors[1], colors[2], colors[1])):
        _put(block, cells, color)
    if rng.randrange(2):
        block = [row[::-1] for row in block]
    for _ in range(rng.randrange(4)):
        block = [list(row) for row in zip(*block[::-1])]
    grid = full_grid(h, w, 0)
    r0, c0 = rng.randrange(h - 6), rng.randrange(w - 6)
    for r, row in enumerate(block):
        for c, value in enumerate(row):
            grid[r0 + r][c0 + c] = value
    return grid


def _partition(length, count, rng):
    widths = [1] * count
    for _ in range(length - (count - 1) - count):
        widths[rng.randrange(count)] += 1
    result = []
    start = 0
    for width in widths:
        result.append((start, width))
        start += width + 1
    return result


def _draw_separated(ctx, h, w, n, color_count, *, canonical_scale):
    """Construct every legal joint override, including the 7x7 / six-object corner."""
    rng = ctx.draw_rng("separated_geometry")
    if canonical_scale:
        # Canonical scenes need not have a full blank row/column separating the
        # objects. Try free placement first; rooms below are a total fallback.
        loose = ctx.draw_rng("canonical_scattered_geometry")
        palette = ctx.draw_rng("canonical_scattered_colors").sample(range(1, 10), color_count)
        colors = palette + [loose.choice(palette) for _ in range(n - color_count)]
        loose.shuffle(colors)
        for _ in range(12):
            grid = full_grid(h, w, 0)
            sizes = [loose.choice((2, 4)), loose.choice((1, 3))]
            sizes += [loose.randrange(1, 5) for _ in range(n - 2)]
            if all(_place(grid, _grow(loose, size, 4, 4), color, loose) is not None
                   for size, color in zip(sizes, colors)):
                return grid
    tilings = {(rows, (n + rows - 1) // rows) for rows in range(1, n + 1)}
    tilings = sorted((rows, cols) for rows, cols in tilings
                     if h >= 2 * rows - 1 and w >= 2 * cols - 1)
    # Prefer roomy cells but retain both orientations when equally good.
    best = max(((h - r + 1) // r) * ((w - c + 1) // c) for r, c in tilings)
    choices = [(r, c) for r, c in tilings
               if ((h - r + 1) // r) * ((w - c + 1) // c) == best]
    rows, cols = rng.choice(choices)
    heights = _partition(h, rows, rng)
    widths = _partition(w, cols, rng)
    rooms = [(r, c, rh, cw) for r, rh in heights for c, cw in widths]
    rng.shuffle(rooms)
    # At least one chosen room must fit an even object.
    even_room = next(room for room in rooms if room[2] * room[3] >= 2)
    rooms.remove(even_room)
    rooms = [even_room] + rooms[:n - 1]
    palette = ctx.draw_rng("separated_colors").sample(range(1, 10), color_count)
    colors = palette + [rng.choice(palette) for _ in range(n - color_count)]
    rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for i, ((r0, c0, rh, cw), color) in enumerate(zip(rooms, colors)):
        cap = min(4 if canonical_scale else 9, rh * cw)
        sizes = list(range(1, cap + 1))
        if i == 0:
            sizes = [size for size in sizes if size % 2 == 0]
        elif i == 1:
            sizes = [size for size in sizes if size % 2]
        size = rng.choice(sizes)
        shape = _normalized(_grow(rng, size, rh, cw))
        sh, sw = max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1
        dr, dc = rng.randrange(rh - sh + 1), rng.randrange(cw - sw + 1)
        _put(grid, [(r0 + dr + r, c0 + dc + c) for r, c in shape], color)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or removed override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_scale"
    ph, pw, pn = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    if not core:
        favored = range(7, 11) if difficulty == "easy" else (
            range(11, 17) if difficulty == "hard" else range(8, 14))
        dimensions = tuple(range(7, 21)) + tuple(favored) * 3
        ph = ctx.draw_rng("broad_height").choice(dimensions)
        pw = ctx.draw_rng("broad_width").choice(dimensions)
        pn = 5
    h = _axis(ctx, "grid_h", 7, 20, ph)
    w = _axis(ctx, "grid_w", 7, 20, pw)
    color_override = overrides.get("n_distinct_colors")
    default_n = max(pn, color_override) if color_override is not None else pn
    n = _axis(ctx, "n", 2, 6, default_n)
    colors = _axis(ctx, "n_distinct_colors", 1, 6, n if core else min(3, n))
    if colors > n:
        raise ValueError("incompatible n and n_distinct_colors: more colors than objects")
    if not core and n == 5 and colors == 3:
        return _draw_witness(ctx, h, w)
    return _draw_separated(ctx, h, w, n, colors, canonical_scale=core)


def _area_prediction(grid, *, diagonal=False, colorblind=False, sizes=None, erase=None):
    output = full_grid(len(grid), len(grid[0]), 0)
    for _, cells in _components(grid, diagonal=diagonal, colorblind=colorblind):
        area = len(cells)
        keep = area % 2 == 1 if sizes is None and erase is None else (
            area in sizes if sizes is not None else area not in erase)
        if keep:
            for r, c in cells:
                output[r][c] = grid[r][c]
    return output


def _global_color_parity(grid):
    counts = Counter(value for row in grid for value in row if value)
    return [[value if value and counts[value] % 2 else 0 for value in row] for row in grid]


def _diagonal_component_parity(grid):
    return _area_prediction(grid, diagonal=True)


def _colorblind_component_parity(grid):
    return _area_prediction(grid, colorblind=True)


def _observed_odd_sizes_only(grid):
    return _area_prediction(grid, sizes={1, 3, 5})


def _observed_even_sizes_only(grid):
    return _area_prediction(grid, erase={2, 4})


def _odd_area_gate(grid, gate):
    output = _area_prediction(grid)
    return [[value if gate[r][c] == value else 0 for c, value in enumerate(row)]
            for r, row in enumerate(output)]


def _odd_area_and_odd_color_total(grid):
    return _odd_area_gate(grid, _global_color_parity(grid))


def _odd_area_and_odd_diagonal_total(grid):
    return _odd_area_gate(grid, _diagonal_component_parity(grid))


SEMANTIC_RIVALS = {
    "global_color_parity": _global_color_parity,
    "diagonal_component_parity": _diagonal_component_parity,
    "colorblind_component_parity": _colorblind_component_parity,
    "observed_odd_sizes_only": _observed_odd_sizes_only,
    "observed_even_sizes_only": _observed_even_sizes_only,
    "odd_area_and_odd_color_total": _odd_area_and_odd_color_total,
    "odd_area_and_odd_diagonal_total": _odd_area_and_odd_diagonal_total,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _counterexample(name):
    def check(grid):
        return SEMANTIC_RIVALS[name](grid) != _area_prediction(grid)
    return check


SEMANTIC_WITNESSES = {name: _counterexample(name) for name in SEMANTIC_RIVALS}
SEMANTIC_WITNESSES["singleton"] = lambda grid: any(len(cells) == 1 for _, cells in _components(grid))
BRANCH_WITNESSES = ("singleton",)
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite, declared-rival test; no claim of universal identifiability."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
