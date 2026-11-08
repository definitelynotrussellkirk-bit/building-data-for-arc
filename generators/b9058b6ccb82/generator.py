"""Generator for b9058b6ccb82 — extract the dihedral odd-one-out.

Every non-zero color is one halo-separated 4-connected object.  All but one
objects have the same free-polyomino shape: translation, rotation, and mirror
reflection do not change a class.  The answer is the singleton class cropped to
its tight bounding box, preserving the object's observed pose and color.

The three-example schedule deliberately blocks the canonical shortcuts.  Each
lesson combines a canonical-like unequal-size example, a chiral equal-size
example shown in both handednesses, and a broader equal-size pairing.  Targets
are never fixed to the last object.  Thus cell count, reading-order position,
and rotation-only matching cannot replace the full dihedral rule.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9058b6ccb82"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "7fc0dbf623b9"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "A 0-background grid contains 3-4 halo-separated objects in distinct "
    "non-zero colors. All but one share a free-polyomino shape under rotation "
    "and reflection. Output the singleton object's observed pose and color, "
    "cropped to its tight bounding box."
)

INVARIANTS = [
    "the background is 0 and every object has its own non-zero color",
    "there are 3-4 halo-separated 4-connected objects",
    "exactly two dihedral shape classes occur with multiplicities (n-1, 1)",
    "the output preserves the singleton object's color and observed pose",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile schedule",
        "valid": "9..18",
        "doc": "Input grid height; every value is accepted in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile schedule",
        "valid": "10..20",
        "doc": "Input grid width; every value is accepted in every difficulty band.",
    },
    "n_siblings": {
        "type": "int",
        "default": "3 for canonical profiles, 2-3 for the broad profile",
        "valid": "2..3",
        "doc": "Number of objects in the repeated dihedral class.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# A compact, audited bank of distinct free polyomino classes.  It spans the
# canonical 3-vs-4-cell relation and same-size 3/4/5-cell counterexamples.  F is
# chiral and therefore supplies a direct test that reflection matters.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "I3": ((0, 0), (0, 1), (0, 2)),
    "L3": ((0, 0), (1, 0), (1, 1)),
    "I4": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "L4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "O4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "S4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "F5": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    "L5": ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "T5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "U5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "V5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "W5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "X5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "Z5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
}
_SHAPES_BY_SIZE = {
    size: tuple(name for name in sorted(_SHAPES) if len(_SHAPES[name]) == size)
    for size in (3, 4, 5)
}
_CANONICAL_OUTLIERS = _SHAPES_BY_SIZE[4]
_PENTOMINO_OUTLIERS = tuple(name for name in _SHAPES_BY_SIZE[5] if name != "F5")
_CHIRAL_COMMON_NAMES = ("L4", "S4", "F5", "L5", "P5", "Z5")


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rot90(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    height = max(row for row, _ in normalized) + 1
    return _norm((col, height - 1 - row) for row, col in normalized)


def _reflect_v(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    width = max(col for _, col in normalized) + 1
    return _norm((row, width - 1 - col) for row, col in normalized)


def _rotation_variants(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: list[tuple[tuple[int, int], ...]] = []
    current = _norm(cells)
    for _ in range(4):
        if current not in variants:
            variants.append(current)
        current = _rot90(current)
    return tuple(sorted(variants))


def _d4_variants(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    direct = set(_rotation_variants(cells))
    mirrored = set(_rotation_variants(_reflect_v(cells)))
    return tuple(sorted(direct | mirrored))


def _rotation_canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    variants = _rotation_variants(cells)
    return variants[0] if variants else ()


def _d4_canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    variants = _d4_variants(cells)
    return variants[0] if variants else ()


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


_CLASS_TO_NAME = {_d4_canonical(cells): name for name, cells in _SHAPES.items()}
if len(_CLASS_TO_NAME) != len(_SHAPES):
    raise AssertionError("_SHAPES contains duplicate dihedral classes")


def _mask(cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    normalized = _norm(cells)
    if not normalized:
        return []
    height, width = _shape_dims(normalized)
    result = full_grid(height, width, 0)
    for row, col in normalized:
        result[row][col] = color
    return result


def _rectangular_grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) and row for row in grid):
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be integer ARC colors 0..9"
    return None


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for delta_row, delta_col in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            neighbor = (row + delta_row, col + delta_col)
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _analysis(grid: Any) -> dict[str, Any]:
    rectangular_error = _rectangular_grid_error(grid)
    if rectangular_error:
        return {"errors": [rectangular_error], "components": []}

    height = len(grid)
    width = len(grid[0])
    palette = {value for row in grid for value in row}
    errors: list[str] = []
    if 0 not in palette:
        errors.append("background color 0 must be present")

    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color != 0:
                by_color[color].append((row, col))

    if not 3 <= len(by_color) <= 4:
        errors.append(f"expected 3..4 distinct non-zero object colors, got {len(by_color)}")

    records: list[dict[str, Any]] = []
    for color, cells in by_color.items():
        if not _connected(cells):
            errors.append(f"color {color} must form exactly one 4-connected object")
        if not 3 <= len(cells) <= 6:
            errors.append(f"color {color} object must contain 3..6 cells, got {len(cells)}")
        normalized = _norm(cells)
        records.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "norm": normalized,
                "canonical": _d4_canonical(normalized),
                "rotation_canonical": _rotation_canonical(normalized),
                "size": len(cells),
                "top_left": min(cells),
            }
        )
    records.sort(key=lambda record: (record["top_left"], record["color"]))
    for index, record in enumerate(records):
        record["index"] = index

    owner: dict[tuple[int, int], int] = {}
    for index, record in enumerate(records):
        for cell in record["cells"]:
            owner[cell] = index
    halo_error = False
    for (row, col), index in owner.items():
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                if delta_row == delta_col == 0:
                    continue
                other = owner.get((row + delta_row, col + delta_col))
                if other is not None and other != index:
                    halo_error = True
                    break
            if halo_error:
                break
        if halo_error:
            break
    if halo_error:
        errors.append("different objects must be separated by a one-cell Chebyshev halo")

    class_counts = Counter(record["canonical"] for record in records)
    singleton_classes = [shape for shape, count in class_counts.items() if count == 1]
    majority_classes = [
        shape for shape, count in class_counts.items() if count == len(records) - 1
    ]
    if len(class_counts) != 2 or len(singleton_classes) != 1 or len(majority_classes) != 1:
        errors.append("expected exactly two dihedral classes with counts (n-1, 1)")

    outlier = None
    common = None
    if len(singleton_classes) == 1:
        outlier = next(
            (record for record in records if record["canonical"] == singleton_classes[0]),
            None,
        )
    if len(majority_classes) == 1:
        common = next(
            (record for record in records if record["canonical"] == majority_classes[0]),
            None,
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": records,
        "class_counts": class_counts,
        "common": common,
        "outlier": outlier,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


_CANONICAL_PROFILES = {(9, 10, 5), (10, 11, 5)}


def canonical_profile_signature(grid) -> tuple[int, int, int] | None:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return analysis["height"], analysis["width"], len(analysis["palette"])


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_PROFILES:
        return [f"canvas/palette profile {signature!r} is not canonical"]
    return []


SCHEDULE_PROFILES = (0, 1, 2)
_BROAD_DEFAULTS = {
    "easy": (9, 12, 2),
    "medium": (13, 15, 3),
    "hard": (18, 20, 3),
}


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return difficulty


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    del seed, difficulty
    return sample_index % len(SCHEDULE_PROFILES)


def _draw_int_with_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _slots(height: int, width: int, count: int) -> tuple[tuple[int, int], ...]:
    """Reading-order 4x3 slots, halo-separated at the minimum dimensions."""
    bottom = height - 4
    right = width - 3
    if count == 3:
        return ((0, 0), (0, right), (bottom, (width - 3) // 2))
    if count == 4:
        return ((0, 0), (0, right), (bottom, 0), (bottom, right))
    raise ValueError(f"unsupported object count: {count}")


def _fitting_variants(shape_name: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = tuple(
        variant
        for variant in _d4_variants(_SHAPES[shape_name])
        if _shape_dims(variant)[0] <= 4 and _shape_dims(variant)[1] <= 3
    )
    if not variants:
        raise ValueError(f"shape {shape_name} has no orientation fitting a 4x3 slot")
    return variants


def _reflection_pair(
    shape_name: str,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    direct = [
        variant
        for variant in _rotation_variants(_SHAPES[shape_name])
        if _shape_dims(variant)[0] <= 4 and _shape_dims(variant)[1] <= 3
    ]
    direct_classes = set(_rotation_variants(_SHAPES[shape_name]))
    mirrored = [
        variant
        for variant in _rotation_variants(_reflect_v(_SHAPES[shape_name]))
        if variant not in direct_classes
        and _shape_dims(variant)[0] <= 4
        and _shape_dims(variant)[1] <= 3
    ]
    if not direct or not mirrored:
        raise ValueError(f"shape {shape_name} has no fitting reflection-only pair")
    return direct[0], mirrored[0]


def _common_orientations(
    shape_name: str, count: int, rng, *, force_reflection: bool
) -> list[tuple[tuple[int, int], ...]]:
    if force_reflection:
        direct, mirrored = _reflection_pair(shape_name)
        direct_variants = [
            variant
            for variant in _rotation_variants(direct)
            if _shape_dims(variant)[0] <= 4 and _shape_dims(variant)[1] <= 3
        ]
        rng.shuffle(direct_variants)
        # The first reading-order common object is mirror-only.  This guarantees
        # a rotation-only solver selects a common object rather than the target.
        return [mirrored] + [
            direct_variants[index % len(direct_variants)]
            for index in range(count - 1)
        ]

    variants = list(_fitting_variants(shape_name))
    rng.shuffle(variants)
    return [variants[index % len(variants)] for index in range(count)]


def _paint_component(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: Sequence[tuple[int, int]],
    color: int,
) -> None:
    row0, col0 = origin
    for row, col in cells:
        rr, cc = row0 + row, col0 + col
        if grid[rr][cc] != 0:
            raise ValueError("internal placement overlap")
        grid[rr][cc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)
    if profile == 0:
        defaults = (9, 10, 3)
    elif profile == 1:
        defaults = (10, 11, 3)
    else:
        defaults = _BROAD_DEFAULTS[band]

    height = _draw_int_with_default(ctx, "grid_h", 9, 18, defaults[0])
    width = _draw_int_with_default(ctx, "grid_w", 10, 20, defaults[1])
    n_siblings = _draw_int_with_default(ctx, "n_siblings", 2, 3, defaults[2])
    count = n_siblings + 1

    pair_rng = ctx.draw_rng("shape_pair")
    if profile == 0:
        # Canonical-like: repeated L triominoes and a four-cell singleton.
        common_name = "L3"
        outlier_name = pair_rng.choice(_CANONICAL_OUTLIERS)
        force_reflection = False
    elif profile == 1:
        # Counterexample: equal-size chiral common class shown in both handednesses.
        common_name = "F5"
        outlier_name = pair_rng.choice(_PENTOMINO_OUTLIERS)
        force_reflection = True
    else:
        # Broader equal-size pair with a second reflection witness.  Multiple
        # chiral 4/5-cell common classes preserve morphology diversity while
        # ensuring any held-out query still leaves reflection evidence in demos.
        common_name = pair_rng.choice(_CHIRAL_COMMON_NAMES)
        names = _SHAPES_BY_SIZE[len(_SHAPES[common_name])]
        outlier_name = pair_rng.choice(
            tuple(name for name in names if name != common_name)
        )
        force_reflection = True

    pose_rng = ctx.draw_rng("poses")
    common_poses = _common_orientations(
        common_name, n_siblings, pose_rng, force_reflection=force_reflection
    )
    outlier_pose = pose_rng.choice(_fitting_variants(outlier_name))

    colors = ctx.draw_rng("colors").sample(tuple(range(1, 10)), count)
    outlier_rank = 1 if count == 3 else (1, 2, 1)[profile]
    origins = _slots(height, width, count)
    grid = full_grid(height, width, 0)
    common_cursor = 0
    for rank, origin in enumerate(origins):
        if rank == outlier_rank:
            cells = outlier_pose
        else:
            cells = common_poses[common_cursor]
            common_cursor += 1
        _paint_component(grid, origin, cells, colors[rank])

    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError(f"internal generator contract violation: {errors}")
    return grid


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_siblings": len(analysis["components"]) - 1,
    }


def rule_mirror(grid) -> list[list[int]] | None:
    """Pure Python diagnostic mirror of the selected Racket rule."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return None
    outlier = analysis["outlier"]
    return _mask(outlier["norm"], outlier["color"])


