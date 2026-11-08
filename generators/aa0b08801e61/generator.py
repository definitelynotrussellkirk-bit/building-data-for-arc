"""Constructive sampler for ARC task aa0b08801e61.

Each nonzero 4-connected monochrome object is classified by reflection symmetry
inside its tight bounding box:

* left-right and up-down symmetric -> color 8
* left-right symmetric only        -> color 2
* up-down symmetric only           -> color 3
* neither                           -> color 4

The canonical examples can be solved by memorizing four exact object masks.
The normal lesson schedule therefore includes novel masks with the same true
symmetry classes, so exact-mask memorization is visibly wrong.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa0b08801e61"
TASK_ID = GENERATOR_ID
RULE_HASH = "febf74c1fcfe"
VERSION = "4.0.1"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "Three or four separated monochrome objects are recolored from their tight-"
    "mask reflection signature: both left-right and up-down symmetric -> 8, "
    "left-right only -> 2, up-down only -> 3, and neither -> 4. Canonical-scale "
    "profiles recur in every difficulty band, while alternating teaching "
    "profiles use unseen masks to refute exact canonical-mask memorization."
)

INVARIANTS = [
    "background is 0 and every cell is an integer ARC color 0..9",
    "there are 3 or 4 distinct-color, 4-connected objects",
    "objects are separated by at least one cell, including diagonals",
    "each object is one of the declared connected masks in a 3x3-or-smaller box",
    "object symmetry classes are distinct within a scene",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule with full 9..15 support",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule with full 12..18 support",
        "valid": "12..18",
    },
    "n_objects": {
        "type": "int",
        "default": "profile-scheduled 3 or 4",
        "valid": "3..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_BOUNDS = {
    "grid_h": (9, 15),
    "grid_w": (12, 18),
    "n_objects": (3, 4),
}

Shape = tuple[tuple[int, int], ...]
Grid = list[list[int]]


def _shape(*cells: tuple[int, int]) -> Shape:
    return tuple(sorted(cells))


# The four exact masks used by the canonical task.
_BOTH_CANONICAL = _shape(
    (0, 1),
    (1, 0), (1, 1), (1, 2),
    (2, 1),
)
_LR_CANONICAL = _shape(
    (0, 1),
    (1, 0), (1, 1), (1, 2),
    (2, 0), (2, 2),
)
_UD_CANONICAL = _shape(
    (0, 0), (0, 1),
             (1, 1), (1, 2),
    (2, 0), (2, 1),
)
_NONE_CANONICAL = _shape(
    (0, 0), (0, 1),
             (1, 1), (1, 2),
)

# Novel masks retain the same semantic classes but break exact-mask lookup.
_BOTH_SQUARE = _shape((0, 0), (0, 1), (1, 0), (1, 1))
_BOTH_RING = _shape(
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)
_LR_T = _shape((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_LR_CROWN = _shape(
    (0, 0),         (0, 2),
    (1, 0), (1, 1), (1, 2),
             (2, 1),
)
_UD_T = _shape((0, 0), (1, 0), (2, 0), (1, 1), (1, 2))
_UD_CROWN = _shape(
             (0, 1), (0, 2),
    (1, 0), (1, 1),
             (2, 1), (2, 2),
)
_NONE_L = _shape((0, 0), (1, 0), (1, 1))
_NONE_STAIR = _shape((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))

SHAPE_BANKS: dict[str, tuple[Shape, ...]] = {
    "both": (_BOTH_CANONICAL, _BOTH_SQUARE, _BOTH_RING),
    "lr": (_LR_CANONICAL, _LR_T, _LR_CROWN),
    "ud": (_UD_CANONICAL, _UD_T, _UD_CROWN),
    "none": (_NONE_CANONICAL, _NONE_L, _NONE_STAIR),
}
_ALL_MASKS = frozenset(shape for bank in SHAPE_BANKS.values() for shape in bank)
_CANONICAL_MASKS = frozenset(
    {_BOTH_CANONICAL, _LR_CANONICAL, _UD_CANONICAL, _NONE_CANONICAL}
)
_CANONICAL_PROFILES = (
    (9, 12, 3),
    (9, 13, 3),
    (10, 13, 4),
    (10, 14, 4),
)
_CLASS_COLOR = {"both": 8, "lr": 2, "ud": 3, "none": 4}

SCHEDULE_PROFILES = (
    "canonical_lr",
    "mask_trap",
    "canonical_ud",
    "mask_trap",
)


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _bbox_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(cells)
    if not normalized:
        return 0, 0
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _is_4_connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(_normalize(cells))
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    reached = {stack[0]}
    while stack:
        row, col = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (row + dr, col + dc)
            if neighbor in remaining and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return reached == remaining


def _symmetry_class(cells: Iterable[tuple[int, int]]) -> str:
    normalized = set(_normalize(cells))
    if not normalized:
        raise ValueError("cannot classify an empty object")
    max_row = max(row for row, _ in normalized)
    max_col = max(col for _, col in normalized)
    left_right = {(row, max_col - col) for row, col in normalized} == normalized
    up_down = {(max_row - row, col) for row, col in normalized} == normalized
    if left_right and up_down:
        return "both"
    if left_right:
        return "lr"
    if up_down:
        return "ud"
    return "none"


# Fail at import time if a source edit duplicates, leaks, or mislabels a
# teaching mask.  Each bank intentionally contains one canonical mask followed
# by two distinct noncanonical masks.
_declared_mask_owners: dict[Shape, str] = {}
for _class_name, _bank in SHAPE_BANKS.items():
    if len(_bank) != 3:
        raise AssertionError(f"{_class_name} shape bank must contain exactly three masks")
    if len(set(_bank)) != len(_bank):
        raise AssertionError(f"{_class_name} shape bank contains duplicate masks")
    if _bank[0] not in _CANONICAL_MASKS:
        raise AssertionError(f"{_class_name} shape bank must start with its canonical mask")
    if any(_mask in _CANONICAL_MASKS for _mask in _bank[1:]):
        raise AssertionError(f"{_class_name} teaching masks must be noncanonical")
    for _mask in _bank:
        _previous_owner = _declared_mask_owners.get(_mask)
        if _previous_owner is not None:
            raise AssertionError(
                f"shape declared in both {_previous_owner} and {_class_name} banks: {_mask!r}"
            )
        _declared_mask_owners[_mask] = _class_name
        if _symmetry_class(_mask) != _class_name or not _is_4_connected(_mask):
            raise AssertionError(f"invalid {_class_name} shape declaration: {_mask!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle canonical and shortcut-breaking profiles with period four."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(
    seed: int,
    sample_index: int,
    difficulty,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (bool is not accepted)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer (bool is not accepted)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    scheduled: int,
) -> int:
    """Record a deterministic default while retaining the full exact domain."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in overrides and overrides[label] is not None:
        return int(ctx.draw_int_strict(label, lo, hi))
    if type(scheduled) is not int or not lo <= scheduled <= hi:
        raise AssertionError(f"internal {label} default {scheduled!r} outside [{lo}, {hi}]")
    ctx.draw_bounds_store[label] = (lo, hi)
    return int(ctx._record(label, scheduled, from_override=False))


