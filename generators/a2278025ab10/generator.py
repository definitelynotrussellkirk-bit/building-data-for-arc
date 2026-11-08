"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k21 — match crop to color-coded frame.

Rule: hollow rectangular frames in colors 1, 2, 3. Non-frame components have a
hole count. Match each non-frame to the frame whose color = holes + 1; center-
place the crop into that frame's interior.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no color-{1,2,3} frames → rule has no
destinations); no_components (frames but no non-frame shapes → no
content to match); component_no_match (a component's hole count
maps to a frame color not present → rule's lookup returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "a2278025ab10"
VERSION = "1.3.1"  # band-aware + grid-capped frame size; raise easy grid (was ~92% easy / ~4% default starvation)
TASK_ID = "a2278025ab10"

SUMMARY = "Hollow rectangular frames in colors {1,2,3}; non-frame components have hole counts 0/1/2; rule matches each component to the frame whose color = holes+1, center-places the crop into that frame's interior."

# Rivals: 'paste component into first frame' refuted by ≥2 demos
# where match changes with hole count. 'paste at corner instead of
# center' refuted by ≥1 demo with clear center alignment. 'use frame
# color for the pasted shape' refuted by any demo (component keeps
# its color). 'erase non-frame component' refuted by any demo (it
# survives in the matched frame).
# 4 demos with varied component layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly 3 hollow color-{1, 2, 3} rectangular frames with interior big enough for the matched shape",
    "1-3 non-frame components with distinct hole counts in {0, 1, 2}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_components", "component_no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 13..16", "valid": "11..22"},
    "grid_w":            {"type": "int", "default": "rng 16..19", "valid": "13..24"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "three_frames_with_hole_components",
                          "valid": "three_frames_with_hole_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_frames|no_components|component_no_match"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 cell each of color-{1,2,3} (frames); >=1 non-{0,1,2,3} component cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    for fcolor in (1, 2, 3):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == fcolor]
        if not cells:
            errs.append(f"no color-{fcolor} frame cells found")
    comp_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1, 2, 3)]
    if not comp_cells:
        errs.append("no non-{0,1,2,3} component cells found")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _solid(rng, color):
    sh, sw = rng.choice([(2, 2), (2, 3), (3, 2)])
    cells = [(r, c, color) for r in range(sh) for c in range(sw)]
    return cells, sh, sw


def _ring(rng, color):
    sh, sw = rng.choice([(3, 3), (3, 4), (4, 3)])
    cells = []
    for r in range(sh):
        for c in range(sw):
            if r in (0, sh - 1) or c in (0, sw - 1):
                cells.append((r, c, color))
    return cells, sh, sw


def _double_ring(rng, color):
    sh, sw = rng.choice([(3, 5), (3, 6)])
    cells = []
    holes = {(1, 1), (1, sw - 2)} if sw == 5 else {(1, 1), (1, 4)}
    for r in range(sh):
        for c in range(sw):
            is_perim = (r in (0, sh - 1) or c in (0, sw - 1))
            middle = (r == 1 and 0 < c < sw - 1)
            if is_perim or (middle and (r, c) not in holes):
                cells.append((r, c, color))
    return cells, sh, sw


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 17, 19)
        rmax = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 22)
        w = ctx.draw_int("grid_w", 20, 24)
        rmax = 7
    else:
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 17, 21)
        rmax = 7
    # Frame 3 is the largest at (rmax+1)×(rmax+2); cap rmax against the actual
    # drawn grid so it (plus the other two frames + three components) can pack —
    # the default band's small end (14×17) with rmax=7 still starved ~0.4%. The
    # floor stays ≥5 for every band's grid range, so crops always fit.
    rmax = min(rmax, h - 9, w - 11)
    rng = ctx.draw_rng("layout")

    for outer in range(150):
        g = full_grid(h, w, 0)
        ok = True
        # Randomized frame sizes (each ≥5 to fit a ring or double-ring). The upper
        # bound scales with the band: the easy grid (12-14 × 14-17) can't pack three
        # up-to-8×9 frames + three components — it failed ~92% — so easy caps frame
        # size at 5 (frame 3 is then 6×7, the same small frames default emits at
        # rsize=5). The runner already accepts these sizes.
        def rsize():
            return rng.randint(5, rmax)
        frame_specs = [
            (1, rsize(), rsize()),
            (2, rsize(), rsize() + 1),
            (3, rsize() + 1, rsize() + 2),
        ]
        for color, fh, fw in frame_specs:
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                    continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue

        builders = [_solid, _ring, _double_ring]
        comp_colors = rng.sample([4, 5, 6, 7, 8, 9], 3)
        for builder, color in zip(builders, comp_colors):
            cells, sh, sw = builder(rng, color)
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for dr, dc, cc in cells:
                    g[r0 + dr][c0 + dc] = cc
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize hard_k21 layout in 40 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 14, 17
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No color-{1,2,3} frames — rule has no destinations.
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 4
        for r in range(3):
            for c in range(3):
                g[7 + r][9 + c] = 5
        return g
    if name == "no_components":
        # Frames present but no shapes to match.
        draw_frame(g, 1, 1, 5, 5, 1)
        draw_frame(g, 1, 7, 6, 12, 2)
        draw_frame(g, 7, 1, 12, 8, 3)
        return g
    if name == "component_no_match":
        # Only color-2 frame present, but components have hole counts 0/1/2 —
        # 0-hole component needs color-1 frame (missing), 2-hole needs color-3 (missing).
        draw_frame(g, 1, 7, 6, 12, 2)
        for r in range(2):
            for c in range(2):
                g[2 + r][2 + c] = 4
        for r in range(3):
            for c in range(3):
                if r in (0, 2) or c in (0, 2):
                    g[8 + r][2 + c] = 5
        return g
    return g
