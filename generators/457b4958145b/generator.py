"""Source-bound sampler for Radial Order Gallery.

The first row-major 9 cell is the anchor; all color-9 objects are excluded.
The selected Racket rule orders monochrome four-connected objects by bbox
centers, then concatenates color-sensitive padded FULL-GRID crops. This is
more specific than the historical prose description. Racket alone labels
examples; the Python predictions below are executable rival probes.
"""
from __future__ import annotations

from fractions import Fraction
from functools import cmp_to_key, lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "457b4958145b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4b56f7983d0d"
SUMMARY = (
    "First-9 anchored bbox-angle gallery with literal color-dependent padding. "
    "Four-demo lessons alternate a combined contrast scene and varied objects; "
    "repeated colors, multiple 9s and intentional padded-crop intrusion are supported."
)
INVARIANTS = [
    "rectangular integer-color grid with background 0 and at least one 9",
    "3..5 monochrome four-connected non-0/non-9 objects; colors may repeat",
    "all reference crops have height 3, preventing hconcat's shortest-crop truncation",
    "the lexicographically first 9 cell is the reference point; every 9 object is excluded",
    "padding may intentionally copy other cells, including a color-9 marker",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 10..16", "valid": "10..16"},
    "grid_w": {"type": "int", "default": "canonical-weighted 12..18", "valid": "12..18"},
    "n_components": {"type": "int", "default": "canonical-weighted 3..5", "valid": "3..5"},
    "palette_size": {"type": "int", "default": "3..7 total colors including 0 and 9", "valid": "3..7"},
    "n_distinct_colors": {"type": "int", "default": "exact alias of palette_size", "valid": "3..7"},
}
# Only the value-dependent exceptions below declare incompatibility. A broad
# axis-pair exemption could accidentally hide an unrelated pair failure.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("combined_contrast", "scattered")
MIN_STRICT_FRAC = 1.0

_RANGES = {"grid_h": (10, 16), "grid_w": (12, 18), "n_components": (3, 5),
           "palette_size": (3, 7), "n_distinct_colors": (3, 7)}
