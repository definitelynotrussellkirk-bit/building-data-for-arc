"""Generator for easy_m07 — retain exact same-colour degree-1 cells.

Each nonzero cell is a vertex in the 4-neighbour graph induced by its own
colour.  The output keeps exactly the vertices of degree one and paints every
other cell background zero.

Five consecutive generated scenes form one identifiable lesson.  Together they
separate the true local rule from four plausible shortcuts: accepting isolated
cells (degree <= 1), handling only path components, counting neighbours without
respecting colour, and applying the rule only to the largest component of each
colour.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e175c009c2a"
TASK_ID = "6e175c009c2a"
VERSION = "2.0.0"
RULE_HASH = "f127fcd9dbfb"

SUMMARY = (
    "On a zero-background grid, keep exactly the nonzero cells having one "
    "orthogonal neighbour of the same colour. Scheduled path, branch, "
    "isolated-cell, zero-leaf-component, repeated-colour-component, and "
    "cross-colour-contact witnesses make the local exact-degree rule visible."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC integer colour 0..9",
    "exactly two nonzero colours are present",
    "each colour has both degree-1 cells to retain and non-degree-1 cells to erase",
    "orthogonal neighbours of other colours do not contribute to degree",
]

_PROFILE_PATHS = "paths"
_PROFILE_BRANCHES = "branches"
_PROFILE_SINGLETON_SPLIT = "singleton_and_split"
_PROFILE_ZERO_LEAF = "zero_leaf_component"
_PROFILE_CROSS_COLOUR = "cross_colour_contact"
SCHEDULE_PROFILES = (
    _PROFILE_PATHS,
    _PROFILE_BRANCHES,
    _PROFILE_SINGLETON_SPLIT,
    _PROFILE_ZERO_LEAF,
    _PROFILE_CROSS_COLOUR,
)
EXAMPLES_NEEDED = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 0.60

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchor on 4/5 draws; difficulty-aware 7..14 otherwise",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchor on 4/5 draws; difficulty-aware 8..14 otherwise",
        "valid": "8..14",
    },
    "scene_profile": {
        "type": "str",
        "default": "five-slot deterministic teaching schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_ENVELOPES = (
    (7, 8, (2, 7)),
    (8, 8, (4, 9)),
    (7, 9, (3, 6)),
    (8, 10, (4, 7)),
)

# Local templates use abstract colour indices 0 and 1.  A single D4 transform
# and translation is applied to the whole scene, preserving every linked
# relation while varying orientation and position.
_SCENE_CELLS: dict[str, tuple[tuple[int, int, int], ...]] = {
    _PROFILE_PATHS: (
        (0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 0),
        (3, 4, 1), (4, 4, 1), (5, 4, 1), (5, 5, 1), (5, 6, 1),
    ),
    _PROFILE_BRANCHES: (
        (0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 1, 0),
        (3, 5, 1), (4, 4, 1), (4, 5, 1), (4, 6, 1), (5, 5, 1),
    ),
    _PROFILE_SINGLETON_SPLIT: (
        # Colour 0 has a path, a two-cell component, and an isolated cell.
        # The latter refutes degree<=1; the domino refutes largest-only.
        (0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 0),
        (2, 5, 0), (2, 6, 0),
        (4, 6, 0),
        (3, 0, 1), (4, 0, 1), (5, 0, 1), (5, 1, 1), (5, 2, 1),
    ),
    _PROFILE_ZERO_LEAF: (
        # Colour 0 combines a path with a 2x2 zero-leaf component.
        (0, 0, 0), (0, 1, 0), (0, 2, 0), (0, 3, 0),
        (3, 0, 0), (3, 1, 0), (4, 0, 0), (4, 1, 0),
        (2, 4, 1), (2, 5, 1), (2, 6, 1), (3, 5, 1),
    ),
    _PROFILE_CROSS_COLOUR: (
        # The two endpoints at (2,3) and (2,4) touch across colours.  Each has
        # one same-colour neighbour but two nonzero neighbours in total.
        (2, 0, 0), (2, 1, 0), (2, 2, 0), (2, 3, 0),
        (2, 4, 1), (3, 4, 1), (4, 4, 1), (5, 4, 1),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every five consecutive sample indices contain every decisive profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_or_pin_int(ctx, label: str, lo: int, hi: int, pinned: int | None) -> int:
    """Honor the full declared override domain while pinning ordinary anchors."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if pinned is not None:
        return ctx.draw_int(label, pinned, pinned)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_or_pin_choice(ctx, label: str, options: tuple[str, ...], pinned: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (pinned,)))


