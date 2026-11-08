"""Generator for arc_puzzle_bank_21_set8:medium_h14 — fill each frame's hole with its color.

Rule (verified against canonical; the old "multi-motif gallery pack" docstring
was boilerplate that masked the real task): for every 4-connected object, fill
the cells of its bbox INTERIOR that are NOT object cells with the object's color,
onto a BLANK canvas. In practice the objects are HOLLOW RECTANGULAR FRAMES, so
the rule fills each frame's interior hole with the frame's color and DROPS the
outline (output = just the filled holes).

A valid input is therefore: several hollow rectangular frames (rings) in distinct
colors, each at least 3x3 so it encloses a hole, well separated (>=1 bg gap) so
they stay distinct 4-connected components. Output is derived by the rule.

Combinatorial axes (8): grid_h, grid_w, n_frames, frame_h, frame_w,
frame_colors, positions, difficulty.
Degenerates: no_frames, single_frame, solid_block (no hole -> empty output).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a2abf5aa05a"
VERSION = "2.0.1"  # WRONG-TASK + POISON FIX: rule fills each object's bbox-interior hole with its color (canonical objects are HOLLOW FRAMES); old gen made tiny SOLID 3-5 cell blobs (no interior hole) -> output near-empty, distinct=10. Now emit varied hollow rectangular frames (varied non-square size -> varied hole shape, distinct colors, multiple per grid, scaled toward contest density on hard).
TASK_ID = "1a2abf5aa05a"
SUMMARY = (
    "0-bg grid with several HOLLOW RECTANGULAR "
    "FRAMES (rings, each >=3x3) in distinct "
    "colors, well separated. Rule: fill each "
    "frame's interior hole with the frame's "
    "color onto a blank canvas and drop the "
    "outline (output = just the filled holes, "
    "one solid rectangle per frame)."
)

INVARIANTS = [
    "background is 0",
    "every object is a hollow rectangular frame at least 3x3 (so it has a hole)",
    "frames are in distinct non-0 colors",
    "frames are separated by >=1 bg cell (distinct 4-connected components)",
]

DEGENERATE_TEXTURES = ("no_frames", "single_frame", "solid_block")
HELPFUL_TEXTURES = ("frames",)

AXES = {
    "grid_h":      {"type": "int", "default": "rng by difficulty", "valid": "7..22"},
    "grid_w":      {"type": "int", "default": "rng by difficulty", "valid": "9..24"},
    "n_frames":    {"type": "int", "default": "rng 2..6", "valid": "1..7"},
    "frame_h":     {"type": "int", "default": "rng 3..8", "valid": "3..10"},
    "frame_w":     {"type": "int", "default": "rng 3..8", "valid": "3..10"},
    "frame_colors":{"type": "list", "default": "distinct non-0", "valid": "1..9"},
    "texture":     {"type": "str", "default": "alias for layout",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 distinct non-zero colors (hollow frames)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frames", "single_frame", "solid_block"):
        return errs
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 1:
        errs.append("no frame cells found")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def _draw_frame(g, r0, c0, fh, fw, color):
    for c in range(c0, c0 + fw):
        g[r0][c] = color
        g[r0 + fh - 1][c] = color
    for r in range(r0 + 1, r0 + fh - 1):
        g[r][c0] = color
        g[r][c0 + fw - 1] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_frames", 2, 3)
        fmax = 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 18, 24)
        n = ctx.draw_int("n_frames", 4, 6)
        fmax = 8
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        n = ctx.draw_int("n_frames", 3, 4)
        fmax = 7
    rng = ctx.draw_rng("layout")
    colors = ctx.draw_distinct_colors("frame_colors", n=min(n, 8), exclude={0})

    for _outer in range(60):
        g = full_grid(h, w, 0)
        placed = 0
        for i in range(n):
            color = colors[i % len(colors)]
            for _ in range(120):
                fh = rng.randint(3, min(fmax, h - 1))
                fw = rng.randint(3, min(fmax, w - 1))
                r0 = rng.randint(0, h - fh)
                c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                    continue
                _draw_frame(g, r0, c0, fh, fw, color)
                placed += 1
                break
        if placed >= max(2, n - 1):  # tolerate one wedge on tight grids
            return g
    return g


def _draw_from_degenerate(name):
    g = full_grid(10, 12, 0)
    if name == "no_frames":
        return g
    if name == "single_frame":
        _draw_frame(g, 2, 2, 4, 5, 3)  # one frame -> one filled hole
        return g
    if name == "solid_block":
        # a solid block has no interior hole -> the rule outputs nothing for it
        for r in range(3, 6):
            for c in range(3, 7):
                g[r][c] = 4
        return g
    return g
