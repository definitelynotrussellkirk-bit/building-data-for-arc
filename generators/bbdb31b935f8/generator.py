"""Generator for b20f7c8b.

Rule: a key around an 8-panel maps solid 5x5 tiles into patterned tiles.

Combinatorial axes (8): grid_h/w, tile_count, n_keys, palette_kind,
anchor_corner, asymmetry_force, position_bias.
Degenerates: no_key, no_tiles, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "bbdb31b935f8"
RULE_HASH = "841872fe143e"  # canonical rule this generator was written against
# 2.0.0: canonical-scene restructure (defect-lint canonical-coverage flag): the
# real task's 8-panel is a LARGE full-height sidebar with the key motifs
# EMBEDDED in it (canonical max component ~86 cells, ~23 objects), not a 3x3
# block with halo keys. Panel is now a 5-6 col sidebar, keys are carved into
# it (the rule reads keys from the 8-bbox+1 window, so both layouts are legal
# — this one matches the demos). Also fixes: AXES ranges now match the actual
# draws (grid_h/w/tile_count lied), and key shapes are picked one-per-D8-
# symmetry-group so no patterned tile can match two keys under the rule's
# 8-transform matching (s0/s3, s1/s2, s4/s5 were mutual transforms).
VERSION = "2.0.0"
TASK_ID = "bbdb31b935f8"
SUMMARY = (
    "A large 8-colored sidebar panel (5-6 cols, near full height) carries "
    "2-4 KEY MOTIFS carved into it in distinct non-{0,1,2,8} colors. The "
    "field beside it holds isolated 5x5 tiles: SOLID tiles in key colors "
    "and PATTERNED tiles (base color 2 + 1-cells at some key's motif "
    "positions). Rule: solid key-color tiles become base-color tiles "
    "stamped with that key's 1-motif; patterned tiles whose 1-motif "
    "matches a key (under the 8 dihedral transforms) become solid tiles "
    "of that key's color."
)

# Rivals: 'leave tiles solid' refuted by any demo (output has 1s
# inside). 'use random pattern' refuted by ≥2 demos where pattern
# matches key's relative positions. 'recolor tile to bg' refuted
# by any demo (recolor uses pattern_base, derived from inputs).
# 4 demos with varied keys + tiles cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "one large 8-panel sidebar with key motifs embedded in distinct colors",
    "solid 5x5 tiles use one of those key colors as their base",
    "patterned 5x5 tiles carry a key's 1-motif on pattern-base 2",
    "key motifs are pairwise distinct under all 8 dihedral transforms",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_key", "no_tiles", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

# Key motifs, grouped by D8 symmetry class: the canonical rule matches a
# patterned tile's 1-cells against EVERY dihedral transform of every key, so
# two keys in one instance must never be transforms of each other (else the
# tile->key mapping is ambiguous). Pick at most ONE shape per group.
# All normalize into the 4x4 stampable area (rel offsets <= 3).
KEY_SHAPE_GROUPS = [
    [[(0, 0), (0, 2), (2, 0)], [(0, 2), (2, 0), (2, 2)]],
    [[(0, 0), (0, 2), (2, 2)], [(0, 0), (2, 0), (2, 2)]],
    [[(0, 0), (0, 2), (3, 3)], [(0, 0), (2, 0), (3, 3)]],
    [[(0, 0), (1, 2), (2, 1), (3, 3)]],
]


def _norm_cells(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _stamp_pattern_tile(g, r0, c0, base_color, rels):
    draw_rect(g, r0, c0, 5, 5, base_color)
    for dr, dc in rels:
        # Tile-info in the canonical rule measures 1-cells from obj-r1/c1 + 1.
        g[r0 + 1 + dr][c0 + 1 + dc] = 1


AXES = {
    "grid_h":         {"type": "int", "default": "18-22 med", "valid": "16..26"},
    "grid_w":         {"type": "int", "default": "20-24 med", "valid": "18..28"},
    "tile_count":     {"type": "int", "default": "rng 2..4 by band", "valid": "2..6"},
    "n_keys":         {"type": "int", "default": "2 easy / 2-3 med / 3-4 hard",
                       "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "position_bias":  {"type": "str", "default": "sidebar_panel",
                       "valid": "sidebar_panel"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_key|no_tiles|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 16, 19)
        w = ctx.draw_int("grid_w", 18, 22)
        tile_count = ctx.draw_int("tile_count", 2, 3)
        n_keys_want = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 20, 26)
        w = ctx.draw_int("grid_w", 22, 28)
        tile_count = ctx.draw_int("tile_count", 4, 6)
        n_keys_want = ctx.draw_int("n_keys", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 18, 22)
        w = ctx.draw_int("grid_w", 20, 24)
        tile_count = ctx.draw_int("tile_count", 3, 4)
        n_keys_want = ctx.draw_int("n_keys", 2, 3)

    for _layout in range(80):
        g = full_grid(h, w, 0)
        # Canonical scene: a 5-6 col, near-full-height 8-panel on one side.
        pw = rng.randint(5, 6)
        ph = rng.randint(max(12, h - 4), h)
        pr0 = rng.randint(0, h - ph)
        side_right = rng.random() < 0.7          # canonical demos use the right edge
        pc0 = (w - pw) if side_right else 0
        draw_rect(g, pr0, pc0, ph, pw, 8)

        # Tile field: strictly beside the panel, >=2 cols clear of its window
        # so tile colors can never leak into the rule's key-reading region.
        # Tiles pack onto a 6-step slot grid (1-cell isolation guaranteed).
        if side_right:
            c_lo, c_hi = 0, pc0 - 7
        else:
            c_lo, c_hi = pc0 + pw + 2, w - 5
        if c_hi < c_lo:
            continue
        tile_slots = [(r0, c0) for r0 in range(0, h - 4, 6)
                      for c0 in range(c_lo, c_hi + 1, 6)]

        # Carve key motifs into the panel, stacked vertically with gaps. Each
        # key takes one shape from a DISTINCT D8 symmetry group (see above).
        # Both map directions per key (a patterned AND a solid tile) need 2
        # slots each, so shrink the key count gracefully on tight canvases.
        key_slots = list(range(pr0 + 1, pr0 + ph - 4, 6))
        n_keys = min(n_keys_want, len(key_slots), len(KEY_SHAPE_GROUPS),
                     len(tile_slots) // 2)
        if n_keys < 2:
            continue
        key_colors = rng.sample([c for c in range(3, 10) if c != 8], n_keys)
        groups = rng.sample(KEY_SHAPE_GROUPS, n_keys)
        key_rels: dict[int, list[tuple[int, int]]] = {}
        for key_color, slot_r, group in zip(key_colors, key_slots, groups):
            shape = _norm_cells(rng.choice(group))
            span_c = max(dc for _, dc in shape)
            c_off = pc0 + rng.randint(0, max(0, pw - 1 - span_c))
            for dr, dc in shape:
                g[slot_r + dr][c_off + dc] = key_color
            if max(max(dr for dr, _ in shape), span_c) > 3:
                raise AssertionError("key motifs must fit the 4x4 stampable area")
            key_rels[key_color] = shape

        pattern_base = 2
        jobs = []
        for key_color in key_colors:
            jobs.append(("pattern", key_color, key_rels[key_color]))
            jobs.append(("solid", key_color, key_rels[key_color]))
        while len(jobs) < min(tile_count, len(tile_slots)):
            key_color = key_colors[len(jobs) % len(key_colors)]
            jobs.append(("solid", key_color, key_rels[key_color]))
        rng.shuffle(jobs)

        for (r0, c0), (kind, tile_color, rels) in zip(
                rng.sample(tile_slots, len(jobs)), jobs):
            if kind == "pattern":
                _stamp_pattern_tile(g, r0, c0, pattern_base, rels)
            else:
                draw_rect(g, r0, c0, 5, 5, tile_color)
        return g
    raise ValueError("could not lay out the sidebar panel + matching tiles")


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 20, 0)
    if name == "no_key":
        draw_rect(g, 10, 2, 5, 5, 3)
        return g
    if name == "no_tiles":
        draw_rect(g, 0, 15, 18, 5, 8)
        for r, c in [(2, 15), (2, 17), (4, 15)]:
            g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(18):
            for c in range(20):
                g[r][c] = 8
        return g
    return g


def _solid_5x5_tiles_for_self_check(grid, color):
    h, w = len(grid), len(grid[0])
    out = []
    for r0 in range(h - 4):
        for c0 in range(w - 4):
            if all(grid[r0 + dr][c0 + dc] == color for dr in range(5) for dc in range(5)):
                out.append((r0, c0))
    return out


def _patterned_5x5_tiles_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    out = []
    for r0 in range(h - 4):
        for c0 in range(w - 4):
            vals = [grid[r0 + dr][c0 + dc] for dr in range(5) for dc in range(5)]
            colors = set(vals)
            if 1 in colors and len(colors - {1}) == 1 and all(v != 0 and v != 8 for v in vals):
                out.append((r0, c0))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Mirror the rule's own reading: keys live in the 8-bbox+1 window."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    eight = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(eight) < 40:
        return ["expected a large 8-panel sidebar (canonical scene: 5-6 cols, near full height)"]
    er1 = min(r for r, _ in eight); er2 = max(r for r, _ in eight)
    ec1 = min(c for _, c in eight); ec2 = max(c for _, c in eight)
    msgs = []
    key_cells: dict[int, list[tuple[int, int]]] = {}
    for r in range(max(0, er1 - 1), min(h, er2 + 2)):
        for c in range(max(0, ec1 - 1), min(w, ec2 + 2)):
            v = grid[r][c]
            if v not in (0, 1, 2, 8):
                key_cells.setdefault(v, []).append((r, c))
    if len(key_cells) < 2:
        msgs.append(f"expected >=2 key motifs inside the 8-panel window, found {len(key_cells)}")
    rel_sets = []
    for color, cells in key_cells.items():
        rels = _norm_cells(cells)
        if max(max(dr for dr, _ in rels), max(dc for _, dc in rels)) > 3:
            msgs.append(f"key {color} motif exceeds the 4x4 stampable area")
        rel_sets.append(tuple(rels))
    if len(rel_sets) != len(set(rel_sets)):
        msgs.append("two keys share an identical motif — tile mapping is ambiguous")
    has_solid = any(_solid_5x5_tiles_for_self_check(grid, kc) for kc in key_cells)
    has_patterned = bool(_patterned_5x5_tiles_for_self_check(grid))
    if not has_solid:
        msgs.append("no solid 5x5 tile in a key color")
    if not has_patterned:
        msgs.append("no patterned 5x5 tile")
    return msgs
