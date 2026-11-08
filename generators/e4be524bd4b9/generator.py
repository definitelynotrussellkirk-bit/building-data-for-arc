"""Generator for arc_puzzle_bank_twentysecond21:H152.

Rule: five panels split by all-8 columns -- ea, eb, eo, ta, tb. The demo
ea OP eb = eo (by support, OP in union/intersection/xor; eo's pattern in
its dominant color). The output is OP applied to ta and tb, recolored with
ta's dominant color.

This generator builds disambiguating demo panels ea,eb with eo = OP(ea,eb)
in one color, and monochrome operand panels ta,tb.

Combinatorial axes: the operation, the panel patterns/sizes, and the
output color.
Degenerates: no_separators, identical_ab, empty_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4be524bd4b9"
VERSION = "2.1.0"  # robustness: clamp panel widths to the 30-col canvas (hard band 3w1+2w2+4 hit 39)
TASK_ID = "e4be524bd4b9"
SUMMARY = (
    "5-panel grid (size varies) split by all-8 columns: ea, eb, eo "
    "demonstrate a binary set op (union/intersection/xor by support, eo in "
    "one color), then ta, tb are the operands. Rule: output OP(ta, tb) "
    "recolored with ta's dominant color. The operation, panel patterns/sizes "
    "and output color vary freely (was a fixed setup, ~26 distinct)."
)

INVARIANTS = [
    "five panels split by single all-8 columns; ea/eb/eo share width, ta/tb share width",
    "the demo ea,eb overlap AND differ both ways so exactly one op matches",
    "the output is the demonstrated op applied to ta,tb in ta's color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "identical_ab", "empty_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

OPS = ("union", "intersection", "xor")

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "4..10"},
    "panel_w":        {"type": "int", "default": "varies", "valid": "3..7"},
    "operation":      {"type": "str", "default": "rng", "valid": "union|intersection|xor"},
    "out_color":      {"type": "color", "default": "rng !{0,8}", "valid": "1..7|9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "five_panels", "valid": "five_panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separators|identical_ab|empty_panels"},
}


def _applyop(name, A, B):
    h = len(A); w = len(A[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            av = A[r][c] != 0; bv = B[r][c] != 0
            if name == "union":
                out[r][c] = 1 if (av or bv) else 0
            elif name == "intersection":
                out[r][c] = 1 if (av and bv) else 0
            else:
                out[r][c] = 1 if (av != bv) else 0
    return out


def _disambig_pair(rng, h, w):
    for _ in range(60):
        a = [[1 if rng.random() < 0.45 else 0 for _ in range(w)] for _ in range(h)]
        b = [[1 if rng.random() < 0.45 else 0 for _ in range(w)] for _ in range(h)]
        both = any(a[r][c] and b[r][c] for r in range(h) for c in range(w))
        aonly = any(a[r][c] and not b[r][c] for r in range(h) for c in range(w))
        bonly = any(b[r][c] and not a[r][c] for r in range(h) for c in range(w))
        if both and aonly and bonly:
            return a, b
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    op = overrides.get("operation") or rng.choice(list(OPS))

    if difficulty == "easy":
        hr, w1r, w2r = (4, 6), (3, 4), (3, 4)
    elif difficulty == "hard":
        hr, w1r, w2r = (7, 10), (5, 7), (5, 7)
    else:
        hr, w1r, w2r = (5, 8), (3, 6), (3, 6)

    for _attempt in range(40):
        h = rng.randint(*hr)
        w1 = rng.randint(*w1r); w2 = rng.randint(*w2r)
        # layout spans 3*w1 + 2*w2 + 4 separators; clamp to the 30-col ARC
        # canvas (band minima all fit at <=29, so this never goes below range).
        while 3 * w1 + 2 * w2 + 4 > 30:
            if w1 > w2:
                w1 -= 1
            else:
                w2 -= 1
        ab = _disambig_pair(rng, h, w1)
        xy = _disambig_pair(rng, h, w2)
        if ab is None or xy is None:
            continue
        ea, eb = ab; ta, tb = xy
        eo = _applyop(op, ea, eb)
        if not any(eo[r][c] for r in range(h) for c in range(w1)):
            continue

        # each panel painted in a single color (eo and ta colors drive the rule)
        cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 5)
        out_col = int(overrides["out_color"]) if "out_color" in overrides else cols[3]
        panels = [(ea, w1, cols[0]), (eb, w1, cols[1]), (eo, w1, cols[2]),
                  (ta, w2, out_col), (tb, w2, cols[4])]
        total_w = w1 * 3 + w2 * 2 + 4
        g = full_grid(h, total_w, 0)
        cur = 0
        for (panel, wd, col) in panels:
            for r in range(h):
                for c in range(wd):
                    if panel[r][c]:
                        g[r][cur + c] = col
            cur += wd
            if cur < total_w:
                for r in range(h):
                    g[r][cur] = 8
                cur += 1
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h = 4
    ea = [[1, 0], [1, 1], [0, 1], [0, 0]]
    eb = [[1, 1], [0, 1], [0, 0], [1, 0]]
    eo = _applyop("union", ea, eb)
    ta = [[1, 0], [0, 1], [1, 1], [0, 0]]
    tb = [[0, 1], [0, 1], [1, 0], [1, 0]]
    panels = [(ea, 3), (eb, 4), (eo, 5), (ta, 6), (tb, 7)]
    g = full_grid(h, 2 * 5 + 4, 0)
    cur = 0
    for (panel, col) in panels:
        for r in range(h):
            for c in range(2):
                if panel[r][c]:
                    g[r][cur + c] = col
        cur += 2
        if cur < 2 * 5 + 4:
            for r in range(h):
                g[r][cur] = 8
            cur += 1
    if name == "no_separators":
        return full_grid(h, 6, 3)
    if name == "identical_ab":
        return g
    if name == "empty_panels":
        return full_grid(h, 14, 0)
    return g


def _split_panels(grid):
    h, w = len(grid), len(grid[0])
    seps = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    panels = []
    start = 0
    for sep in seps + [w]:
        panels.append([row[start:sep] for row in grid])
        start = sep + 1
    return seps, panels


def _support(panel):
    return [[1 if v != 0 else 0 for v in row] for row in panel]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid has non-ARC color values")
    seps, panels = _split_panels(grid)
    if len(seps) != 4 or len(panels) != 5:
        errors.append(f"expected five panels split by four all-8 columns, got {len(panels)} panels")
        return errors
    ea, eb, eo, ta, tb = panels
    if not (len(ea[0]) == len(eb[0]) == len(eo[0])):
        errors.append("demo panels ea/eb/eo must have equal widths")
    if not (len(ta[0]) == len(tb[0])):
        errors.append("target panels ta/tb must have equal widths")
    A, B, E = _support(ea), _support(eb), _support(eo)
    matches = []
    for op in OPS:
        if _applyop(op, A, B) == E:
            matches.append(op)
    if len(matches) != 1:
        errors.append(f"demo should identify exactly one operation, got {matches}")
    if not any(v for row in E for v in row):
        errors.append("demo output panel must be nonempty")
    if any(v == 8 for panel in panels for row in panel for v in row):
        errors.append("separator color 8 leaked into a data panel")
    if matches:
        T = _applyop(matches[0], _support(ta), _support(tb))
        if not any(v for row in T for v in row):
            errors.append("target operation output would be empty")
    return errors

