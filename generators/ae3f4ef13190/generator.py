"""Generator for arc_puzzle_bank_eighth_21_bundle:hard_53_frame_select_rank_center.

Rule: color-8 and color-9 rectangular FRAMES (perfect borders). Inside each
frame there is a KEY cell (1 or 2) and several colored objects of distinct
sizes. key==1 -> pick the SMALLEST interior object; key==2 -> pick the LARGEST.
Crop it, center it in the frame's interior (rotated 180 if the frame is
color 9), redraw the frame outline. Output = the frames with their centered
chosen objects.

v1.1.0 was a WRONG-TASK generator ("multi-motif gallery pack") that scattered
random blobs — it never built color-8/9 rectangular frames with keyed interiors,
so the rule barely did anything (distinct_out 9). Rewritten to construct exactly
the frame/interior structure the rule reads.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "ae3f4ef13190"
RULE_HASH = "62bfd2917960"  # canonical rule this generator was written against
VERSION = "2.0.1"  # WRONG-TASK rewrite: was a random motif gallery; rule reads color-8/9 rect frames with a 1/2 key selecting smallest/largest interior object, centered (rotated for 9). Now build that structure with varied frames/objects/keys.
TASK_ID = "ae3f4ef13190"

SUMMARY = ("Color-8/9 rectangular frames; each holds a 1/2 key + several "
           "distinct-size objects; rule centers the smallest (key 1) or "
           "largest (key 2) object in the frame (rotated 180 for color-9).")

INVARIANTS = [
    "frames are perfect rectangular borders in color 8 or 9, interior >= 5x5",
    "each frame interior has exactly one key cell (1 or 2)",
    "interior objects have strictly distinct sizes (smallest/largest unambiguous)",
    "interior objects use colors not in {0,1,2,8,9} and are separated (own components)",
]

DEGENERATE_TEXTURES = ("no_frames", "empty_frame", "no_key")
HELPFUL_TEXTURES = ()

AXES = {
    "n_frames":  {"type": "int", "default": "by difficulty", "valid": "1..2"},
    "frame_h":   {"type": "int", "default": "by difficulty", "valid": "7..11"},
    "frame_w":   {"type": "int", "default": "by difficulty", "valid": "7..11"},
    "texture":   {"type": "str", "default": "none", "valid": "|".join(DEGENERATE_TEXTURES)},
}

_OBJ_COLORS = [3, 4, 5, 6, 7]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _fill_interior(g, r1, c1, r2, c2, rng):
    """Place a 1/2 key + 2-3 distinct-size colored objects in the frame interior."""
    ir1, ic1, ir2, ic2 = r1 + 1, c1 + 1, r2 - 1, c2 - 1
    occupied = set()                       # cells + 1-ring padding (keep separate)

    def _free(cells):
        for (r, c) in cells:
            if not (ir1 <= r <= ir2 and ic1 <= c <= ic2):
                return False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if (r + dr, c + dc) in occupied:
                        return False
        return True

    def _mark(cells):
        for (r, c) in cells:
            occupied.add((r, c))

    colors = _OBJ_COLORS[:]
    rng.shuffle(colors)
    sizes = rng.sample([1, 2, 3, 4], rng.randint(2, 3))   # strictly distinct sizes
    n_placed = 0
    for i, sz in enumerate(sizes):
        shape = _poly(rng, sz)
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        for _ in range(60):
            r0 = rng.randint(ir1, ir2 - sh + 1); c0 = rng.randint(ic1, ic2 - sw + 1)
            cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
            if _free(cells):
                for (r, c) in cells:
                    g[r][c] = colors[i % len(colors)]
                _mark(cells)
                n_placed += 1
                break
    # key cell (1 or 2), isolated from objects
    key = rng.choice([1, 2])
    for _ in range(80):
        r = rng.randint(ir1, ir2); c = rng.randint(ic1, ic2)
        if _free([(r, c)]):
            g[r][c] = key
            break
    return n_placed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-8 or color-9 frame cells present, key cell (1 or 2) present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frames", "empty_frame", "no_key"):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_frame = any(grid[r][c] in (8, 9) for r in range(h) for c in range(w))
    has_key = any(grid[r][c] in (1, 2) for r in range(h) for c in range(w))
    if not has_frame:
        errs.append("no color-8 or color-9 frame cells found")
    if not has_key:
        errs.append("no key cell (1 or 2) found inside frame")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_frames = 1; fh = ctx.draw_int("frame_h", 7, 8); fw = ctx.draw_int("frame_w", 7, 8)
    elif difficulty == "hard":
        n_frames = 2; fh = ctx.draw_int("frame_h", 8, 11); fw = ctx.draw_int("frame_w", 8, 11)
    else:
        n_frames = rng.randint(1, 2); fh = ctx.draw_int("frame_h", 7, 10); fw = ctx.draw_int("frame_w", 7, 10)

    # lay frames left-to-right with a 1-col gap and 1-cell outer margin
    gap = 1
    w = 1 + n_frames * fw + (n_frames - 1) * gap + 1
    h = fh + 2
    g = full_grid(h, w, 0)
    fcolors = [8, 9] if n_frames == 2 else [rng.choice([8, 9])]
    rng.shuffle(fcolors)
    for i in range(n_frames):
        c1 = 1 + i * (fw + gap)
        r1 = 1
        r2, c2 = r1 + fh - 1, c1 + fw - 1
        draw_frame(g, r1, c1, r2, c2, fcolors[i])
        _fill_interior(g, r1, c1, r2, c2, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    draw_frame(g, 1, 1, 7, 7, 8)
    if name == "no_frames":
        return full_grid(h, w, 0)
    if name == "empty_frame":
        return g                              # frame but no interior objects/key
    if name == "no_key":
        g[3][3] = 4; g[5][5] = 4              # objects but no 1/2 key
        return g
    return g
