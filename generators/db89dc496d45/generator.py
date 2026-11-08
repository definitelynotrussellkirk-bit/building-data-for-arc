"""Curriculum for selecting and cropping the largest connected component.

The canonical examples are also explained by color-frequency shortcuts.  The
curriculum alternates two source-bound counterexample profiles:

* a disconnected distractor color has the largest aggregate population even
  though each of its components is smaller than the target; and
* the target color itself has a disconnected extra fragment and is followed by
  another split color in aggregate-frequency rank.

Together they distinguish connected-component size from global color count,
"take the largest piece of the most frequent color", and conditional rules such
as "if the top color is split, use the second-most-frequent color".
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db89dc496d45"
TASK_ID = GENERATOR_ID
VERSION = "3.1.2"
RULE_HASH = "56bd46ef5a5e"

SUMMARY = (
    "Place a unique largest 4-connected monochromatic component together with "
    "smaller distractor components and crop to that component's bounding box. "
    "Alternating scenes make either a distractor color or the target color "
    "globally dominant through disconnected fragments, refuting aggregate and "
    "conditional color-ranking shortcuts."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "there are at least two non-zero 4-connected monochromatic components",
    "one component is uniquely largest by cell count",
    "the generated target has 5..12 cells",
    "at least one globally dominant color is split across disconnected components",
    "the curriculum alternates split-distractor and split-target counterexamples",
]

PROFILE_DIMENSIONS = {
    "canonical_9x11": (9, 11),
    "canonical_10x12": (10, 12),
    "canonical_11x13": (11, 13),
    "canonical_12x12": (12, 12),
    "expanded_14x16": (14, 16),
    "expanded_16x18": (16, 18),
}
SCENE_PROFILES = tuple(PROFILE_DIMENSIONS)
SCHEDULE_PROFILES = SCENE_PROFILES
SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "six-profile cyclic schedule",
        "valid": "canonical_9x11|canonical_10x12|canonical_11x13|canonical_12x12|expanded_14x16|expanded_16x18",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

_REGION_H = 4
_REGION_W = 5


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic public lesson profile for one sample index."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % SCHEDULE_PERIOD]


def _grow_connected_shape(size: int, rng) -> set[tuple[int, int]]:
    start = (rng.randrange(_REGION_H), rng.randrange(_REGION_W))
    cells = {start}
    while len(cells) < size:
        frontier = sorted(
            {
                (nr, nc)
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                for nr, nc in ((r + dr, c + dc),)
                if 0 <= nr < _REGION_H
                and 0 <= nc < _REGION_W
                and (nr, nc) not in cells
            }
        )
        if not frontier:  # impossible before all 20 cells are occupied
            raise RuntimeError("connected-shape frontier unexpectedly exhausted")
        cells.add(rng.choice(frontier))
    return cells


def _bbox_area(cells: set[tuple[int, int]]) -> int:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _connected_shape(size: int, rng, *, require_sparse: bool = False) -> set[tuple[int, int]]:
    """Grow an exact connected shape inside the fixed 4x5 macro-region."""
    if not 1 <= size <= _REGION_H * _REGION_W:
        raise ValueError(f"shape size {size} does not fit {_REGION_H}x{_REGION_W}")
    for _ in range(128):
        cells = _grow_connected_shape(size, rng)
        if not require_sparse or _bbox_area(cells) > size:
            return cells

    # Deterministic connected perimeter fallback. Every prefix of length 5..12
    # has a 4x2..4x5 bounding box strictly larger than its cell population.
    path = [
        (0, 0), (1, 0), (2, 0), (3, 0),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (2, 4), (1, 4), (0, 4), (0, 3),
        (0, 2), (0, 1), (1, 1), (1, 2),
        (1, 3), (2, 3), (2, 2), (2, 1),
    ]
    fallback = set(path[:size])
    if rng.choice((False, True)):
        fallback = {(row, _REGION_W - 1 - col) for row, col in fallback}
    if rng.choice((False, True)):
        fallback = {(_REGION_H - 1 - row, col) for row, col in fallback}
    return fallback


def _paint(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: set[tuple[int, int]] | tuple[tuple[int, int], ...],
    color: int,
) -> None:
    top, left = origin
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _extra_components(count: int, rng) -> list[set[tuple[int, int]]]:
    """Return 1..3 mutually isolated small components in one 4x5 region."""
    slots = (
        (
            ((0, 0), (0, 1), (1, 0)),
            ((1, 0), (0, 0), (1, 1)),
        ),
        (
            ((0, 4), (0, 3), (1, 4)),
            ((1, 4), (0, 4), (1, 3)),
        ),
        (
            ((3, 2), (3, 1), (3, 3)),
            ((3, 1), (3, 2), (2, 1)),
        ),
    )
    if not 1 <= count <= len(slots):
        raise ValueError(f"extra component count must be 1..3, got {count}")
    result: list[set[tuple[int, int]]] = []
    for index in range(count):
        variant = rng.choice(slots[index])
        size = rng.randint(1, 3)
        result.append(set(variant[:size]))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, shortcut-refuting crop-largest input grid."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    if "scene_profile" in overrides and not isinstance(overrides["scene_profile"], str):
        raise TypeError("scene_profile must be a non-null string")

    requested = overrides.get(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    effective_overrides = dict(overrides)
    effective_overrides["scene_profile"] = requested
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    h, w = PROFILE_DIMENSIONS[profile]
    grid = full_grid(h, w, 0)

    # The four corner macro-regions are separated by at least one blank row and
    # column even on the minimum 9x11 canvas. Thus no requested object can be
    # silently dropped or accidentally merged with an object in another role.
    regions = [
        (0, 0),
        (0, w - _REGION_W),
        (h - _REGION_H, 0),
        (h - _REGION_H, w - _REGION_W),
    ]
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "mixed"
    layout_rng = ctx.draw_rng(f"layout_{band}")
    layout_rng.shuffle(regions)
    target_region, split_a_region, split_b_region, extras_region = regions

    target_size = 5 + ((seed + sample_index) % 8)
    # Consecutive sample indices still alternate the two semantic profiles for
    # any fixed lesson seed, but seed parity prevents exact dimensions from
    # revealing which color-ranking counterexample was chosen.
    split_target_profile = ((seed // 8) + sample_index) % 2 == 1
    split_total = target_size if split_target_profile else target_size + 1
    split_a_size = split_total // 2
    split_b_size = split_total - split_a_size
    extra_count = 1 if profile.startswith("canonical_") else (
        2 if profile == "expanded_14x16" else 3
    )

    colors = ctx.draw_distinct_colors(
        f"palette_{band}", n=2 + extra_count, exclude={0}
    )
    target_color, split_color, *extra_colors = colors

    _paint(
        grid,
        target_region,
        _connected_shape(target_size, layout_rng, require_sparse=True),
        target_color,
    )
    _paint(
        grid,
        split_a_region,
        _connected_shape(split_a_size, layout_rng),
        split_color,
    )
    _paint(
        grid,
        split_b_region,
        _connected_shape(split_b_size, layout_rng),
        split_color,
    )
    if split_target_profile:
        # Make the target color globally most frequent while keeping its main
        # component uniquely largest.  The reserved cell is separated from the
        # target region by the macro-region gutter and never overlaps the extra
        # component templates below.
        _paint(grid, extras_region, ((3, 4),), target_color)
    for color, cells in zip(
        extra_colors, _extra_components(extra_count, layout_rng), strict=True
    ):
        _paint(grid, extras_region, cells, color)
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an integer color 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    """Return all non-zero 4-connected monochromatic components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _crop_cells(
    grid: list[list[int]], cells: set[tuple[int, int]] | list[tuple[int, int]]
) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of ``(extract-largest g 0)`` on this domain."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    components = _components(grid)
    if not components:
        raise ValueError("grid has no non-zero component")
    largest_size = max(len(cells) for _, cells in components)
    largest = [cells for _, cells in components if len(cells) == largest_size]
    if len(largest) != 1:
        raise ValueError("largest component is not unique")
    return _crop_cells(grid, largest[0])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Own the full lawful canonical domain and diagnose malformed inputs."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must occur")
    components = _components(grid)
    if len(components) < 2:
        errors.append(
            f"expected at least two non-zero components, found {len(components)}"
        )
        return errors
    sizes = [len(cells) for _, cells in components]
    largest_size = max(sizes)
    if sizes.count(largest_size) != 1:
        errors.append("largest component is not unique")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical grammar is exactly the unique-largest-component domain."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the one exact public axis from a generated grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    dimensions = (len(grid), len(grid[0]))
    profile = next(
        (name for name, dims in PROFILE_DIMENSIONS.items() if dims == dimensions),
        None,
    )
    return {"scene_profile": profile}


