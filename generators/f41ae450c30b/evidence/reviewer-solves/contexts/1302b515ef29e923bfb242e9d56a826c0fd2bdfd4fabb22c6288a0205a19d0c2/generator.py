"""Lesson-oriented generator for ``f41ae450c30b``.

The task builds a visibility adjacency matrix for colored domino components.
Components are ordered from left to right by centroid (then top to bottom); the
diagonal records component colors and an off-diagonal cell is cyan (8) exactly
when the corresponding components share an unobstructed row or column.

Every ordinary generated scene contains a genuine *occlusion* counterexample:
three collinear components A-B-C where A sees B, B sees C, and B blocks A from
C.  This is stronger than merely producing both 0 and 8 in the answer, because
a non-aligned pair also produces 0 but does not teach that third objects block
line of sight.  All declared controls are exact, observable, and legal in every
difficulty band.
"""
from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]
ComponentCells = tuple[Cell, ...]

GENERATOR_ID = "f41ae450c30b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8601bafc35ff"

SUMMARY = (
    "A zero-background grid contains three or four separated, distinctly "
    "colored domino components. Three components form a horizontal or vertical "
    "A-B-C line: adjacent pairs have clear line of sight, while the middle "
    "component blocks the two outer components. Sort components by centroid "
    "column then centroid row and emit an N×N matrix whose diagonal is the "
    "component colors and whose off-diagonal entries are 8 exactly for "
    "unobstructed row/column visibility, otherwise 0."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "three or four 4-connected domino components use distinct nonzero, non-cyan colors",
    "different components have one-cell 8-neighbor separation",
    "every generated scene has a collinear outer pair occluded by a third component",
    "scene_profile, n, and layout_axis are recoverable exactly from the returned grid",
]

SCENE_PROFILE_SPECS: dict[str, tuple[int, int]] = {
    "canonical_7x10": (7, 10),
    "canonical_8x11": (8, 11),
    "canonical_8x12": (8, 12),
    "canonical_9x12": (9, 12),
    "expanded_10x14": (10, 14),
    "expanded_12x16": (12, 16),
}
SCENE_PROFILES = tuple(SCENE_PROFILE_SPECS)
_PROFILE_BY_DIMS = {dims: name for name, dims in SCENE_PROFILE_SPECS.items()}
LAYOUT_AXES = ("horizontal", "vertical")
_COMPONENT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted keyed draw; all values legal in every band",
        "valid": "canonical_7x10|canonical_8x11|canonical_8x12|canonical_9x12|expanded_10x14|expanded_12x16",
    },
    "n": {
        "type": "int",
        "default": "weighted keyed draw, usually 4",
        "valid": "3..4",
    },
    "layout_axis": {
        "type": "str",
        "default": "keyed draw",
        "valid": "horizontal|vertical",
    },
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if not isinstance(value, str) or value not in SCENE_PROFILE_SPECS:
            raise ValueError(f"invalid scene_profile override: {value!r}")
    if "n" in overrides:
        value = overrides["n"]
        if isinstance(value, bool) or not isinstance(value, int) or value not in (3, 4):
            raise ValueError(f"invalid n override: {value!r}")
    if "layout_axis" in overrides:
        value = overrides["layout_axis"]
        if not isinstance(value, str) or value not in LAYOUT_AXES:
            raise ValueError(f"invalid layout_axis override: {value!r}")


def _scene_options(difficulty: Any) -> tuple[str, ...]:
    c7, c811, c812, c912, e10, e12 = SCENE_PROFILES
    if difficulty == "easy":
        return (c7, c7, c811, c811, c812, c912, e10, e12)
    if difficulty == "hard":
        return (c7, c811, c812, c912, c912, e10, e10, e12, e12)
    return (c7, c811, c811, c812, c812, c912, e10, e12)


