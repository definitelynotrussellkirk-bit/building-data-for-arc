"""Generator for applying two transforms to a proto and stamping at anchors.

Cells ``(0, 0)`` and ``(0, 1)`` encode two transforms.  After those cells are
removed, the unique 4-connected color-9 component is cropped to a binary proto.
The transforms are applied in order, and the result is centered on every
isolated colored anchor, recolored to that anchor, with out-of-bounds cells
cropped exactly as in the selected rule.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "374fae0ec7a2"
TASK_ID = "374fae0ec7a2"
VERSION = "3.1.0"
RULE_HASH = "664609196c7e"

SUMMARY = (
    "Read the two transform codes at the upper left, crop the connected color-9 "
    "proto, apply code1 then code2, and stamp the transformed shape centered at "
    "each isolated anchor in the anchor's color."
)

INVARIANTS = [
    "row 0 contains exactly two transform codes, at (0,0) and (0,1)",
    "after removing the codes there is exactly one all-9 connected proto of size 2..6",
    "all remaining nonzero components are 1..8 isolated anchors colored 2..8",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical height", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "scheduled canonical width", "valid": "9..18"},
    "code1": {"type": "int", "default": "scheduled transform", "valid": "1..7"},
    "code2": {"type": "int", "default": "scheduled transform", "valid": "1..7"},
    "proto_size": {"type": "int", "default": "scheduled 4..6", "valid": "2..6"},
    "n_anchors": {"type": "int", "default": "2 easy / 3 medium / 4 hard", "valid": "1..8"},
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "canonical_12x14",
    "canonical_11x13",
    "canonical_12x12",
    "canonical_13x15",
    "generalized_min_8x9",
    "generalized_max_18x18",
)

_PROFILE_CONFIGS = {
    "canonical_12x14": {"grid_h": 12, "grid_w": 14, "code1": 2, "code2": 4, "proto_size": 6},
    "canonical_11x13": {"grid_h": 11, "grid_w": 13, "code1": 4, "code2": 3, "proto_size": 4},
    "canonical_12x12": {"grid_h": 12, "grid_w": 12, "code1": 2, "code2": 6, "proto_size": 5},
    "canonical_13x15": {"grid_h": 13, "grid_w": 15, "code1": 6, "code2": 3, "proto_size": 6},
    "generalized_min_8x9": {"grid_h": 8, "grid_w": 9, "code1": 2, "code2": 4, "proto_size": 4},
    "generalized_max_18x18": {"grid_h": 18, "grid_w": 18, "code1": 4, "code2": 3, "proto_size": 6},
}

# Connected, asymmetric representatives.  Default code pairs make sequence
# order and both individual codes observable on all size-4+ representatives.
_PROTO_SHAPES = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
}

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_ALLOWED_OVERRIDES = frozenset(AXES)
_DIRECTIONS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_coordinates(seed: int, sample_index: int, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic canonical-scale curriculum branch."""
    _validate_coordinates(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_axis(ctx, label: str, scheduled: int, low: int, high: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _shape_grid(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> list[list[int]]:
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    result = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in cells:
        result[row][col] = 1
    return result


def _flip_lr(shape: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in shape]


def _flip_ud(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(shape)]


def _rotate_cw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(shape))]


def _rotate_180(shape: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(shape)]


def _rotate_ccw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(list(zip(*shape)))]


def _apply_code(shape: list[list[int]], code: int) -> list[list[int]]:
    transform = {
        1: lambda value: [list(row) for row in value],
        2: _flip_lr,
        3: _flip_ud,
        4: _rotate_cw,
        5: _rotate_180,
        6: _rotate_ccw,
    }.get(code, lambda value: [list(row) for row in value])
    return transform(shape)


def _transformed_shape(proto_size: int, code1: int, code2: int) -> list[list[int]]:
    shape = _shape_grid(_PROTO_SHAPES[proto_size])
    return _apply_code(_apply_code(shape, code1), code2)


def _positioned(cells: tuple[tuple[int, int], ...], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + row, left + col) for row, col in cells}


def _anchor_candidates(
    height: int,
    width: int,
    proto_cells: set[tuple[int, int]],
    parity: int,
) -> list[tuple[int, int]]:
    blocked = set(proto_cells)
    for row, col in proto_cells:
        for delta_row, delta_col in _DIRECTIONS4:
            blocked.add((row + delta_row, col + delta_col))
    # Keep the visual code strip separate even though the selected rule erases it
    # before component extraction.
    blocked.update({(1, 0), (1, 1)})
    return [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if (row + col) % 2 == parity and (row, col) not in blocked
    ]


def _stamp_cells(
    shape: list[list[int]],
    anchor: tuple[int, int],
    height: int,
    width: int,
    *,
    require_interior: bool,
) -> set[tuple[int, int]] | None:
    shape_h, shape_w = len(shape), len(shape[0])
    top = anchor[0] - shape_h // 2
    left = anchor[1] - shape_w // 2
    occupied: set[tuple[int, int]] = set()
    for row in range(shape_h):
        for col in range(shape_w):
            if not shape[row][col]:
                continue
            out_row, out_col = top + row, left + col
            if not (0 <= out_row < height and 0 <= out_col < width):
                return None
            if require_interior and out_row == 0:
                return None
            occupied.add((out_row, out_col))
    return occupied


