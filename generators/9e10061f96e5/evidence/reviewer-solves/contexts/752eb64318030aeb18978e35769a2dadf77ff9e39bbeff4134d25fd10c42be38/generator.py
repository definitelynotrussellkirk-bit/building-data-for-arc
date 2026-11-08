"""Generator for H118, the transform-equivalence matrix task.

Each input is a horizontal sequence of 2--4 monochrome shape panels separated
by one full-height zero column.  Panel colors are labels only.  The reference
rule crops and binarizes each panel, canonicalizes its shape under the eight D4
rotations/reflections, and emits an N x N relation matrix: diagonal 5,
off-diagonal 2 for D4-equivalent shapes, otherwise 0.

The sampler deliberately cycles through three counterexamples needed to teach
the rule rather than easier shortcuts:

* equivalent shapes in different orientations (refutes identity-only matching),
* a reflection-only equivalent pair (refutes rotation-only matching), and
* equal-cell-count shapes from different D4 classes (refutes size matching).

The curated bank contains every D4 class present in the canonical train/test
inputs and compact additional classes with 3--8 occupied cells.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9e10061f96e5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "788540441b76"

SUMMARY = (
    "Create 2-4 horizontally separated monochrome shape panels. Crop and "
    "binarize each panel, compare shapes up to all rotations and reflections, "
    "and output an N x N matrix with 5 on the diagonal, 2 for equivalent "
    "off-diagonal pairs, and 0 otherwise. The sampler includes canonical "
    "5-8-cell classes plus compact 3-4-cell classes and guarantees lessons "
    "that refute identity-only, rotation-only, and equal-size shortcuts."
)

INVARIANTS = [
    "background is 0 and separators are exactly one full-height zero column",
    "there are N in {2,3,4} panels and the input height is at least N",
    "each panel is one connected monochrome shape and panel colors are distinct",
    "every shape belongs to the curated 3-8-cell D4-class bank",
]

AXES = {
    "n_panels": {
        "type": "int",
        "default": "difficulty-skewed over the full 2..4 domain",
        "valid": "2..4",
    },
}

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 22  # Bell(2) + Bell(3) + Bell(4)


Shape = tuple[tuple[int, int], ...]
Grid = list[list[int]]


def _normalize(shape: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(shape)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_dims(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(shape)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _rotate_cw(shape: Sequence[tuple[int, int]]) -> Shape:
    normalized = _normalize(shape)
    height, _ = _shape_dims(normalized)
    return _normalize((col, height - 1 - row) for row, col in normalized)


def _flip_lr(shape: Sequence[tuple[int, int]]) -> Shape:
    normalized = _normalize(shape)
    _, width = _shape_dims(normalized)
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _rotations(shape: Sequence[tuple[int, int]]) -> tuple[Shape, ...]:
    variants = set()
    current = _normalize(shape)
    for _ in range(4):
        variants.add(current)
        current = _rotate_cw(current)
    return tuple(sorted(variants))


def _d4_orbit(shape: Sequence[tuple[int, int]]) -> tuple[Shape, ...]:
    variants = set(_rotations(shape))
    variants.update(_rotations(_flip_lr(shape)))
    return tuple(sorted(variants))


def canonical_shape(shape: Sequence[tuple[int, int]]) -> Shape:
    """Canonical binary shape under all rotations and reflections."""
    return min(_d4_orbit(shape))


def _rotation_canonical(shape: Sequence[tuple[int, int]]) -> Shape:
    return min(_rotations(shape))


def _shape_from_rows(*rows: str) -> Shape:
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("shape rows must be a non-empty rectangle")
    return _normalize(
        (row, col)
        for row, values in enumerate(rows)
        for col, value in enumerate(values)
        if value == "1"
    )


# The first eight entries are the eight distinct D4 classes appearing across
# the five canonical H118 inputs.  Remaining entries add compact classes so
# every occupied-cell count 3..8 has at least two distinct classes.
SHAPE_CLASSES: tuple[Shape, ...] = (
    _shape_from_rows("100", "100", "111"),          # canonical size 5
    _shape_from_rows("101", "101", "111"),          # canonical size 7
    _shape_from_rows("11", "11", "10"),             # canonical size 5
    _shape_from_rows("001", "101", "111"),          # canonical size 6
    _shape_from_rows("0011", "1101", "0111"),       # canonical size 8
    _shape_from_rows("111", "101", "111"),          # canonical size 8
    _shape_from_rows("011", "110", "100"),          # canonical size 5
    _shape_from_rows("001", "111", "001"),          # canonical size 5
    _shape_from_rows("10", "11"),                    # L triomino
    _shape_from_rows("111"),                          # I triomino
    _shape_from_rows("11", "11"),                    # O tetromino
    _shape_from_rows("10", "10", "11"),             # L tetromino
    _shape_from_rows("111", "010"),                  # T tetromino
    _shape_from_rows("011", "110"),                  # S tetromino
    _shape_from_rows("1111"),                         # I tetromino
    _shape_from_rows("111", "111"),                  # 2x3 hexomino
    _shape_from_rows("111", "101", "110"),          # compact heptomino
    _shape_from_rows("1111", "1111"),                # 2x4 octomino
)

_CLASS_CANONS = tuple(canonical_shape(shape) for shape in SHAPE_CLASSES)
if len(set(_CLASS_CANONS)) != len(_CLASS_CANONS):
    raise RuntimeError("SHAPE_CLASSES must contain unique D4 classes")

_CLASSES_BY_SIZE: dict[int, tuple[int, ...]] = {}
_grouped: dict[int, list[int]] = defaultdict(list)
for _index, _shape in enumerate(SHAPE_CLASSES):
    _grouped[len(_shape)].append(_index)
_CLASSES_BY_SIZE = {size: tuple(indices) for size, indices in _grouped.items()}

# Restricted-growth strings enumerate every set partition, hence every possible
# equivalence-relation matrix, for the advertised panel counts.  The complete
# finite output alphabet has Bell(2)+Bell(3)+Bell(4) = 22 members.
PARTITIONS_BY_N: dict[int, tuple[tuple[int, ...], ...]] = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 1, 2)),
    4: (
        (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 1, 0),
        (0, 0, 1, 1), (0, 0, 1, 2), (0, 1, 0, 0),
        (0, 1, 0, 1), (0, 1, 0, 2), (0, 1, 1, 0),
        (0, 1, 1, 1), (0, 1, 1, 2), (0, 1, 2, 0),
        (0, 1, 2, 1), (0, 1, 2, 2), (0, 1, 2, 3),
    ),
}
assert sum(len(values) for values in PARTITIONS_BY_N.values()) == EXPECTED_OUTPUT_CODOMAIN


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _panel_spans(grid: Sequence[Sequence[int]]) -> tuple[list[tuple[int, int]], list[int]]:
    height = len(grid)
    width = len(grid[0])
    blank = [all(grid[row][col] == 0 for row in range(height)) for col in range(width)]
    if blank[0] or blank[-1]:
        raise ValueError("leading or trailing full-zero columns are outside the grammar")

    spans: list[tuple[int, int]] = []
    gaps: list[int] = []
    col = 0
    while col < width:
        start = col
        while col < width and not blank[col]:
            col += 1
        spans.append((start, col))
        if col == width:
            break
        gap_start = col
        while col < width and blank[col]:
            col += 1
        gaps.append(col - gap_start)
    return spans, gaps


def split_panels(grid: Sequence[Sequence[int]]) -> list[Grid]:
    """Split a validated rectangular grid at full-height zero columns."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    spans, _ = _panel_spans(grid)
    return [[list(row[start:stop]) for row in grid] for start, stop in spans]