def _scheduled_defaults(sample_index: int, band: str) -> tuple[int, int, int]:
    """Favor canonical profiles while still covering every advertised value.

    Seven phases out of eight use an exact canonical input profile.  The eighth
    walks the complete height/width/count domain across successive cycles.  This
    keeps profile-floor support deterministic without making any axis dead.
    """
    phase = sample_index % 8
    if phase < 7:
        return _CANONICAL_PROFILES[phase % len(_CANONICAL_PROFILES)]
    cycle = sample_index // 8
    band_offset = {"easy": 0, "medium": 2, "hard": 4}[band]
    height = 9 + ((cycle + band_offset) % 7)
    width = 12 + ((2 * cycle + band_offset) % 7)
    count = 3 + ((cycle + band_offset) % 2)
    return height, width, count


def _profile_shapes(profile: str, n_objects: int, rng) -> list[Shape]:
    if profile == "canonical_lr":
        shapes = [_BOTH_CANONICAL, _LR_CANONICAL, _NONE_CANONICAL]
        if n_objects == 4:
            shapes.append(_UD_CANONICAL)
    elif profile == "canonical_ud":
        shapes = [_BOTH_CANONICAL, _UD_CANONICAL, _NONE_CANONICAL]
        if n_objects == 4:
            shapes.append(_LR_CANONICAL)
    elif profile == "mask_trap":
        single_axis = rng.choice(("lr", "ud"))
        other_axis = "ud" if single_axis == "lr" else "lr"
        shapes = [
            rng.choice(SHAPE_BANKS["both"][1:]),
            rng.choice(SHAPE_BANKS[single_axis][1:]),
            rng.choice(SHAPE_BANKS["none"][1:]),
        ]
        if n_objects == 4:
            shapes.append(rng.choice(SHAPE_BANKS[other_axis][1:]))
    else:
        raise ValueError(f"unknown schedule profile: {profile!r}")
    rng.shuffle(shapes)
    return shapes


