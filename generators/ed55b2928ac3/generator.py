"""Generator for ed55b2928ac3 — corner-key transform then crop.

The cell at (0, 0) is a key: 1 rotates clockwise, 2 rotates 180 degrees,
3 flips left/right, 4 flips up/down, and 5/6/7 leave the crop unchanged.
Generation intentionally uses connected non-rectangular teaching shapes, while
``self_check`` accepts the broader canonical domain instead of rejecting the
source examples for optional shape-strength properties.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ed55b2928ac3"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"

SUMMARY = (
    "A 0-background grid has a transform key at (0,0) and one connected "
    "nonzero content shape elsewhere. Clear the key, crop all remaining "
    "nonzero content, then apply 1=rotate-cw, 2=rotate-180, 3=flip-lr, "
    "4=flip-ud, or identity for 5/6/7. Generated lessons use exact keyed "
    "controls and strong connected non-rectangular shapes; the validator "
    "also accepts the less-asymmetric and key-color-reusing canonical cases."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "(0,0) is a key in 1..7",
    "at least one nonzero content cell remains after clearing the key",
    "generated content is one connected non-rectangular shape of 3..6 cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_blob", "blob_at_corner", "blob_is_rectangle")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "keyed 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "keyed 6..12", "valid": "6..12"},
    "palette_kind": {"type": "str", "default": "keyed helpful", "valid": "|".join(PALETTE_KINDS)},
    "key": {"type": "int", "default": "keyed 1..7", "valid": "1..7"},
    "blob_size": {"type": "int", "default": "keyed 3..6", "valid": "3..6"},
    "palette_size": {"type": "int", "default": "2", "valid": "2"},
    "position_bias": {"type": "str", "default": "key_corner_with_blob", "valid": "key_corner_with_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 3, 7, 8, 9),
    "cool": (1, 2, 5, 6, 7, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}

# Fixed connected templates make exact blob_size controls reliable.  A random
# dihedral view and legal placement still provide substantial diversity.
_SHAPES = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (1, 0), (2, 0), (2, 1), (1, 1)),
    6: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 6, 12), ("grid_w", 6, 12), ("key", 1, 7), ("blob_size", 3, 6)):
        if name in overrides and (type(overrides[name]) is not int or not lo <= overrides[name] <= hi):
            raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    for name in ("palette_size", "n_distinct_colors"):
        if name in overrides and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be the exact integer 2")
        if name in overrides and overrides[name] != 2:
            raise ValueError(f"{name} must equal 2 for one key plus one content color")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if "position_bias" in overrides and overrides["position_bias"] != "key_corner_with_blob":
        raise ValueError("position_bias must be 'key_corner_with_blob'")
    if "density" in overrides and overrides["density"] != "sparse":
        raise ValueError("density must be 'sparse'")
    texture = overrides.get("texture")
    palette = overrides.get("palette_kind")
    if texture in HELPFUL_TEXTURES and palette is not None and texture != palette:
        raise ValueError("helpful texture and palette_kind must agree")


def _normal_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    values = dict(overrides)
    texture = values.get("texture")
    palette = values.get("palette_kind")
    if texture in HELPFUL_TEXTURES and palette is None:
        values["palette_kind"] = texture
    elif palette is not None and texture is None:
        values["texture"] = palette
    return values


def _scheduled_int(ctx, overrides: dict[str, Any], name: str, lo: int, hi: int, default: int) -> int:
    if name in overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _transform_cells(cells: tuple[tuple[int, int], ...], variant: int) -> list[tuple[int, int]]:
    pts = list(cells)
    # Four rotations, optionally reflected, followed by normalization.
    turns = variant % 4
    reflected = variant >= 4
    for _ in range(turns):
        pts = [(c, -r) for r, c in pts]
    if reflected:
        pts = [(r, -c) for r, c in pts]
    min_r = min(r for r, _ in pts)
    min_c = min(c for _, c in pts)
    return [(r - min_r, c - min_c) for r, c in pts]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    normalized = _normal_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )

    if normalized.get("texture") in DEGENERATE_TEXTURES:
        name = ctx.draw_choice("texture", DEGENERATE_TEXTURES)
        return _draw_from_degenerate(name, None)

    # Sample-index schedules keep difficulty useful without narrowing any
    # declared exact boundary override.
    if difficulty == "easy":
        default_h = 6 + sample_index % 3
        default_w = 6 + (sample_index // 2) % 3
    elif difficulty == "hard":
        default_h = 10 + sample_index % 3
        default_w = 10 + (sample_index // 2) % 3
    else:
        default_h = 6 + sample_index % 7
        default_w = 6 + (sample_index * 3) % 7
    h = _scheduled_int(ctx, normalized, "grid_h", 6, 12, default_h)
    w = _scheduled_int(ctx, normalized, "grid_w", 6, 12, default_w)
    key = _scheduled_int(ctx, normalized, "key", 1, 7, 1 + sample_index % 7)
    blob_size = _scheduled_int(ctx, normalized, "blob_size", 3, 6, 3 + sample_index % 4)

    if "palette_kind" in normalized:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        palette_kind = ctx.draw_choice("palette_kind", (PALETTE_KINDS[sample_index % len(PALETTE_KINDS)],))
    ctx.draw_choice("texture", (palette_kind,))
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("position_bias", ("key_corner_with_blob",))
    ctx.draw_choice("density", ("sparse",))

    rng = ctx.draw_rng("layout")
    shape = _transform_cells(_SHAPES[blob_size], rng.randrange(8))
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    # Keep a one-cell Chebyshev gap from the key.  Every declared 6x6 boundary
    # can fit every template.
    row0 = rng.randint(2, h - shape_h)
    col0 = rng.randint(2, w - shape_w)
    legal_colors = [c for c in _PALETTES[palette_kind] if c != key]
    color = rng.choice(legal_colors)

    grid = full_grid(h, w, 0)
    grid[0][0] = key
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color
    return grid


def _non_rect(cells):
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1) != len(cells)


def _crop_grid(cells):
    cells = list(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    h = max(r for r, _ in cells) - min_r + 1
    w = max(c for _, c in cells) - min_c + 1
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r - min_r][c - min_c] = 1
    return out


def _tt(grid):
    return tuple(tuple(row) for row in grid)


def _fully_asym(cells):
    """Optional generated-shape diagnostic; not a canonical-domain gate."""
    grid = _crop_grid(cells)
    h, w = len(grid), len(grid[0])
    ident = _tt(grid)
    cw = _tt([[grid[h - 1 - r][c] for r in range(h)] for c in range(w)])
    r180 = _tt([[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)])
    lr = _tt([[grid[r][w - 1 - c] for c in range(w)] for r in range(h)])
    ud = _tt([[grid[h - 1 - r][c] for c in range(w)] for r in range(h)])
    return len({ident, cw, r180, lr, ud}) == 5


def _components4(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical rule domain, not optional teaching strength."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    if len(grid) > 30 or width > 30:
        errors.append("grid exceeds 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a non-integer color or color outside 0..9")
        return errors
    key = grid[0][0]
    if key not in range(1, 8):
        errors.append(f"corner key must be 1..7, found {key}")
    content = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if (r, c) != (0, 0) and value != 0]
    if not content:
        errors.append("missing nonzero content after the corner key")
    elif len(_components4(content)) != 1:
        errors.append("nonzero content must form one 4-connected component")
    return errors


def _draw_from_degenerate(name, rng):
    del rng
    grid = full_grid(8, 8, 0)
    grid[0][0] = 1
    if name == "no_blob":
        return grid
    if name == "blob_at_corner":
        for r, c in ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)):
            grid[r][c] = 4
        return grid
    if name == "blob_is_rectangle":
        for r in range(2, 5):
            for c in range(3, 6):
                grid[r][c] = 6
    return grid
