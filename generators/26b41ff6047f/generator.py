"""Generator for arc_puzzle_bank_21_set15_bundle:hard_o05 — match guide, stamp at anchors.

Rule: a color-9 guide motif. Single-cell color-8 anchors. Among other motifs,
one matches the guide's shape (modulo dihedral). The output stamps that
motif at every anchor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_guide (no color-9 guide → rule has no shape to
match against); no_anchors (guide + match present but no color-8
anchors → no stamps placed); no_match (guide present but no
candidate matches its dihedral class → rule's selector returns
nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26b41ff6047f"
VERSION = "1.1.1"
TASK_ID = "26b41ff6047f"

SUMMARY = "Color-9 guide + 2-3 color-8 anchors + 2-3 candidate motifs (one matches guide shape)."

INVARIANTS = [
    "background is 0",
    "exactly one color-9 guide motif (3-5 cells)",
    "2-3 single-cell color-8 anchors at distinct positions",
    "2-3 candidate motifs in distinct non-{0, 8, 9} colors; at least one matches guide under dihedral",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_guide", "no_anchors", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 10..12", "valid": "9..15"},
    "grid_w":            {"type": "int", "default": "rng 14..16", "valid": "12..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "guide_anchors_candidates",
                          "valid": "guide_anchors_candidates"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_guide|no_anchors|no_match"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-9 guide cell; ≥1 color-8 anchor cell; ≥1 candidate (non-{0,8,9})."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    has_9 = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    has_8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    has_cand = any(grid[r][c] not in (0, 8, 9) for r in range(h) for c in range(w))
    if not has_9 and not has_8 and not has_cand:
        return errors  # degenerate — allowed
    if not has_9:
        errors.append("no color-9 guide cells")
    if not has_8:
        errors.append("no color-8 anchor cells")
    if not has_cand:
        errors.append("no candidate motif cells (non-{0,8,9} colors)")
    return errors


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


def _normalize(cells):
    cs = list(cells)
    rmin = min(r for r, _ in cs); cmin = min(c for _, c in cs)
    return sorted((r - rmin, c - cmin) for r, c in cs)


def _rot(cells):
    return [(c, -r) for r, c in cells]


def _flip(cells):
    return [(r, -c) for r, c in cells]


def _variants(cells):
    out = set()
    cur = list(cells)
    for _ in range(4):
        out.add(tuple(_normalize(cur))); cur = _rot(cur)
    cur = _flip(cells)
    for _ in range(4):
        out.add(tuple(_normalize(cur))); cur = _rot(cur)
    return [list(v) for v in out]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 14, 15)
        n_anchors = ctx.draw_int("n_anchors", 2, 2)
        n_others = ctx.draw_int("n_others", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 15, 16)
        n_anchors = ctx.draw_int("n_anchors", 3, 3)
        n_others = ctx.draw_int("n_others", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 14, 16)
        n_anchors = ctx.draw_int("n_anchors", 2, 3)
        n_others = ctx.draw_int("n_others", 1, 2)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        guide = _normalize(_build_motif(rng, rng.randint(3, 5)))
        gh = max(r for r, _ in guide) + 1; gw = max(c for _, c in guide) + 1
        placed = False
        for _ in range(80):
            r0 = rng.randint(0, h - gh); c0 = rng.randint(0, w - gw)
            if not _free(g, r0, c0, r0 + gh - 1, c0 + gw - 1): continue
            for r, c in guide:
                g[r0 + r][c0 + c] = 9
            placed = True; break
        if not placed:
            continue
        match_v = rng.choice(_variants(guide))
        mh = max(r for r, _ in match_v) + 1; mw = max(c for _, c in match_v) + 1
        match_color = rng.choice([1, 2, 3, 4, 5, 6, 7])
        placed_m = False
        for _ in range(80):
            r0 = rng.randint(0, h - mh); c0 = rng.randint(0, w - mw)
            if not _free(g, r0, c0, r0 + mh - 1, c0 + mw - 1): continue
            for r, c in match_v:
                g[r0 + r][c0 + c] = match_color
            placed_m = True; break
        if not placed_m:
            continue
        used = {match_color}
        for _ in range(n_others):
            for _t in range(40):
                ocells = _normalize(_build_motif(rng, rng.randint(2, 4)))
                if tuple(ocells) in {tuple(v) for v in _variants(guide)}: continue
                oh = max(r for r, _ in ocells) + 1; ow = max(c for _, c in ocells) + 1
                color = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7] if c not in used])
                for _t2 in range(40):
                    r0 = rng.randint(0, h - oh); c0 = rng.randint(0, w - ow)
                    if not _free(g, r0, c0, r0 + oh - 1, c0 + ow - 1): continue
                    for r, c in ocells:
                        g[r0 + r][c0 + c] = color
                    used.add(color)
                    break
                break
        for _ in range(n_anchors):
            for _t in range(80):
                r = rng.randint(0, h - gh); c = rng.randint(0, w - gw)
                if g[r][c] != 0: continue
                if any(g[r + dr][c + dc] != 0 for dr in range(-1, 2) for dc in range(-1, 2)
                       if 0 <= r + dr < h and 0 <= c + dc < w):
                    continue
                g[r][c] = 8
                break
        return g
    raise ValueError("could not realize set15 o05 layout")


def _draw_from_degenerate(name, rng):
    h, w = 11, 15
    g = full_grid(h, w, 0)
    if name == "no_guide":
        # No color-9 guide — rule has no shape to match.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 4
        g[6][6] = 8; g[7][12] = 8
        return g
    if name == "no_anchors":
        # Guide + matching candidate but no color-8 anchors — no stamps.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 9
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[6 + dr][8 + dc] = 4
        return g
    if name == "no_match":
        # Guide is L-tromino but distractors are all 2x2 / lines — no candidate matches.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 9
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[5 + dr][6 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (0, 2)]:
            g[8 + dr][10 + dc] = 5
        g[5][13] = 8; g[8][1] = 8
        return g
    return g
