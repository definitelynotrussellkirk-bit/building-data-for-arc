"""Sample four-pixel tiles for the unchanged center-out Racket ring rule.

Each row-major 2x2 tile supplies the four quadrants of a concentric ring;
the first tile is innermost. Zero is data. This module generates INPUTS only.
The renderers below are explicit rival hypotheses, never label authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "84def340ce03"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e27cc4c77443"
SUMMARY = (
    "Read arbitrary 2x2 tiles in row-major order, from the innermost ring "
    "outward. Each tile's four pixels independently color the corresponding "
    "ring quadrants. Output side is h*w/2, at most 30. Zero is an ordinary "
    "color. A three-draw curriculum interleaves canonical profiles, repeated/"
    "uniform-tile counterexamples at noncanonical shapes, and broader inputs."
)
INVARIANTS = [
    "nonempty rectangular integer grids with even dimensions in 2..30",
    "h*w <= 60, so the reference output side h*w/2 is at most 30",
    "every cell is a plain integer color in 0..9; zero is not background",
    "2x2 tiles may be heterogeneous, identical, adjacent repeats or uniform",
    "requested dimensions, palette cardinality and zero presence are exact",
]
EVEN_SIZES = tuple(range(2, 31, 2))
CANONICAL_PROFILES = ((4, 4, 10), (4, 6, 8), (6, 4, 9))
HELPFUL_TEXTURES = (
    "independent", "repeat_tiles", "mixed_uniform", "contrast", "uniform_blocks",
)
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "curriculum; even 2..30",
               "valid": "2|4|6|8|10|12|14|16|18|20|22|24|26|28|30"},
    "grid_w": {"type": "int", "default": "curriculum; even 2..30",
               "valid": "2|4|6|8|10|12|14|16|18|20|22|24|26|28|30"},
    "palette_size": {"type": "int", "default": "4..10 when feasible; canonical anchors",
                     "valid": "1..10"},
    "include_zero": {"type": "bool", "default": "true for canonical; otherwise keyed choice",
                     "valid": "true|false"},
    "texture": {"type": "str", "default": "canonical/contrast/broad curriculum",
                "valid": "|".join(HELPFUL_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("grid_h", "grid_w"), ("grid_h", "palette_size"),
    ("grid_w", "palette_size"), ("texture", "grid_h"),
    ("texture", "grid_w"), ("texture", "palette_size"),
    ("palette_size", "include_zero"),
]
SCHEDULE_PROFILES = ("canonical", "contrast", "broad")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.60


def schedule_profile(seed, sample_index, difficulty=None):
    """Any three consecutive unoverridden draws contain all three profiles."""
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _incompatible(overrides, reason):
    error = ValueError(reason)
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


def _capacity(h, w, texture):
    """Number of independent color groups after the mode's equalities."""
    n = h * w // 4
    if texture == "repeat_tiles":
        return 4 * n - 4 if n >= 2 else 0
    if texture == "mixed_uniform":
        return 4 * n - 3 if n >= 2 else 0
    if texture == "contrast":
        return 4 * n - 7 if n >= 3 else 0
    if texture == "uniform_blocks":
        return n if n >= 2 else 0
    return 4 * n


def _feasible_shapes(overrides, texture):
    minimum = 1 if texture == "independent" else 2
    requested = overrides.get("palette_size", minimum)
    if requested < minimum:
        return []
    color_limit = 9 if overrides.get("include_zero") is False else 10
    if requested > color_limit:
        return []
    return [
        (h, w) for h in EVEN_SIZES for w in EVEN_SIZES
        if h * w <= 60
        and ("grid_h" not in overrides or h == overrides["grid_h"])
        and ("grid_w" not in overrides or w == overrides["grid_w"])
        and requested <= _capacity(h, w, texture)
    ]


