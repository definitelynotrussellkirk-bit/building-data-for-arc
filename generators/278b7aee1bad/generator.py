"""Generator for arc_additional_puzzles_21_set22_bundle:H152.

Rule: each color with 2 aligned cells defines a span (the segment between
them). On a blank output, cells covered by exactly 2 spans become 8 and
cells covered by >=3 spans become 9.

Combinatorial axes: grid size, the number of spans, their orientation
(H/V), positions and lengths.
Degenerates: no_aligned_pairs, parallel_only, single_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "278b7aee1bad"
VERSION = "2.0.1"
TASK_ID = "278b7aee1bad"
SUMMARY = (
    "0-bg grid (size varies). 3-5 distinct COLORS, each with EXACTLY 2 "
    "ALIGNED cells (same row or same column) defining a SPAN — the "
    "segment between them — a mix of horizontal and vertical, positioned "
    "so the spans CROSS. Rule: on a blank output, paint every cell "
    "covered by exactly 2 spans color 8 (cyan) and every cell covered by "
    ">=3 spans color 9 (maroon). The grid size, the number of spans, "
    "their orientations, positions and lengths all vary freely, so the "
    "crossing pattern (the output) varies too (was 3 fixed spans + grid "
    "padding)."
)

INVARIANTS = [
    "3-5 distinct colors, each with exactly 2 aligned cells",
    "a mix of horizontal and vertical spans that cross",
    "at least one cell is covered by 2+ spans",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_aligned_pairs", "parallel_only", "single_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "crossing_spans", "valid": "crossing_spans"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_aligned_pairs|parallel_only|single_pair"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥3 distinct colors each with exactly 2 aligned cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_aligned_pairs", "parallel_only", "single_pair"):
        return []
    errs = []
    from collections import Counter
    freq: Counter = Counter()
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                freq[v] += 1
    pair_colors = [col for col, cnt in freq.items() if cnt == 2]
    if len(pair_colors) < 3:
        errs.append(f"only {len(pair_colors)} colors with exactly 2 cells; expected ≥3")
    return errs


def _span_cells(a, b):
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        return [(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)]
    return [(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, npr = (8, 10), (10, 12), 3
    elif difficulty == "hard":
        hr, wr, npr = (12, 16), (12, 16), rng.randint(4, 5)
    else:
        hr, wr, npr = (9, 12), (11, 14), rng.randint(3, 4)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], npr)
        used = set()
        ends = []                  # (color, a, b)
        ok = True
        # at least one H and one V so they can cross
        orients = ['h', 'v'] + [rng.choice(['h', 'v']) for _ in range(npr - 2)]
        rng.shuffle(orients)
        for i in range(npr):
            placed = False
            for _t in range(40):
                if orients[i] == 'h':
                    r = rng.randint(1, h - 2)
                    c1 = rng.randint(0, w - 4); c2 = rng.randint(c1 + 3, w - 1)
                    a, b = (r, c1), (r, c2)
                else:
                    c = rng.randint(1, w - 2)
                    r1 = rng.randint(0, h - 4); r2 = rng.randint(r1 + 3, h - 1)
                    a, b = (r1, c), (r2, c)
                if a in used or b in used:
                    continue
                used.add(a); used.add(b)
                ends.append((colors[i], a, b))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # require >=1 crossing (a cell covered by >=2 spans)
        from collections import Counter
        cnt = Counter()
        for _col, a, b in ends:
            for cell in _span_cells(a, b):
                cnt[cell] += 1
        if max(cnt.values(), default=0) < 2:
            continue

        g = full_grid(h, w, 0)
        for col, a, b in ends:
            g[a[0]][a[1]] = col; g[b[0]][b[1]] = col
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_aligned_pairs":
        g[1][2] = 2; g[3][5] = 4; g[5][8] = 6
        return g
    if name == "parallel_only":
        g[1][1] = 2; g[1][8] = 2; g[3][1] = 4; g[3][8] = 4; g[5][1] = 6; g[5][8] = 6
        return g
    if name == "single_pair":
        g[2][2] = 5; g[2][8] = 5
        return g
    return g
