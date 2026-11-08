"""Curriculum sampler for ARC task ``0f801939eff6``.

The authoritative rule extracts every same-color 4-connected non-background
component, sorts components by ``(-area, color)``, and emits one horizontal
color strip whose run lengths are the component areas.

The canonical demonstrations use one component per color, so they also fit a
strong but wrong rival: aggregate all cells by color.  This sampler schedules
explicit disconnected-same-color counterexamples, and separately schedules
equal-area pairs whose color order disagrees with row-major position order.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0f801939eff6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "cbb04236ecda"

SUMMARY = (
    "Four separated monochrome 4-connected components on a 0 background. "
    "The four-step curriculum crosses unique versus repeated component colors "
    "with distinct versus tied component areas. Repeated-color scenes force "
    "component extraction rather than global color counting; tied-area scenes "
    "force the canonical ascending-color tiebreak rather than position order. "
    "The output is one row formed by sorting components by area descending, "
    "then color ascending, and repeating each component color by its area."
)

INVARIANTS = [
    "exactly four generated nonzero components are 4-connected and separated by at least one background cell",
    "every generated output length is the total nonzero area and is at most 28",
    "repeated-color profiles contain two disconnected components of one color and refute color-frequency aggregation",
    "tie profiles contain exactly one equal-area pair and refute row-major position tiebreaking",
]

SCENE_PROFILES = (
    "unique_distinct",
    "repeated_distinct",
    "unique_tie",
    "repeated_tie",
)
SCHEDULE_PROFILES = SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = len(SCENE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8..16; canonical heights 8..10 are favored",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "11..18; canonical widths 11..13 are favored",
        "valid": "11..18",
    },
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile semantic curriculum",
        "valid": "unique_distinct|repeated_distinct|unique_tie|repeated_tie",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_coordinates(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be a literal integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be a literal integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic profile assigned to this sample index."""
    _validate_coordinates(seed, sample_index)
    _band(difficulty)
    return SCENE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_dimension(ctx, label: str, lo: int, hi: int, band: str) -> int:
    """Draw from the full advertised domain while retaining canonical anchors."""
    choices = list(range(lo, hi + 1))
    if label == "grid_h":
        canonical = (8, 9, 10)
        broad = {"easy": (8, 9, 10), "medium": (10, 11, 12), "hard": (14, 15, 16)}[band]
    else:
        canonical = (11, 12, 13)
        broad = {"easy": (11, 12, 13), "medium": (13, 14, 15), "hard": (16, 17, 18)}[band]
    # Every value remains legal in every band.  Duplicate choices are weights,
    # not hidden clipping; exact overrides are still consumed by draw_choice.
    choices += list(canonical) * 20
    choices += list(broad) * 2
    return ctx.draw_choice(label, choices)


