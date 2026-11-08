"""Generator for 8b:m53 — equality matrix from headers.

Rule: top + left headers; matrix at (r, c) is left[r] if equal to
top[c] else 0.

The ordinary sampler now consumes every declared control.  In particular,
``n_shared`` is exact, dimension overrides use the full documented domain, and
all non-background ARC colors (including 1) occur in ordinary support.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87754dbb8687"
VERSION = "1.2.0"
TASK_ID = "87754dbb8687"
RULE_HASH = "0ac662ce40c7"
SUMMARY = "Top row + left col headers with shared colors."

INVARIANTS = [
    "background is 0",
    "row 0 cols >= 1: top header colors",
    "col 0 rows >= 1: left header colors",
    "the interior is empty in the input",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shared_color", "headers_all_same", "missing_one_axis")
HELPFUL_TEXTURES = PALETTE_KINDS
_ALLOWED_OVERRIDES = {
    "grid_h",
    "grid_w",
    "palette_kind",
    "n_shared",
    "palette_size",
    "position_bias",
    "n_distinct_colors",
    "density",
    "texture",
}

AXES = {
    "grid_h": {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "n_shared": {"type": "int", "default": "rng feasible 1..3", "valid": "0..6"},
    "palette_size": {"type": "int", "default": "rng 4..6", "valid": "2..8"},
    "position_bias": {"type": "str", "default": "header_axes", "valid": "header_axes"},
    "n_distinct_colors": {"type": "int", "default": "rng feasible", "valid": "2..8"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _draw_dimension(ctx, name: str, lo: int, hi: int) -> int:
    """Use the full declared domain for an exact override, the band otherwise."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, 4, 10)
    return ctx.draw_int_strict(name, lo, hi)


def _exclusive_split(total: int, shared: int, top_len: int, left_len: int) -> tuple[int, int]:
    """Choose feasible top-only/left-only distinct-color counts."""
    remainder = total - shared
    low = max(0, remainder - (left_len - shared))
    high = min(remainder, top_len - shared)
    if shared == 0:
        low = max(low, 1)
        high = min(high, remainder - 1)
    if low > high:
        raise ValueError(
            "cannot realize requested n_shared/n_distinct_colors on the requested header lengths"
        )
    top_only = (low + high) // 2
    return top_only, remainder - top_only


