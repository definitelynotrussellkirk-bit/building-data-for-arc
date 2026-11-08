"""Constructive generator for the ARC task ``Axis-Key Reflect``.

The top-left cell is a key.  Remove that key, crop the remaining non-zero
content, then reflect the crop left/right for key ``1`` or up/down for key
``2``.

Every advertised axis is exact, observable from the returned grid, and valid
throughout the full Cartesian product.  The four-profile lesson schedule is
chosen so every three-example window demonstrates both keys and refutes the
strongest axis shortcuts exposed by the canonical data.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e92a4eef51d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "bf7a0a12ef08"
SUMMARY = (
    "A corner key selects horizontal or vertical reflection of an asymmetric "
    "cropped object."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "key1_aligned_landscape",
    "key2_conflict_landscape",
    "key1_conflict_portrait",
    "key2_aligned_square",
)
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "background is 0",
    "the only non-zero cell in row 0 or column 0 is the key at (0,0)",
    "key 1 means reflect the cropped object left/right",
    "key 2 means reflect the cropped object up/down",
    "the selected reflection visibly changes the crop",
]

AXES = {
    "grid_h": {"type": "int", "default": "linked profile, then broad cycle", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "linked profile, then broad cycle", "valid": "7..14"},
    "key": {"type": "int", "default": "linked profile", "valid": "1..2"},
    "blob_size": {"type": "int", "default": "cycle 4..7", "valid": "4..7"},
    "n_distinct_colors": {"type": "int", "default": "cycle 1..3", "valid": "1..3"},
    "n_components": {"type": "int", "default": "cycle 1..2", "valid": "1..2"},
    "aspect_relation": {
        "type": "enum",
        "default": "linked profile",
        "valid": ["aligned", "conflict"],
    },
}

_INT_BOUNDS = {
    "grid_h": (7, 14),
    "grid_w": (7, 14),
    "key": (1, 2),
    "blob_size": (4, 7),
    "n_distinct_colors": (1, 3),
    "n_components": (1, 2),
}
_ASPECT_RELATIONS = ("aligned", "conflict")
_DIFFICULTIES = (None, "easy", "medium", "hard")

# Every template is wider than tall, is asymmetric under both horizontal and
# vertical reflection, and has exactly the requested number of 4-components.
# Tall variants are exact transposes, so all 4*2 shape-axis combinations are
# constructive even on the minimum 7x7 canvas.
_WIDE_SHAPES: dict[tuple[int, int], frozenset[tuple[int, int]]] = {
    (4, 1): frozenset({(0, 0), (0, 1), (0, 2), (1, 0)}),
    (4, 2): frozenset({(0, 0), (0, 1), (1, 0), (1, 2)}),
    (5, 1): frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)}),
    (5, 2): frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 3)}),
    (6, 1): frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)}),
    (6, 2): frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 3)}),
    (7, 1): frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)}),
    (7, 2): frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 4)}),
}

_CANONICAL_DIMENSIONS = {
    SCHEDULE_PROFILES[0]: (7, 8),
    SCHEDULE_PROFILES[1]: (7, 9),
    SCHEDULE_PROFILES[2]: (8, 7),
    SCHEDULE_PROFILES[3]: (8, 8),
}
_PROFILE_KEY_RELATION = {
    SCHEDULE_PROFILES[0]: (1, "aligned"),
    SCHEDULE_PROFILES[1]: (2, "conflict"),
    SCHEDULE_PROFILES[2]: (1, "conflict"),
    SCHEDULE_PROFILES[3]: (2, "aligned"),
}

_LANDSCAPE_DIMENSIONS = {
    "easy": ((7, 8), (7, 9), (8, 9), (8, 10), (9, 10), (7, 10), (9, 11), (8, 11)),
    "medium": ((8, 9), (8, 10), (9, 10), (9, 11), (10, 11), (8, 12), (10, 12), (11, 12)),
    "hard": ((10, 11), (10, 12), (11, 12), (11, 13), (12, 13), (10, 14), (12, 14), (13, 14)),
}
_SQUARE_DIMENSIONS = {
    "easy": ((7, 7), (8, 8), (9, 9), (10, 10), (11, 11)),
    "medium": ((8, 8), (9, 9), (10, 10), (11, 11), (12, 12)),
    "hard": ((10, 10), (11, 11), (12, 12), (13, 13), (14, 14)),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the linked profile; seed and difficulty never disturb rotation."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _profile_defaults(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    profile_index = SCHEDULE_PROFILES.index(profile)
    cycle = int(sample_index) // LESSON_SCHEDULE_PERIOD
    key, relation = _PROFILE_KEY_RELATION[profile]

    # Re-emit the four canonical canvas profiles regularly in every band.  The
    # intervening cycles enumerate a broad, relation-preserving dimension set.
    if profile_index == 0 or cycle % 8 == 0:
        height, width = _CANONICAL_DIMENSIONS[profile]
    else:
        band = "medium" if difficulty is None else difficulty
        if profile_index in (0, 1):
            candidates = _LANDSCAPE_DIMENSIONS[band]
        elif profile_index == 2:
            candidates = tuple((w, h) for h, w in _LANDSCAPE_DIMENSIONS[band])
        else:
            candidates = _SQUARE_DIMENSIONS[band]
        height, width = candidates[(cycle + 3 * profile_index) % len(candidates)]

    # Cycle every constructive value without relying on random coverage.
    return {
        "grid_h": height,
        "grid_w": width,
        "key": key,
        "blob_size": 4 + ((cycle + profile_index) % 4),
        "n_distinct_colors": (
            2 if profile_index == 0 else 1 + ((cycle + 2 * profile_index) % 3)
        ),
        "n_components": 1 + ((cycle + profile_index) % 2),
        "aspect_relation": relation,
    }


def _validate_request(difficulty, overrides: dict[str, Any]) -> dict[str, Any]:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    active = {name: value for name, value in overrides.items() if value is not None}
    for name, (low, high) in _INT_BOUNDS.items():
        if name not in active:
            continue
        value = active[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")
    if "aspect_relation" in active:
        value = active["aspect_relation"]
        if not isinstance(value, str):
            raise TypeError("aspect_relation must be a string")
        if value not in _ASPECT_RELATIONS:
            raise ValueError(
                f"aspect_relation={value!r} is not one of {_ASPECT_RELATIONS!r}"
            )
    return active


def _draw_int_axis(ctx, active: dict[str, Any], label: str, default: int) -> int:
    low, high = _INT_BOUNDS[label]
    if label in active:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_int_strict(label, default, default)


def _draw_choice_axis(ctx, active: dict[str, Any], label: str, default: str) -> str:
    if label in active:
        return ctx.draw_choice(label, _ASPECT_RELATIONS)
    return ctx.draw_choice(label, (default,))


def _shape_orientation(key: int, relation: str) -> str:
    keyed = "wide" if key == 1 else "tall"
    if relation == "aligned":
        return keyed
    return "tall" if keyed == "wide" else "wide"


def _shape_cells(blob_size: int, n_components: int, orientation: str) -> set[tuple[int, int]]:
    cells = set(_WIDE_SHAPES[(blob_size, n_components)])
    if orientation == "tall":
        cells = {(col, row) for row, col in cells}
    return cells


def _shape_extent(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _body_palette(key: int, count: int, rng) -> list[int]:
    # Always include colour 2 when it is not the key.  This deliberately keeps
    # a canonical colour in broad sampling rather than silently excluding it.
    legal = [color for color in range(1, 10) if color != key]
    anchor = 2 if key != 2 else 1
    tail = [color for color in legal if color != anchor]
    rng.shuffle(tail)
    return [anchor, *tail[: count - 1]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful scene; all override axes are exact and observable."""
    active = _validate_request(difficulty, overrides)
    defaults = _profile_defaults(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )

    height = _draw_int_axis(ctx, active, "grid_h", defaults["grid_h"])
    width = _draw_int_axis(ctx, active, "grid_w", defaults["grid_w"])
    key = _draw_int_axis(ctx, active, "key", defaults["key"])
    blob_size = _draw_int_axis(ctx, active, "blob_size", defaults["blob_size"])
    n_colors = _draw_int_axis(
        ctx, active, "n_distinct_colors", defaults["n_distinct_colors"]
    )
    n_components = _draw_int_axis(
        ctx, active, "n_components", defaults["n_components"]
    )
    relation = _draw_choice_axis(
        ctx, active, "aspect_relation", defaults["aspect_relation"]
    )

    orientation = _shape_orientation(key, relation)
    local_cells = _shape_cells(blob_size, n_components, orientation)
    shape_h, shape_w = _shape_extent(local_cells)
    if shape_h > height - 1 or shape_w > width - 1:  # defensive; bounds make this unreachable
        raise ValueError("requested canvas cannot contain the selected shape")

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    value_rng = ctx.draw_rng("body_values")
    row0 = layout_rng.randint(1, height - shape_h)
    col0 = layout_rng.randint(1, width - shape_w)

    absolute_cells = [(row0 + row, col0 + col) for row, col in sorted(local_cells)]
    value_rng.shuffle(absolute_cells)
    palette = _body_palette(key, n_colors, palette_rng)

    grid = full_grid(height, width, 0)
    grid[0][0] = key
    for index, (row, col) in enumerate(absolute_cells):
        grid[row][col] = palette[index % len(palette)]

    errors = self_check(grid)
    if errors:  # construction invariant, not a retry path
        raise AssertionError(f"constructive generator emitted invalid grid: {errors}")
    return grid