def _grow_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Draw a connected polyomino of ``size`` cells inside a 3x3 footprint."""
    if not 1 <= size <= 7:
        raise ValueError(f"unsupported component size: {size}")
    start = (rng.randrange(3), rng.randrange(3))
    cells = {start}
    while len(cells) < size:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _NEIGHBORS
                if 0 <= r + dr < 3 and 0 <= c + dc < 3 and (r + dr, c + dc) not in cells
            }
        )
        if not frontier:  # impossible below 9 cells, kept as a loud invariant
            raise RuntimeError("3x3 shape frontier exhausted before requested area")
        cells.add(rng.choice(frontier))
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _pad(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _place_shapes(
    shapes: Sequence[Sequence[tuple[int, int]]], height: int, width: int, rng
) -> list[set[tuple[int, int]]]:
    """Place every shape by exhaustive finite backtracking; never drop an item."""
    candidates: list[list[set[tuple[int, int]]]] = []
    for shape in shapes:
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        options = [
            {(r0 + r, c0 + c) for r, c in shape}
            for r0 in range(height - shape_h + 1)
            for c0 in range(width - shape_w + 1)
        ]
        rng.shuffle(options)
        candidates.append(options)

    order = sorted(range(len(shapes)), key=lambda index: -len(shapes[index]))
    placed: list[set[tuple[int, int]] | None] = [None] * len(shapes)

    def search(depth: int, blocked: set[tuple[int, int]]) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in candidates[index]:
            if cells & blocked:
                continue
            placed[index] = cells
            if search(depth + 1, blocked | _pad(cells)):
                return True
            placed[index] = None
        return False

    if not search(0, set()):
        raise RuntimeError(
            f"constructive placement failed for {len(shapes)} shapes on {height}x{width}"
        )
    return [set(cells) for cells in placed if cells is not None]


def _draw_sizes(profile: str, width: int, rng) -> list[int]:
    """Choose areas whose one-row output is wider than the source grid.

    Every canonical pair is a genuine 2-D-to-long-row reshape, not a crop.
    Enumerating the tiny finite area space makes that relation constructive
    for every advertised width instead of relying on rejection luck.
    """
    if profile.endswith("_distinct"):
        candidates = [
            list(values)
            for values in combinations(range(1, 8), 4)
            if sum(values) > width
        ]
    else:
        candidates = [
            [high, tied, tied, low]
            for low, tied, high in combinations(range(1, 8), 3)
            if high + 2 * tied + low > width
        ]
    if not candidates:
        raise ValueError(f"no component-area profile can reshape width {width}")
    sizes = list(rng.choice(candidates))
    rng.shuffle(sizes)
    return sizes


def _assign_colors(
    profile: str,
    sizes: Sequence[int],
    placements: Sequence[set[tuple[int, int]]],
    rng,
) -> list[int]:
    anchors = [min(cells) for cells in placements]
    tied = profile.endswith("_tie")
    repeated = profile.startswith("repeated_")

    if repeated:
        palette = rng.sample(range(1, 10), 3)
        repeated_color, other_a, other_b = palette
        high_index = max(range(4), key=lambda index: sizes[index])
        low_index = min(range(4), key=lambda index: sizes[index])
        colors: list[int | None] = [None] * 4
        colors[high_index] = repeated_color
        colors[low_index] = repeated_color
        middle = [i for i in range(4) if i not in (high_index, low_index)]
        if tied:
            earlier, later = sorted(middle, key=lambda index: anchors[index])
            colors[earlier] = max(other_a, other_b)
            colors[later] = min(other_a, other_b)
        else:
            rng.shuffle(middle)
            colors[middle[0]] = other_a
            colors[middle[1]] = other_b
        return [int(color) for color in colors]

    palette = rng.sample(range(1, 10), 4)
    colors = list(palette)
    rng.shuffle(colors)
    if tied:
        counts = Counter(sizes)
        tied_size = next(size for size, count in counts.items() if count == 2)
        pair = [index for index, size in enumerate(sizes) if size == tied_size]
        earlier, later = sorted(pair, key=lambda index: anchors[index])
        low_color, high_color = min(colors[earlier], colors[later]), max(
            colors[earlier], colors[later]
        )
        colors[earlier] = high_color
        colors[later] = low_color
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_coordinates(seed, sample_index)
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a literal integer, not {type(value).__name__}")
    requested = overrides.get("scene_profile")
    if requested is not None and (
        type(requested) is not str or requested not in SCENE_PROFILES
    ):
        raise ValueError(f"unknown scene_profile: {requested!r}")

    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_dimension(ctx, "grid_h", 8, 16, band)
    width = _draw_dimension(ctx, "grid_w", 11, 18, band)
    profile = ctx.draw_choice("scene_profile", (scheduled,))

    object_rng = ctx.draw_rng("objects")
    sizes = _draw_sizes(profile, width, object_rng)
    shapes = [_grow_shape(object_rng, size) for size in sizes]
    placements = _place_shapes(shapes, height, width, object_rng)
    colors = _assign_colors(profile, sizes, placements, ctx.draw_rng("colors"))

    grid = full_grid(height, width, 0)
    for cells, color in zip(placements, colors):
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement collision")
            grid[row][col] = color
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(
                {
                    "color": color,
                    "size": len(cells),
                    "anchor": min(cells),
                    "cells": tuple(sorted(cells)),
                }
            )
    return components


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    ordered = sorted(_components(grid), key=lambda item: (-item["size"], item["color"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def _color_frequency_aggregate(grid) -> list[list[int]]:
    """RIVAL: merge disconnected same-color components before sorting."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    counts = Counter(value for row in grid for value in row if value != 0)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    row = [color for color, count in ordered for _ in range(count)]
    return [row or [0]]


