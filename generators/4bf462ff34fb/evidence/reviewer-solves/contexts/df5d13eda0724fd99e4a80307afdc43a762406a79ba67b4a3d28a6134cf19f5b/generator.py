"""Semantic generator for ``4bf462ff34fb``.

Every 4-connected blue-1 component that touches the top edge and no other
edge is recolored green-3.  Blue components with any other border signature,
interior blue components, and non-blue distractors remain unchanged.

A default-only linked-profile prior reconstructs the five public input
profiles from component morphology and border signatures, while randomized
placements and distractor colors prevent full-grid replay.  The remaining
draws deliberately include top-corner blue near-misses so "touches top" is
not a reliable shortcut for "touches only top".
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable, NamedTuple, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.shape import (
    H_LINE_3,
    L_TROMINO_NE,
    L_TROMINO_NW,
    L_TROMINO_SE,
    L_TROMINO_SW,
    SQUARE_2X2,
    T_TETROMINO,
    V_LINE_3,
    rect_cells,
    shape_dims,
)

GENERATOR_ID = "4bf462ff34fb"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "284791f05f91"

SUMMARY = (
    "Recolor exactly the blue components whose border signature is top-only; "
    "preserve blue components touching another edge, interior blue objects, "
    "and all non-blue distractors."
)

INVARIANTS = [
    "background is modal black 0 and input green 3 is absent",
    "at least one blue component touches the top border and no other border",
    "at least one blue component is a non-target because it is interior or touches another border",
    "at least one non-blue distractor component is present",
    "canvas height and width are each within the declared 8..18 range",
]

COUNTER_HYPOTHESES = [
    "recolor every blue component touching the top border",
    "recolor every blue border component regardless of which border it touches",
    "recolor blue objects by size or shape rather than border signature",
    "recolor the first or leftmost blue object",
    "treat a non-blue border object as an answer marker",
    "predict the changed cells from canvas dimensions or component counts alone",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_VALID_H = (8, 18)
_VALID_W = (8, 18)
_BAND_BOUNDS = {
    "easy": ((8, 11), (8, 11)),
    "medium": ((10, 15), (10, 15)),
    "hard": ((14, 18), (14, 18)),
}
_PROFILE_PRIOR = 0.32
_PLACEMENT_NODE_BUDGET = 512

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 8..18; linked-profile prior uses 10 or 12",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 8..18; linked-profile prior uses 10..12",
        "valid": "8..18",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

_SINGLE = ((0, 0),)
_V2 = ((0, 0), (1, 0))
_H2 = ((0, 0), (0, 1))
_RECT_2X3 = tuple(rect_cells(2, 3))
_TOP3_LEFT = ((0, 0), (0, 1), (0, 2), (1, 0))

_SHAPES_SIMPLE = (
    _SINGLE,
    _V2,
    _H2,
    tuple(L_TROMINO_NE),
    tuple(L_TROMINO_NW),
    tuple(L_TROMINO_SE),
    tuple(L_TROMINO_SW),
)
_SHAPES_ALL = _SHAPES_SIMPLE + (
    tuple(V_LINE_3),
    tuple(H_LINE_3),
    tuple(SQUARE_2X2),
    tuple(T_TETROMINO),
    _RECT_2X3,
    _TOP3_LEFT,
)

_BORDER_ORDER = "TBLR"
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


class _ObjectSpec(NamedTuple):
    role: str
    border: str
    shape: tuple[tuple[int, int], ...]
    color: int = 1


class _PlacementCandidate(NamedTuple):
    origin: tuple[int, int]
    cells: frozenset[tuple[int, int]]
    fence: frozenset[tuple[int, int]]


def _spec(role: str, border: str, shape: Sequence[tuple[int, int]]) -> _ObjectSpec:
    return _ObjectSpec(role, border, tuple(sorted(shape)), 1 if role == "blue" else 4)


# Complete linked component profiles extracted from all four train inputs and
# the held-out test input.  Exact placements and distractor colors are nuisance
# variables; dimensions, role, border signature, and normalized morphology are
# preserved jointly.
_PROFILE_SPECS: tuple[tuple[int, int, tuple[_ObjectSpec, ...]], ...] = (
    (
        10,
        12,
        (
            _spec("blue", "T", _V2),
            _spec("blue", "T", L_TROMINO_SW),
            _spec("blue", "T", L_TROMINO_SW),
            _spec("blue", "I", V_LINE_3),
            _spec("blue", "L", _SINGLE),
            _spec("distractor", "I", V_LINE_3),
            _spec("distractor", "I", _SINGLE),
            _spec("distractor", "I", L_TROMINO_NE),
            _spec("distractor", "I", L_TROMINO_SW),
        ),
    ),
    (
        12,
        10,
        (
            _spec("blue", "T", _SINGLE),
            _spec("blue", "T", _SINGLE),
            _spec("blue", "T", L_TROMINO_SW),
            _spec("blue", "R", _SINGLE),
            _spec("blue", "I", V_LINE_3),
            _spec("blue", "B", _V2),
            _spec("blue", "B", L_TROMINO_NE),
            _spec("distractor", "I", L_TROMINO_NE),
            _spec("distractor", "R", L_TROMINO_NE),
        ),
    ),
    (
        12,
        10,
        (
            _spec("blue", "T", _RECT_2X3),
            _spec("blue", "T", _H2),
            _spec("blue", "R", _V2),
            _spec("blue", "L", L_TROMINO_SW),
            _spec("blue", "L", _V2),
            _spec("distractor", "L", L_TROMINO_SW),
            _spec("distractor", "I", SQUARE_2X2),
        ),
    ),
    (
        12,
        10,
        (
            _spec("blue", "T", _TOP3_LEFT),
            _spec("blue", "T", L_TROMINO_SW),
            _spec("blue", "I", SQUARE_2X2),
            _spec("blue", "I", V_LINE_3),
            _spec("blue", "B", L_TROMINO_NE),
            _spec("blue", "B", _V2),
            _spec("distractor", "TL", L_TROMINO_SW),
            _spec("distractor", "I", SQUARE_2X2),
            _spec("distractor", "L", L_TROMINO_SW),
            _spec("distractor", "I", _V2),
        ),
    ),
    (
        12,
        11,
        (
            _spec("blue", "T", _SINGLE),
            _spec("blue", "T", T_TETROMINO),
            _spec("blue", "R", _V2),
            _spec("blue", "B", L_TROMINO_NE),
            _spec("blue", "BR", L_TROMINO_SW),
            _spec("distractor", "I", SQUARE_2X2),
            _spec("distractor", "R", _SINGLE),
        ),
    ),
)


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _coerce_grid(grid) -> list[list[int]]:
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value for value in row]
        for row in grid
    ]


def _components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, tuple[tuple[int, int], ...]]] = []
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
                for dr, dc in _CARDINAL:
                    neighbor = rr + dr, cc + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            found.append((color, tuple(sorted(cells))))
    return found


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _canonical_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize_shape(cells)
    width = max(col for _row, col in normalized) + 1
    reflected = tuple(sorted((row, width - 1 - col) for row, col in normalized))
    return min(normalized, reflected)


def _border_signature(cells: Iterable[tuple[int, int]], height: int, width: int) -> str:
    cells = tuple(cells)
    flags = {
        "T": any(row == 0 for row, _col in cells),
        "B": any(row == height - 1 for row, _col in cells),
        "L": any(col == 0 for _row, col in cells),
        "R": any(col == width - 1 for _row, col in cells),
    }
    return "".join(name for name in _BORDER_ORDER if flags[name]) or "I"


def _profile_signature_from_specs(
    height: int,
    width: int,
    specs: Sequence[_ObjectSpec],
) -> tuple:
    components = tuple(
        sorted(
            (
                spec.role,
                spec.border,
                _canonical_shape(spec.shape),
            )
            for spec in specs
        )
    )
    return height, width, components


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature_from_specs(height, width, specs)
    for height, width, specs in _PROFILE_SPECS
)


def scene_signature(grid) -> tuple | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return None
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return None
    source = _coerce_grid(grid)
    height = len(source)
    width = len(source[0])
    components = tuple(
        sorted(
            (
                "blue" if color == 1 else "distractor",
                _border_signature(cells, height, width),
                _canonical_shape(cells),
            )
            for color, cells in _components(source)
        )
    )
    return height, width, components


def canonical_profile_signature(grid) -> tuple | None:
    signature = scene_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) is not None


def _axis_origins(
    limit: int,
    extent: int,
    *,
    touches_low: bool,
    touches_high: bool,
) -> range | tuple[int, ...]:
    max_origin = limit - extent
    if max_origin < 0:
        return ()
    if touches_low and touches_high:
        return (0,) if max_origin == 0 else ()
    if touches_low:
        return (0,) if max_origin > 0 else ()
    if touches_high:
        return (max_origin,) if max_origin > 0 else ()
    return range(1, max_origin)


def _candidate_origins(
    height: int,
    width: int,
    shape: Sequence[tuple[int, int]],
    border: str,
) -> list[tuple[int, int]]:
    # Every task-local shape is normalized and occupies all four sides of its
    # bounding box.  Its exact border signature therefore depends only on the
    # origin and bounding-box dimensions; materializing every translated cell
    # for every canvas position made the override matrix needlessly quadratic.
    shape_height, shape_width = shape_dims(shape)
    rows = _axis_origins(
        height,
        shape_height,
        touches_low="T" in border,
        touches_high="B" in border,
    )
    cols = _axis_origins(
        width,
        shape_width,
        touches_low="L" in border,
        touches_high="R" in border,
    )
    return [(row, col) for row in rows for col in cols]


def _assign_distractor_colors(
    specs: Sequence[_ObjectSpec], rng
) -> tuple[_ObjectSpec, ...]:
    distractor_count = sum(spec.role != "blue" for spec in specs)
    palette = list((4, 5, 6, 7, 8, 9))
    rng.shuffle(palette)
    if distractor_count > len(palette):
        raise ValueError("too many distractor components for distinct colors")
    colors = iter(palette[:distractor_count])
    return tuple(
        _ObjectSpec(
            spec.role,
            spec.border,
            spec.shape,
            1 if spec.role == "blue" else next(colors),
        )
        for spec in specs
    )


def _place_specs(
    height: int,
    width: int,
    specs: Sequence[_ObjectSpec],
    rng,
) -> list[list[int]] | None:
    prepared = _assign_distractor_colors(specs, rng)
    candidates: list[list[_PlacementCandidate]] = []
    for spec in prepared:
        origins = _candidate_origins(height, width, spec.shape, spec.border)
        rng.shuffle(origins)
        if not origins:
            return None
        choices: list[_PlacementCandidate] = []
        for origin in origins:
            cells = frozenset(
                (origin[0] + dr, origin[1] + dc)
                for dr, dc in spec.shape
            )
            fence = frozenset(
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in _CARDINAL
                if (row + dr, col + dc) not in cells
            )
            choices.append(_PlacementCandidate(origin, cells, fence))
        candidates.append(choices)

    static_order = sorted(
        range(len(prepared)),
        key=lambda index: (len(candidates[index]), prepared[index].role != "blue"),
    )
    occupied: set[tuple[int, int]] = set()
    by_color: dict[int, set[tuple[int, int]]] = {}
    placements: dict[int, _PlacementCandidate] = {}
    remaining = set(static_order)
    nodes = 0

    def viable(index: int) -> list[_PlacementCandidate]:
        same_color = by_color.setdefault(prepared[index].color, set())
        return [
            candidate
            for candidate in candidates[index]
            if not candidate.cells & occupied
            and not candidate.fence & same_color
        ]

    def visit() -> bool:
        nonlocal nodes
        nodes += 1
        if nodes > _PLACEMENT_NODE_BUDGET:
            return False
        if not remaining:
            return True

        index = -1
        choices: list[_PlacementCandidate] | None = None
        # Dynamic minimum-remaining-values plus forward checking prevents the
        # search from exploring thousands of placements before discovering
        # that a fixed border object has no legal location.
        for candidate_index in static_order:
            if candidate_index not in remaining:
                continue
            candidate_choices = viable(candidate_index)
            if not candidate_choices:
                return False
            if choices is None or len(candidate_choices) < len(choices):
                index = candidate_index
                choices = candidate_choices

        assert choices is not None and index >= 0
        spec = prepared[index]
        same_color = by_color.setdefault(spec.color, set())
        remaining.remove(index)
        for candidate in choices:
            occupied.update(candidate.cells)
            same_color.update(candidate.cells)
            placements[index] = candidate
            if visit():
                return True
            placements.pop(index, None)
            same_color.difference_update(candidate.cells)
            occupied.difference_update(candidate.cells)
        remaining.add(index)
        return False

    if not visit():
        return None
    grid = full_grid(height, width, 0)
    for index, spec in enumerate(prepared):
        row, col = placements[index].origin
        paint_at(grid, row, col, spec.shape, spec.color)
    return grid


def _draw_profile(profile_index: int, rng) -> list[list[int]]:
    height, width, specs = _PROFILE_SPECS[profile_index]
    for _ in range(20):
        grid = _place_specs(height, width, specs, rng)
        if grid is not None and canonical_profile_signature(grid) in _CANONICAL_SIGNATURES:
            return grid
    raise AssertionError(f"could not construct linked canonical profile {profile_index}")


def _general_specs(height: int, width: int, band: str, rng) -> tuple[_ObjectSpec, ...]:
    area = height * width
    max_targets = max(1, min(4, (width - 2) // 3))
    ranges = {
        "easy": ((1, 2), (2, 2), (1, 2)),
        "medium": ((2, 3), (2, 4), (2, 3)),
        "hard": ((2, 4), (3, 5), (3, 5)),
    }[band]
    target_count = min(rng.randint(*ranges[0]), max_targets)
    non_target_count = rng.randint(*ranges[1])
    distractor_count = rng.randint(*ranges[2])
    max_total = max(4, min(12, area // 9))
    while target_count + non_target_count + distractor_count > max_total:
        if distractor_count > 1:
            distractor_count -= 1
        elif non_target_count > 1:
            non_target_count -= 1
        else:
            break

    shapes = _SHAPES_SIMPLE if band == "easy" else _SHAPES_ALL
    specs: list[_ObjectSpec] = [
        _spec("blue", "T", rng.choice(shapes))
        for _ in range(target_count)
    ]

    border_pool = ["B", "L", "R", "I"]
    if band == "medium":
        border_pool += ["TL", "TR"]
    elif band == "hard":
        border_pool += ["TL", "TR", "BL", "BR"]
    rng.shuffle(border_pool)
    # A blue top-corner near-miss is the decisive witness against the tempting
    # but wrong "recolor every blue object touching top" rule.
    border_pool[0] = "TL"
    for index in range(non_target_count):
        specs.append(
            _spec(
                "blue",
                border_pool[index % len(border_pool)],
                rng.choice(shapes),
            )
        )

    distractor_borders = ["I", "I", "L", "R", "T", "B"]
    if band == "hard":
        distractor_borders += ["TL", "TR", "BL", "BR"]
    rng.shuffle(distractor_borders)
    # Every generalized lesson needs an explicit color-vs-geometry witness:
    # a non-blue top-only object must remain unchanged.
    distractor_borders[0] = "T"
    for index in range(distractor_count):
        specs.append(
            _spec(
                "distractor",
                distractor_borders[index % len(distractor_borders)],
                rng.choice(shapes),
            )
        )
    return tuple(specs)


def _fallback_specs() -> tuple[_ObjectSpec, ...]:
    return (
        _spec("blue", "TL", _SINGLE),
        _spec("blue", "T", _V2),
        _spec("blue", "B", _V2),
        _spec("distractor", "T", _SINGLE),
    )


def _draw_general(height: int, width: int, band: str, rng) -> list[list[int]]:
    for _ in range(30):
        specs = _general_specs(height, width, band, rng)
        grid = _place_specs(height, width, specs, rng)
        if grid is not None and not self_check(grid, difficulty=band):
            return grid
    grid = _place_specs(height, width, _fallback_specs(), rng)
    if grid is None or self_check(grid, difficulty=band):
        raise AssertionError(f"could not construct a lawful scene in {height}x{width}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the semantic source-grid grammar without mutating ``grid``."""
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    source = _coerce_grid(grid)
    height = len(source)
    errors: list[str] = []
    if not (_VALID_H[0] <= height <= _VALID_H[1] and _VALID_W[0] <= width <= _VALID_W[1]):
        errors.append("grid dimensions must be within declared 8..18 bounds")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in source
        for value in row
    ):
        errors.append("grid colors must be integer values in 0..9")
        return sorted(set(errors))
    counts = Counter(value for row in source for value in row)
    if counts[0] == 0 or counts[0] <= max((count for color, count in counts.items() if color != 0), default=0):
        errors.append("background 0 must be present and modal")
    if counts[3]:
        errors.append("input color 3 is forbidden because it leaks the output color")

    blue_components = []
    distractor_components = 0
    for color, cells in _components(source):
        if color == 1:
            blue_components.append(cells)
        else:
            distractor_components += 1
    target_count = sum(
        _border_signature(cells, height, width) == "T"
        for cells in blue_components
    )
    non_target_count = len(blue_components) - target_count
    if target_count < 1:
        errors.append("need at least one blue top-only target component")
    if non_target_count < 1:
        errors.append("need at least one non-target blue component")
    if distractor_components < 1:
        errors.append("need at least one non-blue distractor component")
    return sorted(set(errors))


