"""Semantic input generator for ARC task ``ad8f72a318b2``.

A unary blue selector chooses one of four 4x4 monochrome library panels.  A
second control chooses one of five geometric transforms and a third control is
the output color.  The selected panel is crop-normalized, transformed, and
recolored.  The synchronized Racket program remains the label authority.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ad8f72a318b2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5d4b4a902077"

SUMMARY = (
    "Read a unary blue selector from row 0 columns 0..3, transform code 1..5 "
    "from column 5, and target color from column 7. Select one of four 4x4 "
    "monochrome panels, crop its nonzero support, apply identity / clockwise / "
    "180 / counter-clockwise / left-right reflection, and recolor the result."
)

INVARIANTS = [
    "the input is exactly 11x9 with a blank row 1, blank row 6, and blank separator column 4",
    "row 0 columns 0..3 are a unary prefix of 1s selecting panel 1..4",
    "row 0 column 5 is transform code 1..5 and column 7 is target color 2..9",
    "four 4x4 panels begin at (2,0), (2,5), (7,0), and (7,5)",
    "each panel is a nonempty 4-connected monochrome shape and panel colors are distinct",
    "the selected support is cropped before transformation and recoloring",
]

TARGET_RELATIONS = ("absent", "selected", "unselected")
AXES = {
    "index": {
        "type": "int",
        "default": "deterministic curriculum",
        "valid": "1..4",
    },
    "transform": {
        "type": "int",
        "default": "deterministic curriculum",
        "valid": "1..5",
    },
    "target_relation": {
        "type": "str",
        "default": "deterministic curriculum",
        "valid": "|".join(TARGET_RELATIONS),
    },
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5

# The coprime cycles enumerate every 4 x 5 x 3 control combination once.  Any
# five consecutive demonstrations cover all panel indices, all transform codes,
# and all target-color relations; the next query repeats the first transform.
LESSON_SCHEDULE_PERIOD = 60
_PROFILE_ROWS = tuple(
    (
        f"panel_{(offset % 4) + 1}_transform_{(offset % 5) + 1}_target_{TARGET_RELATIONS[offset % 3]}",
        (offset % 4) + 1,
        (offset % 5) + 1,
        TARGET_RELATIONS[offset % 3],
    )
    for offset in range(LESSON_SCHEDULE_PERIOD)
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_CONTROLS = {row[1:]: row[0] for row in _PROFILE_ROWS}

_POSITIONS = ((2, 0), (2, 5), (7, 0), (7, 5))
def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic profile for a lesson position."""
    del seed
    _band(difficulty)
    return SCENE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _normalize_cells(
    cells: Sequence[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _cells_to_mask(cells: Sequence[tuple[int, int]]) -> list[list[int]]:
    support = _normalize_cells(cells)
    if not support:
        return [[0]]
    height = max(row for row, _ in support) + 1
    width = max(col for _, col in support) + 1
    mask = full_grid(height, width, 0)
    for row, col in support:
        mask[row][col] = 1
    return mask


def _mask_support(mask: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return _normalize_cells(
        [
            (row, col)
            for row, values in enumerate(mask)
            for col, value in enumerate(values)
            if value != 0
        ]
    )


def _rotate_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _transform_mask(mask: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    grid = [list(row) for row in mask]
    transforms = {
        1: lambda value: value,
        2: _rotate_cw,
        3: _rotate_180,
        4: _rotate_ccw,
        5: _flip_lr,
    }
    if code not in transforms:
        raise ValueError(f"transform code must be 1..5, got {code!r}")
    return transforms[code](grid)


def _transform_support(
    cells: Sequence[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    return _mask_support(_transform_mask(_cells_to_mask(cells), code))


def _dihedral_signatures(
    cells: Sequence[tuple[int, int]],
) -> set[tuple[tuple[int, int], ...]]:
    mask = _cells_to_mask(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    rotated = mask
    for _ in range(4):
        variants.add(_mask_support(rotated))
        variants.add(_mask_support(_flip_lr(rotated)))
        rotated = _rotate_cw(rotated)
    return variants


def _dihedral_key(
    cells: Sequence[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return min(_dihedral_signatures(cells))


def _all_transforms_distinct(cells: Sequence[tuple[int, int]]) -> bool:
    return len({_transform_support(cells, code) for code in range(1, 6)}) == 5


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    support = set(cells)
    if not support:
        return False
    start = next(iter(support))
    seen = {start}
    frontier = [start]
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + dr, col + dc)
            if neighbor in support and neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return len(seen) == len(support)


@lru_cache(maxsize=None)
def _shape_pool(band: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate reusable D4-equivalence classes once per difficulty band.

    The previous rejection sampler could spend thousands of attempts finding
    four asymmetric, pairwise-distinct shapes for every generated grid.  The
    admissible universe is only the 4x4 board, so exhaustive enumeration is
    both cheaper and complete.  Returning canonical representatives also
    makes the pool stable across Python runs.
    """
    area_bounds = {
        "easy": (4, 5),
        "medium": (4, 6),
        "hard": (5, 7),
    }
    if band not in area_bounds:
        raise ValueError(f"unknown difficulty band: {band!r}")
    minimum, maximum = area_bounds[band]
    board = tuple((row, col) for row in range(4) for col in range(4))
    representatives: set[tuple[tuple[int, int], ...]] = set()
    for area in range(minimum, maximum + 1):
        for cells in combinations(board, area):
            if not _connected(cells):
                continue
            support = _normalize_cells(cells)
            if not _all_transforms_distinct(support):
                continue
            representatives.add(_dihedral_key(support))
    pool = tuple(sorted(representatives))
    if len(pool) < 4:
        raise RuntimeError(
            f"difficulty {band!r} has only {len(pool)} admissible shape classes"
        )
    return pool


def _shape_library(rng, band: str) -> list[tuple[tuple[int, int], ...]]:
    keys = rng.sample(_shape_pool(band), 4)
    return [rng.choice(sorted(_dihedral_signatures(key))) for key in keys]


def _paint(
    grid: list[list[int]],
    top: int,
    left: int,
    cells: Sequence[tuple[int, int]],
    color: int,
) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["cells must be literal ARC integers 0..9"]
    return []


def _panel_cells(
    grid: Sequence[Sequence[int]], top: int, left: int
) -> tuple[tuple[int, int], ...]:
    return _normalize_cells(
        [
            (row - top, col - left)
            for row in range(top, top + 4)
            for col in range(left, left + 4)
            if grid[row][col] != 0
        ]
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if (height, width) != (11, 9):
        return {"errors": [f"expected 11x9 grid, got {height}x{width}"]}

    selector = tuple(grid[0][:4])
    if any(value not in (0, 1) for value in selector):
        errors.append("selector cells must be 0 or 1")
    index = sum(value == 1 for value in selector)
    if index not in range(1, 5):
        errors.append(f"selector must contain 1..4 blue cells, got {index}")
    elif selector != (1,) * index + (0,) * (4 - index):
        errors.append("selector must be a left-aligned unary prefix")

    transform = grid[0][5]
    target = grid[0][7]
    if transform not in range(1, 6):
        errors.append(f"transform code must be 1..5, got {transform!r}")
    if target not in range(2, 10):
        errors.append(f"target color must be 2..9, got {target!r}")

    allowed_nonzero = {(0, col) for col in (0, 1, 2, 3, 5, 7)}
    for top, left in _POSITIONS:
        allowed_nonzero.update(
            (row, col)
            for row in range(top, top + 4)
            for col in range(left, left + 4)
        )
    stray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in allowed_nonzero
    ]
    if stray:
        errors.append(f"nonzero cells outside controls/panels: {stray[:4]}")

    panels: list[dict[str, Any]] = []
    panel_colors: list[int | None] = []
    for panel_number, (top, left) in enumerate(_POSITIONS, start=1):
        cells = _panel_cells(grid, top, left)
        colors = {
            grid[row][col]
            for row in range(top, top + 4)
            for col in range(left, left + 4)
            if grid[row][col] != 0
        }
        color = next(iter(colors)) if len(colors) == 1 else None
        if not cells:
            errors.append(f"panel {panel_number} is empty")
        if len(colors) != 1:
            errors.append(f"panel {panel_number} must be monochrome")
        if cells and not _connected(cells):
            errors.append(f"panel {panel_number} must be 4-connected")
        if cells and not 4 <= len(cells) <= 7:
            errors.append(
                f"panel {panel_number} must contain 4..7 cells, got {len(cells)}"
            )
        if color == 1:
            errors.append(f"panel {panel_number} may not use selector color 1")
        panels.append({"cells": cells, "color": color})
        panel_colors.append(color)

    realized_colors = [color for color in panel_colors if color is not None]
    if len(set(realized_colors)) != len(realized_colors):
        errors.append("panel colors must be pairwise distinct")

    target_relation: str | None = None
    if index in range(1, 5) and len(realized_colors) == 4 and target in range(2, 10):
        selected_color = panel_colors[index - 1]
        if target == selected_color:
            target_relation = "selected"
        elif target in panel_colors:
            target_relation = "unselected"
        else:
            target_relation = "absent"

    profile = _PROFILE_BY_CONTROLS.get((index, transform, target_relation))
    return {
        "errors": errors,
        "index": index,
        "transform": transform,
        "target": target,
        "target_relation": target_relation,
        "panels": panels,
        "panel_colors": panel_colors,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact advertised control from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "index": analysis["index"],
        "transform": analysis["transform"],
        "target_relation": analysis["target_relation"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or ambiguous layouts."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    realized = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and realized.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {realized.get(name)!r}"
            )
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    scheduled_index, scheduled_transform, scheduled_relation = _PROFILE_BY_NAME[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    index_bounds = (
        (1, 4)
        if overrides.get("index") is not None
        else (scheduled_index, scheduled_index)
    )
    transform_bounds = (
        (1, 5)
        if overrides.get("transform") is not None
        else (scheduled_transform, scheduled_transform)
    )
    relation_choices = (
        TARGET_RELATIONS
        if overrides.get("target_relation") is not None
        else (scheduled_relation,)
    )
    index = ctx.draw_int("index", *index_bounds)
    transform = ctx.draw_int("transform", *transform_bounds)
    target_relation = ctx.draw_choice("target_relation", relation_choices)

    rng = ctx.draw_rng("library")
    shapes = _shape_library(rng, band)
    panel_colors = rng.sample(list(range(2, 10)), 4)
    if target_relation == "selected":
        target = panel_colors[index - 1]
    elif target_relation == "unselected":
        target = rng.choice(
            [color for offset, color in enumerate(panel_colors) if offset != index - 1]
        )
    elif target_relation == "absent":
        target = rng.choice(
            [color for color in range(2, 10) if color not in panel_colors]
        )
    else:  # guarded by draw_choice, retained for defensive clarity
        raise ValueError(f"unknown target_relation: {target_relation!r}")

    grid = full_grid(11, 9, 0)
    for col in range(index):
        grid[0][col] = 1
    grid[0][5] = transform
    grid[0][7] = target
    for (top, left), cells, color in zip(_POSITIONS, shapes, panel_colors):
        _paint(grid, top, left, cells, color)
    return grid


def _selected_support(analysis: dict[str, Any], index: int) -> tuple[tuple[int, int], ...]:
    return analysis["panels"][index - 1]["cells"]


def _output_from_analysis(
    analysis: dict[str, Any],
    *,
    index: int | None = None,
    transform: int | None = None,
    preserve_source_color: bool = False,
) -> list[list[int]]:
    selected_index = analysis["index"] if index is None else index
    selected_transform = analysis["transform"] if transform is None else transform
    support = _selected_support(analysis, selected_index)
    mask = _transform_mask(_cells_to_mask(support), selected_transform)
    output_color = (
        analysis["panel_colors"][selected_index - 1]
        if preserve_source_color
        else analysis["target"]
    )
    return [
        [output_color if value else 0 for value in row]
        for row in mask
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; the synchronized Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _output_from_analysis(analysis)


def strict_canonical_like(grid) -> list[str]:
    """Require a lawful, canonical-scale, shortcut-resistant instance."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    supports = [panel["cells"] for panel in analysis["panels"]]
    if len({_dihedral_key(cells) for cells in supports}) != 4:
        errors.append("the four panel supports must be pairwise dihedrally distinct")
    selected = supports[analysis["index"] - 1]
    if (
        analysis["transform"] != 1
        and _transform_support(selected, analysis["transform"])
        == _transform_support(selected, 1)
    ):
        errors.append("the selected shape hides the requested non-identity transform")
    output = rule_mirror(grid)
    if not output or not output[0] or not any(value for row in output for value in row):
        errors.append("the transformed crop must be nonempty")
    return errors


def _rival_selector_mapping(mapping: dict[int, int]):
    def rival(grid):
        analysis = _analysis(grid)
        if analysis["errors"]:
            return [list(row) for row in grid]
        chosen = mapping.get(analysis["index"], analysis["index"])
        return _output_from_analysis(analysis, index=chosen)

    return rival


def _rival_transform_mapping(mapping: dict[int, int]):
    def rival(grid):
        analysis = _analysis(grid)
        if analysis["errors"]:
            return [list(row) for row in grid]
        chosen = mapping.get(analysis["transform"], analysis["transform"])
        return _output_from_analysis(analysis, transform=chosen)

    return rival


def _rival_preserve_panel_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _output_from_analysis(analysis, preserve_source_color=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "selector_shifted": _rival_selector_mapping({1: 2, 2: 3, 3: 4, 4: 1}),
    "selector_reversed": _rival_selector_mapping({1: 4, 2: 3, 3: 2, 4: 1}),
    "ignore_transform": _rival_transform_mapping({2: 1, 3: 1, 4: 1, 5: 1}),
    "transform_code_shifted": _rival_transform_mapping(
        {1: 2, 2: 3, 3: 4, 4: 5, 5: 1}
    ),
    "clockwise_counterclockwise_swapped": _rival_transform_mapping({2: 4, 4: 2}),
    "half_turn_reflection_swapped": _rival_transform_mapping({3: 5, 5: 3}),
    "preserve_selected_panel_color": _rival_preserve_panel_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Any]] = {}


def _profile_witness(
    *,
    index: int | None = None,
    transform: int | None = None,
    target_relation: str | None = None,
):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        if analysis["errors"]:
            return False
        return (
            (index is None or analysis["index"] == index)
            and (transform is None or analysis["transform"] == transform)
            and (
                target_relation is None
                or analysis["target_relation"] == target_relation
            )
        )

    return witness


SEMANTIC_WITNESSES = {
    **{
        f"panel_index_{index}": _profile_witness(index=index)
        for index in range(1, 5)
    },
    **{
        f"transform_code_{transform}": _profile_witness(transform=transform)
        for transform in range(1, 6)
    },
    "target_relation_absent": _profile_witness(target_relation="absent"),
    "target_relation_unselected": _profile_witness(target_relation="unselected"),
    "recolor_visible": lambda grid: _rival_preserve_panel_color(grid)
    != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "panel_index_1": ["selector_shifted", "selector_reversed"],
    "panel_index_2": ["selector_shifted", "selector_reversed"],
    "panel_index_3": ["selector_shifted", "selector_reversed"],
    "panel_index_4": ["selector_shifted", "selector_reversed"],
    "transform_code_1": ["transform_code_shifted"],
    "transform_code_2": [
        "ignore_transform",
        "transform_code_shifted",
        "clockwise_counterclockwise_swapped",
    ],
    "transform_code_3": [
        "ignore_transform",
        "transform_code_shifted",
        "half_turn_reflection_swapped",
    ],
    "transform_code_4": [
        "ignore_transform",
        "transform_code_shifted",
        "clockwise_counterclockwise_swapped",
    ],
    "transform_code_5": [
        "ignore_transform",
        "transform_code_shifted",
        "half_turn_reflection_swapped",
    ],
    "target_relation_absent": ["preserve_selected_panel_color"],
    "target_relation_unselected": ["preserve_selected_panel_color"],
    "recolor_visible": ["preserve_selected_panel_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject production lessons that leave a declared shortcut viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    indices: set[int] = set()
    transforms: set[int] = set()
    relations: set[str] = set()
    for position, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {position} must contain input and output")
            continue
        analysis = _analysis(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {position} is invalid: {'; '.join(analysis['errors'])}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {position} disagrees with the canonical pipeline")
        indices.add(analysis["index"])
        transforms.add(analysis["transform"])
        relations.add(analysis["target_relation"])

    query_analysis = _analysis(query["input"])
    if query_analysis["errors"]:
        reasons.append("query is invalid: " + "; ".join(query_analysis["errors"]))
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the canonical pipeline")

    # Five examples from any six-example production lesson retain at least
    # three selector values and four transform codes.  Requiring complete
    # coverage made an otherwise identifiable lesson depend on which pair was
    # chosen as the query.  The rival checks below provide the stronger,
    # behavior-level guarantee.
    if len(indices) < 3:
        reasons.append("demonstrations must cover at least three panel indices")
    if len(transforms) < 4:
        reasons.append("demonstrations must cover at least four transform codes")
    if relations != set(TARGET_RELATIONS):
        reasons.append("demonstrations must cover all target-color relations")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
