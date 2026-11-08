"""Generator for arc_additional_puzzle_bank_volume3:H17 — Fill 5-frame interior with dominant color.

Rule: each 5-frame's interior is filled with the dominant non-5 color
inside. (Largest object's color wins.)

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, monochrome_interior, no_dominant.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "5d439359e290"
VERSION = "1.2.0"
TASK_ID = "5d439359e290"
SUMMARY = "2 5-frames, each ≥4×4 with 2 distinct non-5 colors inside (one majority)."

INVARIANTS = [
    "2 separate 5-frames, each ≥4×4",
    "each frame's interior contains 2 different non-5 colors",
    "one color has more cells than the other (dominant)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "monochrome_interior", "no_dominant")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "two_separated_frames",
                       "valid": "two_separated_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 12, 14)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    placed: list[tuple[int, int, int, int]] = []

    def overlaps(box):
        r0, c0, fh, fw = box
        r1, c1 = r0 + fh - 1, c0 + fw - 1
        for pr0, pc0, pfh, pfw in placed:
            pr1, pc1 = pr0 + pfh - 1, pc0 + pfw - 1
            # Require a one-cell moat so the two color-5 frames remain two
            # separate objects.  The old predicate compared only top-left
            # positions and rejected many perfectly valid side-by-side frames,
            # frequently leaving a one-frame episode.
            if not (r1 + 1 < pr0 or pr1 + 1 < r0 or c1 + 1 < pc0 or pc1 + 1 < c0):
                return True
        return False

    def add_frame(r0, c0, fh, fw):
        draw_rect_outline(g, r0, c0, fh, fw, 5)
        # Fill interior with exactly two colors, with a strict majority.  A
        # 4x4 frame has a 2x2 interior; the previous n-randint(1,2) formula
        # could split that 2/2 and hide the dominant-color rule.
        major, minor = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 2)
        interior_cells = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
                          for c in range(c0 + 1, c0 + fw - 1)]
        n = len(interior_cells)
        n_minor = rng.randint(1, max(1, (n - 1) // 2))
        rng.shuffle(interior_cells)
        for r, c in interior_cells[:-n_minor]:
            g[r][c] = major
        for r, c in interior_cells[-n_minor:]:
            g[r][c] = minor

    for _ in range(160):
        if len(placed) == 2:
            break
        fh = rng.randint(4, min(5, h - 2)); fw = rng.randint(4, min(5, w - 2))
        r0 = rng.randint(1, h - fh - 1); c0 = rng.randint(1, w - fw - 1)
        box = (r0, c0, fh, fw)
        if overlaps(box):
            continue
        placed.append(box)
        add_frame(r0, c0, fh, fw)
    if len(placed) < 2:
        # Fail closed into a known-valid two-frame layout rather than silently
        # emitting one frame when the random placer gets unlucky on small grids.
        g = full_grid(h, w, 0)
        fh = min(4, h - 2); fw = min(4, max(4, (w - 3) // 2))
        for r0, c0 in ((1, 1), (1, w - fw - 1)):
            add_frame(r0, c0, fh, fw)
    return g


def _frame_boxes(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            todo = [(r, c)]; seen.add((r, c)); cells = []
            while todo:
                rr, cc = todo.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 5:
                        seen.add((nr, nc)); todo.append((nr, nc))
            rs = [rr for rr, _ in cells]; cs = [cc for _, cc in cells]
            r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
            want = {(rr, cc) for rr in range(r0, r1 + 1) for cc in range(c0, c1 + 1)
                    if rr in (r0, r1) or cc in (c0, c1)}
            if set(cells) == want:
                boxes.append((r0, c0, r1, c1))
    return boxes


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    frames = _frame_boxes(grid)
    if len(frames) != 2:
        errors.append(f"expected exactly two complete color-5 frames, got {len(frames)}")
    for r0, c0, r1, c1 in frames:
        if r1 - r0 + 1 < 4 or c1 - c0 + 1 < 4:
            errors.append("each frame must be at least 4x4")
        vals = [grid[r][c] for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        if any(v in (0, 5) for v in vals):
            errors.append("frame interiors must be fully filled with non-{0,5} colors")
            continue
        counts = {v: vals.count(v) for v in set(vals)}
        if len(counts) < 2:
            errors.append("each frame interior must contain at least two colors")
        if counts and max(counts.values()) * 2 <= len(vals):
            errors.append("each frame interior must have a strict dominant color")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No 5-frames present — rule has no interiors to fill.
        g[2][3] = 4; g[5][8] = 6
        return g
    if name == "monochrome_interior":
        # Interior already a single color — dominant is trivial, rule is no-op.
        draw_rect_outline(g, 1, 1, 4, 4, 5)
        for r in range(2, 4):
            for c in range(2, 4): g[r][c] = 4
        return g
    if name == "no_dominant":
        # Interior has equal counts — no clear dominant color.
        draw_rect_outline(g, 1, 1, 4, 4, 5)
        g[2][2] = 4; g[2][3] = 6
        g[3][2] = 4; g[3][3] = 6
        return g
    return g
