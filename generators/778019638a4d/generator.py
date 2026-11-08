"""Generator for arc_puzzle_bank_fifth_21_bundle:hard_33_local_transform_gallery_sorted_by_width.

Each target component has a transform key immediately above its bounding-box
top-left. The rule transforms each keyed component and packs the results by
width.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_items,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_keys, no_components, equal_widths.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "778019638a4d"
VERSION = "2.1.0"  # shape-locked-in: fixed 11x12 with 3 fixed-position items. Rule transforms each key+component and packs by width (position/size-generic). Now random grid size, n_items at random separated positions with random polyomino shapes + key directly above each bbox top-left.
TASK_ID = "778019638a4d"
SUMMARY = "Transform keyed components and pack them into a width-sorted gallery."

INVARIANTS = [
    "keys are colors 1..4 and sit directly above their component bbox",
    "target components are nonzero colors other than 1..4",
    "components are separated after key removal",
    "transformed crops are sorted by width then height descending",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_keys", "no_components", "equal_widths")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "13..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_items":        {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "keys_above_components",
                       "valid": "keys_above_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_ITEMS = [
    ([(0, 0), (1, 0), (1, 1)], (2, 1)),
    ([(0, 0), (0, 1), (1, 1), (2, 1)], (2, 7)),
    ([(0, 1), (1, 0), (1, 1), (1, 2)], (7, 3)),
]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_items = ctx.draw_int("n_items", 2, 2)
        h = ctx.draw_int("grid_h", 12, 13); w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        n_items = ctx.draw_int("n_items", 3, 4)
        h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 15, 20)
    else:
        n_items = ctx.draw_int("n_items", 2, 3)
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 13, 17)

    # The normal path should teach both parts of the rule: key-local transforms
    # AND width-ordered packing.  Pure parity allows equal-width transformed
    # crops, but those demos hide the primary sorting signal.  Retry with a
    # different keyed RNG until the executable self_check sees a nontrivial
    # width ordering and a complete key/component binding.
    last = None
    for attempt in range(64):
        rng = ctx.draw_rng("layout" if attempt == 0 else f"layout_retry_{attempt}")
        keys = rng.sample([1, 2, 3, 4], n_items)
        colors = rng.sample([5, 6, 7, 8, 9], n_items)
        g = full_grid(h, w, 0)
        used = set()
        placed = 0
        for _ in range(400):
            if placed >= n_items:
                break
            poly = _rand_poly(rng, rng.randint(3, 5))
            ph = max(r for r, _ in poly) + 1; pw = max(c for _, c in poly) + 1
            top = rng.randint(1, h - ph); left = rng.randint(0, w - pw)
            unit = [(top + dr, left + dc) for dr, dc in poly] + [(top - 1, left)]
            # whole unit (component + key) plus a 1-cell margin must be clear
            halo = {(r + dr, c + dc) for (r, c) in unit
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if any(cell in used for cell in unit) or (top - 1, left) in [u for u in unit[:-1]]:
                continue
            if halo & used:
                continue
            _paint(g, top, left, poly, colors[placed])
            g[top - 1][left] = keys[placed]
            used |= halo
            placed += 1
        last = g
        if not self_check(g, difficulty=difficulty):
            return g
    raise ValueError(f"could not place a nontrivial width-sorted keyed gallery; last={self_check(last)}")


def _components(grid, colors):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] not in colors:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] in colors):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _crop_component(grid, cells):
    r0, c0, r1, c1 = _bbox(cells)
    cellset = set(cells)
    return [[grid[r][c] if (r, c) in cellset else 0
             for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _transform(crop, key):
    if key == 1:
        return crop
    if key == 2:
        return _rot_cw(crop)
    if key == 3:
        return _rot_180(crop)
    if key == 4:
        return _flip_lr(crop)
    return crop


def _keyed_transformed_crops(grid):
    key_positions = [(r, c, grid[r][c])
                     for r in range(len(grid)) for c in range(len(grid[0]))
                     if grid[r][c] in (1, 2, 3, 4)]
    components = _components(grid, {5, 6, 7, 8, 9})
    crops = []
    binding_errors = []
    for kr, kc, key in key_positions:
        matches = []
        for cells in components:
            r0, c0, _, _ = _bbox(cells)
            if kr == r0 - 1 and kc == c0:
                matches.append(cells)
        if len(matches) != 1:
            binding_errors.append((kr, kc, key, len(matches)))
        else:
            crops.append(_transform(_crop_component(grid, matches[0]), key))
    return key_positions, components, crops, binding_errors


def self_check(grid, *, difficulty=None, meta=None):
    """Executable normal-path invariants for the keyed gallery task."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    key_positions, components, crops, binding_errors = _keyed_transformed_crops(grid)
    if len(key_positions) < 2:
        errors.append("normal sample must contain at least two key cells")
    if len(components) < 2:
        errors.append("normal sample must contain at least two target components")
    if len(key_positions) != len(components):
        errors.append("key count must equal component count")
    if binding_errors:
        errors.append("every key must bind exactly one component bbox directly below it")
    widths = [len(crop[0]) for crop in crops]
    if len(widths) >= 2 and len(set(widths)) < 2:
        errors.append("transformed crop widths are all equal; width-sort signal is hidden")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    if name == "no_keys":
        # components without keys → no transforms to apply
        for idx, color in zip(range(2), [5, 6]):
            cells, (top, left) = _ITEMS[idx]
            _paint(g, top, left, cells, color)
        return g
    if name == "no_components":
        # keys without components → nothing to transform/pack
        g[1][1] = 1
        g[1][7] = 2
        return g
    if name == "equal_widths":
        # all components same width → no sorting signal, ambiguous order
        for idx, color in zip(range(2), [5, 6]):
            cells = [(0, 0), (1, 0), (1, 1)]  # width 2
            top = 2 if idx == 0 else 6
            left = 1 if idx == 0 else 5
            g[top - 1][left] = idx + 1
            _paint(g, top, left, cells, color)
        return g
    return g
