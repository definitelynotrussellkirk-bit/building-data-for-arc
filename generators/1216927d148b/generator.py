"""Generator for arc_puzzle_bank_fourteenth_21_bundle:hard_96_build_pairwise_intersection_gallery.

Rule: 3 panels at fixed cols [0..4, 6..10, 12..16], each 5 wide, each holding
one single-color 4-connected glyph.  Output hstacks the 3 pairwise
intersections of their binary masks, drawn in cyan(8).

Every canonical train/test input has three single-color, 4-connected panels
with pairwise-distinct colors and a non-empty witness in all three pairwise
intersections.  The teaching distribution therefore grows one connected glyph
per panel (never random cell scatter), seeds explicit AB/AC/BC witness cells,
and keeps panel A's cell count exactly on the drawn ``panel_cell_count`` axis
(panels B/C jitter +-2, matching the canonical 5..8-cell spread).

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_cell_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_panels, full_panels (lawful edge-but-valid), single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1216927d148b"
VERSION = "3.0.0"  # connected-glyph distribution (drift fix), RULE_HASH pin, honest override contract
TASK_ID = "1216927d148b"
# sha256[:12] of the whitespace-normalized canonical program_solution at
# authoring time (data/canonical/puzzles.jsonl, task_id 1216927d148b).
RULE_HASH = "cc8b8a179b65"

SUMMARY = "3 5-wide panels with binary content; pairwise intersection."

INVARIANTS = [
    "background is 0",
    "grid is H rows tall (H in 5..12) and 17 cols wide",
    "3 panels at cols [0..4], [6..10], [12..16]; each holds non-bg cells",
    "each panel is a single 4-connected one-color glyph; panel colors are pairwise distinct",
    "all three pairwise panel intersections (AB, AC, BC) are non-empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_panels", "full_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS
# full_panels keeps every canonical invariant (three connected one-color
# panels, non-empty intersections); it is an edge-but-valid instance whose
# intersections equal the full panel mask, so it is explicitly lawful.
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ("full_panels",)

AXES = {
    "grid_h":         {"type": "int", "default": "difficulty-skewed 5..12", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "panel_cell_count": {"type": "int", "default": "difficulty-skewed 1..25 (panel A; B/C jitter +-2)", "valid": "1..25"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed_panels", "valid": ["fixed_panels"]},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "varied", "valid": ["varied"]},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PANEL_STARTS = (0, 6, 12)
_PANEL_W = 5
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Axes that remain meaningful when a degenerate texture short-circuits the
# normal draw.  Anything else must be rejected loudly rather than silently
# ignored (override-contract inertness class).
_DEGENERATE_ALLOWED = {
    "empty_panels": {"texture", "grid_h", "grid_w", "density",
                     "position_bias", "palette_size", "n_distinct_colors"},
    "full_panels": {"texture", "grid_h", "grid_w", "density",
                    "position_bias", "palette_size", "n_distinct_colors",
                    "palette_kind"},
    "single_panel": {"texture", "grid_h", "grid_w", "density",
                     "position_bias", "palette_size", "n_distinct_colors",
                     "palette_kind", "panel_cell_count"},
}


def _resolve_overrides(overrides: dict) -> dict:
    """Map the texture alias onto palette_kind; reject conflicts loudly."""
    ov = dict(overrides)
    texture = ov.get("texture")
    if texture is None or texture in DEGENERATE_TEXTURES:
        return ov
    if texture not in PALETTE_KINDS:
        raise ValueError(f"unknown texture {texture!r}")
    kind = ov.get("palette_kind")
    if kind is not None and kind != texture:
        raise ValueError(
            f"texture {texture!r} conflicts with palette_kind {kind!r}"
        )
    ov["palette_kind"] = texture
    return ov


def _palette(rng, kind: str) -> list[int]:
    if kind == "warm":
        return rng.sample([2, 4, 7, 9], 3)
    if kind == "cool":
        return rng.sample([1, 3, 5, 6], 3)
    if kind == "varied":
        # one color from each spaced triad: maximally separated palette
        return [rng.choice(triad) for triad in ((1, 4, 7), (2, 5, 8), (3, 6, 9))]
    if kind != "default":
        raise ValueError(f"unknown palette_kind {kind!r}")
    return rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)


def _neighbors4(cell, h):
    r, c = cell
    return [(r + dr, c + dc) for dr, dc in _DIRECTIONS
            if 0 <= r + dr < h and 0 <= c + dc < _PANEL_W]


def _pick_witnesses(rng, h, n):
    """Pick AB/AC/BC witness cells, pairwise 4-adjacent-or-equal so a connected
    glyph of any declared size n >= 2 can contain its pair."""
    local = [(r, dc) for r in range(h) for dc in range(_PANEL_W)]
    if n == 1:
        cell = rng.choice(local)
        return cell, cell, cell
    ab = rng.choice(local)
    ac = rng.choice([ab] + _neighbors4(ab, h))
    bc_options = [cand for cand in [ab] + _neighbors4(ab, h)
                  if cand == ac or cand in _neighbors4(ac, h)]
    bc = rng.choice(bc_options or [ac])
    return ab, ac, bc


def _grow_shape(rng, h, seed_cells, n):
    """Grow a 4-connected glyph of exactly n cells containing every seed."""
    cells = set(seed_cells)
    if len(cells) == 2:
        # connect the two (adjacent) seeds; the path is the seeds themselves
        pass
    while len(cells) < n:
        frontier = sorted({
            nb for cell in cells for nb in _neighbors4(cell, h)
        } - cells)
        cells.add(rng.choice(frontier))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _resolve_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(ctx, texture, overrides)

    h = ctx.draw_int_diff("grid_h", 5, 12)
    w = ctx.draw_int("grid_w", 17, 17)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    n = ctx.draw_int_diff("panel_cell_count", 1, 25)
    ctx.draw_int("palette_size", 3, 3)
    ctx.draw_int("n_distinct_colors", 3, 3)
    ctx.draw_choice("position_bias", ("fixed_panels",))
    ctx.draw_choice("density", ("varied",))

    rng = ctx.draw_rng("layout")
    palette = _palette(ctx.draw_rng("palette"), kind)
    ab, ac, bc = _pick_witnesses(rng, h, n)
    seed_sets = [(ab, ac), (ab, bc), (ac, bc)]
    counts = [n]
    for _ in range(2):
        counts.append(min(25, max(1, n + rng.randint(-2, 2))))
    g = full_grid(h, w, 0)
    for c0, color, seeds, count in zip(_PANEL_STARTS, palette, seed_sets, counts):
        shape = _grow_shape(rng, h, seeds, count)
        for r, dc in shape:
            g[r][c0 + dc] = color
    return g


def observe_overrides(grid):
    """Realized exact axes, recoverable from the returned grid.

    ``panel_cell_count`` is the realized cell count of panel A (cols 0..4);
    panels B/C are allowed +-2 jitter and are not the keyed axis."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    count_a = sum(
        1 for r in range(h) for dc in range(_PANEL_W)
        if dc < w and grid[r][dc] != 0
    )
    return {"grid_h": h, "grid_w": w, "panel_cell_count": count_a}