def _normalize_tagged(
    cells: Iterable[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    return tuple(sorted((row - row0, col - col0, tag) for row, col, tag in cells))


def _transform_scene(
    cells: Iterable[tuple[int, int, int]], code: int
) -> tuple[tuple[int, int, int], ...]:
    transformed = list(cells)
    if code >= 4:
        transformed = [(row, -col, tag) for row, col, tag in transformed]
    for _ in range(code % 4):
        transformed = [(col, -row, tag) for row, col, tag in transformed]
    return _normalize_tagged(transformed)


def _placement_offset(
    grid_h: int,
    grid_w: int,
    scene_h: int,
    scene_w: int,
    mode: int,
    rng,
) -> tuple[int, int]:
    max_row = grid_h - scene_h
    max_col = grid_w - scene_w
    if max_row < 0 or max_col < 0:
        raise ValueError(
            f"scene {scene_h}x{scene_w} does not fit grid {grid_h}x{grid_w}"
        )
    corners = (
        (0, 0),
        (0, max_col),
        (max_row, 0),
        (max_row, max_col),
    )
    if mode < len(corners):
        return corners[mode]
    return rng.randint(0, max_row), rng.randint(0, max_col)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return [f"grid dimensions must be in 5..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _same_colour_degree(grid: Any, row: int, col: int) -> int:
    value = grid[row][col]
    if value == 0:
        return 0
    height, width = len(grid), len(grid[0])
    return sum(
        0 <= row + drow < height
        and 0 <= col + dcol < width
        and grid[row + drow][col + dcol] == value
        for drow, dcol in _DIR4
    )


def _components(grid: Any) -> dict[int, list[dict[str, Any]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    by_colour: dict[int, list[dict[str, Any]]] = {}
    for start_row in range(height):
        for start_col in range(width):
            colour = grid[start_row][start_col]
            start = (start_row, start_col)
            if colour == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = (row + drow, col + dcol)
                    nrow, ncol = nxt
                    if (
                        0 <= nrow < height
                        and 0 <= ncol < width
                        and nxt not in seen
                        and grid[nrow][ncol] == colour
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            degrees = tuple(sorted(_same_colour_degree(grid, row, col) for row, col in cells))
            by_colour.setdefault(colour, []).append(
                {
                    "cells": tuple(sorted(cells)),
                    "area": len(cells),
                    "degrees": degrees,
                    "leaf_count": sum(degree == 1 for degree in degrees),
                    "max_degree": max(degrees),
                }
            )
    for colour in by_colour:
        by_colour[colour].sort(key=lambda component: component["cells"][0])
    return by_colour


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    colours = sorted({value for row in grid for value in row if value != 0})
    components = _components(grid)
    degrees_by_colour = {
        colour: tuple(
            _same_colour_degree(grid, row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == colour
        )
        for colour in colours
    }
    cross_colour_edges = 0
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            for drow, dcol in ((1, 0), (0, 1)):
                nrow, ncol = row + drow, col + dcol
                if (
                    nrow < height
                    and ncol < width
                    and grid[nrow][ncol] not in (0, value)
                ):
                    cross_colour_edges += 1
    signature = (
        tuple(
            sorted(
                tuple(
                    sorted(
                        (component["area"], component["degrees"])
                        for component in colour_components
                    )
                )
                for colour_components in components.values()
            )
        ),
        cross_colour_edges,
    )
    return {
        "errors": [],
        "height": height,
        "width": width,
        "colours": colours,
        "components": components,
        "degrees_by_colour": degrees_by_colour,
        "cross_colour_edges": cross_colour_edges,
        "signature": signature,
    }


def _tight_grid(cells: Iterable[tuple[int, int, int]]) -> list[list[int]]:
    normalized = _normalize_tagged(cells)
    height = max(5, max(row for row, _, _ in normalized) + 1)
    width = max(5, max(col for _, col, _ in normalized) + 1)
    grid = full_grid(height, width, 0)
    for row, col, tag in normalized:
        grid[row][col] = tag + 1
    return grid


_PROFILE_BY_SIGNATURE = {
    _analysis(_tight_grid(cells))["signature"]: profile
    for profile, cells in _SCENE_CELLS.items()
}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": _PROFILE_BY_SIGNATURE.get(analysis["signature"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if 0 not in {value for row in grid for value in row}:
        errors.append("background colour 0 must be present")
    if len(analysis["colours"]) != 2:
        errors.append(
            f"expected exactly two nonzero colours, found {analysis['colours']}"
        )
    for colour in analysis["colours"]:
        degrees = analysis["degrees_by_colour"][colour]
        if 1 not in degrees:
            errors.append(f"colour {colour} has no exact-degree-1 cell to retain")
        if degrees and all(degree == 1 for degree in degrees):
            errors.append(f"colour {colour} has no non-degree-1 cell to erase")
        if len(degrees) < 3:
            errors.append(f"colour {colour} needs at least three cells, found {len(degrees)}")
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Match the four linked canonical (shape, size, palette) envelopes."""
    errors = self_check(grid)
    if errors:
        return errors
    colours = tuple(sorted({value for row in grid for value in row if value != 0}))
    profile = (len(grid), len(grid[0]), colours)
    if profile not in _CANONICAL_ENVELOPES:
        return [f"outside linked canonical envelope: {profile!r}"]
    return []


def rule_mirror(grid) -> list[list[int]]:
    """Python audit mirror; the Racket rule remains the output authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0 and _same_colour_degree(grid, row, col) == 1:
                output[row][col] = grid[row][col]
    return output


def _rival_degree_at_most_one(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0 and _same_colour_degree(grid, row, col) <= 1:
                output[row][col] = grid[row][col]
    return output


def _rival_path_components_only(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for colour_components in _components(grid).values():
        for component in colour_components:
            if component["max_degree"] <= 2:
                for row, col in component["cells"]:
                    if _same_colour_degree(grid, row, col) == 1:
                        output[row][col] = grid[row][col]
    return output


def _rival_colour_blind_degree_one(grid):
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0:
                continue
            degree = sum(
                0 <= row + drow < height
                and 0 <= col + dcol < width
                and grid[row + drow][col + dcol] != 0
                for drow, dcol in _DIR4
            )
            if degree == 1:
                output[row][col] = grid[row][col]
    return output


def _rival_largest_component_per_colour(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for colour_components in _components(grid).values():
        chosen = max(colour_components, key=lambda component: component["area"])
        for row, col in chosen["cells"]:
            if _same_colour_degree(grid, row, col) == 1:
                output[row][col] = grid[row][col]
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "degree_at_most_one": _rival_degree_at_most_one,
    "path_components_only": _rival_path_components_only,
    "colour_blind_degree_one": _rival_colour_blind_degree_one,
    "largest_component_per_colour": _rival_largest_component_per_colour,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "degree_at_most_one": _rival_degree_at_most_one,
    "colour_blind_degree_one": _rival_colour_blind_degree_one,
    "largest_component_per_colour": _rival_largest_component_per_colour,
}


def _components_flat(grid) -> list[dict[str, Any]]:
    return [
        component
        for colour_components in _components(grid).values()
        for component in colour_components
    ]


SEMANTIC_WITNESSES = {
    "degree_three_branch": lambda grid: any(
        component["leaf_count"] == 3 and component["max_degree"] == 3
        for component in _components_flat(grid)
    ),
    "degree_four_branch": lambda grid: any(
        component["leaf_count"] == 4 and component["max_degree"] == 4
        for component in _components_flat(grid)
    ),
    "isolated_exactness_control": lambda grid: any(
        component["area"] == 1 and component["degrees"] == (0,)
        for component in _components_flat(grid)
    ),
    "secondary_leaf_component": lambda grid: any(
        len(colour_components) > 1
        and any(
            component["leaf_count"] > 0
            for component in sorted(
                colour_components, key=lambda component: component["area"], reverse=True
            )[1:]
        )
        for colour_components in _components(grid).values()
    ),
    "cross_colour_contact": lambda grid: _analysis(grid).get("cross_colour_edges", 0) > 0,
}
WITNESS_RIVALS = {
    "degree_three_branch": ["path_components_only"],
    "degree_four_branch": ["path_components_only"],
    "isolated_exactness_control": ["degree_at_most_one"],
    "secondary_leaf_component": ["largest_component_per_colour"],
    "cross_colour_contact": ["colour_blind_degree_one"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each five-demo sliding lesson to kill every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    profiles: set[str] = set()
    killed = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} disagrees with exact same-colour degree-1 rule")
        profile = observe_overrides(pair["input"]).get("scene_profile")
        if profile:
            profiles.add(profile)
        for name, rival in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or rival(pair["input"]) != expected
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query disagrees with exact same-colour degree-1 rule")
    missing = set(SCHEDULE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations miss scheduled profiles: {sorted(missing)}")
    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


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

    anchor_slot = (int(seed) + int(sample_index)) % len(_CANONICAL_ENVELOPES)
    anchor_h, anchor_w, palette = _CANONICAL_ENVELOPES[anchor_slot]
    use_anchor = int(sample_index) % len(SCHEDULE_PROFILES) != len(SCHEDULE_PROFILES) - 1
    grid_h = _draw_or_pin_int(
        ctx, "grid_h", 7, 14, anchor_h if use_anchor else None
    )
    grid_w = _draw_or_pin_int(
        ctx, "grid_w", 8, 14, anchor_w if use_anchor else None
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = _draw_or_pin_choice(ctx, "scene_profile", SCHEDULE_PROFILES, scheduled)

    scene_rng = ctx.draw_rng("scene_transform")
    tagged = _transform_scene(_SCENE_CELLS[profile], scene_rng.randrange(8))
    scene_h = max(row for row, _, _ in tagged) + 1
    scene_w = max(col for _, col, _ in tagged) + 1
    offset_row, offset_col = _placement_offset(
        grid_h,
        grid_w,
        scene_h,
        scene_w,
        (int(seed) + int(sample_index)) % 5,
        ctx.draw_rng("scene_position"),
    )

    # Pair identity is tied to the same anchor slot as dimensions, guaranteeing
    # repeated support for all four canonical size/palette envelopes.  Swapping
    # the pair is a nuisance variation and does not change the envelope.
    colour_a, colour_b = palette
    if ctx.draw_rng("palette_order").randint(0, 1):
        colour_a, colour_b = colour_b, colour_a
    colours = (colour_a, colour_b)

    grid = full_grid(grid_h, grid_w, 0)
    for row, col, tag in tagged:
        grid[offset_row + row][offset_col + col] = colours[tag]
    return grid
