"""Generator for arc_additional_puzzles_21_set22_bundle:H148 -- apply A->B transform to C.

Rule: 3 panels separated by all-9 columns. The first pair A->B reveals a
dihedral transform (1=identity, 2=cw, 3=180, 4=ccw, 5=flip-lr, 6=flip-ud)
-- the first code k with apply(crop(A),k)==crop(B) -- and the output is
that transform applied to crop(C).

This generator draws an ASYMMETRIC color pattern A (so exactly one code
maps A->B), B = transform(A), and an independent pattern C, separated by
single all-9 columns.

Combinatorial axes: the transform, the A and C patterns, their sizes,
vertical offsets, and colors.
Degenerates: no_separators, no_panel_a, identical_a_b.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4c17a205be08"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e3805c81bf19"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 5x17 zero-background grid has three 5x5 panels separated by full "
    "color-9 columns. Crop A and B, infer the unique transform mapping A to "
    "B from identity/90-degree rotations/180/left-right/up-down flips, then "
    "apply it to cropped panel C. Sparse canonical-scale motifs, colors, "
    "positions, component profiles, and all six transform branches vary."
)

INVARIANTS = [
    "input is 5x17 with full color-9 separator columns 5 and 11",
    "cropped A uses exactly two colors and uniquely identifies one legal transform to B",
    "cropped C uses one or two colors disjoint from A/B",
    "ordinary A and C have six distinct images under the rule's six transforms",
]

ALL_TRANSFORMS = (
    "identity",
    "rotate_cw",
    "rotate_180",
    "rotate_ccw",
    "flip_lr",
    "flip_ud",
)
SCHEDULE_PROFILES = ALL_TRANSFORMS
_OBSERVED_CANONICAL_FAMILY = (
    "rotate_cw",
    "rotate_180",
    "rotate_ccw",
    "flip_lr",
)

AXES = {
    "transform": {
        "type": "str",
        "default": "six-example cyclic schedule",
        "valid": "|".join(ALL_TRANSFORMS),
    },
    "exemplar_cells": {
        "type": "int",
        "default": "difficulty-aware 4..6",
        "valid": "4..6",
    },
    "query_cells": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PANEL_SIZE = 5
_GRID_WIDTH = 17
_SEPARATOR_COLOR = 9
_MOTIF_COLORS = tuple(range(1, 9))
_PATTERN_DIMS = ((2, 2), (2, 3), (3, 2), (3, 3))


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _transform(grid, name: str):
    """Return a fresh crop under one of the selected rule's six transforms."""
    if name == "identity":
        return [list(row) for row in grid]
    if name == "rotate_cw":
        return [list(row) for row in zip(*grid[::-1])]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_ccw":
        return [list(row) for row in zip(*grid)][::-1]
    if name == "flip_lr":
        return [list(reversed(row)) for row in grid]
    if name == "flip_ud":
        return [list(row) for row in reversed(grid)]
    raise ValueError(f"unknown transform: {name!r}")


def _grid_errors(grid) -> list[str]:
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
                return [f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"]
    return []


def _panels(grid):
    return (
        [list(row[0:5]) for row in grid],
        [list(row[6:11]) for row in grid],
        [list(row[12:17]) for row in grid],
    )


def _write_panel(grid, index: int, panel) -> None:
    left = (0, 6, 12)[index]
    for r in range(_PANEL_SIZE):
        for c in range(_PANEL_SIZE):
            grid[r][left + c] = panel[r][c]


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in panel[r0:r1 + 1]]


def _crop_colors(crop):
    return {value for row in crop for value in row if value != 0}


def _cell_count(crop) -> int:
    return sum(value != 0 for row in crop for value in row)


