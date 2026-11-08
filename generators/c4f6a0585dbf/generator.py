"""Generator for 7df24a62.

Rule: the SOURCE TEMPLATE is the bbox of the color-1 cells (with the
color-4 PORT cells inside it). Wherever a D4 transform places >=2 of the
template's ports exactly on existing color-4 cells, the template's
missing color-1 cells are stamped in. The rule only turns 0-cells into 1.

Canonical scene: 23x23 grids with ONE solid color-1 rectangle (bbox
3x4..5x5, 10..22 ones) whose 2..3 interior holes are color-4 ports,
plus a scattered field of 17..47 color-4 cells (singletons and a few
dominoes) outside — the candidate port targets. Every default draw
PLANTS one D4-transformed copy of the template's port pattern at a
fresh anchor, so the rule always has at least one non-self trigger.

Variable geometry: grid_h/w, n_fours, and sampled block size. Port
color is fixed at 4 by the canonical rule. Supported textures are the
degenerates no_targets and full_grid (oracle-total).
no_template was removed: the oracle needs min/max of the color-1 cells
and crashes on an empty ones list.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c4f6a0585dbf"
# Preserve the sampling version so canonical seed/index draws stay unchanged.
VERSION = "3.1.0"
TASK_ID = "c4f6a0585dbf"
RULE_HASH = "d401b3cd92ff"
SUMMARY = (
    "0-bg 23x23 with ONE solid color-1 rectangle (2..3 interior color-4 "
    "ports) plus 17..47 scattered color-4 cells; the rule stamps the "
    "template's 1-cells wherever a D4 transform aligns >=2 ports."
)

INVARIANTS = [
    "background 0; colors exactly {0, 1, 4} with canonical port color 4",
    "exactly one color-1 connected block: a SOLID rectangle, bbox 3x4..5x5",
    "2..3 port cells strictly inside the block bbox (interior holes)",
    "17..47 total port-color cells; outside components are singletons or dominoes",
]

DEGENERATE_TEXTURES = ("no_targets", "full_grid")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":       {"type": "int", "default": "band rng 20..26 (canonical "
                     "always 23)", "valid": "18..30"},
    "grid_w":       {"type": "int", "default": "band rng 20..26",
                     "valid": "18..30"},
    "n_fours":      {"type": "int", "default": "band rng 17..47",
                     "valid": "17..47"},
    "texture":      {"type": "str", "default": "none (canonical scene)",
                     "valid": "|".join(DEGENERATE_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Canonical (bh, bw) block bboxes and their transposes.
_BLOCK_BBOXES = ((3, 4), (4, 3), (4, 4), (5, 4), (4, 5), (5, 5))


def _components(grid, val):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != val or seen[r][c]:
                continue
            stack, cells = [(r, c)], set()
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == val):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _port_color(grid):
    """The unique non-{0,1} color, or None."""
    xs = sorted({v for row in grid for v in row} - {0, 1})
    return xs[0] if len(xs) == 1 else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all canonical pairs
    satisfy them): rectangular grid inside the declared 18..30 envelope;
    colors exactly {0, 1, 4} with canonical port color 4;
    exactly one color-1 block — a solid rectangle with bbox <= 5x5 and
    10..22 cells; 2..3 color-4 ports strictly inside its bbox; 17..47 total
    color-4 cells with every outside-4 component a singleton or domino.
    no_targets (4 cells only inside the block bbox) and full_grid (all 1s)
    are declared degenerates; grids with no color-1 cells are REJECTED
    (the oracle needs the block bbox and crashes on an empty ones list)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    bad = sorted({v for row in grid for v in row} - {0, 1, 4})
    if bad:
        errs.append(f"unsupported colors outside canonical {{0,1,4}}: {bad}")
        return errs
    if not (18 <= h <= 30 and 18 <= w <= 30):
        errs.append(f"dims {h}x{w} outside the declared 18..30 envelope")
        return errs
    flat = [v for row in grid for v in row]
    if len(set(flat)) == 1:
        if flat[0] != 1:
            errs.append(f"single-color grid of {flat[0]} is not a lawful "
                        "input (full_grid is all-1)")
        return errs
    xcol = 4 if 4 in flat else None
    ones = _components(grid, 1)
    if not ones:
        errs.append("no color-1 block (the oracle needs the ones bbox)")
        return errs
    if len(ones) != 1:
        errs.append(f"{len(ones)} separate color-1 components (exactly one "
                    "block allowed)")
        return errs
    cells = ones[0]
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    bh, bw = r2 - r1 + 1, c2 - c1 + 1
    if bh > 5 or bw > 5 or bh < 3 or bw < 3:
        errs.append(f"color-1 block bbox {bh}x{bw} outside 3x3..5x5")
    if not 10 <= len(cells) <= 22:
        errs.append(f"color-1 block of {len(cells)} cells outside "
                    "canonical 10..22")
    if xcol is None:
        errs.append(
            "missing literal color-4 ports (only full_grid may omit color 4)"
        )
        return errs
    ports = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
             if grid[r][c] == xcol]
    non_port_holes = [
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
        if grid[r][c] not in (1, xcol)
    ]
    if non_port_holes:
        errs.append(
            f"{len(non_port_holes)} non-port holes inside the color-1 block bbox"
        )
    if any(not (r1 < r < r2 and c1 < c < c2) for r, c in ports):
        errs.append("all ports inside the block bbox must be strictly interior")
    if not 2 <= len(ports) <= 3:
        errs.append(f"{len(ports)} ports inside the block bbox "
                    "(canonical 2..3 ports)")
    outside = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] == xcol and not (r1 <= r <= r2 and c1 <= c <= c2)]
    if not outside:
        return errs  # no_targets degenerate (declared): valid ports, no candidates
    n4 = len(ports) + len(outside)
    if not 17 <= n4 <= 47:
        errs.append(f"{n4} total port-color cells outside canonical 17..47")
    oset = set(outside)
    ocomps = []
    while oset:
        stack = [oset.pop()]
        comp = [stack[0]]
        while stack:
            a, b = stack.pop()
            for nb in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                if nb in oset:
                    oset.remove(nb)
                    stack.append(nb)
                    comp.append(nb)
        ocomps.append(len(comp))
    if any(n > 2 for n in ocomps):
        errs.append("outside port-color components must be singletons or "
                    "dominoes (canonical allows no larger clusters)")
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): n_ones (block size), n_fours
    (total port-color cells), n_ports (inside the block bbox)."""
    ones = _components(grid, 1)
    xcol = _port_color(grid)
    n4 = sum(1 for row in grid for v in row if v not in (0, 1))
    n_ports = 0
    if ones and xcol is not None:
        cells = ones[0]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        n_ports = sum(1 for r in range(len(grid)) for c in range(len(grid[0]))
                      if grid[r][c] == xcol and r1 <= r <= r2 and c1 <= c <= c2)
    return {"n_ones": len(ones[0]) if ones else 0, "n_fours": n4,
            "n_ports": n_ports}


