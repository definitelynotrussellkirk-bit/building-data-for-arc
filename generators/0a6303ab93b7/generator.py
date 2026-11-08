"""Generator for arc_puzzle_bank_21_set17_bundle:medium_p01 —
selector + transform-code crop.

Rule: (0,0) = selector color; (0,w-1) = transform code (1 identity,
2 rotate-cw, 3 rotate-180, 4 flip-lr, anything else identity). Among
objects of the selector color, EXCLUDING any containing (0,0), the
first in top-left bbox order is cropped/normalized and transformed.
GOTCHA: the code cell itself is NOT excluded — if code == sel the
1-cell code object at (0,w-1) wins top-left order and the output is
[[sel]] (corner_wins texture; the old generator hit this silently on
~9% of boards). (0,0)=0 CRASHES — never generated. The rule has NO
frame logic — frames here are pure decoys (old docstring described a
different frame-centering rule).

Combinatorial axes: grid_h/w, sel/code, shapes, texture
(plain|multi_candidate|weird_code|corner_wins|symmetric).
Degenerates: none survivable (no_sel crashes, documented).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "0a6303ab93b7"
VERSION = "2.1.0"  # diversity: wider selected-object shapes (4-8 cells, 5x5 bbox) to lift transformed-crop output variety
TASK_ID = "0a6303ab93b7"

SUMMARY = (
    "Top-left selector color + top-right transform code crop the "
    "first matching object (rot-cw / rot-180 / flip-lr / identity). "
    "multi_candidate boards carry TWO selector-colored objects "
    "(top-left bbox order wins); weird_code boards use codes 5-9 "
    "(identity); corner_wins boards deliberately set code == sel so "
    "the 1-cell code object wins and the output is [[sel]]; "
    "symmetric boards make the transform invisible on a symmetric "
    "shape. Frames/blobs in other colors are decoys (the rule has no "
    "frame logic)."
)

# Rivals: 'transform the only object' refuted by multi_candidate.
# 'code cell is excluded like the selector' refuted by corner_wins.
# 'codes beyond 4 rotate more' refuted by weird_code (identity).
# 4 demos covering >=3 codes with asymmetric shapes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "(0,0) is never 0 (crashes); main-path code != sel",
    "main-path shapes asymmetric so the transform is inferable",
    "selector-colored body objects clear of row 0",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "multi_candidate", "weird_code",
                    "corner_wins", "symmetric")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..14", "valid": "8..16"},
    "grid_w":  {"type": "int", "default": "rng 10..16", "valid": "9..20"},
    "code":    {"type": "int", "default": "rng 1..4", "valid": "1..9"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|multi_candidate|weird_code|corner_wins|"
                         "symmetric",
                "doc": "corner_wins: code==sel, the code cell itself is "
                       "the first matching object -> output [[sel]]; "
                       "weird_code: codes 5-9 fall to identity."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _grow(rng, k, max_h=4, max_w=4):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _subgrid_of(cells, color):
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r][c] = color
    return out


def _tf(sub, code):
    if code == 2:
        return [list(row) for row in zip(*sub[::-1])]
    if code == 3:
        return [row[::-1] for row in sub[::-1]]
    if code == 4:
        return [row[::-1] for row in sub]
    return sub


def _asym(rng, k):
    for _ in range(300):
        s = _grow(rng, k, max_h=5, max_w=5)  # wider bbox -> richer output crops
        subs = _subgrid_of(s, 1)
        if all(_tf(subs, c) != subs for c in (2, 3, 4)) and \
           len({str(_tf(subs, c)) for c in (1, 2, 3, 4)}) == 4:
            return s
    return [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]


def _mirror(g):
    h, w = len(g), len(g[0])
    sel = g[0][0]
    code = g[0][w - 1]
    seen = set()
    objs = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != sel or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == sel:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if (0, 0) not in cells:
                objs.append(cells)
    if not objs:
        return None
    objs.sort(key=lambda cs: (min(r for r, _ in cs),
                              min(c for _, c in cs)))
    cells = objs[0]
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    norm = [(r - mr, c - mc) for r, c in cells]
    return _tf(_subgrid_of(norm, sel), code)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "multi_candidate",
                                              "weird_code", "corner_wins",
                                              "symmetric"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 10, 16)
    rng = ctx.draw_rng("layout")

    sel, decoy_color = rng.sample(list(_COLORS), 2)
    if texture == "weird_code":
        code = rng.choice([5, 6, 7, 8, 9])
        while code == sel:
            code = rng.choice([5, 6, 7, 8, 9])
    elif texture == "corner_wins":
        code = sel
    else:
        code = int(overrides.get("code") or ctx.draw_int("code", 1, 4))
        while code == sel:
            code = rng.randint(1, 4) if code <= 4 else code + 1
            if code == sel:
                code = (code % 9) + 1

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        g[0][0] = sel
        g[0][w - 1] = code

        def place(shape, color, r_lo=2):
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            for _t in range(150):
                r0 = rng.randint(r_lo, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = [(r0 + r, c0 + c) for r, c in shape]
                if all(g[rr][cc] == 0 and
                       all(g[ar][ac] != color
                           for ar, ac in ((rr - 1, cc), (rr + 1, cc),
                                          (rr, cc - 1), (rr, cc + 1))
                           if 0 <= ar < h and 0 <= ac < w)
                       for rr, cc in cells):
                    for rr, cc in cells:
                        g[rr][cc] = color
                    return True
            return False

        if texture == "symmetric":
            shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
        else:
            shape = _asym(rng, rng.randint(4, 8))
        if not place(shape, sel):
            continue
        if texture == "multi_candidate":
            if not place(_asym(rng, rng.randint(4, 8)), sel):
                continue
        # decoys: a hollow frame + a blob in another color
        if rng.random() < 0.6:
            fh, fw = rng.randint(4, 5), rng.randint(4, 6)
            for _t in range(60):
                r0 = rng.randint(2, h - fh)
                c0 = rng.randint(0, w - fw)
                box = [(r, c) for r in range(r0, r0 + fh)
                       for c in range(c0, c0 + fw)]
                if all(g[r][c] == 0 for r, c in box):
                    draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1,
                               decoy_color)
                    break
        else:
            place(_grow(rng, rng.randint(3, 5)), decoy_color)
        if _mirror(g) is None:
            continue
        return g
    raise ValueError("could not realize selector-transform board")

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the selector+transform crop task."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows have inconsistent widths"]
    sel = grid[0][0]
    code = grid[0][w - 1]
    if sel == 0:
        errs.append("selector cell (0,0) is zero; canonical rule crashes")
    if not (1 <= code <= 9):
        errs.append(f"transform-code cell should be 1..9, got {code}")
    candidates = [c for c in components(grid, colors={sel})
                  if (0, 0) not in set(c["cells"])]
    if not candidates:
        errs.append("no selector-colored candidate object outside (0,0)")
        return errs
    candidates.sort(key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))
    first = candidates[0]
    if code == sel:
        if (0, w - 1) not in set(first["cells"]):
            errs.append("code==selector texture should make the code cell the first candidate")
    else:
        if len(first["cells"]) < 2:
            errs.append("main-path selected object collapsed to a singleton")
        if any(r == 0 for r, _c in first["cells"]):
            errs.append("main-path selected object should be clear of row 0")
    return errs