def _support_components(crop) -> int:
    remaining = {
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _matching_transforms(crop_a, crop_b):
    target = _freeze(crop_b)
    return [
        name
        for name in ALL_TRANSFORMS
        if _freeze(_transform(crop_a, name)) == target
    ]


def _infer_transform(grid) -> str:
    panel_a, panel_b, _ = _panels(grid)
    matches = _matching_transforms(_crop(panel_a), _crop(panel_b))
    if not matches:
        raise ValueError("no selected transform maps cropped panel A to cropped panel B")
    # Mirrors the canonical Racket rule's first-match priority exactly.
    return matches[0]


def rule_mirror(grid):
    """Pure Python mirror for tests and semantic contracts; Racket is authority."""
    _, _, panel_c = _panels(grid)
    return _transform(_crop(panel_c), _infer_transform(grid))


_apply_rule = rule_mirror


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical three-panel crop-transform input grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) != (_PANEL_SIZE, _GRID_WIDTH):
        return [
            f"expected canonical 5x17 geometry, got {len(grid)}x{len(grid[0])}"
        ]

    for column in (5, 11):
        bad_rows = [r for r in range(_PANEL_SIZE) if grid[r][column] != _SEPARATOR_COLOR]
        if bad_rows:
            errors.append(
                f"separator column {column} must be full color-{_SEPARATOR_COLOR}; "
                f"bad rows {bad_rows[:3]}"
            )

    panel_a, panel_b, panel_c = _panels(grid)
    for label, panel in zip("ABC", (panel_a, panel_b, panel_c)):
        if any(value == _SEPARATOR_COLOR for row in panel for value in row):
            errors.append(f"panel {label} contains reserved separator color {_SEPARATOR_COLOR}")
        if not _crop(panel):
            errors.append(f"panel {label} must contain a nonzero crop")

    if errors:
        return errors

    crop_a, crop_b, crop_c = map(_crop, (panel_a, panel_b, panel_c))
    colors_a = _crop_colors(crop_a)
    colors_b = _crop_colors(crop_b)
    colors_c = _crop_colors(crop_c)

    if len(colors_a) != 2:
        errors.append(f"cropped panel A must use exactly two colors, found {sorted(colors_a)}")
    if colors_b != colors_a:
        errors.append(
            f"cropped panels A and B must preserve the same colors, got "
            f"{sorted(colors_a)} and {sorted(colors_b)}"
        )
    if not 1 <= len(colors_c) <= 2:
        errors.append(f"cropped panel C must use one or two colors, found {sorted(colors_c)}")
    if colors_c & colors_a:
        errors.append("cropped panel C colors must be disjoint from panel A/B colors")

    matches = _matching_transforms(crop_a, crop_b)
    if len(matches) != 1:
        errors.append(f"A->B must identify exactly one transform, got {matches}")
    return errors


def _nonbackground_components(grid) -> int:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def strict_canonical_like(grid) -> list[str]:
    """Accept the morphology shared by every canonical row and ordinary draw."""
    errors = self_check(grid)
    if errors:
        return errors

    crop_a, crop_b, crop_c = map(_crop, _panels(grid))
    palette = {value for row in grid for value in row}
    if len(palette) not in {5, 6}:
        errors.append(f"canonical palette has five or six colors, found {sorted(palette)}")
    if not 4 <= _cell_count(crop_a) <= 6:
        errors.append(f"cropped panel A must contain 4..6 cells, found {_cell_count(crop_a)}")
    if _cell_count(crop_b) != _cell_count(crop_a):
        errors.append("cropped panels A and B must have the same cell count")
    if not 3 <= _cell_count(crop_c) <= 6:
        errors.append(f"cropped panel C must contain 3..6 cells, found {_cell_count(crop_c)}")
    for label, crop in zip("ABC", (crop_a, crop_b, crop_c)):
        if not (2 <= len(crop) <= 3 and 2 <= len(crop[0]) <= 3):
            errors.append(
                f"cropped panel {label} must be canonical-scale 2..3 by 2..3, "
                f"got {len(crop)}x{len(crop[0])}"
            )
    components = _nonbackground_components(grid)
    if not 5 <= components <= 7:
        errors.append(f"canonical inputs contain 5..7 non-background components, found {components}")
    return errors


def _teaching_reasons(grid) -> list[str]:
    reasons = strict_canonical_like(grid)
    if reasons:
        return reasons
    crop_a, _, crop_c = map(_crop, _panels(grid))
    if len({_freeze(_transform(crop_a, name)) for name in ALL_TRANSFORMS}) != 6:
        reasons.append("cropped panel A must have six distinct legal transform images")
    if len({_freeze(_transform(crop_c, name)) for name in ALL_TRANSFORMS}) != 6:
        reasons.append("cropped panel C must separate all six legal transform outputs")
    return reasons


def _touches_crop_edges(support, height: int, width: int) -> bool:
    rows = {r for r, _ in support}
    cols = {c for _, c in support}
    return rows == rows | {0, height - 1} and cols == cols | {0, width - 1} \
        and 0 in rows and height - 1 in rows and 0 in cols and width - 1 in cols


