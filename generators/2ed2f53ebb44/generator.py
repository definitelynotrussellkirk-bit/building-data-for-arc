"""Generator for arc_additional_puzzles_21_set15_bundle:H103 — Rotation-equivalent shape relation matrix.

Rule: take the non-zero 4-connected components, sort them by left edge,
and output an NxN matrix where (i,j) = 7 if components i and j have the
same shape under rotation (0/90/180/270 — no reflections), else 0.

Combinatorial axes: number of components (3-7), each component's shape
(rotation class), orientation, and position; plus the color.
Degenerates: all_same_shape, all_distinct_shapes, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2ed2f53ebb44"
# 4.1.0: defect-lint all_background_output + canonical-coverage — all components
# could share one rotation class (solid-7 matrix); failed placements were silently
# DROPPED (partial demos); all objects shared one color while canonical demos use
# per-object colors. Now >=2 classes forced, full placement required (loud raise),
# distinct per-object colors.
VERSION = "4.1.0"
TASK_ID = "2ed2f53ebb44"
SUMMARY = (
    "0-bg grid (size varies) with 3-7 non-touching CONNECTED COMPONENTS "
    "in one color (each a polyomino of some rotation class + orientation), "
    "placed apart. Rule: sort components by left edge and output an NxN "
    "matrix where (i,j) = COLOR 7 if components i,j match under rotation "
    "(0/90/180/270, no reflections), else 0. The number of components, "
    "their shapes/orientations/positions and the color all vary freely "
    "(was 3 fixed components on a fixed 8x14, ~9 distinct)."
)

INVARIANTS = [
    "3-7 non-touching 4-connected components in a single color",
    ">=2 components share a rotation class (an off-diagonal 7) and >=2 differ",
    "the output is the NxN rotation-relation matrix (diagonal always 7)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_shape", "all_distinct_shapes", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

# rotation-distinct base motifs (each fits <=3x3)
_MOTIFS = [
    [(0, 0), (1, 0), (1, 1)],                    # L-tromino
    [(0, 0), (0, 1), (0, 2)],                    # I-tromino
    [(0, 0), (0, 1), (1, 1), (1, 2)],            # S tetromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],            # T tetromino
    [(0, 0), (1, 0), (2, 0), (2, 1)],            # L tetromino
    [(0, 0), (0, 1), (1, 0), (1, 1)],            # square
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],    # plus
]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "third_shape":    {"type": "choice", "default": "varies", "valid": "line|corner"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|"
                                "all_same_shape|all_distinct_shapes|single_component"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rot_cw(cells):
    return [(c, -r) for r, c in cells]


def _rotations(cells):
    out = []
    cur = list(cells)
    for _ in range(4):
        out.append(_norm(cur))
        cur = _rot_cw(cur)
    return out


def _realize(rng, motif):
    cells = list(motif)
    for _ in range(rng.randint(0, 3)):
        cells = _rot_cw(cells)
    return sorted(_norm(cells))


def _reserve_bbox(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=3 4-connected non-bg components (all same color; BFS count)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    nonzero = set((r, c) for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not nonzero:
        return ["no non-bg cells found"]
    visited = set(); n_comp = 0
    for start in nonzero:
        if start in visited:
            continue
        n_comp += 1
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in nonzero and nb not in visited:
                    queue.append(nb)
    if n_comp < 3:
        return [f"expected >=3 4-connected non-bg components for n×n matrix, got {n_comp}"]
    # rotation-class structure: >=2 classes (else solid matrix) and >=1 repeat
    # (else pure identity) — both are contrast-free demos.
    visited2: set[tuple[int, int]] = set()
    canons = []
    for start in nonzero:
        if start in visited2:
            continue
        comp = []
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited2:
                continue
            visited2.add(cell)
            comp.append(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in nonzero and nb not in visited2:
                    queue.append(nb)
        canons.append(min(_rotations(comp)))
    if len(set(canons)) < 2:
        return ["all components share one rotation class — the matrix would be solid"]
    if len(set(canons)) == len(canons):
        return ["no two components share a rotation class — the matrix is a pure identity"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # output = n x n rotation-equivalence matrix (n = component count); widen n so
    # the matrix size + partition pattern vary far more (was n in {3,4} -> distinct=17).
    if difficulty == "easy":
        hr, wr, nr = (11, 14), (11, 14), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr = (16, 22), (16, 22), (5, 7)
    else:
        hr, wr, nr = (13, 18), (13, 18), (3, 6)

    for _attempt in range(60):
        n = rng.randint(*nr)
        # >=2 sharing a class AND >=2 differing: never a solid or pure-identity matrix
        shared = rng.choice(_MOTIFS)
        other = rng.choice([m for m in _MOTIFS if _norm(m) not in _rotations(shared)])
        bases = [shared, shared, other]
        while len(bases) < n:
            bases.append(rng.choice(_MOTIFS))
        bases = bases[:n]
        rng.shuffle(bases)

        h = rng.randint(*hr); w = rng.randint(*wr)
        # canonical demos color each object separately
        colors = rng.sample(range(1, 10), min(n, 9))
        while len(colors) < n:
            colors.append(rng.randint(1, 9))
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        placed = 0
        for base, obj_color in zip(bases, colors):
            shape = _realize(rng, base)
            bh = max(r for r, c in shape) + 1; bw = max(c for r, c in shape) + 1
            for _t in range(60):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _reserve_bbox(occ, top, left, bh, bw, h, w):
                    for r, c in shape:
                        g[top + r][left + c] = obj_color
                    placed += 1
                    break
        # A dropped component silently changes the matrix size AND can collapse
        # the class structure — require the full layout, else retry loudly.
        if placed == len(bases):
            return g

    raise ValueError("could not place all rotation-class components")


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 14, 0)
    color = 4
    if name == "all_same_shape":
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[1 + dr][1 + dc] = color
        for dr, dc in [(0, 0), (0, 1), (1, 0)]: g[2 + dr][6 + dc] = color
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[5 + dr][10 + dc] = color
        return g
    if name == "all_distinct_shapes":
        for dr, dc in [(0, 0), (0, 1), (0, 2)]: g[1 + dr][1 + dc] = color
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]: g[1 + dr][5 + dc] = color
        for dr, dc in [(0, 0), (0, 1), (1, 1), (2, 0)]: g[3 + dr][10 + dc] = color
        return g
    if name == "single_component":
        for dr, dc in [(0, 0), (1, 0), (1, 1)]: g[3 + dr][6 + dc] = color
        return g
    return g