def _position_tiebreak(grid) -> list[list[int]]:
    """RIVAL: break equal-area ties by top-left position instead of color."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    ordered = sorted(_components(grid), key=lambda item: (-item["size"], item["anchor"]))
    row = [item["color"] for item in ordered for _ in range(item["size"])]
    return [row or [0]]


def _profile_from_components(components: Sequence[dict[str, Any]]) -> str | None:
    if len(components) != 4:
        return None
    color_counts = Counter(item["color"] for item in components)
    size_counts = Counter(item["size"] for item in components)
    repeated = sorted(color_counts.values()) == [1, 1, 2]
    unique = sorted(color_counts.values()) == [1, 1, 1, 1]
    tied = sorted(size_counts.values()) == [1, 1, 2]
    distinct = sorted(size_counts.values()) == [1, 1, 1, 1]
    if not (repeated or unique) or not (tied or distinct):
        return None
    return ("repeated" if repeated else "unique") + "_" + (
        "tie" if tied else "distinct"
    )


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared axis from returned pixels."""
    if _rectangular_errors(grid):
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_profile": _profile_from_components(_components(grid)),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical task manifold and reject malformed/degenerate scenes."""
    del difficulty
    errors = _rectangular_errors(grid)
    if errors:
        return errors
    components = _components(grid)
    if not 2 <= len(components) <= 8:
        errors.append(f"expected 2..8 nonzero components, found {len(components)}")
        return errors
    total = sum(item["size"] for item in components)
    if total > 30:
        errors.append(f"encoded output row would exceed 30 cells: {total}")
    if len({item["size"] for item in components}) < 2:
        errors.append("all component areas are equal, so descending order is hidden")
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize lawful inputs for the canonical component-area rule.

    This predicate deliberately describes the task manifold, including the
    canonical three-component scenes.  Scheduled branch discrimination is
    measured separately by SEMANTIC_WITNESSES and WITNESS_RIVALS.
    """
    return self_check(grid)


def _disconnected_same_color_witness(grid) -> bool:
    if _rectangular_errors(grid):
        return False
    components = _components(grid)
    return (
        len({item["color"] for item in components}) < len(components)
        and rule_mirror(grid) != _color_frequency_aggregate(grid)
    )


def _equal_area_color_tiebreak_witness(grid) -> bool:
    if _rectangular_errors(grid):
        return False
    sizes = [item["size"] for item in _components(grid)]
    return len(set(sizes)) < len(sizes) and rule_mirror(grid) != _position_tiebreak(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "color_frequency_aggregate": _color_frequency_aggregate,
    "position_tiebreak": _position_tiebreak,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "disconnected_same_color": _disconnected_same_color_witness,
    "equal_area_color_tiebreak": _equal_area_color_tiebreak_witness,
}
WITNESS_RIVALS = {
    "disconnected_same_color": ["color_frequency_aggregate"],
    "equal_area_color_tiebreak": ["position_tiebreak"],
}
# Every labeled canonical pair uses one component per color, so this rival is a
# verified canonical shortcut.  Position tiebreaking is intentionally omitted:
# a canonical equal-area example already refutes it.
CANONICAL_SHORTCUTS = {
    "color_frequency_aggregate": _color_frequency_aggregate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when three demonstrations leave a declared rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the component-area rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the component-area rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