def _corner_placements(
    height: int,
    width: int,
    shapes: Sequence[Shape],
    rng,
) -> list[tuple[int, int]]:
    """Constructively place up to four 3x3 masks in separated corners."""
    slots = ["tl", "tr", "bl", "br"]
    rng.shuffle(slots)
    placements: list[tuple[int, int]] = []
    for shape, slot in zip(shapes, slots):
        shape_h, shape_w = _bbox_dims(shape)
        row_jitter = rng.randint(0, min(1, height - shape_h))
        col_jitter = rng.randint(0, min(1, width - shape_w))
        top = row_jitter if slot[0] == "t" else height - shape_h - row_jitter
        left = col_jitter if slot[1] == "l" else width - shape_w - col_jitter
        placements.append((top, left))
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    """Return one deterministic lawful input; every advertised override is exact."""
    _validate_request(seed, sample_index, difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    default_h, default_w, default_count = _scheduled_defaults(sample_index, band)
    height = _scheduled_int(ctx, overrides, "grid_h", default_h)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w)
    n_objects = _scheduled_int(ctx, overrides, "n_objects", default_count)

    profile = schedule_profile(seed, sample_index, band)
    shapes = _profile_shapes(profile, n_objects, ctx.draw_rng("shape_selection"))
    colors = list(ctx.draw_distinct_colors("source_colors", n=n_objects, exclude={0}))
    placements = _corner_placements(height, width, shapes, ctx.draw_rng("layout"))

    grid = full_grid(height, width, 0)
    for shape, color, (top, left) in zip(shapes, colors, placements):
        for row, col in shape:
            if grid[top + row][left + col] != 0:
                raise AssertionError("constructive corner placement overlapped")
            grid[top + row][left + col] = color

    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise AssertionError("constructive generator emitted invalid grid: " + "; ".join(errors))
    return grid


