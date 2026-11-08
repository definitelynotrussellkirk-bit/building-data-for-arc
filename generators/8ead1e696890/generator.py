"""Generator for keeping every same-color component touching an outer border.

Ordinary samples contain at least three border-touching components, including
one that extends inward, so both "keep only the first two" and "keep only cells
on the border" are contradicted by construction.  All advertised controls are
strict and materially consumed.
"""
from __future__ import annotations

from itertools import cycle

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ead1e696890"
VERSION = "1.2.1"
TASK_ID = "8ead1e696890"
RULE_HASH = "e3401b50999e"
SUMMARY = "Keep every component touching any outer border; erase all interior components."

INVARIANTS = [
    "background is 0",
    "at least three components touch an outer border",
    "at least one border component contains a fully interior cell",
    "at least one component is fully interior",
    "different components are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 8),
    "varied": (9, 1, 6, 3, 8, 2, 7, 4, 5),
}
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_components")
HELPFUL_TEXTURES = ("plain",) + PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "5..18"},
    "border_objects": {"type": "int", "default": "rng 3..6", "valid": "3..8"},
    "interior_objects": {"type": "int", "default": "rng 1..4", "valid": "1..8"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "texture": {
        "type": "str",
        "default": "plain",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
        "doc": "A helpful palette alias or an explicit degenerate population.",
    },
}


def _validate_request(sample_index, difficulty, overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    for name, low, high in (
        ("grid_h", 5, 18),
        ("grid_w", 5, 18),
        ("border_objects", 3, 8),
        ("interior_objects", 1, 8),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"override {name!r}={value} outside [{low}, {high}]")
    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        value = overrides["palette_kind"]
        if type(value) is not str or value not in PALETTE_KINDS:
            raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str or value not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES + DEGENERATE_TEXTURES}")
        if (value in PALETTE_KINDS and overrides.get("palette_kind") is not None
                and overrides["palette_kind"] != value):
            raise ValueError("incompatible palette_kind and helpful texture alias")
        if value in DEGENERATE_TEXTURES:
            incompatible = [
                name for name in ("grid_h", "grid_w", "border_objects", "interior_objects", "palette_kind")
                if name in overrides and overrides[name] is not None
            ]
            if incompatible:
                raise ValueError(
                    f"incompatible degenerate texture {value!r} and override(s): {incompatible}"
                )


def _draw_count(ctx, name, difficulty, override_present):
    if name == "border_objects":
        bands = {"easy": (3, 3), "medium": (3, 5), "hard": (5, 6), None: (3, 5)}
        full = (3, 8)
    else:
        bands = {"easy": (1, 2), "medium": (2, 4), "hard": (4, 6), None: (1, 4)}
        full = (1, 8)
    return ctx.draw_int_strict(name, *(full if override_present else bands[difficulty]))


def _draw_dimension(ctx, name, difficulty, overrides, border_target, interior_target):
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, 5, 18)
    low, high = {
        "easy": (8, 10),
        "medium": (9, 13),
        "hard": (12, 18),
        None: (8, 14),
    }[difficulty]
    if max(border_target, interior_target) >= 7:
        low = max(low, 10)
    if border_target + interior_target >= 12:
        low = max(low, 12)
    return ctx.draw_int_strict(name, low, high)


def _adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1


def _greedy_positions(rng, candidates, count, blocked=()):
    order = list(candidates)
    rng.shuffle(order)
    chosen = []
    blocked = list(blocked)
    for position in order:
        if any(_adjacent(position, other) for other in blocked) or any(
                _adjacent(position, other) for other in chosen):
            continue
        chosen.append(position)
        if len(chosen) == count:
            return chosen
    return None


def _inward_border_candidates(height, width):
    candidates = []
    for column in range(1, width - 1):
        candidates.append({(0, column), (1, column)})
        candidates.append({(height - 1, column), (height - 2, column)})
    for row in range(1, height - 1):
        candidates.append({(row, 0), (row, 1)})
        candidates.append({(row, width - 1), (row, width - 2)})
    return candidates