def _choose_disjoint_anchors(
    candidates: list[tuple[int, int]],
    count: int,
    shape: list[list[int]],
    height: int,
    width: int,
    rng,
) -> list[tuple[int, int]] | None:
    ordered = list(candidates)
    rng.shuffle(ordered)
    footprints = {
        candidate: _stamp_cells(
            shape, candidate, height, width, require_interior=True
        )
        for candidate in ordered
    }
    ordered = [candidate for candidate in ordered if footprints[candidate] is not None]

    def search(start: int, chosen: list[tuple[int, int]], used: set[tuple[int, int]]):
        if len(chosen) == count:
            return list(chosen)
        needed = count - len(chosen)
        if len(ordered) - start < needed:
            return None
        for index in range(start, len(ordered)):
            candidate = ordered[index]
            footprint = footprints[candidate]
            if footprint is None or footprint & used:
                continue
            chosen.append(candidate)
            found = search(index + 1, chosen, used | footprint)
            if found is not None:
                return found
            chosen.pop()
        return None

    return search(0, [], set())


def _choose_layout(
    height: int,
    width: int,
    proto_size: int,
    n_anchors: int,
    code1: int,
    code2: int,
    rng,
) -> tuple[set[tuple[int, int]], list[tuple[int, int]]]:
    proto_shape = _PROTO_SHAPES[proto_size]
    proto_h = max(row for row, _ in proto_shape) + 1
    proto_w = max(col for _, col in proto_shape) + 1
    positions = [
        (top, left)
        for top in range(2, height - proto_h + 1)
        for left in range(0, width - proto_w + 1)
    ]
    rng.shuffle(positions)
    transformed = _transformed_shape(proto_size, code1, code2)

    # Default lessons (at most four anchors) get clean, fully visible,
    # non-overlapping stamps.  Extreme exact overrides remain lawful even when
    # the selected rule's documented crop/overwrite behavior is unavoidable.
    if n_anchors <= 4:
        for top, left in positions:
            proto_cells = _positioned(proto_shape, top, left)
            parities = [0, 1]
            rng.shuffle(parities)
            for parity in parities:
                candidates = _anchor_candidates(height, width, proto_cells, parity)
                anchors = _choose_disjoint_anchors(
                    candidates, n_anchors, transformed, height, width, rng
                )
                if anchors is not None:
                    return proto_cells, anchors

    for top, left in positions:
        proto_cells = _positioned(proto_shape, top, left)
        parities = [0, 1]
        rng.shuffle(parities)
        for parity in parities:
            candidates = _anchor_candidates(height, width, proto_cells, parity)
            if len(candidates) >= n_anchors:
                rng.shuffle(candidates)
                return proto_cells, candidates[:n_anchors]
    raise ValueError(
        f"cannot place proto size {proto_size} and {n_anchors} anchors in {height}x{width}"
    )


