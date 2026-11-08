"""Generator for arc_puzzle_bank_21_set12_s:S12_M1 — crop max-degree component.

Rule: a contact graph contains one unique highest-degree component,
which is cropped and recolored.

Combinatorial axes (8): grid_h, grid_w, palette_kind, leaf_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_chain, tied_max_degree, all_isolated.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b81390858ebd"
# 1.3.0: hub was 1 of 8 FIXED templates -> output (hub bbox crop in 8) had only
# ~8 distinct values (uniq=0.056). Now hub is a RANDOM connected polyomino of
# varied size/shape, so the cropped output shape varies widely.
VERSION = "1.4.0"  # keep hub non-8 and leaves nonadjacent; add self_check
TASK_ID = "b81390858ebd"
SUMMARY = "Several connected components form a contact graph (touching components are adjacent). A central HUB is a random connected polyomino touched by several singleton leaves (high degree); isolated singleton distractors sit elsewhere (degree 0). Rule finds the component with the highest contact degree (ties broken by size, then top-left), then outputs its bbox crop painted color 8. Hub shape/size varies, so the cropped output varies."

# Rivals: 'pick the largest' refuted by ≥2 demos where the high-degree
# hub is smaller than distractors. 'pick the first' refuted by ≥1 demo
# where the hub is not top-left. 'preserve original color' refuted by
# any demo (output is 8). 'pick the most-isolated' refuted by any
# demo (degree-maximizing, not minimizing). 3 demos with varied hubs.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "nonzero components are same-color 4-connected objects",
    "one central component has strictly higher contact degree than every other component",
    "distractor components have lower contact degree and do not touch the target cluster",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_chain", "tied_max_degree", "all_isolated")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..18"},
    "width":          {"type": "int", "default": "rng 11..15", "valid": "9..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "leaf_count":     {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "position_bias":  {"type": "str", "default": "central_hub_with_leaves",
                       "valid": "central_hub_with_leaves"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..6", "valid": "4..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_chain|tied_max_degree|all_isolated"},
}


def _poly(rng, n, max_h, max_w):
    """Random connected polyomino of n cells, normalized, within max_h x max_w."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    tries = 0
    while len(cells) < n and frontier and tries < 200:
        tries += 1
        r, c = rng.choice(frontier)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        cand = set(cells) | {(nr, nc)}
        rs = [p[0] for p in cand]; cs = [p[1] for p in cand]
        if (max(rs) - min(rs) + 1) <= max_h and (max(cs) - min(cs) + 1) <= max_w \
                and (nr, nc) not in cells:
            cells.add((nr, nc))
            frontier.append((nr, nc))
    r0 = min(p[0] for p in cells); c0 = min(p[1] for p in cells)
    return [(r - r0, c - c0) for (r, c) in sorted(cells)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 11)
        w = ctx.draw_int("width", 10, 13)
        leaf_count = ctx.draw_int("leaf_count", 2, 3)
        n_distract = 1
    elif difficulty == "hard":
        h = ctx.draw_int("height", 14, 18)
        w = ctx.draw_int("width", 15, 20)
        leaf_count = 4
        n_distract = rng.randint(3, 4)
    else:
        h = ctx.draw_int("height", 11, 14)
        w = ctx.draw_int("width", 12, 16)
        leaf_count = rng.randint(3, 4)
        n_distract = rng.randint(2, 3)
    g = full_grid(h, w, 0)
    # Hub + leaves + distractors each need a distinct color; hard needs up to
    # 1+4+4=9. The old 7-color pool (no 5/8) overflowed → "Sample larger than
    # population". 5/8 have no special role here (the degenerates even use 8),
    # so use the full 9-color palette, which exactly covers the worst case.
    hub_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    palette = [hub_color] + rng.sample([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != hub_color],
                                      leaf_count + n_distract)
    # Hub = a RANDOM connected polyomino (multi-cell, varied shape/size) so the
    # output (hub bbox crop in 8) varies. Bound the bbox to fit the grid.
    max_hub_h = max(3, min(6, h - 6))
    max_hub_w = max(3, min(6, w - 6))
    hub_n = rng.randint(3, max(3, min(7, max_hub_h * max_hub_w // 2)))
    hub_shape = _poly(rng, hub_n, max_hub_h, max_hub_w)
    hub_h = max(r for r, _ in hub_shape) + 1
    hub_w = max(c for _, c in hub_shape) + 1
    # Place hub
    hr = rng.randint(2, h - hub_h - 2)
    hc = rng.randint(2, w - hub_w - 2)
    hub_cells = [(hr + dr, hc + dc) for dr, dc in hub_shape]
    for hcell in hub_cells:
        g[hcell[0]][hcell[1]] = palette[0]
    # Leaves: pick cells 4-adjacent to the hub (but not in the hub)
    hub_set = set(hub_cells)
    leaf_candidates = []
    for hr2, hc2 in hub_cells:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = hr2 + dr, hc2 + dc
            if (0 <= nr < h and 0 <= nc < w and
                (nr, nc) not in hub_set and g[nr][nc] == 0):
                leaf_candidates.append((nr, nc))
    leaf_candidates = list(set(leaf_candidates))
    rng.shuffle(leaf_candidates)
    selected_leaves: list[tuple[int, int]] = []
    for (lr, lc) in leaf_candidates:
        if len(selected_leaves) >= leaf_count:
            break
        if g[lr][lc] != 0:
            continue
        # Leaves should contact the hub but not each other; otherwise a middle
        # leaf can tie the hub's contact degree, hiding the unique max-degree rule.
        if any(abs(lr - pr) + abs(lc - pc) == 1 for pr, pc in selected_leaves):
            continue
        selected_leaves.append((lr, lc))
    if len(selected_leaves) != leaf_count:
        raise ValueError("could not place nonadjacent hub leaves")
    placed_leaves = 0
    for (lr, lc) in selected_leaves:
        g[lr][lc] = palette[1 + placed_leaves]
        placed_leaves += 1
    # Distractors: isolated singletons far from the hub
    placed = 0
    for _ in range(120):
        if placed >= n_distract: break
        rr = rng.randint(0, h - 1); cc = rng.randint(0, w - 1)
        if g[rr][cc] != 0: continue
        if any(0 <= rr + dr < h and 0 <= cc + dc < w and g[rr + dr][cc + dc] != 0
               for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
            continue
        g[rr][cc] = palette[1 + placed_leaves + placed]
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_chain":
        # all components isolated → all degree 0, no max to find
        g[2][2] = 3
        g[6][6] = 7
        g[8][9] = 8
        return g
    if name == "tied_max_degree":
        # 2 components share max degree → "unique highest-degree" precondition fails
        g[3][3] = 3; g[3][4] = 1; g[3][2] = 2   # hub A: degree 2
        g[7][8] = 4; g[7][9] = 6; g[7][7] = 5   # hub B: degree 2 (tied)
        return g
    if name == "all_isolated":
        # only one isolated component → trivial degree-0 case
        g[5][5] = 3
        return g
    return g



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _contact_degrees(grid, comps):
    index = {}
    for i, (_, cells) in enumerate(comps):
        for cell in cells:
            index[cell] = i
    degrees = [set() for _ in comps]
    h, w = len(grid), len(grid[0])
    for i, (_, cells) in enumerate(comps):
        for r, c in cells:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    j = index.get((nr, nc))
                    if j is not None and j != i:
                        degrees[i].add(j)
    return [len(x) for x in degrees]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the unique max-contact-degree crop task."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    problems = []
    comps = _components(grid)
    if difficulty == "easy":
        leaf_lo, leaf_hi = 2, 3
        distract_lo, distract_hi = 1, 1
    elif difficulty == "hard":
        leaf_lo, leaf_hi = 4, 4
        distract_lo, distract_hi = 3, 4
    else:
        leaf_lo, leaf_hi = 3, 4
        distract_lo, distract_hi = 2, 3
    degrees = _contact_degrees(grid, comps)
    if not degrees:
        return ["no nonzero components"]
    maxdeg = max(degrees)
    winners = [i for i, d in enumerate(degrees) if d == maxdeg]
    if len(winners) != 1 or maxdeg <= 0:
        problems.append("no unique positive-degree hub component")
        return sorted(set(problems))
    hub_i = winners[0]
    hub_color, hub_cells = comps[hub_i]
    if hub_color == 8:
        problems.append("hub is already color 8, hiding output recoloring")
    if not (leaf_lo <= maxdeg <= leaf_hi):
        problems.append(f"hub degree {maxdeg} outside expected leaf count {leaf_lo}..{leaf_hi}")
    leaf_count = sum(1 for i, d in enumerate(degrees) if i != hub_i and d > 0)
    distract_count = sum(1 for i, d in enumerate(degrees) if i != hub_i and d == 0)
    if leaf_count != maxdeg:
        problems.append("contacting components are not exactly the hub leaves")
    if not (distract_lo <= distract_count <= distract_hi):
        problems.append(f"distractor count {distract_count} outside expected {distract_lo}..{distract_hi}")
    for i, (color, cells) in enumerate(comps):
        if i == hub_i:
            if len(cells) < 3:
                problems.append("hub must be a multi-cell polyomino")
        elif degrees[i] > 0:
            if len(cells) != 1:
                problems.append("hub leaf is not a singleton")
            if degrees[i] != 1:
                problems.append("leaf touches another non-hub component")
        else:
            if len(cells) != 1:
                problems.append("distractor is not an isolated singleton")
    return sorted(set(problems))
