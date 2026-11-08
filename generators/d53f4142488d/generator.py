"""Generator for edcc2ff0.

Rule: top has 3 indicator cells in col 0 (rows 1, 3, 5). Below row 7 is
a colored region; for each indicator color, count its objects and paint
a horizontal bar of that length on the indicator row.

Combinatorial axes (8): grid_h/w, indicator_palette, bg_choice,
n_objs_per_color, position_bias, palette_kind, anchor_corner,
asymmetry_force.
Degenerates: no_indicators, no_bg_row, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d53f4142488d"
VERSION = "1.5.0"  # identity fix: when every indicator had exactly ONE body object, all three output bars were length 1 (just the indicator cell) -> output == input. Now guarantee >=1 indicator color has >=2 SEPARATED body objects so its bar extends past col 0 and the output differs.
TASK_ID = "d53f4142488d"
SUMMARY = "20-tall grid with 3 indicators + uniform-color rect at row 7+."

INVARIANTS = [
    "h >= 16, w in 8..12",
    "rows 0,2,4,6 are all 0",
    "rows 1,3,5 have a single non-zero cell at col 0 (the indicator)",
    "row 7 is a full-width row of one bg color",
    "rows 8+ have non-zero cells of indicator colors at distinct positions",
]

POSITION_BIASES = ("scattered", "stacked", "clustered", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_indicators", "no_bg_row", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 18..22", "valid": "16..26"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..16"},
    "n_objs_per_color":{"type": "int", "default": "rng 2..6", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "bg_choice":      {"type": "color", "default": "rng",
                       "valid": "3|7"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # indicator bar length = count of that colour's objects in the body. Counts were
    # capped low (<=4) -> dup 33%. Widen per-colour object-count range + grid width.
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 16, 18, 7, 9
        no_lo, no_hi = 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 21, 26, 12, 16
        no_lo, no_hi = 3, 8
    else:
        h_lo, h_hi, w_lo, w_hi = 18, 22, 9, 13
        no_lo, no_hi = 2, 6
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, rng)
    indicators = palette[:3]
    bg = int(overrides.get("bg_choice",
                           rng.choice([v for v in [3, 7] if v not in indicators])))
    g[1][0] = indicators[0]
    g[3][0] = indicators[1]
    g[5][0] = indicators[2]
    for r in range(7, h):
        for c in range(w):
            g[r][c] = bg
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    no_per = int(overrides.get("n_objs_per_color",
                               ctx.draw_int("n_objs_per_color",
                                            no_lo, no_hi)))
    no_per = max(1, min(8, no_per))
    for color in indicators:
        n_objs = rng.randint(1, no_per)
        placed_for_color = 0
        for _ in range(n_objs):
            for _try in range(40):
                r = rng.randint(8, h - 2)
                if bias == "stacked":
                    c = 1
                elif bias == "clustered":
                    c = rng.randint(0, max(0, w // 2 - 2))
                else:
                    c = rng.randint(0, w - 2)
                if g[r][c] == bg and g[r][c + 1] == bg:
                    g[r][c] = color
                    g[r][c + 1] = color
                    placed_for_color += 1
                    break
        if placed_for_color == 0:
            forced = False
            for rr in range(8, h):
                for cc in range(0, w - 1):
                    if g[rr][cc] == bg and g[rr][cc + 1] == bg:
                        g[rr][cc] = color
                        g[rr][cc + 1] = color
                        forced = True
                        break
                if forced:
                    break
            if not forced:
                raise ValueError("could not place at least one body object per indicator color")
    # Guarantee a visible bar: if every indicator color has only ONE body
    # object, all output bars are length 1 (== the indicator cell) -> identity.
    # Add a SECOND, separated object for the first indicator so its bar grows.
    if all(_count_body_objs(g, col, h, w) <= 1 for col in indicators):
        col = indicators[0]
        used = [r for r in range(8, h) if any(g[r][c] == col for c in range(w))]
        for rr in range(8, h):
            if any(abs(rr - er) <= 1 for er in used):
                continue                # keep the new bar a separate component
            done = False
            for cc in range(0, w - 1):
                if g[rr][cc] == bg and g[rr][cc + 1] == bg:
                    g[rr][cc] = col; g[rr][cc + 1] = col
                    done = True
                    break
            if done:
                break
    return g


def _count_body_objs(g, color, h, w):
    """# of 4-connected components of `color` in the body (rows 8..h-1)."""
    seen = set(); n = 0
    for r in range(8, h):
        for c in range(w):
            if g[r][c] == color and (r, c) not in seen:
                n += 1; stack = [(r, c)]; seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (8 <= nr < h and 0 <= nc < w
                                and g[nr][nc] == color and (nr, nc) not in seen):
                            seen.add((nr, nc)); stack.append((nr, nc))
    return n


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 2, 4]
    else:
        pool = [1, 2, 4, 5, 6, 8, 9]
    pool = [c for c in pool if c not in (3, 7)]
    rng.shuffle(pool)
    if len(pool) < 3:
        for c in [1, 2, 4, 5, 6, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= 3:
                break
    return pool[:3]


def _draw_from_degenerate(name, rng):
    h, w = 20, 10
    g = full_grid(h, w, 0)
    if name == "no_indicators":
        for c in range(w):
            g[7][c] = 3
        return g
    if name == "no_bg_row":
        g[1][0] = 1; g[3][0] = 2; g[5][0] = 4
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate indicator rows and counted body objects."""
    errs: list[str] = []
    if not isinstance(grid, list) or len(grid) < 16 or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list with at least 16 rows"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if w < 6:
        errs.append("grid must be wide enough for indicator bars")
    indicators = [grid[1][0], grid[3][0], grid[5][0]] if h > 5 else []
    if len(indicators) != 3 or any(c == 0 for c in indicators) or len(set(indicators)) != 3:
        errs.append("rows 1,3,5 must hold three distinct non-zero indicators at column 0")
    for r in (0, 2, 4, 6):
        if r < h and any(grid[r][c] != 0 for c in range(w)):
            errs.append(f"row {r} should be all-zero separator")
            break
    if h <= 7 or len(set(grid[7])) != 1 or grid[7][0] == 0:
        errs.append("row 7 must be a full non-zero body-background row")
    bg = grid[7][0] if h > 7 else None
    for color in indicators:
        if not color:
            continue
        body_cells = [(r, c) for r in range(8, h) for c in range(w) if grid[r][c] == color]
        if len(body_cells) < 2:
            errs.append(f"indicator color {color} must have at least one 2-cell body object")
        elif len(body_cells) % 2:
            errs.append(f"indicator color {color} body cells should form 2-cell bars")
    if bg is not None:
        for r in range(8, h):
            for c in range(w):
                if grid[r][c] not in set(indicators) | {bg}:
                    errs.append("body region should contain only bg and indicator colors")
                    return errs
    # non-identity: >=1 indicator must have >=2 objects (bar longer than 1 cell)
    if (all(c for c in indicators)
            and all(_count_body_objs(grid, c, h, w) <= 1 for c in indicators)):
        errs.append("every indicator has <=1 body object -> all bars length 1 "
                    "-> output == input (identity)")
    return errs
