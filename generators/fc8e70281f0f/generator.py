"""Generator for arc_puzzle_bank_21_set12_s:S12_H5 — pick the cluster with K articulations.

Rule (reverse-engineered from the canonical solution): K = the number of color-1
cells in row 0. Below row 0, group the objects (mono-color 4-connected components)
into CLUSTERS by cardinal adjacency between objects, and for each cluster count its
ARTICULATION objects (cut vertices of the object-adjacency graph — objects whose
removal splits the cluster). OUTPUT the union (bbox crop) of the cluster whose
articulation count equals K, recolored to 8. (The previous SUMMARY described an
unrelated 'gallery pack' — corrected here to match the real rule.)

A chain (path) of m touching single-color cells is a path of m objects, which has
m-2 articulation objects (the internal ones). So a chain of K+2 cells yields K
articulations; we build the target chain plus decoy chains with other counts.

Combinatorial axes: grid size, target articulation K, chain geometry, decoy chains.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc8e70281f0f"
VERSION = "2.0.1"  # +executable self_check for articulation-chain invariants
TASK_ID = "fc8e70281f0f"

SUMMARY = (
    "0-bg grid: row 0 holds K color-1 cells (K = the target "
    "articulation count). Below row 0 are one or more CHAINS "
    "of touching cells in distinct colors — a chain of m "
    "cells is a path of m objects with m-2 ARTICULATION "
    "objects (cut vertices of the object-adjacency graph). "
    "Exactly one chain has m-2 == K. Rule: count the row-0 "
    "ones (K); group body objects into clusters by adjacency; "
    "find the cluster whose articulation count equals K; "
    "OUTPUT its union (bbox crop) recolored to 8."
)

INVARIANTS = [
    "row 0 has K color-1 cells (K = target articulation count)",
    "the body holds chains of touching distinct-color cells (paths of objects)",
    "exactly one cluster has articulation count == K (the target)",
    "clusters are mutually isolated so the object groupings are clean",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 10-15 med / 13-20 hard", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 11-16 med / 14-20 hard", "valid": "9..24"},
    "target_k":       {"type": "int", "default": "0-1 easy / 0-3 med / 1-4 hard", "valid": "0..5"},
    "n_decoys":       {"type": "int", "default": "0-1 easy / 1-2 med / 1-3 hard", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "chain lengths", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "row0_ones_with_object_chains",
                       "valid": "row0_ones_with_object_chains"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _place_chain(g, occ, cells, colors):
    for (r, c), col in zip(cells, colors):
        g[r][c] = col
        occ[r][c] = True
    for r, c in cells:                      # 1-cell halo so chains stay separate clusters
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < len(g) and 0 <= cc < len(g[0]):
                    occ[rr][cc] = True


def _path_walk(rng, m, h, w, occ):
    """Random self-avoiding walk of m single cells where each NEW cell is cardinally
    adjacent ONLY to the immediately-previous cell among the visited ones. That keeps
    the object-adjacency graph exactly a PATH (so it has m-2 articulation objects),
    while the varied walk geometry gives varied output unions. Body rows are >=1."""
    for _ in range(50):
        sr, sc = rng.randint(1, h - 1), rng.randint(0, w - 1)
        if occ[sr][sc]:
            continue
        cells = [(sr, sc)]
        cellset = {(sr, sc)}
        ok = True
        for _ in range(m - 1):
            pr, pc = cells[-1]
            cand = [(pr + dr, pc + dc) for dr, dc in _CARD]
            rng.shuffle(cand)
            stepped = False
            for nr, nc in cand:
                if not (1 <= nr < h and 0 <= nc < w):
                    continue
                if (nr, nc) in cellset or occ[nr][nc]:
                    continue
                # path-property: the new cell touches only the previous cell
                adj = [(nr + dr, nc + dc) for dr, dc in _CARD if (nr + dr, nc + dc) in cellset]
                if any(a != (pr, pc) for a in adj):
                    continue
                cells.append((nr, nc)); cellset.add((nr, nc)); stepped = True
                break
            if not stepped:
                ok = False
                break
        if ok and len(cells) == m:
            return cells
    return None


def _try_chain(g, occ, m, h, w, rng):
    cells = _path_walk(rng, m, h, w, occ)
    if cells is None:
        return False
    colors = (rng.sample([2, 3, 4, 5, 6, 7, 8, 9], m) if m <= 8
              else [rng.choice([2, 3, 4, 5, 6, 7, 8, 9]) for _ in range(m)])
    _place_chain(g, occ, cells, colors)
    return True


def _body_components(grid):
    """4-connected non-zero components below row 0 (the canonical rule's body)."""
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(1, h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARD:
                    rr, cc = r + dr, c + dc
                    if 1 <= rr < h and 0 <= cc < w and (rr, cc) not in seen and grid[rr][cc] != 0:
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            comps.append(cells)
    return comps


def _is_path_component(cells):
    cellset = set(cells)
    if len(cells) < 2:
        return False
    degs = []
    for r, c in cells:
        degs.append(sum((r + dr, c + dc) in cellset for dr, dc in _CARD))
    if len(cells) == 2:
        return sorted(degs) == [1, 1]
    return degs.count(1) == 2 and all(d in (1, 2) for d in degs)


def _articulation_count(cells):
    """Cut-vertex count for the cell-adjacency graph of one body component."""
    cellset = set(cells)
    if len(cells) <= 2:
        return 0

    def count_components_without(skip):
        remaining = cellset - ({skip} if skip is not None else set())
        seen = set()
        n = 0
        for start in list(remaining):
            if start in seen:
                continue
            n += 1
            stack = [start]
            seen.add(start)
            while stack:
                r, c = stack.pop()
                for dr, dc in _CARD:
                    nb = (r + dr, c + dc)
                    if nb in remaining and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
        return n

    base = count_components_without(None)
    return sum(count_components_without(cell) > base for cell in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the articulation-chain selector.

    The canonical rule drops row 0, treats non-zero body cells as objects, groups
    adjacent objects into clusters, and selects the unique cluster whose cut-vertex
    count equals the number of row-0 color-1 cells.  This check locks those facts
    down so future edits cannot silently emit ambiguous or non-path body clusters.
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    row0 = grid[0]
    if any(v not in (0, 1) for v in row0):
        errs.append("row 0 contains a non-{0,1} marker")
    K = sum(1 for v in row0 if v == 1)
    if K > 5:
        errs.append(f"row 0 target K too large: {K}")
    comps = _body_components(grid)
    if not comps:
        errs.append("no body clusters below row 0")
        return errs
    counts = []
    for cells in comps:
        colors = [grid[r][c] for r, c in cells]
        if 1 in colors:
            errs.append("body cluster uses row-marker color 1")
        if len(colors) != len(set(colors)):
            errs.append("body chain reuses a color, so objects may merge ambiguously")
        if not _is_path_component(cells):
            errs.append(f"body component of size {len(cells)} is not a simple path")
        counts.append(_articulation_count(cells))
    if counts.count(K) != 1:
        errs.append(f"expected exactly one cluster with articulation count K={K}, got counts={counts}")
    for i, a in enumerate(comps):
        aset = set(a)
        for b in comps[i + 1:]:
            if any(max(abs(r1 - r2), abs(c1 - c2)) <= 1 for r1, c1 in aset for r2, c2 in b):
                errs.append("body clusters are not separated by a 1-cell halo")
                break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        k_lo, k_hi, nd_hi = 0, 2, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 22)
        w = ctx.draw_int("grid_w", 15, 22)
        k_lo, k_hi, nd_hi = 1, 5, 3
    else:
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 17)
        k_lo, k_hi, nd_hi = 0, 4, 2
    rng = ctx.draw_rng("layout")

    K = rng.randint(k_lo, k_hi)             # target articulation count
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]

    # Target chain: m = K+2 cells -> a path with K articulation objects. (K=0 -> a
    # 2-cell edge, 0 articulations.)
    if not _try_chain(g, occ, K + 2, h, w, rng):
        # deterministic fallback: a horizontal K+2 chain near the top-left
        g = full_grid(h, w, 0)
        cols = [2, 3, 4, 5, 6, 7, 8, 9]
        for i in range(K + 2):
            g[1][i] = cols[i % len(cols)]
        # row-0 ones
        for i in range(K):
            g[0][i] = 1
        return g

    # Decoy chains: different lengths -> different articulation counts (never == K), so
    # the rule's 'cluster with K articulations' uniquely selects the target.
    n_decoy = rng.randint(0, nd_hi)
    used_counts = {K}
    for _ in range(n_decoy * 3):
        if n_decoy <= 0:
            break
        # pick a decoy articulation count != K (length md = count+2)
        choices = [c for c in range(0, 6) if c not in used_counts and c + 2 <= max(w, h) - 1]
        if not choices:
            break
        dc_k = rng.choice(choices)
        if _try_chain(g, occ, dc_k + 2, h, w, rng):
            used_counts.add(dc_k)
            n_decoy -= 1

    # Row 0: K color-1 cells (K = target articulation count). Place at distinct columns.
    for c in rng.sample(range(w), K) if K > 0 else []:
        g[0][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        return g
    if name == "single_motif":
        # one 2-cell chain (0 articulations) + 0 row-0 ones -> rule outputs it
        g[2][2] = 4; g[2][3] = 5
        return g
    if name == "all_same_color":
        # touching same-color cells merge into one object (not a multi-object chain)
        for r, c in [(2, 2), (2, 3), (2, 4)]:
            g[r][c] = 4
        return g
    return g
