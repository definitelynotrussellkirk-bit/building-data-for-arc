"""Teach crop/sort/stack by leftmost object position for d6115f669a8e.

Production labels remain the unchanged canonical Racket rule.  This module only
constructs lawful inputs and exposes diagnostic mirrors/rivals for review gates.
Default draws rotate through five complementary profiles so a five-example
lesson contains canonical morphology plus explicit shortcut counterexamples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "d6115f669a8e"
VERSION = "2.0.0"
RULE_HASH = "e09122d9163c"
SUMMARY = (
    "Zero-background scenes with exactly three monochromatic 4-connected objects. "
    "The reference crops each object, sorts by (leftmost column, top row), and "
    "left-aligns the crops in a vertical gallery with one blank separator row. "
    "A five-profile schedule preserves canonical 3-cell L motifs while exposing "
    "ordering, width/alignment, tied-left, and same-color grouping shortcuts."
)
INVARIANTS = [
    "background is 0 and the grid is rectangular",
    "exactly three monochromatic 4-connected objects, with 2 or 3 object colors",
    "objects are sorted by (leftmost column, top row)",
    "tight component crops are left-aligned with one blank row between crops",
    "input and output fit within 30x30",
]

HELPFUL_TEXTURES = (
    "canonical",
    "order_conflict",
    "width_contrast",
    "equal_left",
    "shared_color",
)
EXAMPLES_NEEDED = 5
_SCHEDULE = HELPFUL_TEXTURES
SCHEDULE_PROFILES = HELPFUL_TEXTURES
CANONICAL_PROFILES = ((7, 9), (9, 9), (9, 10))
AXES = {
    "grid_h": {"type": "int", "default": "canonical 7/9; otherwise banded 7..18", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "canonical 9/10; otherwise banded 9..20", "valid": "9..20"},
    "texture": {"type": "str", "default": "five-example teaching schedule", "valid": "|".join(HELPFUL_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))
_L3_VARIANTS = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_L3 = _L3_VARIANTS[0]
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_H4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_V3 = ((0, 0), (1, 0), (2, 0))
_L5 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))


def schedule_profile(seed, sample_index, difficulty=None):
    """Every five consecutive sample indices contain the complete curriculum."""
    return _SCHEDULE[sample_index % len(_SCHEDULE)]


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components(grid, *, connectivity=4):
    """Same-color connected components, matching Racket ``objects``."""
    h, w = len(grid), len(grid[0])
    steps = _CARD if connectivity == 4 else _CARD + ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            out.append((color, cells))
    return out


def _paint(grid, shape, top, left, color):
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _draw_int(ctx, name, low, high, default_low, default_high):
    # Explicit overrides retain the full advertised range in every band/profile.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default_low, default_high)


def _profile_layout(texture, rng, colors):
    """Return ``(shape, top, left, color)`` rows inside a 7x9 footprint."""
    if texture == "canonical":
        shapes = [rng.choice(_L3_VARIANTS) for _ in range(3)]
        # Distinct left edges and canonical 3-cell/2x2 morphology.
        return (
            (shapes[0], 1, 0, colors[0]),
            (shapes[1], 4, 3, colors[1]),
            (shapes[2], 1, 7, colors[2]),
        )
    if texture == "order_conflict":
        ordered = sorted(colors)
        # x order differs from top, color, and area order.
        return (
            (_T4, 4, 0, ordered[2]),
            (_L3, 0, 3, ordered[0]),
            (_L5, 2, 6, ordered[1]),
        )
    if texture == "width_contrast":
        # The first crop's right edge lies after the second crop's right edge;
        # widths 4/1/2 also distinguish left alignment from centering.
        return (
            (_H4, 0, 0, colors[0]),
            (_V3, 3, 2, colors[1]),
            (_L3, 1, 6, colors[2]),
        )
    if texture == "equal_left":
        # Same left edge requires the canonical top-row tie break.
        return (
            (_L3, 0, 1, colors[0]),
            (_L3_VARIANTS[3], 4, 1, colors[1]),
            (_T4, 2, 6, colors[2]),
        )
    if texture == "shared_color":
        # Two disconnected objects share a color; grouping by color is wrong.
        return (
            (_L3, 4, 0, colors[0]),
            (_T4, 0, 3, colors[0]),
            (_L5, 3, 6, colors[1]),
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
        HELPFUL_TEXTURES if texture_value is not None else (schedule_profile(seed, sample_index, difficulty),),
    )

    if texture == "canonical":
        profile = CANONICAL_PROFILES[(sample_index // len(_SCHEDULE)) % len(CANONICAL_PROFILES)]
        default_h = (profile[0], profile[0])
        default_w = (profile[1], profile[1])
    elif difficulty == "easy":
        default_h, default_w = (7, 9), (9, 12)
    elif difficulty == "hard":
        default_h, default_w = (12, 18), (14, 20)
    else:
        default_h, default_w = (9, 14), (11, 17)

    h = _draw_int(ctx, "grid_h", 7, 18, *default_h)
    w = _draw_int(ctx, "grid_w", 9, 20, *default_w)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(range(1, 10)), 3)
    layout = _profile_layout(texture, rng, colors)

    footprint_h = max(top + _bbox(shape)[2] + 1 for shape, top, left, color in layout)
    footprint_w = max(left + _bbox(shape)[3] + 1 for shape, top, left, color in layout)
    if footprint_h > h or footprint_w > w:
        raise ValueError(f"texture={texture} requires at most 7x9 but received {h}x{w}")
    offset_r = rng.randint(0, h - footprint_h)
    offset_c = rng.randint(0, w - footprint_w)
    grid = full_grid(h, w, 0)
    for shape, top, left, color in layout:
        _paint(grid, shape, top + offset_r, left + offset_c, color)

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

    errors = []
    height = len(grid)
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
    for color, cells in components:
        if not 1 <= len(cells) <= 8:
            errors.append(f"color-{color} object size {len(cells)} outside 1..8")
    boxes = [_bbox(cells) for _, cells in components]
    output_h = sum(bottom - top + 1 for top, left, bottom, right in boxes) + 2
    output_w = max(right - left + 1 for top, left, bottom, right in boxes)
    if output_h > 30 or output_w > 30:
        errors.append(f"stacked output {output_h}x{output_w} exceeds 30x30")
    return errors


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _render(grid, components, *, order="left", align="left", gap=1):
    def key(component):
        color, cells = component
        top, left, bottom, right = _bbox(cells)
        if order == "left":
            return left, top
        if order == "right":
            return right, top, left
        if order == "top":
            return top, left
        if order == "color":
            return color, left, top
        if order == "area":
            return len(cells), left, top
        if order == "reverse_left":
            return -left, top
        if order == "same_left_bottom_first":
            return left, -top
        raise ValueError(f"unknown order: {order}")

    ordered = sorted(components, key=key)
    pieces = []
    for color, cells in ordered:
        top, left, bottom, right = _bbox(cells)
        piece = full_grid(bottom - top + 1, right - left + 1, 0)
        for r, c in cells:
            piece[r - top][c - left] = grid[r][c]
        pieces.append(piece)
    if not pieces:
        return []
    width = max(len(piece[0]) for piece in pieces)
    output = []
    for index, piece in enumerate(pieces):
        if index:
            output.extend([[0] * width for _ in range(gap)])
        delta = width - len(piece[0])
        if align == "left":
            pad_left = 0
        elif align == "center":
            pad_left = delta // 2
        else:
            raise ValueError(f"unknown alignment: {align}")
        output.extend([([0] * pad_left) + row + ([0] * (delta - pad_left)) for row in piece])
    return output


def rule_mirror(grid):
    """Diagnostic Python mirror; Racket remains the production authority."""
    return _render(grid, _components(grid))


def _components_grouped_by_color(grid):
    groups = {}
    order = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            if color not in groups:
                groups[color] = []
                order.append(color)
            groups[color].append((r, c))
    return [(color, groups[color]) for color in order]


SEMANTIC_RIVALS = {
    "sort_by_top": lambda grid: _render(grid, _components(grid), order="top"),
    "sort_by_color": lambda grid: _render(grid, _components(grid), order="color"),
    "sort_by_area": lambda grid: _render(grid, _components(grid), order="area"),
    "reverse_left_order": lambda grid: _render(grid, _components(grid), order="reverse_left"),
    "sort_by_right_edge": lambda grid: _render(grid, _components(grid), order="right"),
    "center_align": lambda grid: _render(grid, _components(grid), align="center"),
    "same_left_bottom_first": lambda grid: _render(grid, _components(grid), order="same_left_bottom_first"),
    "group_by_color": lambda grid: _render(grid, _components_grouped_by_color(grid)),
    "gapless_stack": lambda grid: _render(grid, _components(grid), gap=0),
}


def _refutes_any(grid, names):
    if self_check(grid):
        return False
    target = rule_mirror(grid)
    return any(SEMANTIC_RIVALS[name](grid) != target for name in names)


WITNESS_RIVALS = {
    "ordering": ["sort_by_top", "sort_by_color", "sort_by_area", "reverse_left_order"],
    "width_and_alignment": ["sort_by_right_edge", "center_align"],
    "same_left_tie": ["same_left_bottom_first"],
    "component_identity": ["group_by_color"],
    "separator": ["gapless_stack"],
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, rivals=tuple(rivals): _refutes_any(grid, rivals))
    for name, rivals in WITNESS_RIVALS.items()
}

# These four wrong rules happen to fit all three canonical examples.  The
# scheduled synthetic profiles supply explicit counterexamples.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "sort_by_right_edge",
        "center_align",
        "same_left_bottom_first",
        "group_by_color",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid) -> bool:
    if self_check(grid):
        return False
    profile = (len(grid), len(grid[0]))
    if profile not in CANONICAL_PROFILES:
        return False
    components = _components(grid)
    if len({color for color, _ in components}) != 3:
        return False
    if len({_bbox(cells)[1] for _, cells in components}) != 3:
        return False
    return all(
        len(cells) == 3
        and (_bbox(cells)[2] - _bbox(cells)[0] + 1) == 2
        and (_bbox(cells)[3] - _bbox(cells)[1] + 1) == 2
        for _, cells in components
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Return declared rivals that fit all demos but disagree on the query."""
    qgrid = query["input"] if isinstance(query, dict) else query
    target = rule_mirror(qgrid)
    return [
        f"{name} fits every demo but disagrees on query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in demos)
        and rival(qgrid) != target
    ]