def _crop_panel(panel: Sequence[Sequence[int]]) -> Grid:
    occupied_rows = [row for row, values in enumerate(panel) if any(values)]
    occupied_cols = [
        col
        for col in range(len(panel[0]))
        if any(panel[row][col] != 0 for row in range(len(panel)))
    ]
    if not occupied_rows or not occupied_cols:
        raise ValueError("panel contains no occupied cells")
    return [
        [panel[row][col] for col in range(min(occupied_cols), max(occupied_cols) + 1)]
        for row in range(min(occupied_rows), max(occupied_rows) + 1)
    ]


def _panel_shape(panel: Sequence[Sequence[int]]) -> tuple[int, Shape]:
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"panel must contain exactly one nonzero color, found {sorted(colors)}")
    color = next(iter(colors))
    cropped = _crop_panel(panel)
    shape = _normalize(
        (row, col)
        for row, values in enumerate(cropped)
        for col, value in enumerate(values)
        if value != 0
    )
    return color, shape


def panel_shapes(grid: Sequence[Sequence[int]]) -> tuple[Shape, ...]:
    return tuple(_panel_shape(panel)[1] for panel in split_panels(grid))


def _relation_output(grid: Sequence[Sequence[int]], relation: str) -> Grid:
    shapes = panel_shapes(grid)
    if relation == "d4":
        keys = [canonical_shape(shape) for shape in shapes]
    elif relation == "rotation":
        keys = [_rotation_canonical(shape) for shape in shapes]
    elif relation == "identity":
        keys = [_normalize(shape) for shape in shapes]
    elif relation == "cell_count":
        keys = [len(shape) for shape in shapes]
    else:
        raise ValueError(f"unknown relation {relation!r}")

    size = len(shapes)
    return [
        [5 if row == col else (2 if keys[row] == keys[col] else 0) for col in range(size)]
        for row in range(size)
    ]