def _grid_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _body_cells(grid) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0 and (row, col) != (0, 0)
    ]


def _component_count(cells: Iterable[tuple[int, int]]) -> int:
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        start = unseen.pop()
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
    return count


def _content_crop_without_key(grid):
    shape = _grid_shape(grid)
    if shape is None:
        return None
    rest = [list(row) for row in grid]
    rest[0][0] = 0
    cells = [
        (row, col)
        for row, line in enumerate(rest)
        for col, value in enumerate(line)
        if value != 0
    ]
    if not cells:
        return None
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [line[col0 : col1 + 1] for line in rest[row0 : row1 + 1]]


def _horizontal(crop):
    return [list(reversed(row)) for row in crop]


def _vertical(crop):
    return [list(row) for row in reversed(crop)]


def _reference_output(grid):
    """Independent Python mirror of the pinned Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid axis-key scene: " + "; ".join(errors))
    crop = _content_crop_without_key(grid)
    assert crop is not None
    return _horizontal(crop) if grid[0][0] == 1 else _vertical(crop)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the shared canonical/generated domain without raising."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of non-empty rows"]
    height, width = shape
    errors: list[str] = []
    if not 7 <= height <= 14:
        errors.append(f"grid height {height} not in [7,14]")
    if not 7 <= width <= 14:
        errors.append(f"grid width {width} not in [7,14]")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [
                    f"cell ({row_index},{col_index}) must be an integer ARC colour 0..9"
                ]

    key = grid[0][0]
    if key not in (1, 2):
        errors.append("corner key must be 1 or 2")
    if any(grid[0][col] != 0 for col in range(1, width)):
        errors.append("row 0 may contain only the corner key")
    if any(grid[row][0] != 0 for row in range(1, height)):
        errors.append("column 0 may contain only the corner key")

    cells = _body_cells(grid)
    if not 4 <= len(cells) <= 7:
        errors.append(f"body size {len(cells)} not in [4,7]")
    colors = {grid[row][col] for row, col in cells}
    if not 1 <= len(colors) <= 3:
        errors.append(f"body colour count {len(colors)} not in [1,3]")
    if key in colors:
        errors.append("body colours must not reuse the corner key colour")
    if cells:
        components = _component_count(cells)
        if not 1 <= components <= 2:
            errors.append(f"body component count {components} not in [1,2]")
        crop = _content_crop_without_key(grid)
        assert crop is not None
        crop_h, crop_w = len(crop), len(crop[0])
        if crop_h == crop_w:
            errors.append("body crop must have a visible wide or tall aspect")
        if key == 1 and _horizontal(crop) == crop:
            errors.append("key-1 horizontal reflection must visibly change the crop")
        if key == 2 and _vertical(crop) == crop:
            errors.append("key-2 vertical reflection must visibly change the crop")
    else:
        errors.append("expected a non-key body")
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """Generated scenes and all four canonical pairs share this exact domain."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised control exactly from a generated grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe overrides from invalid grid: {errors}")
    cells = _body_cells(grid)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    crop_h = max(rows) - min(rows) + 1
    crop_w = max(cols) - min(cols) + 1
    orientation = "wide" if crop_w > crop_h else "tall"
    key = grid[0][0]
    keyed_orientation = "wide" if key == 1 else "tall"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "key": key,
        "blob_size": len(cells),
        "n_distinct_colors": len({grid[row][col] for row, col in cells}),
        "n_components": _component_count(cells),
        "aspect_relation": "aligned" if orientation == keyed_orientation else "conflict",
    }


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    observed = observe_overrides(grid)
    observed.update(
        {
            "canvas_relation": _canvas_relation(grid),
            "crop_relation": _crop_relation(grid),
            "truth_axis": "horizontal" if grid[0][0] == 1 else "vertical",
        }
    )
    return observed


