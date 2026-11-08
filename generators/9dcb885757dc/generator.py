"""Semantic generator for ARC task 9dcb885757dc.

Each non-zero four-connected object is a graph vertex. Two vertices are
adjacent when any pair of their cells is at Manhattan distance at most two
(equivalently, their one-step Manhattan dilations touch). Recolor every object
by its graph degree: 0->2, 1->3, 2->4, 3->5, 4->6, and 5+->7.

The previous random scatter overwhelmingly emitted all-isolated scenes, so a
learner could succeed with the shortcut "paint every object red." This version
constructs six contact-graph profiles by design. Every five-example teaching schedule
covers degrees 0 through 5, and mixed-component profiles distinguish counting
neighboring *objects* from counting nearby cells.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9dcb885757dc"
TASK_ID = GENERATOR_ID
VERSION = "2.0.2"
RULE_HASH = "25bd5db7ed17"

SUMMARY = (
    "Five or six distinctly colored objects arranged in scheduled Manhattan-2 "
    "contact graphs that cover touch degrees 0 through 5."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly 5 or 6 four-connected objects in distinct non-zero colors",
    "different objects are never side-adjacent; graph edges occur across a one-cell gap",
    "the scheduled five-profile lesson exercises every output branch from degree 0 through 5",
    "mixed profiles make object-degree counting differ from nearby-cell counting",
]

PROFILE_NAMES = ("isolated", "pair", "chain", "hub3", "hub4", "dense")
# The pure-isolated profile is a lawful canonical edge case and remains an
# exact override value, but it need not consume a teaching slot: every other
# profile already contains at least one degree-0 object. The five scheduled
# profiles therefore cover degrees 0..5 within the worker contract limit.
TEACHING_PROFILES = ("pair", "chain", "hub3", "hub4", "dense")
COMPONENT_STYLES = ("singletons", "mixed")
EXAMPLES_NEEDED = len(TEACHING_PROFILES)
SCHEDULE_PROFILES = TEACHING_PROFILES
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile schedule, 7..8",
        "valid": "7..8",
    },
    "grid_w": {
        "type": "int",
        "default": "profile schedule, 7..10",
        "valid": "7..10",
    },
    "n_components": {
        "type": "int",
        "default": "profile schedule, 5..6",
        "valid": "5..6",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index cycle over five teaching profiles",
        "valid": "|".join(PROFILE_NAMES),
    },
    "component_style": {
        "type": "str",
        "default": "seed+sample_index parity",
        "valid": "|".join(COMPONENT_STYLES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Singleton anchor layouts inside a 7x7 core. Edges have exact minimum
# Manhattan distance two. Taking the first five anchors preserves a distinct,
# lawful profile for n_components=5, so every independent axis combination is
# realizable and exactly observable.
_PROFILE_ANCHORS: dict[str, tuple[tuple[int, int], ...]] = {
    "isolated": ((0, 0), (0, 3), (0, 6), (3, 0), (3, 3), (6, 6)),
    "pair": ((1, 1), (1, 3), (0, 6), (4, 0), (4, 4), (6, 6)),
    "chain": ((1, 1), (1, 3), (1, 5), (5, 0), (5, 3), (5, 6)),
    "hub3": ((3, 3), (1, 3), (3, 1), (3, 5), (6, 0), (6, 6)),
    "hub4": ((3, 3), (1, 3), (3, 1), (3, 5), (5, 3), (0, 0)),
    # With six objects the sorted degrees are (1,1,2,2,3,5), exercising the
    # otherwise-unseen 5+ -> color 7 branch. With five they are (1,2,2,3,4).
    "dense": ((3, 3), (1, 3), (2, 2), (3, 1), (3, 5), (5, 3)),
}

# Profile-derived defaults are all exact canonical (height, width, palette)
# profiles once background is counted. Explicit overrides may independently
# select any declared boundary value.
_PROFILE_DEFAULTS: dict[str, tuple[int, int, int]] = {
    "isolated": (7, 10, 5),
    "pair": (8, 9, 6),
    "chain": (7, 9, 6),
    "hub3": (7, 7, 6),
    "hub4": (7, 9, 6),
    "dense": (7, 7, 6),
}

# Extra cells for the mixed style. Every addition is four-connected to its own
# anchor, preserves the contact graph, and keeps every inter-object distance at
# least two. Pair/chain/hub3 additions deliberately make nearby-cell counts
# disagree with neighboring-object counts.
_MIXED_ADDITIONS: dict[str, dict[int, tuple[tuple[int, tuple[int, int]], ...]]] = {
    "isolated": {
        5: ((2, (1, 6)),),
        6: ((2, (1, 6)),),
    },
    "pair": {
        5: ((0, (0, 1)), (1, (0, 3))),
        6: ((0, (0, 1)), (1, (0, 3))),
    },
    "chain": {
        5: ((0, (0, 1)), (1, (0, 3))),
        6: ((0, (0, 1)), (1, (0, 3))),
    },
    "hub3": {
        5: ((0, (4, 3)), (2, (4, 1))),
        6: ((0, (4, 3)), (2, (4, 1))),
    },
    "hub4": {
        5: ((1, (0, 3)),),
        6: ((1, (0, 3)),),
    },
    "dense": {
        5: ((0, (4, 3)), (3, (4, 1))),
        6: ((1, (0, 3)), (5, (6, 3))),
    },
}

# Exact graph fingerprints used by self_check and observe_overrides. They are
# isomorphism-level signatures for these small graph families.
_PROFILE_SIGNATURES: dict[tuple[int, tuple[int, ...]], str] = {
    (5, (0, 0, 0, 0, 0)): "isolated",
    (6, (0, 0, 0, 0, 0, 0)): "isolated",
    (5, (0, 0, 0, 1, 1)): "pair",
    (6, (0, 0, 0, 0, 1, 1)): "pair",
    (5, (0, 0, 1, 1, 2)): "chain",
    (6, (0, 0, 0, 1, 1, 2)): "chain",
    (5, (0, 1, 1, 1, 3)): "hub3",
    (6, (0, 0, 1, 1, 1, 3)): "hub3",
    (5, (1, 1, 1, 1, 4)): "hub4",
    (6, (0, 1, 1, 1, 1, 4)): "hub4",
    (5, (1, 2, 2, 3, 4)): "dense",
    (6, (1, 1, 2, 2, 3, 5)): "dense",
}


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the declared five-way teaching profile for this draw."""
    del seed
    _validate_difficulty(difficulty)
    return TEACHING_PROFILES[int(sample_index) % len(TEACHING_PROFILES)]