def _color_groups(h, w, texture, palette, rng):
    n = h * w // 4
    tiles = [[4 * i + q for q in range(4)] for i in range(n)]
    mixed_tile = rng.randrange(n)
    if texture in ("repeat_tiles", "contrast"):
        # Adjacent equality tests run-compression as well as global dedup.
        first = rng.randrange(n - 1)
        tiles[first + 1] = list(tiles[first])
        mixed_tile = first
    if texture in ("mixed_uniform", "contrast"):
        available = [i for i in range(n) if i != mixed_tile]
        if texture == "contrast":
            available.remove(mixed_tile + 1)
        uniform = rng.choice(available)
        tiles[uniform] = [tiles[uniform][0]] * 4
    if texture == "uniform_blocks":
        tiles = [[4 * i] * 4 for i in range(n)]

    groups = sorted({group for tile in tiles for group in tile})
    rng.shuffle(groups)
    # Every requested color is placed before additional group colors are drawn.
    colors = dict(zip(groups, palette))
    for group in groups[len(palette):]:
        colors[group] = rng.choice(palette)
    if texture != "uniform_blocks" and len(palette) > 1:
        designated = tiles[mixed_tile]
        if len({colors[group] for group in designated}) == 1:
            # Four distinct groups held the old color, so changing one cannot
            # erase it from the exact palette. No rejection or count clipping.
            old = colors[designated[0]]
            colors[designated[1]] = rng.choice([c for c in palette if c != old])
    result = [[0] * w for _ in range(h)]
    for i, tile in enumerate(tiles):
        br, bc = divmod(i, w // 2)
        for q, group in enumerate(tile):
            dr, dc = divmod(q, 2)
            result[2 * br + dr][2 * bc + dc] = colors[group]
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Draw one input; a known override set to None is unset, as in GenCtx."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer and sample_index a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    supplied = {name: value for name, value in overrides.items() if value is not None}
    for name, value in supplied.items():
        if name in ("grid_h", "grid_w"):
            if type(value) is not int or value not in EVEN_SIZES:
                raise ValueError(f"{name} must be an even integer in 2..30")
        elif name == "palette_size":
            if type(value) is not int or not 1 <= value <= 10:
                raise ValueError("palette_size must be an integer in 1..10")
        elif name == "include_zero":
            if type(value) is not bool:
                raise ValueError("include_zero must be a boolean")
        elif type(value) is not str or value not in HELPFUL_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=supplied)
    profile = schedule_profile(seed, sample_index, difficulty)
    feasible = {name: _feasible_shapes(supplied, name) for name in HELPFUL_TEXTURES}
    options = [name for name in HELPFUL_TEXTURES if feasible[name]]
    if not options or ("texture" in supplied and not feasible[supplied["texture"]]):
        _incompatible(supplied, "dimensions, texture, palette size and zero presence are incompatible")
    preferred = {
        "canonical": ["independent"],
        "contrast": ["contrast"],
        "broad": ["independent", "repeat_tiles", "mixed_uniform", "uniform_blocks"],
    }[profile]
    choices = options if "texture" in supplied else ([t for t in preferred if t in options] or options)
    texture = ctx.draw_choice("texture", choices)
    shapes = feasible[texture]
    # Explicit controls replace curriculum preferences, without silent clipping.
    if not supplied and profile == "canonical":
        shapes = [(h, w) for h, w, _ in CANONICAL_PROFILES]
    elif not supplied and profile == "contrast":
        # These shapes also refute a conservative longest-side rival that
        # merely truncates the tile list instead of inventing missing tiles.
        shapes = [(h, w) for h, w in shapes if min(h, w) > 4]
    if profile == "broad":
        favored = [(h, w) for h, w in shapes
                   if (h * w <= 24 if difficulty == "easy" else
                       h * w >= 32 if difficulty == "hard" else 16 <= h * w <= 36)]
        shapes = shapes + favored * 2
    target_h, target_w = ctx.draw_choice("shape_plan", shapes)
    h = ctx.draw_choice("grid_h", (target_h,))
    w = ctx.draw_choice("grid_w", (target_w,))
    maximum = min(10, _capacity(h, w, texture),
                  9 if supplied.get("include_zero") is False else 10)
    minimum = 1 if texture == "independent" else 2
    palette_options = list(range(minimum, maximum + 1))
    if "palette_size" not in supplied:
        if not supplied and profile == "canonical":
            palette_options = [p for ch, cw, p in CANONICAL_PROFILES if (ch, cw) == (h, w)]
        else:
            palette_options = list(range(min(4, maximum), maximum + 1))
    size = ctx.draw_choice("palette_size", palette_options)
    zero_options = [True] if size == 10 or (not supplied and profile == "canonical") else [True, False]
    include_zero = ctx.draw_choice("include_zero", zero_options)
    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(list(range(1, 10)), size - int(include_zero))
    if include_zero:
        palette.append(0)
    palette_rng.shuffle(palette)
    return _color_groups(h, w, texture, palette, ctx.draw_rng("cell_groups"))


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the rule's full bounded domain, not a color/texture heuristic."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty row sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid or non-sequence row"]
    h = len(grid)
    if h not in EVEN_SIZES or w not in EVEN_SIZES:
        return ["dimensions must be even integers in 2..30"]
    if h * w > 60:
        return ["reference output side h*w/2 would exceed 30"]
    if any(type(c) is not int or not 0 <= c <= 9 for row in grid for c in row):
        return ["pixels must be plain integer colors in 0..9"]
    return []


