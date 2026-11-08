"""Generator for ``Path Endpoints Only`` (ARC task ``a287e878de99``).

The canonical rule is local: a gray (5) cell survives exactly when it has one
orthogonal gray neighbor.  Earlier versions generated only disjoint simple
paths, so several stronger but wrong component-level rules fit every lesson.
This version keeps canonical path anchors while scheduling branch, cycle, and
singleton counterexamples that distinguish the local degree predicate.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a287e878de99"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d7cc9d995b63"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, place 2..5 separated gray components. Keep exactly "
    "the gray cells with one orthogonal gray neighbor; erase all other cells. "
    "A four-example schedule covers paths, a branch, a cycle, and an isolated "
    "cell so the lesson identifies the local degree-one rule."
)

INVARIANTS = [
    "background is 0 and every foreground cell is gray/color 5",
    "generated components are pairwise separated by at least one orthogonal cell",
    "every generated scene contains both a surviving degree-one cell and an erased gray cell",
    "the output keeps exactly gray cells with one orthogonal gray neighbor",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "7 on path anchors; otherwise difficulty-aware 7..15",
        "valid": "7..15",
    },
    "grid_w": {
        "type": "int",
        "default": "8 on path anchors; otherwise difficulty-aware 8..17",
        "valid": "8..17",
    },
    "component_count": {
        "type": "int",
        "default": "2 on path anchors; otherwise difficulty-aware 2..5",
        "valid": "2..5",
    },
    "scene_pattern": {
        "type": "str",
        "default": "scheduled path/branch/cycle/singleton profile",
        "valid": "path|branch|cycle|singleton",
    },
}

# The constructive placer realizes the entire advertised Cartesian product,
# including five components in the minimum 7x8 grid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("path", "branch", "cycle", "singleton")

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Compact connected templates.  Orientations/reflections are generated below.
_SINGLETON = ((0, 0),)
_PAIR = ((0, 0), (0, 1))
_PATH3 = ((0, 0), (0, 1), (0, 2))
_CORNER3 = ((0, 0), (1, 0), (1, 1))
_PATH4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_ZIGZAG4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_PATH5 = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2))
_SNAKE5 = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
_BRANCH_T = ((0, 0), (0, 1), (0, 2), (1, 1))
# A 2x2 cycle with a two-cell tail.  It has one endpoint, one degree-3
# junction, and edge_count == vertex_count, so it exercises the cyclic case.
_CYCLE_TAIL = ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3))

_PATH_BANK = (_PATH3, _CORNER3, _PATH4, _ZIGZAG4, _PATH5, _SNAKE5)
_COMPACT_PATH_BANK = (_PAIR, _PATH3, _CORNER3)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Cycle profiles so every consecutive four-example window covers all four."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "component_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    scene = overrides.get("scene_pattern")
    if scene is not None and type(scene) is not str:
        raise TypeError("scene_pattern must be a string")

    bounds = {"grid_h": (7, 15), "grid_w": (8, 17), "component_count": (2, 5)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name} override {value!r} outside [{lo}, {hi}]")
    if scene is not None and scene not in SCHEDULE_PROFILES:
        raise ValueError(
            f"scene_pattern override {scene!r} is not one of {SCHEDULE_PROFILES}"
        )


def _draw_int_axis(ctx, label: str, lo: int, hi: int, defaults: Iterable[int]) -> int:
    """Honor exact global overrides while keeping scheduled defaults narrow."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return int(ctx.draw_choice(label, tuple(int(value) for value in defaults)))


def _draw_scene_axis(ctx, scheduled: str) -> str:
    if ctx.overrides.get("scene_pattern") is not None:
        return str(ctx.draw_choice("scene_pattern", SCHEDULE_PROFILES))
    return str(ctx.draw_choice("scene_pattern", (scheduled,)))


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        pending = [start]
        while pending:
            r, c = pending.pop()
            for dr, dc in _NEIGHBORS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        result.append(component)
    return result


