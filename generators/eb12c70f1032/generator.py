"""Semantic generator for ARC task eb12c70f1032.

Each nonzero same-color component becomes one bottom-aligned bar whose height
is the component area and whose color is preserved.  Components are ordered by
left edge, then top edge, then color, with one zero separator column between
bars.  The output therefore has height equal to the largest area and width
``2 * object_count - 1``.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "eb12c70f1032"
TASK_ID = "eb12c70f1032"
VERSION = "3.0.0"
RULE_HASH = "548dafbcb9a9"
SUMMARY = (
    "Measure same-color four-connected object areas, order objects by left "
    "edge/top edge/color, and draw their colors as separated bottom-aligned "
    "bars with those heights."
)
INVARIANTS = [
    "background is zero and every foreground color belongs to one component",
    "generated scenes contain two through five same-color four-connected objects",
    "ordinary profiles have distinct left edges; dedicated profiles exercise left-edge and origin ties",
    "bar height equals object area and bar order follows (left, top, color)",
    "the output height is the maximum object area and width is twice the object count minus one",
]


def _grid(*rows: str):
    return [[int(value) for value in row] for row in rows]


PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
_PUBLIC_INPUTS = {
    "public_1": _grid(
        "000000004400", "022000004440", "022006600040", "000000600000",
        "000000000000", "000000000000", "000000000000", "000000000000",
    ),
    "public_2": _grid(
        "00000000000000", "00000770000000", "00000770000000",
        "55500000000000", "00000000033300", "00000000003000",
        "00000000003000", "00000000000000", "00000000000000",
    ),
    "public_3": _grid(
        "0880000000000", "0080000000000", "0000000000000",
        "0000000000000", "0000110000000", "0000111000000",
        "0000001000990", "0000000000990", "0000000000000",
        "0000000000000",
    ),
    "public_4": _grid(
        "000000220000", "000000020000", "066600000000", "006000000000",
        "006000000440", "000000000440", "000000000000", "000000000000",
    ),
}

# The ordered area tuples are deliberately unique.  They make every general
# scene profile recoverable from the returned grid rather than from hidden
# generation metadata.  Canonical area orders are reserved for PUBLIC_PROFILES.
GENERAL_SPECS = {
    "pair_rise": {"areas": (3, 7), "order": "unique"},
    "pair_fall": {"areas": (7, 3), "order": "unique"},
    "trio_rise": {"areas": (2, 5, 8), "order": "unique"},
    "trio_fall": {"areas": (8, 5, 2), "order": "unique"},
    "trio_peak": {"areas": (3, 8, 5), "order": "unique"},
    "trio_valley": {"areas": (7, 2, 5), "order": "unique"},
    "four_rise": {"areas": (2, 4, 6, 8), "order": "unique"},
    "four_fall": {"areas": (8, 6, 4, 2), "order": "unique"},
    "four_mixed": {"areas": (5, 2, 8, 4), "order": "unique"},
    "five_rise": {"areas": (2, 3, 5, 7, 9), "order": "unique"},
    "five_fall": {"areas": (9, 7, 5, 3, 2), "order": "unique"},
    "five_mixed": {"areas": (4, 8, 2, 9, 6), "order": "unique"},
    "tied_areas": {"areas": (4, 4, 7), "order": "unique"},
    "left_edge_tie": {"areas": (3, 6, 8), "order": "left_tie"},
    "origin_tie": {"areas": (3, 5, 8), "order": "origin_tie"},
    "tall_mix": {"areas": (9, 3, 6), "order": "unique"},
}
GENERAL_PROFILES = tuple(GENERAL_SPECS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
PROFILE_TO_CODE = {profile: index for index, profile in enumerate(SCENE_PROFILES)}
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_code": {
        "type": "int",
        "default": "balanced schedule over 0..19",
        "valid": "0..19",
        "doc": "Four complete official scenes plus count, area-order, tie, and height contrasts.",
    }
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _components4_color(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                cr, cc = cell
                for neighbor in (
                    (cr - 1, cc), (cr + 1, cc),
                    (cr, cc - 1), (cr, cc + 1),
                ):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and neighbor not in seen and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "r1": min(r for r, _ in cells),
                "c1": min(c for _, c in cells),
            })
    return tuple(components)


def _sorted_components(grid):
    return tuple(sorted(
        _components4_color(grid),
        key=lambda obj: (obj["c1"], obj["r1"], obj["color"]),
    ))


def _chart(components):
    height = max(obj["size"] for obj in components)
    width = 2 * len(components) - 1
    output = [[0] * width for _ in range(height)]
    for index, obj in enumerate(components):
        for row in range(height - obj["size"], height):
            output[row][2 * index] = obj["color"]
    return output


def rule_mirror(grid):
    """Broad, input-pure mirror of the executable object-to-chart rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _sorted_components(grid)
    if not components:
        raise ValueError("the executable rule requires at least one foreground object")
    return _chart(components)


