"""Generator for 538b439f.

Rule: solid rectangles mirror across a full-span colored line, and the
gaps to both rectangles are filled with the line color.

Combinatorial axes (8): grid_h/w, orientation, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_line, no_rect, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "886360dbb9ba"
RULE_HASH = "8a6df9341a79"  # canonical rule this generator was written against
VERSION = "2.4.0"  # in_sh=out_sh=1: fixed 16x17. Rule mirrors rect across a full-span line, reading h,w generically (canonical 20x20, 21x18). Vary grid h,w (line stays centered; rect placed so its mirror fits) -> input/output dims vary; distinct already 144.
TASK_ID = "886360dbb9ba"
SUMMARY = (
    "Fixed-size 16×17 grid filled with "
    "BG color drawn distinct from "
    "line_color, rect_color (3-color "
    "palette via draw_distinct_colors). "
    "(a) ONE FULL-SPAN LINE in "
    "ORIENTATION ∈ {vertical (col "
    "w//2=8 painted line_color across "
    "all rows) / horizontal (row h//2=8 "
    "painted across all cols)}; "
    "(b) ONE SOLID RECTANGLE of size "
    "rh × rw (rh, rw ∈ 2-4) placed in "
    "the OPPOSITE side of the line "
    "from where the mirror will land — "
    "for vertical line: r0 ∈ 2-9, c0 "
    "∈ 1-3 (left of line); for "
    "horizontal: r0 ∈ 1-3 (above "
    "line), c0 ∈ 3-10 — painted in "
    "rect_color. Rule (MIRROR THE "
    "SOLID RECTANGLE ACROSS THE FULL-"
    "SPAN LINE; FILL THE GAP BETWEEN "
    "THE ORIGINAL AND THE MIRRORED "
    "COPY WITH THE LINE COLOR; "
    "ORIGINAL RECT, MIRRORED RECT, "
    "AND LINE ALL PRESERVED): "
    "IDENTIFY the line (color and "
    "axis). For EACH solid rectangle: "
    "REFLECT it across the line to "
    "get its mirrored position. "
    "PAINT the mirror cells in "
    "rect_color. FILL the GAP between "
    "the original rect and the "
    "mirror's nearest edge with "
    "LINE_COLOR (connecting them). "
    "Net: each rectangle is "
    "duplicated on the other side "
    "of the line; a line-colored "
    "bridge connects the pair "
    "through the original line."
)

INVARIANTS = [
    "the background is the mode color",
    "there is one full-span non-background row or column line",
    "all other non-background objects are solid rectangles",
    "default instances contain many rectangle/singleton sources, matching canonical clutter",
    "each rectangle is mirrored across the line and bridged to the line with the line color",
]

ORIENTATIONS = ("vertical", "horizontal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_line", "no_rect", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "16", "valid": "16"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "vertical|horizontal"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "3..5"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "vertical|horizontal|no_line|no_rect|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    palette = ctx.draw_distinct_colors("colors", n=4, exclude=set())
    bg, line_color, *rect_palette = palette
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 18, 20); w = ctx.draw_int("grid_w", 18, 20)
        target_rects = rng.randint(9, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 20, 24); w = ctx.draw_int("grid_w", 20, 24)
        target_rects = rng.randint(14, 20)
    else:
        h = ctx.draw_int("grid_h", 20, 21); w = ctx.draw_int("grid_w", 18, 20)
        target_rects = rng.randint(11, 16)
    g = full_grid(h, w, bg)

    occupied = set()
    def mark_box(r1, c1, r2, c2):
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                occupied.add((rr, cc))

    if orientation == "vertical":
        line_idx = w // 2
        for r in range(h):
            g[r][line_idx] = line_color
            occupied.add((r, line_idx))
    else:
        line_idx = h // 2
        for c in range(w):
            g[line_idx][c] = line_color
            occupied.add((line_idx, c))

    def mirror_box(r1, c1, r2, c2):
        if orientation == "vertical":
            return r1, 2 * line_idx - c2, r2, 2 * line_idx - c1
        return 2 * line_idx - r2, c1, 2 * line_idx - r1, c2

    def fits(r1, c1, r2, c2):
        if not (0 <= r1 <= r2 < h and 0 <= c1 <= c2 < w):
            return False
        # keep a visible background gap before the mirror line
        if orientation == "vertical" and not (c2 <= line_idx - 2 or c1 >= line_idx + 2):
            return False
        if orientation == "horizontal" and not (r2 <= line_idx - 2 or r1 >= line_idx + 2):
            return False
        mr1, mc1, mr2, mc2 = mirror_box(r1, c1, r2, c2)
        if not (0 <= mr1 <= mr2 < h and 0 <= mc1 <= mc2 < w):
            return False
        for rr in range(r1 - 1, r2 + 2):
            for cc in range(c1 - 1, c2 + 2):
                if (rr, cc) in occupied:
                    return False
        # Do not place a source on top of another source's future mirror target.
        for rr in range(mr1, mr2 + 1):
            for cc in range(mc1, mc2 + 1):
                if (rr, cc) in occupied:
                    return False
        return True

    placed = 0
    # Force one prominent rectangle, then add canonical-like singleton clutter.
    shapes = [(3, 3), (2, 3), (3, 2), (1, 1), (1, 1), (1, 1), (1, 2), (2, 1)]
    for _ in range(target_rects * 80):
        if placed >= target_rects:
            break
        rh, rw = shapes[min(placed, len(shapes) - 1)] if placed < 3 else rng.choice(shapes[3:])
        if orientation == "vertical":
            side_left = rng.choice([True, False])
            r1 = rng.randint(1, h - rh - 2)
            if side_left:
                c1 = rng.randint(1, max(1, line_idx - rw - 2))
            else:
                c1 = rng.randint(line_idx + 2, w - rw - 1)
        else:
            side_top = rng.choice([True, False])
            c1 = rng.randint(1, w - rw - 2)
            if side_top:
                r1 = rng.randint(1, max(1, line_idx - rh - 2))
            else:
                r1 = rng.randint(line_idx + 2, h - rh - 1)
        r2, c2 = r1 + rh - 1, c1 + rw - 1
        if not fits(r1, c1, r2, c2):
            continue
        color = rng.choice(rect_palette)
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                g[rr][cc] = color
        mark_box(r1, c1, r2, c2)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(16, 17, 0)
    if name == "no_line":
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 3
        return g
    if name == "no_rect":
        for c in range(17):
            g[8][c] = 4
        return g
    if name == "full_grid":
        for r in range(16):
            for c in range(17):
                g[r][c] = 4
        return g
    return g



def _mode_color(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _components_excluding_line(grid, bg, vertical, line_idx):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            on_line = (c == line_idx) if vertical else (r == line_idx)
            if on_line or grid[r][c] == bg or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if ((nc == line_idx) if vertical else (nr == line_idx)):
                        continue
                    if (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the mirror-across-line source grid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    bg = _mode_color(grid)
    errors = []
    full_cols = [c for c in range(w) if all(grid[r][c] != bg for r in range(h))]
    full_rows = [r for r in range(h) if all(grid[r][c] != bg for c in range(w))]
    if len(full_cols) + len(full_rows) != 1:
        return [f"expected exactly one full-span non-background line, found {len(full_cols)+len(full_rows)}"]
    vertical = bool(full_cols)
    line_idx = full_cols[0] if vertical else full_rows[0]
    line_color = grid[0][line_idx] if vertical else grid[line_idx][0]
    if vertical and any(grid[r][line_idx] != line_color for r in range(h)):
        errors.append("vertical line is not single-colored")
    if not vertical and any(grid[line_idx][c] != line_color for c in range(w)):
        errors.append("horizontal line is not single-colored")

    comps = _components_excluding_line(grid, bg, vertical, line_idx)
    if len(comps) < 8:
        errors.append(f"expected many source rectangles/singletons, found {len(comps)}")
    for color, cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if len(cells) != (r2 - r1 + 1) * (c2 - c1 + 1):
            errors.append("source object is not a solid rectangle")
        if vertical:
            if not (c2 < line_idx or c1 > line_idx):
                errors.append("rectangle must sit entirely on one side of vertical line")
            if min(abs(line_idx - c1), abs(line_idx - c2)) <= 1:
                errors.append("rectangle must leave a visible background gap before the line")
            mirror_c1, mirror_c2 = 2 * line_idx - c2, 2 * line_idx - c1
            if mirror_c1 < 0 or mirror_c2 >= w:
                errors.append("mirrored rectangle would leave the grid")
        else:
            if not (r2 < line_idx or r1 > line_idx):
                errors.append("rectangle must sit entirely on one side of horizontal line")
            if min(abs(line_idx - r1), abs(line_idx - r2)) <= 1:
                errors.append("rectangle must leave a visible background gap before the line")
            mirror_r1, mirror_r2 = 2 * line_idx - r2, 2 * line_idx - r1
            if mirror_r1 < 0 or mirror_r2 >= h:
                errors.append("mirrored rectangle would leave the grid")
    return sorted(set(errors))
