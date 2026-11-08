"""Generator for 4977f1fc4c50.

Rule: input is a dense periodic field containing one color whose cells form
exactly a one-cell-thick rectangular frame.  Output crops to that frame's bbox.

Combinatorial axes (8): grid_h/w, frame_h, frame_w, position_bias,
palette_kind, interior_phase, anchor_corner, asymmetry_force.
Degenerates: no_frame, two_frames, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "4977f1fc4c50"
VERSION = "2.1.0"  # defect-lint residual: field rebuilt as stripes+delimiter-rows —
# obj_count now brackets the canonical 142-198 (was 260-470 overshoot) and the
# modal color is a field color (canonical demo 3 is 8-dominant; was always 0).
TASK_ID = "4977f1fc4c50"
SUMMARY = (
    "Dense 24-30 square-ish field with many isolated/background texture cells "
    "and exactly one unique-color rectangular outline.  The frame color occurs "
    "only on the border, so the canonical rule can identify its bbox and crop "
    "the enclosed patch."
)

INVARIANTS = [
    "dense periodic field, not a sparse blank canvas",
    "exactly one color forms a perimeter-only rectangular frame, bbox >= 5x5",
    "the frame color occurs nowhere outside that rectangle border",
    "frame interior contains non-frame texture copied into the cropped output",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "two_frames", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 24..28", "valid": "20..30"},
    "grid_w":         {"type": "int", "default": "rng 24..28", "valid": "20..30"},
    "frame_h":        {"type": "int", "default": "rng 6..8", "valid": "5..9"},
    "frame_w":        {"type": "int", "default": "rng 6..8", "valid": "5..9"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "centered|corner|near_edge|scattered"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "warm|cool|broad|primary"},
    "interior_phase": {"type": "int", "default": "rng 0..6", "valid": "0..6"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "centered|corner|near_edge|scattered|no_frame|two_frames|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 22, 24
        f_lo, f_hi = 6, 7
    elif difficulty == "hard":
        h_lo, h_hi = 27, 30
        f_lo, f_hi = 7, 9
    else:
        h_lo, h_hi = 24, 28
        f_lo, f_hi = 6, 8

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 6, rng)
    frame_color = palette[0]
    field_palette = palette[1:]
    phase = int(overrides.get("interior_phase", ctx.draw_int("interior_phase", 0, 6)))
    g = _dense_periodic_field(h, w, field_palette, phase)

    fh = int(overrides.get("frame_h",
                           ctx.draw_int("frame_h", f_lo, min(f_hi, h - 4))))
    fw = int(overrides.get("frame_w",
                           ctx.draw_int("frame_w", f_lo, min(f_hi, w - 4))))
    fh = max(5, min(fh, h - 4))
    fw = max(5, min(fw, w - 4))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    rr, rc = _pick_frame_pos(bias, h, w, fh, fw, rng)
    draw_rect_outline(g, rr, rc, fh, fw, frame_color)
    return g


def _dense_periodic_field(h, w, colors, phase):
    """Canonical-regime field: column stripes + solid delimiter rows + mutation dots.

    Matches the demos' statistics (defect-lint calibrated): modal is a FIELD
    color (not 0) at ~0.35, obj_count ~110-225 across 22-30 sizes vs canonical
    142-198, long solid rows forming the big components. The old checkerboard
    overshot to 260-470 one-cell fragments with modal 0."""
    if not colors:
        colors = [1, 3, 8]
    k = len(colors)
    pr = 5 + (phase % 2)                 # delimiter-row period
    dom = colors[phase % k]              # dominant field color -> the grid's mode
    g = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            m = (c + phase) % 6
            if m == 2:
                v = 0                    # sparse zero columns, like the demos
            elif m in (0, 4):
                v = dom
            else:
                v = colors[(c * 2 + r // pr + phase) % k]
            # mutation dots split vertical runs into demo-like ~2-3 cell pieces
            if v != 0 and (r * 3 + c * 5 + phase) % 5 == 0:
                v = colors[(c + r + phase) % k]
            g[r][c] = v
    for r in range(pr - 1, h, pr):       # solid delimiter rows (the big objects)
        rc = colors[(phase + r // pr) % k]
        for c in range(w):
            g[r][c] = rc
    return g


def _pick_frame_pos(bias, h, w, fh, fw, rng):
    max_r = max(2, h - fh - 2)
    max_c = max(2, w - fw - 2)
    if bias == "centered":
        rr = max(2, (h - fh) // 2 + rng.randint(-2, 2))
        rc = max(2, (w - fw) // 2 + rng.randint(-2, 2))
    elif bias == "corner":
        rr = rng.choice([2, max_r])
        rc = rng.choice([2, max_c])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            rr = rng.choice([2, max_r])
            rc = rng.randint(2, max_c)
        else:
            rr = rng.randint(2, max_r)
            rc = rng.choice([2, max_c])
    else:
        rr = rng.randint(2, max_r)
        rc = rng.randint(2, max_c)
    rr = max(2, min(rr, max_r))
    rc = max(2, min(rc, max_c))
    return rr, rc


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9, 8]
    elif kind == "cool":
        pool = [1, 5, 7, 8, 2, 3]
    elif kind == "primary":
        pool = [1, 2, 3, 4, 8, 6]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _frame_info_for_color(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    if not cells:
        return None
    rs = [r for r, _c in cells]
    cs = [c for _r, c in cells]
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    bh, bw = r2 - r1 + 1, c2 - c1 + 1
    if bh < 3 or bw < 3:
        return None
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return (r1, c1, r2, c2) if set(cells) == border else None


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the unique dense-field rectangular-frame crop invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h * w < 400:
        errs.append(f"grid area {h*w} is too small for dense canonical regime")
    colors = sorted({v for row in grid for v in row})
    frame_infos = [(c, info) for c in colors if (info := _frame_info_for_color(grid, c))]
    if len(frame_infos) != 1:
        errs.append(f"expected exactly one rectangular frame color, found {len(frame_infos)}")
        return errs
    _color, (r1, c1, r2, c2) = frame_infos[0]
    fh, fw = r2 - r1 + 1, c2 - c1 + 1
    if fh < 5 or fw < 5:
        errs.append(f"frame bbox too small: {fh}x{fw}")
    interior = [grid[r][c] for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    if len(set(interior)) < 2:
        errs.append("frame interior lacks varied texture")
    nonzero_count = sum(1 for row in grid for v in row if v != 0)
    if nonzero_count < (h * w) // 3:
        errs.append("field is too sparse; expected dense noisy texture")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_frame":
        for _ in range(8):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice([1, 2, 3, 4])
        return g
    if name == "two_frames":
        draw_rect_outline(g, 1, 1, 5, 5, 2)
        draw_rect_outline(g, 8, 8, 5, 5, 3)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
