"""Generator for v1_e_m_h_keys:H5.

Rule: choose the color with the most components and fill its enclosed
holes with 9.

Combinatorial axes (8): grid_h, grid_w, palette_kind, target_color,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_one_color, no_holes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "b35301a51180"
VERSION = "2.2.1"  # v2.1 could occasionally realize only one target ring, tying another color. Retry until target has >=2 components and remains the unique max.
TASK_ID = "b35301a51180"
SUMMARY = (
    "Fixed 11×9 0-bg grid "
    "with HARDCODED LAYOUT: "
    "(a) TWO HOLLOW 3×3 "
    "RINGS in TARGET COLOR "
    "(from {1..8}) at "
    "(1..3, 1..3) and "
    "(5..7, 4..6); (b) ONE "
    "HOLLOW 3×3 RING in "
    "OTHER COLOR at (8..10, "
    "1..3); (c) ONE SOLID "
    "2×2 BLOCK in OTHER "
    "COLOR at (2..3, 6..7). "
    "Hardcoded positions × "
    "~8 × ~7 color choices "
    "= ~31 unique configs "
    "(HARDCODED-LOW). Rule "
    "(MOST-COMPONENTS "
    "COLOR's HOLES → 9): "
    "identify the COLOR "
    "with the MOST 4-conn "
    "COMPONENTS (target "
    "color has 2 components, "
    "other has 2). With "
    "tiebreak picking "
    "target. For each "
    "COMPONENT of that "
    "color, fill its "
    "ENCLOSED HOLE "
    "(interior 0-cells) "
    "with COLOR-9 (maroon). "
    "Other components, "
    "solid blocks unchanged. "
    "Net: most-component "
    "color's hollow rings "
    "get maroon centers."
)

INVARIANTS = [
    "color A appears as two separate hollow rectangular components",
    "another color appears as one hollow component",
    "the most component-rich color is therefore unambiguous",
    "only holes of the selected color are filled with 9",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_one_color", "no_holes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "11", "valid": "11"},
    "grid_w":         {"type": "int", "default": "9", "valid": "9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "target_color":   {"type": "int", "default": "rng choice", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "two_targets_one_other",
                       "valid": "two_targets_one_other"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "components", "valid": "components"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-bg colors; the most-component color has ≥2 components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # BFS: count components per color
    visited = [[False] * w for _ in range(h)]
    comp_counts: dict[int, int] = {}
    for sr in range(h):
        for sc in range(w):
            v = grid[sr][sc]
            if v == 0 or visited[sr][sc]:
                continue
            q = [(sr, sc)]
            visited[sr][sc] = True
            while q:
                r, c = q.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == v:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            comp_counts[v] = comp_counts.get(v, 0) + 1
    if len(comp_counts) < 2:
        errs.append(f"expected ≥2 distinct non-bg colors; found {sorted(comp_counts)}")
        return errs
    max_comp = max(comp_counts.values())
    if max_comp < 2:
        errs.append(f"expected most-component color to have ≥2 components; max={max_comp}")
    return errs


def _ring(g, top, left, color):
    for c in range(left, left + 3):
        g[top][c] = color
        g[top + 2][c] = color
    for r in range(top, top + 3):
        g[r][left] = color
        g[r][left + 2] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12); n_t = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20); n_t = rng.randint(3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16); n_t = rng.randint(2, 3)

    for _layout_attempt in range(80):
        palette = [1, 2, 3, 4, 5, 6, 7, 8]
        rng.shuffle(palette)
        target_color = palette[0]
        other_colors = palette[1:1 + rng.randint(1, 2)]
        g = full_grid(h, w, 0)
        placed = []  # (r1, c1, r2, c2) with 1-cell padding for 4-conn separation

        def _place_frame(color):
            fh = rng.randint(3, 5); fw = rng.randint(3, 5)
            for _ in range(60):
                if fh > h or fw > w:
                    return False
                r1 = rng.randint(0, h - fh); c1 = rng.randint(0, w - fw)
                r2, c2 = r1 + fh - 1, c1 + fw - 1
                if any(r1 <= p2 + 1 and p0 <= r2 + 1 and c1 <= p3 + 1 and p1 <= c2 + 1
                       for p0, p1, p2, p3 in placed):
                    continue
                draw_frame(g, r1, c1, r2, c2, color)   # hollow -> interior hole -> 9
                placed.append((r1, c1, r2, c2))
                return True
            return False

        # The rule chooses the color with the MOST components.  The earlier
        # fallback accepted target_made==1, after which one other component tied
        # it.  That creates an ambiguous lesson, so resample the whole layout
        # until the target has at least two rings and every other color has less.
        target_made = sum(_place_frame(target_color) for _ in range(n_t))
        if target_made < 2:
            continue

        other_made = 0
        for oc in other_colors:
            cap = target_made - 1
            want = rng.randint(1, cap)
            made = sum(_place_frame(oc) for _ in range(want))
            # It is okay for placement pressure to drop distractors, but there
            # should be at least one competing color in the final input.
            other_made += made
        if other_made == 0:
            continue
        return g
    raise ValueError("could not realize unambiguous most-components layout")


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 9, 0)
    if name == "no_components":
        # empty grid → no components to count
        return g
    if name == "all_one_color":
        # only one color present → "most-components-color" trivially that one, but rule expects competition
        _ring(g, 1, 1, 4)
        _ring(g, 5, 4, 4)
        return g
    if name == "no_holes":
        # solid blocks, no enclosed holes → rule has nothing to fill
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 4
        for r in range(5, 8):
            for c in range(4, 7): g[r][c] = 4
        for r in range(8, 11):
            for c in range(1, 4): g[r][c] = 6
        return g
    return g