def _make_block(rng):
    """A SOLID rectangle (bbox from the canonical set) whose 2..3 interior
    holes become ports; port 4-components never exceed a domino (canonical
    geometry)."""
    for _ in range(60):
        bh, bw = _BLOCK_BBOXES[rng.randrange(len(_BLOCK_BBOXES))]
        interior = [(r, c) for r in range(1, bh - 1) for c in range(1, bw - 1)]
        n_ports = rng.randint(2, 3)
        if len(interior) < n_ports:
            continue
        if not 10 <= bh * bw - n_ports <= 22:
            continue
        ports = rng.sample(interior, n_ports)
        # port 4-connected components must be singletons or dominoes
        pset = set(ports)
        comps = []
        while pset:
            stack = [pset.pop()]
            comp = [stack[0]]
            while stack:
                a, b = stack.pop()
                for nb in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if nb in pset:
                        pset.remove(nb)
                        stack.append(nb)
                        comp.append(nb)
            comps.append(len(comp))
        if any(n > 2 for n in comps):
            continue
        pset = set(ports)
        cells = ([(r, c, 1) for r in range(bh) for c in range(bw)
                  if (r, c) not in pset]
                 + [(r, c, 4) for (r, c) in ports])
        return cells, bh, bw
    raise ValueError("cannot build a canonical block")


def _transform(p, idx):
    r, c = p
    if idx == 0:
        return (r, c)
    if idx == 1:
        return (c, -r)
    if idx == 2:
        return (-r, -c)
    if idx == 3:
        return (-c, r)
    if idx == 4:
        return (r, -c)
    if idx == 5:
        return (-c, -r)
    if idx == 6:
        return (-r, c)
    return (c, r)


def _pc_comp_size(g, r, c, color):
    """4-connected component size of the color cell at (r, c)."""
    seen = {(r, c)}
    stack = [(r, c)]
    h, w = len(g), len(g[0])
    while stack:
        a, b = stack.pop()
        for dr, dc in _DIRS4:
            na, nb = a + dr, b + dc
            if (0 <= na < h and 0 <= nb < w and (na, nb) not in seen
                    and g[na][nb] == color):
                seen.add((na, nb))
                stack.append((na, nb))
    return len(seen)