_PROFILES = ((12, 12, 4), (13, 13, 3), (12, 14, 4), (13, 14, 4))
_SHAPES = (
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule for ordinary production draws, before overrides."""
    return SCHEDULE_PROFILES[sample_index % 2]


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = axes
    raise error


def _objects(grid):
    result = []
    for obj in find_objects(grid, univalued=True, diagonal=False, bg=0):
        color = next(iter(obj))[0]
        cells = frozenset(point for _, point in obj)
        bbox = (min(r for r, _ in cells), min(c for _, c in cells),
                max(r for r, _ in cells), max(c for _, c in cells))
        result.append((color, cells, bbox))
    return sorted(result, key=lambda obj: min(obj[1]))


def _crop_bounds(grid, obj, hub, *, shape_special=False):
    color, cells, (r1, c1, r2, c2) = obj
    h, w = r2 - r1 + 1, c2 - c1 + 1
    dr, dc = r1 + r2 - 2 * hub[0], c1 + c2 - 2 * hub[1]
    if shape_special:
        row_counts = [sum(r == row for r, _ in cells) for row in range(r1, r2 + 1)]
        special = ((h == 3 and w == 3 and row_counts == [1, 3, 1]) or
                   (h == 2 and w == 3 and row_counts == [2, 2]))
    else:
        special = color == 6 or (color == 2 and h < 3 and w == 3)
    left = special or (w < 3 and (dc < 0 or dr > 0))
    return (r1, max(0, c1 - 1) if left else c1,
            min(len(grid) - 1, r2 + 1) if h < 3 else r2,
            min(len(grid[0]) - 1, c2 + 1) if not left and w < 3 else c2)


def _gallery_probe(grid, mode=None):
    """Python comparison model, NEVER a generator label authority.

    The no-mode mirror defines witness predicates, checked against Racket by
    the semantic gate and retained public-apply regression evidence.
    """
    components = _objects(grid)
    hub = min(point for color, cells, _ in components if color == 9 for point in cells)
    if mode == "isolated9":
        singletons = [min(cells) for color, cells, _ in components if color == 9 and len(cells) == 1]
        if singletons:
            hub = min(singletons)
    components = [obj for obj in components if obj[0] != 9]

    def vector(obj):
        _, cells, (r1, c1, r2, c2) = obj
        if mode == "centroid":
            return (2 * Fraction(sum(r for r, _ in cells), len(cells)) - 2 * hub[0],
                    2 * Fraction(sum(c for _, c in cells), len(cells)) - 2 * hub[1])
        return r1 + r2 - 2 * hub[0], c1 + c2 - 2 * hub[1]

    def compare(a, b):
        dra, dca = vector(a)
        drb, dcb = vector(b)
        if (dca >= 0) != (dcb >= 0):
            return -1 if dca >= 0 else 1
        cross = -dra * dcb + dca * drb
        if cross:
            return -1 if cross > 0 else 1
        return (a[2][:2] > b[2][:2]) - (a[2][:2] < b[2][:2])

    crops = []
    for obj in sorted(components, key=cmp_to_key(compare)):
        r1, c1, r2, c2 = _crop_bounds(grid, obj, hub, shape_special=mode == "shape_special")
        crop = [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]
        if mode == "object_only":
            crop = [[grid[r][c] if (r, c) in obj[1] else 0
                     for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]
        crops.append(crop)
    return [sum((crop[r] for crop in crops), []) for r in range(min(map(len, crops)))]


def rival_centroid(grid):
    return _gallery_probe(grid, "centroid")


def rival_isolated9(grid):
    return _gallery_probe(grid, "isolated9")


def rival_shape_special(grid):
    return _gallery_probe(grid, "shape_special")


def rival_object_only(grid):
    return _gallery_probe(grid, "object_only")


def _centroid_witness(grid):
    return _gallery_probe(grid) != rival_centroid(grid)


def _isolated9_witness(grid):
    return _gallery_probe(grid) != rival_isolated9(grid)


def _shape_special_witness(grid):
    return _gallery_probe(grid) != rival_shape_special(grid)


def _object_only_witness(grid):
    return _gallery_probe(grid) != rival_object_only(grid)


SEMANTIC_RIVALS = {
    "centroid": rival_centroid, "isolated9": rival_isolated9,
    "shape_special": rival_shape_special, "object_only": rival_object_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "centroid": _centroid_witness, "isolated9": _isolated9_witness,
    "shape_special": _shape_special_witness, "object_only": _object_only_witness,
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def observe_overrides(grid):
    palette = len({value for row in grid for value in row})
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_components": sum(obj[0] != 9 for obj in _objects(grid)),
            "palette_size": palette, "n_distinct_colors": palette}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions must not exceed 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be Python integer colors 0..9"]
    colors = {value for row in grid for value in row}
    if not {0, 9} <= colors:
        return ["expected background 0 and at least one color-9 anchor cell"]
    components = [obj for obj in _objects(grid) if obj[0] != 9]
    if not 3 <= len(components) <= 5:
        return [f"expected 3..5 non-9 components, got {len(components)}"]
    hub = min((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
    bounds = [_crop_bounds(grid, obj, hub) for obj in components]
    errors = []
    if any(r2 - r1 + 1 != 3 for r1, _, r2, _ in bounds):
        errors.append("each padded object crop must retain exactly three rows")
    if sum(c2 - c1 + 1 for _, c1, _, c2 in bounds) > 30:
        errors.append("gallery width exceeds 30 columns")
    return errors


def strict_canonical_like(grid):
    """Gallery domain, including lawful marker intrusion and repeated colors."""
    return self_check(grid)


def _weighted(ctx, name, low, high, anchor, weight=30, favored=()):
    options = tuple(range(low, high + 1)) + (anchor,) * weight
    options += tuple(value for value in favored if low <= value <= high)
    return ctx.draw_choice(name, options)


def _stamp(grid, color, origin, shape):
    r, c = origin
    for dr, dc in shape:
        if grid[r + dr][c + dc] != 0:
            raise RuntimeError("constructive placement collision")
        grid[r + dr][c + dc] = color


def _combined_contrast(ctx, h, w, n, palette):
    """A scene that distinguishes four canonical-fitting rivals together.

    A top L crosses the bbox/centroid angular seam. An early 9 cluster competes
    with a later singleton in the right object's pad. A color-6 2x3 rectangle
    distinguishes literal-color padding from the canonical shape shortcut.
    """
    rng = ctx.draw_rng("contrast_layout")
    row_offset, col_offset = rng.randrange(h - 9), rng.randrange(w - 10)
    g = full_grid(h, w, 0)
    others = [color for color in palette if color != 6]
    rng.shuffle(others)
    colors = [others[0], others[1], 6] + others[2:]
    colors += [colors[i % len(colors)] for i in range(n - len(colors))]
    placements = (
        ((0, 5), _SHAPES[9]),
        ((4, 9), _SHAPES[4]),
        ((7, 2), _SHAPES[11]),
        ((4, 1), _SHAPES[1]),
        ((0, 0), _SHAPES[3]),
    )
    for color, (origin, shape) in zip(colors, placements[:n]):
        _stamp(g, color, (origin[0] + row_offset, origin[1] + col_offset), shape)
    _stamp(g, 9, (5 + row_offset, 6 + col_offset), ((0, 0), (0, 1), (1, 0)))
    _stamp(g, 9, (5 + row_offset, 10 + col_offset), ((0, 0),))
    return g


@lru_cache(maxsize=49)
def _slot_choices(h, w):
    rows = tuple((a, b) for a, b in combinations(range(h - 2), 2) if b - a >= 4)
    cols = tuple((a, b, c) for a, b, c in combinations(range(w - 2), 3)
                 if b - a >= 4 and c - b >= 4)
    return rows, cols


def _scattered(ctx, h, w, n, palette):
    """Construct separated, variable shapes without rejection/fallback draws."""
    rng = ctx.draw_rng("scattered_layout")
    rows, cols = _slot_choices(h, w)
    selected_rows, selected_cols = rng.choice(rows), rng.choice(cols)
    slots = [(r, c) for r in selected_rows for c in selected_cols]
    rng.shuffle(slots)
    colors = list(palette) + [rng.choice(palette) for _ in range(n - len(palette))]
    rng.shuffle(colors)
    g = full_grid(h, w, 0)
    for origin, color in zip(slots, colors):
        shape = rng.choice(_SHAPES)
        if rng.randrange(2):
            max_c = max(c for _, c in shape)
            shape = tuple((r, max_c - c) for r, c in shape)
        _stamp(g, color, origin, shape)
    # Keep incidental 9s outside every possible padded crop; the contrast lane
    # introduces intrusion deliberately. Shapes already have one-cell gaps.
    blocked = set()
    for _, _, (r1, c1, r2, c2) in _objects(g):
        padded_bottom = r2 + (r2 - r1 + 1 < 3)
        blocked.update((r, c) for r in range(r1, padded_bottom + 1)
                       for c in range(max(0, c1 - 1), min(w, c2 + 2)))
    candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) not in blocked]
    if not candidates:
        raise RuntimeError("constructive slots left no lawful anchor position")
    for r, c in rng.sample(candidates, min(rng.choice((1, 1, 1, 2, 3, 4)), len(candidates))):
        g[r][c] = 9
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a Python integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _RANGES[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be a Python integer in [{lo}, {hi}]")
    p1, p2 = overrides.get("palette_size"), overrides.get("n_distinct_colors")
    if p1 is not None and p2 is not None and p1 != p2:
        _incompatible("conflicting palette_size and n_distinct_colors must agree",
                      "palette_size", "n_distinct_colors")
    requested_palette = p1 if p1 is not None else p2
    requested_n = overrides.get("n_components")
    if requested_palette is not None and requested_n is not None and requested_palette > requested_n + 2:
        palette_axis = "palette_size" if p1 is not None else "n_distinct_colors"
        _incompatible(f"{palette_axis} cannot exceed n_components + background and hub",
                      "n_components", palette_axis)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    ah, aw, an = _PROFILES[(sample_index // 2) % len(_PROFILES)]
    h = _weighted(ctx, "grid_h", 10, 16, ah)
    w = _weighted(ctx, "grid_w", 12, 18, aw)
    min_n = max(3, (requested_palette or 3) - 2)
    favored = (3,) * 8 if difficulty == "easy" else ((5,) * 8 if difficulty == "hard" else ())
    n = _weighted(ctx, "n_components", min_n, 5, max(min_n, an), favored=favored)
    contrast = sample_index % 2 == 0
    if requested_palette is not None:
        palette_size = ctx.draw_choice("palette_size", (requested_palette,))
    elif contrast:
        palette_size = ctx.draw_choice("palette_size", (n + 2,))
    else:
        palette_size = _weighted(ctx, "palette_size", 3, n + 2, n + 2, weight=5)
    ctx.draw_choice("n_distinct_colors", (palette_size,))
    rng = ctx.draw_rng("palette")
    if contrast and palette_size >= 5:
        palette = [6] + rng.sample([1, 2, 3, 4, 5, 7, 8], palette_size - 3)
        return _combined_contrast(ctx, h, w, n, palette)
    palette = rng.sample(list(range(1, 9)), palette_size - 2)
    return _scattered(ctx, h, w, n, palette)