def _components_nonzero(grid: Sequence[Sequence[int]]):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append((color, sorted(cells)))
    return found


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact axes from returned pixels."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_objects": len(_components_nonzero(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact sampled manifold and collect independent findings."""
    del difficulty  # Difficulty changes deterministic defaults, never legality.
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (bool is not a color)"]

    errors: list[str] = []
    height = len(grid)
    if not 9 <= height <= 15:
        errors.append(f"grid_h={height} outside [9,15]")
    if not 12 <= width <= 18:
        errors.append(f"grid_w={width} outside [12,18]")

    components = _components_nonzero(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3 or 4 nonzero objects, found {len(components)}")

    colors = [color for color, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("each object must have a distinct nonzero color")

    classes: list[str] = []
    component_sets: list[set[tuple[int, int]]] = []
    for index, (_, cells) in enumerate(components):
        mask = _normalize(cells)
        component_sets.append(set(cells))
        if not 3 <= len(cells) <= 9:
            errors.append(f"object {index} must contain 3..9 cells, found {len(cells)}")
        box_h, box_w = _bbox_dims(cells)
        if box_h > 3 or box_w > 3:
            errors.append(f"object {index} tight bounding box {box_h}x{box_w} exceeds 3x3")
        if not _is_4_connected(mask):
            errors.append(f"object {index} is not 4-connected")
        if mask not in _ALL_MASKS:
            errors.append(f"object {index} uses an undeclared teaching mask")
        try:
            classes.append(_symmetry_class(mask))
        except ValueError:
            errors.append(f"object {index} is empty")

    if len(classes) != len(set(classes)):
        errors.append("objects must have distinct symmetry classes")

    for left in range(len(component_sets)):
        for right in range(left + 1, len(component_sets)):
            if any(
                abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1
                for r1, c1 in component_sets[left]
                for r2, c2 in component_sets[right]
            ):
                errors.append(
                    f"objects {left} and {right} lack one-cell including-diagonal padding"
                )

    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, requested in meta["overrides"].items():
            if requested is not None and name in AXES and observed[name] != requested:
                errors.append(
                    f"override {name}={requested!r} realized as {observed[name]!r}"
                )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Recognize the complete canonical size/count/mask envelope."""
    errors = list(self_check(grid))
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len(_components_nonzero(grid)))
    if profile not in _CANONICAL_PROFILES:
        errors.append("grid dimensions/object count are outside canonical profiles")
    masks = [_normalize(cells) for _, cells in _components_nonzero(grid)]
    if any(mask not in _CANONICAL_MASKS for mask in masks):
        errors.append("canonical-like profile contains a noncanonical object mask")
    return sorted(set(errors))


def rule_mirror(grid) -> Grid:
    """Python mirror of the pinned Racket authority."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for _, cells in _components_nonzero(grid):
        output_color = _CLASS_COLOR[_symmetry_class(cells)]
        for row, col in cells:
            output[row][col] = output_color
    return output


def _canonical_mask_lookup(grid) -> Grid:
    """Plausible wrong rule that memorizes the four canonical masks exactly."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    lookup = {
        _BOTH_CANONICAL: 8,
        _LR_CANONICAL: 2,
        _UD_CANONICAL: 3,
        _NONE_CANONICAL: 4,
    }
    for _, cells in _components_nonzero(grid):
        output_color = lookup.get(_normalize(cells), 4)
        for row, col in cells:
            output[row][col] = output_color
    return output


def _refutes_canonical_mask_shortcut(grid) -> bool:
    try:
        return self_check(grid) == [] and rule_mirror(grid) != _canonical_mask_lookup(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "canonical_mask_shortcut_counterexample": _refutes_canonical_mask_shortcut,
}
SEMANTIC_RIVALS = {
    "canonical_mask_lookup": _canonical_mask_lookup,
}
WITNESS_RIVALS = {
    "canonical_mask_shortcut_counterexample": ["canonical_mask_lookup"],
}
CANONICAL_SHORTCUTS = {
    "canonical_mask_lookup": _canonical_mask_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Verify examples are lawful and refute every declared lesson competitor."""
    errors: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demonstration {index} is not an input/output pair")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            errors.append(f"demonstration {index} invalid: {'; '.join(input_errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demonstration {index} output disagrees with authority mirror")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is not an input/output pair")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            errors.append("query invalid: " + "; ".join(query_errors))
        elif "output" in query and rule_mirror(query["input"]) != query["output"]:
            errors.append("query output disagrees with authority mirror")
    if errors:
        return errors

    survivors = [
        name
        for name, competitor in LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair["output"] for pair in demos)
    ]
    if survivors:
        return [
            "demonstrations do not refute declared competitor(s): "
            + ", ".join(sorted(survivors))
        ]
    return []
