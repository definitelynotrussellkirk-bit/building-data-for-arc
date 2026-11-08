"""Border-object erasure inputs; labels remain the selected Racket authority.

Objects are monochromatic FOUR-connected components on a fixed zero background.
Ordinary four-demonstration lessons rotate opposing-edge witness pairs and
include repeated colors, diagonal contacts, differently colored contacts, and
more than two erased objects. Explicit count controls may request simpler grids.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "9b37d4bbfb7e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b41941e8090e"
SUMMARY = (
    "Erase each same-color 4-connected object touching any outer border; keep "
    "every fully interior object. Zero is the background. Shapes, edge positions, "
    "dimensions and colors vary, including one color in both erased and surviving "
    "objects, diagonal-only same-color contacts and cardinal different-color contacts."
)
INVARIANTS = [
    "rectangular integer-color grid, height 6..12 and width 7..14, with background 0",
    "2..6 same-color four-connected objects and 2..6 used nonzero colors",
    "at least one border object and at least one wholly interior object",
    "counts describe rendered components and used colors, never attempted placements",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
AXES = {
    "grid_h": {"type": "int", "default": "6..12, weighted toward canonical 7/8", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "7..14, weighted toward canonical 7/8/9", "valid": "7..14"},
    "n_blobs": {"type": "int", "default": "usually 3, occasionally 6 at even positions; 5 or 6 at odd positions", "valid": "2..6"},
    "n_distinct_colors": {"type": "int", "default": "used NONZERO colors, usually 3", "valid": "2..6"},
    "palette_kind": {"type": "str", "default": "uniform palette policy", "valid": "default|warm|cool|varied"},
    # Compatibility aliases are exercised in task tests, not counted twice as
    # independent axes by the Cartesian checker. Conflicting requests are errors.
    "palette_size": {"type": "int", "default": "alias of n_distinct_colors (excludes zero)",
                     "valid": "2..6", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "alias of palette_kind",
                "valid": "default|warm|cool|varied", "probe": "diagnostic"},
    "position_bias": {"type": "str", "default": "fixed mixed outcome policy",
                      "valid": "border_plus_interior_mix", "probe": "diagnostic"},
    "density": {"type": "str", "default": "fixed sparse growth budget",
                "valid": "sparse", "probe": "diagnostic"},
}
# Value-dependent conflicts carry their exact axis names on ValueError.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("top", "right", "bottom", "left")
_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 6, 7, 9),
    "cool": (1, 3, 5, 6, 8, 9),
    "varied": (9, 7, 5, 3, 1, 8, 6, 4, 2),
}
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _conflict(message, *axes):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _integer(name, value, lo, hi=None):
    if type(value) is not int or value < lo or (hi is not None and value > hi):
        raise ValueError(f"{name} must be an integer in {lo}..{hi if hi is not None else 'unbounded'}")
    return value


def _weighted(ctx, name, lo, hi, favored):
    return ctx.draw_choice(name, list(range(lo, hi + 1)) + list(favored))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _settings(seed, sample_index, difficulty, overrides):
    _integer("seed", seed, 0)
    _integer("sample_index", sample_index, 0)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override(s): {sorted(unknown)}")
    values = {k: v for k, v in overrides.items() if v is not None}
    for name, lo, hi in (("grid_h", 6, 12), ("grid_w", 7, 14),
                         ("n_blobs", 2, 6), ("n_distinct_colors", 2, 6),
                         ("palette_size", 2, 6)):
        if name in values:
            _integer(name, values[name], lo, hi)
    for name in ("palette_kind", "texture"):
        if name in values and values[name] not in PALETTE_KINDS:
            raise ValueError(f"{name} must be one of {PALETTE_KINDS}; negative fixtures are not production textures")
    for primary, alias in (("n_distinct_colors", "palette_size"), ("palette_kind", "texture")):
        if primary in values and alias in values and values[primary] != values[alias]:
            _conflict(f"{primary} and its alias {alias} disagree", primary, alias)
        if alias in values:
            values[primary] = values[alias]
    if "n_blobs" in values and "n_distinct_colors" in values and values["n_distinct_colors"] > values["n_blobs"]:
        color_axes = [k for k in ("n_distinct_colors", "palette_size") if k in overrides]
        _conflict("used nonzero colors cannot exceed n_blobs", "n_blobs", *color_axes)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=values)
    band_h = {"easy": [6, 7], "medium": [8, 9], "hard": [10, 11, 12]}.get(difficulty, [8, 9])
    h = _weighted(ctx, "grid_h", 6, 12, [7] * 25 + [8] * 8 + band_h * 3)
    w = _weighted(ctx, "grid_w", 7, 14, [7] * 8 + [8] * 25 + [9] * 8)
    minimum = max(3 if sample_index % 2 == 0 else 5, values.get("n_distinct_colors", 2))
    n = ctx.draw_choice("n_blobs", list(range(2, 7)) if "n_blobs" in values else [minimum] * 12 + [6])
    canonical_style = n == 3 and "n_distinct_colors" not in values
    max_colors = n if "n_distinct_colors" in values or n == 2 or canonical_style else n - 1
    k = (ctx.draw_choice("n_distinct_colors", [3]) if canonical_style else
         _weighted(ctx, "n_distinct_colors", 2, max_colors, [min(3, max_colors)] * 16))
    ctx.draw_choice("palette_size", [k])
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("texture", [kind])
    ctx.draw_choice("position_bias", ["border_plus_interior_mix"])
    ctx.draw_choice("density", ["sparse"])
    return ctx, h, w, n, k, kind


def _sides(cells, h, w):
    result = set()
    for r, c in cells:
        if r == 0:
            result.add("top")
        if r == h - 1:
            result.add("bottom")
        if c == 0:
            result.add("left")
        if c == w - 1:
            result.add("right")
    return result


def _transform(r, c, h, w, orientation):
    if orientation == 0:
        return r, c
    if orientation == 1:
        return c, w - 1 - r
    if orientation == 2:
        return h - 1 - r, w - 1 - c
    return h - 1 - c, r


def _legal_cell(cell, index, groups, colors, owners, h, w, allowed_sides):
    r, c = cell
    if not (0 <= r < h and 0 <= c < w) or cell in owners:
        return False
    if not _sides([cell], h, w) <= allowed_sides:
        return False
    for dr, dc in _DIRS:
        other = owners.get((r + dr, c + dc))
        if other is not None and other != index and colors[other] == colors[index]:
            return False
    return True


def _layout(ctx, h, w, n, k, kind, sample_index):
    rng = ctx.draw_rng("layout")
    palette = ctx.draw_rng("palette").sample(_PALETTES[kind], k)
    labels = [0, 0] + list(range(1, k)) if k < n else list(range(k))
    labels += [rng.randrange(k) for _ in range(n - len(labels))]
    colors = [palette[label] for label in labels]
    orientation = sample_index % 4
    depth, span = (h, w) if orientation % 2 == 0 else (w, h)
    c = rng.randint(2, span - 3)
    canonical_style = n == k == 3
    if canonical_style:
        # Retain the canonical three-object/three-color/no-singleton support.
        # A five-pair ordinary window has at least two diagnostic odd samples;
        # at least one remains when any one pair is held out as the query.
        b = rng.randint(1, span - 3)
        d = rng.randint(1, span - 3)
        seeds = [[(0, c - 1), (0, c), (1, c - 1)],
                 [(2, b), (2, b + 1), (3, b), (3, b + 1)],
                 [(depth - 1, d), (depth - 1, d + 1), (depth - 2, d)]]
    else:
        seeds = [[(0, c - 1), (0, c), (1, c - 1)],
                 [(1, c + 1), (2, c + 1)], [(1, c)]]
    if n >= 4:
        d = rng.randint(1, span - 2)
        seeds.append([(depth - 1, d), (depth - 2, d)])
    groups = [{_transform(r, col, h, w, orientation) for r, col in seed}
              for seed in seeds[:n]]
    owners = {cell: index for index, group in enumerate(groups) for cell in group}
    allowed = [_sides(group, h, w) for group in groups]
    for index in range(len(groups), n):
        # The fifth component guarantees a third erased object. Extra components
        # never merge same-colored stamps; counts remain exact at the 6x7 limit.
        want_border = index == 4 or rng.choice((False, True))
        candidates = [(r, col) for r in range(h) for col in range(w)
                      if bool(_sides([(r, col)], h, w)) == want_border
                      and len(_sides([(r, col)], h, w)) <= 1
                      and _legal_cell((r, col), index, groups, colors, owners, h, w,
                                      set(SCHEDULE_PROFILES) if want_border else set())]
        if not candidates:
            raise RuntimeError("constructive component placement exhausted its verified domain")
        cell = rng.choice(candidates)
        groups.append({cell})
        owners[cell] = index
        allowed.append(_sides([cell], h, w))
    budget = max(10, int(h * w * 0.32)) - len(owners)
    order = list(range(n))
    rng.shuffle(order)
    for index in order:
        if index == 2 and not canonical_style:
            # A singleton survivor alongside a larger survivor refutes keeping
            # only the largest interior object. Its location and color rotate.
            continue
        target = rng.randint(max(2, len(groups[index])), 5)
        for _ in range(target - len(groups[index])):
            if budget <= 0:
                break
            candidates = sorted({(r + dr, col + dc) for r, col in groups[index]
                                 for dr, dc in _DIRS
                                 if _legal_cell((r + dr, col + dc), index, groups,
                                                colors, owners, h, w, allowed[index])})
            if not candidates:
                break  # Shape size is a random bound, not an advertised exact axis.
            cell = rng.choice(candidates)
            groups[index].add(cell)
            owners[cell] = index
            budget -= 1
    grid = full_grid(h, w, 0)
    for index, group in enumerate(groups):
        for r, col in group:
            grid[r][col] = colors[index]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx, h, w, n, k, kind = _settings(seed, sample_index, difficulty, overrides)
    return _layout(ctx, h, w, n, k, kind, sample_index)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(components(grid, same_color=True, connectivity=4)),
            "n_distinct_colors": len({v for row in grid for v in row} - {0}),
            "palette_size": len({v for row in grid for v in row} - {0})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    reasons = []
    if not (6 <= h <= 12 and 7 <= w <= 14):
        reasons.append("outside the documented 6..12 by 7..14 canvas domain")
    colors = {v for row in grid for v in row}
    if 0 not in colors or not 2 <= len(colors - {0}) <= 6:
        reasons.append("expected background zero and 2..6 used nonzero colors")
    comps = components(grid, same_color=True, connectivity=4)
    if not 2 <= len(comps) <= 6:
        reasons.append("expected 2..6 same-color four-connected objects")
    count_border = sum(bool(_sides(comp["cells"], h, w)) for comp in comps)
    if count_border == 0:
        reasons.append("no border object to erase")
    if count_border == len(comps):
        reasons.append("no interior object to retain")
    return reasons


def strict_canonical_like(grid):
    """This task's component domain, including all canonical inputs."""
    return self_check(grid)


