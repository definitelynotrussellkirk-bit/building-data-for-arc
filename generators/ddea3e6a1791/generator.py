"""Generator for ddea3e6a1791 — crop to the tight nonzero bounding box.

The canonical Racket rule crops to the minimum rectangle containing *every*
nonzero cell.  Ordinary lessons alternate canonical-profile monochrome motifs
with disconnected multicolour witnesses.  Thus a four-demonstration lesson,
and every four-of-five query rotation, refutes first/largest-component and
monochrome shortcuts while retaining strong support for the tiny canonicals.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ddea3e6a1791"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "debb1a8a129a"

SUMMARY = (
    "Crop the grid to the tight joint bounding rectangle of every nonzero cell, "
    "preserving colors, zero holes, and gaps between disconnected components. "
    "Two of every four scheduled inputs match canonical canvas/palette profiles; "
    "the alternating inputs contain two differently colored components."
)

INVARIANTS = [
    "background is color 0 and the crop is strictly smaller than the input",
    "the nonzero union has one or two 4-connected components",
    "one or two nonzero colors are preserved exactly",
    "the tight bbox is 2..3 rows by 2..4 columns and contains a zero hole",
    "every four consecutive draws contain two multicomponent multicolor witnesses",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled by profile", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "scheduled by profile", "valid": "5..10"},
    "bbox_h": {"type": "int", "default": "scheduled by profile", "valid": "2..3"},
    "bbox_w": {"type": "int", "default": "scheduled by profile", "valid": "2..4"},
    "n_components": {"type": "int", "default": "alternates 1 and 2", "valid": "1..2"},
    "n_distinct_colors": {"type": "int", "default": "alternates 1 and 2", "valid": "1..2"},
}

# Every Cartesian combination of the advertised ranges is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "canonical_4x6",
    "joint_witness_a",
    "canonical_5x5",
    "joint_witness_b",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

Grid = list[list[int]]
Cell = tuple[int, int]


def _validate_controls(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject coercible public controls instead of silently aliasing lessons."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool or a coercible value)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the four-slot profile; every length-four window has all slots."""
    _validate_controls(seed, sample_index, difficulty)
    return _PROFILE_NAMES[sample_index % len(_PROFILE_NAMES)]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{col_index}) is not an ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _nonzero_cells(grid: Grid) -> set[Cell]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int] | None:
    if not cells:
        return None
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: Grid) -> list[set[Cell]]:
    remaining = _nonzero_cells(grid)
    components: list[set[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for next_cell in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if next_cell in remaining:
                    remaining.remove(next_cell)
                    component.add(next_cell)
                    queue.append(next_cell)
        components.append(component)
    return components


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests and semantic competitor hooks."""
    cells = _nonzero_cells(grid)
    bounds = _bbox(cells)
    if bounds is None:
        return [[0]]
    row0, col0, row1, col1 = bounds
    return [list(row[col0 : col1 + 1]) for row in grid[row0 : row1 + 1]]


def observe_overrides(grid: Grid) -> dict[str, int]:
    cells = _nonzero_cells(grid)
    bounds = _bbox(cells)
    if bounds is None:
        bbox_h = bbox_w = 0
    else:
        row0, col0, row1, col1 = bounds
        bbox_h = row1 - row0 + 1
        bbox_w = col1 - col0 + 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "n_components": len(_components(grid)),
        "n_distinct_colors": len({value for row in grid for value in row if value != 0}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonicals and the declared sparse one/two-component grammar."""
    del difficulty, meta
    height, width, issues = _validate_grid(grid)
    if issues:
        return issues
    if not (4 <= height <= 10):
        issues.append(f"height {height} outside 4..10")
    if not (5 <= width <= 10):
        issues.append(f"width {width} outside 5..10")

    cells = _nonzero_cells(grid)
    if not cells:
        issues.append("at least one nonzero cell is required")
        return issues
    bounds = _bbox(cells)
    assert bounds is not None
    row0, col0, row1, col1 = bounds
    bbox_h, bbox_w = row1 - row0 + 1, col1 - col0 + 1
    if not (2 <= bbox_h <= 3):
        issues.append(f"bbox height {bbox_h} outside 2..3")
    if not (2 <= bbox_w <= 4):
        issues.append(f"bbox width {bbox_w} outside 2..4")
    if bbox_h >= height or bbox_w >= width:
        issues.append("crop must be strictly smaller than the input in both dimensions")
    if len(cells) >= bbox_h * bbox_w:
        issues.append("bbox must preserve at least one interior background cell")

    component_count = len(_components(grid))
    if not (1 <= component_count <= 2):
        issues.append(f"expected one or two nonzero components, found {component_count}")
    colors = {grid[row][col] for row, col in cells}
    if not (1 <= len(colors) <= 2):
        issues.append(f"expected one or two nonzero colors, found {len(colors)}")
    if len(cells) < 2:
        issues.append("at least two nonzero cells are required")
    return issues


_CANONICAL_PROFILES = {
    (4, 6, 2),
    (5, 5, 2),
    (5, 7, 2),
    (5, 6, 2),
}


def strict_canonical_like(grid) -> list[str]:
    """Empirical manifold shared by all four labelled canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical h/w/palette profiles")
    observed = observe_overrides(grid)
    if observed["n_components"] != 1:
        reasons.append("canonical inputs contain exactly one nonzero component")
    if observed["n_distinct_colors"] != 1:
        reasons.append("canonical inputs contain exactly one nonzero color")
    if (observed["bbox_h"], observed["bbox_w"]) not in {(2, 2), (2, 3)}:
        reasons.append("canonical bbox is 2x2 or 2x3")
    if sum(value != 0 for row in grid for value in row) not in {3, 4}:
        reasons.append("canonical motifs contain three or four nonzero cells")
    return reasons


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _largest_component_crop(grid: Grid) -> Grid:
    components = _components(grid)
    if not components:
        return [[0]]
    component = min(components, key=lambda cells: (-len(cells), min(cells)))
    bounds = _bbox(component)
    assert bounds is not None
    row0, col0, row1, col1 = bounds
    return [
        [grid[row][col] if (row, col) in component else 0 for col in range(col0, col1 + 1)]
        for row in range(row0, row1 + 1)
    ]


def _solid_bbox_fill(grid: Grid) -> Grid:
    crop = rule_mirror(grid)
    nonzero = [value for row in crop for value in row if value != 0]
    fill = min(nonzero) if nonzero else 0
    return [[value if value != 0 else fill for value in row] for row in crop]


def _monochrome_crop(grid: Grid) -> Grid:
    crop = rule_mirror(grid)
    nonzero = [value for row in crop for value in row if value != 0]
    color = min(nonzero) if nonzero else 0
    return [[color if value != 0 else 0 for value in row] for row in crop]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _identity,
    "largest_component_only": _largest_component_crop,
    "solid_bbox_fill": _solid_bbox_fill,
    "monochrome_crop": _monochrome_crop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These two actually fit every labelled canonical pair and are the dangerous
# shortcuts the ordinary witness schedule is specifically designed to break.
CANONICAL_SHORTCUTS = {
    "largest_component_only": _largest_component_crop,
    "monochrome_crop": _monochrome_crop,
}


def _valid_and(predicate: Callable[[Grid], bool], grid: Grid) -> bool:
    return not self_check(grid) and predicate(grid)


def _witness_visible_crop(grid: Grid) -> bool:
    return _valid_and(lambda value: rule_mirror(value) != _identity(value), grid)


def _witness_all_components(grid: Grid) -> bool:
    return _valid_and(
        lambda value: _largest_component_crop(value) != rule_mirror(value), grid
    )


def _witness_sparse_bbox(grid: Grid) -> bool:
    return _valid_and(lambda value: _solid_bbox_fill(value) != rule_mirror(value), grid)


def _witness_color_preservation(grid: Grid) -> bool:
    return _valid_and(lambda value: _monochrome_crop(value) != rule_mirror(value), grid)


SEMANTIC_WITNESSES = {
    "visible_crop_refutes_identity": _witness_visible_crop,
    "all_components_determine_bbox": _witness_all_components,
    "interior_background_is_preserved": _witness_sparse_bbox,
    "all_nonzero_colors_are_preserved": _witness_color_preservation,
}
WITNESS_RIVALS = {
    "visible_crop_refutes_identity": ["identity"],
    "all_components_determine_bbox": ["largest_component_only"],
    "interior_background_is_preserved": ["solid_bbox_fill"],
    "all_nonzero_colors_are_preserved": ["monochrome_crop"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that collectively falsify each named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_issues = self_check(query["input"])
        if query_issues:
            reasons.append(f"query input is invalid: {query_issues[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_grid = demo["input"]
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(input_grid)
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact nonzero bbox crop")
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(input_grid) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int, int, int, int]:
    slot = int(sample_index) % 4
    if slot == 0:
        return 4, 6, 2, 2, 1, 1
    if slot == 2:
        return 5, 5, 2, 3, 1, 1
    witness_profiles = {
        "easy": ((5, 6, 2, 3, 2, 2), (5, 7, 2, 4, 2, 2)),
        "medium": ((7, 8, 3, 4, 2, 2), (8, 9, 3, 4, 2, 2)),
        "hard": ((9, 10, 3, 4, 2, 2), (10, 10, 3, 4, 2, 2)),
    }
    first, second = witness_profiles.get(
        difficulty,
        ((6, 7, 3, 4, 2, 2), (7, 9, 3, 4, 2, 2)),
    )
    return first if slot == 1 else second


def _axis_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _local_components(
    bbox_h: int,
    bbox_w: int,
    count: int,
    variant: int,
) -> list[set[Cell]]:
    last_row, last_col = bbox_h - 1, bbox_w - 1
    if count == 1:
        orientation = variant % 4
        if orientation == 0:
            cells = {(0, col) for col in range(bbox_w)} | {
                (row, 0) for row in range(bbox_h)
            }
        elif orientation == 1:
            cells = {(0, col) for col in range(bbox_w)} | {
                (row, last_col) for row in range(bbox_h)
            }
        elif orientation == 2:
            cells = {(last_row, col) for col in range(bbox_w)} | {
                (row, 0) for row in range(bbox_h)
            }
        else:
            cells = {(last_row, col) for col in range(bbox_w)} | {
                (row, last_col) for row in range(bbox_h)
            }
        return [cells]

    if variant % 2 == 0:
        first, second = {(0, 0)}, {(last_row, last_col)}
        if bbox_w >= 3:
            first.add((0, 1))
        elif bbox_h >= 3:
            first.add((1, 0))
    else:
        first, second = {(0, last_col)}, {(last_row, 0)}
        if bbox_w >= 3:
            first.add((0, last_col - 1))
        elif bbox_h >= 3:
            first.add((1, last_col))
    return [first, second]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(sample_index, difficulty)
    height = _axis_int(ctx, overrides, "grid_h", defaults[0], 4, 10)
    width = _axis_int(ctx, overrides, "grid_w", defaults[1], 5, 10)
    bbox_h = _axis_int(ctx, overrides, "bbox_h", defaults[2], 2, 3)
    bbox_w = _axis_int(ctx, overrides, "bbox_w", defaults[3], 2, 4)
    n_components = _axis_int(ctx, overrides, "n_components", defaults[4], 1, 2)
    n_colors = _axis_int(ctx, overrides, "n_distinct_colors", defaults[5], 1, 2)

    # The advertised ranges make these inequalities unconditional, but retain
    # the explicit check so future range edits fail loudly rather than clip.
    if bbox_h >= height or bbox_w >= width:
        raise ValueError("bbox dimensions must be smaller than the grid")

    variant = int(sample_index) // 4 + int(sample_index) % 4
    components = _local_components(bbox_h, bbox_w, n_components, variant)
    cells = [cell for component in components for cell in sorted(component)]
    if len(cells) < n_colors:
        raise ValueError("n_distinct_colors exceeds available nonzero cells")

    palette = ctx.draw_distinct_colors("nonzero_palette", n=n_colors, exclude={0})
    content_rng = ctx.draw_rng("content")
    colors = list(palette)
    while len(colors) < len(cells):
        colors.append(palette[content_rng.randrange(len(palette))])
    content_rng.shuffle(colors)

    placement_rng = ctx.draw_rng("placement")
    row0 = placement_rng.randint(0, height - bbox_h)
    col0 = placement_rng.randint(0, width - bbox_w)
    grid = full_grid(height, width, 0)
    for (row, col), color in zip(cells, colors):
        grid[row0 + row][col0 + col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "n_components": n_components,
        "n_distinct_colors": n_colors,
    }
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_fixtures():
    """Named malformed/rule-hiding inputs that self_check must reject."""
    blank = full_grid(5, 6, 0)
    identity = full_grid(4, 5, 0)
    identity[0][0] = identity[-1][-1] = 2
    solid = full_grid(5, 6, 0)
    for row in range(1, 3):
        for col in range(2, 4):
            solid[row][col] = 4
    three = full_grid(5, 7, 0)
    for row, col in ((1, 1), (2, 3), (3, 5)):
        three[row][col] = 7
    return [
        ("no_nonzero_cells", blank),
        ("bbox_spans_input", identity),
        ("solid_bbox", solid),
        ("three_components", three),
    ]
