"""Generator for f34f99f28c2d — rotate template by control, stamp at anchor.

Rule: find first cell with value in {6, 7, 8, 9} (the control). rot_count
= control - 6. Find the unique color-2 component (template). Find the
unique color-1 cell (anchor). Normalize template's cells, rotate cw
rot_count times. Paint the rotated cells offset by anchor onto a copy
of the input in color 4.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f34f99f28c2d"
VERSION = "2.1.1"  # add executable self_check; control now avoids the stamp footprint (was: stamp could overwrite control -> control vanished, off-canonical)
TASK_ID = "f34f99f28c2d"
SUMMARY = (
    "0-bg grid with exactly: (a) ONE control cell in {6, 7, 8, 9} at "
    "some scattered position; (b) ONE color-2 template (4-connected "
    "blob of 3-5 cells); (c) ONE color-1 anchor cell at some position. "
    "Layout is randomized: template, control, and anchor are placed at "
    "varied positions with 1-cell buffer between them. Rule: find "
    "control → rot_count = control - 6. Find template, normalize its "
    "cells, rotate 90° CW rot_count times. Paint the rotated cells at "
    "offset (anchor) in color 4 onto a copy of the input. Stamps must "
    "fit within grid bounds."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one cell with value in {6, 7, 8, 9} (the control)",
    "exactly one 4-connected color-2 component (the template, 3-5 cells)",
    "exactly one color-1 cell (the anchor)",
    "control, template, and anchor are placed with 1-cell buffer between them",
    "rotated template stamped at anchor fits in-bounds",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (control is
# drawn unconditionally across all bands.)
AXES = {
    "grid_h":        {"type": "int", "default": "rng 11..14", "valid": "9..18",
                      "doc": "Grid height (easy 9..11, medium 11..14, hard 13..18)."},
    "grid_w":        {"type": "int", "default": "rng 13..16", "valid": "11..20",
                      "doc": "Grid width (easy 11..13, medium 13..16, hard 15..20)."},
    "template_size": {"type": "int", "default": "rng 3..5", "valid": "3..6",
                      "doc": "Cells in the color-2 template blob (easy 3..4, medium 3..5, hard 4..6)."},
    "control":       {"type": "int", "default": "rng 6..9", "valid": "6..9",
                      "doc": "Control value in {6,7,8,9}; rot_count = control - 6."},
}


def _free(g, cells, h, w):
    cell_set = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 0:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 0 and (nr, nc) not in cell_set:
                        return False
    return True


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def _rotate_cw_n(cells, n):
    """Apply 90° CW rotation n times."""
    for _ in range(n % 4):
        # (r, c) → (c, -r) then normalize
        maxr = max(r for r, _ in cells)
        cells = [(c, maxr - r) for r, c in cells]
    return cells


def _component_cells(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable input invariants for the rotate-template/stamp-at-anchor task."""
    errors: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    controls = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (6, 7, 8, 9)]
    if len(controls) != 1:
        errors.append(f"expected exactly one control in {{6,7,8,9}}, found {len(controls)}")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-1 anchor, found {len(anchors)}")
    comps = _component_cells(grid, 2)
    if len(comps) != 1:
        errors.append(f"expected exactly one color-2 template component, found {len(comps)}")
    elif not (3 <= len(comps[0]) <= 6):
        errors.append(f"template component size {len(comps[0])} outside expected 3..6")

    if controls and anchors and len(comps) == 1:
        ar, ac = anchors[0]
        _, _, control = controls[0]
        template_abs = comps[0]
        minr = min(r for r, _ in template_abs)
        minc = min(c for _, c in template_abs)
        template = [(r - minr, c - minc) for r, c in template_abs]
        rotated = _rotate_cw_n(template, control - 6)
        rr0 = min(r for r, _ in rotated)
        cc0 = min(c for _, c in rotated)
        rotated = [(r - rr0, c - cc0) for r, c in rotated]
        stamp = {(ar + dr, ac + dc) for dr, dc in rotated}
        oob = [(r, c) for r, c in stamp if not (0 <= r < h and 0 <= c < w)]
        if oob:
            errors.append("rotated stamp footprint falls outside the grid")
        for sr, sc in stamp:
            if 0 <= sr < h and 0 <= sc < w:
                if (sr, sc) != (ar, ac) and grid[sr][sc] != 0:
                    errors.append("rotated stamp footprint collides with input marks")
                    break
        cr, cc, _ = controls[0]
        if (cr, cc) in stamp:
            errors.append("control lies inside the future stamp footprint")
        # The three semantic marks should be visually separable from each other.
        marked = set(template_abs) | set(anchors) | {(cr, cc)}
        for r, c in marked:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in marked and grid[nr][nc] != 0:
                        errors.append("template/control/anchor lack a one-cell visual buffer")
                        return errors
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        template_size = ctx.draw_int("template_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 20)
        template_size = ctx.draw_int("template_size", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        template_size = ctx.draw_int("template_size", 3, 5)
    control_value = ctx.draw_int("control", 6, 9)
    rot_count = control_value - 6

    for outer in range(60):
        g = full_grid(h, w, 0)
        # Build template
        template = _build_blob(rng, template_size)
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        # Place template
        template_placed = False
        for _ in range(40):
            r0 = rng.randint(0, h - th)
            c0 = rng.randint(0, w - tw)
            cells_abs = [(r0 + dr, c0 + dc) for dr, dc in template]
            if not _free(g, cells_abs, h, w):
                continue
            for r, c in cells_abs:
                g[r][c] = 2
            template_placed = True
            break
        if not template_placed:
            continue
        # Compute rotated shape for stamping
        rotated = _rotate_cw_n(template, rot_count)
        # Normalize rotated
        minr = min(r for r, _ in rotated)
        minc = min(c for _, c in rotated)
        rotated = [(r - minr, c - minc) for r, c in rotated]
        rh = max(r for r, _ in rotated) + 1
        rw = max(c for _, c in rotated) + 1
        # Place anchor such that anchor + rotated cells fit in grid
        anchor_placed = False
        for _ in range(80):
            ar = rng.randint(0, h - rh)
            ac = rng.randint(0, w - rw)
            stamp_cells = [(ar + dr, ac + dc) for dr, dc in rotated]
            # All stamp cells need to be on bg (they'll be painted 4, replacing 0)
            # And the anchor itself is at first cell of rotated, which is (0, 0) → (ar, ac)
            # Skip if anchor is on template or control
            if g[ar][ac] != 0:
                continue
            # The stamp covers stamp_cells. They may overlap with anchor (ar, ac).
            # Allow stamp cells to be on bg
            ok = all(0 <= sr < h and 0 <= sc < w and g[sr][sc] == 0 for sr, sc in stamp_cells)
            if not ok:
                continue
            # Stamp shouldn't touch template (1-cell buffer)
            too_close = False
            for sr, sc in stamp_cells:
                for ddr in (-1, 0, 1):
                    for ddc in (-1, 0, 1):
                        nr, nc = sr + ddr, sc + ddc
                        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 2:
                            too_close = True
                            break
                    if too_close:
                        break
                if too_close:
                    break
            if too_close:
                continue
            g[ar][ac] = 1
            stamp_footprint = set(stamp_cells)   # cells the rule will paint 4
            anchor_placed = True
            break
        if not anchor_placed:
            continue
        # Place control (single cell in {6,7,8,9}) somewhere clear AND outside the
        # stamp footprint (else the rule's color-4 stamp would overwrite the control)
        control_placed = False
        for _ in range(60):
            cr = rng.randint(0, h - 1)
            cc = rng.randint(0, w - 1)
            if g[cr][cc] != 0 or (cr, cc) in stamp_footprint:
                continue
            # 1-cell buffer from any non-bg
            too_close = False
            for ddr in (-1, 0, 1):
                for ddc in (-1, 0, 1):
                    nr, nc = cr + ddr, cc + ddc
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                        too_close = True
                        break
                if too_close:
                    break
            if too_close:
                continue
            g[cr][cc] = control_value
            control_placed = True
            break
        if not control_placed:
            continue
        return g
    raise ValueError("could not realize layout")


def _components_of_color(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _normalize(cells):
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return sorted((r - minr, c - minc) for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    bad = sorted({v for row in grid for v in row if v not in (0, 1, 2, 6, 7, 8, 9)})
    if bad:
        errs.append(f"unexpected colors in input grid: {bad}")
    controls = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] in (6, 7, 8, 9)]
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    comps2 = _components_of_color(grid, 2)
    if len(controls) != 1:
        errs.append(f"expected exactly one control cell in {{6,7,8,9}}, found {len(controls)}")
    if len(anchors) != 1:
        errs.append(f"expected exactly one color-1 anchor, found {len(anchors)}")
    if len(comps2) != 1:
        errs.append(f"expected exactly one color-2 template component, found {len(comps2)}")
    elif not (3 <= len(comps2[0]) <= 6):
        errs.append(f"template size should be 3..6 cells, found {len(comps2[0])}")
    if len(controls) == 1 and len(anchors) == 1 and len(comps2) == 1:
        _, _, control = controls[0]
        ar, ac = anchors[0]
        shape = _normalize(comps2[0])
        rotated = _normalize(_rotate_cw_n(shape, control - 6))
        footprint = [(ar + dr, ac + dc) for dr, dc in rotated]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in footprint):
            errs.append("rotated template footprint at anchor goes out of bounds")
        else:
            for r, c in footprint:
                if grid[r][c] not in (0, 1):
                    errs.append("rotated template footprint overlaps template or control")
                    break
            if any((r, c) == (controls[0][0], controls[0][1]) for r, c in footprint):
                errs.append("control lies inside stamp footprint")
    return errs