def _palette_order(kind: str) -> list[int]:
    # Every kind retains all nine interchangeable nonzero colors.  The order is
    # only a prior; a keyed shuffle below gives broad ordinary support.
    return {
        "default": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "warm": [2, 3, 4, 6, 7, 8, 9, 1, 5],
        "cool": [8, 9, 1, 4, 5, 6, 2, 3, 7],
        "varied": [1, 3, 5, 7, 9, 2, 4, 6, 8],
    }[kind]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if set(overrides) != {"texture"}:
            raise ValueError("degenerate texture cannot be combined with exact ordinary controls")
        return _draw_from_degenerate(texture)
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError("unknown texture")

    normalized = dict(overrides)
    if texture in HELPFUL_TEXTURES:
        if normalized.get("palette_kind") not in (None, texture):
            raise ValueError("helpful texture and palette_kind must agree")
        normalized["palette_kind"] = texture

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )
    if difficulty == "easy":
        h = _draw_dimension(ctx, "grid_h", 5, 5)
        w = _draw_dimension(ctx, "grid_w", 5, 6)
    elif difficulty == "hard":
        h = _draw_dimension(ctx, "grid_h", 6, 7)
        w = _draw_dimension(ctx, "grid_w", 6, 7)
    else:
        h = _draw_dimension(ctx, "grid_h", 5, 7)
        w = _draw_dimension(ctx, "grid_w", 5, 7)

    ctx.draw_choice("position_bias", ("header_axes",))
    ctx.draw_choice("density", ("sparse",))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    # The texture axis is an explicit alias, not an independent confound.
    if "texture" in normalized:
        ctx.draw_choice("texture", (palette_kind,))

    palette_size = ctx.draw_int_strict("palette_size", 2, 8) if "palette_size" in normalized else ctx.draw_int_strict("palette_size", 4, 6)
    top_len, left_len = w - 1, h - 1
    max_distinct = min(8, palette_size, top_len + left_len)
    if max_distinct < 2:
        raise ValueError("cannot realize two header colors on the requested grid")
    if "n_distinct_colors" in normalized:
        n_distinct = ctx.draw_int_strict("n_distinct_colors", 2, 8)
        if n_distinct > max_distinct:
            raise ValueError("cannot realize requested n_distinct_colors with palette/grid limits")
    else:
        n_distinct = ctx.draw_int_strict("n_distinct_colors", 2, max_distinct)

    feasible_shared = [
        value
        for value in range(0, min(6, n_distinct, top_len, left_len) + 1)
        if _is_feasible_split(n_distinct, value, top_len, left_len)
    ]
    ordinary_shared = [value for value in feasible_shared if 1 <= value <= 3]
    if "n_shared" in normalized:
        n_shared = ctx.draw_int_strict("n_shared", 0, 6)
        if n_shared not in feasible_shared:
            raise ValueError(
                "cannot realize requested n_shared/n_distinct_colors on the requested header lengths"
            )
    else:
        if not ordinary_shared:
            raise ValueError("cannot realize an ordinary shared-color scene")
        n_shared = ctx.draw_choice("n_shared", ordinary_shared)

    rng = ctx.draw_rng("layout")
    palette = _palette_order(palette_kind)
    rng.shuffle(palette)
    candidate = palette[:palette_size]
    selected = rng.sample(candidate, n_distinct)

    top_only_n, left_only_n = _exclusive_split(n_distinct, n_shared, top_len, left_len)
    shared = selected[:n_shared]
    top_only = selected[n_shared : n_shared + top_only_n]
    left_only = selected[n_shared + top_only_n :]
    top_colors = shared + top_only
    left_colors = shared + left_only

    top = list(top_colors)
    left = list(left_colors)
    while len(top) < top_len:
        top.append(rng.choice(top_colors))
    while len(left) < left_len:
        left.append(rng.choice(left_colors))
    rng.shuffle(top)
    rng.shuffle(left)

    grid = full_grid(h, w, 0)
    for c, color in enumerate(top, start=1):
        grid[0][c] = color
    for r, color in enumerate(left, start=1):
        grid[r][0] = color
    return grid


def _is_feasible_split(total: int, shared: int, top_len: int, left_len: int) -> bool:
    try:
        _exclusive_split(total, shared, top_len, left_len)
    except ValueError:
        return False
    return True


def rule_mirror(grid):
    """Literal Python mirror used only for focused source tests."""
    top = grid[0][1:]
    left = [row[0] for row in grid[1:]]
    return [[row_color if row_color != 0 and row_color == col_color else 0 for col_color in top] for row_color in left]


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if h < 2 or w < 2:
        return ["grid too small for top/left headers"]
    if grid[0][0] != 0:
        errors.append("header corner g[0][0] should be background 0")
    top = grid[0][1:]
    left = [grid[r][0] for r in range(1, h)]
    if any(type(v) is not int or not 1 <= v <= 9 for v in top):
        errors.append("top header must contain nonzero ARC colors")
    if any(type(v) is not int or not 1 <= v <= 9 for v in left):
        errors.append("left header must contain nonzero ARC colors")
    if any(grid[r][c] != 0 for r in range(1, h) for c in range(1, w)):
        errors.append("matrix interior should be empty/background in the input")
    return errors


def _draw_from_degenerate(name):
    h, w = 6, 6
    grid = full_grid(h, w, 0)
    if name == "no_shared_color":
        top = [1, 2, 3, 4, 5]
        left = [6, 7, 8, 9, 6]
        for c, color in enumerate(top, start=1):
            grid[0][c] = color
        for r, color in enumerate(left, start=1):
            grid[r][0] = color
    elif name == "headers_all_same":
        for c in range(1, w):
            grid[0][c] = 5
        for r in range(1, h):
            grid[r][0] = 5
    elif name == "missing_one_axis":
        for c, color in enumerate([1, 2, 3, 4, 5], start=1):
            grid[0][c] = color
    return grid
