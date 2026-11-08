"""Generator for 0beba7b7e706 — count-stamped proto copies.

Rule: proto = the top-left 3x3 subgrid (non-zero cells = stamp mask).
Every cell with value 1-4 OUTSIDE the top-left 3x3 stamps a
transformed proto (1 identity, 2 rotate-cw, 3 flip-lr, 4 flip-ud)
CENTERED on itself; stamps clip at edges. The output is the per-cell
OVERLAP COUNT (1 where one stamp covers, 2 where two overlap, ...).
Markers and the proto vanish unless covered. Values 5-9 are NOT
markers.

Combinatorial axes: grid_h/w, proto mask, markers, texture
(plain|overlap|clip|ignored_marker|top_band_marker).
Degenerates: no_markers (blank output), blank_proto.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0beba7b7e706"
VERSION = "2.0.1"
TASK_ID = "0beba7b7e706"
SUMMARY = (
    "1-4 markers stamp transformed copies of the corner proto, and "
    "the output COUNTS overlaps per cell - overlap boards cluster "
    "markers 2 apart so counts reach 2-4 (the original task's "
    "centerpiece, never generated before: old markers were "
    "deliberately separated). clip boards stamp at edges; "
    "ignored_marker boards add 5-9 cells (not markers); "
    "top_band_marker boards put a marker at r<3, c>=3 (legal - only "
    "the 3x3 corner is excluded)."
)

# Rivals: 'output = stamped color' refuted by count-2+ cells.
# 'any non-zero stamps' refuted by ignored_marker. 'whole top rows
# excluded' refuted by top_band_marker. 3-4 demos incl. >=1 overlap
# board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "proto mask asymmetric under cw/flip-lr/flip-ud (codes distinct)",
    "overlap boards: >=1 cell covered by >=2 stamps",
    "counts never exceed 9 (markers <= 6)",
]

DEGENERATE_TEXTURES = ("no_markers", "blank_proto")
HELPFUL_TEXTURES = ("plain", "overlap", "clip", "ignored_marker",
                    "top_band_marker")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 10..15", "valid": "9..20"},
    "grid_w":  {"type": "int", "default": "rng 10..15", "valid": "9..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|overlap|clip|ignored_marker|"
                         "top_band_marker|no_markers|blank_proto",
                "doc": "overlap: clustered markers, counts 2+; clip: "
                       "edge stamps; ignored_marker: 5-9 cells inert; "
                       "top_band_marker: marker at r<3, c>=3."},
}


def _tf(mask, code):
    if code == 2:
        return [list(row) for row in zip(*mask[::-1])]
    if code == 3:
        return [row[::-1] for row in mask]
    if code == 4:
        return mask[::-1]
    return [row[:] for row in mask]


def _mirror(g):
    h, w = len(g), len(g[0])
    proto = [[g[r][c] for c in range(3)] for r in range(3)]
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v in (1, 2, 3, 4) and not (r < 3 and c < 3):
                obj = _tf(proto, v)
                top = r - len(obj) // 2
                left = c - len(obj[0]) // 2
                for dr, row in enumerate(obj):
                    for dc, pv in enumerate(row):
                        rr, cc = top + dr, left + dc
                        if pv != 0 and 0 <= rr < h and 0 <= cc < w:
                            out[rr][cc] += 1
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "overlap", "overlap",
                                              "clip", "ignored_marker",
                                              "top_band_marker"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_marks = (1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 13, 15)
        n_marks = (3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 10, 15)
        n_marks = (2, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        g = full_grid(h, w, 0)
        pc = rng.choice([5, 6, 7, 8, 9])
        for _t in range(200):
            mask = [[pc if rng.random() < 0.5 else 0 for _ in range(3)]
                    for _ in range(3)]
            nz = sum(1 for row in mask for v in row if v)
            views = {str(_tf(mask, k)) for k in (1, 2, 3, 4)}
            if 3 <= nz <= 6 and len(views) == 4:
                break
        else:
            continue
        for r in range(3):
            for c in range(3):
                g[r][c] = mask[r][c]
        markers = []

        def add_marker(r, c, val):
            if not (0 <= r < h and 0 <= c < w):
                return False
            if r < 3 and c < 3:
                return False
            if g[r][c] != 0:
                return False
            g[r][c] = val
            markers.append((r, c))
            return True

        want = rng.randint(*n_marks)
        if texture == "overlap":
            # a tight cluster: stamps 3x3 centered, spacing 2 overlaps
            r0 = rng.randint(5, h - 3)
            c0 = rng.randint(2, w - 3)
            add_marker(r0, c0, rng.randint(1, 4))
            add_marker(r0, min(w - 1, c0 + 2), rng.randint(1, 4))
            if rng.random() < 0.7:
                add_marker(min(h - 1, r0 + 2), c0, rng.randint(1, 4))
        elif texture == "clip":
            edge = rng.choice(["t", "b", "l", "r"])
            if edge == "t":
                add_marker(3, rng.randint(3, w - 1), rng.randint(1, 4))
            elif edge == "b":
                add_marker(h - 1, rng.randint(0, w - 1),
                           rng.randint(1, 4))
            elif edge == "l":
                add_marker(rng.randint(4, h - 1), 0, rng.randint(1, 4))
            else:
                add_marker(rng.randint(4, h - 1), w - 1,
                           rng.randint(1, 4))
        elif texture == "top_band_marker":
            add_marker(rng.randint(0, 2), rng.randint(4, w - 2),
                       rng.randint(1, 4))
        for _ in range(want):
            for _t in range(80):
                r = rng.randint(4, h - 2)
                c = rng.randint(1, w - 2)
                if all(abs(r - mr) > 3 or abs(c - mc) > 3
                       for mr, mc in markers):
                    if add_marker(r, c, rng.randint(1, 4)):
                        break
        if texture == "ignored_marker":
            for _t in range(60):
                r = rng.randint(4, h - 1)
                c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = rng.choice([5, 6, 7, 8, 9])
                    break
        if not markers:
            continue
        out = _mirror(g)
        if max(v for row in out for v in row) > 9:
            continue
        if texture == "overlap" and \
           max(v for row in out for v in row) < 2:
            continue
        if all(v == 0 for row in out for v in row):
            continue
        return g
    raise ValueError("could not realize count-stamp board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """top-left 3x3 has >=1 non-zero cell (proto mask) AND >=1 marker (1-4) outside the 3x3."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    proto_nz = any(grid[r][c] != 0 for r in range(min(3, h)) for c in range(min(3, w)))
    if not proto_nz:
        errors.append("top-left 3x3 is blank (blank proto — stamps nothing)")
    has_marker = any(grid[r][c] in (1, 2, 3, 4)
                     for r in range(h) for c in range(w)
                     if not (r < 3 and c < 3))
    if not has_marker:
        errors.append("no marker (1-4) outside the top-left 3x3 — blank output")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_markers — proto only: blank output. blank_proto — empty
    corner mask: markers stamp nothing, blank output. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 10, 13)
    g = full_grid(h, w, 0)
    if name == "no_markers":
        pc = rng.choice([5, 6, 7, 8, 9])
        for r in range(3):
            for c in range(3):
                if rng.random() < 0.5:
                    g[r][c] = pc
        return g
    g[rng.randint(5, h - 2)][rng.randint(3, w - 2)] = rng.randint(1, 4)
    return g