def _positions(rng, height, width, border_target, interior_target):
    perimeter = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    ]
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    featured_candidates = _inward_border_candidates(height, width)
    for attempt in range(512):
        trial = rng if attempt == 0 else rng.__class__(rng.getrandbits(128) ^ attempt)
        trial.shuffle(featured_candidates)
        for featured in featured_candidates:
            remaining_border = _greedy_positions(
                trial, perimeter, border_target - 1, blocked=featured
            )
            if remaining_border is None:
                continue
            occupied = set(featured) | set(remaining_border)
            inside = _greedy_positions(trial, interior, interior_target, occupied)
            if inside is not None:
                border_components = [set(featured)] + [{position} for position in remaining_border]
                interior_components = [{position} for position in inside]
                return border_components, interior_components
    raise ValueError(
        "incompatible grid/object overrides: could not place exact separated border and interior components"
    )


def _component_colors(rng, palette_kind, count):
    palette = list(PALETTES[palette_kind])
    rng.shuffle(palette)
    return [color for _, color in zip(range(count), cycle(palette))]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = overrides.get("texture", "plain")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    border_target = _draw_count(
        ctx, "border_objects", difficulty,
        "border_objects" in overrides and overrides["border_objects"] is not None,
    )
    interior_target = _draw_count(
        ctx, "interior_objects", difficulty,
        "interior_objects" in overrides and overrides["interior_objects"] is not None,
    )
    height = _draw_dimension(ctx, "grid_h", difficulty, overrides, border_target, interior_target)
    width = _draw_dimension(ctx, "grid_w", difficulty, overrides, border_target, interior_target)

    if texture in PALETTE_KINDS:
        palette_kind = texture
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    layout_rng = ctx.draw_rng("component_positions")
    border_components, interior_components = _positions(
        layout_rng, height, width, border_target, interior_target
    )
    colors = _component_colors(
        ctx.draw_rng("component_colors"), palette_kind,
        border_target + interior_target,
    )
    grid = full_grid(height, width, 0)
    for cells, color in zip(border_components + interior_components, colors):
        for row, column in sorted(cells):
            grid[row][column] = color
    return grid


def _draw_from_degenerate(name):
    height, width = 9, 10
    grid = full_grid(height, width, 0)
    if name == "all_border":
        for (row, column), color in zip(
            ((0, 1), (0, 5), (height - 1, 2), (3, width - 1)),
            (4, 6, 3, 8),
        ):
            grid[row][column] = color
    elif name == "all_interior":
        for (row, column), color in zip(((2, 2), (4, 5), (6, 7)), (4, 6, 3)):
            grid[row][column] = color
    elif name != "no_components":
        raise ValueError(f"unknown degenerate texture: {name}")
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)):
        return ["expected a non-empty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be exact integer colors 0..9"]
    height, width = len(grid), len(grid[0])
    messages = []
    if not 5 <= height <= 18 or not 5 <= width <= 18:
        messages.append("ordinary grid dimensions must be in 5..18")
    border = interior = 0
    inward_border = False
    for color, cells in _components(grid):
        touches = any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
        border += int(touches)
        interior += int(not touches)
        inward_border |= touches and any(
            0 < r < height - 1 and 0 < c < width - 1 for r, c in cells
        )
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] not in (0, color):
                    messages.append("components are not separated by background")
    if border < 3:
        messages.append(f"expected at least three border-touching components, found {border}")
    if not inward_border:
        messages.append("expected a border component that extends into the interior")
    if interior < 1:
        messages.append("expected at least one fully interior component")
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    expected = {
        "grid_h": height,
        "grid_w": width,
        "border_objects": border,
        "interior_objects": interior,
    }
    for name, observed in expected.items():
        if name in overrides and overrides[name] is not None and overrides[name] != observed:
            messages.append(f"override {name} does not match observed value {observed}")
    return sorted(set(messages))
