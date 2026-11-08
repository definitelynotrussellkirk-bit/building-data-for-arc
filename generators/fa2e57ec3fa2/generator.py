"""Generator for rightward beams from color-2 emitters.

The canonical oracle paints color 7 through zero cells to the right of every
emitter until any nonzero obstacle or the grid edge.  Advertised controls are
strict and consumed; historical inert palette/cardinality controls were removed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fa2e57ec3fa2"
VERSION = "3.1.0"
TASK_ID = "fa2e57ec3fa2"
RULE_HASH = "1eb5cb474942"
SUMMARY = "Color-2 emitters cast color-7 beams rightward through zeros until any nonzero obstacle or the edge."
INVARIANTS = [
    "background is 0",
    "one to six color-2 emitters occupy distinct rows",
    "every ordinary emitter has at least one visible zero cell to its right",
    "any nonzero obstacle stops the canonical rightward beam",
]
PALETTE_KINDS = ("default", "no_walls", "few_walls", "many_walls")
DEGENERATE_TEXTURES = ("no_emitters", "emitter_at_right_edge", "blocked_immediately")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "5..22"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "6..26"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|no_walls|few_walls|many_walls"},
    "emitter_count": {"type": "int", "default": "difficulty schedule", "valid": "1..6"},
    "position_bias": {"type": "str", "default": "rows", "valid": "rows", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "default", "valid": "default|no_emitters|emitter_at_right_edge|blocked_immediately"},
}
_OBSTACLE_COLORS = (1, 3, 4, 5, 6, 8, 9)


def _validate_controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for key in ("grid_h", "grid_w", "emitter_count"):
        if overrides.get(key) is not None and type(overrides[key]) is not int:
            raise TypeError(f"{key} must be an integer (not bool)")
    for key in ("palette_kind", "position_bias", "texture"):
        if overrides.get(key) is not None and type(overrides[key]) is not str:
            raise TypeError(f"{key} must be a string")
    if overrides.get("palette_kind") not in (None, *PALETTE_KINDS):
        raise ValueError("unknown palette_kind")
    if overrides.get("position_bias") not in (None, "rows"):
        raise ValueError("position_bias must be rows")
    if overrides.get("texture") not in (None, "default", *DEGENERATE_TEXTURES):
        raise ValueError("unknown texture")
    if overrides.get("texture") in DEGENERATE_TEXTURES and set(overrides) != {"texture"}:
        raise ValueError("degenerate texture cannot be combined with other overrides")


def _draw_int(ctx, name, global_lo, global_hi, default_lo, default_hi):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, global_lo, global_hi)
    return ctx.draw_int_strict(name, default_lo, default_hi)


def _beam_cells(grid):
    h, w = len(grid), len(grid[0])
    cells = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2:
                continue
            cc = c + 1
            while cc < w and grid[r][cc] == 0:
                cells.add((r, cc))
                cc += 1
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)
    texture = overrides.get("texture", "default")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        defaults = (6, 9, 8, 12, 1, 2)
    elif difficulty == "hard":
        defaults = (12, 20, 14, 24, 3, 6)
    else:
        defaults = (9, 14, 11, 17, 2, 4)
    h = _draw_int(ctx, "grid_h", 5, 22, defaults[0], defaults[1])
    w = _draw_int(ctx, "grid_w", 6, 26, defaults[2], defaults[3])
    count = _draw_int(ctx, "emitter_count", 1, 6, defaults[4], defaults[5])
    if count > h:
        raise ValueError("emitter_count cannot exceed grid_h because rows are distinct")
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("position_bias", ("rows",))
    ctx.draw_choice("texture", ("default",))
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    rows = rng.sample(range(h), count)
    emitters = []
    for row in rows:
        col = rng.randint(0, w - 4)
        grid[row][col] = 2
        emitters.append((row, col))

    if palette_kind == "no_walls":
        wall_indices = set()
    elif palette_kind == "few_walls":
        order = list(range(count)); rng.shuffle(order)
        wall_indices = set(order[:max(1, count // 2)])
    elif palette_kind == "many_walls":
        wall_indices = set(range(count))
    else:
        wall_indices = {i for i in range(count) if rng.random() < 0.6}

    for i in sorted(wall_indices):
        row, col = emitters[i]
        wall_col = rng.randint(col + 2, w - 1)
        grid[row][wall_col] = rng.choice(_OBSTACLE_COLORS)

    if palette_kind in ("default", "many_walls"):
        non_emitter_rows = [row for row in range(h) if row not in set(rows)]
        extra = count if palette_kind == "many_walls" else rng.randint(0, count)
        candidates = [(row, col) for row in non_emitter_rows for col in range(w)]
        rng.shuffle(candidates)
        for row, col in candidates[:extra]:
            grid[row][col] = rng.choice(_OBSTACLE_COLORS)

    if not _beam_cells(grid):
        raise RuntimeError("ordinary construction produced no visible beam")
    return grid


def _draw_from_degenerate(name):
    h, w = 7, 9
    grid = full_grid(h, w, 0)
    if name == "emitter_at_right_edge":
        grid[3][w - 1] = 2
    elif name == "blocked_immediately":
        grid[3][2] = 2
        grid[3][3] = 5
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid too large: {len(grid)}x{width}")
    emitters = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid value at ({r},{c})")
            if value == 7:
                errors.append(f"input already contains beam color 7 at ({r},{c})")
            if value == 2:
                emitters.append((r, c))
    if not emitters:
        errors.append("no color-2 emitters")
    if not errors and not _beam_cells(grid):
        errors.append("no zero cell is visible to the right of any emitter")
    return errors