def _degree(cell: tuple[int, int], component: set[tuple[int, int]]) -> int:
    r, c = cell
    return sum((r + dr, c + dc) in component for dr, dc in _NEIGHBORS4)


def _component_edges(component: set[tuple[int, int]]) -> int:
    return sum(_degree(cell, component) for cell in component) // 2


def _scene_pattern(grid: list[list[int]]) -> str:
    components = _components(grid)
    if any(_component_edges(component) >= len(component) for component in components):
        return "cycle"
    if any(any(_degree(cell, component) >= 3 for cell in component) for component in components):
        return "branch"
    if any(len(component) == 1 for component in components):
        return "singleton"
    return "path"


def _structural_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid rows must have equal width"]

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 15:
        errors.append(f"grid height {height} is outside 7..15")
    if not 8 <= width <= 17:
        errors.append(f"grid width {width} is outside 8..17")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or value not in (0, 5):
                errors.append(f"cell ({r},{c}) must be 0 or 5, found {value!r}")
                if len(errors) >= 4:
                    return errors

    components = _components(grid)
    if not components:
        errors.append("scene has no gray cells")
        return errors
    if len(components) > 5:
        errors.append(f"scene has {len(components)} components; maximum is 5")
    if len(components) == 1 and len(components[0]) < 5:
        errors.append(
            "a one-component lesson needs at least five gray cells; "
            "short isolated motifs are under-informative"
        )

    degrees = [_degree(cell, component) for component in components for cell in component]
    if not any(degree == 1 for degree in degrees):
        errors.append("scene has no degree-one gray cell for the rule to preserve")
    if not any(degree != 1 for degree in degrees):
        errors.append("scene is an identity case: every gray cell has degree one")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and useful generated topology; reject no-op lessons."""
    del difficulty, meta
    return _structural_errors(grid)


def strict_canonical_like(grid) -> list[str]:
    """The local rule lawfully applies to every accepted gray topology."""
    return _structural_errors(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription of the canonical local degree rule."""
    errors = _structural_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful scene: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for component in _components(grid):
        for r, c in component:
            if _degree((r, c), component) == 1:
                output[r][c] = 5
    return output


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every advertised axis directly from returned pixels."""
    errors = _structural_errors(grid)
    if errors:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(_components(grid)),
        "scene_pattern": _scene_pattern(grid),
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    errors = _structural_errors(grid)
    if errors:
        return {"valid": False, "errors": errors}
    components = _components(grid)
    degrees = [_degree(cell, component) for component in components for cell in component]
    return {
        "valid": True,
        "scene_pattern": _scene_pattern(grid),
        "components": len(components),
        "gray_cells": len(degrees),
        "degree_zero": sum(degree == 0 for degree in degrees),
        "degree_one": sum(degree == 1 for degree in degrees),
        "degree_two": sum(degree == 2 for degree in degrees),
        "degree_three_plus": sum(degree >= 3 for degree in degrees),
    }


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _orientations(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all unique rotations/reflections, normalized and sorted."""
    current = tuple(shape)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        cells = tuple((r, -c if reflected else c) for r, c in current)
        for _ in range(4):
            variants.add(_normalize(cells))
            cells = tuple((c, -r) for r, c in cells)
    return tuple(sorted(variants))


def _candidate_placements(
    shape: tuple[tuple[int, int], ...], height: int, width: int
) -> list[tuple[tuple[int, int], ...]]:
    candidates: list[tuple[tuple[int, int], ...]] = []
    for variant in _orientations(shape):
        max_r = max(r for r, _ in variant)
        max_c = max(c for _, c in variant)
        if max_r >= height or max_c >= width:
            continue
        for r0 in range(height - max_r):
            for c0 in range(width - max_c):
                candidates.append(tuple((r0 + r, c0 + c) for r, c in variant))
    return candidates


