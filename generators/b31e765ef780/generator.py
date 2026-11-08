"""Generator for arc_puzzle_bank_21_set13_s:S13_E1 — holed objects → 8.

Rule: holed connected components (those with an enclosed bg hole) are
recolored to 8; solid distractors keep their colors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid (no holed components → rule recolors nothing,
output equals input), all_holed (no solid distractors → rule recolors
everything to 8, no contrast), single_object (one component only →
no contrast between holed/solid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b31e765ef780"
VERSION = "2.0.1"
TASK_ID = "b31e765ef780"
SUMMARY = (
    "0-bg grid (h~11-14, w~13-16) containing "
    "two kinds of CONNECTED COMPONENTS, each in "
    "a DISTINCT non-zero color: (a) 1-2 HOLED "
    "OBJECTS — frame-shaped polyominoes with "
    "an ENCLOSED 0-CELL HOLE inside (3x3 "
    "donut, 3x4 rect outline); (b) 2 SOLID "
    "DISTRACTOR objects — small polyominoes "
    "without enclosed holes. Objects are "
    "non-touching with 1-cell padding. Rule: "
    "for EACH connected component, check if it "
    "has an ENCLOSED 0-CELL inside its bbox "
    "(a bg cell that cannot reach the grid "
    "border via 4-conn through other 0 cells "
    "without crossing this component). If "
    "YES (holed), RECOLOR every cell of that "
    "component to COLOR 8 (cyan). If NO "
    "(solid), leave it unchanged. Net: holed "
    "blobs become cyan; solid blobs keep their "
    "color."
)

INVARIANTS = [
    "background is 0",
    "there is at least one connected component with an enclosed zero hole",
    "there is at least one non-holed distractor component",
    "outputs preserve the grid size and recolor only holed components",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "all_holed", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":            {"type": "int", "default": "rng 11..14", "valid": "9..17"},
    "width":             {"type": "int", "default": "rng 13..16", "valid": "10..19"},
    "holed_count":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "scattered_holed_and_solid",
                          "valid": "scattered_holed_and_solid"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-bg colors;
    at least 1 component has an enclosed bg hole (hollow), at least 1 is solid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-bg colors; found {sorted(colors)}")
        return errs
    # BFS to check if any bg cell inside a component bbox is non-border-reachable
    # Simple proxy: check for 0-cells surrounded on all 4 sides by non-0 cells at ≥1 hop
    def border_reachable(r0, c0):
        if r0 == 0 or r0 == h - 1 or c0 == 0 or c0 == w - 1:
            return True
        q = [(r0, c0)]
        seen = {(r0, c0)}
        while q:
            r, c = q.pop()
            if r == 0 or r == h - 1 or c == 0 or c == w - 1:
                return True
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) not in seen and 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return False
    has_hole = any(grid[r][c] == 0 and not border_reachable(r, c)
                   for r in range(h) for c in range(w))
    if not has_hole:
        errs.append("expected ≥1 component with enclosed bg hole (hollow object); none found")
    return errs


_HOLED = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)],
]
_SOLID = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(160):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place object")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 11, 12)
        w = ctx.draw_int("width", 13, 14)
        holed_count = ctx.draw_int("holed_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 16)
        w = ctx.draw_int("width", 15, 18)
        holed_count = ctx.draw_int("holed_count", 2, 3)
    else:
        h = ctx.draw_int("height", 11, 14)
        w = ctx.draw_int("width", 13, 16)
        holed_count = ctx.draw_int("holed_count", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [2, 3, 4, 6]
    rng.shuffle(colors)
    for i in range(holed_count):
        _place(g, rng, rng.choice(_HOLED), colors[i])
    for color in colors[holed_count:holed_count + 2]:
        _place(g, rng, rng.choice(_SOLID), color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "all_solid":
        # No holed components — rule's recolor selector finds nothing,
        # output equals input exactly.
        for dr, dc in _SOLID[0]:
            g[1 + dr][1 + dc] = 2
        for dr, dc in _SOLID[1]:
            g[5 + dr][6 + dc] = 3
        for dr, dc in _SOLID[2]:
            g[8 + dr][2 + dc] = 4
        return g
    if name == "all_holed":
        # All components are holed — rule recolors every component
        # to 8, no contrast between holed/non-holed remains.
        for dr, dc in _HOLED[0]:
            g[1 + dr][1 + dc] = 2
        for dr, dc in _HOLED[0]:
            g[1 + dr][7 + dc] = 3
        for dr, dc in _HOLED[1]:
            g[6 + dr][1 + dc] = 4
        return g
    if name == "single_object":
        # Only one component — no holed/solid contrast in the output;
        # rule's discriminative behavior is invisible.
        for dr, dc in _HOLED[1]:
            g[3 + dr][4 + dc] = 6
        return g
    return g
