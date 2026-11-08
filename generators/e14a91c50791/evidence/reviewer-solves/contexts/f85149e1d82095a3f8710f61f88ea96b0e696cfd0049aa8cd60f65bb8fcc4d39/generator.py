"""Generator for bank task 7f8a290afe75:H83 / e14a91c50791.

Group color-2 components by normalized shape up to rotation, but not
reflection.  Exactly one class has odd multiplicity; every component in that
class has its bounding box filled with color 7.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at


GENERATOR_ID = "e14a91c50791"
VERSION = "3.0.0"
TASK_ID = "e14a91c50791"
RULE_HASH = "c7f37a119f36"

SUMMARY = (
    "Place two to four rotation-classes of separate red polyominoes; exactly "
    "one class occurs once or three times and every other class occurs twice. "
    "The rule fills every odd-class object's bounding box with orange."
)

INVARIANTS = [
    "all foreground input cells are color 2 on background 0",
    "components have 2..6 cells and fit within 3x3 bounding boxes",
    "there are exactly 2..4 shape classes up to rotation, not reflection",
    "exactly one class has odd multiplicity; every other class occurs twice",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 13..26",
        "valid": "13..26",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 13..26",
        "valid": "13..26",
    },
    "n_classes": {
        "type": "int",
        "default": "difficulty-aware rng 2..4",
        "valid": "2..4",
    },
}

_VALID_H = (13, 26)
_VALID_W = (13, 26)
_VALID_CLASSES = (2, 4)
_PROFILE_PRIOR = 0.08
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    return _norm((c, height - 1 - r) for r, c in cells)


def _rotate(cells, turns):
    current = _norm(cells)
    for _ in range(turns % 4):
        current = _rotate_cw(current)
    return current


def _rotation_key(cells):
    rotations = []
    current = _norm(cells)
    for _ in range(4):
        rotations.append(current)
        current = _rotate_cw(current)
    return min(rotations)


def _shape_dimensions(cells):
    cells = _norm(cells)
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _enumerate_shape_catalog():
    orientations = {((0, 0),)}
    by_size = {}
    for size in range(2, 7):
        expanded = set()
        for shape in orientations:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in _CARDINALS:
                    candidate = (r + dr, c + dc)
                    if candidate in occupied:
                        continue
                    grown = _norm((*shape, candidate))
                    height, width = _shape_dimensions(grown)
                    if height <= 3 and width <= 3:
                        expanded.add(grown)
        orientations = expanded
        by_size[size] = tuple(
            sorted({_rotation_key(shape) for shape in orientations})
        )
    return by_size


_SHAPE_CATALOG = _enumerate_shape_catalog()

# Canvas height, width, then (rotation-canonical shape, multiplicity) classes.
_PROFILE_SPECS = (
    (
        14,
        16,
        (
            (((0, 0), (0, 1)), 2),
            (((0, 0), (0, 1), (0, 2), (1, 0)), 3),
            (((0, 0), (0, 1), (1, 0), (1, 1)), 2),
        ),
    ),
    (
        13,
        15,
        (
            (((0, 0), (0, 1), (0, 2), (1, 1)), 2),
            (((0, 0), (0, 1), (1, 0), (1, 1)), 2),
            (((0, 0), (0, 1), (1, 1), (1, 2)), 3),
        ),
    ),
    (
        15,
        14,
        (
            (((0, 0), (0, 1)), 2),
            (((0, 0), (0, 1), (0, 2), (1, 0)), 2),
            (((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)), 3),
        ),
    ),
    (
        14,
        14,
        (
            (((0, 0), (0, 1), (0, 2)), 2),
            (((0, 0), (0, 1), (0, 2), (1, 1)), 3),
            (((0, 0), (0, 1), (1, 0), (1, 1)), 2),
        ),
    ),
    (
        15,
        15,
        (
            (((0, 0), (0, 1), (1, 0), (1, 1)), 2),
            (((0, 0), (0, 1), (1, 1), (1, 2)), 2),
            (((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)), 3),
        ),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _components4(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _CARDINALS:
                neighbor = (r + dr, c + dc)
                if (
                    0 <= neighbor[0] < h
                    and 0 <= neighbor[1] < w
                    and neighbor in remaining
                ):
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(components)


def _group_components(components):
    groups = {}
    for cells in components:
        key = _rotation_key(cells)
        groups.setdefault(key, []).append(cells)
    return {
        key: tuple(values)
        for key, values in groups.items()
    }


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    components = _components4(grid)
    groups = _group_components(components)
    return {
        "grid": grid,
        "h": len(grid),
        "w": len(grid[0]) if grid else 0,
        "components": components,
        "groups": groups,
        "odd_keys": tuple(
            sorted(
                key
                for key, values in groups.items()
                if len(values) % 2 == 1
            )
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 13..26")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 13..26")
    if any(
        type(value) is not int or value not in (0, 2)
        for row in coerced
        for value in row
    ):
        errors.append("input values must be integer colors 0 or 2")

    scene = _analyze_scene(coerced)
    if not (_VALID_CLASSES[0] <= len(scene["groups"]) <= _VALID_CLASSES[1]):
        errors.append("scene must contain exactly 2..4 rotation classes")
    if len(scene["odd_keys"]) != 1:
        errors.append("scene must contain exactly one odd-frequency class")
    for key, values in scene["groups"].items():
        if not 2 <= len(key) <= 6:
            errors.append("every component must contain 2..6 cells")
        height, width = _shape_dimensions(key)
        if height > 3 or width > 3:
            errors.append("every component bbox must fit within 3x3")
        if not 1 <= len(values) <= 3:
            errors.append("every class multiplicity must be in 1..3")
        if len(values) % 2 == 0 and len(values) != 2:
            errors.append("every even-frequency class must occur twice")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "n_classes": len(scene["groups"]),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    odd_key = scene["odd_keys"][0]
    for cells in scene["groups"][odd_key]:
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                output[r][c] = 7
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        tuple(
            sorted(
                (key, len(values))
                for key, values in scene["groups"].items()
            )
        ),
    )


def _profile_signature(profile):
    h, w, classes = profile
    return (
        h,
        w,
        tuple(
            sorted(
                (_rotation_key(shape), count)
                for shape, count in classes
            )
        ),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _boxes_separated(first, second):
    return (
        first[2] + 1 < second[0]
        or second[2] + 1 < first[0]
        or first[3] + 1 < second[1]
        or second[3] + 1 < first[1]
    )


def _random_placements(h, w, shapes, rng):
    candidates = []
    for shape in shapes:
        height, width = _shape_dimensions(shape)
        options = [
            (r, c, r + height - 1, c + width - 1)
            for r in range(h - height + 1)
            for c in range(w - width + 1)
        ]
        rng.shuffle(options)
        candidates.append(options)
    nodes = 0

    def search(index, boxes):
        nonlocal nodes
        if index == len(shapes):
            return tuple(boxes)
        for box in candidates[index]:
            nodes += 1
            if nodes > 200_000:
                return None
            if all(_boxes_separated(box, prior) for prior in boxes):
                result = search(index + 1, (*boxes, box))
                if result is not None:
                    return result
        return None

    return search(0, ())


def _three_band_starts(length):
    return tuple(
        values
        for values in combinations(range(length - 2), 3)
        if values[1] - values[0] >= 4
        and values[2] - values[1] >= 4
    )


def _slot_fallback(h, w, shapes, rng):
    rows = rng.choice(_three_band_starts(h))
    cols = rng.choice(_three_band_starts(w))
    slots = [(r, c) for r in rows for c in cols]
    rng.shuffle(slots)
    boxes = []
    for shape, (slot_r, slot_c) in zip(shapes, slots):
        height, width = _shape_dimensions(shape)
        top = slot_r + rng.randint(0, 3 - height)
        left = slot_c + rng.randint(0, 3 - width)
        boxes.append(
            (top, left, top + height - 1, left + width - 1)
        )
    return tuple(boxes)


def _draw_scene(h, w, classes, rng):
    shapes = []
    for base, count in classes:
        for _ in range(count):
            shapes.append(_rotate(base, rng.randrange(4)))
    rng.shuffle(shapes)
    placements = _random_placements(h, w, shapes, rng)
    if placements is None:
        placements = _slot_fallback(h, w, shapes, rng)
    grid = full_grid(h, w, 0)
    for shape, box in zip(shapes, placements):
        paint_at(grid, box[0], box[1], shape, 2)
    return grid


def _general_classes(n_classes, band, rng):
    size_range = {
        "easy": range(2, 5),
        "medium": range(2, 6),
        "hard": range(3, 7),
    }[band]
    pool = [
        shape
        for size in size_range
        for shape in _SHAPE_CATALOG[size]
    ]
    rng.shuffle(pool)
    bases = pool[:n_classes]
    target_index = rng.randrange(n_classes)
    target_count = rng.choice((1, 3))
    return tuple(
        (shape, target_count if index == target_index else 2)
        for index, shape in enumerate(bases)
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, classes = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("n_classes", len(classes), len(classes))
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (13, 17),
                    "medium": (15, 21),
                    "hard": (20, 26),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (13, 17),
                    "medium": (15, 21),
                    "hard": (20, 26),
                }[band],
            )
        if overrides.get("n_classes") is not None:
            n_classes = ctx.draw_int("n_classes", *_VALID_CLASSES)
        else:
            n_classes = ctx.draw_int(
                "n_classes",
                *{
                    "easy": (2, 2),
                    "medium": (2, 3),
                    "hard": (3, 4),
                }[band],
            )
        classes = _general_classes(
            n_classes,
            band,
            ctx.draw_rng("classes"),
        )

    grid = _draw_scene(h, w, classes, ctx.draw_rng("layout"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