def _selected_cells(grid, *, same_color=True, connectivity=4, ignored=None, limit=None):
    chosen = [comp for comp in components(grid, same_color=same_color, connectivity=connectivity)
              if _sides(comp["cells"], len(grid), len(grid[0])) - ({ignored} if ignored else set())]
    if limit is not None:
        chosen = chosen[:limit]
    return {p for comp in chosen for p in comp["cells"]}


def _remove(grid, cells):
    out = [list(row) for row in grid]
    for r, c in cells:
        out[r][c] = 0
    return out


def _border_colors(grid):
    colors = {grid[r][c] for r, c in _selected_cells(grid)}
    return [[0 if value in colors else value for value in row] for row in grid]


def _eight_connected(grid):
    return _remove(grid, _selected_cells(grid, connectivity=8))


def _multicolor_four(grid):
    return _remove(grid, _selected_cells(grid, same_color=False))


def _multicolor_eight(grid):
    return _remove(grid, _selected_cells(grid, same_color=False, connectivity=8))


def _ignore_right(grid):
    return _remove(grid, _selected_cells(grid, ignored="right"))


def _first_two(grid):
    return _remove(grid, _selected_cells(grid, limit=2))


def _largest_interior(grid):
    interior = [comp for comp in components(grid, same_color=True, connectivity=4)
                if not _sides(comp["cells"], len(grid), len(grid[0]))]
    largest = max((len(comp["cells"]) for comp in interior), default=0)
    keep = {p for comp in interior if len(comp["cells"]) == largest for p in comp["cells"]}
    return [[value if (r, c) in keep else 0 for c, value in enumerate(row)]
            for r, row in enumerate(grid)]