def _safe_crop(grid):
    crop = _content_crop_without_key(grid)
    return deepcopy(crop) if crop is not None else None


def _rival_always_horizontal(grid):
    crop = _safe_crop(grid)
    return None if crop is None else _horizontal(crop)


def _rival_always_vertical(grid):
    crop = _safe_crop(grid)
    return None if crop is None else _vertical(crop)


def _crop_relation(grid) -> str | None:
    crop = _content_crop_without_key(grid)
    if crop is None:
        return None
    height, width = len(crop), len(crop[0])
    return "landscape" if width > height else "portrait" if height > width else "square"


def _canvas_relation(grid) -> str | None:
    shape = _grid_shape(grid)
    if shape is None:
        return None
    height, width = shape
    return "landscape" if width > height else "portrait" if height > width else "square"


def _rival_crop_aspect_axis(grid):
    crop = _safe_crop(grid)
    relation = _crop_relation(grid)
    if crop is None or relation is None:
        return None
    return _horizontal(crop) if relation == "landscape" else _vertical(crop)


def _rival_canvas_aspect_axis(grid):
    crop = _safe_crop(grid)
    relation = _canvas_relation(grid)
    if crop is None or relation is None:
        return None
    return _horizontal(crop) if relation == "landscape" else _vertical(crop)