@lru_cache(maxsize=None)
def _candidate_patterns(cell_count: int, color_count: int, component_count: int):
    """Enumerate tiny crop patterns satisfying the decisive teaching contract."""
    patterns = []
    labels = tuple(range(1, color_count + 1))
    for height, width in _PATTERN_DIMS:
        if cell_count > height * width:
            continue
        cells = tuple((r, c) for r in range(height) for c in range(width))
        for support_tuple in combinations(cells, cell_count):
            support = frozenset(support_tuple)
            if not _touches_crop_edges(support, height, width):
                continue
            support_grid = full_grid(height, width, 0)
            for r, c in support:
                support_grid[r][c] = 1
            if _support_components(support_grid) != component_count:
                continue
            for assignment in product(labels, repeat=cell_count):
                if set(assignment) != set(labels):
                    continue
                pattern = full_grid(height, width, 0)
                for (r, c), value in zip(support_tuple, assignment):
                    pattern[r][c] = value
                if len({_freeze(_transform(pattern, name)) for name in ALL_TRANSFORMS}) == 6:
                    patterns.append(_freeze(pattern))
    return tuple(patterns)


def _choose_pattern(rng, *, cells: int, components: int, preferred_colors: int):
    color_order = (preferred_colors, 3 - preferred_colors)
    for color_count in color_order:
        candidates = _candidate_patterns(cells, color_count, components)
        if candidates:
            frozen = rng.choice(candidates)
            return [list(row) for row in frozen], color_count
    raise RuntimeError(
        f"no decisive crop pattern for cells={cells}, components={components}"
    )


def _recolor(pattern, colors):
    return [
        [0 if value == 0 else colors[value - 1] for value in row]
        for row in pattern
    ]


def _place_crop(panel, crop, top: int, left: int) -> None:
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            panel[top + r][left + c] = value


def _horizontal_offsets(panel_index: int, width: int):
    if panel_index == 0:  # keep a zero moat before the right separator
        return tuple(range(0, 5 - width))
    if panel_index == 1:  # keep a zero moat on both separator-facing sides
        return tuple(range(1, 5 - width))
    return tuple(range(1, 6 - width))  # keep a zero moat after the left separator


def _paint_panel(rng, crop, panel_index: int):
    height, width = len(crop), len(crop[0])
    panel = full_grid(_PANEL_SIZE, _PANEL_SIZE, 0)
    top = rng.randrange(0, _PANEL_SIZE - height + 1)
    left_options = _horizontal_offsets(panel_index, width)
    if not left_options:
        raise RuntimeError(f"no legal panel offset for panel={panel_index}, width={width}")
    left = rng.choice(left_options)
    _place_crop(panel, crop, top, left)
    return panel


def schedule_profile(seed, sample_index, difficulty=None):
    """Every six consecutive examples contain every legal transform once."""
    del difficulty
    return ALL_TRANSFORMS[(int(seed) + int(sample_index)) % len(ALL_TRANSFORMS)]


def _cell_bounds(label: str, difficulty):
    if label == "exemplar_cells":
        if difficulty == "easy":
            return 4, 4
        if difficulty == "hard":
            return 5, 6
        return 4, 5
    if difficulty == "easy":
        return 3, 4
    if difficulty == "hard":
        return 4, 6
    return 3, 5


def _draw_axis_int(ctx, overrides, label: str, full_bounds: tuple[int, int], difficulty):
    if label in overrides:
        return ctx.draw_int(label, *full_bounds)
    return ctx.draw_int(label, *_cell_bounds(label, difficulty))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic canonical-profile crop-transform input."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "transform" in overrides:
        transform = ctx.draw_choice("transform", ALL_TRANSFORMS)
    else:
        transform = ctx.draw_choice("transform", (scheduled,))
    exemplar_cells = _draw_axis_int(ctx, overrides, "exemplar_cells", (4, 6), difficulty)
    query_cells = _draw_axis_int(ctx, overrides, "query_cells", (3, 6), difficulty)

    # Alternating (A-components, C-components) gives total component counts
    # 6 and 7: 2 separators + 2*A + C.  This matches the canonical median 6.5.
    if int(sample_index) % 2 == 0:
        exemplar_components, query_components = 1, 2
    else:
        exemplar_components, query_components = 2, 1

    exemplar_rng = ctx.draw_rng("exemplar_pattern")
    query_rng = ctx.draw_rng("query_pattern")
    palette_rng = ctx.draw_rng("palette")
    layout_rng = ctx.draw_rng("layout")

    exemplar_labels, exemplar_color_count = _choose_pattern(
        exemplar_rng,
        cells=exemplar_cells,
        components=exemplar_components,
        preferred_colors=2,
    )
    if exemplar_color_count != 2:
        raise RuntimeError("exemplar pattern must use exactly two label colors")

    preferred_query_colors = 1 if (int(seed) + int(sample_index)) % 2 == 0 else 2
    query_labels, query_color_count = _choose_pattern(
        query_rng,
        cells=query_cells,
        components=query_components,
        preferred_colors=preferred_query_colors,
    )

    palette = palette_rng.sample(list(_MOTIF_COLORS), 2 + query_color_count)
    exemplar_crop = _recolor(exemplar_labels, palette[:2])
    query_crop = _recolor(query_labels, palette[2:])
    transformed_crop = _transform(exemplar_crop, transform)

    panel_a = _paint_panel(layout_rng, exemplar_crop, 0)
    panel_b = _paint_panel(layout_rng, transformed_crop, 1)
    panel_c = _paint_panel(layout_rng, query_crop, 2)

    grid = full_grid(_PANEL_SIZE, _GRID_WIDTH, 0)
    for r in range(_PANEL_SIZE):
        grid[r][5] = _SEPARATOR_COLOR
        grid[r][11] = _SEPARATOR_COLOR
    _write_panel(grid, 0, panel_a)
    _write_panel(grid, 1, panel_b)
    _write_panel(grid, 2, panel_c)
    return grid


