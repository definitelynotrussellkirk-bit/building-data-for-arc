"""Generator for arc_puzzle_bank_sixth21:H40 — stamp a recolored template at 9-markers.

Rule: cells (0,0)=a and (0,1)=b are a color legend. The body (rows 1+)
holds ONE template made of 5- and 6-cells (the largest non-9 component).
The template is cropped to its bbox, recolored 5->a / 6->b, then FLIPPED
LEFT-RIGHT and stamped (transparent on 0) at every 9-marker's position
(marker = top-left of the stamp). Output is an empty grid + all stamps.

This generator draws: the (a, b) legend, one 5/6 template in the body,
and K scattered 9-markers with room for the stamp.

Combinatorial axes: grid size, template shape (5/6 polyomino), legend
colors a/b, number and positions of 9-markers.
Degenerates: no_markers, no_template, single_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e4e8588ae61"
VERSION = "2.1.0"  # require all requested 9-markers and add executable self_check coverage
TASK_ID = "0e4e8588ae61"

SUMMARY = "(a,b) color legend + one 5/6 template in body + K 9-markers; rule stamps the recolored flipped template at each marker."

INVARIANTS = [
    "background is 0",
    "cells (0,0) and (0,1) hold the legend colors a (->5) and b (->6)",
    "exactly one connected 5/6 template in rows 1+",
    "1-3 isolated 9-markers, each with room for the stamp",
]

DEGENERATE_TEXTURES = ("no_markers", "no_template", "single_marker")

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "n_markers":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "template_size":  {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "legend_a":       {"type": "color", "default": "rng (!=0)", "valid": "1..9"},
    "legend_b":       {"type": "color", "default": "rng (!=0,!=a)", "valid": "1..9"},
    "texture":        {"type": "str", "default": "n/a (degenerates only)",
                       "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    """Connected polyomino of k cells, normalized to min (0,0)."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        nm_lo, nm_hi = 1, 2
        ts_lo, ts_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        nm_lo, nm_hi = 3, 5
        ts_lo, ts_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        nm_lo, nm_hi = 2, 4
        ts_lo, ts_hi = 3, 6

    for outer in range(60):
        g = full_grid(h, w, 0)
        a = int(overrides.get("legend_a", rng.randint(1, 9)))
        b = int(overrides.get("legend_b", rng.randint(1, 9)))
        if b == a:
            b = (a % 9) + 1
        g[0][0] = a; g[0][1] = b

        # --- template: a 5/6 polyomino placed in the body (rows 1+) ---
        tsize = int(overrides.get("template_size",
                                  rng.randint(ts_lo, ts_hi)))
        tcells = _build_motif(rng, tsize)
        th = max(r for r, _ in tcells) + 1
        tw = max(c for _, c in tcells) + 1
        if th + 1 >= h or tw >= w:
            continue
        # colour each template cell 5 or 6 (at least one of each when size>1)
        tcolors = [rng.choice((5, 6)) for _ in tcells]
        if tsize > 1 and len(set(tcolors)) == 1:
            tcolors[rng.randrange(len(tcolors))] = 11 - tcolors[0]
        placed = False
        for _ in range(120):
            # body rows start at 1
            tr = rng.randint(1, h - th); tc = rng.randint(0, w - tw)
            if not _free(g, tr, tc, tr + th - 1, tc + tw - 1):
                continue
            for (r, c), col in zip(tcells, tcolors):
                g[tr + r][tc + c] = col
            placed = True
            break
        if not placed:
            continue

        # --- 9-markers: each needs room for the th x tw stamp ---
        n_markers = int(overrides.get("n_markers",
                                      rng.randint(nm_lo, nm_hi)))
        markers_placed = 0
        for _ in range(n_markers):
            mok = False
            for _t in range(120):
                mr = rng.randint(0, h - th); mc = rng.randint(0, w - tw)
                # marker cell itself + the stamp footprint must be clear
                if not _free(g, mr, mc, mr + th - 1, mc + tw - 1):
                    continue
                g[mr][mc] = 9
                markers_placed += 1
                mok = True
                break
            if not mok:
                break
        if markers_placed == n_markers:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    g[0][0] = 2; g[0][1] = 3
    # one 5/6 template in the body
    for r, c in [(2, 2), (3, 2), (3, 3)]:
        g[r][c] = 5
    g[2][3] = 6
    if name == "no_markers":
        # template + legend but no 9-marker -> output empty grid
        return g
    if name == "no_template":
        # markers + legend but no 5/6 template -> nothing to stamp
        g2 = full_grid(h, w, 0)
        g2[0][0] = 2; g2[0][1] = 3
        g2[5][5] = 9; g2[7][8] = 9
        return g2
    if name == "single_marker":
        g[6][7] = 9
        return g
    return g



def _components_for_colors(grid, colors):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] not in colors:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                        (nr, nc) not in seen and grid[nr][nc] in colors):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if len(grid) < 2 or len(grid[0]) < 2:
        return ["grid too small for legend"]
    a, b = grid[0][0], grid[0][1]
    if a == 0 or b == 0 or a == b:
        errs.append("legend cells must be distinct non-zero colors")
    body = [row[:] for row in grid[1:]]
    comps56 = _components_for_colors(body, {5, 6})
    if len(comps56) != 1:
        errs.append(f"expected one connected 5/6 template in body, got {len(comps56)}")
    else:
        vals = {body[r][c] for r, c in comps56[0]}
        if not {5, 6}.issubset(vals):
            errs.append("template should exercise both 5 and 6 recolor branches")
    markers = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
               if grid[r][c] == 9 and (r, c) not in ((0, 0), (0, 1))]
    min_markers = 3 if difficulty == "hard" else 1 if difficulty == "easy" else 2
    if len(markers) < min_markers:
        errs.append(f"too few 9-markers: {len(markers)} < {min_markers}")
    return errs
