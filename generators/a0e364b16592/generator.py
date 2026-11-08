"""Generator for arc_puzzle_bank_21_set5_e:medium_e02 — blocker gravity scenes.

Rule: non-5 colored cells fall to the bottom of each column segment; color 5 is
a fixed divider/barrier. Every ordinary draw includes a blocker with payload on
both sides, so segment-aware gravity is observable.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0e364b16592"
VERSION = "1.3.0"
TASK_ID = "a0e364b16592"

SUMMARY = "2-5 separated non-5 motifs plus a color-5 blocker with payload above and below."

INVARIANTS = [
    "background is 0",
    "at least two connected non-{0,5} motifs",
    "color 5 is reserved for fixed separators/barriers",
    "every ordinary draw has payload above and below a color-5 blocker in one column",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "palette_size": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias": {"type": "str", "default": "scattered_colored_motifs", "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    seen = [[False] * w for _ in range(h)]
    blobs = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (0, 5) and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] not in (0, 5):
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                blobs += 1
    if blobs < 2:
        errs.append(f"expected >=2 non-{{0,5}} motifs, found {blobs}")
    blockers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not blockers:
        errs.append("expected at least one color-5 blocker")
    elif not any(
        any(grid[rr][c] not in (0, 5) for rr in range(r))
        and any(grid[rr][c] not in (0, 5) for rr in range(r + 1, h))
        for r, c in blockers
    ):
        errs.append("expected payload above and below a blocker in one column")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for _ in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n)
        blocker_r = rng.randint(3, h - 4)
        blocker_c = rng.randint(1, w - 2)
        g[blocker_r][blocker_c] = 5
        upper = [(blocker_r - 3, blocker_c), (blocker_r - 2, blocker_c), (blocker_r - 2, blocker_c + 1)]
        lower = [(blocker_r + 2, blocker_c), (blocker_r + 3, blocker_c), (blocker_r + 3, blocker_c - 1)]
        for r, c in upper:
            g[r][c] = colors[0]
        for r, c in lower:
            g[r][c] = colors[1]

        ok = True
        for color in colors[2:]:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1
            sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok and not self_check(g, difficulty=difficulty):
            return g
    raise ValueError("could not realize blocker-aware layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]:
            g[r][c] = 4
        return g
    if name == "all_same_color":
        for r, c in [(1, 1), (1, 2), (2, 2), (5, 6), (5, 7), (6, 7), (8, 1), (8, 2), (9, 2)]:
            g[r][c] = 4
        return g
    return g
