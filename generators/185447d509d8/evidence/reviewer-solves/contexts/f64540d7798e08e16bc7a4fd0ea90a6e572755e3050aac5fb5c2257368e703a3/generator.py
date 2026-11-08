"""Generate lessons for recognizing shape equivalence under all D4 symmetries.

Each input contains four isolated, differently coloured tetrominoes.  Components
are ordered by the row-major position of their bounding boxes.  The canonical
output is a 4x4 matrix with red (2) at ``[i][j]`` exactly when components ``i``
and ``j`` have the same binary shape under any rotation or reflection.

Ordinary generation deliberately includes a chiral S/Z pair.  That pair is
reflection-equivalent but not rotation-equivalent, so every generated lesson
rules out the common "rotations only" shortcut.  All objects have four cells,
which simultaneously rules out a same-area shortcut by including at least two
non-equivalent shape classes.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "185447d509d8"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "9586787e3555"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
# With four row-major-labelled objects, the allowed class partitions yield
# C(4,2)=6 one-pair matrices plus 3 perfect-matchings (two-pair matrices).
EXPECTED_OUTPUT_CODOMAIN = 9

SUMMARY = (
    "Find the four isolated coloured objects in row-major bounding-box order. "
    "Emit a 4x4 red(2)/black(0) matrix whose entries mark whether each pair of "
    "binary shapes is identical under any of the eight dihedral symmetries."
)

INVARIANTS = [
    "background is black (0)",
    "exactly four isolated 4-connected objects use four distinct non-zero colours",
    "the object-equivalence partition is either one pair plus two singletons or two pairs",
    "every generated lesson contains a reflection-only equivalent pair",
    "every generated lesson contains equal-area objects that are not equivalent",
]

_SIZE_PROFILES = ("12x14", "13x15", "12x16", "14x14", "12x15")
_PARTITIONS = ("one_pair", "two_pairs")
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SIZE_PROFILES_BY_BAND = {
    None: _SIZE_PROFILES,
    "easy": ("12x14", "12x15"),
    "medium": ("13x15", "14x14"),
    "hard": ("12x16",),
}
_PARTITIONS_BY_BAND = {
    None: _PARTITIONS,
    "easy": ("one_pair",),
    "medium": _PARTITIONS,
    "hard": ("two_pairs",),
}

AXES = {
    "size_profile": {
        "type": "str",
        "default": "difficulty-scheduled canonical profile",
        "valid": "12x14|13x15|12x16|14x14|12x15",
    },
    "partition": {
        "type": "str",
        "default": "difficulty-scheduled relation structure",
        "valid": "one_pair|two_pairs",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Four-cell connected shapes from distinct D4 equivalence classes.
_S_SHAPE = ((0, 1), (0, 2), (1, 0), (1, 1))
_T_SHAPE = ((0, 0), (0, 1), (0, 2), (1, 1))
_L_SHAPE = ((0, 0), (1, 0), (2, 0), (2, 1))
_I_SHAPE = ((0, 0), (0, 1), (0, 2), (0, 3))
_O_SHAPE = ((0, 0), (0, 1), (1, 0), (1, 1))
_SINGLETON_BASES = (_T_SHAPE, _L_SHAPE, _I_SHAPE, _O_SHAPE)
_PAIR_BASES = (_T_SHAPE, _L_SHAPE, _I_SHAPE)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    if not materialized:
        raise ValueError("shape must contain at least one cell")
    min_row = min(row for row, _ in materialized)
    min_col = min(col for _, col in materialized)
    return tuple(sorted((row - min_row, col - min_col) for row, col in materialized))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    max_row = max(row for row, _ in normalized)
    return _normalize((col, max_row - row) for row, col in normalized)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    max_col = max(col for _, col in normalized)
    return _normalize((row, max_col - col) for row, col in normalized)


def _rotation_forms(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    current = _normalize(cells)
    forms = set()
    for _ in range(4):
        forms.add(current)
        current = _rotate_cw(current)
    return frozenset(forms)


def _dihedral_forms(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    rotations = _rotation_forms(cells)
    return frozenset(set(rotations) | {_flip_lr(form) for form in rotations})


def _dihedral_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral_forms(cells))


def _random_rotation(shape: Sequence[tuple[int, int]], rng) -> tuple[tuple[int, int], ...]:
    forms = sorted(_rotation_forms(shape))
    return forms[rng.randrange(len(forms))]


def _shape_dimensions(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Return same-colour 4-connected components in bbox row-major order."""
    height = len(grid)
    width = len(grid[0])
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
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            min_row = min(cell_row for cell_row, _ in cells)
            min_col = min(cell_col for _, cell_col in cells)
            max_row = max(cell_row for cell_row, _ in cells)
            max_col = max(cell_col for _, cell_col in cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": _normalize(cells),
                    "bbox": (min_row, min_col, max_row, max_col),
                }
            )
    return sorted(components, key=lambda component: component["bbox"][:2])


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty or non-grid input"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} outside ARC bounds")
    bad_values = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not (0 <= value <= 9)
    ]
    if bad_values:
        errors.append("grid contains a non-integer or color outside 0..9")
    return errors


