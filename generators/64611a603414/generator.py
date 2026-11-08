"""Generator for arc_puzzle_bank_21_set8:hard_h19 — overlap two shapes (best D4 align).

REAL rule (verified from canonical Racket): take the FIRST TWO components (by
leftmost column). Try all 8 dihedral (rotate/flip) variants of the SECOND shape
and pick the one that, top-left aligned with the first, MAXIMISES cell overlap.
Output the INTERSECTION (cells non-zero in both) painted color 8, cropped.

The previous body drew 3-4 "gallery" motifs (a wrong-task docstring) — the rule
only consumes two components, so the extras were dead weight and the overlap of
random tiny motifs gave few distinct outputs. This rewrite places EXACTLY two
connected shapes whose best-aligned overlap is verified non-trivial (>=2 cells),
so the intersection output varies.

Degenerates: no_shapes, single_shape, no_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "64611a603414"
VERSION = "3.0.4"  # WRONG docstring ('gallery pack') + dup: rule overlaps the FIRST TWO components after best D4 alignment of the 2nd; output = intersection in color 8. Gen drew 3-5 motifs (rule uses 2). Now EXACTLY two shapes with verified best-aligned overlap >=2.
TASK_ID = "64611a603414"

SUMMARY = (
    "0-bg grid with EXACTLY TWO connected SHAPES in distinct colours, a left "
    "one (A) and a right one (B). Rule: rotate/flip B into the dihedral variant "
    "maximising top-left-aligned cell overlap with A, then output the "
    "INTERSECTION (cells non-zero in both) in colour 8, cropped. Shapes are "
    "generated so the best-aligned overlap is non-trivial (>=2 cells)."
)

INVARIANTS = [
    "background is 0",
    "exactly two connected shapes in distinct non-zero colours",
    "the second shape has a dihedral variant overlapping the first in >=2 cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..20"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    comps.sort(key=lambda comp: (min(c for _, c in comp), min(r for r, _ in comp)))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly two mono-color components whose best D4 overlap is non-trivial."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    comps = _nonzero_components(grid)
    if len(comps) != 2:
        errs.append(f"expected exactly two nonzero components; got {len(comps)}")
        return errs
    comp_colors = []
    norm_comps = []
    for comp in comps:
        colors = {grid[r][c] for r, c in comp}
        if len(colors) != 1:
            errs.append(f"component has multiple colors: {sorted(colors)}")
        comp_colors.append(next(iter(colors)))
        r0 = min(r for r, _ in comp)
        c0 = min(c for _, c in comp)
        norm_comps.append([(r - r0, c - c0) for r, c in comp])
    if len(set(comp_colors)) != 2:
        errs.append(f"the two components should use distinct colors, got {comp_colors}")
    if _max_overlap(norm_comps[0], norm_comps[1]) < 3:
        errs.append("best dihedral overlap of the two shapes is <3 cells")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    # Normalize before placement.  The grower may wander into negative
    # coordinates; using those directly caused Python negative-index wrapping
    # and could split/merge the intended two shapes.
    return sorted(_norm(cells))


def _norm(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _variants(cells):
    """All 8 normalized dihedral variants of a cell set."""
    def rot(cs):  # rotate 90
        return [(c, -r) for r, c in cs]
    def flip(cs):
        return [(r, -c) for r, c in cs]
    out = set(); cur = list(cells)
    for _ in range(4):
        out.add(_norm(cur)); out.add(_norm(flip(cur)))
        cur = rot(cur)
    return out


def _max_overlap(a, b):
    """Max top-left-aligned overlap of A with any dihedral variant of B."""
    sa = _norm(a)
    return max(len(sa & v) for v in _variants(b))


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _fits_two_half_layout(a, b, h, w):
    ah, aw = _dims(a)
    bh, bw = _dims(b)
    left_width = max(1, w // 2)
    right_width = w - (w // 2 + 1)
    return ah <= h and bh <= h and aw <= left_width and bw <= right_width


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13); klo, khi = 5, 7
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 20); klo, khi = 7, 11
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 16); klo, khi = 6, 9
    rng = ctx.draw_rng("layout")
    # two shapes with a verified SUBSTANTIAL best-aligned overlap (bigger
    # intersections -> more varied, less duplicated output)
    a = b = None
    for _ in range(400):
        ca = _build_motif(rng, rng.randint(klo, khi))
        cb = _build_motif(rng, rng.randint(klo, khi))
        if _fits_two_half_layout(ca, cb, h, w) and _max_overlap(ca, cb) >= 4:
            a, b = ca, cb
            break
    if a is None:
        for _ in range(200):
            ca = _build_motif(rng, rng.randint(klo, khi))
            cb = _build_motif(rng, rng.randint(klo, khi))
            if _fits_two_half_layout(ca, cb, h, w) and _max_overlap(ca, cb) >= 3:
                a, b = ca, cb
                break
    if a is None:
        a = [(0, 0), (0, 1), (1, 0), (1, 1)]
        b = [(0, 0), (0, 1), (1, 0), (1, 1)]
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
    g = full_grid(h, w, 0)
    # place A in the left half, B in the right half (A's leftmost col < B's)
    ah = max(r for r, _ in a) + 1; aw = max(c for _, c in a) + 1
    bh = max(r for r, _ in b) + 1; bw = max(c for _, c in b) + 1
    for _ in range(200):
        left_hi = w // 2 - aw
        right_lo = w // 2 + 1
        right_hi = w - bw
        if left_hi < 0 or right_hi < right_lo:
            continue
        ar = rng.randint(0, h - ah); ac = rng.randint(0, left_hi)
        br = rng.randint(0, h - bh); bc = rng.randint(right_lo, right_hi)
        acells = {(ar + dr, ac + dc) for dr, dc in a}
        bcells = {(br + dr, bc + dc) for dr, dc in b}
        # 8-separation so they stay distinct components
        halo = {(r + dr, c + dc) for (r, c) in acells for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if acells & bcells or halo & bcells:
            continue
        for r, c in acells:
            g[r][c] = colors[0]
        for r, c in bcells:
            g[r][c] = colors[1]
        return g
    # Fallback: simple guaranteed separated placement that still has a
    # non-trivial best-aligned overlap under the rule.
    g = full_grid(h, w, 0)
    a = [(0, 0), (0, 1), (1, 0), (1, 1)]
    b = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for dr, dc in a:
        g[1 + dr][1 + dc] = colors[0]
    for dr, dc in b:
        g[1 + dr][w - 3 + dc] = colors[1]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