def _scheduled_style(seed: int, sample_index: int) -> str:
    return COMPONENT_STYLES[(int(seed) + int(sample_index)) % len(COMPONENT_STYLES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell {(r, c)} is not a literal ARC color 0..9: {value!r}"]
    return []


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append({"color": color, "cells": tuple(sorted(cells))})
    return found


def _min_distance(a: Sequence[tuple[int, int]], b: Sequence[tuple[int, int]]) -> int:
    return min(abs(ar - br) + abs(ac - bc) for ar, ac in a for br, bc in b)


def _touch_degrees_from_components(components: Sequence[dict[str, Any]]) -> list[int]:
    degrees: list[int] = []
    for i, first in enumerate(components):
        degree = 0
        for j, second in enumerate(components):
            if i != j and _min_distance(first["cells"], second["cells"]) <= 2:
                degree += 1
        degrees.append(degree)
    return degrees


def _profile_from_degrees(degrees: Sequence[int]) -> str | None:
    return _PROFILE_SIGNATURES.get((len(degrees), tuple(sorted(degrees))))


def _component_style(components: Sequence[dict[str, Any]]) -> str | None:
    sizes = [len(component["cells"]) for component in components]
    if sizes and all(size == 1 for size in sizes):
        return "singletons"
    if sizes and all(size in (1, 2) for size in sizes) and 1 <= sum(size == 2 for size in sizes) <= 2:
        return "mixed"
    return None


def semantic_observables(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return exact, task-linked observables used by tests and gates."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    components = _components(grid)
    degrees = _touch_degrees_from_components(components)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_components": len(components),
        "colors": tuple(component["color"] for component in components),
        "component_sizes": tuple(len(component["cells"]) for component in components),
        "degrees": tuple(degrees),
        "degree_multiset": tuple(sorted(degrees)),
        "scene_profile": _profile_from_degrees(degrees),
        "component_style": _component_style(components),
        "output_classes": tuple(sorted({_color_for(degree) for degree in degrees})),
    }


def _transform_cell(cell: tuple[int, int], transform: int) -> tuple[int, int]:
    r, c = cell
    if transform == 0:  # identity
        return r, c
    if transform == 1:  # rotate 90
        return c, 6 - r
    if transform == 2:  # rotate 180
        return 6 - r, 6 - c
    if transform == 3:  # rotate 270
        return 6 - c, r
    if transform == 4:  # reflect left/right
        return r, 6 - c
    if transform == 5:  # reflect top/bottom
        return 6 - r, c
    if transform == 6:  # transpose
        return c, r
    return 6 - c, 6 - r  # anti-transpose


def _profile_components(profile: str, count: int, style: str) -> list[list[tuple[int, int]]]:
    components = [[anchor] for anchor in _PROFILE_ANCHORS[profile][:count]]
    if style == "mixed":
        for index, cell in _MIXED_ADDITIONS[profile][count]:
            components[index].append(cell)
    return components


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    """Generate one deterministic, fully override-observable training input."""
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    requested_profile = overrides.get("scene_profile")
    if requested_profile is None:
        requested_profile = scheduled_profile
    if requested_profile not in PROFILE_NAMES:
        raise ValueError(
            f"scene_profile override {requested_profile!r} not in {PROFILE_NAMES}"
        )

    default_h, default_w, default_n = _PROFILE_DEFAULTS[requested_profile]
    effective = dict(overrides)
    effective.setdefault("scene_profile", requested_profile)
    effective.setdefault("component_style", _scheduled_style(seed, sample_index))
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("n_components", default_n)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 7, 8)
    width = ctx.draw_int("grid_w", 7, 10)
    count = ctx.draw_int("n_components", 5, 6)
    profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    style = ctx.draw_choice("component_style", COMPONENT_STYLES)
    base_colors = ctx.draw_distinct_colors("component_colors", n=count, exclude={0})
    # Difficulty is representation-level rather than rule-level: apply a
    # fixed-point-free cyclic permutation of the nine non-zero ARC colors.
    # This guarantees each band is observably live while preserving the exact
    # contact graph and therefore the reasoning burden measured by the rule.
    color_shift = {None: 3, "easy": 0, "medium": 3, "hard": 6}[difficulty]
    colors = tuple(((color - 1 + color_shift) % 9) + 1 for color in base_colors)

    components = _profile_components(profile, count, style)
    layout_rng = ctx.draw_rng("layout")
    transform = layout_rng.randrange(8)
    row_offset = layout_rng.randint(0, height - 7)
    col_offset = layout_rng.randint(0, width - 7)

    grid = full_grid(height, width, 0)
    for color, component in zip(colors, components):
        for cell in component:
            r, c = _transform_cell(cell, transform)
            grid[r + row_offset][c + col_offset] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"constructed invalid {profile}/{style} scene: {errors}")
    return grid


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed scenes and any scene outside the declared graph grammar."""
    del meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    try:
        _validate_difficulty(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 8:
        errors.append(f"height {height} outside 7..8")
    if not 7 <= width <= 10:
        errors.append(f"width {width} outside 7..10")

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 is missing")

    components = _components(grid)
    if not 5 <= len(components) <= 6:
        errors.append(f"expected 5..6 components, found {len(components)}")
        return errors

    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        errors.append(f"component colors must be distinct, found {colors}")

    style = _component_style(components)
    if style is None:
        sizes = [len(component["cells"]) for component in components]
        errors.append(
            "components must be single cells or at most two dominoes; "
            f"found sizes {sizes}"
        )

    for i, first in enumerate(components):
        for second in components[i + 1 :]:
            distance = _min_distance(first["cells"], second["cells"])
            if distance < 2:
                errors.append(
                    "different objects must have at least one blank cell between "
                    f"them; colors {first['color']} and {second['color']} have distance {distance}"
                )

    degrees = _touch_degrees_from_components(components)
    profile = _profile_from_degrees(degrees)
    if profile is None:
        errors.append(
            f"unrecognized Manhattan-2 contact graph for {len(components)} objects: "
            f"degrees {sorted(degrees)}"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Return [] exactly for this generator's canonical-scale lawful manifold."""
    return self_check(grid)


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors[0]}")
    facts = semantic_observables(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_components": facts["n_components"],
        "scene_profile": facts["scene_profile"],
        "component_style": facts["component_style"],
    }


