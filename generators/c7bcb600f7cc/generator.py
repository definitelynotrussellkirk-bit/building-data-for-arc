"""Generator for arc_additional_puzzle_bank_volume13:H86.

Rule: color-4 rectangular frames sorted by area descending. A control cell
(value 1 or 2) selects outer = frames[control-1] and inner = frames[control].
Fill the cells that are 0, strictly inside the outer frame, and not inside
the inner frame's bbox -> 8 (the ring between the two).

This generator draws K nested concentric color-4 frames plus a control
cell (1 or 2, with K > control).

Combinatorial axes: grid size, the nested frames, and the control value.
Degenerates: no_frames, no_control, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "c7bcb600f7cc"
VERSION = "2.0.1"  # diversity: K nested color-4 frames + control-1/2 ring select (was fixed ~26)
TASK_ID = "c7bcb600f7cc"
SUMMARY = (
    "0-bg grid (size varies) with K (3-4) nested concentric color-4 frames "
    "and a control cell (1 or 2). Rule: outer = frames[control-1], inner = "
    "frames[control]; fill the ring between them (strictly inside outer, not "
    "inside inner) with 8. The grid size, frames and control value vary "
    "freely (was a fixed setup, ~26 distinct)."
)

INVARIANTS = [
    "K nested concentric color-4 frames with distinct areas",
    "a control cell (1 or 2) selects frames[control-1] (outer) and frames[control] (inner)",
    "the output fills the ring between outer and inner with 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_control", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "3..4"},
    "control":        {"type": "int", "default": "rng {1,2}", "valid": "1|2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "nested_plus_control",
                       "valid": "nested_plus_control"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_control|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        kr, cr = (3, 3), (3, 4)
    elif difficulty == "hard":
        kr, cr = (3, 4), (3, 6)
    else:
        kr, cr = (3, 4), (3, 5)

    for _attempt in range(40):
        K = rng.randint(*kr)
        control = rng.randint(1, min(2, K - 1))   # control value is 1 or 2; frames[control] must exist
        ih = rng.randint(*cr); iw = rng.randint(*cr)
        boxes = [(0, 0, ih - 1, iw - 1)]
        for _ in range(K - 1):
            r1, c1, r2, c2 = boxes[-1]
            mt = rng.randint(2, 3); ml = rng.randint(2, 3)
            mb = rng.randint(2, 3); mr = rng.randint(2, 3)
            boxes.append((r1 - mt, c1 - ml, r2 + mb, c2 + mr))
        or1, oc1 = boxes[-1][0], boxes[-1][1]
        boxes = [(r1 - or1, c1 - oc1, r2 - or1, c2 - oc1) for (r1, c1, r2, c2) in boxes]
        oh = boxes[-1][2] + 1; ow = boxes[-1][3] + 1

        h = rng.randint(oh + 3, oh + 7); w = rng.randint(ow + 3, ow + 7)
        if h > 30 or w > 30:
            continue
        top = rng.randint(1, h - oh - 1); left = rng.randint(1, w - ow - 1)

        g = full_grid(h, w, 0)
        for (r1, c1, r2, c2) in boxes:
            draw_frame(g, top + r1, left + c1, top + r2, left + c2, 4)

        # control cell (1 or 2) outside the frames
        outer = (top + boxes[-1][0], left + boxes[-1][1], top + boxes[-1][2], left + boxes[-1][3])
        free = [(r, c) for r in range(h) for c in range(w)
                if not (outer[0] - 1 <= r <= outer[2] + 1 and outer[1] - 1 <= c <= outer[3] + 1)]
        if not free:
            continue
        cr_, cc_ = rng.choice(free)
        g[cr_][cc_] = control
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid must have color-4 frame cells and a control cell of value 1 or 2."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if not fours:
        msgs.append("no color-4 frame cells found")
    controls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2)]
    if not controls:
        msgs.append("no control cell (value 1 or 2) found")
    return msgs


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    draw_frame(g, 1, 1, 13, 13, 4)
    draw_frame(g, 3, 3, 11, 11, 4)
    draw_frame(g, 5, 5, 9, 9, 4)
    g[0][0] = 1
    if name == "no_frames":
        return full_grid(15, 15, 0)
    if name == "no_control":
        g[0][0] = 0
        return g
    if name == "full_grid":
        return full_grid(15, 15, 4)
    return g


def _color4_components(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != 4:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 4:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out

def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))

def _is_outline(cells):
    cellset = set(cells)
    r1, c1, r2, c2 = _bbox(cells)
    outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
               if r in (r1, r2) or c in (c1, c2)}
    return cellset == outline

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal-path invariant: one control cell plus at least three nested color-4 frames."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    bad = sorted({v for row in grid for v in row if v not in (0, 1, 2, 4)})
    if bad:
        errors.append(f"unexpected colors {bad}")
    control = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2)]
    if len(control) != 1:
        errors.append(f"found {len(control)} control cells")
    frames = [cells for cells in _color4_components(grid) if _is_outline(cells)]
    if len(frames) < 3:
        errors.append(f"only {len(frames)} color-4 frames")
    areas = []
    for cells in frames:
        r1, c1, r2, c2 = _bbox(cells)
        areas.append((r2 - r1 + 1) * (c2 - c1 + 1))
    if len(set(areas)) != len(areas):
        errors.append("frame bbox areas are not distinct")
    frames = sorted(frames, key=lambda cells: (_bbox(cells)[2] - _bbox(cells)[0] + 1) * (_bbox(cells)[3] - _bbox(cells)[1] + 1))
    for inner, outer in zip(frames, frames[1:]):
        ir1, ic1, ir2, ic2 = _bbox(inner)
        or1, oc1, or2, oc2 = _bbox(outer)
        if not (or1 < ir1 and oc1 < ic1 and ir2 < or2 and ic2 < oc2):
            errors.append("frames are not strictly nested")
            break
    return errors
