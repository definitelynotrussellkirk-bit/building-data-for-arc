"""Generator for the 9-row two-panel occupancy-XOR ARC family.

The ordinary sampler keeps its historical width and density bands. Explicit
controls are a separate public contract: they are validated strictly against
their declared domains instead of being narrowed by the current difficulty
band. The canonical rule reads only zero/nonzero occupancy in the two 4-row
panels and writes their symmetric difference in color 3.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08eaba8254b2"
VERSION = "2.2.0"
TASK_ID = "08eaba8254b2"
RULE_HASH = "5679cfe5ff27"  # reverified canonical rule authority
SUMMARY = (
    "A 4-row top panel and 4-row bottom panel separated by an inert row; "
    "the output is the panels' zero/nonzero occupancy XOR in color 3."
)

INVARIANTS = [
    "input is a rectangular 9×w grid with 1 <= w <= 30",
    "row 4 contains at least one nonzero separator cell",
    "both 4-row panels contain visible nonzero content",
    "at least one cell differs in zero/nonzero occupancy across the panels",
]

PANEL_PATTERNS = (
    "random", "blob", "stripes", "checker", "border", "diagonal",
    "multicolor", "broken_sep",
)
DEGENERATE_TEXTURES = ("same_panels", "disjoint_panels", "all_filled")
TEXTURES = PANEL_PATTERNS + DEGENERATE_TEXTURES
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_w": {"type": "int", "default": "difficulty-band rng 3..14", "valid": "1..30"},
    "top_color": {"type": "color", "default": "rng !0", "valid": "1..9"},
    "bot_color": {"type": "color", "default": "rng !0 !top", "valid": "1..9 distinct from top"},
    "sep_color": {"type": "color", "default": "rng !0 !top !bot", "valid": "1..9 distinct from panel colors"},
    "top_density": {"type": "float", "default": "rng 0.3..0.7", "valid": "finite 0..1"},
    "bot_density": {"type": "float", "default": "rng 0.3..0.7", "valid": "finite 0..1"},
    "panel_pattern": {"type": "str", "default": "rng helpful", "valid": "|".join(PANEL_PATTERNS)},
    "xor_target": {"type": "int", "default": "rng 1..w", "valid": "1..4*grid_w"},
    "texture": {
        "type": "str",
        "default": "optional alias for panel_pattern",
        "valid": "|".join(TEXTURES),
        "doc": (
            "multicolor varies nonzero colors while preserving occupancy; "
            "broken_sep inserts separator gaps/odd colors; the three degenerate "
            "textures are explicit near-miss controls."
        ),
    },
}


def _strict_int(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _strict_density(value, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number in 0..1 (not bool)")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be in 0..1")
    return result


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))
    if "panel_pattern" in overrides and "texture" in overrides:
        raise ValueError("panel_pattern and texture are aliases; provide only one")
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        _strict_int(overrides["grid_w"], 1, 30, "grid_w")
    if "xor_target" in overrides and overrides["xor_target"] is not None:
        if type(overrides["xor_target"]) is not int:
            raise ValueError("xor_target must be an exact integer")
    for label in ("top_density", "bot_density"):
        if label in overrides and overrides[label] is not None:
            _strict_density(overrides[label], label)
    if "panel_pattern" in overrides and overrides["panel_pattern"] is not None:
        value = overrides["panel_pattern"]
        if type(value) is not str or value not in PANEL_PATTERNS:
            raise ValueError("panel_pattern must be one of: " + ", ".join(PANEL_PATTERNS))
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str or value not in TEXTURES:
            raise ValueError("texture must be one of: " + ", ".join(TEXTURES))
    for label in ("top_color", "bot_color", "sep_color"):
        if label in overrides and overrides[label] is not None:
            _strict_int(overrides[label], 1, 9, label)


def _sample_or_override_int(ctx, label: str, sample_low: int, sample_high: int,
                            valid_low: int, valid_high: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_low, valid_high)
    return ctx.draw_int_strict(label, sample_low, sample_high)


def _xor_count(grid) -> int:
    width = len(grid[0])
    return sum(
        (grid[r][c] == 0) != (grid[5 + r][c] == 0)
        for r in range(4)
        for c in range(width)
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the documented input grammar, not just the XOR nonblank shortcut."""
    if not grid or type(grid) is not list or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    if len(grid) != 9:
        return [f"expected height 9, got {len(grid)}"]
    if not 1 <= width <= 30:
        errors.append(f"expected width in 1..30, got {width}")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        errors.append("grid cells must be exact integer colors 0..9")
        return errors
    if not any(grid[4][c] != 0 for c in range(width)):
        errors.append("separator row must contain at least one nonzero cell")
    if not any(grid[r][c] != 0 for r in range(4) for c in range(width)):
        errors.append("top panel must contain nonzero content")
    if not any(grid[5 + r][c] != 0 for r in range(4) for c in range(width)):
        errors.append("bottom panel must contain nonzero content")
    if _xor_count(grid) == 0:
        errors.append("panels have identical zero-occupancy: XOR output is blank")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        width_band = (3, 5)
    elif difficulty == "hard":
        width_band = (10, 14)
    else:
        width_band = (3, 14)
    width = _sample_or_override_int(ctx, "grid_w", *width_band, 1, 30)

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        extras = sorted(set(overrides) - {"texture", "grid_w"})
        if extras:
            raise ValueError("degenerate texture cannot be combined with: " + ", ".join(extras))
        return _draw_from_degenerate(texture, width, ctx.draw_rng("panels"))

    top_color = ctx.draw_color_strict("top_color", exclude={0})
    bot_color = ctx.draw_color_strict("bot_color", exclude={0, top_color})
    sep_color = ctx.draw_color_strict("sep_color", exclude={0, top_color, bot_color})
    top_density = (
        _strict_density(overrides["top_density"], "top_density")
        if "top_density" in overrides and overrides["top_density"] is not None
        else ctx.draw_rng("top_density").uniform(0.3, 0.7)
    )
    bot_density = (
        _strict_density(overrides["bot_density"], "bot_density")
        if "bot_density" in overrides and overrides["bot_density"] is not None
        else ctx.draw_rng("bot_density").uniform(0.3, 0.7)
    )
    if texture is not None:
        pattern = texture
    else:
        pattern = ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS))

    rng = ctx.draw_rng("panels")
    grid = full_grid(9, width, 0)
    if pattern == "broken_sep":
        for c in range(width):
            if rng.random() < 0.75:
                grid[4][c] = rng.randint(1, 9)
        if not any(grid[4][c] != 0 for c in range(width)):
            grid[4][rng.randrange(width)] = sep_color
        panel_pattern = "random"
    else:
        for c in range(width):
            grid[4][c] = sep_color
        panel_pattern = pattern

    if panel_pattern == "multicolor":
        for r in range(4):
            for c in range(width):
                if rng.random() < top_density:
                    grid[r][c] = rng.randint(1, 9)
                if rng.random() < bot_density:
                    grid[5 + r][c] = rng.randint(1, 9)
    else:
        _fill_panel(grid, 0, 4, width, panel_pattern, top_density, top_color, rng)
        _fill_panel(grid, 5, 9, width, panel_pattern, bot_density, bot_color, rng)

    _ensure_panel_activity(grid, width, top_color, bot_color, rng)
    if "xor_target" in overrides and overrides["xor_target"] is not None:
        target = ctx.draw_int_strict("xor_target", 1, 4 * width)
    else:
        target = ctx.draw_int_strict("xor_target", 1, max(1, width))
    _ensure_xor(grid, width, target, top_color, bot_color, rng)
    if target < 4 * width:
        _avoid_full_xor(grid, width, top_color, bot_color, rng)
    _ensure_panel_activity_preserving_xor(grid, width, top_color, bot_color)
    return grid