def _n_options(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (4, 4, 4, 3)
    if difficulty == "hard":
        return (4, 4, 3, 4)
    return (4, 3, 4, 4)


def _layout_options(difficulty: Any) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("horizontal", "vertical", "horizontal")
    if difficulty == "hard":
        return ("vertical", "horizontal", "vertical")
    return LAYOUT_AXES


def _component_records(grid: Grid) -> list[dict[str, Any]]:
    """Extract same-color 4-connected components without using rule helpers."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
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


def _aligned(a: ComponentCells, b: ComponentCells) -> bool:
    return any(ra == rb or ca == cb for ra, ca in a for rb, cb in b)


def _visible(grid: Grid, a: ComponentCells, b: ComponentCells) -> bool:
    """True when some aligned cell pair has no third-component cell between."""
    a_set, b_set = set(a), set(b)
    for ra, ca in a:
        for rb, cb in b:
            if ra == rb and all(
                (ra, col) in a_set
                or (ra, col) in b_set
                or grid[ra][col] == 0
                for col in range(min(ca, cb), max(ca, cb) + 1)
            ):
                return True
            if ca == cb and all(
                (row, ca) in a_set
                or (row, ca) in b_set
                or grid[row][ca] == 0
                for row in range(min(ra, rb), max(ra, rb) + 1)
            ):
                return True
    return False


def _visibility_mix(grid: Grid, components: list[dict[str, Any]]) -> tuple[bool, bool]:
    visible = nonvisible = False
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            if _visible(grid, components[left]["cells"], components[right]["cells"]):
                visible = True
            else:
                nonvisible = True
    return visible, nonvisible


def has_occluded_aligned_pair(grid: Grid) -> bool:
    """Whether alignment exists but every aligned ray is blocked by a third object."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return False
    components = _component_records(grid)
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            a = components[left]["cells"]
            b = components[right]["cells"]
            if _aligned(a, b) and not _visible(grid, a, b):
                return True
    return False


def _separated(components: list[ComponentCells]) -> bool:
    for left in range(len(components)):
        for right in range(left + 1, len(components)):
            if any(
                max(abs(ra - rb), abs(ca - cb)) <= 1
                for ra, ca in components[left]
                for rb, cb in components[right]
            ):
                return False
    return True


def _all_dominoes(height: int, width: int) -> list[ComponentCells]:
    dominoes: list[ComponentCells] = []
    for row in range(height):
        for col in range(width - 1):
            dominoes.append(((row, col), (row, col + 1)))
    for row in range(height - 1):
        for col in range(width):
            dominoes.append(((row, col), (row + 1, col)))
    return dominoes


def _triple_options(height: int, width: int, layout_axis: str) -> list[list[ComponentCells]]:
    options: list[list[ComponentCells]] = []
    for spacing in (2, 3):
        if layout_axis == "horizontal":
            footprint_w = 2 * spacing + 1
            for row in range(height - 1):
                for col in range(width - footprint_w + 1):
                    options.append([
                        ((row, col), (row + 1, col)),
                        ((row, col + spacing), (row + 1, col + spacing)),
                        ((row, col + 2 * spacing), (row + 1, col + 2 * spacing)),
                    ])
        else:
            footprint_h = 2 * spacing + 1
            for row in range(height - footprint_h + 1):
                for col in range(width - 1):
                    options.append([
                        ((row, col), (row, col + 1)),
                        ((row + spacing, col), (row + spacing, col + 1)),
                        ((row + 2 * spacing, col), (row + 2 * spacing, col + 1)),
                    ])
    return options


def _grid_from_components(
    height: int,
    width: int,
    components: list[ComponentCells],
    colors: list[int] | tuple[int, ...],
) -> Grid:
    grid = full_grid(height, width, 0)
    for color, cells in zip(colors, components):
        for row, col in cells:
            grid[row][col] = color
    return grid


def _construct_layout(
    height: int,
    width: int,
    n: int,
    layout_axis: str,
    rng: Any,
) -> list[ComponentCells]:
    triples = _triple_options(height, width, layout_axis)
    rng.shuffle(triples)
    if n == 3:
        if not triples:
            raise ValueError(f"no {layout_axis} triple fits {height}x{width}")
        return list(triples[0])

    dominoes = _all_dominoes(height, width)
    for triple in triples:
        candidates = [candidate for candidate in dominoes if _separated([*triple, candidate])]
        if not candidates:
            continue
        rng.shuffle(candidates)
        # Separation prevents the fourth component from occupying either clear
        # gap, but verify the teaching relation before accepting the layout.
        for candidate in candidates:
            components = [*triple, candidate]
            probe = _grid_from_components(height, width, components, (1, 2, 3, 4))
            if (
                _visible(probe, triple[0], triple[1])
                and _visible(probe, triple[1], triple[2])
                and _aligned(triple[0], triple[2])
                and not _visible(probe, triple[0], triple[2])
            ):
                return components
    raise ValueError(f"could not construct a lawful {layout_axis} layout in {height}x{width}")


def analyze_grid(grid: Any) -> dict[str, Any]:
    """Pure structural analysis shared by validation, tests, and observers."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list"], "components": []}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must have a nonempty first row"], "components": []}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid rows must be rectangular lists"], "components": []}
    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    bad = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        errors.append(f"cells must be integer ARC colors 0..9: {bad[:3]}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "components": [],
            "has_occluded_aligned_pair": False,
        }

    components = _component_records(grid)
    if not (3 <= len(components) <= 4):
        errors.append(f"expected 3-4 components, found {len(components)}")
    colors = [component["color"] for component in components]
    if any(color in (0, 8) for color in colors):
        errors.append("component colors must be nonzero and non-cyan")
    if len(colors) != len(set(colors)):
        errors.append("component colors must be distinct")
    for component in components:
        cells = component["cells"]
        if len(cells) != 2:
            errors.append(
                f"component color {component['color']} must be a domino, found {len(cells)} cells"
            )
        elif abs(cells[0][0] - cells[1][0]) + abs(cells[0][1] - cells[1][1]) != 1:
            errors.append(f"component color {component['color']} is not 4-connected")
    if not _separated([component["cells"] for component in components]):
        errors.append("components must have one-cell 8-neighbor separation")
    visible, nonvisible = _visibility_mix(grid, components)
    if len(components) >= 3 and not (visible and nonvisible):
        errors.append("visibility matrix must contain both visible and nonvisible pairs")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "visible_pair": visible,
        "nonvisible_pair": nonvisible,
        "has_occluded_aligned_pair": has_occluded_aligned_pair(grid),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    return analyze_grid(grid)["errors"]


def strict_canonical_like(grid: Any) -> list[str]:
    """The structural task manifold; generated scenes add a stronger witness."""
    return self_check(grid)


def observe_overrides(grid: Grid) -> dict[str, Any]:
    analysis = analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    dims = (analysis["height"], analysis["width"])
    try:
        scene_profile = _PROFILE_BY_DIMS[dims]
    except KeyError as exc:
        raise ValueError(f"unrecognized scene dimensions: {dims}") from exc

    vertical = 0
    horizontal = 0
    for component in analysis["components"]:
        (r1, c1), (r2, c2) = component["cells"]
        if c1 == c2:
            vertical += 1
        elif r1 == r2:
            horizontal += 1
    if vertical >= 3 and vertical > horizontal:
        layout_axis = "horizontal"
    elif horizontal >= 3 and horizontal > vertical:
        layout_axis = "vertical"
    else:
        raise ValueError(
            f"cannot infer layout_axis from domino orientations: horizontal={horizontal}, vertical={vertical}"
        )
    return {
        "scene_profile": scene_profile,
        "n": len(analysis["components"]),
        "layout_axis": layout_axis,
    }


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", _scene_options(difficulty))
    n = ctx.draw_choice("n", _n_options(difficulty))
    layout_axis = ctx.draw_choice("layout_axis", _layout_options(difficulty))
    height, width = SCENE_PROFILE_SPECS[scene_profile]

    layout_rng = ctx.draw_rng("layout")
    components = _construct_layout(height, width, n, layout_axis, layout_rng)
    colors = layout_rng.sample(_COMPONENT_COLORS, n)
    grid = _grid_from_components(height, width, components, colors)

    expected = {"scene_profile": scene_profile, "n": n, "layout_axis": layout_axis}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"draw/observation mismatch: expected {expected}, observed {observed}")
    if not has_occluded_aligned_pair(grid):
        raise RuntimeError("constructed layout lost its required third-object occlusion")
    return grid


def _ordered_components(grid: Grid) -> list[dict[str, Any]]:
    components = _component_records(grid)
    return sorted(
        components,
        key=lambda component: (
            Fraction(sum(col for _, col in component["cells"]), len(component["cells"])),
            Fraction(sum(row for row, _ in component["cells"]), len(component["cells"])),
        ),
    )


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python transcription used for focused parity checks."""
    ordered = _ordered_components(grid)
    size = len(ordered)
    output = full_grid(size, size, 0)
    for row, left in enumerate(ordered):
        for col, right in enumerate(ordered):
            if row == col:
                output[row][col] = left["color"]
            elif _visible(grid, left["cells"], right["cells"]):
                output[row][col] = 8
    return output


def _alignment_ignores_blockers(grid: Grid) -> Grid:
    """Plausible wrong rule: any shared row/column counts, even through objects."""
    ordered = _ordered_components(grid)
    size = len(ordered)
    output = full_grid(size, size, 0)
    for row, left in enumerate(ordered):
        for col, right in enumerate(ordered):
            if row == col:
                output[row][col] = left["color"]
            elif _aligned(left["cells"], right["cells"]):
                output[row][col] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "alignment_ignores_blockers": _alignment_ignores_blockers,
}

# All four public pairs happen to agree with this blocker-blind shortcut; the
# generated curriculum therefore owes an executable counterexample.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    "alignment_ignores_blockers": _alignment_ignores_blockers,
}
LESSON_COMPETITORS: dict[str, Callable[[Grid], Grid]] = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "third_component_occlusion": has_occluded_aligned_pair,
}
WITNESS_RIVALS: dict[str, list[str]] = {
    "third_component_occlusion": ["alignment_ignores_blockers"],
}