def equivalence_output(grid: Sequence[Sequence[int]]) -> Grid:
    """Python mirror of the bound Racket semantics, used by tests/contracts."""
    return _relation_output(grid, "d4")


def _identity_only_output(grid: Sequence[Sequence[int]]) -> Grid:
    return _relation_output(grid, "identity")


def _rotation_only_output(grid: Sequence[Sequence[int]]) -> Grid:
    return _relation_output(grid, "rotation")


def _cell_count_only_output(grid: Sequence[Sequence[int]]) -> Grid:
    return _relation_output(grid, "cell_count")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the selected generator's exact input grammar."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    try:
        spans, gaps = _panel_spans(grid)
    except ValueError as exc:
        return [str(exc)]
    if any(gap != 1 for gap in gaps):
        errors.append(f"panel separators must be exactly one column, found gap widths {gaps}")
    if len(spans) not in (2, 3, 4):
        errors.append(f"expected 2..4 panels, found {len(spans)}")
    if len(grid) < len(spans):
        errors.append(
            f"input height {len(grid)} must be at least panel count {len(spans)} so the output shrinks"
        )
    if errors:
        return errors

    colors: list[int] = []
    for index, panel in enumerate(split_panels(grid)):
        try:
            color, shape = _panel_shape(panel)
        except ValueError as exc:
            errors.append(f"panel {index}: {exc}")
            continue
        colors.append(color)
        canon = canonical_shape(shape)
        if canon not in set(_CLASS_CANONS):
            errors.append(
                f"panel {index}: shape with {len(shape)} cells is outside the curated D4-class bank"
            )
    if len(colors) != len(set(colors)):
        errors.append("panel colors must be pairwise distinct")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every generated input lies in the same validated semantic manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | None]:
    try:
        return {"n_panels": len(split_panels(grid))}
    except (TypeError, ValueError, IndexError):
        return {"n_panels": None}


def _has_non_identity_equivalence(grid) -> bool:
    if self_check(grid):
        return False
    shapes = panel_shapes(grid)
    return any(
        canonical_shape(left) == canonical_shape(right) and _normalize(left) != _normalize(right)
        for left, right in combinations(shapes, 2)
    )


def _has_reflection_only_equivalence(grid) -> bool:
    if self_check(grid):
        return False
    shapes = panel_shapes(grid)
    return any(
        canonical_shape(left) == canonical_shape(right)
        and _rotation_canonical(left) != _rotation_canonical(right)
        for left, right in combinations(shapes, 2)
    )


def _has_same_size_non_equivalence(grid) -> bool:
    if self_check(grid):
        return False
    shapes = panel_shapes(grid)
    return any(
        len(left) == len(right) and canonical_shape(left) != canonical_shape(right)
        for left, right in combinations(shapes, 2)
    )


SEMANTIC_WITNESSES = {
    "non_identity_equivalence": _has_non_identity_equivalence,
    "reflection_only_equivalence": _has_reflection_only_equivalence,
    "same_size_non_equivalence": _has_same_size_non_equivalence,
}

