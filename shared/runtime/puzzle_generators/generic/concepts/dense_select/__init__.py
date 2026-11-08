"""DENSE_SELECT concept family: object selection / filtering on a DENSE field.

Closes the eval gap on tasks that place a HANDFUL of SUBSTANTIAL objects on a
LARGE grid and KEEP or REMOVE objects by a property:

  - gen1: keep ONLY the single LARGEST object (erase all others)         (size)
  - gen2: keep ONLY the solid SQUARES (erase every non-square)           (shape predicate)
  - gen3: keep ONLY the unique odd-one-out shape (erase the repeated ones)(uniqueness)

The selection concept (keep/remove a subset of components by a property)
appears in all three. Inputs are tuned against the eval density envelope:
input area ~250-500, 6-16 multi-cell components of 3-15 cells, 4-6 colors,
every component separated by a >=1 bg moat (8-neighborhood) so each placed
shape is exactly one 4-connected component and nothing merges.

Each generator FIXES one transform and resamples the INPUT to emit a full
multi-pair task whose pairs all share ONE Racket `program`. The Python `apply`
is byte-exact with what the Racket `program` produces (proven over >=25 random
seeds in each file's __main__ via RacketBridge).

Shared parity / measurement / placement helpers live here so the bridge wiring
and the Python mirror of `(objects g)` are defined ONCE.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Parity harness (mirrors the extraction family's helper)
# ---------------------------------------------------------------------------

def parity_check(generate_task, *, n=25, version_label=""):
    """Run `generate_task` over n seeds, eval its program body in Racket,
    assert byte-exact equality with every pair's stored output.

    Returns (passed, total). Prints the per-seed first failure if any.
    The program is `(rule! (lambda (g) BODY))`; we eval BODY directly against
    a freshly-defined `g` in the bridge.
    """
    from arc_repl.racket_bridge import RacketBridge

    b = RacketBridge()
    passed = 0
    total = 0
    first_fail = None
    for seed in range(n):
        task = generate_task(seed)
        body = _program_body(task["program"])
        for split in ("train", "test"):
            for pair in task[split]:
                total += 1
                b.define_grid("g", pair["input"])
                got = b.eval_text(body)
                if got == pair["output"]:
                    passed += 1
                elif first_fail is None:
                    first_fail = {
                        "seed": seed, "split": split, "body": body,
                        "py_out": pair["output"], "rkt_out": got,
                        "input_dims": (len(pair["input"]), len(pair["input"][0])),
                    }
    if first_fail is not None:
        print("FIRST MISMATCH:", first_fail)
    tag = f" [{version_label}]" if version_label else ""
    print(f"PARITY: {passed}/{total} exact{tag}")
    return passed, total


def _program_body(program: str) -> str:
    """Extract BODY from `(rule! (lambda (g) BODY))` by paren-matching."""
    marker = "(lambda (g)"
    i = program.index(marker) + len(marker)
    depth = 1
    j = i
    while j < len(program) and depth > 0:
        if program[j] == "(":
            depth += 1
        elif program[j] == ")":
            depth -= 1
        j += 1
    return program[i:j - 1].strip()


def measure(generate_task, *, n=25):
    """Print avg input area + avg component count across n seeds (every pair).
    Returns (avg_area, avg_comps, min_comps, max_comps)."""
    areas = []
    comps = []
    for seed in range(n):
        task = generate_task(seed)
        for split in ("train", "test"):
            for pair in task[split]:
                g = pair["input"]
                areas.append(len(g) * len(g[0]))
                comps.append(len(py_objects(g)))
    avg_a = sum(areas) / len(areas)
    avg_c = sum(comps) / len(comps)
    print(f"AREA: avg={avg_a:.1f} (min={min(areas)}, max={max(areas)})  "
          f"COMPS: avg={avg_c:.1f} (min={min(comps)}, max={max(comps)})")
    return avg_a, avg_c, min(comps), max(comps)


# ---------------------------------------------------------------------------
# Python mirror of the prelude object model
# ---------------------------------------------------------------------------

def py_objects(g, bg=0):
    """Mirror `(objects g)` = `(find-objects g 0 4)`: same-COLOR 4-connected
    components, returned in row-major order of their first-encountered cell.

    Each object is a dict {color, cells (list of [r,c]), size}. Matches the
    prelude's scan order (for r, for c) so any tie-break that resolves by
    object order is reproducible.
    """
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    objs = []
    for r in range(h):
        for c in range(w):
            color = g[r][c]
            if color == bg or seen[r][c]:
                continue
            cells = []
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append([cr, cc])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            objs.append({"color": color, "cells": cells, "size": len(cells)})
    return objs


def obj_bbox(obj):
    rs = [c[0] for c in obj["cells"]]
    cs = [c[1] for c in obj["cells"]]
    return min(rs), min(cs), max(rs), max(cs)


def is_square(obj):
    """Mirror `(square? obj)`: solid N×N (bbox is square AND fully filled)."""
    r1, c1, r2, c2 = obj_bbox(obj)
    hh = r2 - r1 + 1
    ww = c2 - c1 + 1
    return hh == ww and obj["size"] == hh * ww


def norm_shape(cells):
    """Mirror the normalization inside `same-shape?`: shift so min-r=min-c=0,
    return a frozenset of (r,c). Color-blind, rotation-sensitive."""
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    rmin, cmin = min(rs), min(cs)
    return frozenset((r - rmin, c - cmin) for r, c in cells)


def erase_objects(g, objs_to_erase, bg=0):
    """Mirror folding `erase-cells` over a set of objects: their cells -> bg."""
    out = [row[:] for row in g]
    for obj in objs_to_erase:
        for r, c in obj["cells"]:
            out[r][c] = bg
    return out


# ---------------------------------------------------------------------------
# Shape generation + placement engine
# ---------------------------------------------------------------------------

def make_blob(rng, size):
    """Connected multi-cell shape of EXACTLY `size` cells via a random growth
    walk. Returned normalized (min-r=min-c=0) as a sorted list of [r,c]."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size:
        br, bc = rng.choice(frontier)
        cand = [(br + dr, bc + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if (br + dr, bc + dc) not in cells]
        if not cand:
            frontier = [p for p in cells]  # reseed from any cell
            continue
        nc = rng.choice(cand)
        cells.add(nc)
        frontier.append(nc)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    rmin, cmin = min(rs), min(cs)
    return sorted([[r - rmin, c - cmin] for r, c in cells])


def solid_square(n):
    """Solid n×n square as normalized [r,c] cells (square? -> True)."""
    return [[r, c] for r in range(n) for c in range(n)]


def _cells_form_square(cells):
    """Would these cells satisfy square? (solid bbox AND square bbox)."""
    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    hh = max(rs) - min(rs) + 1
    ww = max(cs) - min(cs) + 1
    return hh == ww and len(cells) == hh * ww


def make_nonsquare_blob(rng, size, tries=40):
    """A blob of `size` cells that is NOT a solid square (so square? is False)."""
    for _ in range(tries):
        b = make_blob(rng, size)
        if not _cells_form_square(b):
            return b
    # extremely unlikely fallback: append a stray cell to break squareness
    return make_blob(rng, size + 1)


def place_shapes(rng, gh, gw, shapes_colors, tries=300, bg=0):
    """Place each (cells, color) onto a gh×gw bg grid at a random position with
    an 8-neighborhood bg moat, so every placed shape is its own isolated
    4-connected component. Returns (grid, n_placed). Shapes that cannot be
    placed after `tries` attempts are skipped (kept deterministic by rng).

    `bg` defaults to 0 for the historical generators, but callers can now use a
    nonzero modal background while keeping the same object semantics by passing
    the same bg to `py_objects`, `objects`, and `erase-cells`.
    """
    g = [[bg] * gw for _ in range(gh)]
    forbidden = [[False] * gw for _ in range(gh)]
    placed = 0
    for cells, color in shapes_colors:
        H = max(r for r, _ in cells) + 1
        W = max(c for _, c in cells) + 1
        if H > gh or W > gw:
            continue
        for _ in range(tries):
            r0 = rng.randint(0, gh - H)
            c0 = rng.randint(0, gw - W)
            if all(not forbidden[r0 + dr][c0 + dc] for dr, dc in cells):
                for dr, dc in cells:
                    g[r0 + dr][c0 + dc] = color
                for dr, dc in cells:
                    for er in (-1, 0, 1):
                        for ec in (-1, 0, 1):
                            rr, cc = r0 + dr + er, c0 + dc + ec
                            if 0 <= rr < gh and 0 <= cc < gw:
                                forbidden[rr][cc] = True
                placed += 1
                break
    return g, placed
