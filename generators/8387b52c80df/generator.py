"""Generator for v0_original:hard_02.

Rule: a hollow rectangular frame contains a single non-frame seed; fill
the frame's interior with the seed's color.

Combinatorial axes (8): grid_h/w, palette_kind, frame_color, seed_color,
seed_col, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_seed, multiple_seeds, no_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8387b52c80df"
VERSION = "2.0.0"  # distinct=32/dup-inputs40%/shape-locked: grid was FIXED 6x7 with a single fixed-position frame; only frame/seed colors + 1-of-3 seed col varied. Rule fills EVERY rect-frame interior (for/fold over all frames) and frames are per-color components. Now: random grid size, 1-3 separated frames of random size/position, seed at a random interior cell of each.
TASK_ID = "8387b52c80df"
SUMMARY = "Fill each hollow rectangular frame interior with its enclosed seed color. Grid size, frame count (1-3), frame sizes/positions, frame and seed colors, and seed positions all vary; frames are placed separated so each is its own component."

INVARIANTS = [
    "there is one hollow rectangular frame",
    "the frame contains exactly one non-frame nonzero seed color",
    "the frame border color is preserved",
    "the interior zeros adopt the seed color",
]

PALETTE_KINDS = ("default", "warm_frame", "cool_frame", "primary_frame")
DEGENERATE_TEXTURES = ("no_seed", "multiple_seeds", "no_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "frame_color":    {"type": "int", "default": "rng",
                       "valid": "1..4|6..8"},
    "seed_color":     {"type": "int", "default": "rng", "valid": "5..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "2..6", "valid": "2..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r0, c0, r1, c1):
    """True if the bbox plus a 1-cell margin is entirely background."""
    h, w = len(g), len(g[0])
    for r in range(r0 - 1, r1 + 2):
        for c in range(c0 - 1, c1 + 2):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return True


def _draw_frame(g, rng, r0, c0, r1, c1):
    fcolor = rng.choice([1, 2, 3, 4, 6, 7, 8])
    scolor = rng.choice([5, 6, 7, 8, 9])
    if scolor == fcolor:
        scolor = 9 if fcolor != 9 else 5
    for c in range(c0, c1 + 1):
        g[r0][c] = fcolor
        g[r1][c] = fcolor
    for r in range(r0, r1 + 1):
        g[r][c0] = fcolor
        g[r][c1] = fcolor
    # seed: one cell strictly inside, different color from the frame
    sr = rng.randint(r0 + 1, r1 - 1)
    sc = rng.randint(c0 + 1, c1 - 1)
    g[sr][sc] = scolor


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
        n_frames = ctx.draw_int("n_frames", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18); w = ctx.draw_int("grid_w", 12, 18)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 14); w = ctx.draw_int("grid_w", 8, 14)
        n_frames = ctx.draw_int("n_frames", 1, 3)
    rng = ctx.draw_rng("layout")
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        placed = 0
        for _ in range(300):
            if placed >= n_frames:
                break
            fh = rng.randint(3, min(7, h - 1))
            fw = rng.randint(3, min(7, w - 1))
            r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
            r1 = r0 + fh - 1; c1 = c0 + fw - 1
            if not _free(g, r0, c0, r1, c1):
                continue
            _draw_frame(g, rng, r0, c0, r1, c1)
            placed += 1
        if placed >= n_frames:
            return g
    # Extremely rare congestion fallback: draw deterministic separated frames.
    g = full_grid(h, w, 0)
    anchors = [
        (1, 1, min(5, h - 2), min(5, w - 2)),
        (1, max(1, w - 6), min(5, h - 2), w - 2),
        (max(1, h - 6), 1, h - 2, min(5, w - 2)),
    ]
    placed = 0
    for r0, c0, r1, c1 in anchors:
        if placed >= n_frames:
            break
        if r1 - r0 >= 2 and c1 - c0 >= 2 and _free(g, r0, c0, r1, c1):
            _draw_frame(g, rng, r0, c0, r1, c1)
            placed += 1
    if placed < n_frames:
        raise ValueError("could not place requested number of seed frames")
    return g


def _frame_bboxes(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    frames = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells); r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells); c1 = max(cc for _, cc in cells)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            border = {(rr, cc) for rr in range(r0, r1 + 1)
                      for cc in range(c0, c1 + 1)
                      if rr in (r0, r1) or cc in (c0, c1)}
            if set(cells) == border:
                frames.append((color, r0, c0, r1, c1))
    return frames


def self_check(grid, *, difficulty=None):
    problems = []
    frames = _frame_bboxes(grid)
    min_expected = 2 if difficulty == "hard" else 1
    if len(frames) < min_expected:
        problems.append(f"expected at least {min_expected} frame(s), found {len(frames)}")
    for color, r0, c0, r1, c1 in frames:
        seeds = set()
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                v = grid[r][c]
                if v not in (0, color):
                    seeds.add(v)
        if len(seeds) != 1:
            problems.append(f"frame {(r0, c0, r1, c1)} has {len(seeds)} seed colors")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 7, 0)
    frame_color = 3
    if name == "no_seed":
        # frame but no seed inside — interior fill color undefined
        for c in range(1, 5):
            g[1][c] = frame_color
            g[4][c] = frame_color
        for r in range(1, 5):
            g[r][1] = frame_color
            g[r][4] = frame_color
        return g
    if name == "multiple_seeds":
        # frame with 2 different seeds — fill color ambiguous
        for c in range(1, 5):
            g[1][c] = frame_color
            g[4][c] = frame_color
        for r in range(1, 5):
            g[r][1] = frame_color
            g[r][4] = frame_color
        g[2][2] = 5
        g[3][3] = 7
        return g
    if name == "no_frame":
        # seed without enclosing frame — rule has no region to fill
        g[2][3] = 5
        return g
    return g
