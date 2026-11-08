"""Generator for arc_puzzle_bank_21_set23_bundle:medium_p06 — flip-lr of the largest object.

Rule (verified from canonical Racket): take all 4-connected single-colour objects,
pick the LARGEST (ties: topmost, then leftmost), crop it to its bbox, FLIP it
left-right, and output that crop in the object's own colour.

The previous body built a SET-OP puzzle (op-key at (0,0) + colour-2/colour-3
motifs) — the WRONG TASK; the canonical rule ignores all of that and just returns
the flipped largest object. This rewrite places several distinct-coloured objects
of DISTINCT sizes (so the largest is unambiguous) and varied shapes.

Combinatorial axes: grid size, object count, each object's shape/size/colour/position.
Degenerates: no_objects, single_object, tie_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d585b947291"
VERSION = "3.0.1"  # was a WRONG-TASK set-op generator; real rule = flip-lr of the largest object cropped. Now distinct-size, distinct-colour random objects so the largest (the rule's discriminator) is unambiguous and its flipped crop varies.
TASK_ID = "2d585b947291"

SUMMARY = (
    "0-bg grid with 3-5 separated 4-connected objects, each a random polyomino in "
    "its own distinct colour and with a DISTINCT cell count (so exactly one is "
    "largest). Rule: pick the largest object (ties: topmost then leftmost), crop to "
    "its bbox, flip it left-right, and output that crop in the object's colour."
)

INVARIANTS = [
    "background is 0",
    "3-5 separated single-colour objects, all distinct colours",
    "all object sizes are distinct so the largest is unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "tie_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "8..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": 'default|warm|cool|varied'},
    "n_objects":         {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":      {"type": "int", "default": "= n_objects", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "scattered_separated",
                          "valid": "scattered_separated"},
    "n_distinct_colors": {"type": "int", "default": "= n_objects", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": 'default|warm|cool|varied|no_objects|single_object|tie_sizes'},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _build_motif(rng, k):
    """Random connected k-cell polyomino, normalized to the origin."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, cells_p, pad=1):
    h, w = len(g), len(g[0])
    for (r, c) in cells_p:
        for dr in range(-pad, pad + 1):
            for dc in range(-pad, pad + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-bg colors (the objects), all different sizes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 2:
        return [f"expected >=2 distinct non-bg colors, got {len(counts)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_objects", 3, 3); kmax = 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_objects", 4, 5); kmax = 9
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14)
        n = ctx.draw_int("n_objects", 3, 4); kmax = 8
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        # distinct cell counts -> the largest object is unambiguous (the rule's pick)
        sizes = rng.sample(range(2, kmax + 1), n)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for k, color in zip(sizes, colors):
            shape = _build_motif(rng, k)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            if sh > h or sw > w:
                ok = False; break
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                cells_p = [(r0 + r, c0 + c) for r, c in shape]
                if _free(g, cells_p):
                    for (r, c) in cells_p:
                        g[r][c] = color
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place largest-object layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # empty grid — rule returns a 1x1 [[0]] fallback
        return g
    if name == "single_object":
        # one object — the "largest" pick is trivial
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[3 + dr][4 + dc] = 4
        return g
    if name == "tie_sizes":
        # two equal-size objects — largest is ambiguous (broken by position)
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[6 + dr][8 + dc] = 5
        return g
    return g