def _anchor_colors(code1: int, code2: int, count: int, rng) -> list[int]:
    legal_codes: list[int] = []
    for code in (code1, code2):
        if 2 <= code <= 8 and code not in legal_codes:
            legal_codes.append(code)
    extras = [color for color in range(2, 9) if color not in legal_codes]
    third = rng.choice(extras)
    palette = [third, *legal_codes]
    for color in extras:
        if color not in palette and len(palette) < 3:
            palette.append(color)
    return [palette[index % len(palette)] for index in range(count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_coordinates(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = schedule_profile(seed, sample_index, difficulty)
    profile = _PROFILE_CONFIGS[profile_name]
    height = _draw_axis(ctx, "grid_h", profile["grid_h"], 8, 18)
    width = _draw_axis(ctx, "grid_w", profile["grid_w"], 9, 18)
    code1 = _draw_axis(ctx, "code1", profile["code1"], 1, 7)
    code2 = _draw_axis(ctx, "code2", profile["code2"], 1, 7)
    proto_size = _draw_axis(ctx, "proto_size", profile["proto_size"], 2, 6)
    scheduled_anchors = {None: 3, "easy": 2, "medium": 3, "hard": 4}[difficulty]
    n_anchors = _draw_axis(ctx, "n_anchors", scheduled_anchors, 1, 8)

    layout_rng = ctx.draw_rng("layout")
    proto_cells, anchors = _choose_layout(
        height, width, proto_size, n_anchors, code1, code2, layout_rng
    )
    color_rng = ctx.draw_rng("anchor-colors")
    colors = _anchor_colors(code1, code2, n_anchors, color_rng)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = code1
    grid[0][1] = code2
    for row, col in proto_cells:
        grid[row][col] = 9
    for (row, col), color in zip(anchors, colors):
        grid[row][col] = color

    findings = self_check(grid)
    if findings:  # a generator bug should fail loudly, never emit bad training data
        raise AssertionError(f"generated invalid grid: {findings}")
    return grid


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.pop(0)
                cells.append((current_row, current_col))
                for delta_row, delta_col in _DIRECTIONS4:
                    neighbor = (current_row + delta_row, current_col + delta_col)
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] == 0:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            result.append(sorted(cells))
    return result


def _analyze(grid) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 18:
        errors.append(f"grid height {height} not in [8,18]")
    if not 9 <= width <= 18:
        errors.append(f"grid width {width} not in [9,18]")
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer ARC color 0..9"
                )
                return None, errors
    if width < 2:  # retained for a clear diagnostic despite the width floor
        errors.append("grid is too narrow for two transform codes")
        return None, errors

    code1, code2 = grid[0][0], grid[0][1]
    if not 1 <= code1 <= 7:
        errors.append(f"code1 {code1} not in [1,7]")
    if not 1 <= code2 <= 7:
        errors.append(f"code2 {code2} not in [1,7]")
    extra_header = [(0, col) for col in range(2, width) if grid[0][col] != 0]
    if extra_header:
        errors.append(f"row 0 has non-code payload at {extra_header[:3]}")

    work = deepcopy(grid)
    work[0][0] = 0
    work[0][1] = 0
    components = _components(work)
    proto_components = [
        cells for cells in components if any(work[row][col] == 9 for row, col in cells)
    ]
    if len(proto_components) != 1:
        errors.append(f"expected exactly one color-9 proto component, found {len(proto_components)}")
        return None, errors
    proto = proto_components[0]
    if not 2 <= len(proto) <= 6:
        errors.append(f"proto size {len(proto)} not in [2,6]")
    if any(work[row][col] != 9 for row, col in proto):
        errors.append("the proto component must contain only color 9")

    anchors: list[tuple[int, int]] = []
    for cells in components:
        if cells is proto:
            continue
        if len(cells) != 1:
            errors.append(f"non-proto component has size {len(cells)} instead of 1")
            continue
        row, col = cells[0]
        color = work[row][col]
        if not 2 <= color <= 8:
            errors.append(f"anchor at ({row},{col}) has color {color}, not 2..8")
        anchors.append((row, col))
    if not 1 <= len(anchors) <= 8:
        errors.append(f"anchor count {len(anchors)} not in [1,8]")

    info = {
        "work": work,
        "code1": code1,
        "code2": code2,
        "proto": proto,
        "anchors": anchors,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or semantically unexecutable task inputs."""
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError(f"cannot observe overrides from invalid grid: {errors}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "code1": info["code1"],
        "code2": info["code2"],
        "proto_size": len(info["proto"]),
        "n_anchors": len(info["anchors"]),
    }


def _crop_binary(cells: list[tuple[int, int]]) -> list[list[int]]:
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    shape = [[0 for _ in range(col1 - col0 + 1)] for _ in range(row1 - row0 + 1)]
    for row, col in cells:
        shape[row - row0][col - col0] = 1
    return shape


def _solve_with_codes(
    grid: list[list[int]],
    choose_codes: Callable[[int, int], tuple[int, ...]],
) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError(f"cannot apply rule to invalid grid: {errors}")
    shape = _crop_binary(info["proto"])
    for code in choose_codes(info["code1"], info["code2"]):
        shape = _apply_code(shape, code)

    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    shape_h, shape_w = len(shape), len(shape[0])
    for anchor_row, anchor_col in info["anchors"]:
        color = info["work"][anchor_row][anchor_col]
        top = anchor_row - shape_h // 2
        left = anchor_col - shape_w // 2
        for row in range(shape_h):
            for col in range(shape_w):
                out_row, out_col = top + row, left + col
                if shape[row][col] and 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = color
    return output


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (first, second))


def _rival_reverse_order(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (second, first))


def _rival_ignore_first(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (second,))


def _rival_ignore_second(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_codes(grid, lambda first, second: (first,))


SEMANTIC_RIVALS = {
    "reverse_order": _rival_reverse_order,
    "ignore_first": _rival_ignore_first,
    "ignore_second": _rival_ignore_second,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {}

SEMANTIC_WITNESSES = {
    "sequence_order_matters": lambda grid: _rule_output(grid) != _rival_reverse_order(grid),
    "first_code_matters": lambda grid: _rule_output(grid) != _rival_ignore_first(grid),
    "second_code_matters": lambda grid: _rule_output(grid) != _rival_ignore_second(grid),
}
WITNESS_RIVALS = {
    "sequence_order_matters": ["reverse_order"],
    "first_code_matters": ["ignore_first"],
    "second_code_matters": ["ignore_second"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared wrong rule that fits all demos but changes query."""
    if not isinstance(demos, list) or not demos:
        return ["at least one labeled demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled input/output pair"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demonstration {index} is not a labeled input/output pair"]

    errors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(deepcopy(pair["input"])) == pair["output"] for pair in demos
        )
        if fits_demos and competitor(deepcopy(query["input"])) != query["output"]:
            errors.append(f"{name} fits every demonstration but changes the query")
    return errors
