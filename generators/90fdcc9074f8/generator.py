"""Generator for arc_puzzle_bank_21_set24_s:S24_H2.

Rule: three equal-size panels are separated by full color-9 columns.  A
cell belongs to the repaired shape when at least two panels mark that
position; output is the majority-repaired mask/depth map under the
canonical Racket rule.

Combinatorial axes: panel_h/w, connected mask size, panel noise,
palette, and difficulty.  Degenerates keep the legacy texture names but
are intentionally non-normal branch-hiding cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "90fdcc9074f8"
VERSION = "1.2.1"
TASK_ID = "90fdcc9074f8"

SUMMARY = "Three same-size color panels separated by color-9 columns; noisy panel disagreements are majority-repaired by the rule."

INVARIANTS = [
    "exactly three equal-size panels separated by two full color-9 columns",
    "the majority-occupied mask is non-empty",
    "input uses the canonical sparse palette {0,1,9}; output derives ring/depth colours",
    "at least one panel disagreement makes the majority-repair rule visible",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "motifs_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 5..8", "valid": "5..9"},
    "panel_w":        {"type": "int", "default": "rng 5..8", "valid": "5..9"},
    "mask_cells":     {"type": "int", "default": "rng 7..12", "valid": "6..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "panel_noise":    {"type": "str", "default": "one deletion + one false positive",
                       "valid": "majority-preserving"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 5, 6)
        pw = ctx.draw_int("panel_w", 5, 6)
        k = rng.randint(6, 8)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 7, 9)
        pw = ctx.draw_int("panel_w", 7, 9)
        k = rng.randint(10, 15)
    else:
        ph = ctx.draw_int("panel_h", 5, 8)
        pw = ctx.draw_int("panel_w", 5, 8)
        k = rng.randint(7, 12)

    for _layout_attempt in range(80):
        mask = _connected_mask(rng, ph, pw, k)
        if not mask:
            continue
        panels = []
        true_cells = [(r, c) for r in range(ph) for c in range(pw) if mask[r][c]]
        false_cells = [(r, c) for r in range(ph) for c in range(pw) if not mask[r][c]]
        # Canonical inputs use a binary foreground mask in each panel (only
        # colours 0/1 plus separator 9).  Earlier versions randomized each
        # foreground cell over 1..8, exploding palette size/object-count while
        # teaching the same occupancy rule.
        fg = 1
        for i in range(3):
            panel = full_grid(ph, pw, 0)
            for r, c in true_cells:
                panel[r][c] = fg
            panels.append(panel)
        # One missing true cell in one panel and one one-panel false positive make
        # the majority-repair branch visible while preserving the recovered mask.
        if true_cells:
            r, c = rng.choice(true_cells)
            panels[rng.randrange(3)][r][c] = 0
        if false_cells:
            r, c = rng.choice(false_cells)
            panels[rng.randrange(3)][r][c] = fg
        if _majority_mask(panels) != mask:
            continue
        g = full_grid(ph, 3 * pw + 2, 0)
        for r in range(ph):
            g[r][pw] = 9
            g[r][2 * pw + 1] = 9
        for idx, panel in enumerate(panels):
            left = idx * (pw + 1)
            for r in range(ph):
                for c in range(pw):
                    g[r][left + c] = panel[r][c]
        return g
    raise ValueError("could not realize majority-repair panels")


def _connected_mask(rng, h, w, k):
    k = min(k, h * w - 1)
    r0 = rng.randrange(h)
    c0 = rng.randrange(w)
    cells = [(r0, c0)]
    seen = {(r0, c0)}
    for _ in range(400):
        if len(cells) >= k:
            break
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen:
            seen.add((nr, nc))
            cells.append((nr, nc))
    if len(cells) < max(4, min(k, h * w)):
        return None
    mask = [[False] * w for _ in range(h)]
    for r, c in cells:
        mask[r][c] = True
    return mask


def _split_panels(grid):
    h, w = len(grid), len(grid[0])
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(sep_cols) != 2:
        return []
    starts = [0, sep_cols[0] + 1, sep_cols[1] + 1]
    ends = [sep_cols[0], sep_cols[1], w]
    return [[row[starts[i]:ends[i]] for row in grid] for i in range(3)]


def _majority_mask(panels):
    if len(panels) != 3:
        return []
    h, w = len(panels[0]), len(panels[0][0])
    return [[sum(1 for p in panels if p[r][c] not in (0, 9)) >= 2
             for c in range(w)] for r in range(h)]


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    panels = _split_panels(grid)
    if len(panels) != 3:
        return ["expected exactly three panels separated by two full color-9 columns"]
    shapes = {(len(p), len(p[0])) for p in panels}
    if len(shapes) != 1:
        msgs.append(f"panels must share dimensions; got {shapes}")
    maj = _majority_mask(panels)
    if not any(any(row) for row in maj):
        msgs.append("majority mask should be non-empty")
    used = {v for row in grid for v in row}
    if not used <= {0, 1, 9}:
        msgs.append(f"unexpected input palette {sorted(used)}; expected subset of {{0,1,9}}")
    disagreements = 0
    h, w = len(panels[0]), len(panels[0][0])
    for r in range(h):
        for c in range(w):
            occ = [p[r][c] not in (0, 9) for p in panels]
            if len(set(occ)) > 1:
                disagreements += 1
    if disagreements < 1:
        msgs.append("expected at least one noisy panel disagreement for majority repair")
    return msgs

def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    if name == "motifs_touching":
        g[2][2] = 4; g[2][3] = 4; g[3][3] = 4
        g[3][4] = 5; g[4][4] = 5
        return g
    return g
