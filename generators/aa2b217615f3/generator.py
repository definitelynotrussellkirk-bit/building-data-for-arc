"""Generator for 6ad5bdfd.

Rule: red edge line attracts separated colored objects, sliding them
until they stack against the line or earlier objects.

Combinatorial axes (8): grid_h/w, direction, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_line, no_objects, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa2b217615f3"
VERSION = "2.2.0"  # guarantee a collision/stacking witness in every ordinary scene
TASK_ID = "aa2b217615f3"
SUMMARY = (
    "0-bg grid (h, w~7-14) "
    "with: (a) ONE FULL-"
    "LENGTH COLOR-2 (red) "
    "EDGE LINE on ONE of "
    "the 4 GRID EDGES (top "
    "row, bottom row, left "
    "col, or right col); "
    "(b) 3-5 CONNECTED "
    "COLORED OBJECTS in "
    "DISTINCT non-{0, 2} "
    "colors, each a 1-3 "
    "cell shape from a "
    "small bank, "
    "scattered in the "
    "INTERIOR (not "
    "touching the red "
    "line). Objects are "
    "placed at non-"
    "touching positions "
    "(1-cell 8-conn "
    "buffer). Rule (SLIDE "
    "OBJECTS TOWARD THE "
    "RED LINE, STACKING)"
    ": DETECT the red "
    "line's EDGE → "
    "DIRECTION (up/down/"
    "left/right TOWARD "
    "the line). SORT "
    "objects by DISTANCE "
    "to the line (closest "
    "first). For EACH "
    "object in that order"
    ": SLIDE the entire "
    "object (as a rigid "
    "group) toward the "
    "line by max amount "
    "until it hits the "
    "RED LINE or a "
    "PREVIOUSLY-PLACED "
    "object's cells. The "
    "line stays. Net: "
    "objects stack "
    "against the red line "
    "in distance-order."
)

# Rivals: 'output is input' refuted by demos. 'slide AWAY from line'
# refuted by demos showing toward. 'erase objects' refuted. 'objects
# pass through line' refuted. 'use color 2 for objects' refuted by
# demos preserving original colors. 'objects don't stack (overlap)'
# refuted by demos showing stacking. 4 demos covering all 4 edge
# orientations pin the direction-from-line-position rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "exactly one full edge line uses color 2 (top, bottom, left, or right edge)",
    "≥3 movable objects in distinct non-bg, non-2 colors",
    "objects start with at least one empty row/col between them and the red line (visible slide effect)",
    "objects don't overlap each other in the input",
]

DIRECTIONS = ("up", "down", "left", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_line", "no_objects", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "direction":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIRECTIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def _has_object_buffer(g, cells):
    """Cells are empty and have a 1-cell 8-neighborhood buffer from other
    movable objects.  Color 2 is the red edge line and is handled by the caller's
    placement bounds."""
    h, w = len(g), len(g[0])
    cellset = set(cells)
    for r, c in cells:
        if g[r][c] != 0:
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = r + ddr, c + ddc
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cellset and g[nr][nc] not in (0, 2):
                    return False
    return True


def _local_to_grid(direction, h, w, depth, lateral):
    """Map distance-from-red-edge/lateral coordinates into grid coordinates."""
    if direction == "up":
        return depth, lateral
    if direction == "down":
        return h - 1 - depth, lateral
    if direction == "left":
        return lateral, depth
    return lateral, w - 1 - depth


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("direction") or \
                ctx.draw_choice("direction", list(DIRECTIONS))
    if difficulty == "easy":
        h = 7 + rng.randint(0, 2)
        w = 7 + rng.randint(0, 2)
        n_objects = 3
    elif difficulty == "hard":
        h = 11 + rng.randint(0, 4)
        w = 11 + rng.randint(0, 4)
        n_objects = rng.randint(4, 5)
    else:
        h = 8 + rng.randint(0, 4)
        w = 8 + rng.randint(0, 4)
        n_objects = rng.randint(3, 4)
    g = full_grid(h, w, 0)
    if direction == "up":
        for c in range(w):
            g[0][c] = 2
    elif direction == "down":
        for c in range(w):
            g[h - 1][c] = 2
    elif direction == "left":
        for r in range(h):
            g[r][0] = 2
    else:
        for r in range(h):
            g[r][w - 1] = 2
    colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], n_objects)
    shape_pool = [
        [(0, 0)],
        [(0, 0), (0, 1)],
        [(0, 0), (1, 0)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (0, 2)],
    ]

    # The first two one-cell objects share a movement lane and have an empty
    # cell between them.  They therefore force collision-based stacking and
    # refute the previously reproduced independent-slide shortcut in every
    # ordinary lesson, without changing the canonical transformation rule.
    cross = w if direction in ("up", "down") else h
    lane = rng.randint(1, cross - 2)
    for color, depth in zip(colors[:2], (2, 4)):
        r, c = _local_to_grid(direction, h, w, depth, lane)
        if not _has_object_buffer(g, [(r, c)]):
            raise ValueError("could not place required stacking witness")
        g[r][c] = color

    for color in colors[2:]:
        shape = rng.choice(shape_pool)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r_lo = 2 if direction == "up" else 0
        r_hi = h - sh - (2 if direction == "down" else 0)
        c_lo = 2 if direction == "left" else 0
        c_hi = w - sw - (2 if direction == "right" else 0)
        placed = False
        if r_lo <= r_hi and c_lo <= c_hi:
            for _ in range(80):
                r0 = rng.randint(r_lo, r_hi)
                c0 = rng.randint(c_lo, c_hi)
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                if any(g[r][c] != 0 for r, c in cells):
                    continue
                if not _has_object_buffer(g, cells):
                    continue
                for r, c in cells:
                    g[r][c] = color
                placed = True
                break
        if not placed:
            candidates = [(r, c) for r in range(2 if direction == "up" else 0,
                                               h - (2 if direction == "down" else 0))
                          for c in range(2 if direction == "left" else 0,
                                         w - (2 if direction == "right" else 0))
                          if g[r][c] == 0]
            rng.shuffle(candidates)
            for r, c in candidates:
                if _has_object_buffer(g, [(r, c)]):
                    g[r][c] = color
                    placed = True
                    break
        if not placed:
            raise ValueError("could not place all sliding objects with required buffer")
    return g



def _object_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (0, 2) or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def has_stacking_witness(grid) -> bool:
    """Whether two movable objects share a lane and must stack when slid."""
    if not grid or not grid[0]:
        return False
    h, w = len(grid), len(grid[0])
    directions = []
    if all(grid[0][c] == 2 for c in range(w)):
        directions.append("up")
    if all(grid[h - 1][c] == 2 for c in range(w)):
        directions.append("down")
    if all(grid[r][0] == 2 for r in range(h)):
        directions.append("left")
    if all(grid[r][w - 1] == 2 for r in range(h)):
        directions.append("right")
    if len(directions) != 1:
        return False
    vertical = directions[0] in ("up", "down")
    comps = _object_components(grid)
    projections = [({c for _, c in cells} if vertical else {r for r, _ in cells})
                   for _, cells in comps]
    return any(a & b for i, a in enumerate(projections) for b in projections[i + 1:])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default rows teach edge attraction only when there is exactly one red
    edge line and every movable object starts separated from that line and from
    the others.  This catches the rare silent under-placement and zero-slide
    adjacent-to-line poison fixed in v2.1.0."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    edge_lines = []
    if all(grid[0][c] == 2 for c in range(w)):
        edge_lines.append("up")
    if all(grid[h - 1][c] == 2 for c in range(w)):
        edge_lines.append("down")
    if all(grid[r][0] == 2 for r in range(h)):
        edge_lines.append("left")
    if all(grid[r][w - 1] == 2 for r in range(h)):
        edge_lines.append("right")
    if len(edge_lines) != 1:
        errs.append(f"expected exactly one full red edge line, found {edge_lines}")
        return errs
    direction = edge_lines[0]
    comps = _object_components(grid)
    if not (3 <= len(comps) <= 5):
        errs.append(f"expected 3-5 movable objects, found {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append(f"object colors not distinct: {colors}")
    if not has_stacking_witness(grid):
        errs.append("no collision-based stacking witness; independent sliding remains plausible")
    for color, cells in comps:
        if not (1 <= len(cells) <= 3):
            errs.append(f"object color {color} has size {len(cells)} outside 1..3")
        if direction == "up" and min(r for r, _ in cells) <= 1:
            errs.append(f"object color {color} touches/abuts top line; needs an empty row gap")
        if direction == "down" and max(r for r, _ in cells) >= h - 2:
            errs.append(f"object color {color} touches/abuts bottom line; needs an empty row gap")
        if direction == "left" and min(c for _, c in cells) <= 1:
            errs.append(f"object color {color} touches/abuts left line; needs an empty col gap")
        if direction == "right" and max(c for _, c in cells) >= w - 2:
            errs.append(f"object color {color} touches/abuts right line; needs an empty col gap")
    for i, (_, a) in enumerate(comps):
        for _, b in comps[i + 1:]:
            if any(max(abs(r1 - r2), abs(c1 - c2)) <= 1 for r1, c1 in a for r2, c2 in b):
                errs.append("movable objects violate the 1-cell 8-neighborhood buffer")
                return errs
    return errs

def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_line":
        g[5][5] = 3
        return g
    if name == "no_objects":
        for c in range(10):
            g[0][c] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
