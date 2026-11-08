"""Generator for 54dc2872 — multicolor corner shape moves to matching singleton marker.

Rule: each 2x2 multicolor shape has 3 body-color cells + 1 special-color
corner. A standalone singleton in the special color sits elsewhere.
For each shape: find its missing-body-corner direction; move the shape
so the corresponding diagonally-opposite corner lands at the marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00dc84bcd438"
VERSION = "2.1.1"
TASK_ID = "00dc84bcd438"
SUMMARY = (
    "0-bg grid with N (1-4) multicolor 2×2 shapes, each composed of 3 "
    "body-color cells and 1 special-color cell at one of the 2×2 "
    "corners (TL/TR/BL/BR). Each shape's special color is unique. "
    "For each shape, a matching singleton in the special color sits "
    "elsewhere on the grid. Rule: for each shape, identify which "
    "corner is the special. Compute the diagonally OPPOSITE corner "
    "and use it as the shape's 'anchor'. Move the whole shape so "
    "this anchor lands at the singleton marker. The shape is erased "
    "at its original position and redrawn at the new position. "
    "Markers and bg cells are unaffected except where the moved shape "
    "now lands."
)

# Rivals: 'output is input' refuted by demos (shapes move). 'shapes
# don't move' refuted. 'use color 5 for moved cells' refuted by demos
# preserving body and special colors. 'shapes overlap markers without
# moving' refuted. 'move shape so special-color cell lands at marker'
# refuted by demos showing the OPPOSITE corner lands at marker. 4
# demos with shapes in different corner orientations (TL/TR/BL/BR) and
# scattered markers pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 multicolor 2×2 shape (3 body + 1 special-color corner)",
    "for each shape, exactly one matching singleton marker (same color as special) elsewhere",
    "body and special colors are distinct and non-zero",
    "shape body colors are distinct across shapes (so no merging in the output)",
    "markers don't overlap shapes; markers are clear of obstacles",
    "every shape's DESTINATION footprint is in-bounds (paint-cells clips OOB "
    "silently — border markers would truncate the moved shape) and disjoint "
    "from other shapes, markers, and other destinations",
    "no orphan markers: a marker is only placed when its shape was placed",
]

CORNERS = ("tl", "tr", "bl", "br")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shape", "no_marker", "full_grid")
HELPFUL_TEXTURES = CORNERS

AXES = {
    "grid_h":   {"type": "int", "default": "rng 11..14 (easy 9..11, hard 14..18)",
                 "valid": "8..18", "doc": "Grid height."},
    "grid_w":   {"type": "int", "default": "rng 11..14 (easy 9..11, hard 14..18)",
                 "valid": "8..18", "doc": "Grid width."},
    "n_shapes": {"type": "int", "default": "rng 2..3 (easy 1, hard 3..4)",
                 "valid": "1..4", "doc": "2x2 shapes, each with its own marker."},
    "texture":  {"type": "str", "default": "helpful",
                 "valid": "tl|tr|bl|br|no_shape|no_marker|full_grid",
                 "doc": "Corner choice or a degenerate name."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_shapes = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n_shapes = rng.randint(3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_shapes = rng.randint(2, 3)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(8, 2 * n_shapes))
    placed = []  # (top, left)
    dest_taken = set()  # cells claimed by some shape's destination footprint
    forced_corner = overrides.get("texture") if overrides.get("texture") in CORNERS else None
    for i in range(n_shapes):
        body = palette[2 * i]
        special = palette[2 * i + 1]
        corner = forced_corner or rng.choice(["tl", "tr", "bl", "br"])
        # Place shape
        for _ in range(60):
            r0 = rng.randint(0, h - 2); c0 = rng.randint(0, w - 2)
            # Check 2x2 + buffer free
            ok = True
            for dr in range(-1, 3):
                for dc in range(-1, 3):
                    nr, nc = r0 + dr, c0 + dc
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            # Paint
            for dr in range(2):
                for dc in range(2):
                    g[r0 + dr][c0 + dc] = body
            corner_offsets = {"tl": (0, 0), "tr": (0, 1), "bl": (1, 0), "br": (1, 1)}
            sr, sc = corner_offsets[corner]
            g[r0 + sr][c0 + sc] = special
            placed.append((r0, c0))
            break
        if not placed or placed[-1] != (r0, c0):
            continue  # shape failed to place: skip its marker (no orphans)

        # Marker for this shape's special color. The rule moves the shape
        # so the corner OPPOSITE the special lands at the marker, so the
        # destination 2x2 footprint extends away from the marker:
        #   special tl -> anchor br -> footprint rows mr-1..mr, cols mc-1..mc
        anchor_off = {"tl": (1, 1), "tr": (1, 0), "bl": (0, 1), "br": (0, 0)}
        ar, ac = anchor_off[corner]
        for _ in range(80):
            mr = rng.randint(0, h - 1); mc = rng.randint(0, w - 1)
            if g[mr][mc] != 0 or (mr, mc) in dest_taken:
                continue  # never under an earlier shape's landing zone
            # destination footprint: anchor cell lands at (mr, mc)
            dr0, dc0 = mr - ar, mc - ac
            if not (0 <= dr0 and dr0 + 1 < h and 0 <= dc0 and dc0 + 1 < w):
                continue  # would be clipped by paint-cells
            dest = {(dr0 + a, dc0 + b) for a in range(2) for b in range(2)}
            if dest & dest_taken:
                continue  # two shapes landing on the same cells
            # destination must not cover other shapes/markers (its own
            # original cells are erased first, so self-overlap is fine)
            own = {(r0 + a, c0 + b) for a in range(2) for b in range(2)}
            if any(g[r][c] != 0 and (r, c) not in own for r, c in dest):
                continue
            # marker must not touch any existing non-zero cell
            if any(0 <= mr + a < h and 0 <= mc + b < w and g[mr + a][mc + b] != 0
                   for a in (-1, 0, 1) for b in (-1, 0, 1)):
                continue
            g[mr][mc] = special
            dest_taken |= dest
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 fully-filled 2x2 multicolor shape (3 body + 1 special corner)
    and at least one isolated singleton cell (marker)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    # Find fully-filled 2x2 blocks with exactly 2 distinct colors (3 body + 1 special)
    shapes_found = False
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            if all(v != 0 for v in vals) and len(set(vals)) == 2:
                shapes_found = True
                break
        if shapes_found:
            break
    if not shapes_found:
        msgs.append("no 2x2 block found with all 4 cells nonzero and exactly 2 distinct colors")
    # Find isolated singletons (each connected to no other nonzero cell)
    singletons = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            neighbors = [grid[r + dr][c + dc]
                         for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                         if 0 <= r + dr < h and 0 <= c + dc < w]
            if not any(v != 0 for v in neighbors):
                singletons += 1
    if singletons == 0:
        msgs.append("no isolated singleton cell (marker) found")
    return msgs


def _draw_from_degenerate(name, rng):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_shape  — markers only: nothing matches them, grid unchanged.
    no_marker — a shape with no singleton in its special color: the
                rule finds no target and leaves the shape in place.
    full_grid — one solid color: a single one-color component, no move.
    """
    h, w = rng.randint(8, 12), rng.randint(8, 12)
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    if name == "no_shape":
        for color in colors[:rng.randint(1, 3)]:
            g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = color
        return g
    if name == "no_marker":
        r0 = rng.randint(0, h - 2); c0 = rng.randint(0, w - 2)
        for dr in range(2):
            for dc in range(2):
                g[r0 + dr][c0 + dc] = colors[0]
        sr, sc = rng.choice(((0, 0), (0, 1), (1, 0), (1, 1)))
        g[r0 + sr][c0 + sc] = colors[1]
        return g
    # full_grid
    color = colors[0]
    for r in range(h):
        for c in range(w):
            g[r][c] = color
    return g
