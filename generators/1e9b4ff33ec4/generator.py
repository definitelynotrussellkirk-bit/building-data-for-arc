"""Generator for 20b:hard_135 — overlay blocked ray counts.

Rule: emitters of color 2 cast cardinal rays; rays are blocked by
color 8 cells. Output is a count map: 1→2, 2→3, 3+→4, 8 stays, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, no_walls, isolated_emitter.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e9b4ff33ec4"
VERSION = "1.2.0"  # v1.2.0: add executable self_check for emitter/wall ray-count inputs.
TASK_ID = "1e9b4ff33ec4"

SUMMARY = "2-4 isolated color-2 emitters + 1-3 8-walls (line segments)."

INVARIANTS = [
    "background is 0",
    "2-4 isolated single color-2 emitter cells",
    "1-3 line segments (length 3-6) of color 8 (walls)",
    "emitters and walls are mutually non-adjacent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "no_walls", "isolated_emitter")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "emitters_with_walls",
                       "valid": "emitters_with_walls"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n_walls = rng.randint(1, 3)
    for _ in range(n_walls):
        for _ in range(40):
            if rng.random() < 0.5:
                r = rng.randint(2, h - 3)
                c1 = rng.randint(1, w - 4)
                length = rng.randint(3, min(6, w - 1 - c1))
                cells = [(r, c) for c in range(c1, c1 + length)]
            else:
                c = rng.randint(2, w - 3)
                r1 = rng.randint(1, h - 4)
                length = rng.randint(3, min(6, h - 1 - r1))
                cells = [(r, c) for r in range(r1, r1 + length)]
            if any(p in used for p in cells): continue
            for r, c in cells: g[r][c] = 8
            used |= set(cells); break
    n_em = rng.randint(2, 4)
    for _ in range(n_em):
        for _ in range(60):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) in used: continue
            adj = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    adj = True; break
            if adj: continue
            g[r][c] = 2; used.add((r, c)); break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # Walls but no emitters — rule has no rays to count.
        for c in range(2, 6): g[3][c] = 8
        return g
    if name == "no_walls":
        # Emitters but no walls — every ray reaches a grid edge;
        # rule's "blocked" branch never fires.
        g[3][3] = 2
        g[5][7] = 2
        return g
    if name == "isolated_emitter":
        # Single emitter, walls placed so no two rays overlap any
        # cell — rule's count map collapses to all-1 (encoded as 2).
        g[4][4] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate isolated emitters plus blocking wall cells."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    emitters = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    wall_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not (2 <= len(emitters) <= 4):
        errs.append(f"expected 2-4 color-2 emitters, got {len(emitters)}")
    if len(wall_cells) < 3:
        errs.append("expected at least one wall segment of length >=3")
    for r, c in emitters:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
                errs.append("emitters must be isolated from non-background neighbors")
                return errs
    return errs
