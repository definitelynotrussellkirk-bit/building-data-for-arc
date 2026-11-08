"""Generator for arc_puzzle_bank_21_more:hard_b07 — swap frame contents.

REAL rule (the "gallery pack" docstring was WRONG): find the hollow
rectangular FRAMES; extract each frame's interior content (crop-to-content);
keep the frame outlines but REDISTRIBUTE the contents in REVERSED frame order,
re-centering each moved content inside its new frame. Output is the same size
as the input.

The old generator drew scattered motifs with NO frames, so the rule found
nothing -> near-constant output (distinct=9). This builds K frames each with a
distinct interior content; the rule swaps the contents.

Combinatorial axes: grid size, frame count/sizes/positions, contents/colors.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "92074aefc590"
VERSION = "3.1.1"
TASK_ID = "92074aefc590"

SUMMARY = (
    "0-bg grid with K (2-3) hollow rectangular FRAMES in distinct border "
    "colors, each containing a small centered interior content (a 2-4 cell "
    "shape in a distinct content color, bbox <= 2x2 so it fits any frame). "
    "Rule: keep the frame outlines but redistribute the interior contents in "
    "REVERSED frame order, re-centering each. Frame count/sizes/positions, "
    "contents and colors all vary."
)

INVARIANTS = [
    "background is 0",
    "K hollow rectangular frames (distinct border colors), 4-conn isolated",
    "each frame holds one centered interior content of a distinct color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..20"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-bg colors present (frames + content)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_motifs", "single_motif", "all_same_color"):
        return errs
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"need >=2 distinct non-bg colors (frames + content), found {len(colors)}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


_CONTENTS = [
    [(0, 0), (0, 1)],                 # domino
    [(0, 0), (1, 0)],                 # v-domino
    [(0, 0), (0, 1), (1, 0)],         # L-tromino
    [(0, 0), (0, 1), (1, 1)],         # L-tromino
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)], # 2x2 square
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 14); K = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17); w = ctx.draw_int("grid_w", 15, 20)
        K = 3
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 13, 17)
        K = ctx.draw_int("n_frames", 2, 3)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        cols = rng.sample([c for c in range(1, 10)], 2 * K)
        frame_cols = cols[:K]; content_cols = cols[K:]
        # Random frame placement was correct in spirit but starved on small K=3
        # grids (12/1000 raised "could not realize frame-content layout"). A 2x2
        # slot layout keeps varied frame sizes/positions while guaranteeing the
        # one-cell moat _free() requires: quadrants are separated by the blank
        # middle row (h//2) and column (w//2). The rule finds frames wherever
        # they are, so quadrant placement preserves semantics.
        slots = [(0, 0), (0, 1), (1, 0), (1, 1)]
        rng.shuffle(slots)
        ok = True
        for i, (sr, sc) in enumerate(slots[:K]):
            r_start = 0 if sr == 0 else h // 2 + 1
            r_stop = h // 2 - 1 if sr == 0 else h - 1
            c_start = 0 if sc == 0 else w // 2 + 1
            c_stop = w // 2 - 1 if sc == 0 else w - 1
            slot_h = r_stop - r_start + 1
            slot_w = c_stop - c_start + 1
            if slot_h < 5 or slot_w < 5:
                ok = False; break
            fh = rng.randint(5, min(7, slot_h))
            fw = rng.randint(5, min(7, slot_w))
            r0 = rng.randint(r_start, r_stop - fh + 1)
            c0 = rng.randint(c_start, c_stop - fw + 1)
            if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                ok = False; break
            # outline
            for c in range(c0, c0 + fw):
                g[r0][c] = frame_cols[i]; g[r0 + fh - 1][c] = frame_cols[i]
            for r in range(r0, r0 + fh):
                g[r][c0] = frame_cols[i]; g[r][c0 + fw - 1] = frame_cols[i]
            # centered interior content (bbox <= 2x2, fits any interior)
            shape = rng.choice(_CONTENTS)
            ch = max(r for r, _ in shape) + 1; cw = max(c for _, c in shape) + 1
            ih = fh - 2; iw = fw - 2
            tr = r0 + 1 + (ih - ch) // 2; tc = c0 + 1 + (iw - cw) // 2
            for dr, dc in shape:
                g[tr + dr][tc + dc] = content_cols[i]
        if ok:
            return g
    raise ValueError("could not realize frame-content layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
