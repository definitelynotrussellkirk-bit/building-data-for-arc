"""Generator for arc_puzzle_bank_21_set11_s:S11_H6 — Find blob with target area+boundary; output bbox-cropped mask.

Rule: area = count of 1s in row 0; bcount = count of 2s in row 0. Find
the body blob (rows 1..) with size==area AND boundary-cell count==bcount;
output that blob bbox-cropped, painted color 8.

Combinatorial axes: grid_h/w, target shape (drives the output), n_distractors,
distractor shapes, marker/blob placement, colors.
Degenerates: no_markers, no_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d03b427c121"
VERSION = "3.0.1"  # diversity: random target shape (varies output) + grid size + placement (was 1 fixed 2x4 blob)
TASK_ID = "0d03b427c121"
SUMMARY = (
    "0-bg grid (h in 4..6, w sized to fit). ROW 0 is a MARKER STRIP: "
    "k color-1 (blue) cells encode TARGET AREA = k, m color-2 (red) "
    "cells encode TARGET BOUNDARY = m, scattered at random columns. "
    "Rows 1.. (the body) hold a RANDOM target polyomino whose "
    "(size, boundary-cell count) == (k, m), PLUS 1-3 distractor blobs "
    "with a DIFFERENT (size, boundary) pair, each a separate component. "
    "Rule: find the unique body blob with size==k AND boundary==m, crop "
    "it to its bbox and paint color 8 (cyan). The target SHAPE is "
    "random, so the OUTPUT varies; grid size, distractors, colors and "
    "all placements vary too (was a single fixed 2x4 blob → k=m=8)."
)

INVARIANTS = [
    "row 0 has k 1-cells (area marker)",
    "row 0 has m 2-cells (boundary marker)",
    "exactly one body blob has size=k AND boundary count=m",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..5 (easy 4, hard 5..6)", "valid": "4..6"},
    "grid_w":         {"type": "int", "default": "sized to fit markers+body", "valid": "12..30"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_distractors":  {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng", "valid": "4..7"},
    "position_bias":  {"type": "str", "default": "row0_markers_body_blobs",
                       "valid": "row0_markers_body_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "4..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_match|multiple_matches"},
}

_BLOB_COLORS = [3, 4, 5, 6, 7, 9]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 has >=1 color-1 and >=1 color-2 (markers); >=1 body blob in rows 1+."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    has_1 = any(grid[0][c] == 1 for c in range(w))
    has_2 = any(grid[0][c] == 2 for c in range(w))
    if not has_1:
        errors.append("no color-1 area markers in row 0")
    if not has_2:
        errors.append("no color-2 boundary markers in row 0")
    body_nz = any(grid[r][c] not in (0, 1, 2) for r in range(1, h) for c in range(w))
    if not body_nz:
        errors.append("no body blob cells (non-{0,1,2}) in rows 1+")
    return errors


def _boundary(cells):
    """Count cells with a 4-neighbor outside the cell set (shape-intrinsic)."""
    s = set(cells)
    return sum(1 for (r, c) in s
               if (r - 1, c) not in s or (r + 1, c) not in s
               or (r, c - 1) not in s or (r, c + 1) not in s)


def _random_blob(rng, size, maxh, maxw):
    """Random connected polyomino of `size` cells fitting maxh x maxw."""
    for _ in range(300):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        minr = min(r for r, c in cells)
        minc = min(c for r, c in cells)
        norm = [(r - minr, c - minc) for r, c in cells]
        bh = max(r for r, c in norm) + 1
        bw = max(c for r, c in norm) + 1
        if bh <= maxh and bw <= maxw:
            return sorted(norm)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        h = 4
        n_distract = rng.randint(1, 2)
        size_lo, size_hi = 3, 5
    elif difficulty == "hard":
        h = rng.randint(5, 6)
        n_distract = rng.randint(2, 3)
        size_lo, size_hi = 4, 7
    else:
        h = rng.randint(4, 5)
        n_distract = rng.randint(1, 3)
        size_lo, size_hi = 3, 6

    body_h = h - 1               # body = rows 1..h-1
    maxw_blob = 5

    # Target shape — its (size, boundary) becomes the marker counts, and the
    # shape itself is the output, so this is the primary diversity axis.
    target = None
    for _ in range(60):
        cand = _random_blob(rng, rng.randint(size_lo, size_hi), body_h, maxw_blob)
        if cand is not None:
            target = cand
            break
    if target is None:                       # tiny fallback (always fits 3x1)
        target = [(0, 0), (0, 1), (1, 0)]
    k, m = len(target), _boundary(target)

    # Distractor blobs with a DIFFERENT (size, boundary) pair so the target
    # is the unique match. Each is its own connected component.
    blobs = [target]
    for _ in range(n_distract):
        for _try in range(40):
            cand = _random_blob(rng, rng.randint(size_lo, size_hi), body_h, maxw_blob)
            if cand is not None and (len(cand), _boundary(cand)) != (k, m):
                blobs.append(cand)
                break

    # Lay blobs left-to-right in the body with a 1-col gap; random vertical
    # offset per blob. Width budget = body extent OR marker count (k+m).
    rng.shuffle(blobs)                        # target not always first
    widths = [max(c for r, c in b) + 1 for b in blobs]
    body_w = sum(widths) + (len(blobs) - 1) + 2
    w = min(30, max(12, k + m, body_w))

    g = full_grid(h, w, 0)
    palette = _BLOB_COLORS[:]
    rng.shuffle(palette)
    col = 1
    for i, b in enumerate(blobs):
        bw = widths[i]
        bh = max(r for r, c in b) + 1
        roff = 1 + rng.randint(0, body_h - bh)
        color = palette[i % len(palette)]
        for r, c in b:
            g[roff + r][col + c] = color
        col += bw + 1

    # Markers: k color-1 and m color-2 cells at random distinct columns in row 0.
    cols = rng.sample(range(w), min(w, k + m))
    for j, c in enumerate(cols):
        g[0][c] = 1 if j < k else 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 4, 16
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # row 0 empty → no area/boundary specification, undefined target
        for r in range(1, 3):
            for c in range(0, 4):
                g[r][c] = 4
        return g
    if name == "no_match":
        # markers specify (size=8, boundary=8) but no body blob matches
        for c in range(8): g[0][c] = 1
        for c in range(8, 16): g[0][c] = 2
        for r, c in [(2, 0), (2, 1)]: g[r][c] = 4
        return g
    if name == "multiple_matches":
        # 2 blobs both match (size=8, boundary=8) → ambiguous target
        for c in range(8): g[0][c] = 1
        for c in range(8, 16): g[0][c] = 2
        for r in range(1, 3):
            for c in range(0, 4): g[r][c] = 4
            for c in range(8, 12): g[r][c] = 6
        return g
    return g
