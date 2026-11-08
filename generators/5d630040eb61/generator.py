"""Generator for puzzle a934301b.

Rule: multicolor 8-connected objects. Remove (recolor to 0) any object
containing >1 cyan(8) cell; keep objects with <=1 cyan.

Combinatorial axes (8): grid_h/w, n_bad_objects, n_good_objects,
object_size_range, cyan_count_per_bad, position_bias,
inter_object_margin, palette_size.
Degenerates: all_bad, all_good, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "5d630040eb61"
VERSION = "2.1.0"  # FIX all_background_output (6/18) + identity (5/18): objects were placed with margin= (edge distance) but NO padding, so two rects could land 8-ADJACENT and MERGE into one component -> their cyan counts combined -> the whole merged object erased -> blank output; and the weak fallback returned a good-only object -> no bad object -> identity. Now separate objects with padding>=1 and retry until the layout has >=1 genuine bad (>=2 cyan) AND >=1 good (<=1 cyan) SEPARATE component, with a guaranteed hand-built fallback. + self_check.
TASK_ID = "5d630040eb61"
SUMMARY = (
    "0-bg grid (h, w ~10-16) with multiple MULTICOLOR 8-conn "
    "OBJECTS (each a rectangular block in some base color, with "
    "some cells overpainted as color 8 / cyan). Objects are "
    "isolated by margin ≥ 2. There are 1-3 'BAD' objects (each "
    "has ≥ 2 cyan cells) and 1-3 'GOOD' objects (each has ≤ 1 "
    "cyan cell). Rule: extract 8-connected MULTICOLOR objects. "
    "For each object, count its cyan(8) cells. If count > 1 → "
    "erase the entire object (set all its cells to 0). Else "
    "(count ≤ 1) → keep the object as-is. Output: input with "
    "all 'bad' (≥2 cyan) objects erased."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 multicolor object with ≥2 cyan(8) cells (will be removed)",
    "≥1 multicolor object with ≤1 cyan cell (will be kept)",
    "objects 8-conn, non-overlapping with margin ≥ 2",
]

DEGENERATE_TEXTURES = ("all_bad", "all_good", "single_object")
HELPFUL_TEXTURES = ("balanced", "bad_heavy", "good_heavy", "many_objects")

AXES = {
    "grid_h":              {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "grid_w":              {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "n_bad_objects":       {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "n_good_objects":      {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "object_size_range":   {"type": "str", "default": "rng small|medium|large",
                            "valid": "small|medium|large"},
    "cyan_count_per_bad":  {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "inter_object_margin": {"type": "int", "default": "2", "valid": "1..3"},
    "position_bias":       {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "texture":             {"type": "str", "default": "rng helpful",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 8, 11
    elif difficulty == "hard":
        h_lo, h_hi = 14, 20
    else:
        h_lo, h_hi = 10, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    if texture == "bad_heavy":
        n_bad, n_good = 3, 1
    elif texture == "good_heavy":
        n_bad, n_good = 1, 3
    elif texture == "many_objects":
        n_bad, n_good = 2, 2
    else:
        n_bad = int(overrides.get("n_bad_objects",
                                  ctx.draw_int("n_bad_objects", 1, 2)))
        n_good = int(overrides.get("n_good_objects",
                                   ctx.draw_int("n_good_objects", 1, 2)))
    n_bad = max(1, min(3, n_bad))
    n_good = max(1, min(3, n_good))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=max(2, n_bad + n_good),
                                            exclude={0, 8}))
    while len(palette) < n_bad + n_good:
        palette.append(palette[0])
    size_range = overrides.get("object_size_range",
                               ctx.draw_choice("object_size_range",
                                               ["small", "medium", "large"]))
    cyan_count = int(overrides.get("cyan_count_per_bad",
                                   ctx.draw_int("cyan_count_per_bad", 2, 4)))
    margin = int(overrides.get("inter_object_margin", 2))
    # `pad` is the inter-OBJECT gap (Chebyshev): padding=1 already guarantees a
    # full empty cell between objects so they never merge under the rule's
    # 8-connectivity (the bug was padding=0). Keep it at 1 so even the tight
    # easy grids can pack without falling back. (Was passed as `margin`=
    # edge-distance with padding=0, so objects could touch + merge.)
    pad = 1
    s_lo, s_hi = {"small": (3, 3), "medium": (3, 4), "large": (4, 5)}[size_range]

    for _attempt in range(30):
        g = full_grid(h, w, 0)
        placed_bad = 0
        for i in range(n_bad):
            for _ in range(20):
                rh, rw = rng.randint(s_lo, s_hi), rng.randint(s_lo, s_hi)
                cells = normalize(rect_cells(rh, rw))
                pos = place_no_overlap(rng, g, cells, palette[i], bg=0,
                                       margin=1, padding=pad, max_tries=20)
                if pos is not None:
                    rr, rc = pos
                    local_cells = [(rr + dr, rc + dc)
                                   for dr in range(rh) for dc in range(rw)]
                    n_cyan = min(cyan_count, len(local_cells) - 1)
                    n_cyan = max(2, n_cyan)   # a BAD object needs >=2 cyan
                    for r, c in rng.sample(local_cells, n_cyan):
                        g[r][c] = 8
                    placed_bad += 1
                    break
        placed_good = 0
        for i in range(n_good):
            color = palette[n_bad + i] if (n_bad + i) < len(palette) else palette[-1]
            for _ in range(20):
                rh, rw = rng.randint(s_lo, s_hi), rng.randint(s_lo, s_hi)
                cells = normalize(rect_cells(rh, rw))
                pos = place_no_overlap(rng, g, cells, color, bg=0,
                                       margin=1, padding=pad, max_tries=20)
                if pos is not None:
                    rr, rc = pos
                    if rng.random() < 0.5:
                        # at most ONE cyan (random cell) -> stays GOOD
                        gcells = [(rr + dr, rc + dc)
                                  for dr in range(rh) for dc in range(rw)]
                        gr, gc = rng.choice(gcells)
                        g[gr][gc] = 8
                    placed_good += 1
                    break
        if placed_bad >= 1 and placed_good >= 1 and _layout_ok(g):
            return g
    return _guaranteed_layout(h, w, rng, palette)


def _components_8(g):
    h, w = len(g), len(g[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            st = [(r, c)]; seen.add((r, c)); cells = []
            while st:
                rr, cc = st.pop(); cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                                and g[nr][nc] != 0:
                            seen.add((nr, nc)); st.append((nr, nc))
            out.append(cells)
    return out


def _layout_ok(g):
    """>=1 object with >=2 cyan (erased) AND >=1 object with <=1 cyan (kept)."""
    comps = _components_8(g)
    bad = [c for c in comps if sum(1 for (r, cc) in c if g[r][cc] == 8) >= 2]
    good = [c for c in comps if sum(1 for (r, cc) in c if g[r][cc] == 8) <= 1]
    return len(bad) >= 1 and len(good) >= 1


def _guaranteed_layout(h, w, rng, palette):
    """A minimal, well-separated valid board: one BAD (2 cyan) + one GOOD."""
    g = full_grid(h, w, 0)
    cb, cg = (palette + [1, 2])[0], (palette + [1, 3])[1]
    if cg == cb:
        cg = 1 if cb != 1 else 2
    # bad 3x3 in the top-left, good 3x3 in the bottom-right, well apart
    for r in range(1, 4):
        for c in range(1, 4):
            g[r][c] = cb
    g[1][1] = 8; g[2][2] = 8                    # 2 cyan -> bad
    # good block in the bottom-right, separated by a >=1 gap (rows 1-3 / cols
    # 1-3 vs rows h-3.. / cols w-3.. ; with h,w>=8 the gap is row 4 / col 4).
    br, bc = h - 3, w - 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            g[r][c] = cg                          # 0 cyan -> good
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one 8-connected object has >=2 cyan(8) cells (erased) and at
    least one has <=1 cyan (kept), so the rule removes something but not
    everything. Returns a list of violations (empty == pass)."""
    comps = _components_8(grid)
    bad = sum(1 for c in comps
              if sum(1 for (r, cc) in c if grid[r][cc] == 8) >= 2)
    good = sum(1 for c in comps
               if sum(1 for (r, cc) in c if grid[r][cc] == 8) <= 1)
    msgs = []
    if bad < 1:
        msgs.append("no object with >=2 cyan (nothing erased -> identity)")
    if good < 1:
        msgs.append("no object with <=1 cyan (all erased -> blank)")
    return msgs


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 8]
    rng.shuffle(palette)
    if name == "all_bad":
        # bad object only
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = palette[0]
        for r in range(2, 5):
            for c in range(2, 5):
                if rng.random() < 0.5:
                    g[r][c] = 8
        return g
    if name == "all_good":
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = palette[0]
        return g
    if name == "single_object":
        for r in range(3, 6):
            for c in range(3, 6):
                g[r][c] = palette[0]
        g[3][3] = 8
        return g
    return g
