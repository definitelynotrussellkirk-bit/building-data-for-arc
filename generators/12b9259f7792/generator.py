"""Generator for arc_additional_puzzle_bank_volume5:M31 — recolor 5-blobs by nearest marker.

Rule: for each color-5 component, find the marker color in {1,2,3,4}
with minimum Manhattan distance to any component cell and recolor the
component with that marker color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "12b9259f7792"
VERSION = "2.1.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "0-background grid with 2-4 distinct single-cell markers in colors 1..4 "
    "and 2-4 separated color-5 blobs. Recolor each blob to the color of its "
    "unique nearest marker under minimum Manhattan cell distance."
)

INVARIANTS = [
    "2-4 markers, each a distinct color in {1,2,3,4}",
    "2-4 color-5 blobs, each strictly closest to one marker",
    "blobs are separated so each is its own component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_blobs", "blob_equidistant_to_two_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "n_blobs": {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size": {"type": "int", "default": "4", "valid": "4"},
    "position_bias": {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..4"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied|no_markers|no_blobs|blob_equidistant_to_two_markers"},
}


def _normalized_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    values = dict(overrides)
    texture = values.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture: {texture!r}")
    if texture in HELPFUL_TEXTURES:
        if values.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind aliases disagree")
        values["palette_kind"] = texture
    return values


def _random_poly(rng, size, maxd=3):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            cells.add((r + dr, c + dc))
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if max(r for r, _ in norm) < maxd and max(c for _, c in norm) < maxd:
            return norm
    raise ValueError("could not grow a compact blob")


def _free(occupied, cells, h, w):
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and occupied[rr][cc]:
                    return False
    return True


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = rr + dr, cc + dc
                    if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt not in seen and grid[nxt[0]][nxt[1]] == color:
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(sorted(cells))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be exact ARC colors"]
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4)]
    blobs = _components_of_color(grid, 5)
    if not markers or not blobs:
        return []  # explicitly supported degenerate fixtures
    errors = []
    colors = [color for _, _, color in markers]
    if len(colors) != len(set(colors)):
        errors.append("marker colors must be distinct")
    for cells in blobs:
        distances = sorted(
            min(abs(r - mr) + abs(c - mc) for r, c in cells)
            for mr, mc, _ in markers
        )
        if len(distances) > 1 and distances[0] == distances[1]:
            errors.append("a color-5 blob is tied between nearest markers")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _normalized_overrides(overrides)
    texture = values.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, None)

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=values)
    if difficulty == "easy":
        hr, wr, mk_range, blob_range = (8, 10), (9, 11), (2, 2), (2, 2)
    elif difficulty == "hard":
        hr, wr, mk_range, blob_range = (12, 16), (12, 16), (4, 4), (3, 4)
    else:
        hr, wr, mk_range, blob_range = (9, 12), (10, 13), (2, 3), (2, 3)

    h = ctx.draw_int_strict("grid_h", 8, 16) if "grid_h" in values else ctx.draw_int_strict("grid_h", *hr)
    w = ctx.draw_int_strict("grid_w", 9, 16) if "grid_w" in values else ctx.draw_int_strict("grid_w", *wr)
    n_markers = (ctx.draw_int_strict("n_distinct_colors", 2, 4)
                 if "n_distinct_colors" in values else ctx.draw_int_strict("n_distinct_colors", *mk_range))
    n_blobs = (ctx.draw_int_strict("n_blobs", 2, 4)
               if "n_blobs" in values else ctx.draw_int_strict("n_blobs", *blob_range))
    ctx.draw_int_strict("palette_size", 4, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("position_bias", ("varied",))
    ctx.draw_choice("density", ("sparse",))
    rng = ctx.draw_rng("layout")

    base_palettes = {
        "default": [1, 2, 3, 4],
        "warm": [2, 4, 1, 3],
        "cool": [1, 3, 2, 4],
        "varied": [1, 2, 3, 4],
    }
    palette = list(base_palettes[palette_kind])
    if palette_kind == "varied":
        rng.shuffle(palette)

    for _attempt in range(120):
        occupied = [[False] * w for _ in range(h)]
        marker_colors = rng.sample(palette, n_markers)
        markers = []
        for color in marker_colors:
            for _ in range(120):
                r, c = rng.randrange(h), rng.randrange(w)
                if all(abs(r - mr) + abs(c - mc) >= 4 for mr, mc, _ in markers):
                    markers.append((r, c, color))
                    occupied[r][c] = True
                    break
            else:
                break
        if len(markers) != n_markers:
            continue

        def nearest_unique(cells):
            ranked = sorted(
                (min(abs(r - mr) + abs(c - mc) for r, c in cells), color)
                for mr, mc, color in markers
            )
            if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
                return None
            return ranked[0][1]

        grid = full_grid(h, w, 0)
        for r, c, color in markers:
            grid[r][c] = color
        placed = 0
        for _ in range(n_blobs):
            target_r, target_c, _ = rng.choice(markers)
            success = False
            for _ in range(160):
                shape = _random_poly(rng, rng.randint(2, 4))
                top = max(0, min(h - 3, target_r + rng.randint(-4, 4)))
                left = max(0, min(w - 3, target_c + rng.randint(-4, 4)))
                cells = [(top + r, left + c) for r, c in shape]
                if not _free(occupied, cells, h, w) or nearest_unique(cells) is None:
                    continue
                for r, c in cells:
                    grid[r][c] = 5
                    occupied[r][c] = True
                placed += 1
                success = True
                break
            if not success:
                break
        if placed == n_blobs and self_check(grid) == []:
            return grid
    raise ValueError("could not place the requested nearest-marker scene")


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    grid = full_grid(h, w, 0)
    if name == "no_markers":
        paint_at(grid, 2, 1, [(0, 0), (1, 0), (1, 1)], 5)
        paint_at(grid, h - 3, w // 2, [(0, 0), (0, 1), (1, 0)], 5)
    elif name == "no_blobs":
        grid[0][0] = 1
        grid[0][w - 1] = 2
        grid[h - 1][w - 1] = 3
    elif name == "blob_equidistant_to_two_markers":
        grid[0][0] = 1
        grid[0][w - 1] = 2
        paint_at(grid, 0, w // 2, [(0, 0), (1, 0)], 5)
    return grid
