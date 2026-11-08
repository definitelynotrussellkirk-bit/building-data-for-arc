"""Generator for arc_puzzle_bank_twelfth21:H81 -- repeat object along marker vector by counter.

Rule: the vector is (first color-2 cell) - (first color-1 cell); k = the
number of color-3 cells. The PAYLOAD (cells whose color is not 0/1/2/3) is
stamped k+1 times (multiplier 0..k) along the vector onto a grid that
preserves the 1/2/3 markers.

This generator draws a payload, two markers (the vector), and k color-3
counter cells, sized so the k+1 copies stay in bounds.

Combinatorial axes: grid size, the payload, the vector, and the counter k.
Degenerates: no_markers, no_payload, zero_counter.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c41c09ae1d5"
VERSION = "2.0.1"  # diversity: random payload + vector + counter k (was fixed ~25)
TASK_ID = "2c41c09ae1d5"
SUMMARY = (
    "0-bg grid (size varies). A multi-color PAYLOAD (colors 4-9), a color-1 "
    "and color-2 marker (their difference is the step vector), and k color-3 "
    "counter cells. Rule: stamp the payload k+1 times along the vector "
    "(keeping the 1/2/3 markers). The grid size, payload, vector and counter "
    "k vary freely (was a fixed setup, ~25 distinct)."
)

INVARIANTS = [
    "one color-1 and one color-2 marker define the step vector",
    "k = the number of color-3 cells; the payload is stamped k+1 times",
    "the k+1 payload copies stay in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_payload", "zero_counter")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_PCOLORS = [4, 5, 6, 7, 8, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "payload_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "counter_k":      {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "payload_vector_counter",
                       "valid": "payload_vector_counter"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_payload|zero_counter"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1, one color-2 (vector markers), and >=1 color-3 (counter)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    for color, label in ((1, "marker-1"), (2, "marker-2")):
        count = sum(grid[r][c] == color for r in range(h) for c in range(w))
        if count != 1:
            errs.append(f"expected exactly 1 {label} cell, got {count}")
    count3 = sum(grid[r][c] == 3 for r in range(h) for c in range(w))
    if count3 == 0:
        errs.append("no color-3 counter cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, sr, kr = (12, 14), (12, 15), (2, 3), (1, 2)
    elif difficulty == "hard":
        hr, wr, sr, kr = (16, 22), (18, 24), (4, 5), (3, 4)
    else:
        hr, wr, sr, kr = (13, 17), (14, 19), (2, 4), (1, 3)

    for _attempt in range(50):
        h = rng.randint(*hr); w = rng.randint(*wr)
        shape = _poly(rng, rng.randint(*sr))
        ph = max(r for r, c in shape) + 1; pw = max(c for r, c in shape) + 1
        k = rng.randint(*kr)
        ncol = rng.randint(1, 3)
        pal = [rng.choice(_PCOLORS) for _ in range(ncol)]

        # step vector with magnitude >= payload extent so copies are separate
        axis = rng.choice(["v", "h", "diag"])
        step = rng.randint(max(ph, pw) + 1, max(ph, pw) + 3)
        if axis == "v":
            dr, dc = rng.choice([1, -1]) * step, 0
        elif axis == "h":
            dr, dc = 0, rng.choice([1, -1]) * step
        else:
            dr, dc = rng.choice([1, -1]) * step, rng.choice([1, -1]) * step

        # place payload so all k+1 copies fit
        rmin = min(0, k * dr); rmax = max(0, k * dr)
        cmin = min(0, k * dc); cmax = max(0, k * dc)
        # top-left of base copy in [lo, hi] so base..base+k*delta in bounds
        rlo = -rmin; rhi = h - ph - rmax
        clo = -cmin; chi = w - pw - cmax
        if rlo > rhi or clo > chi:
            continue
        pr = rng.randint(rlo, rhi); pc = rng.randint(clo, chi)

        g = full_grid(h, w, 0)
        occ = set()
        # stamp base payload only (the rule generates the copies)
        for (lr, lc) in shape:
            g[pr + lr][pc + lc] = rng.choice(pal); occ.add((pr + lr, pc + lc))
        # also reserve the copy footprints so markers/3-cells don't collide
        for mult in range(k + 1):
            for (lr, lc) in shape:
                rr, cc = pr + lr + mult * dr, pc + lc + mult * dc
                if 0 <= rr < h and 0 <= cc < w:
                    occ.add((rr, cc))

        free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in occ]
        rng.shuffle(free)
        if len(free) < 2 + k:
            continue
        # markers: p1, p2 = p1 + delta. find a free p1 with p2 free in bounds
        placed = None
        for (pr1, pc1) in free:
            qr, qc = pr1 + dr, pc1 + dc
            if 0 <= qr < h and 0 <= qc < w and (qr, qc) not in occ and (qr, qc) != (pr1, pc1):
                placed = (pr1, pc1, qr, qc); break
        if not placed:
            continue
        a, bcol, qr, qc = placed
        g[a][bcol] = 1; g[qr][qc] = 2; occ.add((a, bcol)); occ.add((qr, qc))
        # k color-3 counter cells
        free2 = [(r, c) for r in range(h) for c in range(w) if (r, c) not in occ]
        rng.shuffle(free2)
        if len(free2) < k:
            continue
        for (r, c) in free2[:k]:
            g[r][c] = 3
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    g[5][2] = 6; g[5][3] = 6
    g[10][1] = 1; g[10][3] = 2     # delta (0,2)
    g[0][0] = 3; g[0][2] = 3       # k=2
    if name == "no_markers":
        g[10][1] = 0; g[10][3] = 0
        return g
    if name == "no_payload":
        g[5][2] = 0; g[5][3] = 0
        return g
    if name == "zero_counter":
        g[0][0] = 0; g[0][2] = 0
        return g
    return g
