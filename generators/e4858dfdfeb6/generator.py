"""Generator for 2e65ae53 -- complete lattice slots across templates.

Rule: frame-color is the most common non-0 color. Each frame-color object
(size > 4) is a lattice whose full-frame rows/cols are grid lines; the gaps
between them are slots. For each slot index (ri,ci), gather the non-frame
swatch values at that slot across all lattices; the mode color fills every
empty (ri,ci) slot in every lattice.

This generator draws N identical lattices (an R x C array of single-cell
slots) and places each slot's color in a random nonempty subset of lattices,
leaving the rest blank for the rule to complete.

Combinatorial axes: lattice dims, template count, frame/swatch colors, which
templates carry each swatch, positions.
Degenerates: no_templates, no_swatch, full_grid.

NOTE: the output completes the lattices, so OUTPUTS are bounded by the
slot-color arrays; distinct INPUTS are large.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4858dfdfeb6"
VERSION = "2.1.3"  # larger sparse lattices: match canonical scale without overfragmenting slots
TASK_ID = "e4858dfdfeb6"
SUMMARY = (
    "0-bg grid (size varies) with N identical frame-color lattices (an R x C "
    "array of single-cell slots). Each slot's color appears in some lattices; "
    "the rule completes every empty matching slot with that color. The "
    "lattice dims, template count, colors and positions vary freely (was a "
    "fixed 8x14 setup, ~38 distinct)."
)

INVARIANTS = [
    "frame-color (most common non-0) forms identical lattices, size > 4",
    "each slot index carries one swatch color in a nonempty subset of lattices",
    "the output fills every empty matching slot with that slot's color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_templates", "no_swatch", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_COLORS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

AXES = {
    "slot_rows":      {"type": "int", "default": "varies", "valid": "4..8"},
    "slot_cols":      {"type": "int", "default": "varies", "valid": "3..6"},
    "n_templates":    {"type": "int", "default": "varies", "valid": "2..3"},
    "frame_color":    {"type": "color", "default": "rng", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "active_slots":   {"type": "int", "default": "varies", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "side_by_side", "valid": "side_by_side"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_templates|no_swatch|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify lattice panels and at least one fillable blank slot."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h = len(grid)
    w = len(grid[0])
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        return ["normal sample has no nonzero lattice frame cells"]
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    frame, _ = counts.most_common(1)[0]
    frame_rows = [r for r in range(h) if any(grid[r][c] == frame for c in range(w))]
    frame_cols = [c for c in range(w) if any(grid[r][c] == frame for r in range(h))]
    if not frame_rows:
        errors.append("no frame rows found")
        return errors
    row0, row1 = min(frame_rows), max(frame_rows)
    panel_h = row1 - row0 + 1
    if frame_rows != list(range(row0, row1 + 1)) or panel_h % 2 != 1:
        errors.append(f"lattice panel rows must form one odd-height band, got rows={frame_rows[:8]}...")
        return errors
    runs = []
    i = 0
    while i < len(frame_cols):
        start = frame_cols[i]
        end = start
        i += 1
        while i < len(frame_cols) and frame_cols[i] == end + 1:
            end = frame_cols[i]
            i += 1
        runs.append((start, end))
    if len(runs) < 2:
        errors.append("expected at least two separated lattice panels")
        return errors
    widths = {end - start + 1 for start, end in runs}
    if len(widths) != 1 or next(iter(widths)) % 2 != 1:
        errors.append(f"lattice panels must share odd widths, got runs={runs}")
        return errors
    panel_w = next(iter(widths))
    # Even local rows/cols are the frame grid-lines in every panel.
    for start, end in runs:
        for r in range(row0, row1 + 1):
            for c in range(start, end + 1):
                if ((r - row0) % 2 == 0 or (c - start) % 2 == 0) and grid[r][c] != frame:
                    errors.append("frame-color cells do not form complete lattice grid-lines")
                    return errors
    fillable = False
    for r in range(row0 + 1, row1 + 1, 2):
        for dc in range(1, panel_w, 2):
            vals = [grid[r][start + dc] for start, _end in runs]
            nz = [v for v in vals if v != 0]
            if nz and len(set(nz)) == 1 and any(v == 0 for v in vals):
                fillable = True
    if not fillable:
        errors.append("no slot has a swatch in some panels and a blank in another; completion branch hidden")
    return errors


def _lattice(R, C, frame):
    """(2R+1) x (2C+1) lattice: frame on even rows/cols, slots at (odd,odd)."""
    H = 2 * R + 1; W = 2 * C + 1
    panel = [[0] * W for _ in range(H)]
    for r in range(H):
        for c in range(W):
            if r % 2 == 0 or c % 2 == 0:
                panel[r][c] = frame
    return panel


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        Rr, Cr, nr, ar = (4, 5), (3, 4), (2, 2), (3, 5)
    elif difficulty == "hard":
        Rr, Cr, nr, ar = (6, 8), (4, 6), (2, 2), (5, 8)
    else:
        Rr, Cr, nr, ar = (5, 7), (3, 5), (2, 2), (4, 7)

    for _attempt in range(60):
        R = rng.randint(*Rr); C = rng.randint(*Cr)
        n = rng.randint(*nr)
        # clamp to the 30x30 ARC canvas: H=2R+1, total width = n*(2C+1)+(n-1)
        if (2 * R + 1) > 30 or n * (2 * C + 1) + (n - 1) > 30:
            continue
        frame = int(overrides["frame_color"]) if "frame_color" in overrides \
            else rng.choice(_COLORS)
        swcolors = [col for col in _COLORS if col != frame]

        # One color per active slot index.  Keep the lattice sparse: the
        # canonical examples have large frames with a modest number of swatches,
        # not a nearly-filled checkerboard of dozens of separate slot objects.
        all_slots = [(ri, ci) for ri in range(R) for ci in range(C)]
        rng.shuffle(all_slots)
        n_active = int(overrides.get("active_slots", ctx.draw_int("active_slots", *ar)))
        n_active = max(1, min(n_active, len(all_slots)))
        slot_color = {slot: rng.choice(swcolors) for slot in all_slots[:n_active]}

        if not slot_color:
            continue

        panels = [_lattice(R, C, frame) for _ in range(n)]
        # Place each slot color in a random nonempty subset of templates.  Force
        # the first colored slot to be absent from at least one template so the
        # canonical completion rule has visible work to do (no identity demos).
        made_fillable = False
        for (ri, ci), col in slot_color.items():
            hi = n - 1 if not made_fillable else n
            subset = rng.sample(range(n), rng.randint(1, hi))
            if len(subset) < n:
                made_fillable = True
            for ti in subset:
                panels[ti][2 * ri + 1][2 * ci + 1] = col

        # Assemble side by side on a mostly-zero canvas.  The canonical
        # examples use large zero backgrounds around the lattices; keeping the
        # tight panel crop made the frame color modal, which in turn made every
        # blank slot look like a separate object to modal-background metrics.
        H = 2 * R + 1; W = 2 * C + 1
        tight_total = n * W + (n - 1)
        canvas_h = min(30, max(22, H + 2))
        canvas_w = min(30, max(22, tight_total + 2))
        if H > canvas_h or tight_total > canvas_w:
            continue
        g = full_grid(canvas_h, canvas_w, 0)
        row0 = rng.randint(0, canvas_h - H)
        col0 = rng.randint(0, canvas_w - tight_total)
        for panel in panels:
            for r in range(H):
                for c in range(W):
                    g[row0 + r][col0 + c] = panel[r][c]
            col0 += W + 1
        return g

    return _draw_from_degenerate("no_swatch", rng)   # fallback (rare)


def _draw_from_degenerate(name, rng):
    R = C = 2; frame = 1
    panels = [_lattice(R, C, frame) for _ in range(2)]
    if name == "no_swatch":
        pass
    elif name != "no_templates":
        panels[0][1][1] = 3   # one swatch
    H = 2 * R + 1; W = 2 * C + 1
    total = 2 * W + 1
    g = full_grid(H, total, 0)
    if name == "no_templates":
        g[1][1] = 3
        return g
    if name == "full_grid":
        return full_grid(H, total, 1)
    col0 = 0
    for panel in panels:
        for r in range(H):
            for c in range(W):
                g[r][col0 + c] = panel[r][c]
        col0 += W + 1
    return g