def _most_frequent_color_crop(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical-fitting rival: aggregate disconnected cells by color."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("grid has no non-zero color")
    color = max(counts, key=lambda value: (counts[value], -value))
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    return _crop_cells(grid, cells)


def _color_groups(
    grid: list[list[int]],
) -> dict[int, list[set[tuple[int, int]]]]:
    groups: dict[int, list[set[tuple[int, int]]]] = {}
    for color, cells in _components(grid):
        groups.setdefault(color, []).append(cells)
    return groups


def _ranked_colors(grid: list[list[int]]) -> list[int]:
    counts = Counter(value for row in grid for value in row if value != 0)
    return sorted(counts, key=lambda color: (-counts[color], color))


def _largest_component_of_most_frequent_color(
    grid: list[list[int]],
) -> list[list[int]]:
    """Canonical-fitting rival: pick only the largest piece of the top color."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    ranked = _ranked_colors(grid)
    if not ranked:
        raise ValueError("grid has no non-zero color")
    groups = _color_groups(grid)[ranked[0]]
    cells = max(groups, key=lambda group: (len(group), -min(group)[0], -min(group)[1]))
    return _crop_cells(grid, cells)


def _second_color_when_top_disconnected(
    grid: list[list[int]],
) -> list[list[int]]:
    """Canonical-fitting rival exposed by the first split-distractor repair."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    ranked = _ranked_colors(grid)
    if not ranked:
        raise ValueError("grid has no non-zero color")
    groups = _color_groups(grid)
    chosen = ranked[1] if len(groups[ranked[0]]) > 1 and len(ranked) > 1 else ranked[0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == chosen
    ]
    return _crop_cells(grid, cells)


def _largest_single_component_color(
    grid: list[list[int]],
) -> list[list[int]]:
    """Canonical-fitting rival: ignore colors occurring in multiple pieces."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    ranked = _ranked_colors(grid)
    if not ranked:
        raise ValueError("grid has no non-zero color")
    groups = _color_groups(grid)
    chosen = next((color for color in ranked if len(groups[color]) == 1), ranked[0])
    cells = groups[chosen][0] if len(groups[chosen]) == 1 else max(
        groups[chosen], key=len
    )
    return _crop_cells(grid, cells)


def _largest_component_record(
    grid: list[list[int]],
) -> tuple[int, set[tuple[int, int]], int] | None:
    components = _components(grid)
    if not components:
        return None
    largest_size = max(len(cells) for _, cells in components)
    largest = [item for item in components if len(item[1]) == largest_size]
    if len(largest) != 1:
        return None
    return largest[0][0], largest[0][1], largest_size


def _split_distractor_color_dominates_by_total(grid: list[list[int]]) -> bool:
    if _grid_errors(grid):
        return False
    largest = _largest_component_record(grid)
    if largest is None:
        return False
    target_color, _, largest_size = largest
    by_color = _color_groups(grid)
    structural_witness = any(
        color != target_color
        and len(groups) >= 2
        and all(len(group) < largest_size for group in groups)
        and sum(len(group) for group in groups) > largest_size
        for color, groups in by_color.items()
    )
    if not structural_witness:
        return False
    try:
        truth = rule_mirror(grid)
        return (
            _most_frequent_color_crop(grid) != truth
            and _largest_component_of_most_frequent_color(grid) != truth
        )
    except ValueError:
        return False


def _split_target_color_dominates_by_total(grid: list[list[int]]) -> bool:
    if _grid_errors(grid):
        return False
    largest = _largest_component_record(grid)
    if largest is None:
        return False
    target_color, _, largest_size = largest
    by_color = _color_groups(grid)
    ranked = _ranked_colors(grid)
    if not ranked or ranked[0] != target_color or len(by_color[target_color]) < 2:
        return False
    if not any(
        color != target_color
        and len(groups) >= 2
        and all(len(group) < largest_size for group in groups)
        for color, groups in by_color.items()
    ):
        return False
    try:
        truth = rule_mirror(grid)
        return (
            _most_frequent_color_crop(grid) != truth
            and _second_color_when_top_disconnected(grid) != truth
            and _largest_single_component_color(grid) != truth
        )
    except ValueError:
        return False


SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "most_frequent_color": _most_frequent_color_crop,
    "largest_component_of_most_frequent_color": (
        _largest_component_of_most_frequent_color
    ),
    "second_color_when_top_disconnected": _second_color_when_top_disconnected,
    "largest_single_component_color": _largest_single_component_color,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "split_distractor_color_dominates_by_total": (
        _split_distractor_color_dominates_by_total
    ),
    "split_target_color_dominates_by_total": (
        _split_target_color_dominates_by_total
    ),
}
WITNESS_RIVALS = {
    "split_distractor_color_dominates_by_total": [
        "most_frequent_color",
        "largest_component_of_most_frequent_color",
    ],
    "split_target_color_dominates_by_total": [
        "most_frequent_color",
        "second_color_when_top_disconnected",
        "largest_single_component_color",
    ],
}
