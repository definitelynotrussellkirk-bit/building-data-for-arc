"""DENSE_RECOLOR concept family: per-object recolor by a PROPERTY on a
dense field of substantial objects.

Each generator scatters a HANDFUL (6-12) of MULTI-CELL connected shapes
(3-12 cells each) across a LARGE grid (sides 16-22 -> area ~256-484),
every shape separated by a full 1-cell background halo so each is its
own 4-connected component. The input shapes all share ONE neutral
colour; the output RECOLORS every object by a property:

  - gen1: by SIZE EXTREMES   (largest -> A, smallest -> B, rest -> C)
  - gen2: by SHAPE CLASS     (square -> A, line -> B, other -> C)
  - gen3: by EXACT CELL-COUNT (size -> colour via a fixed map)

All pairs of a task share ONE Racket `program`; the Python `apply` is
byte-exact with what that program produces in a real Racket subprocess
(proven over >=25 random seeds per file via RacketBridge).

This module holds the shared, self-contained parity+density harness so
the bridge wiring and the eval-density measurement live in one place.
"""
from __future__ import annotations


# --------------------------------------------------------------------------
# 4-connected component finder (mirrors the prelude `objects` w/ bg=0).
def components(g, bg=0):
    """Return list of (color, cells) — one entry per 4-connected same-colour
    component. cells is a list of (r, c) tuples. Order is row-major by the
    component's first-discovered cell (matches find-objects), but every
    generator's transform here is order-independent."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == bg or seen[r][c]:
                continue
            col = g[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] \
                            and g[nr][nc] == col:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((col, cells))
    return comps


# --------------------------------------------------------------------------
# Polyomino + placement helpers (shared so each gen file stays compact, but
# imported — not editing the global primitives.py).
def random_blob(rng, size, maxdim=4):
    """A random connected polyomino of exactly `size` cells whose bounding
    box spans < maxdim in each axis. Returns normalised sorted (r, c) list."""
    cells = {(0, 0)}
    while len(cells) < size:
        cands = []
        for (r, c) in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    continue
                rs = [p[0] for p in cells] + [nb[0]]
                cs = [p[1] for p in cells] + [nb[1]]
                if max(rs) - min(rs) < maxdim and max(cs) - min(cs) < maxdim:
                    cands.append(nb)
        if not cands:
            maxdim += 1
            continue
        cells.add(rng.choice(cands))
    r0 = min(p[0] for p in cells)
    c0 = min(p[1] for p in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def place_shapes(rng, gh, gw, shapes, color, *, tries=300):
    """Stamp each normalised shape (a cell list) onto a gh x gw grid in
    `color`, keeping a full 8-neighbour background halo around every shape so
    each becomes its own isolated 4-connected component. Shapes that cannot
    be placed within `tries` attempts are SKIPPED. Returns (grid, n_placed)."""
    grid = [[0] * gw for _ in range(gh)]
    occ = [[False] * gw for _ in range(gh)]
    placed = 0
    for cells in shapes:
        bh = max(r for r, c in cells) + 1
        bw = max(c for r, c in cells) + 1
        if bh > gh or bw > gw:
            continue
        for _ in range(tries):
            r0 = rng.randint(0, gh - bh)
            c0 = rng.randint(0, gw - bw)
            abs_cells = [(r0 + r, c0 + c) for r, c in cells]
            clash = False
            for (r, c) in abs_cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < gh and 0 <= cc < gw and occ[rr][cc]:
                            clash = True
                            break
                    if clash:
                        break
                if clash:
                    break
            if clash:
                continue
            for (r, c) in abs_cells:
                grid[r][c] = color
                occ[r][c] = True
            placed += 1
            break
    return grid, placed


# --------------------------------------------------------------------------
def program_body(program: str) -> str:
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


def parity_and_stats(generate_task, *, n=25, version_label=""):
    """Build n tasks, eval each program body in a real Racket subprocess,
    require BYTE-EXACT equality on every pair, and report eval-density.

    A seed PASSES only if all of its pairs match. Prints `PARITY: P/n exact`
    and a DENSITY line with avg input area + avg component count."""
    from arc_repl.racket_bridge import RacketBridge

    b = RacketBridge()
    seed_pass = 0
    first_fail = None
    areas, comp_counts = [], []
    nonidentity = 0
    out_signatures = set()
    for seed in range(n):
        task = generate_task(seed)
        body = program_body(task["program"])
        all_ok = True
        for split in ("train", "test"):
            for pair in task[split]:
                gin, gout = pair["input"], pair["output"]
                areas.append(len(gin) * len(gin[0]))
                comp_counts.append(len(components(gin)))
                if gout != gin:
                    nonidentity += 1
                out_signatures.add(repr(gout))
                b.define_grid("g", gin)
                got = b.eval_text(body)
                if got != gout:
                    all_ok = False
                    if first_fail is None:
                        first_fail = {
                            "seed": seed, "split": split, "body": body,
                            "py_out": gout, "rkt_out": got,
                            "dims": (len(gin), len(gin[0])),
                        }
        if all_ok:
            seed_pass += 1
    if first_fail is not None:
        print("FIRST MISMATCH:", first_fail)
    tag = f" [{version_label}]" if version_label else ""
    print(f"PARITY: {seed_pass}/{n} exact{tag}")
    print(f"DENSITY: avg_area={sum(areas) / len(areas):.1f} "
          f"avg_comps={sum(comp_counts) / len(comp_counts):.2f} "
          f"(area {min(areas)}-{max(areas)}, comps {min(comp_counts)}-{max(comp_counts)})")
    print(f"SANITY: nonidentity_pairs={nonidentity}/{len(areas)} "
          f"distinct_outputs={len(out_signatures)}")
    return seed_pass, n