def observe_overrides(grid) -> dict[str, int]:
    """Return the exact public axes observable from a valid generated grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def strict_canonical_like(grid) -> list[str]:
    """Recognize the five linked component profiles, modulo nuisance layout."""
    errors = self_check(grid)
    if errors:
        return errors
    if canonical_profile_signature(grid) is None:
        return ["scene is lawful but does not match a linked canonical profile"]
    return []


def rule_mirror(grid) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    source = _coerce_grid(grid)
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0])
    for color, cells in _components(source):
        if color == 1 and _border_signature(cells, height, width) == "T":
            for row, col in cells:
                output[row][col] = 3
    return output


def _recolor_where(
    grid,
    predicate: Callable[[int, tuple[tuple[int, int], ...], str], bool],
) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    source = _coerce_grid(grid)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    for color, cells in _components(source):
        signature = _border_signature(cells, height, width)
        if predicate(color, cells, signature):
            for row, col in cells:
                output[row][col] = 3
    return output


def _rival_recolor_all_top_blue(grid):
    return _recolor_where(
        grid,
        lambda color, _cells, signature: color == 1 and "T" in signature,
    )


def _rival_recolor_all_border_blue(grid):
    return _recolor_where(
        grid,
        lambda color, _cells, signature: color == 1 and signature != "I",
    )


def _rival_recolor_first_blue(grid):
    source = _coerce_grid(grid)
    blue = [cells for color, cells in _components(source) if color == 1]
    first = blue[0] if blue else ()
    return _recolor_where(
        source,
        lambda color, cells, _signature: color == 1 and cells == first,
    )


def _rival_recolor_all_top_only_objects(grid):
    return _recolor_where(
        grid,
        lambda _color, _cells, signature: signature == "T",
    )


SEMANTIC_RIVALS = {
    "all_top_blue": _rival_recolor_all_top_blue,
    "all_border_blue": _rival_recolor_all_border_blue,
    "first_blue": _rival_recolor_first_blue,
    "all_top_only_objects": _rival_recolor_all_top_only_objects,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid, rival) -> bool:
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "top_corner_is_not_top_only": lambda grid: _rival_differs(
        grid, _rival_recolor_all_top_blue
    ),
    "other_borders_are_preserved": lambda grid: _rival_differs(
        grid, _rival_recolor_all_border_blue
    ),
    "selection_is_not_first_blue": lambda grid: _rival_differs(
        grid, _rival_recolor_first_blue
    ),
    "non_blue_top_object_is_preserved": lambda grid: _rival_differs(
        grid, _rival_recolor_all_top_only_objects
    ),
}

WITNESS_RIVALS = {
    "top_corner_is_not_top_only": ["all_top_blue"],
    "other_borders_are_preserved": ["all_border_blue"],
    "selection_is_not_first_blue": ["first_blue"],
    "non_blue_top_object_is_preserved": ["all_top_only_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared rivals that fit every demonstration but alter the query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if self_check(demo.get("input")):
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        if rule_mirror(demo["input"]) != demo.get("output"):
            reasons.append(f"demo {index} output does not match the task rule")
    if self_check(query.get("input")):
        reasons.append("query input is outside the task grammar")
        return reasons
    answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo.get("output") for demo in demos):
            if competitor(query["input"]) != answer:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query"
                )
    return reasons


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
    has_override = any(overrides.get(name) is not None for name in AXES)
    profile_index = None
    if not has_override and sample_index % 2 == 1:
        prior_rng = ctx.draw_rng(f"linked_profile_prior|{band}")
        # Half of indices are eligible, so 0.64 retains the intended roughly
        # 32% linked-profile prior.  Every four-pair rotation then contains two
        # generalized anti-shortcut scenes; after any one holdout, one remains.
        if prior_rng.random() < _PROFILE_PRIOR * 2:
            profile_index = ctx.draw_choice(
                f"linked_profile_index|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )

    if profile_index is not None:
        height, width, _specs = _PROFILE_SPECS[profile_index]
        height = ctx.draw_int("grid_h", height, height)
        width = ctx.draw_int("grid_w", width, width)
        grid = _draw_profile(profile_index, ctx.draw_rng("profile_layout"))
    else:
        height_bounds, width_bounds = _BAND_BOUNDS[band]
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        grid = _draw_general(height, width, band, ctx.draw_rng("general_layout"))

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    if (len(grid), len(grid[0])) != (height, width):
        raise AssertionError("returned grid disagrees with keyed dimensions")
    return grid
