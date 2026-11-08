"""Generator for e4888269.

Rule: solid two-column key table defines ordered color substitutions.

Combinatorial axes (8): grid_h/w, key_height, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, key_position.
Degenerates: no_key, no_targets, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "35b257d07d86"
VERSION = "2.1.0"  # fix identity_demo: targets placed in the key's 8-neighborhood merged with it (multicolor 8-conn), widening the key past 2 columns so the rule failed to detect it -> no substitution -> output==input. Keep a 1-cell margin around the key.
TASK_ID = "35b257d07d86"
SUMMARY = (
    "0-bg grid (h~8-14, w~"
    "8-14) with: (a) A "
    "2-COLUMN × kh-TALL "
    "(kh ∈ [3, 5]) KEY "
    "TABLE — a solid "
    "rectangle at (kr0, "
    "kc0)..(kr0+kh, kc0+1) "
    "where each row r of "
    "the key holds a "
    "(LEFT_COLOR, "
    "RIGHT_COLOR) PAIR "
    "(distinct colors from "
    "a palette, encoding "
    "the mapping LEFT → "
    "RIGHT); (b) OPTIONAL "
    "VERTICAL SEPARATOR "
    "LINE at col w//2 in "
    "COLOR 2 (sometimes "
    "present, sometimes "
    "not); (c) SPARSE "
    "TARGET CELLS outside "
    "the key bbox in "
    "values drawn from "
    "the key's LEFT colors "
    "(so they trigger "
    "substitution). Rule "
    "(APPLY KEY-TABLE "
    "SUBSTITUTION TO ALL "
    "CELLS OUTSIDE THE "
    "KEY BBOX): identify "
    "the KEY TABLE (2-"
    "column × kh-tall "
    "solid multicolor "
    "component). PARSE "
    "each key row as a "
    "MAPPING LEFT_COLOR → "
    "RIGHT_COLOR. For EACH "
    "CELL OUTSIDE the key "
    "bbox: if its color "
    "matches any key "
    "row's LEFT color, "
    "RECOLOR to that "
    "row's RIGHT color. "
    "Else, keep. Key "
    "table stays intact. "
    "Net: target cells "
    "get substituted "
    "color-by-color "
    "according to the "
    "table's lookup."
)

# Rivals: 'output is input' refuted by demos (target cells recolor).
# 'recolor key too' refuted by demos (key stays). 'use most frequent
# color' refuted by demos (mapping-based recolor visible). 'recolor
# all cells uniformly' refuted by demos with multiple target colors.
# 3 demos with ≥2 distinct target colors covered by key map cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "the key table is a solid 2-column multicolor component",
    "key rows are read top-to-bottom as color substitution pairs",
    "the key table itself is preserved while other cells are substituted",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_key", "no_targets", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "10", "valid": "8..14"},
    "key_height":     {"type": "int", "default": "3", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 4..5", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = rng.randint(8, 10); w = rng.randint(10, 14); kh = rng.randint(3, 3)
        n_targets = rng.randint(2, 3)
    elif difficulty == "hard":
        h = rng.randint(12, 16); w = rng.randint(16, 22); kh = rng.randint(4, 6)
        n_targets = rng.randint(6, 12)
    else:
        h = rng.randint(9, 12); w = rng.randint(12, 18); kh = rng.randint(3, 5)
        n_targets = rng.randint(3, 6)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, kh + 1, rng)
    if len(pool) < kh + 1:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    colors = pool[:kh + 1]
    g = full_grid(h, w, 0)
    # Place key table at a random position in the left half (so right half has room for targets)
    kr0 = rng.randint(0, h - kh)
    kc0 = rng.randint(0, max(0, w // 2 - 3))
    pairs = [(colors[i], colors[i + 1]) for i in range(kh)]
    for r in range(kh):
        g[kr0 + r][kc0] = pairs[r][0]
        g[kr0 + r][kc0 + 1] = pairs[r][1]
    # Optional vertical separator at col w//2
    if rng.random() < 0.5 and w // 2 != kc0 and w // 2 != kc0 + 1:
        for r in range(h):
            if g[r][w // 2] == 0:
                g[r][w // 2] = 2
    # Place n_targets target cells outside key bbox at random positions,
    # using values from colors (so they'll be substituted).
    placed = 0
    for _ in range(n_targets * 8):
        if placed >= n_targets:
            break
        rr = rng.randint(0, h - 1); cc = rng.randint(0, w - 1)
        # Keep a 1-cell margin (incl. diagonals) around the key bbox: a
        # target touching the key would 8-merge into its multicolor
        # component, widening it past 2 columns so the rule can no longer
        # recognise the key (-> no substitution -> identity output).
        if kr0 - 1 <= rr <= kr0 + kh and kc0 - 1 <= cc <= kc0 + 2:
            continue
        if g[rr][cc] != 0:
            continue
        g[rr][cc] = rng.choice(colors)
        placed += 1
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _find_key(grid):
    """Locate an isolated 2-wide, >=3-tall solid multicolor (>=3 distinct)
    rectangle — the key table. Returns (kr0, kc0, kh) or None."""
    h, w = len(grid), len(grid[0])
    for kr0 in range(h):
        for kc0 in range(w - 1):
            # extend downward while both columns are non-bg
            kh = 0
            while (kr0 + kh < h and grid[kr0 + kh][kc0] != 0
                   and grid[kr0 + kh][kc0 + 1] != 0):
                kh += 1
            if kh < 3:
                continue
            # must start fresh (row above is bg in these two cols)
            if kr0 > 0 and (grid[kr0 - 1][kc0] != 0 or grid[kr0 - 1][kc0 + 1] != 0):
                continue
            vals = {grid[kr0 + i][kc0] for i in range(kh)} | \
                   {grid[kr0 + i][kc0 + 1] for i in range(kh)}
            if len(vals) < 3:
                continue
            # isolated: 8-neighborhood outside the bbox must be all bg
            iso = True
            for r in range(kr0 - 1, kr0 + kh + 1):
                for c in range(kc0 - 1, kc0 + 3):
                    if kr0 <= r < kr0 + kh and kc0 <= c <= kc0 + 1:
                        continue
                    if 0 <= r < h and 0 <= c < w and grid[r][c] != 0:
                        iso = False
            if iso:
                return (kr0, kc0, kh)
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Input must hold one isolated 2-wide key table plus >=1 target cell
    whose colour matches a key LEFT colour (else the rule is a no-op)."""
    issues = []
    key = _find_key(grid)
    if key is None:
        issues.append("no isolated 2-wide x >=3 multicolor key table found")
        return issues
    kr0, kc0, kh = key
    left_colors = {grid[kr0 + i][kc0] for i in range(kh)}
    h, w = len(grid), len(grid[0])
    in_key = lambda r, c: kr0 <= r < kr0 + kh and kc0 <= c <= kc0 + 1
    triggers = any(grid[r][c] in left_colors and not in_key(r, c)
                   for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not triggers:
        issues.append("no outside cell matches a key LEFT colour -> no-op")
    return issues


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_key":
        for i, value in enumerate([1, 2, 3, 4]):
            g[6][4 + i] = value
        return g
    if name == "no_targets":
        for r in range(3):
            g[1 + r][1] = r + 2
            g[1 + r][2] = r + 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
