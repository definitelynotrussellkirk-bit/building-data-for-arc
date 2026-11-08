"""Generator for ``Recolor exact cyan line triominoes``.

The input is a zero-background grid containing cyan connected components.  The
selected rule recolors exactly those components that contain three cells in a
straight horizontal or vertical line.  Other cyan components stay unchanged.

Ordinary draws are constructive teaching scenes rather than positive-only
samples.  Every one contains horizontal and vertical targets, an L-triomino
contrast, a short straight contrast, multiple targets, and targets both on and
off the border.  These contrasts falsify the strongest cheap alternatives on a
single example while remaining inside the canonical 8x8--10x10 manifold.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3dcd7ae3aaf"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "672defea5335"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, inspect each 4-connected cyan (8) component. "
    "Recolor it orange (7) exactly when it has three cells forming one "
    "straight horizontal or vertical line; leave every other cyan component "
    "unchanged."
)

INVARIANTS = [
    "input colors are only background 0 and cyan 8",
    "each foreground object is a separate 4-connected cyan component",
    "ordinary draws contain at least two exact straight cyan triominoes",
    "ordinary draws contain both horizontal and vertical target orientations",
    "ordinary draws contain an L-triomino and a straight domino as non-targets",
    "ordinary draws contain both an edge target and an interior target",
]

# Public axes are only facts that can be recovered exactly from the returned
# grid.  Shape choices and layout profile are nuisance variation, not promises.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed choice in 8..10",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed choice in 8..10",
        "valid": "8..10",
    },
    "n_targets": {
        "type": "int",
        "default": "difficulty-skewed choice in 2..4",
        "valid": "2..4",
    },
    "n_distractors": {
        "type": "int",
        "default": "difficulty-skewed choice in 2..3",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

SCHEDULE_PROFILES = (0, 1, 2, 3)

# Normalized local coordinates for the small connected shapes used below.
_H3 = ((0, 0), (0, 1), (0, 2))
_V3 = ((0, 0), (1, 0), (2, 0))
_L3S = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_DOMINOES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)
_SIZE4_DISTRACTORS = (
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Curriculum slot; every four consecutive indices exercise all profiles."""
    return sample_index % len(SCHEDULE_PROFILES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")


def _difficulty_options(difficulty: Any) -> tuple[list[int], ...]:
    """Skew defaults without making any declared override illegal."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if difficulty == "easy":
        return (
            [8, 8, 8, 9, 9, 10],
            [8, 8, 8, 9, 9, 10],
            [2, 2, 2, 3, 4],
            [2, 2, 2, 3],
        )
    if difficulty == "hard":
        return (
            [8, 9, 10, 10, 10],
            [8, 9, 10, 10, 10],
            [2, 3, 4, 4, 4],
            [2, 3, 3, 3],
        )
    return (
        [8, 9, 9, 10],
        [8, 9, 9, 10],
        [2, 2, 3, 3, 4],
        [2, 2, 3, 3],
    )


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _cyan_components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected cyan components in stable top-left order."""
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 8
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            row, column = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    component.append(neighbor)
        components.append(sorted(component))
    return components


def _is_straight(component: Sequence[tuple[int, int]]) -> bool:
    rows = {row for row, _ in component}
    columns = {column for _, column in component}
    return len(rows) == 1 or len(columns) == 1


def _is_target(component: Sequence[tuple[int, int]]) -> bool:
    return len(component) == 3 and _is_straight(component)


def _is_horizontal_target(component: Sequence[tuple[int, int]]) -> bool:
    return _is_target(component) and len({row for row, _ in component}) == 1


def _is_vertical_target(component: Sequence[tuple[int, int]]) -> bool:
    return _is_target(component) and len({column for _, column in component}) == 1


def _touches_edge(
    component: Sequence[tuple[int, int]], height: int, width: int
) -> bool:
    return any(
        row in (0, height - 1) or column in (0, width - 1)
        for row, column in component
    )


def _candidate_placements(
    shape: Sequence[tuple[int, int]],
    height: int,
    width: int,
    position: str | None,
) -> list[frozenset[tuple[int, int]]]:
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(column for _, column in shape) + 1
    placements: list[frozenset[tuple[int, int]]] = []
    for anchor_row in range(height - shape_height + 1):
        for anchor_column in range(width - shape_width + 1):
            cells = frozenset(
                (anchor_row + row, anchor_column + column)
                for row, column in shape
            )
            edge = _touches_edge(cells, height, width)
            if position == "edge" and not edge:
                continue
            if position == "interior" and edge:
                continue
            placements.append(cells)
    return placements


def _plan_components(
    height: int,
    width: int,
    specs: Sequence[tuple[str, Sequence[tuple[int, int]], str | None]],
    rng,
) -> list[tuple[str, frozenset[tuple[int, int]]]]:
    """Place every component with no overlap or cardinal contact."""
    candidate_sets: list[
        tuple[str, list[frozenset[tuple[int, int]]]]
    ] = []
    for name, shape, position in specs:
        candidates = _candidate_placements(shape, height, width, position)
        rng.shuffle(candidates)
        candidate_sets.append((name, candidates))

    def search(
        index: int,
        occupied: set[tuple[int, int]],
        chosen: list[tuple[str, frozenset[tuple[int, int]]]],
    ) -> list[tuple[str, frozenset[tuple[int, int]]]] | None:
        if index == len(candidate_sets):
            return chosen
        name, candidates = candidate_sets[index]
        forbidden = set(occupied)
        for row, column in occupied:
            forbidden.update(
                ((row + 1, column), (row - 1, column),
                 (row, column + 1), (row, column - 1))
            )
        for cells in candidates:
            if cells & forbidden:
                continue
            result = search(
                index + 1,
                occupied | set(cells),
                [*chosen, (name, cells)],
            )
            if result is not None:
                return result
        return None

    result = search(0, set(), [])
    if result is None:
        raise RuntimeError(
            f"could not place {len(specs)} separated components in "
            f"{height}x{width}"
        )
    return result


def _component_specs(
    n_targets: int,
    n_distractors: int,
    profile: int,
) -> list[tuple[str, Sequence[tuple[int, int]], str | None]]:
    # Swap which orientation carries the edge cue across schedule slots.  The
    # other mandatory target is interior, so neither position is predictive.
    if profile % 2 == 0:
        specs = [
            ("target_edge_horizontal", _H3, "edge"),
            ("target_interior_vertical", _V3, "interior"),
        ]
    else:
        specs = [
            ("target_edge_vertical", _V3, "edge"),
            ("target_interior_horizontal", _H3, "interior"),
        ]

    for index in range(n_targets - 2):
        shape = _H3 if (profile + index) % 2 == 0 else _V3
        specs.append((f"target_extra_{index}", shape, None))

    specs.extend(
        [
            ("distractor_l_triomino", _L3S[profile], None),
            ("distractor_domino", _DOMINOES[profile % 2], None),
        ]
    )
    if n_distractors == 3:
        specs.append(
            ("distractor_size4", _SIZE4_DISTRACTORS[profile], None)
        )
    return specs


def _teaching_errors(grid: Sequence[Sequence[int]]) -> list[str]:
    """Strong ordinary-draw postconditions, intentionally stricter than canon."""
    components = _cyan_components(grid)
    targets = [component for component in components if _is_target(component)]
    non_targets = [component for component in components if not _is_target(component)]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if len(targets) < 2:
        errors.append("ordinary draws need multiple target triominoes")
    if not any(_is_horizontal_target(component) for component in targets):
        errors.append("ordinary draws need a horizontal target")
    if not any(_is_vertical_target(component) for component in targets):
        errors.append("ordinary draws need a vertical target")
    if not any(len(component) == 3 and not _is_straight(component) for component in non_targets):
        errors.append("ordinary draws need an L-triomino contrast")
    if not any(len(component) == 2 and _is_straight(component) for component in non_targets):
        errors.append("ordinary draws need a straight domino contrast")
    if not any(_touches_edge(component, height, width) for component in targets):
        errors.append("ordinary draws need an edge target")
    if not any(not _touches_edge(component, height, width) for component in targets):
        errors.append("ordinary draws need an interior target")
    return errors


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
    h_options, w_options, target_options, distractor_options = _difficulty_options(
        difficulty
    )
    height = ctx.draw_choice("grid_h", h_options)
    width = ctx.draw_choice("grid_w", w_options)
    n_targets = ctx.draw_choice("n_targets", target_options)
    n_distractors = ctx.draw_choice("n_distractors", distractor_options)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("component_layout")

    specs = _component_specs(n_targets, n_distractors, profile)
    placements = _plan_components(height, width, specs, rng)
    grid = full_grid(height, width, 0)
    for _, cells in placements:
        for row, column in cells:
            grid[row][column] = 8

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid input: " + "; ".join(errors))
    teaching_errors = _teaching_errors(grid)
    if teaching_errors:
        raise RuntimeError(
            "constructed weak teaching input: " + "; ".join(teaching_errors)
        )
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_targets": n_targets,
        "n_distractors": n_distractors,
    }
    if observed != expected:
        raise RuntimeError(
            f"keyed-axis mismatch: expected {expected}, observed {observed}"
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked canonical input grammar.

    Canonical examples intentionally contain legal non-target cyan components,
    so this checker validates the contrastive component family rather than
    requiring every cyan object to be a target.
    """
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 10:
        errors.append(f"height must be in 8..10, got {height}")
    if not 8 <= width <= 10:
        errors.append(f"width must be in 8..10, got {width}")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 8}:
        errors.append(
            f"input palette must be a subset of {{0, 8}}, got {sorted(palette)}"
        )
    if 0 not in palette:
        errors.append("input must retain a zero background")
    if 8 not in palette:
        errors.append("input must contain cyan foreground components")

    components = _cyan_components(grid)
    if not 2 <= len(components) <= 8:
        errors.append(f"need 2..8 cyan components, got {len(components)}")
    bad_sizes = sorted({len(component) for component in components if not 2 <= len(component) <= 4})
    if bad_sizes:
        errors.append(
            f"cyan component sizes must stay in 2..4, got invalid sizes {bad_sizes}"
        )
    target_count = sum(_is_target(component) for component in components)
    if target_count < 1:
        errors.append("need at least one exact straight cyan triomino target")
    if components and target_count == len(components):
        errors.append("need at least one unchanged non-target cyan component")
    if sum(value == 8 for row in grid for value in row) > (height * width) // 2:
        errors.append("foreground is too dense for the sparse component grammar")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked predicate used by the strict semantic census."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    components = _cyan_components(grid)
    n_targets = sum(_is_target(component) for component in components)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": n_targets,
        "n_distractors": len(components) - n_targets,
    }


def _paint_selected(
    grid: Sequence[Sequence[int]],
    predicate: Callable[[Sequence[tuple[int, int]]], bool],
) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _cyan_components(grid):
        if predicate(component):
            for row, column in component:
                output[row][column] = 7
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Diagnostic Python mirror; the selected Racket rule is authoritative."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    return _paint_selected(grid, _is_target)


def _identity(grid):
    return [list(row) for row in grid]


def _recolor_all_cyan(grid):
    return [[7 if value == 8 else value for value in row] for row in grid]


def _recolor_all_size3_components(grid):
    return _paint_selected(grid, lambda component: len(component) == 3)


def _recolor_horizontal_targets(grid):
    return _paint_selected(grid, _is_horizontal_target)


def _recolor_vertical_targets(grid):
    return _paint_selected(grid, _is_vertical_target)


def _recolor_first_target(grid):
    output = [list(row) for row in grid]
    for component in _cyan_components(grid):
        if _is_target(component):
            for row, column in component:
                output[row][column] = 7
            break
    return output


def _recolor_all_straight_components(grid):
    return _paint_selected(grid, _is_straight)


def _recolor_components_at_most_three(grid):
    return _paint_selected(grid, lambda component: len(component) <= 3)


def _recolor_edge_targets(grid):
    height, width = len(grid), len(grid[0])
    return _paint_selected(
        grid,
        lambda component: _is_target(component)
        and _touches_edge(component, height, width),
    )


def _recolor_interior_targets(grid):
    height, width = len(grid), len(grid[0])
    return _paint_selected(
        grid,
        lambda component: _is_target(component)
        and not _touches_edge(component, height, width),
    )


SEMANTIC_RIVALS: dict[
    str, Callable[[Sequence[Sequence[int]]], list[list[int]]]
] = {
    "identity": _identity,
    "recolor_all_cyan": _recolor_all_cyan,
    "recolor_all_size3_components": _recolor_all_size3_components,
    "recolor_only_horizontal_targets": _recolor_horizontal_targets,
    "recolor_only_vertical_targets": _recolor_vertical_targets,
    "recolor_only_first_target": _recolor_first_target,
    "recolor_all_straight_components": _recolor_all_straight_components,
    "recolor_components_at_most_three": _recolor_components_at_most_three,
    "recolor_only_edge_targets": _recolor_edge_targets,
    "recolor_only_interior_targets": _recolor_interior_targets,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _multiple_targets(grid) -> bool:
    return sum(_is_target(component) for component in _cyan_components(grid)) >= 2


def _both_target_orientations(grid) -> bool:
    components = _cyan_components(grid)
    return (
        any(_is_horizontal_target(component) for component in components)
        and any(_is_vertical_target(component) for component in components)
    )


def _l_triomino_contrast(grid) -> bool:
    return any(
        len(component) == 3 and not _is_straight(component)
        for component in _cyan_components(grid)
    )


def _short_straight_contrast(grid) -> bool:
    return any(
        len(component) == 2 and _is_straight(component)
        for component in _cyan_components(grid)
    )


def _edge_and_interior_targets(grid) -> bool:
    height, width = len(grid), len(grid[0])
    targets = [
        component for component in _cyan_components(grid) if _is_target(component)
    ]
    return (
        any(_touches_edge(component, height, width) for component in targets)
        and any(not _touches_edge(component, height, width) for component in targets)
    )


SEMANTIC_WITNESSES = {
    "multiple_targets": _multiple_targets,
    "horizontal_and_vertical_targets": _both_target_orientations,
    "l_triomino_unchanged": _l_triomino_contrast,
    "short_straight_component_unchanged": _short_straight_contrast,
    "edge_and_interior_targets": _edge_and_interior_targets,
}

WITNESS_RIVALS = {
    "multiple_targets": ["recolor_only_first_target"],
    "horizontal_and_vertical_targets": [
        "identity",
        "recolor_only_horizontal_targets",
        "recolor_only_vertical_targets",
    ],
    "l_triomino_unchanged": [
        "recolor_all_cyan",
        "recolor_all_size3_components",
        "recolor_components_at_most_three",
    ],
    "short_straight_component_unchanged": [
        "recolor_all_cyan",
        "recolor_all_straight_components",
        "recolor_components_at_most_three",
    ],
    "edge_and_interior_targets": [
        "recolor_only_edge_targets",
        "recolor_only_interior_targets",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared wrong rule survives every demo."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"{role} input is not canonical-like: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(
                f"{role} output does not match exact straight-triomino recoloring"
            )
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def _paint_shape(
    grid: list[list[int]],
    shape: Sequence[tuple[int, int]],
    anchor_row: int,
    anchor_column: int,
    color: int = 8,
) -> None:
    for row, column in shape:
        grid[anchor_row + row][anchor_column + column] = color


def mutation_fixtures():
    """Task-local near misses that the input checker must reject."""
    blank = full_grid(8, 8, 0)

    no_target = full_grid(8, 8, 0)
    _paint_shape(no_target, _L3S[0], 0, 0)
    _paint_shape(no_target, _DOMINOES[0], 0, 5)
    _paint_shape(no_target, _SIZE4_DISTRACTORS[1], 3, 7)

    all_targets = full_grid(8, 8, 0)
    _paint_shape(all_targets, _H3, 1, 1)
    _paint_shape(all_targets, _V3, 4, 5)

    singleton_component = full_grid(8, 8, 0)
    _paint_shape(singleton_component, _H3, 0, 0)
    _paint_shape(singleton_component, _V3, 3, 5)
    singleton_component[7][0] = 8

    oversized_component = full_grid(8, 8, 0)
    _paint_shape(oversized_component, _H3, 0, 0)
    _paint_shape(oversized_component, ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)), 2, 6)

    wrong_palette = full_grid(8, 8, 0)
    _paint_shape(wrong_palette, _H3, 0, 0)
    _paint_shape(wrong_palette, _V3, 2, 5)
    _paint_shape(wrong_palette, _L3S[2], 5, 0)
    wrong_palette[7][7] = 7

    return [
        ("blank_no_components", blank),
        ("no_exact_straight_triomino", no_target),
        ("all_components_are_targets", all_targets),
        ("singleton_component", singleton_component),
        ("oversized_component", oversized_component),
        ("input_contains_output_color", wrong_palette),
    ]