def _fill_panel(grid, row0, row1, width, pattern, density, foreground, rng):
    panel_height = row1 - row0
    if pattern == "random":
        for r in range(row0, row1):
            for c in range(width):
                grid[r][c] = foreground if rng.random() < density else 0
    elif pattern == "blob":
        blob_height = max(1, int(panel_height * density))
        blob_width = max(1, int(width * density))
        rr = rng.randint(row0, row1 - blob_height)
        cc = rng.randint(0, width - blob_width)
        for r in range(rr, rr + blob_height):
            for c in range(cc, cc + blob_width):
                grid[r][c] = foreground
    elif pattern == "stripes":
        for r in range(row0, row1):
            if (r - row0) % 2 == 0:
                for c in range(width):
                    grid[r][c] = foreground
    elif pattern == "checker":
        for r in range(row0, row1):
            for c in range(width):
                if (r + c) % 2 == 0:
                    grid[r][c] = foreground
    elif pattern == "border":
        for c in range(width):
            grid[row0][c] = foreground
            grid[row1 - 1][c] = foreground
        for r in range(row0, row1):
            grid[r][0] = foreground
            grid[r][width - 1] = foreground
    elif pattern == "diagonal":
        for k in range(min(panel_height, width)):
            grid[row0 + k][k] = foreground
    else:
        raise ValueError(f"unsupported panel pattern: {pattern}")


