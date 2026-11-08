"""Generator for arc_puzzle_bank_21_set4_d:hard_d01 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0498cb707356"
VERSION = "3.1.0"  # add executable size-ordering invariants
TASK_ID = "0498cb707356"

SUMMARY = (
    "0-bg grid with 4-5 non-touching motifs (distinct colors, sizes "
    "3-6 mostly distinct); rule sorts objects by size DESC (bbox-area "
    "tiebreak), takes the TOP FOUR, crops each, and packs them into a "
    "2x2 gallery with 1-cell gutters (biggest top-left). A 5th motif "
    "is silently dropped. (Old doc claimed a 'vertical pack'; the old "
    "generator emitted 2-3 motif boards which CRASH the rule at "
    "(fourth shapes) — 15/24 smoke rejections.)"
)

# Rivals: 'vertical stack' refuted by the 2x2 layout. 'order by color'
# refuted by size ordering. 'all motifs appear' refuted by 5-motif
# boards whose smallest vanishes. 4 demos incl. >=1 five-motif board.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "EXACTLY 4-5 motifs (fewer CRASHES the rule at (fourth shapes))",
    "motif sizes mostly distinct so the size order is visible",
]

DEGENERATE_TEXTURES = ("tied_sizes",)
HELPFUL_TEXTURES = ("plain", "five_motifs")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..11 (hard 11..14)",
                "valid": "8..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 11..13 (hard 13..16)",
                "valid": "9..16", "doc": "Grid width."},
    "n":       {"type": "int", "default": "4 (five_motifs: 5)", "valid": "4..5",
                "doc": "Motif count — never below 4."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|five_motifs|tied_sizes",
                "doc": "five_motifs: the smallest is dropped from the gallery."},
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
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "five_motifs"))
    if difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    n = 5 if texture == "five_motifs" else \
        int(overrides.get("n", 4))
    n = max(4, min(5, n))  # the rule indexes the top FOUR unconditionally
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        sizes = rng.sample([3, 4, 5, 6], min(4, n))
        while len(sizes) < n:
            sizes.append(rng.randint(3, 6))
        ok = True
        for color, size in zip(colors, sizes):
            cells = _build_motif(rng, size)
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
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, ctx):
    """tied_sizes — all 4 motifs share one size: only the bbox-area
    key orders the gallery. rng-varied, rule-safe (always 4 motifs;
    the old no_motifs/single_motif/all_same_color degenerates left
    fewer than 4 objects and CRASHED the rule)."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 12)
    w = ctx.draw_int("grid_w", 12, 14)
    g = full_grid(h, w, 0)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 4)
    size = rng.randint(3, 4)
    placed_n = 0
    for color in colors:
        cells = _build_motif(rng, size)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        for _ in range(120):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed_n += 1
                break
    # the rule indexes 4 objects unconditionally: top up with singles
    while placed_n < 4:
        for r in range(h):
            done = False
            for c in range(w):
                if _free(g, r, c, r, c):
                    g[r][c] = colors[placed_n % 4]
                    placed_n += 1
                    done = True
                    break
            if done:
                break
    return g

def _components_same_color(grid, colors=None):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or (colors is not None and v not in colors) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and grid[nx][ny] == v:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append((v, cells))
    return comps


def self_check(grid, *, seed=None, sample_index=None, difficulty=None, **kwargs):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular and nonempty"]
    comps = _components_same_color(grid)
    if not (4 <= len(comps) <= 5):
        errs.append(f"expected 4-5 nonzero motifs, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("motifs should have distinct colors")
    sizes = [len(cells) for _, cells in comps]
    if len(set(sizes)) < 3:
        errs.append(f"expected at least three distinct motif sizes, got {sorted(set(sizes))}")
    if any(len(cells) < 3 for _, cells in comps):
        errs.append("motifs should be nontrivial connected shapes")
    return errs
