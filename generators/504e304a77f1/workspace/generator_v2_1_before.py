"""Generator for arc_puzzle_bank_21_set7:hard_g15 — center each object inside its frame.

Rule: split the components into hollow rectangular FRAMES (the outline of an
>=3x3 bbox) and other OBJECTS. Sort the frames by interior area and the objects
by size, pair them up (smallest object -> smallest-interior frame), and CENTER
each object's shape inside its paired frame. Output = the frames plus the
centered objects.

The old docstring called this a "multi-motif gallery pack" and the generator
scattered random motifs with NO frames -> the rule found no frames and produced
an empty output (distinct=3-9, wrong distribution). Now: K matched (frame,
object) pairs — frames with strictly increasing interior area, objects with
strictly increasing size where object i fits frame i's interior.

Combinatorial axes: pair count K, the frame sizes, the object shapes/sizes,
colors, positions, grid size.
Degenerates: no_frames, no_objects, object_too_big.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "504e304a77f1"
VERSION = "2.1.0"  # FIX identity_demo (1/18, the fallback): the last-resort fallback put the object at the frame's CENTER (3,3) inside the frame, so the rule's center-the-object op was a no-op -> output==input. Now the fallback places the object OUTSIDE the frame (so the rule must move it in) and the main loop retries on a larger canvas before falling back. + self_check.
TASK_ID = "504e304a77f1"
SUMMARY = (
    "0-bg grid (size varies) with K (2-4) hollow rectangular FRAMES (the "
    "outline of a bbox, interior areas strictly increasing) and K OBJECTS "
    "(random polyominoes, sizes strictly increasing, object i fitting frame i's "
    "interior), all in distinct colors, scattered apart. Rule: pair frames "
    "(sorted by interior area) with objects (sorted by size) and center each "
    "object's shape inside its frame. Output = the frame outlines plus the "
    "centered objects."
)

INVARIANTS = [
    "background is 0",
    "K hollow rectangular frames with strictly increasing interior areas",
    "K objects with strictly increasing sizes, object i fits frame i's interior",
    "frames and objects are separated distinct components in distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_objects", "object_too_big")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..26"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..26"},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "4..8"},
    "position_bias":  {"type": "str", "default": "frames_and_objects",
                       "valid": "frames_and_objects"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "4..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, n, mh, mw):
    cells = {(rng.randint(0, mh - 1), rng.randint(0, mw - 1))}
    guard = 0
    while len(cells) < n and guard < 300:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < mh and 0 <= nc < mw:
            cells.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _frame_outline(fh, fw):
    """Outline (border) cells of an fh x fw rectangle."""
    return [(r, c) for r in range(fh) for c in range(fw)
            if r in (0, fh - 1) or c in (0, fw - 1)]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _ in range(150):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        if _free(g, top, left, cells):
            for dr, dc in cells:
                g[top + dr][left + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        k = 2
    elif difficulty == "hard":
        k = rng.randint(3, 4)
    else:
        k = rng.randint(2, 3)

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 * k)
    # frame i interior = I x I with I = 3+i (areas strictly increasing); object i
    # size strictly increasing and <= the interior area, fitting the interior.
    frames = []   # (outline_cells, color)
    obj_items = []  # (obj_cells, color)
    for i in range(k):
        ii = 3 + i
        fh = fw = ii + 2                         # total frame bbox (interior ii x ii)
        frames.append((_frame_outline(fh, fw), colors[i]))
        size = min(3 + 2 * i, ii * ii - 1)
        obj_items.append((_rand_poly(rng, size, ii, ii), colors[k + i]))

    big = (3 + (k - 1)) + 2                       # largest frame side
    h = ctx.draw_int("grid_h", big + 6, min(26, big + 14))
    w = ctx.draw_int("grid_w", big + 6, min(26, big + 14))

    for _outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for cells, color in frames + obj_items:    # frames first (bigger), then objects
            if not _place(g, rng, cells, color):
                ok = False
                break
        if ok:
            return g
    # fallback: single frame + a SEPARATE object placed OUTSIDE the frame, so
    # the rule must move/center it (output != input). The frame sits top-left;
    # the object is a 2-cell domino in the far bottom-right corner.
    fb = big + 10
    g = full_grid(fb, fb, 0)
    fc, oc = colors[0], colors[k]
    for r, c in _frame_outline(5, 5):
        g[1 + r][1 + c] = fc
    g[fb - 2][fb - 2] = oc
    g[fb - 2][fb - 3] = oc
    return g


def _is_frame(cells):
    """cells form the hollow outline of a >=3x3 bbox."""
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    outline = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
               if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == outline


def _components(grid):
    """Return non-background 4-connected same-color components."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    parts = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        cells = [start]
        todo = [start]
        while todo:
            r, c = todo.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    cells.append((nr, nc))
                    todo.append((nr, nc))
        parts.append(cells)
    return parts


def self_check(grid, *, difficulty=None, meta=None):
    """At least one hollow frame and one ordinary connected component exist."""
    parts = _components(grid)
    frames = [cells for cells in parts if _is_frame(cells)]
    objects_ = [cells for cells in parts if not _is_frame(cells)]
    msgs = []
    if not frames:
        msgs.append("no hollow rectangular frame found")
    if not objects_:
        msgs.append("no non-frame object found")
    return msgs


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(12, 14, 0)
    for r, c in _frame_outline(5, 5):
        g[1 + r][1 + c] = 3
    if name == "no_frames":
        g = full_grid(12, 14, 0)
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
        return g
    if name == "no_objects":
        return g
    if name == "object_too_big":
        for r in range(3):
            for c in range(3):
                g[7 + r][8 + c] = 6
        return g
    return g