def _color_for(degree: int) -> int:
    return degree + 2 if 0 <= degree <= 4 else 7


def _paint_components(
    grid: Sequence[Sequence[int]],
    metric: Callable[[int, Sequence[dict[str, Any]]], int],
) -> list[list[int]]:
    components = _components(grid)
    output = full_grid(len(grid), len(grid[0]), 0)
    for index, component in enumerate(components):
        color = _color_for(metric(index, components))
        for r, c in component["cells"]:
            output[r][c] = color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])

    def degree(index: int, components: Sequence[dict[str, Any]]) -> int:
        return sum(
            index != other
            and _min_distance(components[index]["cells"], candidate["cells"]) <= 2
            for other, candidate in enumerate(components)
        )

    return _paint_components(grid, degree)


def _rival_all_isolated(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return _paint_components(grid, lambda index, components: 0)


def _rival_binary_touch(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    def metric(index: int, components: Sequence[dict[str, Any]]) -> int:
        touching = any(
            index != other
            and _min_distance(components[index]["cells"], candidate["cells"]) <= 2
            for other, candidate in enumerate(components)
        )
        return 1 if touching else 0

    return _paint_components(grid, metric)


def _rival_direct_contact(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    def metric(index: int, components: Sequence[dict[str, Any]]) -> int:
        return sum(
            index != other
            and _min_distance(components[index]["cells"], candidate["cells"]) <= 1
            for other, candidate in enumerate(components)
        )

    return _paint_components(grid, metric)


def _rival_count_nearby_cells(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    def metric(index: int, components: Sequence[dict[str, Any]]) -> int:
        own = components[index]["cells"]
        return sum(
            1
            for other, candidate in enumerate(components)
            if other != index
            for cell in candidate["cells"]
            if min(abs(cell[0] - r) + abs(cell[1] - c) for r, c in own) <= 2
        )

    return _paint_components(grid, metric)


def _rival_cap_at_four(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    def metric(index: int, components: Sequence[dict[str, Any]]) -> int:
        degree = sum(
            index != other
            and _min_distance(components[index]["cells"], candidate["cells"]) <= 2
            for other, candidate in enumerate(components)
        )
        return min(degree, 4)

    return _paint_components(grid, metric)


def _witness_nonzero_contact(grid: Sequence[Sequence[int]]) -> bool:
    return any(degree > 0 for degree in semantic_observables(grid)["degrees"])


def _witness_degree_at_least_two(grid: Sequence[Sequence[int]]) -> bool:
    return any(degree >= 2 for degree in semantic_observables(grid)["degrees"])


def _witness_component_not_cell_count(grid: Sequence[Sequence[int]]) -> bool:
    return _rival_count_nearby_cells(grid) != rule_mirror(grid)


def _witness_degree_five(grid: Sequence[Sequence[int]]) -> bool:
    return any(degree >= 5 for degree in semantic_observables(grid)["degrees"])


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "all_objects_isolated": _rival_all_isolated,
    "binary_touch_only": _rival_binary_touch,
    "direct_contact_only": _rival_direct_contact,
    "count_nearby_cells": _rival_count_nearby_cells,
    "cap_degree_at_four": _rival_cap_at_four,
}

SEMANTIC_WITNESSES = {
    "nonzero_contact": _witness_nonzero_contact,
    "degree_at_least_two": _witness_degree_at_least_two,
    "component_not_cell_count": _witness_component_not_cell_count,
    "degree_five_branch": _witness_degree_five,
}

WITNESS_RIVALS = {
    "nonzero_contact": ["all_objects_isolated", "direct_contact_only"],
    "degree_at_least_two": ["binary_touch_only"],
    "component_not_cell_count": ["count_nearby_cells"],
    "degree_five_branch": ["cap_degree_at_four"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require a complete five-profile lesson that eliminates named shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    valid_demos: list[dict[str, Any]] = []
    profiles: set[str] = set()
    degrees_seen: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match touch-degree recoloring")
            continue
        facts = semantic_observables(demo["input"])
        profiles.add(facts["scene_profile"])
        degrees_seen.update(facts["degrees"])
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output does not match touch-degree recoloring")

    missing_profiles = sorted(set(TEACHING_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"lesson is missing scheduled profiles: {missing_profiles}")
    missing_degrees = sorted(set(range(6)) - degrees_seen)
    if missing_degrees:
        reasons.append(f"lesson does not demonstrate degree branches: {missing_degrees}")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"named shortcut survives every demo: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Return deterministic destructive mutations for local regression tests."""
    base = generate(
        7,
        5,
        difficulty="medium",
        grid_h=7,
        grid_w=7,
        n_components=6,
        scene_profile="dense",
        component_style="mixed",
    )
    fixtures: list[tuple[str, list[list[int]]]] = []

    cropped = [row[:] for row in base[:-1]]
    fixtures.append(("cropped-height", cropped))

    components = _components(base)
    too_few = [row[:] for row in base]
    for component in components[:2]:
        for r, c in component["cells"]:
            too_few[r][c] = 0
    fixtures.append(("too-few-components", too_few))

    duplicate_color = [row[:] for row in base]
    replacement = components[0]["color"]
    for r, c in components[-1]["cells"]:
        duplicate_color[r][c] = replacement
    fixtures.append(("duplicate-object-color", duplicate_color))

    oversized = [row[:] for row in base]
    target = components[0]
    added = 0
    occupied = {(r, c) for component in components for r, c in component["cells"]}
    for r, c in target["cells"]:
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(base) and 0 <= nc < len(base[0]) and (nr, nc) not in occupied:
                oversized[nr][nc] = target["color"]
                occupied.add((nr, nc))
                added += 1
                if len(target["cells"]) + added >= 3:
                    break
        if len(target["cells"]) + added >= 3:
            break
    fixtures.append(("oversized-component", oversized))

    illegal_color = [row[:] for row in base]
    r, c = components[0]["cells"][0]
    illegal_color[r][c] = 10
    fixtures.append(("illegal-color", illegal_color))

    unrecognized_graph = generate(
        11,
        0,
        grid_h=7,
        grid_w=7,
        n_components=5,
        scene_profile="isolated",
        component_style="singletons",
    )
    isolated_components = _components(unrecognized_graph)
    # Move one isolated singleton to make exactly two edges sharing a vertex,
    # a three-vertex path plus only two isolates is the chain profile; then add
    # a third edge between isolates to create an undeclared graph signature.
    points = [component["cells"][0] for component in isolated_components]
    colors = [component["color"] for component in isolated_components]
    unrecognized_graph = full_grid(7, 7, 0)
    custom = ((1, 1), (1, 3), (3, 3), (5, 3), (5, 5))
    for color, (rr, cc) in zip(colors, custom):
        unrecognized_graph[rr][cc] = color
    fixtures.append(("unrecognized-contact-graph", unrecognized_graph))

    return fixtures
