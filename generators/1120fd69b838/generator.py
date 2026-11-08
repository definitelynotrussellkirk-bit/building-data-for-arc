"""Generator for arc_additional_puzzles_21_set16_bundle:M111 — N×N dihedral-equivalence matrix.

Rule: each object (sorted top-left) becomes a binary mask. Output is
N×N matrix where cell (r, c) = 8 if mask r is some dihedral transform
of mask c, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects (grid is all bg → rule's matrix has size 0),
single_object (only one object → 1x1 trivial matrix, no contrast),
all_dihedral_equivalent (every object is dihedrally equivalent → output
matrix is all 8s, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "1120fd69b838"
# 3.1.0: defect-lint all_background_output — n_distinct could be 1 (all objects one
# family -> the matrix is SOLID 8s, a contrast-free demo) and n_obj=2 could not
# satisfy both invariants. Now n_obj >= 3 with 2..n-1 distinct families, every
# family guaranteed placed at least once; adds an executable self_check.
VERSION = "3.1.0"
TASK_ID = "1120fd69b838"
SUMMARY = (
    "0-bg grid with N (2..6) 4-connected OBJECTS, each in a "
    "distinct color, placed apart by >=1 bg cell. Shapes are drawn "
    "from a pool of PAIRWISE-DIHEDRALLY-DISTINCT families; some "
    "families repeat (each instance independently rotated/flipped) "
    "to create dihedral-equivalent pairs. Rule: extract objects, "
    "sort by top-left (row, col), binary-crop each (drop color). "
    "Output: an N x N MATRIX where cell (r, c) = 8 (cyan) if "
    "mask[r] is DIHEDRAL EQUIVALENT to mask[c] (some transform "
    "code 1..8 maps one to the other), else 0. Diagonal always 8. "
    "Both N and the equivalence block-structure vary (was fixed 3x3)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "2..6 4-connected non-bg objects, each a distinct color",
    "shapes come from pairwise-dihedrally-distinct families; repeats are dihedral-equivalent",
    "at least one repeated family so some off-diagonal cell is 8",
    "objects don't touch each other (>=1 bg-cell gap)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "all_dihedral_equivalent")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 10..14", "valid": "7..18"},
    "grid_w":            {"type": "int", "default": "rng 13..18", "valid": "10..22"},
    "n_objects":         {"type": "int", "default": "3 easy / 3-5 med / 4-6 hard", "valid": "3..6"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "= n_objects", "valid": "2..6"},
    "position_bias":     {"type": "str", "default": "scattered_with_gaps",
                          "valid": "scattered_with_gaps"},
    "n_distinct_colors": {"type": "int", "default": "= n_objects", "valid": "2..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Base shape families that are PAIRWISE DIHEDRALLY DISTINCT (verified): no
# transform of one equals any transform of another. Repeating a family (with a
# random dihedral transform applied) creates a dihedral-equivalent pair in the
# N×N matrix; using different families creates 0-cells. This lets the matrix's
# block structure — and N itself — vary, instead of the old fixed 3×3.
_SHAPE_FAMILIES = [
    [(0, 0), (0, 1), (1, 0)],                       # L tromino
    [(0, 0), (0, 1), (0, 2)],                       # I tromino
    [(0, 0), (0, 1), (1, 0), (1, 1)],               # square tetromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],               # T tetromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],               # S tetromino
    [(0, 0), (0, 1), (0, 2), (0, 3)],               # I tetromino
    [(0, 0), (1, 0), (2, 0), (2, 1)],               # L tetromino
    [(0, 0), (0, 1)],                               # domino
    [(0, 0)],                                        # single cell
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],        # P pentomino
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],        # plus pentomino
]


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _normalize(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    mr = min(rs); mc = min(cs)
    return [(r - mr, c - mc) for r, c in cells]


def _rot_cw(cells):
    rs = [r for r, _ in cells]; mx = max(rs)
    return _normalize([(c, mx - r) for r, c in cells])


def _flip_lr(cells):
    cs = [c for _, c in cells]; mx = max(cs)
    return _normalize([(r, mx - c) for r, c in cells])


def _random_dihedral(cells, rng):
    out = _normalize(cells)
    for _ in range(rng.randint(0, 3)):
        out = _rot_cw(out)
    if rng.random() < 0.5:
        out = _flip_lr(out)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
        n_obj = ctx.draw_int("n_objects", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 16, 20)
        n_obj = ctx.draw_int("n_objects", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 13, 18)
        n_obj = ctx.draw_int("n_objects", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Choose a multiset of shape FAMILIES of size n_obj. Repeats create
    # dihedral-equivalent pairs (8-blocks in the matrix); distinct families
    # create 0s. Bias toward at least one repeat so the matrix isn't all-identity.
    families = list(_SHAPE_FAMILIES)
    rng.shuffle(families)
    # 2 <= classes <= n-1: guarantees BOTH a repeated family (an off-diagonal 8)
    # AND a non-equivalent pair (a 0) — never a solid or pure-identity matrix.
    n_distinct = rng.randint(2, max(2, n_obj - 1))
    base = families[:n_distinct]
    chosen = list(base)                     # every family placed at least once
    while len(chosen) < n_obj:
        chosen.append(rng.choice(base))
    rng.shuffle(chosen)
    # Apply an independent random dihedral transform per object: equivalent
    # families stay equivalent (rule is dihedral-invariant) but pixels differ.
    shapes = [_random_dihedral(s, rng) for s in chosen]
    # distinct colors per object (rule sorts by position; colors only need to
    # keep objects as separate components, which separation already guarantees).
    palette = list(random_palette(rng, min(9, n_obj))) if n_obj <= 9 else \
        [(i % 9) + 1 for i in range(n_obj)]
    while len(palette) < n_obj:
        palette.append(rng.randint(1, 9))
    placed: list[tuple[int, int, int, int]] = []
    for shape, color in zip(shapes, palette):
        sh, sw = _bbox(shape)
        ok = False
        for _ in range(120):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            bb_pad = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb_pad, p) for p in placed):
                continue
            paint_at(g, r0, c0, shape, color)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            ok = True
            break
        if not ok:
            raise ValueError("could not place all objects without overlap")
    return g


def _all_transforms(cells):
    out = []
    cur = _normalize(cells)
    for _ in range(4):
        out.append(tuple(sorted(cur)))
        out.append(tuple(sorted(_flip_lr(cur))))
        cur = _rot_cw(cur)
    return set(out)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=3 isolated objects whose dihedral classes include BOTH a repeat (an
    off-diagonal 8) and two distinct classes (a 0) — else the matrix demo is
    solid or pure-identity and teaches nothing."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    seen: set[tuple[int, int]] = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    if len(comps) < 3:
        return [f"expected >=3 objects, found {len(comps)}"]
    canon = [min(_all_transforms(comp)) for comp in comps]
    if len(set(canon)) < 2:
        return ["all objects are dihedral-equivalent — the matrix would be solid 8s"]
    if len(set(canon)) == len(canon):
        return ["no two objects are dihedral-equivalent — the matrix is a pure identity"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # No objects — rule's matrix has size 0.
        return g
    if name == "single_object":
        # Only one object — trivial 1x1 matrix.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][5 + dc] = 4
        return g
    if name == "all_dihedral_equivalent":
        # Three L-trominoes — all dihedral equivalents; output matrix
        # is all 8s.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][6 + dc] = 6
        for dr, dc in [(0, 1), (1, 0), (1, 1)]:
            g[1 + dr][11 + dc] = 8   # all are L variants
        return g
    return g