def observe_overrides(grid):
    panel_a, _, panel_c = _panels(grid)
    crop_a, crop_c = _crop(panel_a), _crop(panel_c)
    return {
        "transform": _infer_transform(grid),
        "exemplar_cells": _cell_count(crop_a),
        "query_cells": _cell_count(crop_c),
    }


def _rival_fixed(transform: str):
    def rival(grid):
        return _transform(_crop(_panels(grid)[2]), transform)
    return rival


def _rival_copy_panel_b(grid):
    return _crop(_panels(grid)[1])


def _rival_observed_transform_family_only(grid):
    panel_a, panel_b, panel_c = _panels(grid)
    crop_a, crop_b, crop_c = map(_crop, (panel_a, panel_b, panel_c))
    target = _freeze(crop_b)
    for transform in _OBSERVED_CANONICAL_FAMILY:
        if _freeze(_transform(crop_a, transform)) == target:
            return _transform(crop_c, transform)
    # Canonical demonstrations never require this branch.  A solver that only
    # learned their four observed commands defaults to rotate-CW elsewhere.
    return _transform(crop_c, "rotate_cw")


def _transform_witness(expected: str):
    def witness(grid):
        return not _teaching_reasons(grid) and _infer_transform(grid) == expected
    return witness


SEMANTIC_RIVALS = {
    f"fixed_{transform}": _rival_fixed(transform)
    for transform in ALL_TRANSFORMS
}
SEMANTIC_RIVALS.update({
    "copy_panel_b": _rival_copy_panel_b,
    "observed_transform_family_only": _rival_observed_transform_family_only,
})

SEMANTIC_WITNESSES = {
    f"transform_{transform}_unique": _transform_witness(transform)
    for transform in ALL_TRANSFORMS
}

WITNESS_RIVALS = {}
for transform in ALL_TRANSFORMS:
    witness_name = f"transform_{transform}_unique"
    rivals = [
        f"fixed_{other}"
        for other in ALL_TRANSFORMS
        if other != transform
    ]
    rivals.append("copy_panel_b")
    if transform not in _OBSERVED_CANONICAL_FAMILY:
        rivals.append("observed_transform_family_only")
    WITNESS_RIVALS[witness_name] = rivals

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "observed_transform_family_only": _rival_observed_transform_family_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a five-demo window that validates scenes and refutes all rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    profiles = set()
    survivors = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        teaching_errors = _teaching_reasons(grid)
        if teaching_errors:
            errors.append(f"demo {index} is outside the teaching grammar: {teaching_errors[0]}")
            continue
        authoritative = rule_mirror(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        profiles.add(_infer_transform(grid))
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    if len(profiles) < EXAMPLES_NEEDED:
        errors.append(
            f"demonstrations need {EXAMPLES_NEEDED} distinct transform branches, "
            f"found {sorted(profiles)}"
        )
    if not (profiles - set(_OBSERVED_CANONICAL_FAMILY)):
        errors.append("demonstrations do not expose a transform absent from canonical demos")

    query_grid = query["input"]
    query_errors = _teaching_reasons(query_grid)
    if query_errors:
        errors.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query_grid):
        errors.append("query output disagrees with the selected rule")

    if survivors:
        errors.append("demonstrations leave rival rule(s) alive: " + ", ".join(sorted(survivors)))
    return errors