def _record_mask(record: dict[str, Any]) -> list[list[int]]:
    return _mask(record["norm"], record["color"])


def _odd_by_key(
    records: Sequence[dict[str, Any]], key: Callable[[dict[str, Any]], Any]
) -> dict[str, Any] | None:
    counts = Counter(key(record) for record in records)
    for record in records:
        if counts[key(record)] == 1:
            return record
    return records[0] if records else None


def _rival_last_component(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        return None
    return _record_mask(analysis["components"][-1])


def _rival_unique_cell_count(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    record = _odd_by_key(analysis["components"], lambda item: item["size"])
    return _record_mask(record) if record is not None else None


def _rival_rotation_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    record = _odd_by_key(
        analysis["components"], lambda item: item["rotation_canonical"]
    )
    return _record_mask(record) if record is not None else None


SEMANTIC_RIVALS = {
    "last_component": _rival_last_component,
    "unique_cell_count": _rival_unique_cell_count,
    "rotation_only_equivalence": _rival_rotation_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "last_component": _rival_last_component,
    "unique_cell_count": _rival_unique_cell_count,
}


def _valid_and_differs(grid, rival_name: str) -> bool:
    answer = rule_mirror(grid)
    return answer is not None and SEMANTIC_RIVALS[rival_name](grid) != answer


def _same_size_refutes_counting(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None or analysis["outlier"] is None:
        return False
    return (
        analysis["common"]["size"] == analysis["outlier"]["size"]
        and _valid_and_differs(grid, "unique_cell_count")
    )


def _outlier_not_last(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return False
    return (
        analysis["outlier"]["index"] != len(analysis["components"]) - 1
        and _valid_and_differs(grid, "last_component")
    )


def _common_requires_reflection(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None:
        return False
    common_key = analysis["common"]["canonical"]
    rotation_classes = {
        record["rotation_canonical"]
        for record in analysis["components"]
        if record["canonical"] == common_key
    }
    return len(rotation_classes) >= 2 and _valid_and_differs(
        grid, "rotation_only_equivalence"
    )


SEMANTIC_WITNESSES = {
    "equal_cell_counts_refute_size_shortcut": _same_size_refutes_counting,
    "nonlast_target_refutes_position_shortcut": _outlier_not_last,
    "common_class_requires_reflection": _common_requires_reflection,
}
WITNESS_RIVALS = {
    "equal_cell_counts_refute_size_shortcut": ["unique_cell_count"],
    "nonlast_target_refutes_position_shortcut": ["last_component"],
    "common_class_requires_reflection": ["rotation_only_equivalence"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if expected is None:
            reasons.append(f"demo {index} is not a lawful task instance")
        elif pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the dihedral rule")

    query_answer = rule_mirror(query["input"])
    if query_answer is None:
        reasons.append("query is not a lawful task instance")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the dihedral rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair.get("output") for pair in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    base = generate(19, 0, difficulty="easy")

    all_background = full_grid(9, 10, 0)

    one_object = full_grid(9, 10, 0)
    _paint_component(one_object, (0, 0), _SHAPES["F5"], 1)

    all_same_class = full_grid(9, 10, 0)
    for origin, color, pose in zip(
        _slots(9, 10, 3),
        (1, 2, 3),
        _common_orientations(
            "F5",
            3,
            gen_ctx(seed=3, sample_index=0, version=VERSION, task_id=TASK_ID).draw_rng(
                "fixture_poses"
            ),
            force_reflection=True,
        ),
    ):
        _paint_component(all_same_class, origin, pose, color)

    all_different = full_grid(9, 10, 0)
    for origin, color, name in zip(
        _slots(9, 10, 3), (1, 2, 3), ("F5", "T5", "U5")
    ):
        _paint_component(all_different, origin, _fitting_variants(name)[0], color)

    disconnected_color = [row[:] for row in base]
    existing_color = next(value for row in disconnected_color for value in row if value)
    disconnected_color[4][4] = existing_color

    halo_touch = [row[:] for row in base]
    # A new singleton color in the gap is both too small and halo-adjacent.
    halo_touch[3][1] = 9 if existing_color != 9 else 8

    ragged = [row[:] for row in base]
    ragged[-1] = ragged[-1][:-1]

    bool_cell = [row[:] for row in base]
    bool_cell[0][0] = True

    return [
        ("all_background", all_background),
        ("single_object", one_object),
        ("no_singleton_all_same_class", all_same_class),
        ("no_majority_all_different", all_different),
        ("disconnected_same_color_noise", disconnected_color),
        ("halo_touching_noise", halo_touch),
        ("ragged_grid", ragged),
        ("boolean_cell", bool_cell),
    ]
