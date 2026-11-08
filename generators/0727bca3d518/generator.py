"""Generator for arc_puzzle_bank_21_set24_s:S24_M6 — onion depth of two panels.

Rule (ACTUAL): split at full color-9 COLUMNS into panels. For a panel,
merge all non-{0,9} cells into one mask, split into 4-connected
components, onion-peel each (boundary cells = depth 1, next shell 2,
...) and take the max depth across the panel. Output is the 1x2 grid
[[depth(panel1), depth(panel2)]]. Panels beyond the second are IGNORED.

Combinatorial axes: panel_h, panel widths, depths, texture
(plain|extra_panels|multi_comp|multicolor_blob).
Degenerates: empty_panels ([[0,0]]). no_dividers / single_panel were
DROPPED: fewer than 2 panels -> (second panels) = #f -> CRASH.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0727bca3d518"
VERSION = "2.1.1"  # + self_check
TASK_ID = "0727bca3d518"

SUMMARY = (
    "Two (or more, ignored) panels split by 9-columns; output is "
    "[[onion_depth(p1), onion_depth(p2)]] - depth 1 for thin shapes, "
    "2 for shapes with a fat 3x3 core, 3 for 5x5 cores. Colors merge "
    "into one mask (multicolor blobs are ONE component). (Was: 1-3 "
    "cell motifs in 4-7 panels - every output was [[1,1]], plus two "
    "degenerates that crashed the rule.)"
)

# Rivals: 'count cells / components' refuted by same-depth shapes of
# different sizes. 'per-color components' refuted by multicolor blobs
# that peel as one. 'all panels read' refuted by extra_panels. 'depth
# is max 1' refuted by depth-2/3 boards. 4 demos with varied depths.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    ">=2 panels ALWAYS (fewer crash the rule)",
    "panel depths are mirror-verified to match the intended targets",
    "panels contain >=1 component each on main path",
]

DEGENERATE_TEXTURES = ("empty_panels",)
HELPFUL_TEXTURES = ("plain", "extra_panels", "multi_comp", "multicolor_blob")

AXES = {
    "panel_h": {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "depth1":  {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "depth2":  {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|extra_panels|multi_comp|multicolor_blob|"
                         "empty_panels",
                "doc": "extra_panels: trailing panels the rule ignores; "
                       "multi_comp: panel depth = MAX over 2 components; "
                       "multicolor_blob: touching colors peel as one."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _depth(panel):
    """Max onion depth over 4-connected components of the non-{0,9} mask."""
    h, w = len(panel), len(panel[0])
    mask = {(r, c) for r in range(h) for c in range(w)
            if panel[r][c] not in (0, 9)}
    best = 0
    seen = set()
    for start in sorted(mask):
        if start in seen:
            continue
        stack = [start]
        comp = {start}
        seen.add(start)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in mask and p not in seen:
                    seen.add(p)
                    comp.add(p)
                    stack.append(p)
        cur, d = set(comp), 0
        while cur:
            boundary = {(r, c) for r, c in cur
                        if any((r + dr, c + dc) not in cur
                               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))}
            cur -= boundary
            d += 1
        best = max(best, d)
    return best


def _depth_shape(rng, d, ph, pw):
    """Random cells (panel-local) with onion depth exactly d."""
    for _ in range(120):
        if d == 1:
            cells = [(0, 0)]
            seen = {(0, 0)}
            k = rng.randint(1, 5)
            while len(cells) < k:
                r, c = cells[rng.randrange(len(cells))]
                dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
                if (r + dr, c + dc) not in seen:
                    cells.append((r + dr, c + dc))
                    seen.add((r + dr, c + dc))
        else:
            core = 2 * d - 1
            if core > ph or core > pw:
                return None
            rh = rng.randint(core, min(ph, core + 2))
            rw = rng.randint(core, min(pw, core + 2))
            cells = [(r, c) for r in range(rh) for c in range(rw)]
            for _w in range(rng.randint(0, 3)):  # warts keep the core
                r, c = cells[rng.randrange(len(cells))]
                dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
                if (r + dr, c + dc) not in cells:
                    cells.append((r + dr, c + dc))
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        cells = [(r - mr, c - mc) for r, c in cells]
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        if sh > ph or sw > pw:
            continue
        probe = [[0] * sw for _ in range(sh)]
        for r, c in cells:
            probe[r][c] = 1
        if _depth(probe) == d:
            return cells
    return None


def _fill_panel(rng, ph, pw, d, texture):
    """Build one ph x pw panel whose max onion depth is exactly d."""
    panel = [[0] * pw for _ in range(ph)]
    shape = _depth_shape(rng, d, ph, pw)
    if shape is None:
        shape = [(r, c) for r in range(2 * d - 1) for c in range(2 * d - 1)]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    r0 = rng.randint(0, ph - sh)
    c0 = rng.randint(0, pw - sw)
    if texture == "multicolor_blob" and len(shape) >= 2:
        ca, cb = rng.sample(_COLORS, 2)
        for i, (r, c) in enumerate(shape):
            panel[r0 + r][c0 + c] = ca if i % 2 else cb
    else:
        color = rng.choice(_COLORS)
        for r, c in shape:
            panel[r0 + r][c0 + c] = color
    if texture == "multi_comp" and d >= 2:
        # add a SHALLOWER component: max() keeps the deep one's depth
        small = _depth_shape(rng, 1, ph, pw)
        if small:
            ssh = max(r for r, _ in small) + 1
            ssw = max(c for _, c in small) + 1
            for _try in range(60):
                rr = rng.randint(0, ph - ssh)
                cc = rng.randint(0, pw - ssw)
                spots = [(rr + r, cc + c) for r, c in small]
                if all(panel[r][c] == 0
                       and all(panel[nr][nc] == 0
                               for nr in range(max(0, r - 1), min(ph, r + 2))
                               for nc in range(max(0, c - 1), min(pw, c + 2))
                               if (nr, nc) not in spots)
                       for r, c in spots):
                    color2 = rng.choice(_COLORS)
                    for r, c in spots:
                        panel[r][c] = color2
                    break
    return panel


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 full-height color-9 columns splitting the grid into >=2 panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    divider_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divider_cols) < 1:
        errs.append("no full-height color-9 divider column: rule crashes (fewer than 2 panels)")
    # number of panels = dividers+1; need >=2 panels -> >=1 divider
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "extra_panels", "multi_comp",
                        "multicolor_blob"))
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 5, 6)
        dmax = 2
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 6, 8)
        dmax = 3
    else:
        ph = ctx.draw_int("panel_h", 5, 8)
        dmax = 2 if ph < 6 else 3
    # both depths range over the rule's full 1..dmax so all depth-pairs
    # (d1, d2) are reachable; the output is the tiny [[d1, d2]] encoding,
    # so the depth-combination count is the diversity ceiling.
    d1 = int(overrides.get("depth1") or ctx.draw_int("depth1", 1, dmax))
    d2 = int(overrides.get("depth2") or ctx.draw_int("depth2", 1, dmax))
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        widths = [rng.randint(max(4, 2 * d1 - 1), 7),
                  rng.randint(max(4, 2 * d2 - 1), 7)]
        n_extra = rng.randint(1, 2) if texture == "extra_panels" else 0
        for _ in range(n_extra):
            widths.append(rng.randint(4, 6))
        if sum(widths) + len(widths) - 1 > 29:
            continue
        panels = [_fill_panel(rng, ph, widths[0], d1, texture),
                  _fill_panel(rng, ph, widths[1], d2, texture)]
        for i in range(n_extra):
            panels.append(_fill_panel(rng, ph, widths[2 + i],
                                      rng.randint(1, 2), "plain"))
        if _depth(panels[0]) != d1 or _depth(panels[1]) != d2:
            continue
        w = sum(widths) + len(widths) - 1
        g = full_grid(ph, w, 0)
        c0 = 0
        for i, p in enumerate(panels):
            for r in range(ph):
                for c in range(widths[i]):
                    g[r][c0 + c] = p[r][c]
            c0 += widths[i]
            if i < len(panels) - 1:
                for r in range(ph):
                    g[r][c0] = 9
                c0 += 1
        return g
    raise ValueError("could not realize onion-depth board")


def _draw_from_degenerate(name, ctx):
    """empty_panels — dividers with blank panels: output [[0,0]].
    (no_dividers / single_panel dropped: <2 panels crash the rule.)"""
    rng = ctx.draw_rng("degenerate_layout")
    ph = ctx.draw_int("panel_h", 4, 6)
    widths = [rng.randint(4, 6) for _ in range(rng.randint(2, 3))]
    w = sum(widths) + len(widths) - 1
    g = full_grid(ph, w, 0)
    c0 = 0
    for i, wd in enumerate(widths):
        c0 += wd
        if i < len(widths) - 1:
            for r in range(ph):
                g[r][c0] = 9
            c0 += 1
    return g
