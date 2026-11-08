"""Generator for arc_puzzle_bank_fifteenth21:M104 — crop blob, stamp at marker."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "a90d16507995"
VERSION = "2.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A connected multicolor source blob and one color-9 marker. Crop the source "
    "to its tight bounding box, clear the source, and stamp the crop with the "
    "marker as its top-left destination cell."
)

INVARIANTS = [
    "background is 0",
    "exactly one 9-cell and one connected non-9 blob",
    "the marker has room for the complete crop",
    "output contains only the stamped crop",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_blob", "marker_inside_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "blob_size": {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "palette_size": {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias": {"type": "str", "default": "blob_upper_marker_lower", "valid": "blob_upper_marker_lower"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied|no_marker|no_blob|marker_inside_blob"},
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
    aliases = [values.get("palette_size"), values.get("n_distinct_colors")]
    explicit = [v for v in aliases if v is not None]
    if len(explicit) == 2 and explicit[0] != explicit[1]:
        raise ValueError("palette_size and n_distinct_colors must agree")
    if explicit:
        values["palette_size"] = explicit[0]
        values["n_distinct_colors"] = explicit[0]
    return values


def _blob_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (0, 9) or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = rr + dr, cc + dc
                    if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt not in seen and grid[nxt[0]][nxt[1]] not in (0, 9):
                        seen.add(nxt)
                        queue.append(nxt)
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be exact ARC colors"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), width
    errors = []
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    comps = _blob_components(grid)
    if len(nines) != 1:
        errors.append(f"expected exactly 1 color-9 marker; got {len(nines)}")
    if len(comps) != 1:
        errors.append(f"expected exactly one connected non-9 blob; got {len(comps)}")
    if len(nines) == 1 and len(comps) == 1:
        mr, mc = nines[0]
        rows = [r for r, _ in comps[0]]
        cols = [c for _, c in comps[0]]
        bh, bw = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
        if mr + bh > h or mc + bw > w:
            errors.append("marker does not have room for the blob crop")
        if (mr, mc) in comps[0]:
            errors.append("marker overlaps the source blob")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _normalized_overrides(overrides)
    texture = values.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, None)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=values)
    if difficulty == "easy":
        hr, wr, size_range = (6, 7), (7, 8), (2, 3)
    elif difficulty == "hard":
        hr, wr, size_range = (8, 10), (9, 12), (4, 6)
    else:
        hr, wr, size_range = (6, 9), (7, 10), (2, 4)
    h = ctx.draw_int_strict("grid_h", 5, 14) if "grid_h" in values else ctx.draw_int_strict("grid_h", *hr)
    w = ctx.draw_int_strict("grid_w", 6, 14) if "grid_w" in values else ctx.draw_int_strict("grid_w", *wr)
    blob_size = (ctx.draw_int_strict("blob_size", 2, 6)
                 if "blob_size" in values else ctx.draw_int_strict("blob_size", *size_range))
    palette_size = ctx.draw_int_strict("palette_size", 2, 3)
    if "n_distinct_colors" in values:
        n_colors = ctx.draw_int_strict("n_distinct_colors", 2, 3)
    else:
        n_colors = palette_size
    if n_colors != palette_size:
        raise ValueError("palette_size and n_distinct_colors must agree")
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("position_bias", ("blob_upper_marker_lower",))
    ctx.draw_choice("density", ("sparse",))
    rng = ctx.draw_rng("layout")
    palettes = {
        "default": [2, 3, 4],
        "warm": [2, 4, 6],
        "cool": [1, 3, 8],
        "varied": [1, 2, 3, 4, 5, 6, 7, 8],
    }
    palette = rng.sample(palettes[palette_kind], n_colors)

    for _layout in range(160):
        grid = full_grid(h, w, 0)
        blocked = {(r, c) for r in range(h) for c in range(w) if r >= h // 2 or c >= w // 2}
        cells = grow_blob(rng, h, w, blocked, blob_size, max_attempts=240)
        if cells is None:
            continue
        cells_list = sorted(cells)
        for index, (r, c) in enumerate(cells_list):
            grid[r][c] = palette[index % n_colors]
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        bh, bw = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
        if h // 2 > h - bh or w // 2 > w - bw:
            continue
        for _ in range(160):
            mr = rng.randint(h // 2, h - bh)
            mc = rng.randint(w // 2, w - bw)
            if grid[mr][mc] == 0:
                grid[mr][mc] = 9
                if self_check(grid) == []:
                    return grid
                grid[mr][mc] = 0
    raise ValueError("could not place source blob plus in-bounds marker")


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    grid = full_grid(h, w, 0)
    if name == "no_marker":
        grid[0][0] = 2; grid[0][1] = 3; grid[1][0] = 2
    elif name == "no_blob":
        grid[5][5] = 9
    elif name == "marker_inside_blob":
        grid[1][1] = 2; grid[1][2] = 3; grid[2][1] = 2; grid[2][2] = 9
    return grid
