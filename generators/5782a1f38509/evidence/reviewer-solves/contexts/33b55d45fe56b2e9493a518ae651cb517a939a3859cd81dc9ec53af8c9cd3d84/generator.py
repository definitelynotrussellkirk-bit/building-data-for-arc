"""Teach sort-by-cell-area, tight crop, and left-to-right packing.

The unchanged canonical Racket rule remains the production label authority.
This module constructs lawful zero-background scenes and exposes a diagnostic
Python mirror plus explicit wrong-rule competitors for review gates.

Default draws rotate through five complementary profiles.  Any five consecutive
sample indices therefore contain a canonical-scale anchor and counterexamples
to position/color/shape-size ordering, bounding-box-area sorting, vertical
alignment, gapless packing, rectangle filling, and grouping by color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "5782a1f38509"
VERSION = "2.0.0"
RULE_HASH = "a6b584fba994"
SUMMARY = (
    "Exactly three separated monochromatic 4-connected objects with distinct "
    "cell areas. The rule tightly crops the objects, sorts by cell count "
    "ascending, and top-aligns them left-to-right with one blank column gap. "
    "A five-profile schedule anchors canonical scale and refutes common "
    "position, color, bbox-area, alignment, fill, and grouping shortcuts."
)
INVARIANTS = [
    "background is 0 and the input is rectangular",
    "exactly three pairwise 4-separated monochromatic objects",
    "object cell areas are strictly distinct",
    "two or three object colors are used",
    "tight crops are sorted by cell area and top-aligned with one blank column gap",
    "input and output fit within 30x30",
]

HELPFUL_TEXTURES = (
    "canonical",
    "order_conflict",
    "bbox_metric",
    "alignment_gap_shape",
    "shared_color",
)
_SCHEDULE = HELPFUL_TEXTURES
SCHEDULE_PROFILES = HELPFUL_TEXTURES
EXAMPLES_NEEDED = 5
CANONICAL_PROFILES = ((5, 6), (5, 7))
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 5; otherwise banded 5..18",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 6/7; otherwise banded 6..20",
        "valid": "6..20",
    },
    "texture": {
        "type": "str",
        "default": "five-example teaching schedule",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_S1 = ((0, 0),)
_V2 = ((0, 0), (1, 0))
_H2 = ((0, 0), (0, 1))
_V3 = ((0, 0), (1, 0), (2, 0))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_CANONICAL_L4 = ((0, 0), (1, 0), (1, 1), (1, 2))
_CANONICAL_T4 = ((0, 0), (1, 0), (1, 1), (2, 0))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_H5 = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
_PATH5 = ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every five consecutive sample indices contain the full curriculum."""
    return _SCHEDULE[sample_index % len(_SCHEDULE)]


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _components(grid):
    """Return same-color 4-connected components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINALS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append((color, cells))
    return components


def _paint(grid, shape, top, left, color):
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _draw_int(ctx, name, low, high, default_low, default_high):
    """Use full advertised bounds for explicit overrides in every band."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default_low, default_high)