SEMANTIC_RIVALS = {
    "identity_only": _identity_only_output,
    "rotation_only": _rotation_only_output,
    "cell_count_only": _cell_count_only_output,
}

WITNESS_RIVALS = {
    "non_identity_equivalence": ["identity_only"],
    "reflection_only_equivalence": ["rotation_only"],
    "same_size_non_equivalence": ["cell_count_only"],
}

CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require a valid lesson that visibly refutes the three main shortcuts."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the generator grammar")

    seen_witnesses: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = self_check(demo["input"])
        if input_errors:
            reasons.append(f"demo {index} input is outside the generator grammar")
            continue
        if demo["output"] != equivalence_output(demo["input"]):
            reasons.append(f"demo {index} output does not match D4 equivalence semantics")
        seen_witnesses.update(
            name for name, predicate in SEMANTIC_WITNESSES.items() if predicate(demo["input"])
        )

    for witness in SEMANTIC_WITNESSES:
        if witness not in seen_witnesses:
            reasons.append(f"demonstrations do not expose {witness}")
    return reasons


def _variants_fitting(class_index: int, max_height: int) -> tuple[Shape, ...]:
    return tuple(
        shape for shape in _d4_orbit(SHAPE_CLASSES[class_index]) if _shape_dims(shape)[0] <= max_height
    )


def _rotation_pair(class_index: int, max_height: int, rng) -> tuple[Shape, Shape]:
    variants = [shape for shape in _rotations(SHAPE_CLASSES[class_index]) if _shape_dims(shape)[0] <= max_height]
    if len(variants) < 2:
        raise ValueError("class has no two fitting rotational variants")
    first = rng.choice(variants)
    second = rng.choice([shape for shape in variants if shape != first])
    return first, second


def _choose_distinct_classes(
    rng, count: int, *, excluded: set[int] | None = None, max_height: int | None = None
) -> list[int]:
    excluded = excluded or set()
    candidates = [
        index
        for index in range(len(SHAPE_CLASSES))
        if index not in excluded
        and (max_height is None or _variants_fitting(index, max_height))
    ]
    if count > len(candidates):
        raise ValueError("not enough distinct fitting shape classes")
    return rng.sample(candidates, count)


def _partition_groups(partition: Sequence[int]) -> dict[int, list[int]]:
    groups: dict[int, list[int]] = defaultdict(list)
    for panel_index, group in enumerate(partition):
        groups[group].append(panel_index)
    return dict(groups)


def _partition_for(seed: int, sample_index: int, n_panels: int, case: int) -> tuple[int, ...]:
    candidates = list(PARTITIONS_BY_N[n_panels])
    if case in (0, 1):
        candidates = [p for p in candidates if len(set(p)) < len(p)]
    elif case == 2:
        candidates = [p for p in candidates if len(set(p)) >= 2]
    if not candidates:
        raise ValueError("semantic schedule has no compatible relation partition")
    # The arithmetic schedule is deliberate: the linter's fixed 24x6 probe
    # traverses the whole finite codomain instead of repeatedly sampling a few
    # high-probability matrices.  Shape/color nuisance remains independently keyed.
    return candidates[(int(seed) + int(sample_index)) % len(candidates)]


def _reflection_candidates(class_index: int, max_height: int) -> tuple[tuple[Shape, ...], tuple[Shape, ...]]:
    base = tuple(
        shape
        for shape in _rotations(SHAPE_CLASSES[class_index])
        if _shape_dims(shape)[0] <= max_height
    )
    if not base:
        return (), ()
    rotation_key = _rotation_canonical(base[0])
    mirrored = tuple(
        shape
        for shape in _rotations(_flip_lr(SHAPE_CLASSES[class_index]))
        if _shape_dims(shape)[0] <= max_height
        and _rotation_canonical(shape) != rotation_key
    )
    return base, mirrored


def _reflection_pair(class_index: int, max_height: int, rng) -> tuple[Shape, Shape]:
    base, mirrored = _reflection_candidates(class_index, max_height)
    if not base or not mirrored:
        raise ValueError("class has no fitting reflection-only pair")
    return rng.choice(base), rng.choice(mirrored)


