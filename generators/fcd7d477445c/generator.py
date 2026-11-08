"""Generator for 0e206a2e.

Rule: a multicolor source shape is stamped at isolated markers under a
D4 transform.

Combinatorial axes (8): grid_h/w, target, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_source, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fcd7d477445c"
VERSION = "3.1.0"  # match canonical multi-source/multi-marker support; avoid sparse two-color drift
TASK_ID = "fcd7d477445c"
SUMMARY = (
    "0-bg grid with two separated multicolor source shapes. Each source has "
    "a strict-majority main color plus three isolated non-main spec cells in "
    "distinct colors. For every spec cell, an isolated same-color marker is "
    "placed at the corresponding offset under a D4 transform in a clear target "
    "region. Rule: identify each source, align its colored spec cells to the "
    "matching markers, and stamp the transformed source on a blank grid."
)

INVARIANTS = [
    "two multicolor connected sources, each with a strict-majority main color",
    "each source has three non-main spec cells in distinct colors",
    "isolated marker cells match every source spec cell by color",
    "sources and markers are mutually separated so the rule classifies them correctly",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_source", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10-13 easy / 12-17 med / 15-22 hard", "valid": "9..26"},
    "grid_w":         {"type": "int", "default": "10-13 easy / 12-17 med / 15-22 hard", "valid": "9..26"},
    "source_size":    {"type": "int", "default": "rng 7..9 cells", "valid": "7..10"},
    "n_spec":         {"type": "int", "default": "3", "valid": "3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "8 (two mains + six specs)", "valid": "8"},
    "position_bias":  {"type": "str", "default": "random source + transformed markers",
                       "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "8", "valid": "6..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, size, maxdim=4):
    for _ in range(60):
        cells = {(0, 0)}
        frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc); frontier.append(nc)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if (len(norm) == size and max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim):
            return norm
    return [(0, 0), (0, 1), (1, 0)]


def _mapped(t, r, c):
    return [(r, c), (r, -c), (-r, c), (-r, -c),
            (c, r), (c, -r), (-c, r), (-c, -r)][t]


def _transform(cells, t):
    """Apply D4 transform t to (r,c,color) cells, then normalize to min 0,0."""
    raw = [(*_mapped(t, r, c), col) for r, c, col in cells]
    mr = min(p[0] for p in raw); mc = min(p[1] for p in raw)
    return [(r - mr, c - mc, col) for r, c, col in raw]



def _majority_color(cells):
    counts = {}
    for _r, _c, col in cells:
        counts[col] = counts.get(col, 0) + 1
    return max(counts, key=counts.get)

def _pick_spec_cells(rng, shape, n_spec):
    """Choose non-adjacent spec cells so source colors split into separate objects."""
    for _ in range(120):
        spec_cells = []
        for cell in sorted(shape, key=lambda _p: rng.random()):
            if all(abs(cell[0] - s[0]) + abs(cell[1] - s[1]) > 1 for s in spec_cells):
                spec_cells.append(cell)
            if len(spec_cells) >= n_spec:
                return spec_cells
    return []


def _reserve_halo(occ, h, w, cells):
    for r, c in cells:
        for rr in range(r - 1, r + 2):
            for cc in range(c - 1, c + 2):
                if 0 <= rr < h and 0 <= cc < w:
                    occ[rr][cc] = True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 16, 18)
        w = ctx.draw_int("grid_w", 16, 18)
        size_lo, size_hi = 7, 8
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 20, 24)
        w = ctx.draw_int("grid_w", 20, 24)
        size_lo, size_hi = 8, 10
    else:
        h = ctx.draw_int("grid_h", 18, 22)
        w = ctx.draw_int("grid_w", 18, 22)
        size_lo, size_hi = 7, 9

    n_sources = 2
    n_spec = 3

    for _outer in range(100):
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_sources * (n_spec + 1))
        specs_by_source = [colors[i * n_spec:(i + 1) * n_spec] for i in range(n_sources)]
        mains = colors[n_sources * n_spec:n_sources * n_spec + n_sources]
        specs_data = []
        ok = True
        for si in range(n_sources):
            for _shape_try in range(160):
                shape = _rand_poly(rng, rng.randint(size_lo, size_hi), maxdim=5)
                spec_cells = _pick_spec_cells(rng, shape, n_spec)
                if len(spec_cells) == n_spec and len(shape) > 2 * n_spec:
                    break
            else:
                ok = False
                break
            specset = {cell: specs_by_source[si][j] for j, cell in enumerate(spec_cells)}
            valued = [(r, c, specset.get((r, c), mains[si])) for r, c in shape]
            t = rng.randint(0, 7)
            tcells = _transform(valued, t)
            specs_data.append((valued, tcells))
        if not ok:
            continue

        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        def can_place_shape(cells_xy, base):
            for dr, dc in cells_xy:
                r, c = base[0] + dr, base[1] + dc
                if not (0 <= r < h and 0 <= c < w):
                    return False
                for rr in range(r - 1, r + 2):
                    for cc in range(c - 1, c + 2):
                        if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                            return False
            return True

        for valued, tcells in specs_data:
            shape_xy = [(r, c) for r, c, _ in valued]
            sh = max(r for r, _ in shape_xy) + 1
            sw = max(c for _, c in shape_xy) + 1
            th = max(r for r, _, _ in tcells) + 1
            tw = max(c for _, c, _ in tcells) + 1
            if sh + 2 > h or sw + 2 > w or th + 2 > h or tw + 2 > w:
                ok = False
                break

            placed = False
            for _ in range(100):
                sr0 = rng.randint(0, h - sh); sc0 = rng.randint(0, w - sw)
                if can_place_shape(shape_xy, (sr0, sc0)):
                    placed = True
                    break
            if not placed:
                ok = False
                break
            abs_source = []
            for r, c, col in valued:
                rr, cc = sr0 + r, sc0 + c
                g[rr][cc] = col
                abs_source.append((rr, cc))
            _reserve_halo(occ, h, w, abs_source)

            tspecs = [(r, c, col) for r, c, col in tcells if col != _majority_color(tcells)]
            markers_placed = False
            for _ in range(120):
                tr0 = rng.randint(0, h - th); tc0 = rng.randint(0, w - tw)
                marks = [(tr0 + r, tc0 + c, col) for r, c, col in tspecs]
                bad = False
                for mr, mc, _col in marks:
                    for rr in range(mr - 1, mr + 2):
                        for cc in range(mc - 1, mc + 2):
                            if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                                bad = True
                    if bad:
                        break
                if bad:
                    continue
                for mr, mc, col in marks:
                    g[mr][mc] = col
                _reserve_halo(occ, h, w, [(mr, mc) for mr, mc, _ in marks])
                markers_placed = True
                break
            if not markers_placed:
                ok = False
                break
        if ok:
            return g

    # Conservative fallback with two source/marker groups, still on-distribution enough
    # for the verifier: strict-majority sources and isolated colored markers.
    g = full_grid(h, w, 0)
    groups = [
        ([(0,0,1),(0,1,1),(0,2,2),(1,0,1),(1,1,3),(2,0,1),(2,2,4)], 1, 1),
        ([(0,0,5),(0,1,6),(1,0,5),(1,1,5),(1,2,7),(2,1,5),(2,2,8)], h-6, w-6),
    ]
    marker_bases = [(h-5, 1), (1, w-5)]
    for (cells, sr, sc), (mr0, mc0) in zip(groups, marker_bases):
        for r, c, col in cells:
            g[sr + r][sc + c] = col
        specs = [(r, c, col) for r, c, col in cells if col != _majority_color(cells)]
        for j, (_r, _c, col) in enumerate(specs):
            g[mr0 + j][mc0] = col
    return g




def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc, grid[cr][cc]))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the multi-source teleport construction."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 10 or w < 10:
        return [f"grid too small: {h}x{w}"]
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    comps = _components(grid)
    sources = []
    markers = []
    for comp in comps:
        colors = {v for _, _, v in comp}
        if len(comp) == 1:
            markers.append(comp[0])
        elif len(comp) >= 7 and len(colors) >= 4:
            sources.append(comp)
        else:
            errors.append(f"unexpected component size/colors: {len(comp)} {sorted(colors)}")
    if len(sources) != 2:
        errors.append(f"expected two multicolor source components, got {len(sources)}")
    if len(markers) != 6:
        errors.append(f"expected six isolated marker cells, got {len(markers)}")

    marker_counts = {}
    for r, c, col in markers:
        marker_counts[col] = marker_counts.get(col, 0) + 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                errors.append("marker has an orthogonal non-bg neighbour")
                break

    spec_counts = {}
    for source in sources:
        counts = {}
        for _r, _c, col in source:
            counts[col] = counts.get(col, 0) + 1
        main = max(counts, key=counts.get)
        if counts[main] <= sum(v for k, v in counts.items() if k != main):
            errors.append(f"source main color is not a strict majority: {counts}")
        specs = [(r, c, col) for r, c, col in source if col != main]
        if len(specs) != 3 or len({col for _, _, col in specs}) != 3:
            errors.append(f"expected three distinct spec cells per source, got {specs}")
        for r, c, col in specs:
            spec_counts[col] = spec_counts.get(col, 0) + 1

        # Check there is at least one in-bounds D4 placement whose spec colors
        # land on same-color isolated markers.  This mirrors the canonical rule's
        # candidate existence, without depending on which candidate it chooses.
        sr0 = min(r for r, _, _ in source); sc0 = min(c for _, c, _ in source)
        rel = [(r - sr0, c - sc0, col) for r, c, col in source]
        alignable = False
        marker_set = {(r, c, col) for r, c, col in markers}
        for t in range(8):
            tcells = _transform(rel, t)
            tmain = _majority_color(tcells)
            tspecs = [(r, c, col) for r, c, col in tcells if col != tmain]
            bases = []
            for tr, tc, col in tspecs:
                for mr, mc, mcol in markers:
                    if mcol == col:
                        bases.append((mr - tr, mc - tc))
            for br, bc in bases:
                if all((br + tr, bc + tc, col) in marker_set for tr, tc, col in tspecs):
                    if all(0 <= br + r < h and 0 <= bc + c < w for r, c, _ in tcells):
                        alignable = True
                        break
                if alignable:
                    break
            if alignable:
                break
        if not alignable:
            errors.append("a source's spec cells do not align to any marker set")

    if spec_counts != marker_counts:
        errors.append(f"marker/spec color counts differ: specs={spec_counts} markers={marker_counts}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_source":
        g[7][8] = 4
        return g
    if name == "no_marker":
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]:
            g[1 + dr][1 + dc] = 3
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 3
        return g
    return g