def _valid_witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and bool(predicate(observed))


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "key1_branch": lambda grid: _valid_witness(grid, lambda obs: obs["key"] == 1),
    "key2_branch": lambda grid: _valid_witness(grid, lambda obs: obs["key"] == 2),
    "crop_axis_conflict": lambda grid: _valid_witness(
        grid, lambda obs: obs["aspect_relation"] == "conflict"
    ),
    "canvas_axis_conflict": lambda grid: _valid_witness(
        grid,
        lambda obs: (
            (obs["truth_axis"] == "horizontal")
            != (obs["canvas_relation"] == "landscape")
        ),
    ),
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "always_horizontal": _rival_always_horizontal,
    "always_vertical": _rival_always_vertical,
    "crop_aspect_axis": _rival_crop_aspect_axis,
    "canvas_aspect_axis": _rival_canvas_aspect_axis,
}

WITNESS_RIVALS = {
    "key1_branch": ["always_vertical"],
    "key2_branch": ["always_horizontal"],
    "crop_axis_conflict": ["crop_aspect_axis"],
    "canvas_axis_conflict": ["canvas_aspect_axis"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All three canonical demonstrations and the canonical test happen to map
    # landscape canvases to horizontal reflection and portrait/square canvases
    # to vertical reflection.  Generated conflict profiles break that shortcut.
    "canvas_aspect_axis": _rival_canvas_aspect_axis,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report unresolved competitors that would change the query answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query input is invalid: {query_errors[0]}"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        truth = _reference_output(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output does not match the selected rule")
    if reasons:
        return reasons

    query_truth = _reference_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if survives and rival(query["input"]) != query_truth:
            reasons.append(
                f"demonstrations remain compatible with rival {name!r}, "
                "which changes the query answer"
            )
    return reasons
