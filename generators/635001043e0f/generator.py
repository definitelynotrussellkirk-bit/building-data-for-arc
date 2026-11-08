"""Generator for dc2e9a9d.

Rule: each color-3 object is a hollow rectangular frame with a single-cell
tab on exactly one bbox edge. The canonical rule mirrors the whole object
away from that tab: vertical-tab objects paint the copy in color 8, and
horizontal-tab objects paint the copy in color 1.

Combinatorial axes: grid size, object count, tab direction, frame size, and
object placement.
Degenerates: no_objects, symmetric_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "635001043e0f"
VERSION = "2.1.0"
TASK_ID = "635001043e0f"
SUMMARY = (
    "0-bg grid with 1-3 canonical-style color-3 tabbed hollow rectangles. "
    "Each object has one single-cell tab on exactly one bbox edge and a wider "
    "base on the opposite edge. The rule mirrors the object away from that tab, "
    "painting vertical-tab copies color 8 and horizontal-tab copies color 1."
)

INVARIANTS = [
    "every source object is color 3, matching the canonical task palette",
    "each object is a hollow rectangular frame with exactly one outward tab",
    "the mirrored copy region beyond the base is reserved empty and in-bounds",
    "vertical tabs stamp in color 8; horizontal tabs stamp in color 1",
]

PALETTE_KINDS = ("default", "canonical")
DEGENERATE_TEXTURES = ("no_objects", "symmetric_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "canonical-like", "valid": "16..28"},
    "grid_w":         {"type": "int", "default": "canonical-like", "valid": "15..26"},
    "n_objects":      {"type": "int", "default": "2..3", "valid": "1..4"},
    "direction":      {"type": "str", "default": "varies", "valid": "up|down|left|right"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "objects_apart", "valid": "objects_apart"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "canonical",
                       "valid": "default|canonical|no_objects|symmetric_object|full_grid"},
}


def _frame_outline(r0, c0, fh, fw):
    cells = set()
    for c in range(c0, c0 + fw):
        cells.add((r0, c))
        cells.add((r0 + fh - 1, c))
    for r in range(r0, r0 + fh):
        cells.add((r, c0))
        cells.add((r, c0 + fw - 1))
    return cells


def _tabbed_mask(direction, fh, fw):
    """Return normalized cells for a hollow frame plus a one-cell outward tab."""
    cells = set()
    if direction == "up":
        tab_c = fw // 2
        cells.add((0, tab_c))
        cells |= _frame_outline(1, 0, fh, fw)
    elif direction == "down":
        tab_c = fw // 2
        cells |= _frame_outline(0, 0, fh, fw)
        cells.add((fh, tab_c))
    elif direction == "left":
        tab_r = fh // 2
        cells.add((tab_r, 0))
        cells |= _frame_outline(0, 1, fh, fw)
    else:  # right
        tab_r = fh // 2
        cells |= _frame_outline(0, 0, fh, fw)
        cells.add((tab_r, fw))
    return sorted(cells)


def _copy_cells(ocells, direction):
    rs = [r for r, c in ocells]; cs = [c for r, c in ocells]
    r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
    bh = r1 - r0 + 1; bw = c1 - c0 + 1
    out = []
    for (pr, pc) in ocells:
        if direction == "up":
            out.append(((r0 + r1 - pr) + bh + 1, pc))
        elif direction == "down":
            out.append(((r0 + r1 - pr) - bh - 1, pc))
        elif direction == "left":
            out.append((pr, (c0 + c1 - pc) + bw + 1))
        else:  # right
            out.append((pr, (c0 + c1 - pc) - bw - 1))
    return out


def _reserve(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, nr, size_rng = (16, 20), (15, 19), (1, 2), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, size_rng = (22, 28), (20, 26), (3, 4), (3, 5)
    else:
        hr, wr, nr, size_rng = (20, 24), (17, 22), (2, 3), (3, 5)

    for _attempt in range(120):
        h = ctx.draw_int("grid_h", *hr)
        w = ctx.draw_int("grid_w", *wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        target = rng.randint(*nr)
        for _ in range(target):
            direction = rng.choice(["up", "down", "left", "right"])
            fh = rng.randint(*size_rng)
            fw = rng.randint(*size_rng)
            shape = _tabbed_mask(direction, fh, fw)
            sh = max(r for r, c in shape) + 1
            sw = max(c for r, c in shape) + 1
            for _t in range(120):
                top = rng.randint(0, h - sh)
                left = rng.randint(0, w - sw)
                obj = [(top + r, left + c) for r, c in shape]
                copy = _copy_cells(obj, direction)
                if all(0 <= r < h and 0 <= c < w for r, c in copy) and _reserve(occ, obj + copy, h, w):
                    for r, c in obj:
                        g[r][c] = 3
                    placed += 1
                    break
        if placed == target and placed >= nr[0]:
            return g

    raise ValueError("could not realize tabbed-object layout with reserved mirror copies")


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_objects":
        return g
    if name == "symmetric_object":
        for (r, c) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
            g[r][c] = 3          # square -> no single tab -> no stamp
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 3
        return g
    return g


def _nonzero_components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _tab_direction(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
    topn = sum(1 for r, _ in cells if r == r0)
    botn = sum(1 for r, _ in cells if r == r1)
    leftn = sum(1 for _, c in cells if c == c0)
    rightn = sum(1 for _, c in cells if c == c1)
    dirs = []
    if topn == 1 and botn > 1:
        dirs.append("up")
    if botn == 1 and topn > 1:
        dirs.append("down")
    if leftn == 1 and rightn > 1:
        dirs.append("left")
    if rightn == 1 and leftn > 1:
        dirs.append("right")
    return dirs


def _is_hollow_tabbed_object(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0, r1, c1 = min(rs), min(cs), max(rs), max(cs)
    norm = {(r - r0, c - c0) for r, c in cells}
    h, w = r1 - r0 + 1, c1 - c0 + 1
    for direction in ("up", "down", "left", "right"):
        for fh in range(3, 6):
            for fw in range(3, 6):
                mask = set(_tabbed_mask(direction, fh, fw))
                if max(r for r, _ in mask) + 1 == h and max(c for _, c in mask) + 1 == w and norm == mask:
                    return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    vals = {v for row in grid for v in row}
    if not vals <= {0, 3}:
        errors.append(f"unexpected source colors: {sorted(vals - {0, 3})}")
    comps = _nonzero_components(grid)
    if not comps:
        return ["no tabbed source object"]
    if len(comps) > 4:
        errors.append(f"too many source objects: {len(comps)}")
    directions = []
    h, w = len(grid), len(grid[0])
    for color, cells in comps:
        if color != 3:
            errors.append(f"source object color should be 3, got {color}")
        dirs = _tab_direction(cells)
        if len(dirs) != 1:
            errors.append(f"object does not have exactly one single-tab edge: dirs={dirs}")
            continue
        directions.extend(dirs)
        if not _is_hollow_tabbed_object(cells):
            errors.append("object is not a canonical hollow rectangle plus one-cell tab")
        copy = _copy_cells(cells, dirs[0])
        if not all(0 <= r < h and 0 <= c < w for r, c in copy):
            errors.append("mirrored copy would leave the grid")
        if any(grid[r][c] != 0 for r, c in copy if 0 <= r < h and 0 <= c < w):
            errors.append("mirrored copy region is not empty")
    if directions and not ({"up", "down"} & set(directions) or {"left", "right"} & set(directions)):
        errors.append("unreachable")
    return errors