def _profile_layout(texture, sample_index, colors):
    """Return ``(shape, top, left, color)`` rows inside a 5x6 footprint."""
    ordered = sorted(colors)
    if texture == "canonical":
        if (sample_index // len(_SCHEDULE)) % 2 == 0:
            # Canonical train-1 morphology: areas 1, 2, 4.
            return (
                (_S1, 1, 0, colors[0]),
                (_V2, 1, 4, colors[1]),
                (_CANONICAL_L4, 3, 0, colors[2]),
            )
        # Canonical train-2 morphology: areas 1, 3, 4.
        return (
            (_S1, 0, 2, colors[0]),
            (_V3, 1, 4, colors[1]),
            (_CANONICAL_T4, 2, 0, colors[2]),
        )
    if texture == "order_conflict":
        # Area order is singleton -> domino -> square.  Left, top, color,
        # width, height, and descending-area orders all disagree.
        return (
            (_SQUARE4, 0, 0, ordered[0]),
            (_V2, 0, 4, ordered[2]),
            (_S1, 4, 2, ordered[1]),
        )
    if texture == "bbox_metric":
        # The 4-cell T has bbox area 6; the 5-cell line has bbox area 5.
        # Sorting by occupied cells and sorting by bbox area therefore differ.
        return (
            (_H5, 0, 0, ordered[1]),
            (_T4, 2, 1, ordered[0]),
            (_S1, 4, 0, ordered[2]),
        )
    if texture == "alignment_gap_shape":
        # Unequal heights refute bottom/center alignment.  PATH5 has holes in
        # its bbox, and every output needs the explicit one-column separators.
        return (
            (_PATH5, 0, 0, colors[2]),
            (_S1, 0, 4, colors[0]),
            (_V3, 2, 5, colors[1]),
        )
    if texture == "shared_color":
        # The singleton and 4-cell L are disconnected objects of one color.
        return (
            (_H2, 0, 0, colors[1]),
            (_CANONICAL_L4, 2, 0, colors[0]),
            (_S1, 4, 5, colors[0]),
        )
    raise ValueError(f"unknown texture: {texture}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(sorted(unknown))}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"override {name} must be an integer, not {type(value).__name__}")
    texture_value = overrides.get("texture")
    if texture_value is not None and not isinstance(texture_value, str):
        raise ValueError("override texture must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = ctx.draw_choice(
        "texture",
        HELPFUL_TEXTURES
        if texture_value is not None
        else (schedule_profile(seed, sample_index, difficulty),),
    )

    if texture in {"canonical", "order_conflict"}:
        profile = CANONICAL_PROFILES[(sample_index // len(_SCHEDULE)) % len(CANONICAL_PROFILES)]
        default_h = (profile[0], profile[0])
        default_w = (profile[1], profile[1])
    elif difficulty == "easy":
        default_h, default_w = (5, 8), (6, 10)
    elif difficulty == "hard":
        default_h, default_w = (12, 18), (14, 20)
    else:
        default_h, default_w = (8, 13), (10, 15)

    height = _draw_int(ctx, "grid_h", 5, 18, *default_h)
    width = _draw_int(ctx, "grid_w", 6, 20, *default_w)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(range(1, 10)), 3)
    layout = _profile_layout(texture, sample_index, colors)

    footprint_h = max(top + _bbox(shape)[2] + 1 for shape, top, left, color in layout)
    footprint_w = max(left + _bbox(shape)[3] + 1 for shape, top, left, color in layout)
    if footprint_h > height or footprint_w > width:
        raise ValueError(
            f"texture={texture} requires at most {footprint_h}x{footprint_w} "
            f"but received {height}x{width}"
        )
    offset_row = rng.randint(0, height - footprint_h)
    offset_col = rng.randint(0, width - footprint_w)
    grid = full_grid(height, width, 0)
    for shape, top, left, color in layout:
        _paint(grid, shape, top + offset_row, left + offset_col, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive profile {texture} violated invariants: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid is empty or not a row sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid contains an empty or non-sequence row"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer colors in 0..9 (booleans rejected)"]

    height = len(grid)
    errors = []
    if height > 30 or width > 30:
        errors.append("input exceeds 30x30")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three sortable objects, found {len(components)}")
        return errors
    colors = {color for color, _ in components}
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected two or three object colors, found {len(colors)}")
    sizes = [len(cells) for _, cells in components]
    if len(set(sizes)) != len(sizes):
        errors.append(f"object cell areas must be strictly distinct, found {sizes}")

    owner = {
        point: index
        for index, (_, cells) in enumerate(components)
        for point in cells
    }
    touching = False
    for (row, col), index in owner.items():
        for dr, dc in _CARDINALS:
            neighbor = row + dr, col + dc
            if neighbor in owner and owner[neighbor] != index:
                touching = True
                break
        if touching:
            break
    if touching:
        errors.append("distinct objects must not 4-touch")

    boxes = [_bbox(cells) for _, cells in components]
    output_h = max(bottom - top + 1 for top, left, bottom, right in boxes)
    output_w = sum(right - left + 1 for top, left, bottom, right in boxes) + 2
    if output_h > 30 or output_w > 30:
        errors.append(f"packed output {output_h}x{output_w} exceeds 30x30")
    return errors


def observe_overrides(grid):
    """Recover the exact dimension axes directly from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _render(components, *, order="area", align="top", gap=1, fill_bbox=False):
    def key(component):
        color, cells = component
        top, left, bottom, right = _bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        if order == "area":
            return len(cells)
        if order == "descending_area":
            return -len(cells), top, left
        if order == "left":
            return left, top
        if order == "top":
            return top, left
        if order == "color":
            return color, top, left
        if order == "bbox_area":
            return height * width, top, left
        if order == "width":
            return width, top, left
        if order == "height":
            return height, top, left
        raise ValueError(f"unknown order: {order}")

    pieces = []
    for color, cells in sorted(components, key=key):
        top, left, bottom, right = _bbox(cells)
        height = bottom - top + 1
        width = right - left + 1
        if fill_bbox:
            piece = full_grid(height, width, color)
        else:
            piece = full_grid(height, width, 0)
            for row, col in cells:
                piece[row - top][col - left] = color
        pieces.append(piece)
    if not pieces:
        return [[0]]

    output_h = max(len(piece) for piece in pieces)
    output_w = sum(len(piece[0]) for piece in pieces) + gap * (len(pieces) - 1)
    output = full_grid(output_h, output_w, 0)
    left = 0
    for piece in pieces:
        delta = output_h - len(piece)
        if align == "top":
            top = 0
        elif align == "bottom":
            top = delta
        elif align == "center":
            top = delta // 2
        else:
            raise ValueError(f"unknown alignment: {align}")
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value:
                    output[top + row][left + col] = value
        left += len(piece[0]) + gap
    return output


def rule_mirror(grid):
    """Diagnostic Python mirror; canonical Racket remains label authority."""
    return _render(_components(grid))


def _components_grouped_by_color(grid):
    groups = {}
    order = []
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            if color not in groups:
                groups[color] = []
                order.append(color)
            groups[color].append((row, col))
    return [(color, groups[color]) for color in order]


SEMANTIC_RIVALS = {
    "sort_by_left": lambda grid: _render(_components(grid), order="left"),
    "sort_by_top": lambda grid: _render(_components(grid), order="top"),
    "sort_by_color": lambda grid: _render(_components(grid), order="color"),
    "descending_area": lambda grid: _render(_components(grid), order="descending_area"),
    "sort_by_bbox_area": lambda grid: _render(_components(grid), order="bbox_area"),
    "sort_by_width": lambda grid: _render(_components(grid), order="width"),
    "sort_by_height": lambda grid: _render(_components(grid), order="height"),
    "bottom_align": lambda grid: _render(_components(grid), align="bottom"),
    "center_align": lambda grid: _render(_components(grid), align="center"),
    "gapless_pack": lambda grid: _render(_components(grid), gap=0),
    "fill_bbox": lambda grid: _render(_components(grid), fill_bbox=True),
    "group_by_color": lambda grid: _render(_components_grouped_by_color(grid)),
}


def _refutes_any(grid, names):
    if self_check(grid):
        return False
    target = rule_mirror(grid)
    return any(SEMANTIC_RIVALS[name](grid) != target for name in names)


WITNESS_RIVALS = {
    "ordering": [
        "sort_by_left",
        "sort_by_top",
        "sort_by_color",
        "descending_area",
        "sort_by_width",
        "sort_by_height",
    ],
    "area_metric": ["sort_by_bbox_area"],
    "vertical_alignment": ["bottom_align", "center_align"],
    "separator": ["gapless_pack"],
    "shape_preservation": ["fill_bbox"],
    "component_identity": ["group_by_color"],
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, rivals=tuple(rivals): _refutes_any(grid, rivals))
    for name, rivals in WITNESS_RIVALS.items()
}

# These two wrong rules fit all three canonical pairs.  Scheduled synthetic
# profiles provide generated counterexamples to both.
CANONICAL_SHORTCUTS = {
    "sort_by_height": SEMANTIC_RIVALS["sort_by_height"],
    "group_by_color": SEMANTIC_RIVALS["group_by_color"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid) -> bool:
    if self_check(grid):
        return False
    if (len(grid), len(grid[0])) not in CANONICAL_PROFILES:
        return False
    components = _components(grid)
    if len({color for color, _ in components}) != 3:
        return False
    return tuple(sorted(len(cells) for _, cells in components)) in {
        (1, 2, 4),
        (1, 3, 4),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Return declared rivals that fit all demos but change the query answer."""
    query_grid = query["input"] if isinstance(query, dict) else query
    target = rule_mirror(query_grid)
    return [
        f"{name} fits every demo but disagrees on query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in demos)
        and rival(query_grid) != target
    ]
