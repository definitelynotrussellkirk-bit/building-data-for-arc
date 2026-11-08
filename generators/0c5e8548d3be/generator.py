"""Generator for ARC task 0c5e8548d3be — rotation-equivalence matrix.

The input has four five-column object panels separated by blank columns.  The
unchanged Racket authority crops each panel, ignores its color, and emits a 4x4
matrix whose entry is cyan(8) exactly when the two shapes are equal up to a
quarter-turn rotation.

Every ordinary generated input is deliberately shortcut-resistant: all four
objects have the same cell count, at least one equivalent pair needs a genuine
rotation, and a chiral shape appears beside its mirror even though reflections
are *not* equivalent.  Thus one example already distinguishes the intended rule
from cell-count, exact-shape, reflection-inclusive, and color shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c5e8548d3be"
TASK_ID = GENERATOR_ID
RULE_HASH = "c0e3bdee7bdc"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50
# Three supported class partitions yield 3 + 4 + 6 labeled relation matrices.
EXPECTED_OUTPUT_CODOMAIN = 13

SUMMARY = (
    "Four single-color shapes occupy fixed 5-column panels in a 23-column grid. "
    "Return a 4x4 matrix with cyan(8) exactly for pairs whose cropped binary "
    "shapes are equivalent under rotation; translation and color are ignored, "
    "but reflection alone is not equivalence."
)

INVARIANTS = [
    "background is 0; input color 8 is reserved for the output relation",
    "grid height is 5..8 and width is 23 with blank separators at columns 5, 11, and 17",
    "four nonempty connected panels use four distinct single colors",
    "ordinary generated panels all have the same 4..12 cell count",
    "ordinary generated inputs contain both rotation-equivalent and rotation-distinct pairs",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical height 5 with broader 6..8 support",
        "valid": "5..8",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-aware scheduled value",
        "valid": "4..12",
    },
    "relation_profile": {
        "type": "int",
        "default": "scheduled 0,2,0,1 cycle",
        "valid": "0..2 (0=2+2, 1=3+1, 2=2+1+1 rotation classes)",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_two_pairs",
    "canonical_pair_and_singles",
    "canonical_two_pairs_alt",
    "broad_triple_and_single",
)

_PANEL_STARTS = (0, 6, 12, 18)
_SEPARATOR_COLS = (5, 11, 17)
_INPUT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_COLORS = (2, 3, 4, 6)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

Shape = tuple[tuple[int, int], ...]

# For each size, A is connected, chiral, and has four distinct rotations.
# C has the same size but belongs to a different dihedral class.  Fixed finite
# families make every advertised override constructive without rejection loops.
_SHAPE_CATALOG: dict[int, tuple[Shape, Shape]] = {
    4: (
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    7: (
        ((0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
    8: (
        ((0, 3), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 0), (3, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
    ),
    9: (
        ((0, 2), (0, 3), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    10: (
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4)),
    ),
    11: (
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1), (3, 2), (4, 0), (4, 1)),
    ),
    12: (
        ((0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (4, 2), (4, 3)),
        ((0, 1), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3), (3, 2), (3, 3), (4, 2), (4, 3), (4, 4)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rotate(shape: Iterable[tuple[int, int]]) -> Shape:
    points = _normalize(shape)
    if not points:
        return ()
    height = max(row for row, _ in points) + 1
    return _normalize((col, height - 1 - row) for row, col in points)


def _rotate_n(shape: Iterable[tuple[int, int]], turns: int) -> Shape:
    result = _normalize(shape)
    for _ in range(turns % 4):
        result = _rotate(result)
    return result


def _mirror(shape: Iterable[tuple[int, int]]) -> Shape:
    points = _normalize(shape)
    if not points:
        return ()
    width = max(col for _, col in points) + 1
    return _normalize((row, width - 1 - col) for row, col in points)


def _rotations(shape: Iterable[tuple[int, int]]) -> tuple[Shape, ...]:
    result: list[Shape] = []
    current = _normalize(shape)
    for _ in range(4):
        if current not in result:
            result.append(current)
        current = _rotate(current)
    return tuple(result)


def _rotation_key(shape: Iterable[tuple[int, int]]) -> Shape:
    return min(_rotations(shape))


def _dihedral_key(shape: Iterable[tuple[int, int]]) -> Shape:
    points = _normalize(shape)
    return min((*_rotations(points), *_rotations(_mirror(points))))


def _connected(shape: Iterable[tuple[int, int]]) -> bool:
    points = set(shape)
    if not points:
        return False
    pending = [next(iter(points))]
    seen = {pending[0]}
    while pending:
        row, col = pending.pop()
        for drow, dcol in _CARDINAL:
            neighbor = row + drow, col + dcol
            if neighbor in points and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return len(seen) == len(points)


def _validate_catalog() -> None:
    if set(_SHAPE_CATALOG) != set(range(4, 13)):
        raise RuntimeError("shape catalogue must cover every declared shape_size")
    for size, (primary, secondary) in _SHAPE_CATALOG.items():
        if len(primary) != size or len(secondary) != size:
            raise RuntimeError(f"shape catalogue size mismatch for {size}")
        if not _connected(primary) or not _connected(secondary):
            raise RuntimeError(f"shape catalogue disconnected at size {size}")
        if len(_rotations(primary)) != 4 or _rotation_key(primary) == _rotation_key(_mirror(primary)):
            raise RuntimeError(f"primary shape must be four-way chiral at size {size}")
        if _dihedral_key(primary) == _dihedral_key(secondary):
            raise RuntimeError(f"secondary shape must be a different dihedral class at size {size}")
        for shape in (primary, secondary):
            if max(row for row, _ in shape) >= 5 or max(col for _, col in shape) >= 5:
                raise RuntimeError(f"shape catalogue exceeds 5x5 at size {size}")


_validate_catalog()


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Stable four-cycle with three canonical-like slots in every cycle."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(profile: str, difficulty: Any, rng: Any) -> tuple[int, int, int]:
    slot = SCHEDULE_PROFILES.index(profile)
    relation_profiles = (0, 2, 0, 1)
    sizes = {
        None: (5, 7, 9, 11),
        "easy": (4, 5, 6, 7),
        "medium": (6, 7, 8, 9),
        "hard": (8, 9, 10, 12),
    }
    if slot < 3:
        height = 5
    elif difficulty == "easy":
        height = 6
    elif difficulty == "medium":
        height = 7
    elif difficulty == "hard":
        height = 8
    else:
        height = rng.randint(6, 8)
    return height, sizes[difficulty][slot], relation_profiles[slot]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> dict[str, int]:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (5, 8),
        "shape_size": (4, 12),
        "relation_profile": (0, 2),
    }
    clean: dict[str, int] = {}
    for name, value in overrides.items():
        if value is None:
            continue
        low, high = bounds[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in {low}..{high}")
        clean[name] = value
    return clean


def _axis_int(ctx: Any, label: str, low: int, high: int, default: int) -> int:
    """Record the scheduled default while honoring exact validated overrides."""
    if label in ctx.overrides:
        return ctx.draw_int(label, low, high)
    return ctx.draw_int(label, default, default)


def _oriented(shape: Shape, rng: Any) -> Shape:
    result = _rotate_n(shape, rng.randrange(4))
    if rng.randrange(2):
        result = _mirror(result)
    return result


def _relation_shapes(ctx: Any, shape_size: int, relation_profile: int) -> list[Shape]:
    primary, secondary = _SHAPE_CATALOG[shape_size]
    family_rng = ctx.draw_rng("shape_family")
    primary = _oriented(primary, family_rng)
    secondary = _oriented(secondary, family_rng)

    primary_rotations = list(_rotations(primary))
    mirror_rotations = list(_rotations(_mirror(primary)))
    if len(primary_rotations) != 4 or len(mirror_rotations) != 4:
        raise RuntimeError("catalogue invariant lost: primary orbit is not four-way")

    if relation_profile == 0:
        shapes = family_rng.sample(primary_rotations, 2) + family_rng.sample(mirror_rotations, 2)
    elif relation_profile == 1:
        shapes = family_rng.sample(primary_rotations, 3) + [family_rng.choice(mirror_rotations)]
    elif relation_profile == 2:
        shapes = family_rng.sample(primary_rotations, 2) + [
            family_rng.choice(mirror_rotations),
            secondary,
        ]
    else:  # validated before this helper
        raise ValueError(f"unsupported relation_profile {relation_profile}")

    ctx.draw_rng("panel_order").shuffle(shapes)
    return shapes


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    clean_overrides = _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean_overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_size, default_relation = _scheduled_defaults(
        profile, difficulty, ctx.draw_rng("schedule_defaults")
    )
    height = _axis_int(ctx, "grid_h", 5, 8, default_h)
    shape_size = _axis_int(ctx, "shape_size", 4, 12, default_size)
    relation_profile = _axis_int(ctx, "relation_profile", 0, 2, default_relation)

    shapes = _relation_shapes(ctx, shape_size, relation_profile)
    if profile.startswith("canonical_"):
        colors = list(_CANONICAL_COLORS)
    else:
        colors = ctx.draw_rng("palette").sample(list(_INPUT_COLORS), 4)
    ctx.draw_rng("color_order").shuffle(colors)

    grid = full_grid(height, 23, 0)
    position_rng = ctx.draw_rng("panel_positions")
    for start, color, shape in zip(_PANEL_STARTS, colors, shapes):
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        top = position_rng.randint(0, height - shape_height)
        left = position_rng.randint(0, 5 - shape_width)
        for row, col in shape:
            grid[top + row][start + left + col] = color
    return grid


def _grid_diagnostics(grid: Any) -> tuple[list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"], 0, 0
    if not all(isinstance(row, list) for row in grid):
        return ["every grid row must be a list"], 0, 0
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular with nonempty rows"], len(grid), width
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid cells must be integer ARC colors 0..9")
    return errors, len(grid), width


def _panel_facts(grid: list[list[int]]) -> tuple[list[Shape], list[set[int]]]:
    height = len(grid)
    shapes: list[Shape] = []
    colors: list[set[int]] = []
    for start in _PANEL_STARTS:
        cells = []
        panel_colors = set()
        for row in range(height):
            for offset in range(5):
                value = grid[row][start + offset]
                if value != 0:
                    cells.append((row, offset))
                    panel_colors.add(value)
        shapes.append(_normalize(cells))
        colors.append(panel_colors)
    return shapes, colors


def _class_sizes(shapes: Iterable[Shape]) -> tuple[int, ...]:
    keys = [_rotation_key(shape) for shape in shapes]
    return tuple(sorted(keys.count(key) for key in set(keys)))


def _relation_profile_for_shapes(shapes: Iterable[Shape]) -> int:
    profiles = {(2, 2): 0, (1, 3): 1, (1, 1, 2): 2}
    sizes = _class_sizes(shapes)
    if sizes not in profiles:
        raise ValueError(f"unsupported relation partition {sizes}")
    return profiles[sizes]


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover each declared exact control from returned pixels."""
    errors, height, width = _grid_diagnostics(grid)
    if errors or width != 23 or not 5 <= height <= 8:
        raise ValueError("grid is outside the observable generator domain")
    shapes, _ = _panel_facts(grid)
    counts = {len(shape) for shape in shapes}
    if len(counts) != 1:
        raise ValueError("shape_size is not observable because panel counts differ")
    return {
        "grid_h": height,
        "shape_size": next(iter(counts)),
        "relation_profile": _relation_profile_for_shapes(shapes),
    }


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: Any = None,
) -> list[str]:
    del difficulty
    errors, height, width = _grid_diagnostics(grid)
    if errors:
        return errors
    if not 5 <= height <= 8 or width != 23:
        errors.append("expected grid shape 5..8 x 23")
        return errors
    if any(grid[row][col] != 0 for row in range(height) for col in _SEPARATOR_COLS):
        errors.append("separator columns 5, 11, and 17 must remain background")

    shapes, colors = _panel_facts(grid)
    if any(not shape for shape in shapes):
        errors.append("all four panels must be nonempty")
    if any(shape and not 4 <= len(shape) <= 12 for shape in shapes):
        errors.append("each panel must contain 4..12 nonzero cells")
    if any(shape and not _connected(shape) for shape in shapes):
        errors.append("each panel shape must be 4-neighbor connected")
    if any(8 in panel_colors for panel_colors in colors):
        errors.append("input color 8 is reserved for the output relation")
    if any(len(panel_colors) != 1 for panel_colors in colors):
        errors.append("each panel must use exactly one nonzero color")
    single_colors = [next(iter(values)) for values in colors if len(values) == 1]
    if len(single_colors) == 4 and len(set(single_colors)) != 4:
        errors.append("the four panels must use four distinct colors")

    if all(shapes):
        class_count = len({_rotation_key(shape) for shape in shapes})
        if not 2 <= class_count <= 3:
            errors.append("expected two or three rotation-equivalence classes")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict) and not errors:
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {
                axis: candidate[axis]
                for axis in AXES
                if axis in candidate and candidate[axis] is not None
            }
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for axis, value in requested.items():
                if observed[axis] != value:
                    errors.append(f"{axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    shapes, colors = _panel_facts(grid)
    if len(grid) != 5:
        reasons.append("canonical inputs are 5 rows tall")
    palette = {next(iter(values)) for values in colors}
    if palette != set(_CANONICAL_COLORS):
        reasons.append("canonical panel palette is {2,3,4,6}")
    if _class_sizes(shapes) not in {(2, 2), (1, 1, 2)}:
        reasons.append("canonical relations use 2+2 or 2+1+1 class partitions")
    return reasons


def _matrix(values: list[Any]) -> list[list[int]]:
    return [[8 if left == right else 0 for right in values] for left in values]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python semantic mirror; Racket remains the label authority."""
    shapes, _ = _panel_facts(grid)
    return _matrix([_rotation_key(shape) for shape in shapes])


def _cell_count_equivalence(grid: list[list[int]]) -> list[list[int]]:
    shapes, _ = _panel_facts(grid)
    return _matrix([len(shape) for shape in shapes])


def _exact_shape_without_rotation(grid: list[list[int]]) -> list[list[int]]:
    shapes, _ = _panel_facts(grid)
    return _matrix(shapes)


def _reflection_equivalence(grid: list[list[int]]) -> list[list[int]]:
    shapes, _ = _panel_facts(grid)
    return _matrix([_dihedral_key(shape) for shape in shapes])


def _same_panel_color(grid: list[list[int]]) -> list[list[int]]:
    _, colors = _panel_facts(grid)
    values = [next(iter(panel)) if len(panel) == 1 else None for panel in colors]
    return _matrix(values)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "cell_count_equivalence": _cell_count_equivalence,
    "exact_shape_without_rotation": _exact_shape_without_rotation,
    "reflection_equivalence": _reflection_equivalence,
    "same_panel_color": _same_panel_color,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# The canonical demonstrations never place a chiral shape beside its mirror, so
# allowing reflections fits all five canonical pairs while changing the task.
CANONICAL_SHORTCUTS = {"reflection_equivalence": _reflection_equivalence}


def _witness_same_count_not_equivalent(grid: Any) -> bool:
    try:
        shapes, _ = _panel_facts(grid)
        return len({len(shape) for shape in shapes}) == 1 and len({_rotation_key(shape) for shape in shapes}) > 1
    except Exception:
        return False


def _witness_rotation_not_exact(grid: Any) -> bool:
    try:
        shapes, _ = _panel_facts(grid)
        return any(
            _rotation_key(shapes[left]) == _rotation_key(shapes[right])
            and shapes[left] != shapes[right]
            for left in range(4)
            for right in range(left + 1, 4)
        )
    except Exception:
        return False


def _witness_reflection_not_rotation(grid: Any) -> bool:
    try:
        shapes, _ = _panel_facts(grid)
        return any(
            _dihedral_key(shapes[left]) == _dihedral_key(shapes[right])
            and _rotation_key(shapes[left]) != _rotation_key(shapes[right])
            for left in range(4)
            for right in range(left + 1, 4)
        )
    except Exception:
        return False


def _witness_color_irrelevant(grid: Any) -> bool:
    try:
        shapes, colors = _panel_facts(grid)
        single = [next(iter(values)) for values in colors]
        return len(set(single)) == 4 and any(
            _rotation_key(shapes[left]) == _rotation_key(shapes[right])
            for left in range(4)
            for right in range(left + 1, 4)
        )
    except Exception:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "same_count_different_relation": _witness_same_count_not_equivalent,
    "rotation_changes_normalized_shape": _witness_rotation_not_exact,
    "reflection_is_not_rotation": _witness_reflection_not_rotation,
    "panel_color_is_irrelevant": _witness_color_irrelevant,
}
WITNESS_RIVALS = {
    "same_count_different_relation": ["cell_count_equivalence"],
    "rotation_changes_normalized_shape": ["exact_shape_without_rotation"],
    "reflection_is_not_rotation": ["reflection_equivalence"],
    "panel_color_is_irrelevant": ["same_panel_color"],
}


def lesson_identifiable(
    demos: list[dict[str, Any]],
    query: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
    return reasons
