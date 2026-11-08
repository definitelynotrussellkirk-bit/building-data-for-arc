"""Generator for arc_puzzle_bank_seventh_21_bundle:hard_44_template_tiling_from_code_grid.

Rule: a LIBRARY of color-1 rectangular frames, each holding a th x tw
TEMPLATE in its interior (keyed by the interior's first-nonzero color =
its CODE). A separate solid CODE GRID lays out which template tiles where.
Output = each code cell expanded into its template, tiled.

This generator builds K distinct same-size templates inside color-1
frames (top band) and a solid code grid of those codes (bottom band).

Combinatorial axes: template count, template size, the template patterns,
the codes, and the code-grid shape/contents.
Degenerates: no_library, no_codes, code_not_in_library.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b1fcb840c8ab"
VERSION = "3.2.0"  # oversize fix: trim K so top frame band fits 30 cols (overran to ~38 -> clipped/corrupt)
TASK_ID = "b1fcb840c8ab"
SUMMARY = (
    "0-bg grid (size varies). A top band of K (2-4) color-1 rectangular "
    "FRAMES, each holding a distinct th x tw TEMPLATE in its interior; the "
    "interior's top-left (first-nonzero) color is that template's CODE. A "
    "solid CR x CC CODE GRID below uses those codes. Rule: expand each code "
    "cell into its template and tile -> a (CR*th) x (CC*tw) grid. Template "
    "count/size/patterns, the codes and the code-grid shape all vary freely "
    "(was 3 fixed monochrome 5x5 templates, ~17 distinct)."
)

INVARIANTS = [
    "every template frame is a color-1 rectangle (h,w >= 3), all interiors same size",
    "each template's code = its interior top-left color, distinct across templates",
    "the code grid is a solid rectangle of valid codes, clear of every frame's rows",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_codes", "code_not_in_library")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "n_templates":    {"type": "int", "default": "varies", "valid": "2..4"},
    "tile_h":         {"type": "int", "default": "varies", "valid": "2..4"},
    "tile_w":         {"type": "int", "default": "varies", "valid": "2..4"},
    "code_rows":      {"type": "int", "default": "varies", "valid": "2..4"},
    "code_cols":      {"type": "int", "default": "varies", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_library|no_codes|code_not_in_library"},
}


def _template(rng, th, tw, code, palette):
    """th x tw grid; [0][0] = code (first-nonzero), rest random from palette+0."""
    pat = [[0] * tw for _ in range(th)]
    pat[0][0] = code
    for r in range(th):
        for c in range(tw):
            if (r, c) == (0, 0):
                continue
            pat[r][c] = rng.choice([0] + palette)
    return pat


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        kr, tr, cr = (2, 2), (2, 3), (2, 2)
    elif difficulty == "hard":
        kr, tr, cr = (3, 4), (3, 4), (3, 4)
    else:
        kr, tr, cr = (2, 4), (2, 3), (2, 3)

    K = rng.randint(*kr)
    th = rng.randint(*tr); tw = rng.randint(*tr)
    codes = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], K)
    palette = [c for c in [2, 3, 4, 5, 6, 7, 8, 9]]
    templates = {code: _template(rng, th, tw, code, palette) for code in codes}

    # top band: K frames in a row, each (th+2) x (tw+2), gap 2 between them
    fw = tw + 2; fh = th + 2
    # trim K so the top frame band + padding fits the 30-col canvas (overran to ~38 -> clipped/corrupt)
    while K > 1 and K * fw + (K - 1) * 2 + 2 > 30:
        K -= 1
    codes = codes[:K]
    g_w = max(K * fw + (K - 1) * 2, 1)
    # code grid
    crc = rng.randint(*cr); ccc = rng.randint(*cr)
    code_cells = [[rng.choice(codes) for _ in range(ccc)] for _ in range(crc)]

    g_w = max(g_w, ccc) + 2
    code_top = fh + 2
    g_h = code_top + crc + 1
    g = full_grid(g_h, g_w, 0)

    # place frames
    left = 1
    for code in codes:
        draw_frame(g, 1, left, 1 + fh - 1, left + fw - 1, 1)
        pat = templates[code]
        for r in range(th):
            for c in range(tw):
                if pat[r][c]:
                    g[1 + 1 + r][left + 1 + c] = pat[r][c]
        left += fw + 2

    # place the solid code grid (bottom band, clear of all frame rows)
    cl = rng.randint(1, max(1, g_w - ccc - 1))
    for r in range(crc):
        for c in range(ccc):
            g[code_top + r][cl + c] = code_cells[r][c]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    draw_frame(g, 1, 1, 4, 4, 1)
    g[2][2] = 2
    if name == "no_library":
        return full_grid(6, 6, 0)
    if name == "no_codes":
        return g
    if name == "code_not_in_library":
        g[7][1] = 9   # code with no matching template
        return g
    return g


def _color_components(g, color):
    h, w = len(g), len(g[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _is_rect_frame(cells):
    r0, c0, r1, c1 = _bbox(cells)
    border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
              if r in (r0, r1) or c in (c0, c1)}
    return (r1 - r0 >= 2 and c1 - c0 >= 2 and set(cells) == border)


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    frames = sorted([_bbox(cells) for cells in _color_components(grid, 1) if _is_rect_frame(cells)])
    if len(frames) < 2:
        msgs.append(f"expected at least two color-1 template frames, got {len(frames)}")
    sizes = set()
    codes = []
    frame_rect_cells = set()
    for r0, c0, r1, c1 in frames:
        sizes.add((r1 - r0 - 1, c1 - c0 - 1))
        frame_rect_cells.update((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
        interior = [grid[r][c] for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        nz = [v for v in interior if v != 0]
        if not nz:
            msgs.append("template interior is blank")
        else:
            codes.append(nz[0])
    if len(sizes) > 1:
        msgs.append(f"template interiors have inconsistent sizes: {sorted(sizes)}")
    if len(codes) != len(set(codes)):
        msgs.append("template codes are not distinct")
    valid_codes = set(codes)
    code_cells = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] != 0 and (r, c) not in frame_rect_cells]
    # Exclude accidental non-frame color-1 cells from the code grid check: those
    # are already caught by missing/invalid frames above.
    code_cells = [(r, c) for r, c in code_cells if grid[r][c] != 1]
    if not code_cells:
        msgs.append("missing solid code grid")
    else:
        r0, c0, r1, c1 = _bbox(code_cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] not in valid_codes:
                    msgs.append("code grid is not a solid rectangle of valid template codes")
                    return msgs
        if any(r <= max(fr[2] for fr in frames) for r, _ in code_cells):
            msgs.append("code grid overlaps template-frame rows")
    return msgs
