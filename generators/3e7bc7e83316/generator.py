"""Semantic generator for ARC task 3e7bc7e83316.

The input contains monochromatic 4-connected objects.  Each object keeps its
shape and is recolored from its cell count: 1 -> 2, 2 -> 4, 3 -> 6, and every
larger supported object -> 8.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e7bc7e83316"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "33c17f76d56e"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Find each monochromatic orthogonally connected nonzero object, preserve "
    "its cells, and recolor it by exact size: size 1 to red(2), size 2 to "
    "yellow(4), size 3 to magenta(6), and every size above 3 to cyan(8)."
)
INVARIANTS = [
    "the background is zero",
    "objects are monochromatic 4-connected components",
    "object shape and position are preserved by the rule",
    "input colors are deliberately not a proxy for object size",
    "generated lessons cover sizes 1, 2, 3 and multiple sizes above 3",
]

SCENE_PROFILES = (
    "canonical_small",
    "cross_size_alias",
    "large_equivalence",
    "gap_sizes",
)
GRID_SIZES = ("5x5", "5x6", "6x6", "7x8", "8x7", "9x9", "10x10")
SHAPE_STYLES = ("linear", "bent")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "layout_scale": {
        "type": "str",
        "default": "schedule anchored to canonical 5x5 and 5x6",
        "valid": "|".join(GRID_SIZES),
    },
    "shape_style": {
        "type": "str",
        "default": "alternating linear and bent polyominoes",
        "valid": "|".join(SHAPE_STYLES),
    },
}

_PROFILE_SIZES = {
    "canonical_small": (1, 1, 2, 3),
    "cross_size_alias": (1, 2, 3, 4),
    "large_equivalence": (1, 2, 3, 4, 5),
    "gap_sizes": (1, 3, 4, 5),
}

# The eight-slot schedule makes every four-demo lesson cover all four semantic
# profiles while anchoring exact canonical dimensions twice per cycle.
_SCHEDULE = (
    ("canonical_small", "5x5", "linear"),
    ("cross_size_alias", "6x6", "bent"),
    ("large_equivalence", "7x8", "linear"),
    ("gap_sizes", "8x7", "bent"),
    ("canonical_small", "5x6", "bent"),
    ("cross_size_alias", "9x9", "linear"),
    ("large_equivalence", "10x10", "bent"),
    ("gap_sizes", "6x6", "linear"),
)

_LINEAR_BASES = {
    size: (tuple((0, col) for col in range(size)),) for size in range(1, 6)
}
_BENT_BASES = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    height = max(row for row, _ in cells) + 1
    return _normalize((col, height - 1 - row) for row, col in cells)


def _reflect(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    width = max(col for _, col in cells) + 1
    return _normalize((row, width - 1 - col) for row, col in cells)


def _orientations(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    current = _normalize(cells)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


def _shape_pool(size: int, style: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    bases = _LINEAR_BASES[size] if style == "linear" else _BENT_BASES[size]
    shapes = set()
    for base in bases:
        shapes.update(_orientations(base))
    return tuple(sorted(shapes))


def _target_color(size: int) -> int:
    return {1: 2, 2: 4, 3: 6}.get(size, 8)


def _pick_distinct_colors(rng, sizes: tuple[int, ...]) -> list[int]:
    pool = list(range(1, 10))
    rng.shuffle(pool)
    chosen: list[int] = []
    for size in sizes:
        legal = [color for color in pool if color != _target_color(size)]
        if not legal:
            raise RuntimeError("unable to choose a non-answer input palette")
        color = legal[0]
        pool.remove(color)
        chosen.append(color)
    return chosen


def _profile_colors(profile: str, sizes: tuple[int, ...], rng) -> list[int]:
    if profile in ("canonical_small", "large_equivalence"):
        return _pick_distinct_colors(rng, sizes)

    shared_targets = {"cross_size_alias": (0, 1), "gap_sizes": (0, 1)}[profile]
    first, second = shared_targets
    forbidden = {_target_color(sizes[first]), _target_color(sizes[second])}
    shared = rng.choice([color for color in range(1, 10) if color not in forbidden])
    colors = [None] * len(sizes)
    colors[first] = shared
    colors[second] = shared
    used = {shared}
    for index, size in enumerate(sizes):
        if colors[index] is not None:
            continue
        legal = [
            color for color in range(1, 10)
            if color not in used and color != _target_color(size)
        ]
        color = rng.choice(legal)
        colors[index] = color
        used.add(color)
    return [int(color) for color in colors]


def _scheduled_choice(ctx, label: str, values: tuple[str, ...], desired: str) -> str:
    """Use GenCtx while guaranteeing the lesson schedule on default draws."""
    options = list(values)
    selected_index = ctx.draw_rng(label).randrange(len(options))
    desired_index = options.index(desired)
    options[selected_index], options[desired_index] = (
        options[desired_index], options[selected_index]
    )
    return ctx.draw_choice(label, options)


def _candidate_cells(shape, row0, col0):
    return tuple((row0 + row, col0 + col) for row, col in shape)


def _place_components(
    height: int,
    width: int,
    specs: list[tuple[int, int]],
    style: str,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()
    occupied_by_color: dict[int, set[tuple[int, int]]] = {}
    placements: dict[int, tuple[tuple[int, int], ...]] = {}
    order = sorted(range(len(specs)), key=lambda index: (-specs[index][0], index))

    def fits(cells, color):
        if any(cell in occupied for cell in cells):
            return False
        same_color = occupied_by_color.get(color, set())
        for row, col in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (row + dr, col + dc) in same_color:
                    return False
        return True

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        spec_index = order[depth]
        size, color = specs[spec_index]
        candidates = []
        for shape in _shape_pool(size, style):
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            for row0 in range(height - shape_height + 1):
                for col0 in range(width - shape_width + 1):
                    candidates.append(_candidate_cells(shape, row0, col0))
        rng.shuffle(candidates)
        for cells in candidates:
            if not fits(cells, color):
                continue
            occupied.update(cells)
            occupied_by_color.setdefault(color, set()).update(cells)
            placements[spec_index] = cells
            if search(depth + 1):
                return True
            del placements[spec_index]
            occupied.difference_update(cells)
            occupied_by_color[color].difference_update(cells)
        return False

    if not search(0):
        raise RuntimeError(
            f"unable to place profile sizes {[size for size, _ in specs]} "
            f"in {height}x{width} with style={style}"
        )
    for index, (_, color) in enumerate(specs):
        for row, col in placements[index]:
            grid[row][col] = color
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            cells = []
            stack = [(row0, col0)]
            seen.add((row0, col0))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _is_linear(cells) -> bool:
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    return len(rows) == 1 or len(cols) == 1


def _analysis(grid):
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["rows must be nonempty"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"]}

    components = _components(grid)
    sizes = tuple(sorted(len(component["cells"]) for component in components))
    colors_by_size: dict[int, set[int]] = {}
    sizes_by_color: dict[int, set[int]] = {}
    for component in components:
        size = len(component["cells"])
        color = component["color"]
        colors_by_size.setdefault(size, set()).add(color)
        sizes_by_color.setdefault(color, set()).add(size)

    if len(components) < 3:
        errors.append(f"expected at least three objects, found {len(components)}")
    if any(size < 1 or size > 5 for size in sizes):
        errors.append(f"supported object sizes are 1..5, found {list(sizes)}")
    if len(set(sizes)) < 3:
        errors.append(f"need at least three distinct size classes, found {list(sizes)}")
    if sum(sizes) >= len(grid) * width:
        errors.append("background must retain at least one zero cell")

    repeated_size_different_colors = any(len(colors) >= 2 for colors in colors_by_size.values())
    same_color_different_sizes = any(len(size_set) >= 2 for size_set in sizes_by_color.values())
    multiple_large_sizes = len({size for size in sizes if size > 3}) >= 2
    if not (
        repeated_size_different_colors
        or same_color_different_sizes
        or multiple_large_sizes
    ):
        errors.append(
            "scene lacks a size-vs-input-color contrast or two distinct >3 sizes"
        )
    if components and all(
        component["color"] == _target_color(len(component["cells"]))
        for component in components
    ):
        errors.append("identity scene hides the recoloring operation")

    profile = next(
        (name for name, profile_sizes in _PROFILE_SIZES.items() if sizes == tuple(sorted(profile_sizes))),
        None,
    )
    large_components = [component for component in components if len(component["cells"]) >= 3]
    if large_components and all(_is_linear(component["cells"]) for component in large_components):
        shape_style = "linear"
    elif large_components and all(not _is_linear(component["cells"]) for component in large_components):
        shape_style = "bent"
    else:
        shape_style = None

    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "components": components,
        "sizes": sizes,
        "colors_by_size": colors_by_size,
        "sizes_by_color": sizes_by_color,
        "scene_profile": profile,
        "layout_scale": f"{len(grid)}x{width}",
        "shape_style": shape_style,
        "repeated_size_different_colors": repeated_size_different_colors,
        "same_color_different_sizes": same_color_different_sizes,
        "multiple_large_sizes": multiple_large_sizes,
    }


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["scene_profile"] not in SCENE_PROFILES:
        raise ValueError(f"unrecognized generated size profile {analysis['sizes']}")
    if analysis["layout_scale"] not in GRID_SIZES:
        raise ValueError(f"unrecognized generated grid size {analysis['layout_scale']}")
    if analysis["shape_style"] not in SHAPE_STYLES:
        raise ValueError("generated shape style is not exactly observable")
    return {
        "scene_profile": analysis["scene_profile"],
        "layout_scale": analysis["layout_scale"],
        "shape_style": analysis["shape_style"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the returned-grid teaching grammar, including canonical inputs."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """Task-linked predicate used by the strict semantic census."""
    return self_check(grid)


def rule_mirror(grid):
    """Input-pure test mirror; the canonical Racket program is authoritative."""
    output = [list(row) for row in grid]
    for component in _components(grid):
        color = _target_color(len(component["cells"]))
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_profile, scheduled_grid, scheduled_style = _SCHEDULE[sample_index % len(_SCHEDULE)]
    profile = _scheduled_choice(ctx, "scene_profile", SCENE_PROFILES, scheduled_profile)
    layout_scale = _scheduled_choice(ctx, "layout_scale", GRID_SIZES, scheduled_grid)
    shape_style = _scheduled_choice(ctx, "shape_style", SHAPE_STYLES, scheduled_style)

    height, width = (int(part) for part in layout_scale.split("x"))
    sizes = _PROFILE_SIZES[profile]
    rng = ctx.draw_rng(f"layout:{band}")
    colors = _profile_colors(profile, sizes, rng)
    grid = _place_components(
        height,
        width,
        list(zip(sizes, colors)),
        shape_style,
        rng,
    )
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"constructed invalid {profile!r} scene: {findings}")
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": profile,
        "layout_scale": layout_scale,
        "shape_style": shape_style,
    }
    if observed != expected:
        raise RuntimeError(f"axis observation mismatch: expected {expected}, got {observed}")
    return [row[:] for row in grid]


def _facts(grid):
    return _analysis(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "size_1_red": lambda grid: 1 in _facts(grid)["sizes"],
    "size_2_yellow": lambda grid: 2 in _facts(grid)["sizes"],
    "size_3_magenta": lambda grid: 3 in _facts(grid)["sizes"],
    "size_4_cyan": lambda grid: 4 in _facts(grid)["sizes"],
    "size_5_cyan": lambda grid: 5 in _facts(grid)["sizes"],
    "same_size_different_input_colors": lambda grid: _facts(grid)[
        "repeated_size_different_colors"
    ],
    "same_input_color_different_sizes": lambda grid: _facts(grid)[
        "same_color_different_sizes"
    ],
    "two_large_sizes_share_output_class": lambda grid: _facts(grid)[
        "multiple_large_sizes"
    ],
    "missing_size_two_gap": lambda grid: (
        1 in _facts(grid)["sizes"]
        and 2 not in _facts(grid)["sizes"]
        and 3 in _facts(grid)["sizes"]
    ),
}


def _recolor_by_component_order(grid):
    output = [list(row) for row in grid]
    components = sorted(
        _components(grid),
        key=lambda component: min(component["cells"]),
    )
    colors = (2, 4, 6, 8)
    for index, component in enumerate(components):
        color = colors[min(index, len(colors) - 1)]
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _recolor_by_ranked_distinct_size(grid):
    output = [list(row) for row in grid]
    distinct = sorted({len(component["cells"]) for component in _components(grid)})
    mapping = {
        size: (2, 4, 6, 8)[min(index, 3)]
        for index, size in enumerate(distinct)
    }
    for component in _components(grid):
        for row, col in component["cells"]:
            output[row][col] = mapping[len(component["cells"])]
    return output


def _recolor_by_input_color(grid):
    output = [list(row) for row in grid]
    mapping = {1: 2, 2: 4, 3: 6, 4: 8, 5: 8}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                output[row][col] = mapping.get(value, 8)
    return output


def _recolor_large_as_magenta(grid):
    output = [list(row) for row in grid]
    for component in _components(grid):
        size = len(component["cells"])
        color = {1: 2, 2: 4, 3: 6, 4: 8}.get(size, 6)
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _identity(grid):
    return [list(row) for row in grid]


LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "legacy input-color lookup": _recolor_by_input_color,
    "scan-order recoloring": _recolor_by_component_order,
    "ranked distinct-size classes": _recolor_by_ranked_distinct_size,
    "size five remains magenta": _recolor_large_as_magenta,
}

# The strict semantic gate verifies these witness-to-rival claims against the
# live Racket oracle, rather than treating feature presence as semantic proof.
SEMANTIC_RIVALS = LESSON_COMPETITORS
WITNESS_RIVALS = {
    "size_1_red": ["identity"],
    "size_2_yellow": ["identity"],
    "size_3_magenta": ["identity"],
    "size_4_cyan": ["identity"],
    "size_5_cyan": ["identity"],
    "same_size_different_input_colors": ["legacy input-color lookup"],
    "same_input_color_different_sizes": ["legacy input-color lookup"],
    "two_large_sizes_share_output_class": ["size five remains magenta"],
    "missing_size_two_gap": ["ranked distinct-size classes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the size rule")
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the size rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
