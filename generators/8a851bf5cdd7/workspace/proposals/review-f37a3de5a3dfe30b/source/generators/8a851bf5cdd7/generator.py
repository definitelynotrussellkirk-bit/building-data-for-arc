"""Generator for 8a851bf5cdd7 — transfer an A→B stencil onto query C.

The input contains three equal panels separated by full-height color-8
columns.  The first two panels use one color and define a binary edit stencil;
the third panel uses a different color and receives that stencil.
"""
from __future__ import annotations

from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a851bf5cdd7"
VERSION = "4.0.0"
TASK_ID = "8a851bf5cdd7"
SUMMARY = (
    "A 0-background grid contains three equal PHxPW panels separated by "
    "full-height color-8 columns. Panels A and B use one shared color and "
    "differ by additions and deletions; panel C uses a different color. "
    "Apply the A→B stencil to C: additions receive C's color and deletions "
    "become 0. The output is the transformed PHxPW query panel."
)

INVARIANTS = [
    "the input has three equal panels separated by exactly two full color-8 columns",
    "panel B differs from panel A by at least one deletion and one addition",
    "panels A and B share one nonzero color and panel C has one different nonzero color",
    "at least one addition and one deletion visibly affect the query panel",
    "additions are painted with the query color and deletions become zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
# Retained as named diagnostics for audits and hand-authored negative tests.  They
# are deliberately not advertised as generatable texture values.
DEGENERATE_TEXTURES = ("no_query", "identical_panels", "no_separator")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "variant": {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "palette_size": {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias": {
        "type": "str",
        "default": "three_panels_8sep",
        "valid": "three_panels_8sep",
    },
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PALETTE_POOLS = {
    "default": (1, 2, 3, 4, 5, 6, 7, 9),
    "warm": (1, 2, 3, 4),
    "cool": (5, 6, 7, 9),
    "varied": (9, 2, 6, 1, 7, 3, 5, 4),
}


def _normalize_overrides(overrides: dict) -> dict:
    """Reject undeclared knobs and make ``texture`` a true palette alias."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    normalized = dict(overrides)
    palette_kind = normalized.get("palette_kind")
    texture = normalized.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(
            f"texture override {texture!r} is not label-preserving; "
            f"expected one of {HELPFUL_TEXTURES}"
        )
    if palette_kind is not None and texture is not None and palette_kind != texture:
        raise ValueError(
            f"conflicting palette_kind={palette_kind!r} and texture={texture!r}"
        )
    if texture is not None:
        normalized["palette_kind"] = texture
    elif palette_kind is not None:
        normalized["texture"] = palette_kind
    return normalized


def _rectangular_integer_grid(grid) -> tuple[list[str], int, int]:
    """Return structural errors and dimensions without ever indexing unsafely."""
    if not isinstance(grid, list) or not grid:
        return ["empty grid"], 0, 0
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"], 0, 0

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color in 0..9")
    return errors, len(grid), width


def _split_panels(grid: Sequence[Sequence[int]], panel_width: int) -> list[list[list[int]]]:
    height = len(grid)
    return [
        [
            [grid[r][panel * (panel_width + 1) + c] for c in range(panel_width)]
            for r in range(height)
        ]
        for panel in range(3)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the labelable stencil domain; malformed grids return errors."""
    errors, height, width = _rectangular_integer_grid(grid)
    if errors:
        return errors
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append(f"difficulty must be one of easy, medium, hard or None; got {difficulty!r}")

    if width < 5 or (width - 2) % 3:
        errors.append("width must encode three equal panels plus two separators")
        return errors
    panel_width = (width - 2) // 3
    if panel_width < 1:
        errors.append("panels must have positive width")
        return errors

    separators = (panel_width, 2 * panel_width + 1)
    full_8_cols = [
        c for c in range(width) if all(grid[r][c] == 8 for r in range(height))
    ]
    if full_8_cols != list(separators):
        errors.append(
            f"expected full-color-8 separator columns {list(separators)}; "
            f"found {full_8_cols}"
        )
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if c not in separators and value == 8:
                errors.append(f"color 8 is reserved for separators; found at ({r},{c})")
                break
        if errors and errors[-1].startswith("color 8 is reserved"):
            break

    panels = _split_panels(grid, panel_width)
    colors = [
        {value for row in panel for value in row if value != 0}
        for panel in panels
    ]
    if len(colors[0]) != 1 or colors[0] != colors[1]:
        errors.append("panels A and B must use the same single nonzero color")
    if len(colors[2]) != 1:
        errors.append("query panel C must use exactly one nonzero color")
    if colors[0] and colors[2] and colors[0] == colors[2]:
        errors.append("query color must differ from the A/B color")

    a, b, c = panels
    additions = [
        (r, col)
        for r in range(height)
        for col in range(panel_width)
        if a[r][col] == 0 and b[r][col] != 0
    ]
    deletions = [
        (r, col)
        for r in range(height)
        for col in range(panel_width)
        if a[r][col] != 0 and b[r][col] == 0
    ]
    if not additions:
        errors.append("A→B stencil must contain at least one addition")
    if not deletions:
        errors.append("A→B stencil must contain at least one deletion")
    if additions and not any(c[r][col] == 0 for r, col in additions):
        errors.append("the query must expose at least one visible addition")
    if deletions and not any(c[r][col] != 0 for r, col in deletions):
        errors.append("the query must expose at least one visible deletion")
    return errors


def _mask(height: int, width: int, cells: set[tuple[int, int]]) -> list[list[int]]:
    return [
        [1 if (r, c) in cells else 0 for c in range(width)]
        for r in range(height)
    ]


def _recolor(grid: Sequence[Sequence[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in grid]


def _paste_panel(
    output: list[list[int]], panel_index: int, panel: Sequence[Sequence[int]], panel_width: int
) -> None:
    left = panel_index * (panel_width + 1)
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            output[r][left + c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy, medium, hard or None; got {difficulty!r}"
        )
    normalized = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )

    variant = ctx.draw_int_strict("variant", 0, 2)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    # Consume every declared axis. Texture is constrained to the selected
    # palette so it is an actual alias rather than a second inert knob.
    ctx.draw_choice("texture", (palette_kind,))
    ctx.draw_int_strict("palette_size", 3, 3)
    ctx.draw_choice("position_bias", ("three_panels_8sep",))
    ctx.draw_int_strict("n_distinct_colors", 3, 3)
    ctx.draw_choice("density", ("sparse",))

    if difficulty == "easy":
        panel_height = ctx.draw_int_strict("panel_h", 3, 3)
        panel_width = ctx.draw_int_strict("panel_w", 3, 3)
    elif difficulty == "hard":
        panel_height = ctx.draw_int_strict("panel_h", 4, 6)
        panel_width = ctx.draw_int_strict("panel_w", 4, 6)
    else:
        panel_height = ctx.draw_int_strict("panel_h", 3, 5)
        panel_width = ctx.draw_int_strict("panel_w", 3, 5)

    color_rng = ctx.draw_rng("colors")
    base_color, query_color = color_rng.sample(list(_PALETTE_POOLS[palette_kind]), 2)

    edit_count = variant + 1
    area = panel_height * panel_width
    all_cells = [(r, c) for r in range(panel_height) for c in range(panel_width)]
    layout_rng = ctx.draw_rng("stencil-layout")
    a_count = layout_rng.randint(edit_count, area - edit_count)
    a_cells = set(layout_rng.sample(all_cells, a_count))
    off_cells = [cell for cell in all_cells if cell not in a_cells]
    removals = set(layout_rng.sample(sorted(a_cells), edit_count))
    additions = set(layout_rng.sample(off_cells, edit_count))
    b_cells = (a_cells - removals) | additions

    query_rng = ctx.draw_rng("query-layout")
    query_count = query_rng.randint(1, area - 1)
    query_cells = set(query_rng.sample(all_cells, query_count))
    # Force at least one semantically observable add and delete. This prevents
    # valid-looking examples whose label happens to equal the query input.
    query_cells.discard(min(additions))
    query_cells.add(min(removals))

    a = _recolor(_mask(panel_height, panel_width, a_cells), base_color)
    b = _recolor(_mask(panel_height, panel_width, b_cells), base_color)
    c = _recolor(_mask(panel_height, panel_width, query_cells), query_color)

    output_width = 3 * panel_width + 2
    grid = full_grid(panel_height, output_width, 0)
    for separator in (panel_width, 2 * panel_width + 1):
        for r in range(panel_height):
            grid[r][separator] = 8
    _paste_panel(grid, 0, a, panel_width)
    _paste_panel(grid, 1, b, panel_width)
    _paste_panel(grid, 2, c, panel_width)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator error: {'; '.join(errors)}")
    return grid
