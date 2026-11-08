"""Generator for arc_puzzle_bank_twelfth_21_bundle:easy_83_complete_l_trominoes_to_2x2.

Rule: each same-color L-tromino in a 2x2 box is completed to a solid
2x2 block.  Different-colored Ls may touch and a missing corner may already
contain another color; the selected Racket rule operates on colored objects and
may overwrite that occupied corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "68e9f92d8e4b"
VERSION = "3.0.0"
TASK_ID = "68e9f92d8e4b"

SUMMARY = (
    "0-background grid with 2-5 same-color L-trominoes.  Each object has "
    "three cells in a 2x2 bounding box; differently colored objects may touch "
    "and some draws place one object in another object's missing corner.  "
    "Complete every colored L to its 2x2 square using that object's color, "
    "overwriting an occupied missing corner when necessary."
)

INVARIANTS = [
    "background is 0",
    "each same-color connected component is a three-cell L in a 2x2 box",
    "different-colored L objects may touch orthogonally",
    "the selected rule fills each object's missing bbox corner with its own color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_trominoes", "already_solid", "trominoes_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..11", "valid": "4..20"},
    "grid_w": {"type": "int", "default": "rng 8..12", "valid": "4..22"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "objects": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "palette_size": {"type": "int", "default": "rng 2..9", "valid": "1..9"},
    "position_bias": {"type": "str", "default": "touching_colored_l_trominoes", "valid": "touching_colored_l_trominoes"},
    "n_distinct_colors": {"type": "int", "default": "one per object", "valid": "1..9"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _color_components(grid):
    """Return row-major cardinal components, connecting only equal colors."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected colored-object grammar, including touching colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer colors 0..9"]
    errors = []
    components = _color_components(grid)
    if not components:
        errors.append("no colored L-trominoes found")
    for index, (_, cells) in enumerate(components):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        if (len(cells) != 3 or max(rows) - min(rows) != 1
                or max(cols) - min(cols) != 1):
            errors.append(f"colored object {index} is not a three-cell L in a 2x2 box")
    return errors


def _transform_groups(groups, turns, mirror):
    transformed = []
    for group in groups:
        cells = []
        for row, col in group:
            if mirror:
                col = -col
            for _ in range(turns % 4):
                row, col = col, -row
            cells.append((row, col))
        transformed.append(cells)
    min_row = min(r for group in transformed for r, _ in group)
    min_col = min(c for group in transformed for _, c in group)
    return [[(r - min_row, c - min_col) for r, c in group] for group in transformed]


def _place_required_pair(grid, colors, rng, *, overlap):
    if overlap:
        groups = [
            [(0, 0), (0, 1), (1, 0)],
            [(1, 1), (1, 2), (2, 1)],
        ]
    else:
        groups = [
            [(0, 0), (0, 1), (1, 0)],
            [(0, 2), (0, 3), (1, 3)],
        ]
    groups = _transform_groups(groups, rng.randrange(4), bool(rng.randrange(2)))
    span_h = 1 + max(r for group in groups for r, _ in group)
    span_w = 1 + max(c for group in groups for _, c in group)
    h, w = len(grid), len(grid[0])
    top = rng.randrange(h - span_h + 1)
    left = rng.randrange(w - span_w + 1)
    for color, group in zip(colors, groups):
        for row, col in group:
            rr, cc = top + row, left + col
            if grid[rr][cc] != 0:
                raise RuntimeError("required colored-L pair overlaps unexpectedly")
            grid[rr][cc] = color


def _candidate_cells(row, col, missing):
    return [
        (row + dr, col + dc)
        for dr in (0, 1)
        for dc in (0, 1)
        if (dr, dc) != missing
    ]


def _place_additional(grid, color, rng) -> bool:
    h, w = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    rng.shuffle(candidates)
    missing_values = [(0, 0), (0, 1), (1, 0), (1, 1)]
    rng.shuffle(missing_values)
    for row, col in candidates:
        for missing in missing_values:
            cells = _candidate_cells(row, col, missing)
            if any(grid[r][c] != 0 for r, c in cells):
                continue
            # This color is unique in ordinary draws, but keep the helper total.
            if any(
                grid[r + dr][c + dc] == color
                for r, c in cells
                for dr, dc in CARDINAL
                if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in cells
            ):
                continue
            for r, c in cells:
                grid[r][c] = color
            return True
    return False


def _palette(kind):
    palettes = {
        "default": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "warm": [2, 4, 7, 1, 3, 9, 5, 6, 8],
        "cool": [1, 8, 6, 9, 5, 3, 2, 4, 7],
        "varied": [9, 3, 6, 1, 7, 4, 8, 2, 5],
    }
    return list(palettes.get(kind, palettes["default"]))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("objects", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("objects", 2, 5)
    if not 1 <= target <= 9:
        raise ValueError("objects must be in 1..9")
    rng = ctx.draw_rng("layout")
    palette = _palette(overrides.get("palette_kind", texture or "default"))
    rng.shuffle(palette)
    colors = palette[:target]
    grid = full_grid(h, w, 0)
    if target >= 2:
        _place_required_pair(grid, colors[:2], rng, overlap=((seed + sample_index) % 2 == 0))
        placed = 2
    else:
        placed = 0
    while placed < target:
        if not _place_additional(grid, colors[placed], rng):
            raise RuntimeError(f"could place only {placed}/{target} colored L objects")
        placed += 1
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid colored-L scene: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_trominoes":
        return g
    if name == "already_solid":
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 4
        for r in range(2):
            for c in range(2):
                g[5 + r][5 + c] = 6
        return g
    if name == "trominoes_touching":
        # Retained as a historical malformed same-color fusion case.  Ordinary
        # generation now includes lawful touching between different colors.
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4
        g[2][2] = 4; g[2][3] = 4; g[3][3] = 4
        return g
    return g
