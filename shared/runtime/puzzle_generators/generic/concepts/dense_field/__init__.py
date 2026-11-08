"""DENSE_FIELD concept family: transforms on FULLY-COLORED grids.

Closes the pool's single biggest distribution gap vs eval: FILL DENSITY. Eval
inputs are ~73% non-background (large contiguous color regions); the pool was
~12% (a few small blobs on a black field). These generators emit grids that are
100% filled by a handful of LARGE contiguous regions — high density AND a LOW
component count (matching eval's ~5 components, not pixel noise).

  - gen1: learn a COLOR REMAP (palette bijection) and apply it everywhere   (recolor-map)
  - gen2: ... (future)

Each generator FIXES one transform and resamples the dense INPUT, emitting a
full multi-pair task whose pairs share ONE Racket `program`; the Python `apply`
is byte-exact with the Racket program (proven over >=25 seeds in __main__).

The parity / program-body harness is shared with the rest of the concept tree
(imported from dense_select) so it is defined ONCE; the density-aware measure +
the dense-partition builder live here.
"""
from __future__ import annotations

# DRY: the parity harness + Python object-model mirror are generic — reuse them.
from puzzle_generators.generic.concepts.dense_select import (  # noqa: F401
    parity_check, _program_body, py_objects,
)


def _non_bg_components(g, bg=0):
    """4-connected components of non-bg cells — the SAME definition the param-space
    tracker (distribution_audit.comps) uses. Color-blind: a fully-filled dense field
    is ONE component even with many colors (unlike color-aware py_objects)."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if g[r][c] == bg or seen[r][c]:
                continue
            n += 1
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] != bg:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
    return n


def _modal_bg(g):
    """Most common color — the SEMANTIC background. Counting non-bg cells against
    THIS rather than literal 0 avoids mistaking a colored background for occupancy."""
    from collections import Counter
    return Counter(v for row in g for v in row).most_common(1)[0][0]


def measure(generate_task, *, n=25):
    """Avg input area, component counts, and fill density under THREE definitions.

    The param-space tracker counts components and density against the MODAL
    background (not literal 0), so an "eval-like" claim must be made against the
    modal-bg numbers, not the color-aware object count. We print all three:
      - COLOR_COMPS : color-aware objects (py_objects) — highest count
      - NON_BG_COMPS: 4-conn components vs bg=0       — a filled field is 1
      - MODAL_COMPS : 4-conn components vs modal bg   — what the tracker uses
    and both zero-bg DENSITY and modal-bg NON-MODAL density."""
    areas, color_comps, non_bg_comps, modal_comps, dens, dens_nonmodal = [], [], [], [], [], []
    for seed in range(n):
        task = generate_task(seed)
        for split in ("train", "test"):
            for pair in task[split]:
                g = pair["input"]
                a = len(g) * len(g[0])
                bg = _modal_bg(g)
                nz = sum(1 for row in g for v in row if v != 0)
                nm = sum(1 for row in g for v in row if v != bg)
                areas.append(a)
                color_comps.append(len(py_objects(g)))
                non_bg_comps.append(_non_bg_components(g, 0))
                modal_comps.append(_non_bg_components(g, bg))
                dens.append(nz / a if a else 0.0)
                dens_nonmodal.append(nm / a if a else 0.0)
    avg = lambda xs: sum(xs) / len(xs)
    avg_a = avg(areas)
    print(f"AREA: avg={avg_a:.1f} (min={min(areas)}, max={max(areas)})  "
          f"COMPS: color={avg(color_comps):.1f} bg0={avg(non_bg_comps):.1f} modal={avg(modal_comps):.1f}  "
          f"DENSITY: zero-bg={avg(dens):.2f} non-modal={avg(dens_nonmodal):.2f}")
    return avg_a, avg(modal_comps), avg(dens_nonmodal)


def make_dense_partition(rng, gh, gw, palette):
    """A gh×gw grid FULLY tiled by a coarse rb×cb rectangular partition, each
    tile a random palette color. 100% filled; adjacent same-color tiles merge
    into larger regions, so the component count stays low (eval-like), not noise.

    Returns the grid (list of rows). No background cells.
    """
    rb = rng.randint(2, 4)
    cb = rng.randint(2, 4)
    # band boundaries (even-ish splits along each axis)
    rbnd = [round(i * gh / rb) for i in range(rb + 1)]
    cbnd = [round(j * gw / cb) for j in range(cb + 1)]
    tile_color = [[rng.choice(palette) for _ in range(cb)] for _ in range(rb)]
    g = [[0] * gw for _ in range(gh)]
    for ti in range(rb):
        for tj in range(cb):
            col = tile_color[ti][tj]
            for r in range(rbnd[ti], rbnd[ti + 1]):
                for c in range(cbnd[tj], cbnd[tj + 1]):
                    g[r][c] = col
    return g
