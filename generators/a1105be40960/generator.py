"""Generator for arc_additional_puzzle_bank_volume8:H51 -- Mark k-th largest color-4 object.

Rule: k = count of color-1 (blue) cells. Among the color-4 objects sorted
by bbox area descending, recolor the k-th largest to color 3 (when
1 <= k <= #objects).

Combinatorial axes: grid size, the number of objects, their (distinct)
bbox areas and positions, the selector count k, and the marker positions.
Degenerates: k_too_large, no_ones, tied_areas.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "a1105be40960"
VERSION = "2.0.1"  # diversity: scattered distinct-area solid blobs + random k + positions + grid (was nested frames ~16)
TASK_ID = "a1105be40960"
SUMMARY = (
    "0-bg grid (size varies). Several solid COLOR-4 (yellow) objects of "
    "DISTINCT bbox areas, scattered apart, plus k blue(1) marker cells "
    "(1<=k<=#objects). Rule: recolor the k-th LARGEST object (by bbox area) "
    "to color 3 (green). The grid size, object count/sizes/positions, the "
    "selector k and the marker positions all vary freely (was several "
    "nested frames, ~16 distinct)."
)

INVARIANTS = [
    "color-4 objects have strictly distinct bbox areas (so k-th largest is unambiguous)",
    "objects are separated (each a distinct component)",
    "k blue(1) cells select the k-th largest object, 1<=k<=#objects",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("k_too_large", "no_ones", "tied_areas")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..26"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..5"},
    "k":              {"type": "int", "default": "varies", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "objects_apart", "valid": "objects_apart"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "solid", "valid": "solid"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|k_too_large|no_ones|tied_areas"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 color-4 objects + k>=1 color-1 cells; k <= number of color-4 objects."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Count color-1 cells
    k = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if k == 0:
        errs.append("no color-1 selector cells found")
    # Count color-4 4-connected components
    seen = [[False] * w for _ in range(h)]
    n_obj = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 4 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == 4:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                n_obj += 1
    if n_obj < 2:
        errs.append(f"expected >=2 color-4 objects, found {n_obj}")
    if k > 0 and n_obj > 0 and k > n_obj:
        errs.append(f"k={k} > number of color-4 objects ({n_obj})")
    return errs


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, nr, fr = (11, 13), (11, 14), (2, 3), (2, 4)
    elif difficulty == "hard":
        hr, wr, nr, fr = (17, 24), (18, 26), (3, 5), (2, 7)
    else:
        hr, wr, nr, fr = (13, 18), (14, 20), (2, 4), (2, 6)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        want = rng.randint(*nr)
        areas = set()
        placed = 0
        for _ in range(want):
            for _t in range(30):
                fh = rng.randint(*fr); fw = rng.randint(*fr)
                if fh * fw in areas or fh > h - 1 or fw > w - 1:
                    continue
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                if _reserve(occ, top, left, fh, fw, h, w, margin=1):
                    draw_rect(g, top, left, fh, fw, 4)
                    areas.add(fh * fw)
                    placed += 1
                    break
        if placed < 2:
            continue

        k = rng.randint(1, placed)
        dropped = 0
        for _ in range(k):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if _reserve(occ, r, c, 1, 1, h, w, margin=1):
                    g[r][c] = 1
                    dropped += 1
                    break
        if dropped == k:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    draw_rect(g, 1, 1, 4, 4, 4)
    draw_rect(g, 8, 8, 3, 3, 4)
    if name == "k_too_large":
        for i in range(5):
            g[0][i] = 1          # k=5 > 2 objects -> unchanged
        return g
    if name == "no_ones":
        return g                 # no markers -> unchanged
    if name == "tied_areas":
        g2 = full_grid(13, 13, 0)
        draw_rect(g2, 1, 1, 3, 3, 4)
        draw_rect(g2, 8, 8, 3, 3, 4)   # equal areas -> ambiguous
        g2[0][0] = 1
        return g2
    return g
