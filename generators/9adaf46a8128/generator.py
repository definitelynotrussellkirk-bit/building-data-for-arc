"""Generator for transformed-template stamping below a separator."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "9adaf46a8128"
VERSION = "1.2.0"
TASK_ID = "9adaf46a8128"
RULE_HASH = "97f1e4b799fa"
SUMMARY = "Top template (color 2 cells) + full-5 row separator + bottom canvas with transform-command markers."
INVARIANTS = [
    "background is 0",
    "rows above the separator hold one nonempty color-2 template",
    "one row is entirely color 5",
    "rows below it hold command markers in {1,2,3,4}",
]
DEGENERATE_TEXTURES = ("no_markers", "no_template", "all_identity_markers")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "10..16"},
    "n_markers": {"type": "int", "default": "2 easy / 2..3 medium / 3..4 hard", "valid": "1..4"},
    "position_bias": {"type": "str", "default": "template_separator_markers", "valid": "template_separator_markers", "probe": "diagnostic"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "default", "valid": "default|no_markers|no_template|all_identity_markers"},
}
_TEMPLATES = [
    [(0, 1), (0, 3), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
]


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
    for key in ("grid_h", "grid_w", "n_markers"):
        if overrides.get(key) is not None and type(overrides[key]) is not int:
            raise TypeError(f"{key} must be an integer (not bool)")
    for key in ("position_bias", "density", "texture"):
        if overrides.get(key) is not None and type(overrides[key]) is not str:
            raise TypeError(f"{key} must be a string")
    if overrides.get("position_bias") not in (None, "template_separator_markers"):
        raise ValueError("position_bias must be template_separator_markers")
    if overrides.get("density") not in (None, "sparse"):
        raise ValueError("density must be sparse")
    if overrides.get("texture") not in (None, "default", *DEGENERATE_TEXTURES):
        raise ValueError("unknown texture")


def _draw_int(ctx, name, global_lo, global_hi, default_lo, default_hi):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, global_lo, global_hi)
    return ctx.draw_int_strict(name, default_lo, default_hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture", "default")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, None)
    if difficulty == "easy":
        defaults = (9, 9, 11, 11, 2, 2)
    elif difficulty == "hard":
        defaults = (11, 13, 13, 16, 3, 4)
    else:
        defaults = (9, 11, 11, 13, 2, 3)
    h = _draw_int(ctx, "grid_h", 8, 14, defaults[0], defaults[1])
    w = _draw_int(ctx, "grid_w", 10, 16, defaults[2], defaults[3])
    n_markers = _draw_int(ctx, "n_markers", 1, 4, defaults[4], defaults[5])
    ctx.draw_choice("position_bias", ("template_separator_markers",))
    ctx.draw_choice("density", ("sparse",))
    if texture == "default":
        ctx.draw_choice("texture", ("default",))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    template = rng.choice(_TEMPLATES)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    sep = min(th + 1, h - 4)
    fill_box(g, sep, 0, sep, w - 1, 5)
    tr0 = rng.randint(0, max(0, sep - th))
    tc0 = rng.randint(0, w - tw)
    for dr, dc in template:
        g[tr0 + dr][tc0 + dc] = 2
    candidates = [(r, c) for r in range(sep + 1, h) for c in range(w)]
    rng.shuffle(candidates)
    placed = []
    for position in candidates:
        if all(abs(position[0] - r) >= 2 or abs(position[1] - c) >= 2 for r, c in placed):
            placed.append(position)
            if len(placed) == n_markers:
                break
    if len(placed) < n_markers:
        placed.extend([p for p in candidates if p not in placed][:n_markers - len(placed)])
    role_start = sample_index % 4
    roles = [1 + ((role_start + i) % 4) for i in range(n_markers)]
    for (r, c), role in zip(sorted(placed), roles):
        g[r][c] = role
    return g


def _draw_from_degenerate(name, rng):
    del rng
    h, w = 10, 12
    g = full_grid(h, w, 0)
    sep = 4
    fill_box(g, sep, 0, sep, w - 1, 5)
    if name == "no_markers":
        for dr, dc in _TEMPLATES[0]:
            g[1 + dr][2 + dc] = 2
    elif name == "no_template":
        g[6][3] = 1; g[7][8] = 2
    elif name == "all_identity_markers":
        for dr, dc in _TEMPLATES[1]:
            g[1 + dr][2 + dc] = 2
        g[6][3] = 1; g[7][8] = 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    msgs = []
    if len(grid) > 30 or width > 30:
        msgs.append("grid too large")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        msgs.append("invalid cell")
    sep_rows = [r for r, row in enumerate(grid) if all(v == 5 for v in row)]
    if len(sep_rows) != 1:
        msgs.append("expected exactly one full-width color-5 separator row")
        return msgs
    sep = sep_rows[0]
    if not any(grid[r][c] == 2 for r in range(sep) for c in range(width)):
        msgs.append("no color-2 template cells above separator")
    if not any(grid[r][c] in (1, 2, 3, 4) for r in range(sep + 1, len(grid)) for c in range(width)):
        msgs.append("no command markers below separator")
    return msgs
