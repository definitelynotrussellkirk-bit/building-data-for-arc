"""Generator for 4b:hard_26 — stamp unique bi-symmetric component at markers.

Rule: among color-1 components, the FIRST one that has both H and V
mirror symmetry is the template. Output is rebuilt from an EMPTY grid:
for each marker cell (value in {2,3,4,5}, scan order), the cropped
template is recolored to the marker color and pasted with its center
(bh//2, bw//2) on the marker; out-of-bounds stamp cells clip; later
stamps overwrite earlier ones. Template and marker cells themselves
do NOT survive unless covered by a stamp.

Combinatorial axes: grid_h, grid_w, n_markers, texture
(plain|asym_decoy|clip).
Degenerates: no_markers (output is a BLANK grid — the rebuild has
nothing to stamp), single_cell_template (1x1 template: stamps are
single recolored dots). no_template was DROPPED: with no bi-symmetric
color-1 component the rule does (obj-cells #f) and CRASHES.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "060d20779ba7"
VERSION = "2.0.1"
TASK_ID = "060d20779ba7"
SUMMARY = (
    "One bi-symmetric (H+V mirror) color-1 component is the template; "
    "markers in {2,3,4,5} each get a center-aligned stamp of the "
    "template recolored to the marker color, on a blank canvas. "
    "asym_decoy boards add color-1 components that are NOT bi-"
    "symmetric (selection must check BOTH symmetries); clip boards "
    "put a marker near the border. (Was: 2 hardcoded templates, no "
    "decoys, and a degenerate that crashed the rule.)"
)

# Rivals: 'use any color-1 component' refuted by asym decoys (h-only /
# v-only / no symmetry) the rule skips. 'template survives' refuted by
# every demo (blank rebuild). 'stamps keep color 1' refuted by marker-
# colored stamps. 'stamps always fit' refuted by clip boards.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly ONE bi-symmetric color-1 component (asym decoys verified not H+V symmetric)",
    ">=1 marker in {2,3,4,5} on main path",
    "markers keep clearance so stamps don't collide (except clip's OOB)",
    "no bi-symmetric-free boards (the rule crashes without a template)",
]

DEGENERATE_TEXTURES = ("no_markers", "single_cell_template")
HELPFUL_TEXTURES = ("plain", "asym_decoy", "clip")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "grid_w":    {"type": "int", "default": "rng 12..16", "valid": "11..18"},
    "n_markers": {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|asym_decoy|clip|no_markers|single_cell_template",
                  "doc": "asym_decoy: extra color-1 blobs lacking full "
                         "H+V symmetry; clip: one stamp partially OOB."},
}


def _bisym_shape(rng):
    """Random connected shape symmetric across BOTH axes (odd dims)."""
    th = rng.choice((3, 3, 5))
    tw = rng.choice((3, 5, 5))
    cr, cc = th // 2, tw // 2
    cells = {(cr, cc)}
    cand = [(r, c) for r in range(th) for c in range(tw)]
    rng.shuffle(cand)
    target = rng.randint(5, min(13, th * tw - 1))
    for r, c in cand:
        if len(cells) >= target:
            break
        orbit = {(r, c), (r, tw - 1 - c), (th - 1 - r, c), (th - 1 - r, tw - 1 - c)}
        if orbit & cells:
            continue
        # connectivity: at least one orbit cell touches the set
        if any((rr + dr, cc2 + dc) in cells
               for rr, cc2 in orbit for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            cells |= orbit
    norm = sorted(cells)
    mr = min(r for r, _ in norm)
    mc = min(c for _, c in norm)
    return [(r - mr, c - mc) for r, c in norm]


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _bisym(cells):
    th = max(r for r, _ in cells) + 1
    tw = max(c for _, c in cells) + 1
    s = set(cells)
    return (all((th - 1 - r, c) in s for r, c in s) and
            all((r, tw - 1 - c) in s for r, c in s))


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-1 component with H+V symmetry; >=1 marker in {2,3,4,5}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    # check for bi-symmetric color-1 component
    seen: set = set()
    found_bisym = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 1 and (r, c) not in seen:
                stack = [(r, c)]
                comp: list = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                if len(comp) > 1:
                    norm = frozenset((rr - min(rr for rr, _ in comp),
                                      cc - min(cc for _, cc in comp))
                                     for rr, cc in comp)
                    mh = max(rr for rr, _ in norm) + 1
                    mw = max(cc for _, cc in norm) + 1
                    lr = frozenset((rr, mw - 1 - cc) for rr, cc in norm)
                    ud = frozenset((mh - 1 - rr, cc) for rr, cc in norm)
                    if norm == lr and norm == ud:
                        found_bisym = True
    if not found_bisym:
        errs.append("no bi-symmetric (H+V) color-1 component: rule would crash")
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (2, 3, 4, 5)]
    if not markers:
        errs.append("no marker in {2,3,4,5}: output would be blank")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "asym_decoy", "clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        n_markers = ctx.draw_int("n_markers", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 15, 16)
        n_markers = ctx.draw_int("n_markers", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 12, 16)
        n_markers = ctx.draw_int("n_markers", 1, 3)
    rng = ctx.draw_rng("layout")

    for _rebuild in range(30):
        g = full_grid(h, w, 0)
        template = _bisym_shape(rng)
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        for _ in range(60):
            r0 = rng.randint(0, h - th)
            c0 = rng.randint(0, w - tw)
            if _free(g, r0, c0, r0 + th - 1, c0 + tw - 1):
                for dr, dc in template:
                    g[r0 + dr][c0 + dc] = 1
                break

        if texture == "asym_decoy":
            for _ in range(rng.randint(1, 2)):
                for _try in range(60):
                    blob = _grow(rng, rng.randint(3, 6))
                    if _bisym(blob):
                        continue  # must NOT be a rival template
                    bh = max(r for r, _ in blob) + 1
                    bw = max(c for _, c in blob) + 1
                    if bh > h or bw > w:
                        continue
                    br = rng.randint(0, h - bh)
                    bc = rng.randint(0, w - bw)
                    if _free(g, br, bc, br + bh - 1, bc + bw - 1):
                        for dr, dc in blob:
                            g[br + dr][bc + dc] = 1
                        break

        placed = 0
        attempts = 0
        while placed < n_markers and attempts < 400:
            attempts += 1
            # clip placement can starve — fall back to interior markers
            want_clip = texture == "clip" and placed == 0 and attempts <= 150
            if want_clip:
                # marker close to a border: stamp partially clips
                edge = rng.randrange(4)
                if edge == 0:
                    r, c = 0, rng.randint(2, w - 3)
                elif edge == 1:
                    r, c = h - 1, rng.randint(2, w - 3)
                elif edge == 2:
                    r, c = rng.randint(2, h - 3), 0
                else:
                    r, c = rng.randint(2, h - 3), w - 1
                sr, sc = r - th // 2, c - tw // 2
                ok = g[r][c] == 0 and all(
                    g[rr][cc] == 0
                    for rr in range(max(0, sr), min(h, sr + th))
                    for cc in range(max(0, sc), min(w, sc + tw)))
                if not ok:
                    continue
            else:
                r = rng.randint(2, h - 3)
                c = rng.randint(2, w - 3)
                sr, sc = r - th // 2, c - tw // 2
                if not _free(g, sr, sc, sr + th - 1, sc + tw - 1):
                    continue
            g[r][c] = rng.choice([2, 3, 4, 5])
            placed += 1
        if placed >= 1:
            return g
        # a big centered template can leave no stamp room on a small
        # grid — rebuild the whole board with a fresh template
    raise ValueError("could not place any marker after 30 rebuilds")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_markers           — template only: output is a BLANK grid (the
                           rule rebuilds from empty; nothing to stamp).
    single_cell_template — a lone 1-cell IS trivially bi-symmetric;
                           stamps collapse to single recolored dots.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 11, 14)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    if name == "no_markers":
        shape = _bisym_shape(rng)
        th = max(r for r, _ in shape) + 1
        tw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - th)
        c0 = rng.randint(0, w - tw)
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 1
        return g
    # single_cell_template
    g[rng.randint(1, h - 2)][rng.randint(1, w - 2)] = 1
    for _ in range(rng.randint(1, 3)):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = rng.choice([2, 3, 4, 5])
    return g
