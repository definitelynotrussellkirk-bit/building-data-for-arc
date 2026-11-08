"""Generator for arc_puzzle_bank_21_set22_bundle:hard_p06 — frames + motifs by symmetry class.

Rule: 2-3 hollow frames in distinct colors plus 2-3 multi-cell motifs in
matching colors. Each motif's symmetry class (LR-mirror / UD-mirror / both /
none) is matched to the frame's color, and the motif is centered in the
frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no hollow frames → rule has no destinations);
no_motifs (frames but no motifs → rule has nothing to center);
color_no_match (each frame color has no matching motif color elsewhere
→ rule's pair lookup returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "9bf865d6d39c"
VERSION = "2.0.1"
TASK_ID = "9bf865d6d39c"

SUMMARY = (
    "Grid (h~11-13, w~16-18) with: (a) 2-3 hollow "
    "rectangular FRAMES (5×5, 5×6, or 6×5) in distinct "
    "non-{0,5,8} colors, isolated; (b) 2-3 small 4-conn "
    "MOTIFS (3-5 cells) in the SAME distinct colors as "
    "the frames (one motif per frame color), placed "
    "elsewhere. Rule: detect frames and motifs. For each "
    "color, find its frame and its motif. Move/center the "
    "motif INTO its matching frame (paint motif cells at "
    "the centered position inside the frame's interior). "
    "Empty motif's original position back to bg."
)

INVARIANTS = [
    "background is 0",
    "2-3 hollow rectangular frames in distinct colors",
    "2-3 multi-cell motifs in distinct colors (one per frame color)",
    "no other non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_motifs", "color_no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 16..18", "valid": "14..20"},
    "n_pairs":           {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "frames_with_matching_motifs",
                          "valid": "frames_with_matching_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 16, 17)
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 17, 18)
        n_pairs = ctx.draw_int("n_pairs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 16, 18)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 6, 7, 9], n_pairs)
        ok = True
        for color in colors:
            fh, fw = rng.choice([(5, 5), (5, 6), (6, 5)])
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize set22 p06 layout")


def _draw_from_degenerate(name, rng):
    h, w = 12, 17
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No frames — rule has no destinations.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[3 + dr][10 + dc] = 6
        return g
    if name == "no_motifs":
        # Frames but no motifs.
        draw_frame(g, 1, 1, 5, 5, 4)
        draw_frame(g, 1, 9, 5, 14, 6)
        return g
    if name == "color_no_match":
        # Frames in colors {4, 6} but motifs in colors {7, 9} — no match.
        draw_frame(g, 1, 1, 5, 5, 4)
        draw_frame(g, 1, 9, 5, 14, 6)
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[8 + dr][2 + dc] = 7
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[8 + dr][10 + dc] = 9
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0; >=2 distinct nonzero colors; at least one 4-conn component is a hollow rectangular frame."""
    msgs = []
    h, w = len(grid), len(grid[0])
    colors_used = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors_used) < 2:
        msgs.append(f"expected >=2 distinct nonzero colors, got {len(colors_used)}")
        return msgs
    # Find all 4-connected components and check if any is a perfect rectangular perimeter
    frame_found = False
    seen = set()
    for r0 in range(h):
        for c0 in range(w):
            v = grid[r0][c0]
            if (r0, c0) not in seen and v != 0:
                stack = [(r0, c0)]; seen.add((r0, c0)); cells = [(r0, c0)]
                while stack:
                    r, c = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == v:
                            seen.add((nr, nc)); stack.append((nr, nc)); cells.append((nr, nc))
                if len(cells) < 8:
                    continue
                rs = [r for r, c in cells]; cs = [c for r, c in cells]
                r1, r2 = min(rs), max(rs); c1, c2 = min(cs), max(cs)
                if r2 - r1 < 2 or c2 - c1 < 2:
                    continue
                # A hollow rectangular frame: all cells are on the perimeter of their bbox
                perim = set()
                for r in range(r1, r2 + 1):
                    perim.add((r, c1)); perim.add((r, c2))
                for c in range(c1, c2 + 1):
                    perim.add((r1, c)); perim.add((r2, c))
                if set(cells) == perim:
                    frame_found = True
                    break
        if frame_found:
            break
    if not frame_found:
        msgs.append("no hollow rectangular frame found (expected >=1 frame-like 4-conn component)")
    return msgs