def _has_repeated_border_color(grid):
    erased = _selected_cells(grid)
    colors = {grid[r][c] for r, c in erased}
    return any(value in colors and value != 0 and (r, c) not in erased
               for r, row in enumerate(grid) for c, value in enumerate(row))


def _only_side(grid, side):
    return any(_sides(comp["cells"], len(grid), len(grid[0])) == {side}
               for comp in components(grid, same_color=True, connectivity=4))


CANONICAL_SHORTCUTS = {
    "border_colors": _border_colors,
    "eight_connected": _eight_connected,
    "multicolor_four": _multicolor_four,
    "multicolor_eight": _multicolor_eight,
    "ignore_right": _ignore_right,
    "first_two": _first_two,
    "largest_interior": _largest_interior,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    "repeated_border_color": _has_repeated_border_color,
    "diagonal_border_link": lambda g: bool(_selected_cells(g, connectivity=8) - _selected_cells(g)),
    "different_color_border_link": lambda g: bool(_selected_cells(g, same_color=False) - _selected_cells(g)),
    "right_only": lambda g: _only_side(g, "right"),
    "third_border_object": lambda g: len([c for c in components(g, same_color=True, connectivity=4)
                                         if _sides(c["cells"], len(g), len(g[0]))]) > 2,
    "unequal_interior_objects": lambda g: len({len(c["cells"]) for c in components(g, same_color=True, connectivity=4)
                                              if not _sides(c["cells"], len(g), len(g[0]))}) > 1,
}
WITNESS_RIVALS = {
    "repeated_border_color": ["border_colors"],
    "diagonal_border_link": ["eight_connected", "multicolor_eight"],
    "different_color_border_link": ["multicolor_four"],
    "right_only": ["ignore_right"],
    "third_border_object": ["first_two"],
    "unequal_interior_objects": ["largest_interior"],
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "ignore_top": lambda g: _remove(g, _selected_cells(g, ignored="top")),
    "ignore_bottom": lambda g: _remove(g, _selected_cells(g, ignored="bottom")),
    "ignore_left": lambda g: _remove(g, _selected_cells(g, ignored="left")),
    "border_pixels_only": lambda g: _remove(g, {(r, c) for r, row in enumerate(g)
                                               for c, value in enumerate(row)
                                               if value and _sides([(r, c)], len(g), len(g[0]))}),
    "identity": lambda g: [list(row) for row in g],
    "erase_all": lambda g: [[0] * len(row) for row in g],
}

