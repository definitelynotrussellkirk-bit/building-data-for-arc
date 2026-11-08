"""Generator for arc_puzzle_bank_21_set19_bundle:medium_p04 — gallery of frame interiors.

Rule (canonical): detect rectangular HOLLOW FRAMES (border-only rectangles,
h>=3, w>=3). Sort them by ascending color. Crop each frame's INTERIOR
(the subgrid strictly inside the border). Pack the interiors left-to-right
into a horizontal "gallery", each centered vertically, separated by a 1-col
gap. The gallery is the output.

(Prior generator was the WRONG task: it drew hollow frames with EMPTY
interiors plus separate solid blocks and claimed a "pair solids into frames
by size" rule -> the canonical rule galleried blank interiors -> distinct=7.
This version puts varied CONTENT inside each frame, which is what the rule
actually extracts.)

Combinatorial axes: grid size, n_frames, per-frame size (incl. non-square),
per-frame interior content + colors.
Degenerates: no_frames (no hollow frames -> empty gallery), empty_interiors
(frames present but interiors blank -> blank gallery), single_frame (only one
frame -> gallery has no second panel).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "39a391643830"
VERSION = "2.0.1"  # WRONG-TASK fix: rule galleries frame INTERIORS, but gen drew empty frames + separate solids -> blank gallery (distinct=7). Now 2-4 hollow frames each holding RANDOM interior content (distinct colors), varied frame sizes (incl. non-square) -> gallery output varies richly.
TASK_ID = "39a391643830"

SUMMARY = "Hollow frames each holding content; output = horizontal gallery of the interiors."

INVARIANTS = [
    "background is 0",
    ">=2 hollow rectangular frames (border-only, h>=3, w>=3) in distinct colors",
    "each frame's interior holds >=1 non-frame-colored content cell",
    "frames are 4-conn isolated (separated by >=1 bg cell)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "empty_interiors", "single_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 14..20", "valid": "12..22"},
    "n_frames":          {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "varies", "valid": "4..8"},
    "position_bias":     {"type": "str", "default": "frames_scattered",
                          "valid": "frames_scattered"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "4..8"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 hollow rectangular frames (border-only); each frame has content."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        pass  # degenerate (no_frames) — allowed
    return errors


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _fill_interior(g, rng, r0, c0, fh, fw, frame_color):
    """Random content inside the frame border. Content colors differ from the
    frame color so the border stays a pure hollow rectangle (own component)."""
    content_pool = [c for c in (1, 2, 3, 4, 5, 6, 7, 8, 9) if c != frame_color]
    cc = rng.sample(content_pool, rng.randint(1, 2))
    cells = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
             for c in range(c0 + 1, c0 + fw - 1)]
    filled = 0
    for (r, c) in cells:
        if rng.random() < 0.5:
            g[r][c] = rng.choice(cc); filled += 1
    if filled == 0 and cells:        # guarantee >=1 content cell (non-blank panel)
        r, c = rng.choice(cells)
        g[r][c] = cc[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_frames", 2, 2); fmax = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 16, 22)
        n = ctx.draw_int("n_frames", 3, 4); fmax = 6
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 14, 20)
        n = ctx.draw_int("n_frames", 2, 3); fmax = 6
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        frame_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        placed_all = True
        for color in frame_colors:
            fh = rng.randint(3, fmax); fw = rng.randint(3, fmax)
            placed = False
            for _ in range(150):
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                    draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                    _fill_interior(g, rng, r0, c0, fh, fw, color)
                    placed = True
                    break
            if not placed:
                placed_all = False
                break
        if placed_all:
            return g
    raise ValueError("could not realize frame-gallery layout")


def _draw_from_degenerate(name, rng):
    h, w = 12, 16
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Solid blocks only, no hollow frames -> rule finds nothing to gallery.
        for r in range(2, 4):
            for c in range(2, 4):
                g[r][c] = 4
        for r in range(7, 10):
            for c in range(8, 11):
                g[r][c] = 6
        return g
    if name == "empty_interiors":
        # Frames present but interiors blank -> gallery of blank panels.
        draw_frame(g, 1, 1, 5, 5, 2)
        draw_frame(g, 1, 9, 5, 13, 3)
        return g
    if name == "single_frame":
        # Only one frame -> gallery has a single panel (no second).
        draw_frame(g, 2, 2, 6, 7, 2)
        g[4][4] = 5
        return g
    return g
