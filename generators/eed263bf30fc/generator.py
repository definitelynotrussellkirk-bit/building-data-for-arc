"""Generator for eed263bf30fc — infer transform from top panels, apply to bottom-left.

Rule: find full color-9 row (separator) and column. Split into 4 panels.
Detect which transform t in {identity, rot-cw, rot-180, rot-ccw,
flip-lr, flip-ud} maps top-left to top-right. Apply t to bottom-left,
paste into bottom-right. Output = input with bottom-right filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eed263bf30fc"
VERSION = "2.2.0"  # guarantee bottom-left witness has >=2 cells + axis metadata matches hard band
TASK_ID = "eed263bf30fc"
SUMMARY = (
    "2N+1 by 2N+1 grid with one full color-9 row (separator row) and "
    "one full color-9 column (separator col), splitting the grid into "
    "4 N×N panels. Top-left has a small shape A in some color cA. "
    "Top-right is t(A) for some transform t in {rot-cw, rot-180, "
    "rot-ccw, flip-lr, flip-ud}. Bottom-left has a different shape Q "
    "in color cQ (cQ ≠ cA possibly). Bottom-right is empty. Rule: "
    "find separators, split into panels, detect transform t. Apply t "
    "to Q. Paste t(Q) into bottom-right. Output = input + filled "
    "bottom-right."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "grid has one full color-9 row and one full color-9 column (the separators)",
    "the 4 panels are equal-size",
    "top-left and top-right panels are related by some non-identity transform",
    "bottom-left has non-trivial content (≥2 non-bg cells)",
    "bottom-right is empty (all 0)",
]

# Free axes the runner may override. Keys match the keyed draw labels in
# generate(); defaults are the medium band, valid spans easy..hard. (panel_n is
# a constant 3 in the easy band, so it's only keyed in medium/hard.)
AXES = {
    "panel_n":   {"type": "int", "default": "rng 3..4", "valid": "3..8",
                  "doc": "Side length of each of the 4 panels (easy 3, medium 3..4, hard 5..8)."},
    "transform": {"type": "choice", "default": "rng r1|r2|r3|fh|fv", "valid": "r1|r2|r3|fh|fv",
                  "doc": "Top-left→top-right transform: r1=rot-cw r2=rot-180 r3=rot-ccw fh=flip-lr fv=flip-ud."},
}

_TRANSFORMS = ["r1", "r2", "r3", "fh", "fv"]
# rule's transform-detection order (id checked first, then these)
_RULE_ORDER = ["id", "r1", "r2", "r3", "fh", "fv"]


def _detect(a, tr):
    """First transform (in the rule's order) mapping a -> tr, or None."""
    if a == tr:
        return "id"
    for code in ("r1", "r2", "r3", "fh", "fv"):
        if _xform_grid(a, code) == tr:
            return code
    return None


def _xform_grid(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "r1":  # rotate CW
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":  # rotate 180
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":  # rotate CCW
        return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w - 1, -1, -1)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    return list(reversed([row[:] for row in grid]))


def _paste(g, top, left, panel):
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            g[top + r][left + c] = value


def _build_shape(rng, n, color, density=0.5):
    """Random shape on n×n with given density."""
    shape = [[0] * n for _ in range(n)]
    cells = 0
    for r in range(n):
        for c in range(n):
            if rng.random() < density:
                shape[r][c] = color
                cells += 1
    if cells == 0:
        shape[0][0] = color
    return shape


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n = 3
    elif difficulty == "hard":
        n = ctx.draw_int("panel_n", 5, 8)
    else:
        n = ctx.draw_int("panel_n", 3, 4)
    h_total = 2 * n + 1
    code = ctx.draw_choice("transform", _TRANSFORMS)
    color_a = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    color_q = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7, 8] if c != 9 and c != color_a])

    # Pick A so that `code` is the UNIQUE first-match transform tl->tr (the rule
    # detects exactly the intended transform; no ambiguity from symmetric A).
    a = _build_shape(rng, n, color_a, density=0.45)
    for _ in range(40):
        cand = _build_shape(rng, n, color_a, density=0.45)
        tr = _xform_grid(cand, code)
        if _detect(cand, tr) == code:
            a = cand
            break
    q = _build_shape(rng, n, color_q, density=0.4)
    if sum(v != 0 for row in q for v in row) < 2:
        # The invariant and demos need a non-trivial bottom-left witness; a
        # one-cell Q makes every transform look identical on that branch.
        q = [[0] * n for _ in range(n)]
        q[0][0] = color_q
        q[min(1, n - 1)][0] = color_q

    g = full_grid(h_total, h_total, 0)
    # Place separators at middle row and column
    sep = n
    for i in range(h_total):
        g[sep][i] = 9
        g[i][sep] = 9
    _paste(g, 0, 0, a)
    _paste(g, 0, sep + 1, _xform_grid(a, code))
    _paste(g, sep + 1, 0, q)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if h != w or h % 2 != 1:
        return [f"expected odd square 2N+1 grid, got {h}x{w}"]
    n = h // 2
    if n < 3 or n > 8:
        errors.append(f"panel size outside declared range: {n}")
    if any(grid[n][c] != 9 for c in range(w)) or any(grid[r][n] != 9 for r in range(h)):
        errors.append("middle row/column are not full color-9 separators")
    tl = [row[:n] for row in grid[:n]]
    tr = [row[n + 1:] for row in grid[:n]]
    bl = [row[:n] for row in grid[n + 1:]]
    br = [row[n + 1:] for row in grid[n + 1:]]

    def xform(g, code):
        hh, ww = len(g), len(g[0])
        if code == "r1":
            return [[g[hh - 1 - r][c] for r in range(hh)] for c in range(ww)]
        if code == "r2":
            return [[g[hh - 1 - r][ww - 1 - c] for c in range(ww)] for r in range(hh)]
        if code == "r3":
            return [[g[r][ww - 1 - c] for r in range(hh)] for c in range(ww - 1, -1, -1)]
        if code == "fh":
            return [list(reversed(row)) for row in g]
        return list(reversed([row[:] for row in g]))

    matches = []
    if tl == tr:
        matches.append("id")
    for code in ("r1", "r2", "r3", "fh", "fv"):
        if xform(tl, code) == tr:
            matches.append(code)
    if not matches or matches[0] == "id":
        errors.append(f"top panels do not teach a non-identity first-match transform: {matches}")
    if sum(v != 0 for row in bl for v in row) < 2:
        errors.append("bottom-left witness has fewer than 2 non-zero cells")
    if any(v != 0 for row in br for v in row):
        errors.append("bottom-right panel should be empty")
    return errors