def _place_components(
    height: int,
    width: int,
    shapes: list[tuple[tuple[int, int], ...]],
    rng,
) -> list[list[int]]:
    """Backtrack over compact shape placements with orthogonal separation."""
    # Placing larger/less flexible objects first makes the minimum 7x8 corner
    # constructive without relying on lucky retries.
    ordered = sorted(
        enumerate(shapes),
        key=lambda item: (-len(item[1]), -len(_orientations(item[1])), item[0]),
    )
    candidate_sets: list[list[tuple[tuple[int, int], ...]]] = []
    for original_index, shape in ordered:
        candidates = _candidate_placements(shape, height, width)
        local_rng = rng if original_index == 0 else None
        if local_rng is not None:
            local_rng.shuffle(candidates)
        else:
            # Use the same deterministic stream, but make component-specific
            # shuffles independent of dictionary/set iteration.
            rng.shuffle(candidates)
        candidate_sets.append(candidates)

    occupied: set[tuple[int, int]] = set()
    chosen: list[tuple[tuple[int, int], ...]] = []
    nodes = 0

    def search(index: int) -> bool:
        nonlocal nodes
        if index == len(candidate_sets):
            return True
        for placement in candidate_sets[index]:
            nodes += 1
            if nodes > 300_000:
                return False
            placement_set = set(placement)
            if placement_set & occupied:
                continue
            if any(
                (r + dr, c + dc) in occupied
                for r, c in placement
                for dr, dc in _NEIGHBORS4
            ):
                continue
            occupied.update(placement_set)
            chosen.append(placement)
            if search(index + 1):
                return True
            chosen.pop()
            occupied.difference_update(placement_set)
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(shapes)} separated components in {height}x{width}"
        )

    grid = full_grid(height, width, 0)
    for placement in chosen:
        for r, c in placement:
            grid[r][c] = 5
    return grid


def _path_shape(rng, *, compact: bool) -> tuple[tuple[int, int], ...]:
    bank = _COMPACT_PATH_BANK if compact else _PATH_BANK
    return tuple(rng.choice(bank))


def _scene_shapes(
    scene: str,
    count: int,
    height: int,
    width: int,
    rng,
    *,
    canonical_anchor: bool,
) -> list[tuple[tuple[int, int], ...]]:
    if canonical_anchor:
        return [tuple(_PATH5), tuple(_PAIR)]

    compact = height * width <= 72 or count >= 5
    if scene == "path":
        first_bank = (_PATH3, _CORNER3) if compact else _PATH_BANK
        shapes = [tuple(rng.choice(first_bank))]
        while len(shapes) < count:
            shapes.append(_path_shape(rng, compact=True if compact else False))
        return shapes

    if scene == "branch":
        shapes = [tuple(_BRANCH_T), tuple(_SINGLETON)]
    elif scene == "cycle":
        shapes = [tuple(_CYCLE_TAIL), tuple(_SINGLETON)]
    elif scene == "singleton":
        shapes = [tuple(rng.choice((_PATH3, _CORNER3, _ZIGZAG4))), tuple(_SINGLETON)]
    else:  # validated by _validate_call / draw_choice
        raise ValueError(f"unknown scene pattern {scene!r}")

    while len(shapes) < count:
        shapes.append(_path_shape(rng, compact=True if compact else False))
    return shapes


