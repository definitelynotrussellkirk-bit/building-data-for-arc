"""Generator for ARC task 6ea4a07e.

Rule: find the unique non-background color, map it through
``{3: 1, 5: 4, 8: 2}`` (other colors map to themselves), then complement
the binary mask: foreground becomes 0 and background becomes the mapped color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03478139591b"
VERSION = "1.4.0"
TASK_ID = "03478139591b"
RULE_HASH = "e5a2cb4531f0"
SUMMARY = (
    "Binary two-color complement with a color map: 3→1, 5→4, 8→2, "
    "and every other nonzero color maps to itself."
)

EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular 3..15 grid of exact ARC integer colors",
    "exactly color 0 and one nonzero foreground color",
    "at least one foreground and one background cell",
]

FG_LAYOUTS = ("random", "cluster", "row", "column", "diagonal", "blob", "border")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES = FG_LAYOUTS + ("unmapped_color",)
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "fg_color", "fg_density", "fg_layout", "texture"}
_MAPPED = {3: 1, 5: 4, 8: 2}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 3..15", "valid": "3..15"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 3..15", "valid": "3..15"},
    "fg_color": {"type": "choice", "default": "rng 3|5|8; 20% unmapped", "valid": "1..9"},
    "fg_density": {"type": "float", "default": "rng 0.25..0.65", "valid": "0.05..0.95"},
    "fg_layout": {"type": "str", "default": "rng helpful", "valid": "|".join(FG_LAYOUTS)},
    "texture": {"type": "str", "default": "alias for layout", "valid": "|".join(HELPFUL_TEXTURES)},
}


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "fg_color"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an exact integer (not bool)")
    if "fg_density" in overrides and overrides["fg_density"] is not None:
        value = overrides["fg_density"]
        if type(value) not in (int, float):
            raise TypeError("fg_density override must be a finite number")
        if isinstance(value, bool):
            raise TypeError("fg_density override must be a finite number (not bool)")
        if not 0.05 <= float(value) <= 0.95:
            raise ValueError("fg_density override must be in 0.05..0.95")
    if "fg_layout" in overrides and overrides["fg_layout"] is not None:
        if type(overrides["fg_layout"]) is not str or overrides["fg_layout"] not in FG_LAYOUTS:
            raise ValueError(f"fg_layout must be one of {FG_LAYOUTS}")
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str or overrides["texture"] not in HELPFUL_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")


def _size_bounds(difficulty):
    if difficulty == "easy":
        return 3, 5
    if difficulty == "medium":
        return 6, 10
    if difficulty == "hard":
        return 11, 15
    if difficulty is None:
        return 3, 15
    raise ValueError("difficulty must be None, easy, medium, or hard")


def self_check(grid, *, difficulty=None, meta=None):
    """Return structural domain errors without raising or mutating ``grid``."""
    errors: list[str] = []
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list of rows"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if not 3 <= len(grid) <= 15 or not 3 <= width <= 15:
        errors.append("grid dimensions must each be in 3..15")
    for index, row in enumerate(grid):
        if type(row) is not list or len(row) != width:
            errors.append(f"row {index} is ragged or not a list")
            continue
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                errors.append("cells must be exact integer colors 0..9")
                break
    if errors:
        return errors
    colors = {cell for row in grid for cell in row}
    foregrounds = colors - {0}
    if 0 not in colors:
        errors.append("at least one background cell is required")
    if len(foregrounds) != 1:
        errors.append("exactly one nonzero foreground color is required")
    return errors


def rule_mirror(grid):
    """Independent Python mirror used only by focused tests and audits."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generator-domain grid: " + "; ".join(errors))
    color = next(cell for row in grid for cell in row if cell != 0)
    mapped = _MAPPED.get(color, color)
    return [[0 if cell != 0 else mapped for cell in row] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    lo, hi = _size_bounds(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_strict("grid_h", lo, hi)
    w = ctx.draw_int_strict("grid_w", lo, hi)
    texture = overrides.get("texture")

    if "fg_color" in overrides and overrides["fg_color"] is not None:
        color = ctx.draw_color_strict("fg_color", exclude={0})
        if texture == "unmapped_color" and color in _MAPPED:
            raise ValueError("texture=unmapped_color requires fg_color outside {3,5,8}")
    elif texture == "unmapped_color" or ctx.draw_int("unmapped_roll", 0, 99) < 20:
        color = ctx.draw_choice("fg_color_unmapped", [1, 2, 4, 6, 7, 9])
    else:
        color = ctx.draw_choice("fg_color", [3, 5, 8])

    density = (
        float(overrides["fg_density"])
        if overrides.get("fg_density") is not None
        else ctx.draw_rng("fg_density").uniform(0.25, 0.65)
    )
    layout = (
        texture
        if texture in FG_LAYOUTS
        else overrides.get("fg_layout")
        or ctx.draw_choice("fg_layout", list(FG_LAYOUTS))
    )
    rng = ctx.draw_rng("cells")
    grid = full_grid(h, w, 0)

    if layout == "random":
        for r in range(h):
            for c in range(w):
                if rng.random() < density:
                    grid[r][c] = color
    elif layout == "cluster":
        cr, cc = rng.randrange(h), rng.randrange(w)
        radius = max(1, round(min(h, w) * density / 2))
        for r in range(h):
            for c in range(w):
                if abs(r - cr) + abs(c - cc) <= radius and rng.random() < 0.82:
                    grid[r][c] = color
    elif layout == "row":
        r = rng.randrange(h)
        for c in range(w):
            if rng.random() < density:
                grid[r][c] = color
    elif layout == "column":
        c = rng.randrange(w)
        for r in range(h):
            if rng.random() < density:
                grid[r][c] = color
    elif layout == "diagonal":
        offset = rng.randrange(max(h, w))
        for r in range(h):
            c = (r + offset) % w
            grid[r][c] = color
    elif layout == "blob":
        blob_h = max(1, min(h, round(h * density)))
        blob_w = max(1, min(w, round(w * density)))
        r0 = rng.randrange(h - blob_h + 1)
        c0 = rng.randrange(w - blob_w + 1)
        for r in range(r0, r0 + blob_h):
            for c in range(c0, c0 + blob_w):
                grid[r][c] = color
    elif layout == "border":
        for c in range(w):
            grid[0][c] = color
            grid[h - 1][c] = color
        for r in range(h):
            grid[r][0] = color
            grid[r][w - 1] = color
    else:  # guarded above; keep a defensive invariant at the point of use
        raise ValueError(f"unsupported layout: {layout}")

    # Ordinary episodes always expose both sides of the complement.
    if not any(cell != 0 for row in grid for cell in row):
        grid[rng.randrange(h)][rng.randrange(w)] = color
    if all(cell != 0 for row in grid for cell in row):
        grid[rng.randrange(h)][rng.randrange(w)] = 0
    return grid
