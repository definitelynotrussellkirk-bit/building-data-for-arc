"""Generator for arc_additional_puzzle_bank_volume18:E124.

Magenta cells are reflected across a full orange divider as cyan.  Ordinary
sampling reserves every reflected destination before distractors are placed, so
unrelated colors are preserved as documented.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "329f699c3e09"
VERSION = "1.4.0"
TASK_ID = "329f699c3e09"
SUMMARY = (
    "Full orange(7) divider row/col + magenta(6) cells on one side; reflect "
    "each magenta across the divider and paint the destination cyan(8). "
    "Ordinary generation reserves those destinations so all other colors survive."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "there is exactly one full orange divider row or column",
    "magenta source cells lie strictly on one side of the divider",
    "every reflected destination is in bounds and empty in the input",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_magenta", "magenta_on_divider")
HELPFUL_TEXTURES = PALETTE_KINDS
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "palette_kind", "n_cells", "texture"}
_DISTRACTOR_PALETTES = {
    "default": (1, 2, 3, 4, 5, 9),
    "warm": (2, 3, 4, 9),
    "cool": (1, 5, 9),
    "varied": (1, 2, 3, 4, 5, 9),
}

AXES = {
    "grid_h": {"type": "int", "default": "rng by difficulty", "valid": "7..30"},
    "grid_w": {"type": "int", "default": "rng by difficulty", "valid": "7..30"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_cells": {"type": "int", "default": "rng by difficulty", "valid": "1..30"},
    "palette_size": {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias": {"type": "str", "default": "one_side_of_divider", "valid": "one_side_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "2 plus distractors", "valid": "2..8"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError("unknown palette_kind")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if (overrides.get("texture") in HELPFUL_TEXTURES and "palette_kind" in overrides
            and overrides["texture"] != overrides["palette_kind"]):
        raise ValueError("helpful texture and palette_kind must agree")


def _divider(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 7 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 7 for r in range(h))]
    if len(rows) + len(cols) != 1:
        raise ValueError("need exactly one full orange divider row or column")
    return ("row", rows[0]) if rows else ("col", cols[0])


def reflected_destinations(grid, *, strict=False):
    axis, div = _divider(grid)
    h, w = len(grid), len(grid[0])
    result = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 6:
                continue
            nr, nc = ((2 * div - r, c) if axis == "row" else (r, 2 * div - c))
            if not (0 <= nr < h and 0 <= nc < w):
                if strict:
                    raise ValueError("magenta reflection leaves the grid")
                continue
            result.append((nr, nc))
    return result


def rule_mirror(grid):
    out = deepcopy(grid)
    for r, c in reflected_destinations(grid):
        out[r][c] = 8
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(type(row) is not list or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colors"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errors = []
    try:
        axis, div = _divider(grid)
    except ValueError as exc:
        return [str(exc)]
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if not sources:
        return ["no magenta (6) source cells"]
    side_values = [(r - div) if axis == "row" else (c - div) for r, c in sources]
    if any(value == 0 for value in side_values) or not (all(value < 0 for value in side_values) or all(value > 0 for value in side_values)):
        errors.append("magenta sources must lie strictly on one side of the divider")
    h, w = len(grid), len(grid[0])
    for r, c in sources:
        nr, nc = ((2 * div - r, c) if axis == "row" else (r, 2 * div - c))
        if not (0 <= nr < h and 0 <= nc < w):
            errors.append(f"reflection destination {(nr, nc)} is out of bounds")
        elif grid[nr][nc] != 0:
            errors.append(f"reflection destination {(nr, nc)} is occupied by color {grid[nr][nc]}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    effective = dict(overrides)
    if texture in HELPFUL_TEXTURES:
        effective.setdefault("palette_kind", texture)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = ctx.draw_int_strict("grid_h", 7, 12)
        w = ctx.draw_int_strict("grid_w", 8, 14)
        n_cells = ctx.draw_int_strict("n_cells", 3, 6)
        n_distractors = rng.randint(1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int_strict("grid_h", 13, 30)
        w = ctx.draw_int_strict("grid_w", 15, 30)
        n_cells = ctx.draw_int_strict("n_cells", 8, 30)
        n_distractors = rng.randint(5, 12)
    else:
        h = ctx.draw_int_strict("grid_h", 9, 24)
        w = ctx.draw_int_strict("grid_w", 11, 26)
        n_cells = ctx.draw_int_strict("n_cells", 5, 14)
        n_distractors = rng.randint(2, 7)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    g = full_grid(h, w, 0)
    sources: set[tuple[int, int]] = set()
    vertical = rng.choice([False, True])
    if vertical:
        div = rng.randint(3, w - 4)
        source_left = rng.choice([True, False])
        if source_left:
            choices = list(range(max(0, 2 * div - (w - 1)), div))
        else:
            choices = list(range(div + 1, min(w, 2 * div + 1)))
        for r in range(h):
            g[r][div] = 7
        capacity = h * len(choices)
        target = min(n_cells, capacity)
        while len(sources) < target:
            sources.add((rng.randrange(h), rng.choice(choices)))
        reserved = {(r, 2 * div - c) for r, c in sources}
    else:
        div = rng.randint(3, h - 4)
        source_top = rng.choice([True, False])
        if source_top:
            choices = list(range(max(0, 2 * div - (h - 1)), div))
        else:
            choices = list(range(div + 1, min(h, 2 * div + 1)))
        for c in range(w):
            g[div][c] = 7
        capacity = w * len(choices)
        target = min(n_cells, capacity)
        while len(sources) < target:
            sources.add((rng.choice(choices), rng.randrange(w)))
        reserved = {(2 * div - r, c) for r, c in sources}
    for r, c in sources:
        g[r][c] = 6
    pool = _DISTRACTOR_PALETTES[palette_kind]
    attempts = max(120, h * w * 2)
    while n_distractors and attempts:
        attempts -= 1
        rr, cc = rng.randrange(h), rng.randrange(w)
        if g[rr][cc] != 0 or (rr, cc) in reserved:
            continue
        g[rr][cc] = rng.choice(pool)
        n_distractors -= 1
    findings = self_check(g, difficulty=difficulty, meta={"texture": palette_kind})
    if findings:
        raise RuntimeError(f"constructed invalid ordinary scene: {findings}")
    return g


def _draw_from_degenerate(name):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_divider":
        g[2][2] = 6; g[3][3] = 6; g[5][7] = 6
    elif name == "no_magenta":
        for r in range(h): g[r][5] = 7
    elif name == "magenta_on_divider":
        for r in range(h): g[r][5] = 7
        g[2][5] = 6; g[5][5] = 6
    return g
