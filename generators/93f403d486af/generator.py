"""Generator for arc_additional_puzzle_bank_volume9:M62 -- Pick rectangle by aspect.

Rule: control = top-left cell. want = 0(wide) if control==2, 1(tall) if
control==3, else 2(square). Among the solid color-1 rectangles, output the
first one (scan order) whose aspect matches want, as an h x w grid of 1s.

This generator sets the control cell and places exactly ONE solid color-1
rectangle of the wanted aspect plus distractors of the other aspects.

Combinatorial axes: the control/aspect, the target rect dims, the
distractor rects, grid size, and positions.
Degenerates: no_ctrl, no_matching_aspect, missing_rect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "93f403d486af"
VERSION = "2.4.0"  # distinct=28 = all 28 sizes for the old _rect_dims ranges (output is a solid 1-rect, distinct = #possible (h,w)). Widen square k 2..7, wide/tall a 2..5 b a+1..a+5 -> far more distinct sizes.
TASK_ID = "93f403d486af"
SUMMARY = (
    "0-bg grid (size varies). A top-left CONTROL cell (2->wide, 3->tall, "
    "else->square) and several solid color-1 rectangles. Rule: output the "
    "first rectangle whose aspect matches the control, as an h x w grid of "
    "1s. The control/aspect, target rect dims, distractor rects, grid size "
    "and positions vary freely (was a fixed setup, ~21 distinct)."
)

INVARIANTS = [
    "the control cell sets the wanted aspect (wide/tall/square)",
    "exactly one solid color-1 rectangle has the wanted aspect",
    "the output is that rectangle filled with 1s",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_ctrl", "no_matching_aspect", "missing_rect")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "want":           {"type": "int", "default": "rng 0..2", "valid": "0|1|2"},
    "n_distractors":  {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "scattered_rects", "valid": "scattered_rects"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_ctrl|no_matching_aspect|missing_rect"},
}


def _rect_dims(rng, aspect):
    """aspect 0=wide(w>h), 1=tall(h>w), 2=square(h==w). Wide ranges so the
    solid-1-rect output spans many distinct sizes."""
    if aspect == 2:
        k = rng.randint(2, 8); return k, k
    a = rng.randint(2, 6); b = rng.randint(a + 1, a + 6)
    return (a, b) if aspect == 0 else (b, a)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ndr = (12, 14), (12, 15), (1, 2)
    elif difficulty == "hard":
        hr, wr, ndr = (17, 22), (18, 24), (2, 3)
    else:
        hr, wr, ndr = (13, 18), (14, 20), (1, 3)

    want = int(overrides["want"]) if "want" in overrides else rng.randint(0, 2)
    control = {0: 2, 1: 3}.get(want, rng.choice([0, 4, 5, 6, 7, 8, 9]))

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        occ[0][0] = True   # reserve the control cell

        # exactly one rect of the wanted aspect + distractors of other aspects
        others = [a for a in (0, 1, 2) if a != want]
        plan = [want] + [rng.choice(others) for _ in range(rng.randint(*ndr))]
        ok = True
        for aspect in plan:
            rh, rw = _rect_dims(rng, aspect)
            placed = False
            for _t in range(50):
                if rh > h or rw > w:
                    break
                top = rng.randint(0, h - rh); left = rng.randint(0, w - rw)
                if _reserve(occ, top, left, rh, rw, h, w):
                    for r in range(top, top + rh):
                        for c in range(left, left + rw):
                            g[r][c] = 1
                    placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        g[0][0] = control
        return g

    raise ValueError("could not place target rectangle plus distractors")




def _component_cells(grid, start, seen):
    h, w = len(grid), len(grid[0])
    color = grid[start[0]][start[1]]
    stack = [start]
    seen.add(start)
    cells = []
    while stack:
        r, c = stack.pop()
        cells.append((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                    and grid[nr][nc] == color):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return cells


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _aspect(rh, rw):
    if rw > rh:
        return 0
    if rh > rw:
        return 1
    return 2


def _wanted_aspect(control):
    return 0 if control == 2 else 1 if control == 3 else 2


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the control-selected solid-rectangle extraction invariant."""
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    control = grid[0][0]
    want = _wanted_aspect(control)
    if control == 1:
        errors.append("control cell must not be color 1; it would merge with rectangles")

    seen: set[tuple[int, int]] = set()
    rects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            cells = _component_cells(grid, (r, c), seen)
            r0, c0, r1, c1 = _bbox(cells)
            rh, rw = r1 - r0 + 1, c1 - c0 + 1
            if len(cells) != rh * rw:
                errors.append(f"color-1 component at {(r0, c0)} is not a solid rectangle")
            rects.append((r0, c0, rh, rw, _aspect(rh, rw)))
    if not rects:
        errors.append("missing color-1 rectangles")
    matches = [rect for rect in rects if rect[4] == want]
    if len(matches) != 1:
        errors.append(f"expected exactly one rectangle matching wanted aspect {want}, got {len(matches)}")
    if len(rects) < 2:
        errors.append("expected at least one distractor rectangle")
    if rects and len({rect[4] for rect in rects}) < 2:
        errors.append("rectangles do not cover multiple aspect classes")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    g[0][0] = 2
    for r in range(3, 5):
        for c in range(3, 7):
            g[r][c] = 1     # a wide rect
    if name == "no_ctrl":
        g[0][0] = 0
        return g
    if name == "no_matching_aspect":
        g[0][0] = 3         # want tall, but only a wide rect exists
        return g
    if name == "missing_rect":
        return full_grid(12, 12, 0)
    return g