def _components(cells):
    cells = set(cells)
    out = []
    while cells:
        stack = [cells.pop()]
        comp = {stack[0]}
        while stack:
            r, c = stack.pop()
            for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nb in cells:
                    cells.remove(nb)
                    stack.append(nb)
                    comp.add(nb)
        out.append(comp)
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        return ["grid cells must be ARC color integers 0..9"]
    texture = (meta or {}).get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _degenerate_errors(grid, texture)
    if w != 17:
        errors.append(f"expected width 17 for three 5-wide panels, got {w}")
    if not 5 <= h <= 12:
        errors.append(f"expected height 5..12, got {h}")
    for sep in (5, 11):
        if sep >= w or any(grid[r][sep] != 0 for r in range(h)):
            errors.append(f"separator column {sep} is not all background")
    masks = []
    panel_colors = []
    for c0 in _PANEL_STARTS:
        cells = [(r, dc) for r in range(h) for dc in range(_PANEL_W)
                 if c0 + dc < w and grid[r][c0 + dc] != 0]
        if not cells:
            errors.append(f"panel at col {c0} is empty")
            masks.append(set())
            panel_colors.append(None)
            continue
        colors = {grid[r][c0 + dc] for r, dc in cells}
        if len(colors) != 1:
            errors.append(f"panel at col {c0} mixes colors {sorted(colors)}")
        panel_colors.append(next(iter(colors)) if len(colors) == 1 else None)
        if len(cells) > 25:
            errors.append(f"panel at col {c0} has {len(cells)} cells (> 25)")
        if len(_components(cells)) != 1:
            errors.append(f"panel at col {c0} is not a single 4-connected glyph")
        masks.append(set(cells))
    known = [c for c in panel_colors if c is not None]
    if len(set(known)) != len(known):
        errors.append(f"panel colors are not pairwise distinct: {panel_colors}")
    if len(masks) == 3 and all(masks):
        pair_names = ((0, 1, "AB"), (0, 2, "AC"), (1, 2, "BC"))
        for a, b, name in pair_names:
            if not (masks[a] & masks[b]):
                errors.append(f"missing {name} pairwise-intersection witness")
    return errors


