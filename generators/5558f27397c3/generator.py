"""Generator for arc_puzzle_bank_seventh_21_bundle:hard_46_local_symmetry_completion_by_frame_key.

Rule: 2 hollow color-5 frames; each has a small key marker above its top-left
and partial pattern inside. Rule completes symmetry inside each frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no color-5 frames → rule has no chambers);
no_keys (frames present but no key markers above → rule has no
symmetry-axis hint); no_partial (frames + keys but interiors empty
→ rule has nothing to complete).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5558f27397c3"
# 2.2.0: interior cells were scattered anywhere, so a frame's partial pattern
# was sometimes ALREADY symmetric across its key axis -> mirroring added nothing
# -> identity (~5/24 seeds). 2.2.0 places each frame's cells only in the SOURCE
# half (left half for key 6, top half for key 7), so the mirror always fills the
# empty other half -> the completion is always visible (non-identity).
VERSION = "2.2.0"  # (2.1.0 raised easy w floor 17->18: two 8-wide frames collided at w=17)
TASK_ID = "5558f27397c3"

SUMMARY = (
    "0-bg grid (h ∈ 12-20, w ∈ 17-26, "
    "by difficulty) with: TWO HOLLOW "
    "COLOR-5 RECTANGULAR FRAMES each "
    "8×8, anchored at FIXED positions "
    "(r0=2, c0=2) and (r0=2, c0=w//2+1) "
    "— each frame's interior is "
    "6×6. FOR EACH FRAME: (a) ONE KEY "
    "MARKER one row ABOVE the frame's "
    "TOP-LEFT CORNER (at row r0-1, "
    "col c0+1), value ∈ {6, 7} chosen "
    "independently per frame; (b) "
    "2-4 SPARSE INTERIOR CELLS — "
    "placed at random non-overlapping "
    "interior positions (rows "
    "r0+1..r0+6, cols c0+1..c0+6), "
    "each painted in ONE non-{0, 5} "
    "color drawn per-frame from "
    "{2,3,4,6,7,8,9}. Rule (FOR EACH "
    "FRAME, USE ITS KEY TO PICK A "
    "MIRROR AXIS AND COMPLETE THE "
    "INTERIOR PATTERN BY MIRRORING "
    "THE CELLS ACROSS THAT AXIS): "
    "For EACH color-5 frame: READ "
    "its KEY (above top-left). IF "
    "KEY = 6: MIRROR each interior "
    "cell LEFT↔RIGHT across the "
    "frame's vertical center axis "
    "(c -> c0 + (c0 + fw - 1 - c)). "
    "IF KEY = 7: MIRROR each "
    "interior cell TOP↔BOTTOM "
    "across the horizontal center "
    "axis. The mirrored cell is "
    "painted with the SAME color "
    "as the source. Original "
    "interior cells preserved. "
    "Net: each frame's partial "
    "pattern is completed into a "
    "symmetric pattern across the "
    "axis selected by its key."
)

# Rivals: 'output is input' refuted by any demo where interior gains
# new cells. 'mirror both axes' refuted by ≥1 demo with key=6 (only
# LR), and ≥1 with key=7 (only UD). 'mirror the whole grid' refuted
# by any demo (only interiors change). 'use key color for mirror'
# refuted by any demo (mirror uses interior cell colors). 3 demos
# with mixed keys cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 hollow color-5 rectangular frames",
    "each frame has a small key color marker just above and a partial pattern inside",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_keys", "no_partial")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 14..16", "valid": "12..20"},
    "grid_w":            {"type": "int", "default": "rng 18..22", "valid": "16..26"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "two_frames_with_keys_and_partials",
                          "valid": "two_frames_with_keys_and_partials"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_frames|no_keys|no_partial"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 14)
        # Frame 1 occupies cols 2..9; frame 2 anchors at w//2+1. At w=17 that
        # lands on col 9 — colliding with frame 1's right wall — so _free rejects
        # it forever ("could not realize layout"). Two 8-wide frames anchored at
        # col 2 need w ≥ 18; but two frames whose walls TOUCH (frame2 left col ==
        # frame1 right col + 1) merge into one non-rect color-5 component that the
        # rule skips -> identity. We now force a >=1-col GAP (frame2 at col >= 11),
        # which needs w >= 19.
        w = ctx.draw_int("grid_w", 19, 20)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20)
        w = ctx.draw_int("grid_w", 21, 26)
    else:
        h = ctx.draw_int("grid_h", 14, 17)
        w = ctx.draw_int("grid_w", 19, 22)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        # frame1 spans cols 2..9; place frame2 at col >= 11 so a blank col (10)
        # separates them and they stay TWO distinct rect frames.
        positions = [(2, 2), (2, max(w // 2 + 1, 11))]
        placed = 0
        for r0, c0 in positions:
            fh, fw = 8, 8
            if r0 + fh > h or c0 + fw > w: continue
            if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1): continue
            for c in range(c0, c0 + fw):
                g[r0][c] = 5
                g[r0 + fh - 1][c] = 5
            for r in range(r0, r0 + fh):
                g[r][c0] = 5
                g[r][c0 + fw - 1] = 5
            key = rng.choice([6, 7])
            if r0 - 1 >= 0:
                g[r0 - 1][c0 + 1] = key
            inner_color = rng.choice([2, 3, 4, 6, 7, 8, 9])
            n_cells = rng.randint(2, 4)
            # place ONLY in the source half so the key-axis mirror fills the
            # (empty) other half -> the symmetry completion is always non-trivial.
            if key == 6:                       # LR mirror: source = left columns
                ir_lo, ir_hi = r0 + 1, r0 + fh - 2
                ic_lo, ic_hi = c0 + 1, c0 + fw // 2 - 1
            else:                              # UD mirror: source = top rows
                ir_lo, ir_hi = r0 + 1, r0 + fh // 2 - 1
                ic_lo, ic_hi = c0 + 1, c0 + fw - 2
            for _ in range(n_cells):
                for _t in range(20):
                    ir = rng.randint(ir_lo, ir_hi)
                    ic = rng.randint(ic_lo, ic_hi)
                    if g[ir][ic] == 0:
                        g[ir][ic] = inner_color
                        break
            placed += 1
        if placed == 2:
            return g
    raise ValueError("could not realize layout")


def _color5_frames(grid):
    """Bboxes of 4-connected color-5 components that are hollow rectangle
    frames (cells == bbox border)."""
    h = len(grid); w = len(grid[0])
    seen = [[False] * w for _ in range(h)]
    frames = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or seen[r][c]:
                continue
            stack = [(r, c)]; seen[r][c] = True; cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 5):
                        seen[nr][nc] = True; stack.append((nr, nc))
            rs = [p[0] for p in cells]; cs = [p[1] for p in cells]
            r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            border = {(rr, cc) for rr in range(r0, r1 + 1) for cc in range(c0, c1 + 1)
                      if rr in (r0, r1) or cc in (c0, c1)}
            if set(cells) == border:
                frames.append((r0, c0, r1, c1))
    return frames


def _apply_rule(grid):
    out = [row[:] for row in grid]
    for r0, c0, r1, c1 in _color5_frames(grid):
        ir0, ic0, ir1, ic1 = r0 + 1, c0 + 1, r1 - 1, c1 - 1
        key = None
        if r0 - 1 >= 0:
            for c in range(c0, c1 + 1):
                if grid[r0 - 1][c] in (6, 7):
                    key = grid[r0 - 1][c]; break
        if key is None:
            continue
        for r in range(ir0, ir1 + 1):
            for c in range(ic0, ic1 + 1):
                v = grid[r][c]
                if v == 0:
                    continue
                if key == 6:
                    out[r][ic0 + ic1 - c] = v
                else:
                    out[ir0 + ir1 - r][c] = v
    return out


def _find_hollow_five_frames(grid):
    """Return top-left/bottom-right boxes for every exact 8x8 hollow 5-frame.
    Frames may be side-adjacent in this generator, so connected-components of
    color 5 are too coarse: two valid frames can form one connected component
    through adjacent border columns."""
    h, w = len(grid), len(grid[0])
    out = []
    for r0 in range(0, h - 7):
        r1 = r0 + 7
        for c0 in range(0, w - 7):
            c1 = c0 + 7
            ok = True
            for c in range(c0, c1 + 1):
                if grid[r0][c] != 5 or grid[r1][c] != 5:
                    ok = False; break
            if not ok:
                continue
            for r in range(r0, r1 + 1):
                if grid[r][c0] != 5 or grid[r][c1] != 5:
                    ok = False; break
            if not ok:
                continue
            if any(grid[r][c] == 5 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
                continue
            out.append((r0, r1, c0, c1))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Two hollow 8x8 color-5 frames, each with a 6/7 key above and a non-empty
    non-5 interior partial that changes under the rule (non-identity)."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    frames = _find_hollow_five_frames(grid)
    if len(frames) != 2:
        errs.append(f"expected exactly 2 hollow 8x8 color-5 frames, found {len(frames)}")
        return errs
    for r0, r1, c0, c1 in frames:
        key = grid[r0 - 1][c0 + 1] if r0 - 1 >= 0 else 0
        if key not in (6, 7):
            errs.append(f"frame {(r0, c0)} key should be 6 or 7 at {(r0-1, c0+1)}, found {key}")
        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        partial = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] not in (0, 5)]
        if not (2 <= len(partial) <= 4):
            errs.append(f"frame {(r0, c0)} expected 2-4 interior partial cells, found {len(partial)}")
    if not errs and _apply_rule(grid) == grid:
        errs.append("symmetry completion leaves the grid unchanged (identity demo)")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 15, 20
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No color-5 frames — rule has no chambers.
        g[3][3] = 4; g[5][5] = 4
        g[3][12] = 6; g[5][14] = 6
        return g
    if name == "no_keys":
        # Frames + interior but no key markers above.
        for r0, c0 in [(2, 2), (2, 11)]:
            for c in range(c0, c0 + 8):
                g[r0][c] = 5; g[r0 + 7][c] = 5
            for r in range(r0, r0 + 8):
                g[r][c0] = 5; g[r][c0 + 7] = 5
            g[r0 + 2][c0 + 2] = 4; g[r0 + 4][c0 + 5] = 4
        return g
    if name == "no_partial":
        # Frames + keys but interiors empty — nothing to complete.
        for r0, c0 in [(2, 2), (2, 11)]:
            for c in range(c0, c0 + 8):
                g[r0][c] = 5; g[r0 + 7][c] = 5
            for r in range(r0, r0 + 8):
                g[r][c0] = 5; g[r][c0 + 7] = 5
            g[r0 - 1][c0 + 1] = 4
        return g
    return g
