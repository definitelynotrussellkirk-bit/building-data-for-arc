"""Generator for 10b:m69 — crop component with most holes.

Rule: of the connected components, exactly one has the maximum number
of bg cells inside its bbox (holes). Output is that component cropped.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components (no objects → rule has nothing to crop);
tied_holes (two components share max holes → rule's "exactly one
max" precondition fails, selector ambiguous); all_solid (all
components are solid rectangles, hole count = 0 across all →
selector returns whichever rng picks first, no clear pattern).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03d36f36821e"
VERSION = "3.1.2"  # + self_check
TASK_ID = "03d36f36821e"
SUMMARY = (
    "0-bg grid with 2-3 isolated components in distinct colors: one "
    "LADDER shape with k=2-3 enclosed chambers (varied dims and "
    "orientation) plus 1-2 distractors (1-hole rings of varied size, "
    "solids); rule crops the component with the most ENCLOSED "
    "0-REGIONS. (Old doc said 'bg cells inside bbox' — the rule "
    "counts enclosed REGIONS; and the old shape bank had exactly 2 "
    "fixed winners, capping uniq_out at ~13.)"
)

# Rivals: 'pick the biggest object' refuted by small multi-chamber
# winners beating large rings. 'count hole CELLS' refuted by boards
# where a big 1-chamber ring has more hole cells but fewer regions.
# 'crop loses the holes' refuted (interior bg survives in the crop).
# 3 demos with varied ladder dims/orientations.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 isolated 4-connected components, distinct colors",
    "exactly one component has strictly the most ENCLOSED 0-regions",
]

DEGENERATE_TEXTURES = ("tied_holes", "all_solid")
HELPFUL_TEXTURES = ("plain", "big_ring_decoy")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "grid_w":     {"type": "int", "default": "rng 12..15", "valid": "11..18"},
    "n_chambers": {"type": "int", "default": "rng 2..3", "valid": "2..4",
                   "doc": "Enclosed regions in the winning ladder."},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "plain|big_ring_decoy|tied_holes|all_solid",
                   "doc": "big_ring_decoy: a LARGE 1-hole ring with more "
                          "hole CELLS than the winner has — only region "
                          "counting picks the ladder."},
}


def _enclosed_regions(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    occ = {(r - r0, c - c0) for r, c in cells}
    hh, ww = r1 - r0 + 1, c1 - c0 + 1
    seen = set()
    enclosed = 0
    for r in range(hh):
        for c in range(ww):
            if (r, c) in occ or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            touches_edge = False
            while stack:
                cr, cc = stack.pop()
                if cr in (0, hh - 1) or cc in (0, ww - 1):
                    touches_edge = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < hh and 0 <= nc < ww and (nr, nc) not in occ and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches_edge:
                enclosed += 1
    return enclosed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify components are distinct and one has the strict max hole count."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                color = grid[r][c]
                stack = [(r, c)]
                seen.add((r, c))
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                comps.append((color, cells))
    if len(comps) < 2:
        errs.append(f"only {len(comps)} component(s); need >=2")
        return errs
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        errs.append("components do not all have distinct colors")
    hole_counts = [_enclosed_regions(cells) for _, cells in comps]
    max_holes = max(hole_counts)
    if max_holes <= 0:
        errs.append("no component has an enclosed hole")
    if hole_counts.count(max_holes) != 1:
        errs.append(f"hole-count winner is not unique: {hole_counts}")
    return errs


def _ladder(k, rw, vertical, ch=1):
    """Rect outline with k interior chambers each `ch` rows tall.
    Walls are 1-row bars; chamber rows are hollow (only side walls).
    Always exactly k enclosed 0-regions regardless of ch."""
    rh = (k + 1) + k * ch  # k+1 horizontal bars + k chambers of height ch
    cells = set()
    r = 0
    for chamber in range(k):
        # top wall bar (full width)
        for c in range(rw):
            cells.add((r, c))
        r += 1
        # chamber rows: only side walls
        for _ in range(ch):
            cells.add((r, 0)); cells.add((r, rw - 1))
            r += 1
    # final bottom bar
    for c in range(rw):
        cells.add((r, c))
    if vertical:
        cells = {(c, r) for r, c in cells}
    return sorted(cells)


def _ring(rh, rw):
    return [(r, c) for r in range(rh) for c in range(rw)
            if r in (0, rh - 1) or c in (0, rw - 1)]


_SOLIDS = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "big_ring_decoy"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
    k = int(overrides.get("n_chambers", ctx.draw_int("n_chambers", 2, 3)))
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        n_others = rng.randint(1, 2)
        palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + n_others)
        rw = rng.randint(3, 6)
        vertical = rng.random() < 0.5
        ch = rng.randint(1, 2)  # chamber height: multiplies distinct winner shapes
        winner = _ladder(k, rw, vertical, ch)
        if not _place(g, rng, winner, palette[0]):
            continue
        ok = True
        for i, color in enumerate(palette[1:]):
            if texture == "big_ring_decoy" and i == 0:
                # 1 region but MANY hole cells: only region counting
                # (not cell counting) keeps the ladder as the winner
                decoy = _ring(rng.randint(4, 5), rng.randint(5, 6))
            elif rng.random() < 0.5:
                decoy = _ring(3, rng.randint(3, 4))
            else:
                decoy = _SOLIDS[rng.randrange(len(_SOLIDS))]
            if not _place(g, rng, decoy, color):
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not realize hole-count board")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.
    (no_components was dropped: an empty grid leaves the rule's
    component selector with nothing — crash territory.)

    tied_holes — two components share the max region count: the
                 selector's tie-break silently decides.
    all_solid  — every component has 0 enclosed regions.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    if name == "tied_holes":
        ring = _ring(3, rng.randint(3, 4))
        _place(g, rng, ring, colors[0])
        _place(g, rng, _ring(3, rng.randint(3, 4)), colors[1])
        return g
    # all_solid
    for color in colors:
        _place(g, rng, _SOLIDS[rng.randrange(len(_SOLIDS))], color)
    return g
