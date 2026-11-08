"""Generator for arc_puzzle_bank_sixth_21_bundle:hard_36_local_diagonal_rays_in_frames.

From color-2 seeds inside color-5 hollow frames, draw bounded diagonal
rays (color 8) that stay inside the frame interior and stop at color-6
blockers (and at the frame border). The seed cell itself becomes 8.

Combinatorial axes: grid size, number of frames (1-3) + their
sizes/positions, each frame's seed position, and its color-6 blockers.
Degenerates: no_seed, no_frame, seed_outside_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "59c1ad6d4a45"
VERSION = "3.0.0"  # diversity: N random frames (size/pos) + seeds + blockers + grid (was fixed 8x15)
TASK_ID = "59c1ad6d4a45"
SUMMARY = (
    "0-bg grid (size varies). 1-3 color-5 (gray) hollow rectangular "
    "FRAMES (>=5 per side so each interior is >=3x3) at random "
    "sizes/positions, placed apart. Each frame interior holds one color-2 "
    "(red) SEED and 0-2 color-6 (magenta) BLOCKERS; an optional distractor "
    "sits outside. Rule: from each seed emit 4 DIAGONAL RAYS painting "
    "color 8 (the seed becomes 8 too), bounded by the frame interior and "
    "stopping at color-6 blockers (preserved) and the frame border. The "
    "grid size, frame count, frame sizes/positions, seed positions and "
    "blockers all vary freely (was a fixed 8x15 grid with 5 blocker "
    "presets)."
)

INVARIANTS = [
    "1-3 non-touching color-5 hollow frames, each interior >=3x3",
    "each frame interior has exactly one color-2 seed and 0-2 color-6 blockers",
    "diagonal rays stay inside the interior and stop at blockers/border",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seed", "no_frame", "seed_outside_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "varies", "valid": "varies"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "no_seed|no_frame|seed_outside_frame"},
}


def _reserve_bbox(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, nfr, szr, nbr = (9, 11), (10, 13), (1, 2), (5, 7), (0, 1)
    elif difficulty == "hard":
        hr, wr, nfr, szr, nbr = (14, 18), (15, 20), (2, 3), (5, 9), (1, 2)
    else:
        hr, wr, nfr, szr, nbr = (11, 15), (12, 16), (1, 2), (5, 8), (1, 2)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        placed = 0
        n_frames = rng.randint(*nfr)
        for _ in range(n_frames):
            for _t in range(40):
                fh = rng.randint(*szr); fw = rng.randint(*szr)
                if fh > h or fw > w:
                    continue
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                if not _reserve_bbox(occ, top, left, fh, fw, h, w):
                    continue
                draw_frame(g, top, left, top + fh - 1, left + fw - 1, 5)
                # interior cells
                interior = [(r, c) for r in range(top + 1, top + fh - 1)
                            for c in range(left + 1, left + fw - 1)]
                seed_cell = rng.choice(interior)
                g[seed_cell[0]][seed_cell[1]] = 2
                rest = [p for p in interior if p != seed_cell]
                nb = min(rng.randint(*nbr), len(rest))
                for (br, bc) in rng.sample(rest, nb):
                    g[br][bc] = 6
                placed += 1
                break
        if placed < 1:
            continue

        # optional distractor outside frames (rule ignores it)
        if rng.random() < 0.5:
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if not occ[r][c]:
                    g[r][c] = rng.choice([3, 7, 9])
                    break
        return g

    raise ValueError("could not realize at least one valid frame layout")


def _components4(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _frame_box(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return (r0, c0, r1, c1), border


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = sorted({v for row in grid for v in row if v not in (0, 2, 3, 5, 6, 7, 9)})
    if bad:
        errs.append(f"unexpected colors present: {bad}")
    frames = []
    for cells in _components4(grid, 5):
        box, border = _frame_box(cells)
        r0, c0, r1, c1 = box
        if set(cells) != border:
            errs.append("color-5 component must be a hollow rectangular frame")
            continue
        if (r1 - r0 + 1) < 5 or (c1 - c0 + 1) < 5:
            errs.append("frame interior must be at least 3x3")
        frames.append(box)
    if not frames:
        errs.append("default board must contain at least one color-5 frame")
    for i, a in enumerate(frames):
        ar0, ac0, ar1, ac1 = a
        for b in frames[i + 1:]:
            br0, bc0, br1, bc1 = b
            if not (ar1 + 1 < br0 or br1 + 1 < ar0 or ac1 + 1 < bc0 or bc1 + 1 < ac0):
                errs.append("frames must be non-touching with a one-cell gap")
                break
    all_seeds = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    all_blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6}
    covered_seeds = set()
    covered_blockers = set()
    for r0, c0, r1, c1 in frames:
        interior = {(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)}
        seeds = all_seeds & interior
        blockers = all_blockers & interior
        covered_seeds |= seeds
        covered_blockers |= blockers
        if len(seeds) != 1:
            errs.append("each frame interior must contain exactly one color-2 seed")
        if len(blockers) > 2:
            errs.append("each frame interior must contain at most two color-6 blockers")
    if covered_seeds != all_seeds:
        errs.append("all color-2 seeds must lie inside frame interiors")
    if covered_blockers != all_blockers:
        errs.append("all color-6 blockers must lie inside frame interiors")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 15, 0)
    if name == "no_seed":
        draw_frame(g, 0, 0, 6, 6, 5)
        return g
    if name == "no_frame":
        g[3][3] = 2
        return g
    if name == "seed_outside_frame":
        draw_frame(g, 0, 0, 6, 6, 5)
        g[7][10] = 2
        return g
    return g