def _degenerate_errors(grid, name):
    """Validate a declared degenerate draw against its own contract."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if w != 17:
        errors.append(f"expected width 17, got {w}")
    for sep in (5, 11):
        if sep < w and any(grid[r][sep] != 0 for r in range(h)):
            errors.append(f"separator column {sep} is not all background")
    panels = [
        {(r, dc) for r in range(h) for dc in range(_PANEL_W)
         if c0 + dc < w and grid[r][c0 + dc] != 0}
        for c0 in _PANEL_STARTS
    ]
    if name == "empty_panels":
        if any(panels):
            errors.append("empty_panels draw has non-background cells")
    elif name == "full_panels":
        for c0, cells in zip(_PANEL_STARTS, panels):
            if len(cells) != h * _PANEL_W:
                errors.append(f"full_panels panel at col {c0} is not fully filled")
    elif name == "single_panel":
        if not panels[0]:
            errors.append("single_panel draw left panel A empty")
        if panels[1] or panels[2]:
            errors.append("single_panel draw populated panel B or C")
    else:
        errors.append(f"unknown degenerate texture {name!r}")
    return errors


def _draw_from_degenerate(ctx, name, overrides):
    allowed = _DEGENERATE_ALLOWED[name]
    bad = sorted(k for k, v in overrides.items()
                 if v is not None and k not in allowed)
    if bad:
        raise ValueError(
            f"texture {name!r} is incompatible with override(s): {', '.join(bad)}"
        )
    h = ctx.draw_int_diff("grid_h", 5, 12)
    w = ctx.draw_int("grid_w", 17, 17)
    g = full_grid(h, w, 0)
    if name == "empty_panels":
        # all 3 panels empty → every pairwise intersection is empty, output all-bg
        return g
    palette = _palette(ctx.draw_rng("palette"),
                       ctx.draw_choice("palette_kind", PALETTE_KINDS))
    if name == "full_panels":
        # all 3 panels fully filled → every intersection equals the panel mask
        for c0, color in zip(_PANEL_STARTS, palette):
            for r in range(h):
                for dc in range(_PANEL_W):
                    g[r][c0 + dc] = color
        return g
    if name == "single_panel":
        # only the first panel populated → intersections with B and C are empty
        n = ctx.draw_int_diff("panel_cell_count", 1, 25)
        rng = ctx.draw_rng("layout")
        seed = (rng.randrange(h), rng.randrange(_PANEL_W))
        for r, dc in _grow_shape(rng, h, [seed], n):
            g[r][dc] = palette[0]
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
