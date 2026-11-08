"""Generator for arc_puzzle_bank_21_set5_s:S5_E5 — crop red border-toucher.

Among red objects, crop the one that touches the grid border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_border_touch (no red touches the border → rule's
selector finds nothing, output undefined), all_border_touch (every
red touches the border → tie-break decides which one to crop, no
contrast), single_object (only one red object, trivially the
border-toucher → no candidate contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7768dfc99e25"
VERSION = "2.0.1"  # distinct=3/shape-locked-out: border shape from a 3-shape bank -> 3 cropped outputs. Output = the border-touching red objects crop. Use a RANDOM polyomino (3-7 cells) flush against the chosen edge -> output varies widely incl non-square.
TASK_ID = "7768dfc99e25"
RULE_HASH = "be1e3a1eb944"

SUMMARY = "Among red objects, crop the one that touches the grid border."

INVARIANTS = [
    "background is 0",
    "there are multiple red objects",
    "exactly one red object touches the outer border",
    "interior red distractors do not touch the selected border object",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_border_touch", "all_border_touch", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..10", "valid": "6..15"},
    "grid_w":            {"type": "int", "default": "rng 8..11", "valid": "6..16"},
    "border_side":       {"type": "choice", "default": "rng top|left|right|bottom",
                          "valid": "top|left|right|bottom"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 1..1", "valid": "1..1"},
    "position_bias":     {"type": "str", "default": "border_red_plus_interior_reds",
                          "valid": "border_red_plus_interior_reds"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..1", "valid": "1..1"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_border_touch|all_border_touch|single_object"},
}

_BORDER_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
]

_INTERIOR_SHAPES = [
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _components_of_color(grid, color):
    """Return 4-connected components containing exactly ``color``."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        component = {seed}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    component.add((rr, cc))
                    stack.append((rr, cc))
        components.append(component)
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify that color 2 has candidate contrast and one border selector."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    h, w = len(grid), width
    components = _components_of_color(grid, 2)
    errors = []
    if len(components) < 2:
        errors.append("at least two separate red components are required")
    border_components = [
        component
        for component in components
        if any(r == 0 or r == h - 1 or c == 0 or c == w - 1 for r, c in component)
    ]
    if len(border_components) != 1:
        errors.append("exactly one red component must touch the outer border")
    return errors


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _paint(g, cells, r0, c0, color):
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def _clear(g, cells, r0, c0, occupied):
    h = len(g)
    w = len(g[0])
    placed = [(r0 + r, c0 + c) for r, c in cells]
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in placed):
        return False
    if any(g[r][c] != 0 for r, c in placed):
        return False
    return not any(abs(r - rr) <= 1 and abs(c - cc) <= 1
                   for r, c in placed for rr, cc in occupied)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_distractors = 1; bk_lo, bk_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 13, 16)
        n_distractors = 3; bk_lo, bk_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        n_distractors = 2; bk_lo, bk_hi = 3, 7
    side = ctx.draw_choice("border_side", ["top", "left", "right", "bottom"])
    rng = ctx.draw_rng("layout")
    # The border shape (placed at an edge) plus the earlier distractors can occupy
    # the small grid (with _clear's Chebyshev-1 buffer) so a later distractor has
    # nowhere to land → its 200 per-object tries fail and the for/else raises
    # (~3/300 None). Per-object retry can't reposition the border shape or earlier
    # distractors, so reset-and-retry the whole layout, catching the ValueError:
    # outer attempt 0 replays the same border-shape/position then the same
    # distractor sequence + corner coin-flip, so every first-pass-success seed
    # returns byte-identically; only the previously-wedged seeds resample fresh
    # positions (`side` is drawn once before the loop and stays fixed). Early-
    # placement-wedging class (1a21a4a82b48/13507b4f7614).
    for _outer in range(60):
        g = full_grid(h, w, 0)
        try:
            shape = _rand_poly(rng, rng.randint(bk_lo, bk_hi))
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            if side == "top":
                r0 = 0
                c0 = rng.randint(1, w - sw - 1)
            elif side == "bottom":
                r0 = h - sh
                c0 = rng.randint(1, w - sw - 1)
            elif side == "left":
                r0 = rng.randint(1, h - sh - 1)
                c0 = 0
            else:
                r0 = rng.randint(1, h - sh - 1)
                c0 = w - sw
            _paint(g, shape, r0, c0, 2)
            occupied = {(r0 + r, c0 + c) for r, c in shape}
            for _ in range(n_distractors):
                cells = rng.choice(_INTERIOR_SHAPES)
                max_r = max(r for r, _ in cells)
                max_c = max(c for _, c in cells)
                for _attempt in range(200):
                    rr = rng.randint(1, h - max_r - 2)
                    cc = rng.randint(1, w - max_c - 2)
                    if _clear(g, cells, rr, cc, occupied):
                        _paint(g, cells, rr, cc, 2)
                        occupied.update((rr + r, cc + c) for r, c in cells)
                        break
                else:
                    raise ValueError("could not place interior red object")
            if rng.random() < 0.5:
                g[h - 1][w - 1] = 1
            return g
        except ValueError:
            continue
    raise ValueError("could not place interior red object")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_border_touch":
        # No red touches the outer border — rule's selector finds
        # nothing; output is undefined.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 2
        for dr, dc in [(0, 0), (1, 0)]:
            g[5 + dr][6 + dc] = 2
        return g
    if name == "all_border_touch":
        # Every red touches the border — tie-break decides which one
        # is cropped; no contrast.
        g[0][2] = 2; g[0][3] = 2; g[1][3] = 2
        g[h - 1][6] = 2; g[h - 2][6] = 2
        g[4][0] = 2; g[5][0] = 2
        return g
    if name == "single_object":
        # Only one red object, trivially the border-toucher — no
        # cross-candidate contrast.
        g[0][3] = 2; g[1][3] = 2; g[1][4] = 2; g[2][3] = 2
        return g
    return g
