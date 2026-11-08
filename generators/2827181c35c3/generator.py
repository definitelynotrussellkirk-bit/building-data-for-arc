"""Generator for arc_additional_puzzles_21_set12_bundle:H78 — zone commands transform and pack.

Rule: row 0 holds N commands (each non-zero cell = transform code 1..4) at distinct
columns. Below row 0 there are N components; each is associated with the nearest top-row
command (by horizontal-center distance). Apply that command's transform to the cropped
component, sort transforms by (cell_count desc, min_color asc), and pack the
transformed crops left-to-right starting at row 1, col 0 with one blank column
between them. Output is same size as input.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_commands (row 0 empty → rule has no transforms);
no_objects (commands but no body components → rule has nothing to
transform); identity_commands (all command codes = identity → output
== input shape order).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2827181c35c3"
VERSION = "2.0.1"
TASK_ID = "2827181c35c3"

SUMMARY = "Row-0 commands (codes 1..4) at distinct columns; each non-row-0 component is matched to nearest command by column; rule transforms (rotate/flip) each, sorts by size desc + color asc, packs left-to-right from row 1, col 0."

# Rivals: 'output = input' refuted by ≥1 demo where transformed crops
# differ from originals. 'pack by input order' refuted by ≥2 demos
# where size-sort changes the order. 'discard commands' refuted by
# any demo where commands clearly affect the transform.
# 'pack vertically' refuted by ≥2 demos showing horizontal packing.
# 4 demos with varied commands + shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 has 2-3 non-zero cells (transform codes 1..4) at distinct columns",
    "below row 0, exactly that many isolated 4-connected components in distinct colors",
    "components are placed in horizontal zones near their assigned command",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_commands", "no_objects", "identity_commands")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_objs":            {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":     {"type": "str", "default": "row0_commands_with_zoned_objects",
                          "valid": "row0_commands_with_zoned_objects"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has ≥2 command cells (1..4); body rows have ≥1 non-zero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_commands", "no_objects", "identity_commands"):
        return []
    errs = []
    commands = [v for v in grid[0] if 1 <= v <= 4]
    if len(commands) < 2:
        errs.append(f"row-0 has only {len(commands)} command cell(s) (1..4); expected ≥2")
    body_nonzero = sum(1 for r in range(1, h) for c in range(w) if grid[r][c] != 0)
    if body_nonzero == 0:
        errs.append("body rows have no non-zero cells")
    return errs


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],                     # L-tromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],             # S-tet
    [(0, 0), (0, 1), (0, 2), (1, 1)],             # T-tet
    [(0, 0), (1, 0), (1, 1), (2, 0)],             # T-rot
    [(0, 0), (0, 1), (0, 2), (1, 0)],             # J-tet
    [(0, 0), (0, 1), (1, 0), (1, 1)],             # square
    [(0, 0), (0, 1), (0, 2), (0, 3)],             # I-tet horizontal
    [(0, 0), (1, 0), (2, 0), (3, 0)],             # I-tet vertical
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)],     # P-pent
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],     # U-pent
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 15)
        n_objs = ctx.draw_int("n_objs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 18, 22)
        n_objs = ctx.draw_int("n_objs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 18)
        n_objs = ctx.draw_int("n_objs", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        zone_w = w // n_objs
        cmd_cols = []
        for i in range(n_objs):
            cstart = i * zone_w
            cend = (i + 1) * zone_w - 1 if i < n_objs - 1 else w - 1
            cmd_cols.append(rng.randint(cstart, min(cend, w - 1)))
        codes = [rng.randint(1, 4) for _ in range(n_objs)]
        for cc, code in zip(cmd_cols, codes):
            g[0][cc] = code

        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n_objs)
        ok = True
        for i in range(n_objs):
            cstart = i * zone_w
            cend = (i + 1) * zone_w - 1 if i < n_objs - 1 else w - 1
            placed = False
            for _ in range(60):
                shape = rng.choice(_SHAPES)
                sh = max(r for r, _ in shape) + 1
                sw = max(c for _, c in shape) + 1
                r0 = rng.randint(2, h - sh)
                c0 = rng.randint(cstart, max(cstart, cend - sw + 1))
                if c0 + sw - 1 > cend: continue
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = colors[i]
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not realize zone-commands layout in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 12, 16
    g = full_grid(h, w, 0)
    if name == "no_commands":
        # Row 0 empty — rule has no transforms.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[3 + dr][11 + dc] = 5
        return g
    if name == "no_objects":
        # Commands but no objects.
        g[0][3] = 1; g[0][11] = 2
        return g
    if name == "identity_commands":
        # All command codes = 1 (identity) — output unchanged.
        g[0][3] = 1; g[0][11] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[3 + dr][11 + dc] = 5
        return g
    return g