def _ensure_panel_activity(grid, width, top_color, bot_color, rng):
    cells = [(r, c) for r in range(4) for c in range(width)]
    if not any(grid[r][c] != 0 for r, c in cells):
        r, c = rng.choice(cells)
        grid[r][c] = top_color
    if not any(grid[5 + r][c] != 0 for r, c in cells):
        r, c = rng.choice(cells)
        grid[5 + r][c] = bot_color


def _ensure_xor(grid, width, target, top_color, bot_color, rng):
    target = _strict_int(target, 1, 4 * width, "xor_target")
    have = _xor_count(grid)
    if have >= target:
        return
    equal_cells = [
        (r, c)
        for r in range(4)
        for c in range(width)
        if (grid[r][c] == 0) == (grid[5 + r][c] == 0)
    ]
    rng.shuffle(equal_cells)
    orient_top = bool(rng.randrange(2))
    for r, c in equal_cells:
        if have >= target:
            break
        top_nonzero = grid[r][c] != 0
        bottom_nonzero = grid[5 + r][c] != 0
        if not top_nonzero and not bottom_nonzero:
            if orient_top:
                grid[r][c] = top_color
            else:
                grid[5 + r][c] = bot_color
        else:  # both are nonzero; clear one side to create a difference
            if orient_top:
                grid[5 + r][c] = 0
            else:
                grid[r][c] = 0
        orient_top = not orient_top
        have += 1
    if have < target:
        raise ValueError(f"could not realize xor_target={target} on width {width}")


def _avoid_full_xor(grid, width, top_color, bot_color, rng):
    """Keep ordinary draws from collapsing to an all-3 output."""
    if _xor_count(grid) != 4 * width:
        return
    cells = [(r, c) for r in range(4) for c in range(width)]
    rng.shuffle(cells)
    r, c = cells[0]
    if grid[r][c] == 0:
        grid[r][c] = top_color
    else:
        grid[5 + r][c] = bot_color


def _ensure_panel_activity_preserving_xor(grid, width, top_color, bot_color):
    """Repair a blank panel without turning the other panel blank.

    If the populated side has multiple XOR cells, flip one cell's orientation.
    If it has only one, activate the blank side on a different equal-zero cell;
    the requested XOR count is a minimum, so that safe extra difference is valid.
    """
    cells = [(r, c) for r in range(4) for c in range(width)]
    top_count = sum(grid[r][c] != 0 for r, c in cells)
    bottom_count = sum(grid[5 + r][c] != 0 for r, c in cells)
    if top_count == 0:
        if bottom_count >= 2:
            r, c = next((r, c) for r, c in cells if grid[5 + r][c] != 0)
            grid[r][c] = top_color
            grid[5 + r][c] = 0
        else:
            r, c = next(
                (r, c) for r, c in cells
                if grid[r][c] == 0 and grid[5 + r][c] == 0
            )
            grid[r][c] = top_color
    top_count = sum(grid[r][c] != 0 for r, c in cells)
    bottom_count = sum(grid[5 + r][c] != 0 for r, c in cells)
    if bottom_count == 0:
        if top_count >= 2:
            r, c = next((r, c) for r, c in cells if grid[r][c] != 0)
            grid[5 + r][c] = bot_color
            grid[r][c] = 0
        else:
            r, c = next(
                (r, c) for r, c in cells
                if grid[r][c] == 0 and grid[5 + r][c] == 0
            )
            grid[5 + r][c] = bot_color


def _draw_from_degenerate(name, width, rng):
    grid = full_grid(9, width, 0)
    top_color = rng.choice([1, 2, 3, 4, 5])
    bot_color = rng.choice([6, 7, 8, 9])
    separator = rng.choice([c for c in range(1, 10) if c not in {top_color, bot_color}])
    for c in range(width):
        grid[4][c] = separator
    if name == "same_panels":
        for r in range(4):
            for c in range(width):
                occupied = rng.random() < 0.5
                grid[r][c] = top_color if occupied else 0
                grid[5 + r][c] = bot_color if occupied else 0
        return grid
    if name == "disjoint_panels":
        for r in range(4):
            for c in range(width):
                if rng.random() < 0.5:
                    grid[r][c] = top_color
                else:
                    grid[5 + r][c] = bot_color
        return grid
    if name == "all_filled":
        for r in range(4):
            for c in range(width):
                grid[r][c] = top_color
                grid[5 + r][c] = bot_color
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")
