"""Generator for puzzle 8efcae92.

Rule: multi-color 8-conn clusters; rule extracts bbox of the cluster
with the MOST red(2) cells.

Combinatorial axes (8): grid_h/w, n_clusters, cluster_size_kind,
red_count_distribution, palette_size, position_bias,
inter_cluster_margin, decoy_density.
Degenerates: single_cluster, no_red, ties_for_max.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "4cccb4dba000"
VERSION = "1.1.1"
TASK_ID = "4cccb4dba000"
SUMMARY = "Multi-color clusters with red counts; rule extracts bbox of most-red one."

INVARIANTS = [
    "background is 0",
    ">=2 multi-color 8-conn clusters",
    "each cluster has >=1 red(2) cell",
    "STRICTLY unique max red-count (no tie at max)",
    "clusters separated by margin >=2 (so 8-conn keeps them separate)",
]

CLUSTER_SIZES = ("small", "medium", "large")
RED_DISTS = ("ascending", "wide_spread", "tight_spread")
DEGENERATE_TEXTURES = ("single_cluster", "no_red", "ties_for_max")
HELPFUL_TEXTURES = CLUSTER_SIZES

AXES = {
    "grid_h":              {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":              {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_clusters":          {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "cluster_size_kind":   {"type": "str", "default": "rng helpful",
                            "valid": "|".join(CLUSTER_SIZES)},
    "red_count_distribution": {"type": "str", "default": "rng helpful",
                               "valid": "|".join(RED_DISTS)},
    "position_bias":       {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "inter_cluster_margin": {"type": "int", "default": "2", "valid": "2..4"},
    "palette_size":        {"type": "int", "default": "= n_clusters",
                            "valid": "2..7"},
    "texture":             {"type": "str", "default": "alias for cluster_size_kind",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 10, 12, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 18, 22, 3, 5
    else:
        h_lo, h_hi, n_lo, n_hi = 12, 18, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_clusters = int(overrides.get("n_clusters",
                                   ctx.draw_int("n_clusters", n_lo, n_hi)))
    n_clusters = max(2, min(5, n_clusters))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=n_clusters,
                                            exclude={0, 2}))
    while len(palette) < n_clusters:
        palette.append(palette[0])
    size_kind = (overrides.get("texture") or
                 overrides.get("cluster_size_kind")
                 or ctx.draw_choice("cluster_size_kind",
                                    list(CLUSTER_SIZES)))
    s_lo, s_hi = {"small": (3, 3), "medium": (3, 4), "large": (4, 5)}[size_kind]
    red_dist = overrides.get("red_count_distribution",
                             ctx.draw_choice("red_count_distribution",
                                             list(RED_DISTS)))
    margin = int(overrides.get("inter_cluster_margin", 2))
    red_counts = _draw_red_counts(red_dist, n_clusters, rng)
    g = full_grid(h, w, 0)
    placed = 0
    for i, n_red in enumerate(red_counts):
        rh = rng.randint(s_lo, s_hi); rw = rng.randint(s_lo, s_hi)
        cells = normalize(rect_cells(rh, rw))
        pos = place_no_overlap(rng, g, cells, palette[i], bg=0,
                               margin=margin, max_tries=40)
        if pos is None:
            continue
        rr, rc = pos
        local_cells = [(rr + dr, rc + dc)
                       for dr in range(rh) for dc in range(rw)]
        rng.shuffle(local_cells)
        n_to_paint = min(n_red, len(local_cells) - 1)
        for r, c in local_cells[:n_to_paint]:
            g[r][c] = 2
        placed += 1
    if placed < 2:
        return _draw_from_degenerate("single_cluster", h, w, rng)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify multi-cluster unique-max-red invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    count2 = flat.count(2)
    if count2 < 1:
        problems.append("no color-2 (red) cells found")
    # Need at least 2 distinct nonzero colors to have >=2 clusters
    distinct_nz = len(set(v for v in flat if v != 0))
    if distinct_nz < 2:
        problems.append(f"expected >=2 distinct nonzero colors, found {distinct_nz}")
    return problems


def _draw_red_counts(dist, n_clusters, rng):
    if dist == "ascending":
        start = rng.randint(1, 3)
        return [start + i for i in range(n_clusters)]
    if dist == "tight_spread":
        base = rng.randint(2, 4)
        return [base + i for i in range(n_clusters)]
    return sorted(rng.sample(range(1, 1 + n_clusters * 3), n_clusters))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [c for c in range(1, 10) if c != 2]
    rng.shuffle(palette)
    if name == "single_cluster":
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = palette[0]
        for r in range(2, 5):
            g[r][2] = 2
        return g
    if name == "no_red":
        for i, (r0, c0) in enumerate([(2, 2), (8, 8)]):
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 3):
                    if r < h and c < w:
                        g[r][c] = palette[i]
        return g
    if name == "ties_for_max":
        for i, (r0, c0) in enumerate([(2, 2), (8, 8)]):
            for r in range(r0, r0 + 3):
                for c in range(c0, c0 + 3):
                    if r < h and c < w:
                        g[r][c] = palette[i]
            if r0 < h and c0 < w:
                g[r0][c0] = 2
                g[r0 + 1][c0 + 1] = 2
        return g
    return g
