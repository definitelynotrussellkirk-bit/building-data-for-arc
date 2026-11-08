"""Generator for 36fdfd69.

Rule: nearby red cells form groups whose bounding boxes replace
background cells with color 4.

Combinatorial axes (8): grid_h/w, group_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_groups, single_red, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "405c8d5c7709"
VERSION = "3.1.0"  # FIX identity: clamp each red cluster INSIDE the bg region and require its bbox to hold >=1 non-red cell, so every cluster bbox contains bg cells for the rule to recolor to 4 (was: clusters straddled the region edge / formed 1xN red-only bboxes -> no bg in bbox -> identity).
TASK_ID = "405c8d5c7709"
SUMMARY = (
    "12×12 grid filled with a single non-{0,2,4} BACKGROUND "
    "color, with 1-3 small CLUSTERS of color-2 (red) cells. "
    "Each cluster: 2-3 red cells placed within Chebyshev "
    "distance ≤ 2 of one another (so they merge into a single "
    "group). Different clusters are placed apart. Rule: (1) "
    "find the most frequent non-zero value bg in the grid. (2) "
    "collect all color-2 cells. (3) cluster them greedily by "
    "Chebyshev distance ≤ 2 (cells within radius-2 in any "
    "direction merge into the same group). (4) For each group, "
    "compute the bbox over its red cells. (5) Inside each bbox, "
    "set every bg cell (NOT red, NOT 4, NOT other) to color 4. "
    "Red cells inside the bbox stay red."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "12×12 grid",
    "exactly one dominant non-{0,2,4} background color",
    "1-3 red clusters of 2-3 cells each (Chebyshev-2 cohesive)",
    "clusters are spaced apart so they don't merge across",
    "each red-cluster bbox contains some bg cells (so the rule fires)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_groups", "single_red", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "12", "valid": "12"},
    "group_count":    {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        group_count = ctx.draw_int("group_count", 1, 1)
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
    elif difficulty == "hard":
        group_count = ctx.draw_int("group_count", 3, 3)
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22)
    else:
        group_count = ctx.draw_int("group_count", 1, 3)
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
    bg = ctx.draw_color("background", exclude={0, 2, 4})
    # canonical input = 0-bg + a LARGE bg-color REGION (~half) + color-2 clusters
    # whose bboxes overlap the region (rule recolours the region cells in each
    # cluster's bbox to 4). (Was: whole grid filled with bg -> no zeros.)
    g = full_grid(h, w, 0)
    reg_h = rng.randint(max(3, h // 2), h - 1)
    reg_w = rng.randint(max(3, w // 2), w - 1)
    reg_r0 = rng.randint(0, h - reg_h); reg_c0 = rng.randint(0, w - reg_w)
    for r in range(reg_r0, reg_r0 + reg_h):
        for c in range(reg_c0, reg_c0 + reg_w):
            g[r][c] = bg
    placed_bboxes = []  # (r1, c1, r2, c2)

    def overlaps_with_buffer(r1, c1, r2, c2, buffer=3):
        for pr1, pc1, pr2, pc2 in placed_bboxes:
            if (r1 - buffer <= pr2 and r2 + buffer >= pr1
                    and c1 - buffer <= pc2 and c2 + buffer >= pc1):
                return True
        return False

    for _ in range(group_count):
        for _try in range(80):
            # anchor INSIDE the region so the cluster's bbox overlaps bg cells
            anchor_r = rng.randint(reg_r0, reg_r0 + reg_h - 1)
            anchor_c = rng.randint(reg_c0, reg_c0 + reg_w - 1)
            cluster = [(anchor_r, anchor_c)]
            for _ in range(rng.randint(1, 2)):
                dr = rng.randint(-2, 2); dc = rng.randint(-2, 2)
                # clamp INSIDE the bg region so the bbox cells are bg (not the
                # 0 background outside it) -- otherwise the bbox may hold no bg
                # cell for the rule to recolor.
                nr = max(reg_r0, min(reg_r0 + reg_h - 1, anchor_r + dr))
                nc = max(reg_c0, min(reg_c0 + reg_w - 1, anchor_c + dc))
                cluster.append((nr, nc))
            uniq = set(cluster)
            rs = [r for r, _ in cluster]; cs = [c for _, c in cluster]
            r1, r2 = min(rs), max(rs); c1, c2 = min(cs), max(cs)
            if r2 == r1 and c2 == c1:
                continue
            # the bbox must contain a non-red cell (a bg cell) for the fill to
            # have a visible effect -- reject all-red bboxes (e.g. 1x2 adjacent).
            if (r2 - r1 + 1) * (c2 - c1 + 1) <= len(uniq):
                continue
            if overlaps_with_buffer(r1, c1, r2, c2):
                continue
            for r, c in cluster:
                g[r][c] = 2
            placed_bboxes.append((r1, c1, r2, c2))
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one red(2)-cluster bbox must contain a bg cell (the dominant
    non-zero colour), so the recolor-to-4 rule fires. Returns violation list."""
    from collections import Counter
    h, w = len(grid), len(grid[0])
    cnt = Counter(v for row in grid for v in row if v != 0)
    if not cnt:
        return ["no non-zero cells"]
    bg = cnt.most_common(1)[0][0]
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not reds:
        return ["no red(2) cells -> rule is a no-op"]
    # greedy chebyshev<=2 clustering
    groups = []
    for p in reds:
        hit = [i for i, g in enumerate(groups)
               if any(max(abs(p[0] - q[0]), abs(p[1] - q[1])) <= 2 for q in g)]
        if not hit:
            groups.append([p])
        else:
            merged = [p]
            for i in sorted(hit, reverse=True):
                merged += groups.pop(i)
            groups.append(merged)
    for g in groups:
        rs = [r for r, _ in g]; cs = [c for _, c in g]
        if any(grid[r][c] == bg
               for r in range(min(rs), max(rs) + 1)
               for c in range(min(cs), max(cs) + 1)):
            return []
    return ["no cluster bbox contains a bg cell -> rule would be identity"]


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 5)
    if name == "no_groups":
        return g
    if name == "single_red":
        g[6][6] = 2
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