def observe_overrides(grid):
    colors = {c for row in grid for c in row}
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "palette_size": len(colors), "include_zero": 0 in colors}


def _tiles(grid):
    return [tuple(grid[r + dr][c + dc] for dr in (0, 1) for dc in (0, 1))
            for r in range(0, len(grid), 2) for c in range(0, len(grid[0]), 2)]


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    tiles = _tiles(grid)
    if len(tiles) < 2:
        return ["one tile is a lawful identity edge case, not a nesting lesson"]
    if not any(len(set(tile)) > 1 for tile in tiles):
        return ["uniform tiles are lawful but do not teach four-pixel quadrant routing"]
    return []


def mutation_fixtures():
    return [("odd_height", [[0, 1], [2, 3], [4, 5]]),
            ("odd_width", [[0, 1, 2], [3, 4, 5]]),
            ("output_overflow", [[0] * 8 for _ in range(8)]),
            ("invalid_color", [[0, 1], [2, 10]]),
            ("boolean_color", [[0, 1], [2, True]])]


def _render_rival_tiles(tiles):
    """Shared geometry of deliberately rival hypotheses; not a label API."""
    if not tiles:
        return [[0]]
    n = len(tiles) * 2
    result = []
    for r in range(n):
        row = []
        for c in range(n):
            layer = min(r, c, n - 1 - r, n - 1 - c)
            quadrant = 2 * int(r >= n // 2) + int(c >= n // 2)
            row.append(tiles[len(tiles) - 1 - layer][quadrant])
        result.append(row)
    return result


def _max_dimension_rival(grid):
    """Wrongly cap the tile sequence at the longest input side."""
    tiles = _tiles(grid)
    count = max(len(grid), len(grid[0]))
    return _render_rival_tiles(tiles[:count])


def _deduplicate_rival(grid):
    return _render_rival_tiles(list(dict.fromkeys(_tiles(grid))))


def _compress_runs_rival(grid):
    kept = []
    for tile in _tiles(grid):
        if not kept or tile != kept[-1]:
            kept.append(tile)
    return _render_rival_tiles(kept)


def _skip_uniform_rival(grid):
    return _render_rival_tiles([tile for tile in _tiles(grid) if len(set(tile)) > 1])


def _top_left_only_rival(grid):
    return _render_rival_tiles([(tile[0],) * 4 for tile in _tiles(grid)])


def _outside_in_rival(grid):
    return _render_rival_tiles(list(reversed(_tiles(grid))))


CANONICAL_SHORTCUTS = {
    "max_dimension": _max_dimension_rival,
    "deduplicate_tiles": _deduplicate_rival,
    "compress_adjacent_tiles": _compress_runs_rival,
    "skip_uniform_tiles": _skip_uniform_rival,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS,
                       top_left_only=_top_left_only_rival,
                       outside_in=_outside_in_rival)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "more_tiles_than_long_side": lambda g: len(g) * len(g[0]) // 4 > max(len(g), len(g[0])),
    "repeated_tiles": lambda g: len(set(_tiles(g))) < len(_tiles(g)),
    "adjacent_repeat": lambda g: any(a == b for a, b in zip(_tiles(g), _tiles(g)[1:])),
    "uniform_tile": lambda g: any(len(set(tile)) == 1 for tile in _tiles(g)),
    "heterogeneous_tile": lambda g: any(len(set(tile)) > 1 for tile in _tiles(g)),
    "order_sensitive": lambda g: _tiles(g) != list(reversed(_tiles(g))),
}
WITNESS_RIVALS = {
    "more_tiles_than_long_side": ["max_dimension"],
    "repeated_tiles": ["deduplicate_tiles"],
    "adjacent_repeat": ["compress_adjacent_tiles"],
    "uniform_tile": ["skip_uniform_tiles"],
    "heterogeneous_tile": ["top_left_only"],
    "order_sensitive": ["outside_in"],
}
