"""Generator for arc_additional_puzzle_bank_volume7:E48.

Odd-sized hollow red rectangles receive a cyan center dot.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, even_size_frames, filled_centers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "02b1f274e160"
VERSION = "2.1.1"
TASK_ID = "02b1f274e160"
SUMMARY = (
    "0-bg grid with 1-3 hollow color-2 (red) rectangular FRAMES, each "
    "with ODD height and ODD width (so integer center exists). Frames "
    "are separated (≥1-cell buffer). Optionally 1-2 decoy cells in "
    "other colors (color 5 etc.) that the rule preserves but ignores. "
    "Rule: for each color-2 4-connected component, check if it's a "
    "hollow rectangle outline with odd dimensions. If yes, set its "
    "center cell to color 8. Otherwise leave."
)

# Rivals: 'dot every red object' refuted by near-miss objects (solid
# rects, broken frames, even frames) that get nothing. 'center must be
# empty' refuted by center_other boards whose center cell is OVERWRITTEN
# with 8 (the rule never checks the center). 'red center is fine'
# refuted by center_red boards (the component stops being an outline).
# 3 demos incl. >=1 near-miss object.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-3 perfect hollow red outlines with ODD sides (3/5/7) get dots",
    "near-miss red objects (solid / broken / even / red-center) get nothing",
    "center_other boards: a non-red center cell is overwritten with 8",
    "frames separated (>=1-cell buffer)",
]

NEAR_MISSES = ("solid_rect", "broken_frame", "even_frame", "center_red")
DEGENERATE_TEXTURES = ("no_frames",)
HELPFUL_TEXTURES = ("plain", "center_other") + NEAR_MISSES

AXES = {
    "grid_h":    {"type": "int", "default": "rng 11..15", "valid": "5..22"},
    "grid_w":    {"type": "int", "default": "rng 11..15", "valid": "5..22"},
    "n_frames":  {"type": "int", "default": "rng 1..3", "valid": "1..6",
                  "doc": "Qualifying odd hollow frames."},
    "near_miss": {"type": "enum", "default": "rng ~50%: one of solid_rect|"
                                             "broken_frame|even_frame|center_red",
                  "valid": "none|solid_rect|broken_frame|even_frame|center_red",
                  "doc": "An extra red object the rule must NOT dot."},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|center_other|solid_rect|broken_frame|"
                           "even_frame|center_red|no_frames",
                  "doc": "Forces a near-miss kind or a degenerate."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 hollow red(2) outline with odd dimensions (3, 5, or 7)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    # find 4-connected components of color 2
    seen: set = set()
    found_valid = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2 and (r, c) not in seen:
                stack = [(r, c)]
                comp: list = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                r1 = min(rr for rr, _ in comp); r2 = max(rr for rr, _ in comp)
                c1 = min(cc for _, cc in comp); c2 = max(cc for _, cc in comp)
                rh = r2 - r1 + 1; rw = c2 - c1 + 1
                if rh % 2 == 1 and rw % 2 == 1 and rh >= 3 and rw >= 3:
                    # check it is a hollow outline: all cells are on the boundary
                    bbox_size = 2 * rh + 2 * rw - 4
                    if len(comp) == bbox_size:
                        found_valid = True
    if not found_valid:
        errs.append("no valid hollow red(2) outline with odd dimensions >= 3x3")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "center_other", "solid_rect",
                        "broken_frame", "even_frame", "center_red"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_frames = ctx.draw_int("n_frames", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 14, 15)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 11, 15)
        n_frames = ctx.draw_int("n_frames", 1, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int, int, int]] = []
    for _ in range(220):
        if len(boxes) >= n_frames:
            break
        rh = rng.choice([3, 5, 7])
        rw = rng.choice([3, 5, 7])
        if rh > h - 1 or rw > w - 1:
            continue
        r = rng.randint(0, h - rh)
        c = rng.randint(0, w - rw)
        if any(not (r + rh + 1 < ar or ar + ah + 1 < r or c + rw + 1 < ac or ac + aw + 1 < c)
               for ar, ac, ah, aw in boxes):
            continue
        draw_rect_outline(g, r, c, rh, rw, 2)
        boxes.append((r, c, rh, rw))
    if not boxes:
        draw_rect_outline(g, 1, 1, 5, 5, 2)
        boxes.append((1, 1, 5, 5))

    if texture == "center_other" and boxes:
        # non-red cell AT a frame center: the rule never checks the
        # center and OVERWRITES it with 8
        r, c, rh, rw = boxes[rng.randrange(len(boxes))]
        g[r + rh // 2][c + rw // 2] = rng.choice([1, 3, 4, 5, 6, 7, 9])
    elif texture in NEAR_MISSES:
        # one extra RED object that must NOT receive a dot
        for _ in range(120):
            if texture == "even_frame":
                nh, nw = rng.choice([4, 6]), rng.choice([4, 6])
            elif texture == "center_red":
                # MUST be 3x3: only there the red center touches the ring
                # and breaks the outline. At 5x5+ the lone red center is
                # its own 1x1 component — which QUALIFIES as a perfect
                # odd outline and would get dotted itself.
                nh = nw = 3
            else:
                nh, nw = rng.choice([3, 5]), rng.choice([3, 5])
            if nh > h - 1 or nw > w - 1:
                continue
            r = rng.randint(0, h - nh)
            c = rng.randint(0, w - nw)
            if any(not (r + nh + 1 < ar or ar + ah + 1 < r
                        or c + nw + 1 < ac or ac + aw + 1 < c)
                   for ar, ac, ah, aw in boxes):
                continue
            if texture == "solid_rect":
                for rr in range(r, r + nh):
                    for cc in range(c, c + nw):
                        g[rr][cc] = 2
            elif texture == "broken_frame":
                draw_rect_outline(g, r, c, nh, nw, 2)
                # knock out one border cell: the component is no longer
                # a perfect outline of its bbox
                g[r][c + rng.randint(1, nw - 2)] = 0
            elif texture == "center_red":
                draw_rect_outline(g, r, c, nh, nw, 2)
                g[r + nh // 2][c + nw // 2] = 2  # 3x3: joins the ring,
                # the component stops being a pure outline -> no dot
            else:  # even_frame
                draw_rect_outline(g, r, c, nh, nw, 2)
            boxes.append((r, c, nh, nw))
            break

    # 0-2 decoy cells in other colors
    n_decor = rng.randint(0, 2)
    decoy_pool = [1, 3, 4, 5, 6, 7, 9]
    for _ in range(n_decor * 6):
        if n_decor <= 0:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(decoy_pool)
        n_decor -= 1
    return g


def _draw_from_degenerate(name, ctx):
    """no_frames — blank or decoy-only grid: nothing qualifies.
    (even_size_frames and filled_centers were PROMOTED to helpful
    textures: even frames are a near-miss the rule skips, and a filled
    center is either overwritten (non-red) or disqualifying (red) —
    the old 'center must be empty' comment was wrong; the rule never
    checks the center.)"""
    rng = ctx.draw_rng("degenerate_placement")
    h = ctx.draw_int("grid_h", 11, 14)
    w = ctx.draw_int("grid_w", 11, 14)
    g = full_grid(h, w, 0)
    for _ in range(rng.randint(0, 2)):
        g[rng.randrange(h)][rng.randrange(w)] = rng.choice([1, 3, 4, 5, 6])
    return g