def _default_options(difficulty: str | None) -> tuple[range, range, range]:
    if difficulty == "easy":
        return range(7, 10), range(8, 12), range(2, 4)
    if difficulty == "hard":
        return range(11, 16), range(13, 18), range(4, 6)
    if difficulty == "medium":
        return range(9, 13), range(10, 15), range(3, 5)
    return range(7, 16), range(8, 18), range(2, 6)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    scene = _draw_scene_axis(ctx, scheduled)

    canonical_anchor = scheduled == "path" and not overrides
    if canonical_anchor:
        height_options, width_options, count_options = (7,), (8,), (2,)
    else:
        height_options, width_options, count_options = _default_options(difficulty)

    height = _draw_int_axis(ctx, "grid_h", 7, 15, height_options)
    width = _draw_int_axis(ctx, "grid_w", 8, 17, width_options)
    count = _draw_int_axis(ctx, "component_count", 2, 5, count_options)

    layout_rng = ctx.draw_rng("layout")
    shapes = _scene_shapes(
        scene,
        count,
        height,
        width,
        layout_rng,
        canonical_anchor=canonical_anchor,
    )
    grid = _place_components(height, width, shapes, layout_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    recorded = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != recorded[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={recorded[axis]!r}, "
                f"observed={observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Semantic rivals and counterexample witnesses
# ---------------------------------------------------------------------------


def _blank_like(grid: list[list[int]]) -> list[list[int]]:
    return full_grid(len(grid), len(grid[0]), 0)


def _two_extrema_per_component(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: reduce every component to at most two representative cells."""
    output = _blank_like(grid)
    for component in _components(grid):
        endpoints = sorted(cell for cell in component if _degree(cell, component) == 1)
        if len(endpoints) == 2 and all(_degree(cell, component) <= 2 for cell in component):
            keep = endpoints
        else:
            ordered = sorted(component)
            keep = ordered[:1] if len(ordered) == 1 else [ordered[0], ordered[-1]]
        for r, c in keep:
            output[r][c] = 5
    return output


def _nonbranching_components_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: only solve components that are ordinary simple paths."""
    output = _blank_like(grid)
    for component in _components(grid):
        endpoints = [cell for cell in component if _degree(cell, component) == 1]
        if len(endpoints) == 2 and all(_degree(cell, component) <= 2 for cell in component):
            for r, c in endpoints:
                output[r][c] = 5
    return output


def _degree_at_most_one(grid: list[list[int]]) -> list[list[int]]:
    """Wrong local shortcut: retain isolated cells in addition to endpoints."""
    output = _blank_like(grid)
    for component in _components(grid):
        for r, c in component:
            if _degree((r, c), component) <= 1:
                output[r][c] = 5
    return output


def _has_branching_component(grid: list[list[int]]) -> bool:
    return any(
        any(_degree(cell, component) >= 3 for cell in component)
        for component in _components(grid)
    )


def _has_cyclic_component(grid: list[list[int]]) -> bool:
    return any(
        _component_edges(component) >= len(component)
        for component in _components(grid)
    )


def _has_isolated_cell(grid: list[list[int]]) -> bool:
    return any(len(component) == 1 for component in _components(grid))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "branching_component": _has_branching_component,
    "cyclic_component": _has_cyclic_component,
    "isolated_cell": _has_isolated_cell,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "two_extrema_per_component": _two_extrema_per_component,
    "nonbranching_components_only": _nonbranching_components_only,
    "degree_at_most_one": _degree_at_most_one,
}
WITNESS_RIVALS = {
    "branching_component": [
        "two_extrema_per_component",
        "nonbranching_components_only",
    ],
    "cyclic_component": [
        "two_extrema_per_component",
        "nonbranching_components_only",
    ],
    "isolated_cell": ["degree_at_most_one"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and reject any rival that survives the lesson."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is not lawful: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the degree-one rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Near-miss inputs used by the defect linter and regression tests."""
    blank = full_grid(7, 8, 0)

    pair_only = full_grid(7, 8, 0)
    pair_only[2][2] = pair_only[2][3] = 5

    short_line = full_grid(7, 8, 0)
    for col in range(4):
        short_line[3][col] = 5

    singleton_only = full_grid(7, 8, 0)
    singleton_only[2][2] = 5

    cycle_only = full_grid(7, 8, 0)
    for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)):
        cycle_only[r][c] = 5

    wrong_color = full_grid(7, 8, 0)
    wrong_color[1][1] = 8

    ragged = [[0, 5, 0], [0, 0], [0, 5, 0]]

    return [
        ("blank", blank),
        ("pair_only_identity", pair_only),
        ("short_line", short_line),
        ("singleton_only", singleton_only),
        ("cycle_without_endpoint", cycle_only),
        ("wrong_color", wrong_color),
        ("ragged", ragged),
    ]