def _class_plan(
    partition: Sequence[int], case: int, max_height: int, rng
) -> tuple[list[int], dict[int, Shape]]:
    groups = _partition_groups(partition)
    labels = sorted(groups)
    forced_shapes: dict[int, Shape] = {}
    group_classes: dict[int, int] = {}
    used: set[int] = set()

    if case == 0:  # a repeated group shown in two visibly rotated orientations
        repeated_groups = [label for label in labels if len(groups[label]) >= 2]
        target_group = rng.choice(repeated_groups)
        candidates = [
            index
            for index in range(len(SHAPE_CLASSES))
            if len([
                shape for shape in _rotations(SHAPE_CLASSES[index])
                if _shape_dims(shape)[0] <= max_height
            ]) >= 2
        ]
        class_index = rng.choice(candidates)
        group_classes[target_group] = class_index
        used.add(class_index)
        left, right = _rotation_pair(class_index, max_height, rng)
        first, second = groups[target_group][:2]
        forced_shapes[first], forced_shapes[second] = left, right

    elif case == 1:  # a repeated group requiring reflection, not rotation
        repeated_groups = [label for label in labels if len(groups[label]) >= 2]
        target_group = rng.choice(repeated_groups)
        candidates = [
            index for index in range(len(SHAPE_CLASSES))
            if all(_reflection_candidates(index, max_height))
        ]
        class_index = rng.choice(candidates)
        group_classes[target_group] = class_index
        used.add(class_index)
        left, right = _reflection_pair(class_index, max_height, rng)
        first, second = groups[target_group][:2]
        forced_shapes[first], forced_shapes[second] = left, right

    elif case == 2:  # two distinct groups with equal occupied-cell counts
        first_group, second_group = rng.sample(labels, 2)
        size_options: list[tuple[int, tuple[int, ...]]] = []
        for size, indices in _CLASSES_BY_SIZE.items():
            fitting = tuple(i for i in indices if _variants_fitting(i, max_height))
            if len(fitting) >= 2:
                size_options.append((size, fitting))
        _, fitting = rng.choice(size_options)
        first_class, second_class = rng.sample(list(fitting), 2)
        group_classes[first_group] = first_class
        group_classes[second_group] = second_class
        used.update((first_class, second_class))

    remaining = [label for label in labels if label not in group_classes]
    chosen = _choose_distinct_classes(
        rng, len(remaining), excluded=used, max_height=max_height
    )
    group_classes.update(zip(remaining, chosen))
    return [group_classes[label] for label in partition], forced_shapes

def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; the bound Racket rule owns labels."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if "n_panels" in overrides:
        value = overrides["n_panels"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("n_panels override must be an integer in 2..4")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_panels = ctx.draw_int_diff("n_panels", 2, 4)
    height = max(3, n_panels)
    class_rng = ctx.draw_rng("class_plan")
    orientation_rng = ctx.draw_rng("orientations")
    offset_rng = ctx.draw_rng("vertical_offsets")

    case = sample_index % EXAMPLES_NEEDED
    partition = _partition_for(seed, sample_index, n_panels, case)
    class_ids, forced_shapes = _class_plan(partition, case, height, class_rng)

    shapes: list[Shape] = []
    for panel_index, class_index in enumerate(class_ids):
        if panel_index in forced_shapes:
            shape = forced_shapes[panel_index]
        else:
            variants = _variants_fitting(class_index, height)
            if not variants:
                raise ValueError(f"shape class {class_index} has no orientation fitting height {height}")
            shape = orientation_rng.choice(variants)
        shapes.append(shape)

    colors = ctx.draw_distinct_colors("panel_colors", n=n_panels, exclude=(0,))
    widths = [_shape_dims(shape)[1] for shape in shapes]
    grid = full_grid(height, sum(widths) + n_panels - 1, 0)

    start_col = 0
    for color, shape, width in zip(colors, shapes, widths):
        shape_height, _ = _shape_dims(shape)
        top = offset_rng.randrange(height - shape_height + 1)
        for row, col in shape:
            grid[top + row][start_col + col] = color
        start_col += width + 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]
