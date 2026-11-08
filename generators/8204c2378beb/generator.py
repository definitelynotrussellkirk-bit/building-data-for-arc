"""Generator for 8204c2378beb — paste stamp into color-8 frame interior.

Rule (from canonical Racket):
  Detect the color-8 frame (rectangular outline).
  Detect all non-zero non-8 cells (the STAMP).
  Crop the stamp to its bbox.
  Build a new canvas: 0-bg + 8-frame at original position.
  Paste the cropped stamp into the frame's interior starting at
  (frame_top + 1, frame_left + 1). If stamp is larger than interior,
  it may overflow and overwrite the frame's right/bottom edges.
  Output: cleaned canvas (stamp moved into frame, original stamp
  position erased).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import color_rect_frames, components

GENERATOR_ID = "8204c2378beb"
VERSION = "2.1.0"  # self_check verifies exact frame + outside stamp component
TASK_ID = "8204c2378beb"

SUMMARY = (
    "0-bg grid (h×w, ~8-12 by ~8-12) with: (a) one COLOR-8 (cyan) "
    "RECTANGULAR FRAME (border-only) of size 4-6 per side, placed "
    "with ≥1-cell margin from grid borders; (b) one connected STAMP "
    "of 3-6 cells in some non-zero non-8 color, placed OUTSIDE the "
    "frame (at ≥1-cell distance from frame border). Rule: build "
    "fresh 0-canvas. Re-draw the 8-frame at its original position. "
    "Crop the stamp to its bbox. Paste the cropped stamp into the "
    "frame's interior starting at (frame_r1+1, frame_c1+1). If "
    "stamp dimensions exceed interior dimensions, the stamp can "
    "overflow and overwrite the frame's right or bottom edge."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-8 rectangular frame (border-only)",
    "exactly one connected stamp of 3-6 cells in some non-{0, 8} color",
    "stamp placed outside the frame (no cells inside or adjacent)",
    "frame has ≥1-cell margin from grid borders",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_stamp", "stamp_inside_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "frame_size":     {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "stamp_size":     {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "frame_plus_stamp",
                       "valid": "frame_plus_stamp"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frame|no_stamp|stamp_inside_frame"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one hollow color-8 frame plus one outside non-8 stamp component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    frames = color_rect_frames(grid, 8, min_outer_h=4, min_outer_w=4)
    if len(frames) != 1:
        errs.append(f"expected exactly one color-8 rectangular frame, got {len(frames)}")
        return errs
    stamps = components(grid, colors={1, 2, 3, 4, 5, 6, 7, 9}, same_color=True)
    if len(stamps) != 1:
        errs.append(f"expected exactly one connected stamp component, got {len(stamps)}")
        return errs
    if not (3 <= len(stamps[0]["cells"]) <= 6):
        errs.append(f"stamp size should be 3..6, got {len(stamps[0]['cells'])}")
    fr1, fc1, fr2, fc2 = frames[0]
    for r, c in stamps[0]["cells"]:
        if fr1 - 1 <= r <= fr2 + 1 and fc1 - 1 <= c <= fc2 + 1:
            errs.append("stamp touches or lies inside the frame buffer")
            break
    return errs


def _draw_frame(g, r0, c0, h_, w_, color):
    for c in range(c0, c0 + w_):
        g[r0][c] = color
        g[r0 + h_ - 1][c] = color
    for r in range(r0, r0 + h_):
        g[r][c0] = color
        g[r][c0 + w_ - 1] = color


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        fs = ctx.draw_int("frame_size", 4, 4)
        ss = ctx.draw_int("stamp_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        fs = ctx.draw_int("frame_size", 5, 6)
        ss = ctx.draw_int("stamp_size", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        fs = ctx.draw_int("frame_size", 4, 5)
        ss = ctx.draw_int("stamp_size", 3, 5)

    for _ in range(80):
        g = full_grid(h, w, 0)
        # Place frame
        fr0 = rng.randint(1, h - fs - 1)
        fc0 = rng.randint(1, w - fs - 1)
        _draw_frame(g, fr0, fc0, fs, fs, 8)
        # Build a stamp blob
        stamp_cells = _build_blob(rng, ss)
        sh = max(r for r, _ in stamp_cells) + 1
        sw = max(c for _, c in stamp_cells) + 1
        stamp_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        placed = False
        for _try in range(80):
            sr0 = rng.randint(0, h - sh)
            sc0 = rng.randint(0, w - sw)
            cells_abs = [(sr0 + r, sc0 + c) for r, c in stamp_cells]
            # Ensure all cells are outside frame's bbox + 1-cell buffer
            ok = True
            for r, c in cells_abs:
                if not (0 <= r < h and 0 <= c < w):
                    ok = False; break
                # must not be inside or touching frame
                if (fr0 - 1 <= r <= fr0 + fs and
                        fc0 - 1 <= c <= fc0 + fs):
                    ok = False; break
                if g[r][c] != 0:
                    ok = False; break
            if not ok:
                continue
            for r, c in cells_abs:
                g[r][c] = stamp_color
            placed = True
            break
        if placed:
            return g
    raise ValueError("could not realize frame + stamp layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # no color-8 frame — rule has nothing to anchor the paste
        for r, c in [(2, 2), (2, 3), (3, 3)]:
            g[r][c] = 4
        return g
    if name == "no_stamp":
        # frame but no stamp — output is just the empty frame
        _draw_frame(g, 3, 3, 4, 4, 8)
        return g
    if name == "stamp_inside_frame":
        # stamp inside frame — rule still pastes but result trivially overwrites
        _draw_frame(g, 1, 1, 6, 6, 8)
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 4
        return g
    return g
