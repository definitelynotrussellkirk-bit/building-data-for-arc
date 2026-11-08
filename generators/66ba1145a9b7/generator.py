"""Generator for arc_puzzle_bank_21_set6_s:S6_E1 — recolor red-attached blue wire.

A red marker selects the attached blue wire; only that wire recolors green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (no red marker → rule's selector returns
nothing, no wire chosen), no_attached_wire (red marker has no
adjacent blue cell → rule's wire-from-marker selector finds nothing),
all_strays (no red marker, only stray blue components → rule has no
selection criterion, output undefined).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "66ba1145a9b7"
VERSION = "1.2.0"
TASK_ID = "66ba1145a9b7"

SUMMARY = "Red(2) marker + attached blue(1) wire + optional stray blue components. Rule recolors the wire reachable from the marker to green(3); strays stay blue."

# Rivals: 'recolor all blue cells' refuted by ≥1 demo with stray blue
# staying 1. 'recolor red marker too' refuted by any demo (marker
# stays 2). 'use bg color' refuted by any demo (recolor is 3).
# 'recolor only marker neighbor' refuted by ≥2 demos with wire of
# length > 1.
# 4 demos with varied wire shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "there is exactly one red start marker",
    "the marker has exactly one orthogonally adjacent blue wire",
    "the marked blue wire is non-branching",
    "stray blue components are not adjacent to the marker or marked wire",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_attached_wire", "all_strays")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":            {"type": "int", "default": "rng 9..13", "valid": "6..17"},
    "wire_shape":        {"type": "choice", "default": "rng 0..3", "valid": "0..3"},
    "stray_count":       {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "marker_attached_wire_plus_strays",
                          "valid": "marker_attached_wire_plus_strays"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PATHS = [
    [(0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4)],
    [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 4), (3, 4)],
    [(1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)],
    [(0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3), (3, 4)],
]

_STRAYS = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1)],
]


def _place_shape(g, rng, cells, color, occupied):
    h = len(g)
    w = len(g[0])
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    for _ in range(200):
        r0 = rng.randint(0, h - max_r - 1)
        c0 = rng.randint(0, w - max_c - 1)
        placed = [(r0 + r, c0 + c) for r, c in cells]
        if any(g[r][c] != 0 for r, c in placed):
            continue
        if any(abs(r - rr) + abs(c - cc) <= 1 for r, c in placed for rr, cc in occupied):
            continue
        for r, c in placed:
            g[r][c] = color
        occupied.update(placed)
        return
    raise ValueError("could not place stray component")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 11)
        stray_lo, stray_hi = 0, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 17)
        stray_lo, stray_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 14)
        stray_lo, stray_hi = 1, 3
    path = _PATHS[ctx.draw_choice("wire_shape", list(range(len(_PATHS))))]
    stray_count = ctx.draw_int("stray_count", stray_lo, stray_hi)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    max_r = max([0] + [r for r, _ in path])
    max_c = max([0] + [c for _, c in path])
    min_r = min([0] + [r for r, _ in path])
    min_c = min([0] + [c for _, c in path])
    r0 = rng.randint(1 - min_r, h - max_r - 2)
    c0 = rng.randint(1 - min_c, w - max_c - 2)
    g[r0][c0] = 2
    occupied = {(r0, c0)}
    for dr, dc in path:
        g[r0 + dr][c0 + dc] = 1
        occupied.add((r0 + dr, c0 + dc))
    for _ in range(stray_count):
        _place_shape(g, rng, rng.choice(_STRAYS), 1, occupied)
    return g


def _blue_components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != 1:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 1:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Executable normal-path invariants for the marked-wire recolor task."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(reds) != 1:
        return ["normal sample must contain exactly one red marker"]
    marker = reds[0]
    adj = [(marker[0] + dr, marker[1] + dc)
           for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
           if 0 <= marker[0] + dr < h and 0 <= marker[1] + dc < w
           and grid[marker[0] + dr][marker[1] + dc] == 1]
    if len(adj) != 1:
        errors.append("red marker must touch exactly one blue wire cell")
    blue_components = _blue_components(grid)
    if adj:
        marked = next((cells for cells in blue_components if adj[0] in cells), [])
        if len(marked) <= 1:
            errors.append("marked blue wire must have length > 1")
        marked_set = set(marked)
        for cell in marked:
            deg = sum((cell[0] + dr, cell[1] + dc) in marked_set
                      for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)])
            if deg > 2:
                errors.append("marked blue wire must be non-branching")
                break
        for stray in blue_components:
            if stray is marked:
                continue
            if any(abs(r - rr) + abs(c - cc) <= 1
                   for r, c in stray for rr, cc in marked + [marker]):
                errors.append("stray blue components must not touch the marker or marked wire")
                break
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # No red marker — rule's selector returns nothing.
        for r, c in [(2, 2), (2, 3), (3, 3), (4, 3)]: g[r][c] = 1
        for r, c in [(5, 7), (5, 8)]: g[r][c] = 1
        return g
    if name == "no_attached_wire":
        # Red marker is isolated from any blue cells.
        g[2][2] = 2
        for r, c in [(5, 7), (5, 8), (6, 7)]: g[r][c] = 1
        return g
    if name == "all_strays":
        # No red marker, only stray blue components — rule has no
        # selection criterion.
        for r, c in [(2, 2), (2, 3)]: g[r][c] = 1
        for r, c in [(5, 7), (5, 8), (6, 7)]: g[r][c] = 1
        return g
    return g
