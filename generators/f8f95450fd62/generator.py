"""Generator for arc_puzzle_bank_21_set19_s:S19_E7.

Combinatorial axes (8): panel_h, panel_w, palette_kind, candidate_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "f8f95450fd62"
VERSION = "2.1.1"  # cap assembled width to the 30-col ARC box (hard drew up to 10x38; validity sweep)
TASK_ID = "f8f95450fd62"
SUMMARY = (
    "0-bg grid: vertical PANELS separated by color-9 divider columns. The first "
    "panel is the KEY (its single color is the key color). The remaining "
    "CANDIDATE panels each hold a RANDOM shape in a distinct color; exactly one "
    "candidate's color equals the key color. Rule: split by color-9 dividers; "
    "read the key color from the first panel; find the FIRST candidate panel "
    "whose color matches; OUTPUT that panel's shape recolored to 8 (same panel "
    "size). Because each candidate has its own random shape, the matched "
    "panel's output shape varies widely. Candidate/key shapes are compact "
    "connected polyominoes rather than scattered singleton noise, keeping "
    "object-count near the canonical task. (Was all panels sharing one fixed "
    "3-cell shape -> a near-constant output.)"
)

INVARIANTS = [
    "vertical panels are separated by color 9",
    "the first panel contains the key color",
    "exactly one candidate panel starts with the key color",
    "the matching candidate is recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "5-6 easy / 5-8 med / 6-10 hard", "valid": "4..12"},
    "panel_w":        {"type": "int", "default": "5-6 easy / 5-8 med / 6-10 hard", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "candidate_count":{"type": "int", "default": "2-3 easy / 3-4 med / 4-6 hard", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "= candidates + key", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "key_plus_candidates",
                       "valid": "key_plus_candidates"},
    "n_distinct_colors": {"type": "int", "default": "= candidates + key", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_panel(h, w, color, rng):
    """A panel with one compact connected random shape (>=2 cells) in `color`."""
    panel = full_grid(h, w, 0)
    k_hi = max(2, min(6, (h * w) // 3))
    k = rng.randint(2, k_hi)
    cells = {(rng.randrange(h), rng.randrange(w))}
    for _ in range(200):
        if len(cells) >= k:
            break
        r, c = rng.choice(tuple(cells))
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        rng.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                cells.add((nr, nc))
                break
    for r, c in cells:
        panel[r][c] = color
    return panel


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("panel_h", 5, 6); w = ctx.draw_int("panel_w", 5, 6)
        n = ctx.draw_int("candidate_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("panel_h", 6, 10); w = ctx.draw_int("panel_w", 6, 10)
        n = ctx.draw_int("candidate_count", 4, 6)
    else:
        h = ctx.draw_int("panel_h", 5, 8); w = ctx.draw_int("panel_w", 5, 8)
        n = ctx.draw_int("candidate_count", 3, 4)
    # ARC cap: assembled width = 2 (key) + n*(w+1) <= 30 — shrink the panel
    # width first (keeps the candidate count = the task structure), then the
    # count (validity-sweep find: hard drew up to 10x38).
    while w > 5 and 2 + n * (w + 1) > 30:
        w -= 1
    while n > 2 and 2 + n * (w + 1) > 30:
        n -= 1
    rng = ctx.draw_rng("layout")
    key_color = ctx.draw_choice("key_color", [2, 3, 4, 5, 6, 7, 8])
    key = _rand_panel(h, 2, key_color, rng)            # key panel: any shape, its color is the key
    match_idx = ctx.draw_int("match_index", 0, n - 1)
    other_colors = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in (key_color, 9)]
    rng.shuffle(other_colors)
    candidates = []
    oi = 0
    for idx in range(n):
        color = key_color if idx == match_idx else other_colors[oi]
        if idx != match_idx:
            oi += 1
        candidates.append(_rand_panel(h, w, color, rng))
    return assemble_vertical_panels([key] + candidates)


def _split_cols_9(grid):
    h, w = len(grid), len(grid[0])
    panels = []
    start = 0
    c = 0
    while c < w:
        if all(grid[r][c] == 9 for r in range(h)):
            if start < c:
                panels.append([row[start:c] for row in grid])
            while c < w and all(grid[r][c] == 9 for r in range(h)):
                c += 1
            start = c
        else:
            c += 1
    if start < w:
        panels.append([row[start:w] for row in grid])
    return panels


def _panel_colors(panel):
    return {v for row in panel for v in row if v not in (0, 9)}


def _same_color_components(panel, color):
    h, w = len(panel), len(panel[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if panel[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and panel[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the key/candidate panel-selection task."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    panels = _split_cols_9(grid)
    if len(panels) < 3:
        return [f"expected key plus at least two candidate panels, found {len(panels)}"]
    key_colors = _panel_colors(panels[0])
    if len(key_colors) != 1:
        errs.append(f"key panel should have exactly one nonzero/non-divider color, got {sorted(key_colors)}")
        return errs
    key_color = next(iter(key_colors))
    matches = 0
    for idx, panel in enumerate(panels[1:]):
        colors = _panel_colors(panel)
        if len(colors) != 1:
            errs.append(f"candidate {idx} has {len(colors)} semantic colors: {sorted(colors)}")
            continue
        color = next(iter(colors))
        comps = _same_color_components(panel, color)
        if len(comps) != 1:
            errs.append(f"candidate {idx} shape is split into {len(comps)} components")
        elif len(comps[0]) < 2:
            errs.append(f"candidate {idx} shape has fewer than 2 cells")
        if color == key_color:
            matches += 1
    if matches != 1:
        errs.append(f"expected exactly one key-color candidate, found {matches}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    if name == "no_divider":
        # candidates concatenated without color-9 dividers → no panel boundary
        g = full_grid(h, 2 + w * 3, 0)
        g[1][1] = 4
        for i in range(3):
            base = 2 + i * w
            color = [4, 6, 7][i]
            g[1][base + 1] = color
        return g
    if name == "no_match":
        # no candidate has the key color → nothing to recolor
        key = full_grid(h, 2, 0); key[1][1] = 4
        candidates = []
        for color in [6, 7, 3]:
            p = full_grid(h, w, 0); p[1][1] = color
            candidates.append(p)
        return assemble_vertical_panels([key] + candidates)
    if name == "multiple_matches":
        # multiple candidates start with key color → ambiguous selection
        key = full_grid(h, 2, 0); key[1][1] = 4
        candidates = []
        for color in [4, 4, 6]:
            p = full_grid(h, w, 0); p[1][1] = color
            candidates.append(p)
        return assemble_vertical_panels([key] + candidates)
    return full_grid(h, w, 0)