def _partition_name(components: Sequence[dict[str, Any]]) -> str | None:
    class_counts = Counter(_dihedral_key(component["shape"]) for component in components)
    sizes = sorted(class_counts.values())
    if sizes == [1, 1, 2]:
        return "one_pair"
    if sizes == [2, 2]:
        return "two_pairs"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed inputs and lessons that hide the intended D4 relation."""
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors

    height = len(grid)
    width = len(grid[0])
    components = _components(grid)
    if len(components) != 4:
        errors.append(f"expected exactly 4 components; found {len(components)}")
        return errors

    colors = [component["color"] for component in components]
    if len(set(colors)) != 4:
        errors.append(f"expected 4 distinct object colours; found {len(set(colors))}")

    occupied = {
        (row, col): grid[row][col]
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    touching_pairs = set()
    for (row, col), color in occupied.items():
        for delta_row, delta_col in ((1, 0), (0, 1)):
            neighbor = (row + delta_row, col + delta_col)
            if neighbor in occupied and occupied[neighbor] != color:
                touching_pairs.add(tuple(sorted((color, occupied[neighbor]))))
    if touching_pairs:
        errors.append(f"objects must be spatially isolated; touching colour pairs {sorted(touching_pairs)}")

    partition = _partition_name(components)
    if partition is None:
        class_sizes = sorted(
            Counter(_dihedral_key(component["shape"]) for component in components).values()
        )
        errors.append(
            "expected equivalence partition one_pair [1,1,2] or two_pairs [2,2]; "
            f"found {class_sizes}"
        )

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested = nested
        else:
            requested = {axis: meta[axis] for axis in AXES if axis in meta}
    if requested:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and value is not None and observed.get(axis) != value:
                errors.append(
                    f"meta {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """The strict profile is the ordinary, canonical-compatible profile."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact advertised axis directly from the returned grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _components(grid)
    if len(components) != 4:
        raise ValueError(f"expected exactly 4 components; found {len(components)}")
    size_profile = f"{len(grid)}x{len(grid[0])}"
    if size_profile not in _SIZE_PROFILES:
        raise ValueError(f"unrecognized size profile {size_profile!r}")
    partition = _partition_name(components)
    if partition is None:
        raise ValueError("grid does not realize an advertised partition")
    return {"size_profile": size_profile, "partition": partition}


def _difficulty_band(difficulty: Any) -> str | None:
    if difficulty in _ALLOWED_DIFFICULTIES:
        return difficulty
    value = float(difficulty)
    if value < 1 / 3:
        return "easy"
    if value < 2 / 3:
        return "medium"
    return "hard"


def _draw_scheduled_choice(context, label: str, full_domain, scheduled_domain):
    """Use a visible band schedule while preserving every exact override."""
    options = full_domain if label in context.overrides else scheduled_domain
    return context.draw_choice(label, options)


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        if type(difficulty) not in (int, float) or isinstance(difficulty, bool):
            raise ValueError("difficulty must be None, easy, medium, hard, or a number in [0,1]")
        if not 0.0 <= float(difficulty) <= 1.0:
            raise ValueError("numeric difficulty must be in [0,1]")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")
    domains = {"size_profile": _SIZE_PROFILES, "partition": _PARTITIONS}
    for axis, value in overrides.items():
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{axis} override must be a string")
        if value not in domains[axis]:
            raise ValueError(f"{axis} override {value!r} not in {domains[axis]}")


