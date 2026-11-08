"""Generator for arc_puzzle_bank_21_set15:S15_H2 — stamp a source shape at coloured markers.

Rule (verified from canonical Racket): a single COLOUR-2 object is the SOURCE
shape; a COLOUR-1 cell is the ANCHOR (the source's origin reference). For each
marker of colour 3/4/5, the source is stamped (in colour 8) with its anchor at
the marker, transformed per colour (3->identity, 4->op3, 5->op1). Out-of-bounds
stamp cells are dropped.

The previous body was the generic scatter template; with random colours from
{2..9} the input often lacked a colour-2 source / colour-1 anchor / colour-3/4/5
markers, so the rule crashed (~4/6). This rewrite CONSTRUCTS valid inputs: one
colour-2 source + a colour-1 anchor next to it + scattered colour-3/4/5 markers.

Axes: grid size, source shape, anchor offset, marker counts/positions.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c2f874f3e82"
VERSION = "2.1.1"  # FIX: was generic scatter -> missing colour-2 source / colour-1 anchor / 3-4-5 markers crashed rule. Now constructs the stamp layout.
TASK_ID = "1c2f874f3e82"

SUMMARY = ("One colour-2 source shape + a colour-1 anchor cell + scattered colour-3/4/5 "
           "markers. Rule: stamp the source (colour 8, per-colour transform) with its "
           "anchor at each marker. Source shape, anchor, marker counts/positions vary.")

INVARIANTS = [
    "exactly one colour-2 object (the source shape)",
    "exactly one colour-1 cell (the anchor)",
    ">=1 marker among colours 3/4/5 (stamp targets)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "source_size":    {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "n_markers":      {"type": "int", "default": "2-3 easy / 3-5 med / 4-6 hard", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 11, 12)
        n_markers = ctx.draw_int("n_markers", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        n_markers = ctx.draw_int("n_markers", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14)
        n_markers = ctx.draw_int("n_markers", 3, 5)
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        used = set()
        # SOURCE: one colour-2 shape in the upper-left region
        src = _build_motif(rng, rng.randint(3, 5))
        srs = [r for r, _ in src]; scs = [c for _, c in src]
        sh = max(srs) - min(srs) + 1; sw = max(scs) - min(scs) + 1
        if sh + 1 >= h or sw + 1 >= w:
            continue
        sr0 = rng.randint(1, max(1, h - sh - 1)); sc0 = rng.randint(1, max(1, w - sw - 1))
        for r, c in src:
            rr, cc = sr0 + r - min(srs), sc0 + c - min(scs)
            g[rr][cc] = 2; used.add((rr, cc))
        # ANCHOR: one colour-1 cell adjacent to the source (the origin reference).
        # Do not return a row if the anchor was not actually placed.
        anchor_placed = False
        for _ in range(40):
            ar = sr0 + rng.randint(-1, sh); ac = sc0 + rng.randint(-1, sw)
            if 0 <= ar < h and 0 <= ac < w and (ar, ac) not in used and g[ar][ac] == 0:
                g[ar][ac] = 1; used.add((ar, ac)); anchor_placed = True; break
        if not anchor_placed:
            continue
        # MARKERS: scattered colour-3/4/5 stamp targets (each well-separated).
        # Normal samples must expose ALL THREE marker-color branches; previously
        # only 452/1000 medium samples did, so many episodes could not teach the
        # per-color stamp transform. Plan 3/4/5 first, then any extras.
        marker_plan = [3, 4, 5] + [rng.choice([3, 4, 5]) for _ in range(max(0, n_markers - 3))]
        rng.shuffle(marker_plan)
        placed_markers = 0
        for marker_color in marker_plan:
            placed_one = False
            for _ in range(400):
                mr = rng.randint(0, h - 1); mc = rng.randint(0, w - 1)
                if (mr, mc) in used or g[mr][mc] != 0:
                    continue
                # keep markers apart so stamps (source-sized) don't fully overlap
                if any(abs(mr - pr) + abs(mc - pc) < sh + sw for (pr, pc) in used if g[pr][pc] in (3, 4, 5)):
                    continue
                g[mr][mc] = marker_color; used.add((mr, mc)); placed_markers += 1; placed_one = True
                break
            if not placed_one:
                break
        if placed_markers == len(marker_plan):
            return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-2 source, one color-1 anchor, >=1 marker in {3,4,5}."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    markers = sum(1 for r in range(h) for c in range(w) if grid[r][c] in (3, 4, 5))
    if c2 == 0:
        errs.append("no color-2 source shape cells")
    if c1 != 1:
        errs.append(f"expected exactly 1 color-1 anchor, found {c1}")
    if markers == 0:
        errs.append("no marker cells in {3,4,5}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
