"""Shortcut-refuting curriculum for cropping the largest connected component.

The selected rule is ``(rule! extract-largest)``.  Canonical examples also fit
several color-frequency heuristics, so ordinary generated lessons alternate two
counterexample phases:

* ``split_distractor`` — a distractor color is globally most frequent only
  because it is split across two components, each smaller than the target; and
* ``split_target`` — the target color is globally most frequent but has an extra
  disconnected fragment, while another color is split as well.

Both phases keep one uniquely largest monochromatic 4-connected component.  The
answer is the tight bounding-box crop of that component, including background
holes inside the box.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fea6a4ce763f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "5f27f31fdbe8"

SUMMARY = (
    "Generate a canonical-scale zero-background scene with one uniquely largest "
    "4-connected monochromatic component and crop to its bounding box. Ordinary "
    "lessons alternate split-distractor and split-target color-frequency "
    "counterexamples, so aggregate-color and conditional color-ranking shortcuts "
    "cannot explain the demonstrations."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "there are at least two non-zero monochromatic 4-connected components",
    "one component is uniquely largest by cell count",
    "the target crop contains at least one background hole",
    "ordinary lessons alternate split-distractor and split-target counterexamples",
]

# These are exactly the five canonical (height, width, palette-size) profiles.
# Keeping palette size in the profile prevents a dimension-only override from
# silently drifting away from the task's observed color support.
PROFILE_DIMENSIONS = {
    "canonical_5x10_p4": (5, 10, 4),
    "canonical_6x11_p4": (6, 11, 4),
    "canonical_7x9_p4": (7, 9, 4),
    "canonical_7x13_p4": (7, 13, 4),
    "canonical_9x9_p5": (9, 9, 5),
}
SCHEDULE_PROFILES = tuple(PROFILE_DIMENSIONS)
# Dimension profile repeats every five indices; the semantic phase repeats every
# two.  Their combined finite schedule therefore repeats every ten indices.
SCHEDULE_PERIOD = len(SCHEDULE_PROFILES) * 2
LESSON_SCHEDULE_PERIOD = SCHEDULE_PERIOD

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five canonical profiles in a cyclic schedule",
        "valid": "canonical_5x10_p4|canonical_6x11_p4|canonical_7x9_p4|canonical_7x13_p4|canonical_9x9_p5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Every target is connected, has 6 or 7 cells, spans its full listed bbox, and
# leaves at least one zero inside that bbox.  This makes crop boundaries visible
# rather than teaching a weaker solid-color answer.
_TARGET_TEMPLATES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3)),
)
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_TRIOMINOES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the exact public canvas/palette profile for one sample index."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def semantic_phase(seed, sample_index, difficulty=None):
    """Return the source-bound color-ranking counterexample phase."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return "split_distractor" if sample_index % 2 == 0 else "split_target"


