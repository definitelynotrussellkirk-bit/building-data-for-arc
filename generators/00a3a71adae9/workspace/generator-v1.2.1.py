"""Generator for arc_puzzle_bank_21_set17_s:S17_H6 (task 00a3a71adae9).

THE RULE (what a solver must learn to see):
  Among the color-2 motifs, select the one whose one-cell square growth
  overlaps the color-1 mask cells the most; output that motif's tight
  crop recolored 8.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - scoring mask cells sit ONLY in the target's exclusive growth ring,
    so the winner is unique by construction (overlap >= 2 vs 0)
  - NOISE mask cells far from every motif (mask_noise axis) score zero
    for everyone — "the mask points at the target" beats "count the
    blue cells anywhere"
  - motifs may share a size (selection is by mask, not size); 2-4
    motifs of 2-6 cells on grids up to 12x14

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_motifs          nothing to select from
  - no_mask            no selection signal
  - mask_overlaps_all  the mask touches everyone equally (ambiguous)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00a3a71adae9"
VERSION = "1.2.1"
TASK_ID = "00a3a71adae9"

SUMMARY = (
    "2-4 separated color-2 motifs (2-6 cells each, sizes may repeat) "
    "plus color-1 mask cells inside exactly one motif's square-growth "
    "ring, with optional far-away noise mask cells that score zero for "
    "every motif; rule outputs the selected motif's tight crop in 8."
)

INVARIANTS = [
    "background is 0",
    "2-4 separated color-2 motifs",
    "scoring mask cells overlap exactly one motif's square growth",
    "noise mask cells (if any) overlap NO motif's growth",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "no_mask", "mask_overlaps_all")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..10 (hard 10..12)",
                   "valid": "6..12", "doc": "Grid height."},
    "grid_w":     {"type": "int", "default": "rng 10..12 (hard 12..14)",
                   "valid": "8..14", "doc": "Grid width."},
    "n":          {"type": "int", "default": "rng 2..3 (hard 3..4)",
                   "valid": "2..4", "doc": "Number of color-2 motifs."},
    "motif_size": {"type": "int", "default": "rng 2..6 per motif",
                   "valid": "2..6", "doc": "Cells per motif (sizes may repeat)."},
    "mask_cells": {"type": "int", "default": "rng 2..5",
                   "valid": "2..6", "doc": "Scoring mask cells in the target's ring."},
    "mask_noise": {"type": "int", "default": "rng 0..2",
                   "valid": "0..3", "doc": "Mask cells far from EVERY motif (score 0)."},
    "texture":    {"type": "enum", "default": "helpful",
                   "valid": "default|warm|cool|varied|no_motifs|no_mask|mask_overlaps_all",
                   "doc": "Set to a degenerate name to build a rule-hiding input."},
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


def _grown_square(cells, h, w):
    out = set()
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out.add((nr, nc))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(80):
        g = full_grid(h, w, 0)
        # sizes may REPEAT: same-size motifs prove selection is by mask
        sizes = [rng.randint(2, 6) for _ in range(n)]
        target_idx = rng.randrange(n)
        motifs = []
        ok = True
        for size in sizes:
            cells = _build_motif(rng, size)
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                placed_cells = []
                for r, c in cells:
                    pr, pc = r0 + r - min(rs), c0 + c - min(cs)
                    g[pr][pc] = 2
                    placed_cells.append((pr, pc))
                motifs.append(placed_cells)
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            target = motifs[target_idx]
            target_grown = _grown_square(target, h, w)
            other_grown = set()
            for i, cells in enumerate(motifs):
                if i != target_idx:
                    other_grown.update(_grown_square(cells, h, w))
            target_cells = set(target)
            candidates = sorted(
                p for p in target_grown
                if p not in target_cells and p not in other_grown and g[p[0]][p[1]] == 0
            )
            if len(candidates) < 2:
                continue
            mask_count = rng.randint(2, min(5, len(candidates)))
            for r, c in rng.sample(candidates, mask_count):
                g[r][c] = 1
            # noise mask cells: far from EVERY motif's growth — they score
            # zero overlap for all candidates, so the winner is unchanged,
            # but "count all blue cells anywhere" stops working
            all_grown = set(target_grown) | other_grown
            far = sorted(
                (r, c) for r in range(h) for c in range(w)
                if g[r][c] == 0 and (r, c) not in all_grown
            )
            n_noise = rng.randint(0, min(2, len(far)))
            if far and n_noise:
                for r, c in rng.sample(far, n_noise):
                    g[r][c] = 1
            return g
    raise ValueError("could not realize layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """2-4 color-2 motifs; at least 2 color-1 mask cells; bg=0."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    motif_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    mask_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    # find 4-connected components of color-2
    seen = set()
    motifs = []
    for sr, sc in motif_cells:
        if (sr, sc) in seen:
            continue
        stack = [(sr, sc)]
        seen.add((sr, sc))
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        motifs.append(comp)
    if not (2 <= len(motifs) <= 4):
        errors.append(f"expected 2-4 color-2 motifs, found {len(motifs)}")
    if len(mask_cells) < 2:
        errors.append(f"expected >=2 color-1 mask cells, found {len(mask_cells)}")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — still diverse (sizes, motifs, placements vary)."""
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 10, 12)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Only mask cells — selector has no candidates.
        for _ in range(rng.randint(2, 4)):
            g[rng.randrange(h)][rng.randrange(w)] = 1
        return g

    def drop_motif(anchor_r, anchor_c):
        cells = _build_motif(rng, rng.randint(2, 4))
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        for r, c in cells:
            pr = min(h - 1, max(0, anchor_r + r - min(rs)))
            pc = min(w - 1, max(0, anchor_c + c - min(cs)))
            g[pr][pc] = 2

    if name == "no_mask":
        # Motifs but no mask — selector has no signal.
        drop_motif(rng.randint(0, h // 2 - 1), rng.randint(0, w // 2 - 1))
        drop_motif(rng.randint(h // 2, h - 3), rng.randint(w // 2, w - 3))
        return g
    # mask_overlaps_all: two motifs, mask centered between them
    drop_motif(1, 1)
    drop_motif(1, w - 4)
    mid = w // 2
    for r in (h // 2, h // 2 + 1):
        g[r][mid] = 1
    return g