def _ordering_mode(components):
    left_counts = Counter(obj["c1"] for obj in components)
    origin_counts = Counter((obj["c1"], obj["r1"]) for obj in components)
    repeated_left = sorted(count for count in left_counts.values() if count > 1)
    repeated_origin = sorted(count for count in origin_counts.values() if count > 1)
    if repeated_origin == [2] and repeated_left == [2]:
        return "origin_tie"
    if repeated_left == [2] and not repeated_origin:
        return "left_tie"
    if not repeated_left:
        return "unique"
    return "unsupported"


def _facts(grid):
    components = _sorted_components(grid)
    colors = tuple(obj["color"] for obj in components)
    areas = tuple(obj["size"] for obj in components)
    return {
        "components": components,
        "object_count": len(components),
        "colors": colors,
        "areas": areas,
        "order_mode": _ordering_mode(components),
        "output": _chart(components) if components else None,
    }


def _reflect_horizontal(grid):
    return tuple(tuple(reversed(row)) for row in grid)


_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_CORE_LOOKUP = {}
for _profile, _grid_values in _PUBLIC_INPUTS.items():
    _core = tuple(map(tuple, _grid_values))
    for _variant in {_core, _reflect_horizontal(_core)}:
        _shape = (len(_variant), len(_variant[0]))
        _PUBLIC_CORE_LOOKUP.setdefault(_shape, {})[_variant] = _profile


def _public_family(grid, facts):
    if facts["object_count"] != 3:
        return None
    height, width = len(grid), len(grid[0])
    matches = set()
    for (core_height, core_width), lookup in _PUBLIC_CORE_LOOKUP.items():
        if core_height > height or core_width > width:
            continue
        for top in range(height - core_height + 1):
            for left in range(width - core_width + 1):
                core = tuple(
                    tuple(grid[row][left:left + core_width])
                    for row in range(top, top + core_height)
                )
                profile = lookup.get(core)
                if profile is not None:
                    matches.add(profile)
    return next(iter(matches)) if len(matches) == 1 else None