def _paint(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: tuple[tuple[int, int], ...] | set[tuple[int, int]],
    color: int,
) -> None:
    top, left = origin
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _reflect_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _reflect_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic canonical-profile crop-largest lesson input."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")

    requested = overrides.get(
        "scene_profile", schedule_profile(seed, sample_index, difficulty)
    )
    if not isinstance(requested, str):
        raise TypeError("scene_profile must be a non-null string")
    if requested not in PROFILE_DIMENSIONS:
        raise ValueError(
            f"scene_profile must be one of {list(PROFILE_DIMENSIONS)}, got {requested!r}"
        )

    # Pass the scheduled default through the same exact override path so the
    # context receipt and explicit calls exercise identical code.
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
    profile = ctx.draw_choice("scene_profile", list(SCHEDULE_PROFILES))
    h, w, palette_size = PROFILE_DIMENSIONS[profile]
    grid = full_grid(h, w, 0)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "mixed"
    # Difficulty changes only keyed randomness, never the public profile or
    # semantic guarantee. This keeps every band on the canonical manifold while
    # making the advertised difficulty argument observably live.
    rng = ctx.draw_rng(f"layout_{band}")

    colors = ctx.draw_distinct_colors(
        f"palette_{band}", n=palette_size - 1, exclude={0}
    )
    target_color, split_color, *extra_colors = colors

    target = rng.choice(_TARGET_TEMPLATES)
    _paint(grid, (0, 0), target, target_color)

    # On the minimum 5x9 canvas the target occupies columns 0..3, column 4 is
    # blank, the two split components occupy columns w-4..w-3, column w-2 is
    # blank, and the rightmost column is reserved for isolated fragments.
    split_origin_a = (0, w - 4)
    split_origin_b = (h - 2, w - 4)
    phase = semantic_phase(seed, sample_index, difficulty)
    if phase == "split_distractor":
        _paint(grid, split_origin_a, _SQUARE, split_color)
        _paint(grid, split_origin_b, _SQUARE, split_color)
    else:
        _paint(grid, split_origin_a, rng.choice(_TRIOMINOES), split_color)
        _paint(grid, split_origin_b, rng.choice(_TRIOMINOES), split_color)

    # The reserved rightmost-column rows are pairwise non-adjacent on every
    # supported height.  A split-target scene consumes one slot for a detached
    # target fragment; the remaining slots expose every requested extra color.
    reserved_rows = (0, h // 2, h - 1)
    extra_cursor = 0
    if phase == "split_target":
        grid[reserved_rows[0]][w - 1] = target_color
        extra_cursor = 1
    for color in extra_colors:
        grid[reserved_rows[extra_cursor]][w - 1] = color
        extra_cursor += 1

    # Reflections preserve the profile while moving the target across all four
    # corners and increasing spatial diversity without weakening invariants.
    if rng.choice((False, True)):
        grid = _reflect_lr(grid)
    if rng.choice((False, True)):
        grid = _reflect_ud(grid)
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
    """Return all non-zero monochromatic 4-connected components."""
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
    """Own the full lawful canonical unique-largest-component domain."""
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
    """Canonical grammar: background plus a uniquely largest component."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public profile from dimensions and palette size."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    observed = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    profile = next(
        (name for name, signature in PROFILE_DIMENSIONS.items() if signature == observed),
        None,
    )
    return {"scene_profile": profile}


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


def _most_frequent_color_crop(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: aggregate all cells of the globally most frequent color."""
    ranked = _ranked_colors(grid)
    if not ranked:
        raise ValueError("grid has no non-zero color")
    color = ranked[0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    return _crop_cells(grid, cells)


def _largest_component_of_most_frequent_color(
    grid: list[list[int]],
) -> list[list[int]]:
    """Wrong rule: choose the largest piece of the aggregate top color."""
    ranked = _ranked_colors(grid)
    if not ranked:
        raise ValueError("grid has no non-zero color")
    groups = _color_groups(grid)[ranked[0]]
    cells = max(groups, key=lambda group: (len(group), -min(group)[0], -min(group)[1]))
    return _crop_cells(grid, cells)


def _second_color_when_top_disconnected(
    grid: list[list[int]],
) -> list[list[int]]:
    """Wrong rule: fall back to the second-ranked color when top is split."""
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


def _largest_single_component_color(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: ignore every color occurring in multiple components."""
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


def _split_distractor_witness(grid: list[list[int]]) -> bool:
    """A split non-target color dominates only after aggregating its pieces."""
    if _grid_errors(grid):
        return False
    largest = _largest_component_record(grid)
    if largest is None:
        return False
    target_color, _, largest_size = largest
    structural = any(
        color != target_color
        and len(groups) >= 2
        and all(len(group) < largest_size for group in groups)
        and sum(len(group) for group in groups) > largest_size
        for color, groups in _color_groups(grid).items()
    )
    if not structural:
        return False
    truth = rule_mirror(grid)
    return (
        _most_frequent_color_crop(grid) != truth
        and _largest_component_of_most_frequent_color(grid) != truth
    )


def _split_target_witness(grid: list[list[int]]) -> bool:
    """The target color is top-ranked but split, and another color is split."""
    if _grid_errors(grid):
        return False
    largest = _largest_component_record(grid)
    if largest is None:
        return False
    target_color, _, largest_size = largest
    groups = _color_groups(grid)
    ranked = _ranked_colors(grid)
    if not ranked or ranked[0] != target_color or len(groups[target_color]) < 2:
        return False
    if not any(
        color != target_color
        and len(parts) >= 2
        and all(len(part) < largest_size for part in parts)
        for color, parts in groups.items()
    ):
        return False
    truth = rule_mirror(grid)
    return (
        _most_frequent_color_crop(grid) != truth
        and _second_color_when_top_disconnected(grid) != truth
        and _largest_single_component_color(grid) != truth
    )


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
    "split_distractor": _split_distractor_witness,
    "split_target": _split_target_witness,
}
WITNESS_RIVALS = {
    "split_distractor": [
        "most_frequent_color",
        "largest_component_of_most_frequent_color",
    ],
    "split_target": [
        "most_frequent_color",
        "second_color_when_top_disconnected",
        "largest_single_component_color",
    ],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a universal induction proof."""
    query_input = query["input"]
    query_output = query.get("output")
    if query_output is None:
        query_output = rule_mirror(query_input)
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_input) != query_output:
                reasons.append(
                    f"declared rival fits demonstrations but changes query: {name}"
                )
    return reasons
