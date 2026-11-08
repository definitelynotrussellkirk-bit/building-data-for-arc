"""Generator for arc_puzzle_bank_twentieth21:H138 — four-panel transform chain.

Rule: split the input into four equal square panels separated by one blank
column. Infer the transform that maps panel A to panel B, infer the transform
that maps B to C, then apply that two-step transform chain to the query panel D.

Combinatorial axes: panel_size, palette, transform_1, transform_2, query_shape,
fill_density, texture.
Degenerates: no_panels, ambiguous_transform, identity_chain.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67518e88ad2a"
VERSION = "3.3.0"  # panel_size capped at 6: w=4n+3 must fit the 30-col ARC box (hard's 7-8 overflowed on EVERY draw)
RULE_HASH = "3bc59d5b684a"  # canonical rule this generator was written against
TASK_ID = "67518e88ad2a"

SUMMARY = (
    "Four square panels in one row: B is a visible transform of A, C is a "
    "visible transform of B, and D is a query panel. Canonical rule composes "
    "the inferred A->B and B->C transforms and applies the chain to D."
)

INVARIANTS = [
    "input width is 4*panel_size+3; panels are separated by one UNIFORM column "
    "(colored like the canonical demos ~75% of the time, else 0)",
    "A->B and B->C each have exactly one non-identity transform explanation",
    "query panel D is asymmetric and the composed transform is non-identity",
]

TRANSFORMS = ("rot90", "rot180", "rot270", "flip-h", "flip-v", "transpose", "anti-transpose")
ALL_TRANSFORMS = ("id",) + TRANSFORMS
DEGENERATE_TEXTURES = ("no_panels", "ambiguous_transform", "identity_chain")
# "default" is definitionally identical to the un-textured draw — declaring it
# as a helpful texture is a no-op (defect-lint texture-dead).
HELPFUL_TEXTURES = ("warm", "cool", "varied")

AXES = {
    "panel_size": {"type": "int", "default": "3-5 easy / 3-6 med / 6 hard",
                   "valid": "3..6"},
    "transform_1": {"type": "str", "default": "rng non-identity", "valid": "|".join(TRANSFORMS)},
    "transform_2": {"type": "str", "default": "rng non-identity", "valid": "|".join(TRANSFORMS)},
    "density": {"type": "str", "default": "sparse_asymmetric", "valid": "sparse_asymmetric"},
    "texture": {"type": "str", "default": "default", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rotate_cw(g):
    return [list(row) for row in zip(*g[::-1])]


def _rotate_180(g):
    return [row[::-1] for row in g[::-1]]


def _rotate_ccw(g):
    return [list(row) for row in zip(*g)][::-1]


def _flip_lr(g):
    return [row[::-1] for row in g]


def _flip_ud(g):
    return g[::-1]


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _anti_transpose(g):
    return _rotate_180(_transpose(g))


def _apply(name, g):
    if name == "id": return [row[:] for row in g]
    if name == "rot90": return _rotate_cw(g)
    if name == "rot180": return _rotate_180(g)
    if name == "rot270": return _rotate_ccw(g)
    if name == "flip-h": return _flip_lr(g)
    if name == "flip-v": return _flip_ud(g)
    if name == "transpose": return _transpose(g)
    if name == "anti-transpose": return _anti_transpose(g)
    raise ValueError(name)


def _infer_unique(a, b):
    hits = [name for name in ALL_TRANSFORMS if _apply(name, a) == b]
    return hits


def _palette(texture):
    if texture == "warm":
        return [2, 3, 4, 6]
    if texture == "cool":
        return [1, 5, 7, 8]
    if texture == "varied":
        return [1, 2, 3, 4, 5, 6, 7, 8, 9]
    return [2, 3, 4, 5, 6, 7, 8, 9]


def _asymmetric_panel(rng, n, palette):
    """Compact 1-2-color square whose dihedral transforms are all distinct.

    Canonical panels are single-color contiguous shapes (~1-2 components each),
    not multi-color pixel noise — grow from an anchor with adjacency bias and
    color from a tiny per-panel palette (defect-lint obj_count coverage)."""
    for _ in range(200):
        g = full_grid(n, n, 0)
        k = rng.randint(max(4, n - 1), min(n * n - 1, n + 4))
        cells = set()
        # Seed an off-center L-like anchor so symmetry is unlikely, then grow.
        anchor = [(0, 1), (1, 1), (1, 2), (2, 1)]
        r0 = rng.randint(0, n - 3)
        c0 = rng.randint(0, n - 3)
        for dr, dc in anchor:
            cells.add((r0 + dr, c0 + dc))
        while len(cells) < k:
            if rng.random() < 0.75:
                r, c = rng.choice(sorted(cells))
                dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                if 0 <= r + dr < n and 0 <= c + dc < n:
                    cells.add((r + dr, c + dc))
            else:
                cells.add((rng.randrange(n), rng.randrange(n)))
        panel_colors = rng.sample(palette, 1 if rng.random() < 0.7 else 2)
        for r, c in cells:
            g[r][c] = rng.choice(panel_colors)
        if all(len(_infer_unique(g, _apply(t, g))) == 1 for t in TRANSFORMS):
            return g
    raise ValueError("could not build asymmetric panel")


def _compose_panels(panels, sep_color=0):
    n = len(panels[0])
    g = full_grid(n, 4 * n + 3, sep_color)
    for i, panel in enumerate(panels):
        left = i * (n + 1)
        for r in range(n):
            for c in range(n):
                g[r][left + c] = panel[r][c]
    return g


def _split_panels(g):
    h, w = len(g), len(g[0])
    if (w - 3) % 4 != 0:
        return []
    n = (w - 3) // 4
    if h != n:
        return []
    return [[row[i * (n + 1): i * (n + 1) + n] for row in g] for i in range(4)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    rng = ctx.draw_rng("layout")
    # ARC cap: the rule splits ONE row of 4 panels + 3 gap cols -> w = 4n+3,
    # so n <= 6. The old hard band (7-8) emitted 31/35-wide grids on EVERY
    # draw (validity sweep).
    if difficulty == "easy":
        n = ctx.draw_int("panel_size", 3, 5)
    elif difficulty == "hard":
        n = ctx.draw_int("panel_size", 6, 6)
    else:
        n = ctx.draw_int("panel_size", 3, 6)
    pal = _palette(texture or "default")
    a = _asymmetric_panel(rng, n, pal)
    d = _asymmetric_panel(rng, n, pal)
    t1 = rng.choice(TRANSFORMS)
    # A and B/C transitions are individually visible, but rot90 followed by
    # rot270 (or vice versa) makes the *composed* query transform identity.
    # That leaks the explicit identity_chain degenerate into normal rows: the
    # learner can output D unchanged even though both demonstrations move.  Pick
    # t2 only from pairs whose composition visibly changes the asymmetric query.
    t2_choices = [t for t in TRANSFORMS
                  if t != t1 and _apply(t, _apply(t1, d)) != d]
    t2 = rng.choice(t2_choices)
    b = _apply(t1, a)
    c = _apply(t2, b)
    # canonical demos use a COLORED separator column (e.g. 8), not blank —
    # draw one most of the time, from outside the panels' palette
    used = {v for p in (a, b, c, d) for row in p for v in row if v}
    sep_pool = [v for v in pal if v not in used]
    sep_color = rng.choice(sep_pool) if sep_pool and rng.random() < 0.75 else 0
    return _compose_panels([a, b, c, d], sep_color)


def _draw_from_degenerate(name):
    if name == "no_panels":
        return full_grid(6, 10, 0)
    n = 5
    if name == "ambiguous_transform":
        p = full_grid(n, n, 0)
        p[1][1] = p[1][3] = p[3][1] = p[3][3] = 4  # symmetric under several transforms
        return _compose_panels([p, p, p, p])
    if name == "identity_chain":
        p = full_grid(n, n, 0)
        p[0][1] = 2; p[2][3] = 5; p[4][0] = 7
        return _compose_panels([p, p, p, p])
    return full_grid(6, 10, 0)


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    panels = _split_panels(grid)
    if len(panels) != 4:
        return ["does not split into four equal square panels with 1-col gaps"]
    n = len(panels[0])
    for sep in (n, 2 * n + 1, 3 * n + 2):
        if len({row[sep] for row in grid}) != 1:
            msgs.append("panel separator column is not uniform")
            break
    ab = _infer_unique(panels[0], panels[1])
    bc = _infer_unique(panels[1], panels[2])
    if len(ab) != 1 or ab[0] == "id":
        msgs.append(f"A->B transform is not uniquely non-identity: {ab}")
    if len(bc) != 1 or bc[0] == "id":
        msgs.append(f"B->C transform is not uniquely non-identity: {bc}")
    if any(not any(v != 0 for row in panel for v in row) for panel in panels):
        msgs.append("one of the four panels is empty")
    if len(ab) == 1 and len(bc) == 1:
        moved_d = _apply(bc[0], _apply(ab[0], panels[3]))
        if moved_d == panels[3]:
            msgs.append(f"composed A->B->C transform is identity on D: {ab[0]} then {bc[0]}")
        elif not any(moved_d[r][c] != panels[3][r][c] for r in range(n) for c in range(n)):
            msgs.append("composed transform does not visibly change D")
    if any(len(_infer_unique(panels[3], _apply(t, panels[3]))) != 1 for t in TRANSFORMS):
        msgs.append("query panel D has a symmetry that can hide at least one transform")
    return msgs
