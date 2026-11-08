"""Generator for e6721834.

Rule: split the grid into halves (the axis with the larger non-bg
imbalance); the denser half is the SOURCE (multi-color objects), the
sparser is the TARGET (sparse anchor markers). For each source object,
find the translation aligning its anchor-color cells onto target markers
of that color, and stamp the whole object there (greedy, non-overlapping)
on a target-sized output.

This generator forces a vertical split (h odd) with a denser left half of
objects -- each object having a single UNIQUE anchor color matched by one
target marker -- so every object stamps at a disjoint target footprint.

Combinatorial axes: grid size, the object shapes/colors, the anchor
colors, and the target footprints.
Degenerates: no_source, no_target, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd39d31edb3c"
RULE_HASH = "fc1d5ce5e89e"  # canonical rule this generator was written against
VERSION = "2.1.0"  # wider grids + more objects (up to 5) + bigger shapes
TASK_ID = "fd39d31edb3c"
SUMMARY = (
    "Two-half grid (size varies, h odd -> vertical split). The denser LEFT "
    "half holds multi-color objects, each with a unique anchor color; the "
    "sparser RIGHT half holds one matching anchor marker per object. Rule: "
    "stamp each object onto its marker (aligning the anchor cell), on a "
    "half-width output. The grid size, object shapes/colors, anchor colors "
    "and marker footprints vary freely (was a fixed setup, ~23 distinct)."
)

INVARIANTS = [
    "h is odd and w even so the rule splits vertically; the left half is denser",
    "each object has one unique anchor color matched by exactly one right-half marker",
    "object footprints in the target are disjoint so all stamp",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_target", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies odd", "valid": "9..21 odd"},
    "grid_w":         {"type": "int", "default": "varies even", "valid": "16..28 even"},
    "n_objects":      {"type": "int", "default": "varies", "valid": "1..3"},
    "obj_size":       {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "left_objects_right_markers",
                       "valid": "left_objects_right_markers"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_source|no_target|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _release(occ, top, left, sh, sw):
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, half_wr, nr, ss = (9, 13), (7, 10), (1, 2), (3, 4)
    elif difficulty == "hard":
        hr, half_wr, nr, ss = (17, 27), (11, 15), (3, 5), (4, 7)
    else:
        hr, half_wr, nr, ss = (11, 19), (8, 12), (2, 4), (3, 5)

    for _attempt in range(40):
        h = rng.randint(*hr) | 1                 # force odd -> vertical split
        hw = rng.randint(*half_wr)               # half width
        w = hw * 2
        SB, TB = rng.sample(range(10), 2)        # left bg, right bg
        anchors_pool = [c for c in range(10) if c not in (SB, TB)]
        rng.shuffle(anchors_pool)
        body_pool = [c for c in range(10) if c not in (SB, TB)]

        K = rng.randint(*nr)
        if K > len(anchors_pool):
            continue
        anchor_colors = anchors_pool[:K]
        body_colors = [c for c in body_pool if c not in anchor_colors]
        if not body_colors:
            continue

        g_left = [[SB] * hw for _ in range(h)]
        g_right = [[TB] * hw for _ in range(h)]
        occ_l = [[False] * hw for _ in range(h)]
        occ_r = [[False] * hw for _ in range(h)]
        placed = 0
        for i in range(K):
            shape = _poly(rng, rng.randint(*ss))
            sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
            if sh + 1 > h or sw + 1 > hw:
                continue
            A = anchor_colors[i]
            anchor_idx = rng.randrange(len(shape))
            colored = []
            for j, (lr, lc) in enumerate(shape):
                colored.append((lr, lc, A if j == anchor_idx else rng.choice(body_colors)))
            oar, oac = shape[anchor_idx]

            # Reserve both panels before painting either one.  The old code
            # painted the source object first and, when the target marker failed
            # to place, left an unpaired source template in the input.
            ok_src = False
            src_pos = None
            for _t in range(40):
                sr = rng.randint(0, h - sh); sc = rng.randint(0, hw - sw)
                if _reserve(occ_l, sr, sc, sh, sw, h, hw):
                    ok_src = True; src_pos = (sr, sc); break
            if not ok_src:
                continue
            ok_tgt = False
            tgt_pos = None
            for _t in range(40):
                tr = rng.randint(0, h - sh); tc = rng.randint(0, hw - sw)
                if _reserve(occ_r, tr, tc, sh, sw, h, hw):
                    ok_tgt = True; tgt_pos = (tr, tc); break
            if not ok_tgt:
                _release(occ_l, src_pos[0], src_pos[1], sh, sw)
                continue
            sr, sc = src_pos
            tr, tc = tgt_pos
            for (lr, lc, col) in colored:
                g_left[sr + lr][sc + lc] = col
            g_right[tr + oar][tc + oac] = A
            placed += 1

        if placed < 1:
            continue
        # assemble full grid: left | right
        g = full_grid(h, w, 0)
        for r in range(h):
            for c in range(hw):
                g[r][c] = g_left[r][c]
                g[r][c + hw] = g_right[r][c]
        return g

    return g   # fallback (rare)



def _non_bg_components(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != bg):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    h, w = len(grid), len(grid[0])
    errors = []
    if w % 2 != 0:
        return ["grid width must split into equal source/target panels"]
    hw = w // 2
    left = [row[:hw] for row in grid]
    right = [row[hw:] for row in grid]
    from collections import Counter
    src_bg = Counter(v for row in left for v in row).most_common(1)[0][0]
    tgt_bg = Counter(v for row in right for v in row).most_common(1)[0][0]
    target_colors = {v for row in right for v in row if v != tgt_bg}
    comps = _non_bg_components(left, src_bg)
    expected = {"easy": (1, 2), "hard": (3, 5)}.get(difficulty, (2, 4))
    if not (expected[0] <= len(target_colors) <= expected[1]):
        errors.append(f"expected {expected[0]}-{expected[1]} target markers, got {len(target_colors)}")
    if len(comps) < len(target_colors):
        errors.append(f"source components fewer than target markers: {len(comps)} vs {len(target_colors)}")
    for cells in comps:
        colors = {left[r][c] for r, c in cells if left[r][c] != src_bg}
        if colors.isdisjoint(target_colors):
            errors.append(f"source component colors {sorted(colors)} have no matching target marker")
            break
    return errors

def _draw_from_degenerate(name, rng):
    h, w = 9, 16
    g = full_grid(h, w, 6)
    for r in range(h):
        for c in range(8, 16):
            g[r][c] = 1
    g[2][1] = 3; g[2][2] = 8; g[3][1] = 3      # left object (anchor 8)
    g[5][12] = 8                                # right marker
    if name == "no_source":
        return full_grid(h, w, 6)
    if name == "no_target":
        for r in range(h):
            for c in range(8, 16):
                g[r][c] = 1
        return g
    if name == "full_grid":
        return full_grid(h, w, 3)
    return g
