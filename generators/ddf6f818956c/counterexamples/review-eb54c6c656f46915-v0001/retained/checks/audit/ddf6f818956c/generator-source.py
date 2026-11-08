"""Generator for f8a8fe49.

Rule: gray cells reflect across the red frame's near solid side. If the
top bar is solid the reflection is vertical (across top/bottom); else it
is horizontal (across left/right walls).

Combinatorial axes: grid size, reflection axis, frame size/position, and
the gray markers (count / side / position), each reflecting in-bounds.
Degenerates: no_frame, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "ddf6f818956c"
VERSION = "2.0.0"  # diversity: random axis/frame/markers, real horizontal case (was fixed 12x12, ~8 configs)
TASK_ID = "ddf6f818956c"
SUMMARY = (
    "0-bg grid (size varies). A red (color-2) frame defines the "
    "reflection box. VERTICAL axis: a full rectangular frame (solid top "
    "bar) with 1-3 gray (color-5) markers ABOVE/BELOW it. HORIZONTAL "
    "axis: only the LEFT and RIGHT vertical walls (top bar not solid) "
    "with markers to the LEFT/RIGHT. Rule: detect the frame bbox; if the "
    "top bar is solid reflect each gray vertically across the near "
    "top/bottom edge, else reflect horizontally across the near "
    "left/right wall; the original gray is removed and the reflection "
    "drawn (always in-bounds, landing in the box interior). Grid size, "
    "axis, frame size/position and the markers all vary freely (was a "
    "fixed 12x12 frame with one marker)."
)

INVARIANTS = [
    "a red rectangular frame (or left/right walls) establishes the reflection box",
    "gray marker cells are removed from their original positions",
    "gray markers reappear reflected across the near solid side, in-bounds",
]

AXES_DIR = ("vertical", "horizontal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "no_marker", "full_grid")
HELPFUL_TEXTURES = AXES_DIR

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "reflection_axis":{"type": "str", "default": "rng helpful",
                       "valid": "vertical|horizontal"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "frame_h":        {"type": "int", "default": "varies", "valid": "4..8"},
    "frame_w":        {"type": "int", "default": "varies", "valid": "4..8"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for reflection_axis",
                       "valid": "vertical|horizontal|no_frame|no_marker|full_grid"},
}


def _walls_lr(g, r0, c0, r1, c1):
    for r in range(r0, r1 + 1):
        g[r][c0] = 2
        g[r][c1] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    axis = (overrides.get("texture") if overrides.get("texture") in AXES_DIR else None) or \
           overrides.get("reflection_axis") or \
           rng.choice(list(AXES_DIR))

    if difficulty == "easy":
        hr, wr, fr, nm = (10, 12), (10, 12), (4, 5), (1, 1)
    elif difficulty == "hard":
        hr, wr, fr, nm = (13, 18), (13, 18), (5, 8), (2, 3)
    else:
        hr, wr, fr, nm = (11, 14), (11, 14), (4, 6), (1, 2)

    for _attempt in range(80):
        h = rng.randint(*hr); w = rng.randint(*wr)
        fh = rng.randint(*fr); fw = rng.randint(*fr)
        # Leave room outside the box for the markers (>=2 margin on the box's sides).
        r0 = rng.randint(2, h - fh - 2); c0 = rng.randint(2, w - fw - 2)
        r1 = r0 + fh - 1; c1 = c0 + fw - 1

        g = full_grid(h, w, 0)
        used = set()
        markers = []
        ok = True
        for _ in range(rng.randint(*nm)):
            for _t in range(30):
                if axis == "vertical":
                    side = rng.choice([-1, 1])
                    d = rng.randint(1, fh - 2)
                    gc = rng.randint(c0 + 1, c1 - 1)
                    gr = (r0 - d) if side < 0 else (r1 + d)
                    nr = (r0 + d) if side < 0 else (r1 - d)
                    nc = gc
                else:
                    side = rng.choice([-1, 1])
                    d = rng.randint(1, fw - 2)
                    gr = rng.randint(r0 + 1, r1 - 1)
                    gc = (c0 - d) if side < 0 else (c1 + d)
                    nr = gr
                    nc = (c0 + d) if side < 0 else (c1 - d)
                if not (0 <= gr < h and 0 <= gc < w and 0 <= nr < h and 0 <= nc < w):
                    continue
                if (gr, gc) in used or (nr, nc) in used:
                    continue
                markers.append((gr, gc)); used.add((gr, gc)); used.add((nr, nc))
                break
            else:
                ok = False
        if not ok or not markers:
            continue

        if axis == "vertical":
            draw_frame(g, r0, c0, r1, c1, 2)
        else:
            _walls_lr(g, r0, c0, r1, c1)
        # markers must land on empty cells (not on the frame).
        bad = False
        for gr, gc in markers:
            if g[gr][gc] != 0:
                bad = True; break
            g[gr][gc] = 5
        if bad:
            continue
        return g

    # Fallback: original known-valid layout.
    g = full_grid(12, 12, 0)
    draw_frame(g, 3, 3, 7, 7, 2)
    g[1][5] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the default frame-reflection input."""
    errors = []
    if not grid or not isinstance(grid, list) or any(not isinstance(row, list) for row in grid):
        return ["grid must be a nonempty 2D list"]
    h = len(grid); w = len(grid[0]) if grid[0] else 0
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    vals = {v for row in grid for v in row}
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in vals):
        errors.append("grid values must be integer colors 0..9")
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if not red:
        errors.append("missing red reflection frame/walls")
    if not gray:
        errors.append("missing gray marker(s)")
    if not red or not gray:
        return errors
    r0, r1 = min(r for r, _ in red), max(r for r, _ in red)
    c0, c1 = min(c for _, c in red), max(c for _, c in red)
    if r1 - r0 < 3 or c1 - c0 < 3:
        errors.append(f"frame bbox too small: rows {r0}-{r1}, cols {c0}-{c1}")
        return errors

    def all_red(cells):
        return all(grid[r][c] == 2 for r, c in cells)

    left_wall = all_red((r, c0) for r in range(r0, r1 + 1))
    right_wall = all_red((r, c1) for r in range(r0, r1 + 1))
    top_bar = all_red((r0, c) for c in range(c0, c1 + 1))
    bottom_bar = all_red((r1, c) for c in range(c0, c1 + 1))
    if not (left_wall and right_wall):
        errors.append("red bbox must have complete left and right walls")
        return errors

    if top_bar:
        if not bottom_bar:
            errors.append("vertical-reflection frame must include a complete bottom bar")
        axis = "vertical"
    else:
        axis = "horizontal"

    used_targets = set()
    for gr, gc in gray:
        if axis == "vertical":
            if not (c0 < gc < c1):
                errors.append(f"vertical marker column {gc} must be inside frame interior cols")
                continue
            if gr < r0:
                d = r0 - gr; target = (r0 + d, gc)
            elif gr > r1:
                d = gr - r1; target = (r1 - d, gc)
            else:
                errors.append(f"vertical marker {(gr, gc)} must sit outside frame vertically")
                continue
        else:
            if not (r0 < gr < r1):
                errors.append(f"horizontal marker row {gr} must be inside frame interior rows")
                continue
            if gc < c0:
                d = c0 - gc; target = (gr, c0 + d)
            elif gc > c1:
                d = gc - c1; target = (gr, c1 - d)
            else:
                errors.append(f"horizontal marker {(gr, gc)} must sit outside frame horizontally")
                continue
        tr, tc = target
        if not (r0 < tr < r1 and c0 < tc < c1):
            errors.append(f"reflected target {target} must land in frame interior")
        elif grid[tr][tc] != 0:
            errors.append(f"reflected target {target} must be empty in the input")
        if target in used_targets:
            errors.append(f"two markers collide at reflected target {target}")
        used_targets.add(target)
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_frame":
        g[3][5] = 5
        return g
    if name == "no_marker":
        draw_frame(g, 3, 3, 7, 7, 2)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
