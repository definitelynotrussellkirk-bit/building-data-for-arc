"""Generator for 8b:m51 — bottom-row key selects a same-color blob to rotate.

Rule: the KEY color is the first non-zero cell in the BOTTOM ROW. The target is
the (first) object whose color == key, EXCLUDING the single key marker sitting on
the bottom row. Output = the target blob cropped to its bbox and rotated 90deg CW.

Prior generator placed the key at (0,0) (TOP-LEFT corner) and described a "corner
key", but the rule reads the key from the BOTTOM ROW. It only "validated" because
the rule still runs deterministically on whatever happened to be in the bottom row
-- the produced task was off-distribution. This version puts a single key marker
in the bottom row, one same-color non-rectangular target blob in the body, and
1-4 distractor blobs in other colors (all matching the canonical structure).

Rule-safe diversity: grid size, target blob shape/size, distractor count/shapes,
colors, positions.
Degenerates: no_key, no_blob, square_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f3e3a362e6c4"
VERSION = "2.0.1"  # add executable self_check for bottom-row key + target blob invariants
TASK_ID = "f3e3a362e6c4"
SUMMARY = (
    "0-bg grid with a single KEY MARKER cell in the BOTTOM ROW (color = key), one "
    "same-color NON-RECTANGULAR target blob in the body, and 1-4 distractor blobs "
    "in other colors. Blobs are non-touching (grow_blob padding) and stay off the "
    "bottom row. Rule: key = first non-zero in bottom row; target = the body object "
    "of that color; output = its bbox crop rotated 90deg CW. (Was: key at top-left "
    "corner -> off-distribution.)"
)

INVARIANTS = [
    "background is 0",
    "exactly one key marker (single cell) in the bottom row",
    "exactly one body blob in the key color (non-rectangular, size >= 2)",
    "1-4 distractor blobs in colors other than the key",
    "all blobs are separate 4-connected components and off the bottom row",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blob", "square_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":      {"type": "int", "default": "8-9 easy / 9-12 med / 11-14 hard", "valid": "6..16"},
    "grid_w":      {"type": "int", "default": "8-10 easy / 9-12 med / 11-15 hard", "valid": "7..16"},
    "blob_size":   {"type": "int", "default": "target 3-4 easy / 3-5 med / 4-6 hard", "valid": "2..7"},
    "n_distractors": {"type": "int", "default": "1-2 easy / 2-3 med / 3-4 hard", "valid": "1..5"},
    "density":     {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":     {"type": "str", "default": "alias for palette_kind",
                    "valid": "default|warm|cool|varied|no_key|no_blob|square_blob"},
}


def _nonrect_blob(rng, h1, w, used, size):
    """A non-rectangular blob (bbox area != cell count) in rows 0..h1-1."""
    for _ in range(40):
        cells = grow_blob(rng, h1, w, used, size, max_attempts=20)
        if cells is None:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if area != len(cells):
            return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, tsz, nd = (8, 10), (8, 11), (3, 5), (1, 2)
    elif difficulty == "hard":
        hr, wr, tsz, nd = (12, 15), (12, 16), (6, 10), (3, 4)
    else:
        hr, wr, tsz, nd = (10, 13), (10, 13), (4, 8), (2, 3)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    n_distract = rng.randint(*nd)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 1 + n_distract)
    key = colors[0]; distractors = colors[1:]
    h1 = h - 1                              # body rows 0..h-2 (keep blobs off bottom row)

    for _outer in range(30):
        g = full_grid(h, w, 0)
        mc = rng.randrange(w)
        g[h - 1][mc] = key                 # single key marker in the bottom row
        used = {(h - 1, mc)}
        target = _nonrect_blob(rng, h1, w, used, rng.randint(*tsz))
        if target is None:
            continue
        for r, c in target:
            g[r][c] = key
        used |= target
        ok = True
        for col in distractors:
            blob = grow_blob(rng, h1, w, used, rng.randint(2, 4), max_attempts=40)
            if blob is None:
                ok = False; break
            for r, c in blob:
                g[r][c] = col
            used |= blob
        if ok:
            return g
    raise ValueError("could not realize layout")


def _components4_by_color(grid, cells):
    """Return [(color, set[(r,c)]), ...] 4-connected within the provided cells."""
    cell_set = set(cells)
    comps = []
    while cell_set:
        start = cell_set.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        comp = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cell_set and grid[nb[0]][nb[1]] == color:
                    cell_set.remove(nb)
                    comp.add(nb)
                    stack.append(nb)
        comps.append((color, comp))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for bottom-row-key component rotation instances."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]

    bottom_nonzero = [(c, grid[h - 1][c]) for c in range(w) if grid[h - 1][c] != 0]
    if len(bottom_nonzero) != 1:
        errs.append(f"expected exactly one non-zero bottom-row key marker, got {len(bottom_nonzero)}")
        return errs
    _marker_col, key = bottom_nonzero[0]
    if not (1 <= key <= 9):
        errs.append(f"key color must be 1..9, got {key}")

    body_cells = [(r, c) for r in range(h - 1) for c in range(w) if grid[r][c] != 0]
    comps = _components4_by_color(grid, body_cells)
    key_comps = [cells for color, cells in comps if color == key]
    distractor_comps = [(color, cells) for color, cells in comps if color != key]
    if len(key_comps) != 1:
        errs.append(f"expected exactly one body component in key color {key}, got {len(key_comps)}")
    else:
        target = key_comps[0]
        if len(target) < 2:
            errs.append("target key-color body component must have at least two cells")
        rs = [r for r, _ in target]
        cs = [c for _, c in target]
        bbox_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if bbox_area == len(target):
            errs.append("target key-color component is a solid rectangle; rotation branch is under-exercised")
    if not distractor_comps:
        errs.append("expected at least one distractor component in a non-key color")
    if any(color == 0 for color, _ in comps):
        errs.append("component extraction included background unexpectedly")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_key":
        # body blobs but empty bottom row -> rule has no key
        for r, c in [(3, 3), (4, 3), (4, 4)]: g[r][c] = 4
        for r, c in [(2, 6), (3, 6)]: g[r][c] = 6
        return g
    if name == "no_blob":
        # key marker in bottom row but no same-color body blob
        g[h - 1][4] = 4
        for r, c in [(3, 5), (4, 5)]: g[r][c] = 6
        return g
    if name == "square_blob":
        # body blob is a solid 2x2 -> rotate-cw is identity
        g[h - 1][2] = 4
        for r in range(3, 5):
            for c in range(3, 5):
                g[r][c] = 4
        for r, c in [(1, 6), (1, 7)]: g[r][c] = 6
        return g
    return g