def _zones(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Four separated interior rectangles, each large enough for any tetromino."""
    top = (1, height // 2 - 2)
    bottom = (height // 2 + 1, height - 2)
    left = (1, width // 2 - 2)
    right = (width // 2 + 1, width - 2)
    zones = (
        (top[0], top[1], left[0], left[1]),
        (top[0], top[1], right[0], right[1]),
        (bottom[0], bottom[1], left[0], left[1]),
        (bottom[0], bottom[1], right[0], right[1]),
    )
    if any(r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4 for r1, r2, c1, c2 in zones):
        raise ValueError(f"size profile {height}x{width} is too small for four zones")
    return zones


def _shape_plan(partition: str, rng) -> list[tuple[tuple[int, int], ...]]:
    # Chiral pair: reflection-equivalent, provably not rotation-equivalent.
    first = _random_rotation(_S_SHAPE, rng)
    second = _random_rotation(_flip_lr(_S_SHAPE), rng)
    shapes = [first, second]

    if partition == "one_pair":
        singleton_bases = rng.sample(list(_SINGLETON_BASES), 2)
        shapes.extend(_random_rotation(base, rng) for base in singleton_bases)
    elif partition == "two_pairs":
        pair_base = rng.choice(list(_PAIR_BASES))
        forms = sorted(_rotation_forms(pair_base))
        pair_indices = rng.sample(range(len(forms)), 2)
        shapes.extend(forms[index] for index in pair_indices)
    else:  # Defensive: generation validation should make this unreachable.
        raise ValueError(f"unsupported partition {partition!r}")

    rng.shuffle(shapes)
    return shapes


def _paint_in_zone(grid, shape, color: int, zone, rng) -> None:
    min_row, max_row, min_col, max_col = zone
    shape_height, shape_width = _shape_dimensions(shape)
    last_origin_row = max_row - shape_height + 1
    last_origin_col = max_col - shape_width + 1
    if last_origin_row < min_row or last_origin_col < min_col:
        raise AssertionError(f"shape {shape} does not fit zone {zone}")
    origin_row = rng.randint(min_row, last_origin_row)
    origin_col = rng.randint(min_col, last_origin_col)
    for delta_row, delta_col in shape:
        if grid[origin_row + delta_row][origin_col + delta_col] != 0:
            raise AssertionError("constructive zones unexpectedly overlap")
        grid[origin_row + delta_row][origin_col + delta_col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = _difficulty_band(difficulty)
    size_profile = _draw_scheduled_choice(
        context,
        "size_profile",
        _SIZE_PROFILES,
        _SIZE_PROFILES_BY_BAND[band],
    )
    partition = _draw_scheduled_choice(
        context,
        "partition",
        _PARTITIONS,
        _PARTITIONS_BY_BAND[band],
    )
    height, width = (int(part) for part in size_profile.split("x"))

    shape_rng = context.draw_rng("shape_plan")
    layout_rng = context.draw_rng("layout")
    palette_rng = context.draw_rng("palette")
    shapes = _shape_plan(partition, shape_rng)
    colors = palette_rng.sample(list(range(1, 10)), 4)
    zones = list(_zones(height, width))
    layout_rng.shuffle(zones)

    grid = full_grid(height, width, 0)
    for shape, color, zone in zip(shapes, colors, zones):
        _paint_in_zone(grid, shape, color, zone, layout_rng)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"size_profile": size_profile, "partition": partition}},
    )
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _relation_matrix(grid, relation) -> list[list[int]]:
    shapes = [component["shape"] for component in _components(grid)]
    return [
        [2 if relation(left, right) else 0 for right in shapes]
        for left in shapes
    ]


def _rival_rotation_only(grid) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: right in _rotation_forms(left))


def _rival_same_area(grid) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: len(left) == len(right))


def _rival_exact_orientation(grid) -> list[list[int]]:
    return _relation_matrix(grid, lambda left, right: _normalize(left) == _normalize(right))


SEMANTIC_RIVALS = {
    "rotation_only": _rival_rotation_only,
    "same_area": _rival_same_area,
    "exact_orientation_only": _rival_exact_orientation,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_shapes(grid) -> list[tuple[tuple[int, int], ...]]:
    if self_check(grid):
        return []
    return [component["shape"] for component in _components(grid)]


def _has_reflection_only_match(grid) -> bool:
    shapes = _valid_shapes(grid)
    return any(
        right in _dihedral_forms(left) and right not in _rotation_forms(left)
        for index, left in enumerate(shapes)
        for right in shapes[index + 1 :]
    )


def _has_equal_area_nonmatch(grid) -> bool:
    shapes = _valid_shapes(grid)
    return any(
        len(left) == len(right) and right not in _dihedral_forms(left)
        for index, left in enumerate(shapes)
        for right in shapes[index + 1 :]
    )


def _has_orientation_variant_match(grid) -> bool:
    shapes = _valid_shapes(grid)
    return any(
        right in _dihedral_forms(left) and _normalize(right) != _normalize(left)
        for index, left in enumerate(shapes)
        for right in shapes[index + 1 :]
    )


SEMANTIC_WITNESSES = {
    "reflection_only_pair": _has_reflection_only_match,
    "equal_area_nonmatch": _has_equal_area_nonmatch,
    "orientation_variant_match": _has_orientation_variant_match,
}

WITNESS_RIVALS = {
    "reflection_only_pair": ["rotation_only"],
    "equal_area_nonmatch": ["same_area"],
    "orientation_variant_match": ["exact_orientation_only"],
}