def _general_profile(facts):
    for profile, spec in GENERAL_SPECS.items():
        if facts["areas"] == spec["areas"] and facts["order_mode"] == spec["order"]:
            return profile
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 22 or not 7 <= width <= 26:
        errors.append("calibrated chart scenes require height 7..22 and width 7..26")
    facts = _facts(grid)
    if not 2 <= facts["object_count"] <= 5:
        errors.append("calibrated chart scenes require two through five objects")
    if 0 in facts["colors"] or len(facts["colors"]) != len(set(facts["colors"])):
        errors.append("each generated object must have one distinct nonzero color")
    if any(not 2 <= area <= 9 for area in facts["areas"]):
        errors.append("generated object areas must lie between two and nine")
    palette = {value for row in grid for value in row}
    if palette != {0, *facts["colors"]}:
        errors.append("the palette must be zero plus exactly the object colors")
    public_profile = _public_family(grid, facts)
    profile = public_profile or _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("object areas and comparator geometry do not match a declared scene profile")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "scene_profile": profile,
        "public_profile": public_profile,
    })
    return {
        "errors": errors,
        "scene_profile": profile,
        "facts": details,
        "output": facts["output"],
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_code": PROFILE_TO_CODE[analysis["scene_profile"]]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _random_shape(rng, size):
    box_height = max(3, (size + 1) // 2)
    start = (rng.randrange(box_height), 0)
    cells = {start}
    while len(cells) < size:
        frontier = sorted({
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= row + dr < box_height and 0 <= col + dc < 3
            and (row + dr, col + dc) not in cells
        })
        cells.add(rng.choice(frontier))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _paint(grid, shape, top, left, color):
    for row, col in shape:
        grid[top + row][left + col] = color


def _general_scene(profile, rng):
    spec = GENERAL_SPECS[profile]
    areas = spec["areas"]
    if spec["order"] == "left_tie":
        colors = rng.sample(range(1, 10), 3)
        top_pad, left_pad = rng.randrange(0, 4), rng.randrange(0, 4)
        height, width = 10 + top_pad + rng.randrange(0, 3), 12 + left_pad + rng.randrange(0, 4)
        grid = [[0] * width for _ in range(height)]
        first = ((0, 0), (0, 1), (1, 0))
        second = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
        third = _random_shape(rng, 8)
        _paint(grid, first, top_pad, left_pad, colors[0])
        _paint(grid, second, top_pad + 3, left_pad, colors[1])
        _paint(grid, third, top_pad + rng.randrange(0, 3), left_pad + 6, colors[2])
        return grid
    if spec["order"] == "origin_tie":
        colors = sorted(rng.sample(range(1, 10), 3))
        top_pad, left_pad = rng.randrange(0, 4), rng.randrange(0, 4)
        height, width = 10 + top_pad + rng.randrange(0, 3), 12 + left_pad + rng.randrange(0, 4)
        grid = [[0] * width for _ in range(height)]
        first = ((0, 0), (0, 1), (1, 0))
        second = ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2))
        third = _random_shape(rng, 8)
        _paint(grid, first, top_pad, left_pad, colors[0])
        _paint(grid, second, top_pad, left_pad, colors[1])
        _paint(grid, third, top_pad + rng.randrange(0, 3), left_pad + 6, colors[2])
        return grid

    count = len(areas)
    colors = rng.sample(range(1, 10), count)
    left_pad, right_pad = rng.randrange(0, 4), rng.randrange(0, 4)
    width = left_pad + 4 * count - 1 + right_pad
    height = max(8, max((area + 1) // 2 for area in areas) + 3) + rng.randrange(0, 6)
    grid = [[0] * width for _ in range(height)]
    for index, (area, color) in enumerate(zip(areas, colors)):
        shape = _random_shape(rng, area)
        shape_height = 1 + max(row for row, _ in shape)
        top = rng.randrange(0, height - shape_height + 1)
        left = left_pad + 4 * index
        _paint(grid, shape, top, left, color)
    return grid


_PUBLIC_CODES = tuple(
    (top, bottom, left, right, reflected)
    for row_padding in range(7)
    for top in range(row_padding + 1)
    for bottom in (row_padding - top,)
    for col_padding in range(7)
    for left in range(col_padding + 1)
    for right in (col_padding - left,)
    for reflected in (False, True)
)


def _embed_core(core, code):
    top, bottom, left, right, reflected = code
    if reflected:
        core = _reflect_horizontal(core)
    height = top + len(core) + bottom
    width = left + len(core[0]) + right
    grid = [[0] * width for _ in range(height)]
    for row, values in enumerate(core):
        grid[top + row][left:left + len(values)] = values
    return grid


def _unique_public_codes(core):
    unique = []
    seen = set()
    for code in _PUBLIC_CODES:
        grid = _embed_core(core, code)
        key = tuple(map(tuple, grid))
        if key not in seen:
            seen.add(key)
            unique.append(code)
    return tuple(unique)


_PUBLIC_PROFILE_CODES = {
    profile: _unique_public_codes(tuple(map(tuple, grid)))
    for profile, grid in _PUBLIC_INPUTS.items()
}


def _embed_public(profile, variant_index):
    core = tuple(map(tuple, _PUBLIC_INPUTS[profile]))
    codes = _PUBLIC_PROFILE_CODES[profile]
    return _embed_core(core, codes[variant_index % len(codes)])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_code"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    explicit = overrides.get("scene_code") is not None
    if explicit:
        scene_code = ctx.draw_int("scene_code", 0, len(SCENE_PROFILES) - 1)
    else:
        # The quotient term keeps the common seed==sample census stream
        # balanced too: within each 20-draw block it visits one parity twice,
        # and the next block visits the other parity, yielding 250 occurrences
        # of every profile over 5,000 draws.  With a fixed seed, sample indexes
        # 0..19 still visit every profile exactly once.
        scheduled = (
            seed + sample_index
            + sample_index // len(SCENE_PROFILES)
            + 7 * band_index
        ) % len(SCENE_PROFILES)
        scene_code = ctx.draw_int("scene_code", scheduled, scheduled)
    profile = SCENE_PROFILES[scene_code]
    # Six independent rows and columns of zero padding plus reflection provide
    # 1,568 public variants per official core.  Mixing both producer counters
    # keeps the seed-advancing, sample-advancing, and seed==sample workflows
    # injective over their bounded review/training windows.
    variant_index = seed + sample_index + band_index
    if profile in PUBLIC_PROFILES:
        if explicit:
            grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
        else:
            grid = _embed_public(profile, variant_index)
    else:
        grid = _general_scene(profile, ctx.draw_rng(f"scene:{profile}"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid bar-chart lesson: " + "; ".join(errors))
    return grid