def _plant_trigger(g, occ, base, bh, bw, rng, port_color=4):
    """Plant one guaranteed non-self rule trigger: a D4-transformed copy of
    the template's port pattern at a fresh anchor, so the rule stamps the
    transformed 1-rectangle there."""
    entries = [(r, c, v) for (r, c, v) in base]
    h, w = len(g), len(g[0])
    order = list(range(8))
    rng.shuffle(order)
    for idx in order:
        raws = [_transform((r, c), idx) for (r, c, _v) in entries]
        mr = min(r for r, _ in raws)
        mc = min(c for _, c in raws)
        norm = [(r - mr, c - mc, v) for (r, c), (_r, _c, v)
                in zip(raws, entries)]
        th = max(r for r, _, _ in norm) + 1
        tw = max(c for _, c, _ in norm) + 1
        anchors = [(ar, ac) for ar in range(h - th + 1)
                   for ac in range(w - tw + 1)]
        rng.shuffle(anchors)
        for ar, ac in anchors:
            cells = [(ar + r, ac + c) for (r, c, _v) in norm]
            if any(occ[r][c] for (r, c) in cells):
                continue
            # also keep a one-cell moat so planted ports stay singletons /
            # dominoes of the template's own geometry
            moat = {(r + dr, c + dc) for (r, c) in cells
                    for dr, dc in _DIRS4
                    if 0 <= r + dr < h and 0 <= c + dc < w}
            if any(occ[r][c] and g[r][c] != 1 for (r, c) in moat):
                continue
            for (r, c, v) in norm:
                if v == 4:
                    g[ar + r][ac + c] = port_color
                occ[ar + r][ac + c] = True
            return sum(1 for (_r, _c, v) in norm if v == 4)
    return 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("palette_kind") is not None:
        raise ValueError(
            "palette_kind is unsupported: the canonical rule requires port color 4")
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed diagnostic layout; "
                f"it takes no other overrides, got {extra}")
        return _draw_from_degenerate(tex, ctx.draw_rng("layout"))
    if tex is not None:
        raise ValueError(f"unknown texture {tex!r}; valid: {DEGENERATE_TEXTURES}")
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        hr = (20, 22)
    elif difficulty == "hard":
        hr = (24, 26)
    else:
        hr = (22, 24)

    # Canonical-form prior (KRF-0003): ~35% of fully-unoverridden draws pin
    # the official 23x23 canvas.
    if not any(k in overrides for k in ("grid_h", "grid_w")):
        if ctx.draw_rng("canonical_prior").random() < 0.35:
            for label, value in (("grid_h", 23), ("grid_w", 23)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)

    h = ctx.draw_int("grid_h", *( (18, 30) if overrides.get("grid_h") is not None
                                  else hr))
    w = ctx.draw_int("grid_w", *( (18, 30) if overrides.get("grid_w") is not None
                                  else hr))
    n4 = ctx.draw_int("n_fours", *( (17, 47) if overrides.get("n_fours") is not None
                                    else (17, 47)))
    port_color = 4
    base, bh, bw = _make_block(rng)
    block_cells = [(r, c) for (r, c, v) in base]
    n_ports = sum(1 for (r, c, v) in base if v == 4)
    ctx.overrides["n_ones"] = len(block_cells) - n_ports
    ctx.draw_int("n_ones", ctx.overrides["n_ones"], ctx.overrides["n_ones"])
    ctx.overrides["n_ports"] = n_ports
    ctx.draw_int("n_ports", n_ports, n_ports)

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = False
        for _t in range(80):
            sr = rng.randint(0, h - bh)
            sc = rng.randint(0, w - bw)
            cells = [(sr + r, sc + c) for (r, c) in block_cells]
            if any(occ[r][c] for r, c in cells):
                continue
            for (r, c, v) in base:
                g[sr + r][sc + c] = v if v == 1 else port_color
                occ[sr + r][sc + c] = True
            placed = True
            break
        if not placed:
            continue
        # guaranteed non-self trigger (keeps the demo visible)
        n_planted = _plant_trigger(g, occ, base, bh, bw, rng,
                                           port_color)
        if not n_planted:
            continue
        # scattered port-color cells, guarded so no outside component ever
        # exceeds a domino (canonical geometry): a new cell may touch at
        # most one existing port-color cell, and only a singleton.
        n_scatter = n4 - n_ports - n_planted
        got = 0
        for _t in range(n_scatter * 200):
            if got >= n_scatter:
                break
            r = rng.randrange(h)
            c = rng.randrange(w)
            if occ[r][c]:
                continue
            nbrs = [(r + dr, c + dc) for dr, dc in _DIRS4
                    if 0 <= r + dr < h and 0 <= c + dc < w
                    and g[r + dr][c + dc] == port_color]
            if len(nbrs) > 1:
                continue
            if nbrs and _pc_comp_size(g, nbrs[0][0], nbrs[0][1],
                                      port_color) > 1:
                continue
            g[r][c] = port_color
            occ[r][c] = True
            got += 1
        if got < n_scatter:
            continue
        errs = self_check(g)
        if not errs:
            return g
    raise ValueError(
        f"cannot place the block + trigger + {n_scatter} scattered port "
        f"cells on {h}x{w}")


def _draw_from_degenerate(name, rng):
    g = full_grid(23, 23, 0)
    if name == "no_targets":
        # solid 3x4 block with 2 interior ports and no candidate targets
        for dr in range(3):
            for dc in range(4):
                g[10 + dr][10 + dc] = 1
        g[11][11] = 4
        g[11][12] = 4
        return g
    if name == "full_grid":
        for r in range(23):
            for c in range(23):
                g[r][c] = 1
        return g
    return g
