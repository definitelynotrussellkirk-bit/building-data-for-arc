"""Generator for arc_additional_puzzles_21_set20_bundle:H138.

Rule: two command cells transform the cropped motif: cw, 180,
left-right, up-down, or transpose.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_choice,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_commands, no_motif, square_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3550b85c52f2"
VERSION = "3.1.0"  # distinct=16: motif came from a FIXED bank. Output = motif crop under two dihedral transforms (cmd1@(0,0), cmd2@(0,1)). Now RANDOM connected multicolour motif (3-7 cells) -> many more distinct transformed outputs.
TASK_ID = "3550b85c52f2"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) with: (a) cells (0,0) and "
    "(0,1) = TWO TRANSFORM COMMAND values in {1..5}; (b) one "
    "MOTIF (3-5 connected cells in 2-3 colors) placed in the "
    "interior, away from (0,0)/(0,1). Rule: read cmd1 = "
    "grid[0][0], cmd2 = grid[0][1]. Clear those two cells. "
    "Crop the rest to its non-zero bbox (the motif). Apply "
    "cmd1 then cmd2 in order, each chosen by code: 1 = rot-"
    "CW, 2 = 180°, 3 = flip-LR, 4 = flip-UD, 5+ = transpose. "
    "Output: motif after both transforms applied."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "commands live in cells (0,0) and (0,1)",
    "the motif is separated from command cells and has a non-square bounding box",
    "both commands are in {1..5}",
    "the two commands are usually different (composed effect is observable)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_commands", "no_motif", "square_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motif_choice":   {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "command_top_left",
                       "valid": "command_top_left"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


MOTIFS = (
    ((0, 0, 6), (0, 1, 6), (1, 1, 7), (2, 1, 7)),
    ((0, 2, 5), (1, 0, 8), (1, 1, 8), (1, 2, 5), (2, 0, 8)),
)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cmd1 = rng.randint(1, 5)
    cmd2 = rng.randint(1, 5)
    if cmd2 == cmd1:
        cmd2 = (cmd2 % 5) + 1
    g[0][0] = cmd1        # cmd1 (dihedral transform code)
    g[0][1] = cmd2        # cmd2
    # RANDOM connected multicolour motif (was a fixed bank -> distinct=16); output
    # is this motif crop transformed by cmd1 then cmd2, so varied motif -> varied out.
    norm = _rand_motif(rng, rng.randint(3, 7), h - 2, w - 2)
    mh = max(r for r, _ in norm) + 1; mw = max(c for _, c in norm) + 1
    top = rng.randint(1, h - mh - 1)
    left = rng.randint(1, w - mw - 1)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, min(3, len(norm))))
    colors = [palette[0], palette[1]] + [rng.choice(palette) for _ in range(len(norm) - 2)]
    rng.shuffle(colors)
    for (dr, dc), color in zip(norm, colors):
        g[top + dr][left + dc] = color
    return g


def _normalize(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rand_motif(rng, k, max_h, max_w):
    """Connected motif with non-square bbox that fits the interior canvas."""
    fallback = [(0, 0), (1, 0), (1, 1), (2, 1)]  # 3x2, connected, non-square
    if max_h < 3 or max_w < 2:
        return [(0, 0), (0, 1), (1, 1)]
    for _ in range(120):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nb = (r + dr, c + dc)
            if nb not in seen:
                cells.append(nb)
                seen.add(nb)
        norm = _normalize(cells)
        mh = max(r for r, _ in norm) + 1
        mw = max(c for _, c in norm) + 1
        if mh != mw and mh <= max_h and mw <= max_w:
            return norm
    return fallback


def _component_count(cells):
    cells = set(cells)
    if not cells:
        return 0
    seen = set()
    comps = 0
    for cell in list(cells):
        if cell in seen:
            continue
        comps += 1
        stack = [cell]
        seen.add(cell)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    cmds = [grid[0][0], grid[0][1] if w > 1 else 0]
    if any(v not in {1, 2, 3, 4, 5} for v in cmds):
        errors.append(f"command cells must be in 1..5, found {cmds}")
    if cmds[0] == cmds[1]:
        errors.append("two command cells should differ so the composition is visible")
    motif = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] != 0 and (r, c) not in {(0, 0), (0, 1)}]
    if len(motif) < 3:
        errors.append(f"motif must have at least 3 cells, found {len(motif)}")
        return errors
    if _component_count(motif) != 1:
        errors.append("motif must be one 4-connected component")
    rs = [r for r, _ in motif]
    cs = [c for _, c in motif]
    bh, bw = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
    if bh == bw:
        errors.append(f"motif bbox must be non-square, found {bh}x{bw}")
    if min(rs) == 0:
        errors.append("motif must be separated from the command row")
    colors = {grid[r][c] for r, c in motif}
    if len(colors) < 2:
        errors.append("motif must use at least two colors")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "missing_commands":
        # cells (0,0) and (0,1) empty → no transform commands to apply
        motif = ((0, 0, 6), (0, 1, 6), (1, 1, 7), (2, 1, 7))
        for dr, dc, color in motif:
            g[3 + dr][4 + dc] = color
        return g
    if name == "no_motif":
        # commands present but no motif body → nothing to transform
        g[0][0] = 3
        g[0][1] = 5
        return g
    if name == "square_motif":
        # motif's bounding box is square → cw / transpose / 180 may produce identical results
        g[0][0] = 3
        g[0][1] = 5
        for dr in range(3):
            for dc in range(3):
                if (dr + dc) % 2 == 0:
                    g[3 + dr][4 + dc] = 6
        return g
    return g
