"""Generator for arc_puzzle_bank_21_next:medium_c02 — keep only frame-shaped objects.

Rule: keep objects whose cells form an exact rectangle FRAME — h≥3,
w≥3, all cells on bbox border (i.e., size = perimeter). Drop solid
rectangles and irregular shapes. Output preserves only the frame
objects with original colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid, draw_rect

GENERATOR_ID = "54875f792be0"
VERSION = "2.1.0"
TASK_ID = "54875f792be0"
SUMMARY = (
    "0-bg grid with: (a) N (1-3) hollow rectangle FRAMES (h≥3, w≥3, "
    "cells form only the bbox border); (b) M (1-3) DISTRACTOR shapes "
    "— solid rectangles or irregular shapes. All objects in distinct "
    "colors. Rule: extract every connected non-bg component. For each, "
    "check if it's a frame: h≥3, w≥3, size = perimeter = 2(h+w) - 4, "
    "and all cells on bbox border. Keep frames (preserve colors), "
    "drop all non-frames. Output: fresh 0-grid with only the frames."
)

# Rivals: 'output is input' refuted by demos with ≥1 distractor.
# 'keep solid rectangles too' refuted by demos where solid drops.
# 'use color 8 for frames' refuted by demos preserving frame colors.
# 'keep all objects' refuted by demos showing distractors dropped.
# 'drop frames, keep distractors' refuted (the opposite). 'keep
# largest only' refuted by demos with multiple frames all kept.
# 3 demos with mix of frames + distractors of varied sizes pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 hollow frame (h≥3, w≥3) in some non-bg color",
    "≥1 distractor (solid rectangle, irregular shape, or 1×N strip) in another color",
    "components don't 4-touch (each is its own 4-conn component)",
    "all components in distinct colors so the rule's per-shape verdict is unambiguous",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate() (frame/distractor counts are drawn off the layout rng, not keyed).
# Defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h": {"type": "int", "default": "rng 11..13", "valid": "9..16",
               "doc": "Grid height (easy 9..11, medium 11..13, hard 13..16)."},
    "grid_w": {"type": "int", "default": "rng 13..15", "valid": "11..18",
               "doc": "Grid width (easy 11..13, medium 13..15, hard 14..18)."},
}


def _draw_solid(g, r1, c1, r2, c2, color):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = color


def _free(g, r0, c0, h_obj, w_obj, margin=1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + h_obj > h or c0 + w_obj > w:
        return False
    for r in range(max(0, r0 - margin), min(h, r0 + h_obj + margin)):
        for c in range(max(0, c0 - margin), min(w, c0 + w_obj + margin)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n_frames, n_distractors = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_frames, n_distractors = rng.randint(2, 3), rng.randint(2, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
        n_frames, n_distractors = rng.randint(1, 2), rng.randint(1, 2)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_frames + n_distractors)
    # Place frames
    for i in range(n_frames):
        color = palette[i]
        for _ in range(60):
            fh = rng.randint(3, 5); fw = rng.randint(3, 5)
            r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
            if _free(g, r0, c0, fh, fw):
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                break
    # Place distractors
    for i in range(n_distractors):
        color = palette[n_frames + i]
        kind = rng.choice(["solid", "irregular", "thin"])
        for _ in range(60):
            if kind == "solid":
                dh = rng.randint(2, 3); dw = rng.randint(2, 3)
            elif kind == "thin":
                dh = rng.randint(1, 1); dw = rng.randint(2, 4)
            else:
                dh = rng.randint(2, 3); dw = rng.randint(2, 3)
            r0 = rng.randint(0, h - dh); c0 = rng.randint(0, w - dw)
            if not _free(g, r0, c0, dh, dw):
                continue
            if kind == "solid" or kind == "thin":
                _draw_solid(g, r0, c0, r0 + dh - 1, c0 + dw - 1, color)
            else:
                # Irregular: place 3-5 cells in some L-shape
                irregular_cells = [(0, 0), (0, 1), (1, 0)]
                for dr, dc in irregular_cells:
                    g[r0 + dr][c0 + dc] = color
            break
    return g

def _components(grid):
    h = len(grid); w = len(grid[0]) if h else 0; seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def _is_frame(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    hh, ww = r2 - r1 + 1, c2 - c1 + 1
    if hh < 3 or ww < 3:
        return False
    border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
              if r in (r1, r2) or c in (c1, c2)}
    return set(cells) == border


def self_check(grid, *, difficulty=None, meta=None):
    comps = _components(grid)
    frames = [cells for _, cells in comps if _is_frame(cells)]
    distractors = [cells for _, cells in comps if not _is_frame(cells)]
    msgs = []
    if not frames:
        msgs.append("no hollow frame component")
    if not distractors:
        msgs.append("no non-frame distractor component")
    if len({color for color, _ in comps}) != len(comps):
        msgs.append("component colors are not distinct")
    return msgs
