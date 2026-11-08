"""Generator for 212895b5 — cyan-square rays around gray blockers.

A solid 3x3 cyan square sits in a black field with scattered gray cells.  The
selected Racket rule emits two different ray families from the square corners:

* red follows the four outward diagonals.  A ray stops before a gray diagonal
  cell, or before a diagonal cell whose two inward orthogonal neighbours are
  both gray;
* yellow follows the four clockwise-adjacent outward diagonals as an
  alternating staircase.  A gray start cell suppresses the ray, a gray
  intermediate step stops before that step, and a gray next diagonal cell
  leaves the intermediate step painted before stopping.

The three-step OPEN/MIXED/MIXED schedule pairs opposite mixed layouts.
Every three consecutive ordinary samples expose both upward and downward
corner-pinches. Blocker distances vary across the available ray lengths.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fbf36c193fa6"
TASK_ID = "fbf36c193fa6"
VERSION = "4.1.0"
RULE_HASH = "df658022eba5"

SUMMARY = (
    "A 16..23 by 16..23 zero-background grid contains one solid 3x3 cyan(8) "
    "square and 20..64 gray(5) obstacles. Red(2) rays leave the four square "
    "corners on the outward diagonals, stopping before a diagonal gray cell or "
    "before a diagonal cell pinched by gray cells on both inward orthogonal "
    "sides. Yellow(4) rays leave the corners in the clockwise-adjacent diagonal "
    "directions as alternating staircases: gray at the start suppresses the "
    "ray, gray on an intermediate step stops before it, and gray on the next "
    "diagonal cell preserves the intermediate step before stopping. Gray and "
    "cyan cells remain unchanged. Ordinary draws use open/mixed/mixed profiles with opposite mixed "
    "orientations and variable blocker depths, so every three-example lesson "
    "exposes free travel, all blocker branches, and a downward corner-pinch."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular 16..23 by 16..23 grid with colors exactly from {0,5,8}",
    "exactly one solid 3x3 cyan square with at least four cells of margin on every side",
    "20..64 gray cells do not overlap the cyan square",
    "all four red and all four yellow ray families have visible in-bounds support",
    "open lessons keep every ray-sensitive cell clear",
    "mixed lessons contain direct-red, corner-pair-red, yellow-start, yellow-intermediate, and yellow-diagonal blockers plus open control rays",
    "every three consecutive ordinary sample indices contain open and opposite mixed profiles",
    "mixed blocker roles reach all four corners across seeds and use variable distances",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware with frequent canonical dimensions",
        "valid": "16..23",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware with frequent canonical dimensions",
        "valid": "16..23",
    },
    "n_gray": {
        "type": "int",
        "default": "difficulty-aware 20..64",
        "valid": "20..64",
    },
    "square_row_band": {
        "type": "str",
        "default": "keyed upper|center|lower",
        "valid": "upper|center|lower",
    },
    "square_col_band": {
        "type": "str",
        "default": "keyed left|center|right",
        "valid": "left|center|right",
    },
    "barrier_profile": {
        "type": "str",
        "default": "three-step schedule open|mixed|mixed with opposite mixed orientations",
        "valid": "open|mixed",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = (
    "no_square",
    "broken_square",
    "multiple_squares",
    "output_color_in_input",
    "too_few_gray",
)

_ALLOWED_OVERRIDES = frozenset({*AXES, "texture"})
_CANONICAL_DIMS = ((18, 17), (20, 20), (16, 19), (21, 23))
_SQUARE_SIZE = 3
_MARGIN = 4

Cell = tuple[int, int]
BBox = tuple[int, int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the blocker profile used by the sliding-window lesson schedule."""
    del seed, difficulty
    return "open" if sample_index % 3 == 0 else "mixed"


SCHEDULE_PROFILES = ("open", "mixed")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    texture = overrides.get("texture")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")


def _partition(values: list[int]) -> dict[str, tuple[int, ...]]:
    """Split at least six legal anchors into three deterministic nonempty bands."""
    n = len(values)
    q, rem = divmod(n, 3)
    sizes = [q + (index < rem) for index in range(3)]
    out: dict[str, tuple[int, ...]] = {}
    cursor = 0
    for name, size in zip(("upper", "center", "lower"), sizes):
        out[name] = tuple(values[cursor : cursor + size])
        cursor += size
    return out


def _row_bands(height: int) -> dict[str, tuple[int, ...]]:
    return _partition(list(range(_MARGIN, height - _MARGIN - _SQUARE_SIZE + 1)))


def _col_bands(width: int) -> dict[str, tuple[int, ...]]:
    bands = _partition(list(range(_MARGIN, width - _MARGIN - _SQUARE_SIZE + 1)))
    return {"left": bands["upper"], "center": bands["center"], "right": bands["lower"]}


def _in_bounds(row: int, col: int, height: int, width: int) -> bool:
    return 0 <= row < height and 0 <= col < width


def _square_cells(box: BBox) -> set[Cell]:
    top, left, bottom, right = box
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _red_specs(box: BBox) -> tuple[tuple[Cell, int, int], ...]:
    top, left, bottom, right = box
    return (
        ((top, left), -1, -1),
        ((top, right), -1, 1),
        ((bottom, left), 1, -1),
        ((bottom, right), 1, 1),
    )


def _yellow_specs(box: BBox) -> tuple[tuple[Cell, int, int], ...]:
    top, left, bottom, right = box
    return (
        ((top, left), -1, 1),
        ((top, right), 1, 1),
        ((bottom, right), 1, -1),
        ((bottom, left), -1, -1),
    )


def _red_trace(
    grid: list[list[int]],
    corner: Cell,
    dr: int,
    dc: int,
    *,
    ignore_gray: bool = False,
    ignore_corner_pair: bool = False,
) -> tuple[list[Cell], str]:
    """Mirror the selected Racket red-ray branch and report its stop reason."""
    height, width = len(grid), len(grid[0])
    row, col = corner[0] + dr, corner[1] + dc
    cells: list[Cell] = []
    while _in_bounds(row, col, height, width):
        if not ignore_gray and grid[row][col] == 5:
            return cells, "direct_gray"
        if (
            not ignore_gray
            and not ignore_corner_pair
            and grid[row][col - dc] == 5
            and grid[row - dr][col] == 5
        ):
            return cells, "corner_pair"
        cells.append((row, col))
        row += dr
        col += dc
    return cells, "edge"


def _yellow_trace(
    grid: list[list[int]],
    corner: Cell,
    dr: int,
    dc: int,
    *,
    ignore_gray: bool = False,
    diagonal_stop_before_intermediate: bool = False,
) -> tuple[list[Cell], str]:
    """Mirror the selected alternating yellow staircase and its stop policy."""
    height, width = len(grid), len(grid[0])
    active_row, active_col = corner[0] + dr, corner[1] + dc
    if not _in_bounds(active_row, active_col, height, width):
        return [], "edge"
    if not ignore_gray and grid[active_row][active_col] == 5:
        return [], "start_gray"

    cells: list[Cell] = [(active_row, active_col)]
    phase = 0 if dr * dc < 0 else 1
    while True:
        next_row, next_col = active_row + dr, active_col + dc
        if phase == 0:
            step_row, step_col = active_row + dr, active_col
        else:
            step_row, step_col = active_row, active_col + dc

        if not _in_bounds(next_row, next_col, height, width):
            return cells, "edge"
        if not _in_bounds(step_row, step_col, height, width):
            return cells, "edge"
        if not ignore_gray and grid[step_row][step_col] == 5:
            return cells, "intermediate_gray"
        if (
            not ignore_gray
            and diagonal_stop_before_intermediate
            and grid[next_row][next_col] == 5
        ):
            return cells, "diagonal_gray"

        cells.append((step_row, step_col))
        if not ignore_gray and grid[next_row][next_col] == 5:
            return cells, "diagonal_gray"
        cells.append((next_row, next_col))
        active_row, active_col = next_row, next_col
        phase = 1 - phase


def _ray_sensitive_cells(height: int, width: int, box: BBox) -> set[Cell]:
    """Every cell whose gray/non-gray state can change the selected rule."""
    sensitive = set(_square_cells(box))
    for corner, dr, dc in _red_specs(box):
        row, col = corner[0] + dr, corner[1] + dc
        while _in_bounds(row, col, height, width):
            sensitive.add((row, col))
            sensitive.add((row, col - dc))
            sensitive.add((row - dr, col))
            row += dr
            col += dc
    for corner, dr, dc in _yellow_specs(box):
        active_row, active_col = corner[0] + dr, corner[1] + dc
        if not _in_bounds(active_row, active_col, height, width):
            continue
        sensitive.add((active_row, active_col))
        phase = 0 if dr * dc < 0 else 1
        while True:
            next_row, next_col = active_row + dr, active_col + dc
            if phase == 0:
                step_row, step_col = active_row + dr, active_col
            else:
                step_row, step_col = active_row, active_col + dc
            if not _in_bounds(next_row, next_col, height, width):
                break
            if not _in_bounds(step_row, step_col, height, width):
                break
            sensitive.add((step_row, step_col))
            sensitive.add((next_row, next_col))
            active_row, active_col = next_row, next_col
            phase = 1 - phase
    return sensitive


def _mixed_blockers(box: BBox, height: int, width: int, ctx) -> set[Cell]:
    """Vary blocker roles and depths without losing short-lesson witnesses.

    Mixed residues 1 and 2 are opposite rotations for a fixed seed. Their
    corner-pair directions therefore have opposite vertical signs. This also
    holds for windows that straddle a cycle. Exact profile overrides are still
    honored, but arbitrary override sequences do not promise lesson coverage.
    """
    base_rotation = 0 if ctx.seed % 2 == 0 else 3
    rotation = (base_rotation + (2 if ctx.sample_index % 3 == 2 else 0)) % 4
    rng = ctx.draw_rng("blocker_depths")
    empty = full_grid(height, width, 0)
    red = _red_specs(box)
    yellow = _yellow_specs(box)
    clockwise_red = (0, 1, 3, 2)
    blockers: set[Cell] = set()

    # Select from every legal stopping depth, not a fixed third step.
    direct = red[clockwise_red[rotation]]
    direct_cells, _ = _red_trace(empty, *direct)
    blockers.add(rng.choice(direct_cells))

    pinch = red[clockwise_red[(rotation + 1) % 4]]
    pinch_cells, _ = _red_trace(empty, *pinch)
    row, col = rng.choice(pinch_cells)
    _corner, dr, dc = pinch
    blockers.update({(row, col - dc), (row - dr, col)})

    start_cells, _ = _yellow_trace(empty, *yellow[rotation])
    blockers.add(start_cells[0])
    intermediate_cells, _ = _yellow_trace(empty, *yellow[(rotation + 1) % 4])
    blockers.add(rng.choice(intermediate_cells[1::2]))
    diagonal_cells, _ = _yellow_trace(empty, *yellow[(rotation + 2) % 4])
    blockers.add(rng.choice(diagonal_cells[2::2]))
    if len(blockers) != 6:
        raise AssertionError("mixed blocker roles overlap")
    return blockers


def _extract_scene(grid: Any) -> tuple[list[list[int]] | None, dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, {}, ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, {}, ["grid rows must be rectangular and nonempty"]
    height = len(grid)
    if not (16 <= height <= 23 and 16 <= width <= 23):
        errors.append(f"grid dimensions {height}x{width} outside 16..23")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in (0, 5, 8)
            ):
                errors.append(
                    f"cell ({row_index},{col_index}) has {value!r}; input colors must be 0,5,8"
                )
                return None, {}, errors

    cyan = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if len(cyan) != 9:
        errors.append(f"expected exactly nine cyan cells, found {len(cyan)}")
        return [row[:] for row in grid], {}, errors
    top = min(row for row, _ in cyan)
    left = min(col for _, col in cyan)
    bottom = max(row for row, _ in cyan)
    right = max(col for _, col in cyan)
    box = (top, left, bottom, right)
    if bottom - top != 2 or right - left != 2 or set(cyan) != _square_cells(box):
        errors.append("cyan cells must form one solid 3x3 square")
    margins = (top, left, height - 1 - bottom, width - 1 - right)
    if min(margins) < _MARGIN:
        errors.append(f"cyan square needs >=4 margin on every side, got {margins}")

    n_gray = sum(value == 5 for row in grid for value in row)
    if not (20 <= n_gray <= 64):
        errors.append(f"expected 20..64 gray cells, found {n_gray}")

    return [row[:] for row in grid], {
        "height": height,
        "width": width,
        "box": box,
        "n_gray": n_gray,
        "margins": margins,
    }, errors


def _trace_features(grid: list[list[int]], box: BBox) -> dict[str, Any]:
    red = [_red_trace(grid, *spec) for spec in _red_specs(box)]
    yellow = [_yellow_trace(grid, *spec) for spec in _yellow_specs(box)]
    return {
        "red": red,
        "yellow": yellow,
        "red_reasons": [reason for _, reason in red],
        "yellow_reasons": [reason for _, reason in yellow],
    }


def _classify_profile(features: dict[str, Any]) -> str:
    red = features["red_reasons"]
    yellow = features["yellow_reasons"]
    if red == ["edge"] * 4 and yellow == ["edge"] * 4:
        return "open"
    if (
        "direct_gray" in red
        and "corner_pair" in red
        and "edge" in red
        and "start_gray" in yellow
        and "intermediate_gray" in yellow
        and "diagonal_gray" in yellow
        and "edge" in yellow
    ):
        return "mixed"
    return "other"


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests and adversarial lesson checks."""
    coerced, scene, errors = _extract_scene(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    assert coerced is not None
    output = [row[:] for row in coerced]
    features = _trace_features(coerced, scene["box"])
    for cells, _reason in features["red"]:
        for row, col in cells:
            output[row][col] = 2
    for cells, _reason in features["yellow"]:
        for row, col in cells:
            output[row][col] = 4
    return output


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    coerced, scene, errors = _extract_scene(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    assert coerced is not None
    top, left, _bottom, _right = scene["box"]
    row_band = next(
        name for name, values in _row_bands(scene["height"]).items() if top in values
    )
    col_band = next(
        name for name, values in _col_bands(scene["width"]).items() if left in values
    )
    profile = _classify_profile(_trace_features(coerced, scene["box"]))
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "n_gray": scene["n_gray"],
        "square_row_band": row_band,
        "square_col_band": col_band,
        "barrier_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes while accepting every canonical input."""
    del difficulty
    coerced, scene, errors = _extract_scene(grid)
    if errors or coerced is None:
        return errors

    features = _trace_features(coerced, scene["box"])
    red_cells = {cell for cells, _ in features["red"] for cell in cells}
    yellow_cells = {cell for cells, _ in features["yellow"] for cell in cells}
    if not red_cells:
        errors.append("all red rays are suppressed; the transformation is hidden")
    if not yellow_cells:
        errors.append("all yellow staircases are suppressed; the transformation is hidden")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    if requested:
        try:
            observed = observe_overrides(coerced)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for name, value in requested.items():
                if name in observed and observed[name] != value:
                    errors.append(
                        f"override {name} requested {value!r}, observed {observed[name]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The repaired teaching grammar stays inside the complete canonical envelope."""
    return self_check(grid)


def _build_valid(ctx) -> list[list[int]]:
    height = ctx.draw_int_diff("grid_h", 16, 23)
    width = ctx.draw_int_diff("grid_w", 16, 23)
    n_gray = ctx.draw_int_diff("n_gray", 20, 64)
    row_band = ctx.draw_choice("square_row_band", ("upper", "center", "lower"))
    col_band = ctx.draw_choice("square_col_band", ("left", "center", "right"))
    profile = ctx.draw_choice("barrier_profile", ("open", "mixed"))

    layout_rng = ctx.draw_rng("layout")
    top = layout_rng.choice(_row_bands(height)[row_band])
    left = layout_rng.choice(_col_bands(width)[col_band])
    box = (top, left, top + 2, left + 2)

    grid = full_grid(height, width, 0)
    for row, col in _square_cells(box):
        grid[row][col] = 8

    sensitive = _ray_sensitive_cells(height, width, box)
    blockers = _mixed_blockers(box, height, width, ctx) if profile == "mixed" else set()
    if not blockers <= sensitive:
        raise AssertionError("mixed blockers escaped the ray-sensitive set")
    for row, col in blockers:
        grid[row][col] = 5

    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in sensitive
    ]
    remaining = n_gray - len(blockers)
    if remaining < 0 or remaining > len(available):
        raise ValueError(
            f"cannot place {n_gray} gray cells in {height}x{width} with profile {profile}"
        )
    for row, col in layout_rng.sample(available, remaining):
        grid[row][col] = 5

    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_gray": n_gray,
        "square_row_band": row_band,
        "square_col_band": col_band,
        "barrier_profile": profile,
    }
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, got {observed}")
    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name: str, ctx) -> list[list[int]]:
    """Return task-linked malformed inputs that self_check must reject."""
    grid = full_grid(18, 18, 0)
    for row in range(5, 8):
        for col in range(7, 10):
            grid[row][col] = 8
    rng = ctx.draw_rng(f"degenerate_{name}")
    candidates = [
        (row, col)
        for row in range(18)
        for col in range(18)
        if grid[row][col] == 0
    ]
    for row, col in rng.sample(candidates, 24):
        grid[row][col] = 5

    if name == "no_square":
        for row, col in _square_cells((5, 7, 7, 9)):
            grid[row][col] = 0
    elif name == "broken_square":
        grid[6][8] = 0
    elif name == "multiple_squares":
        for row in range(11, 14):
            for col in range(11, 14):
                grid[row][col] = 8
    elif name == "output_color_in_input":
        grid[0][0] = 2
    elif name == "too_few_gray":
        for row in range(18):
            for col in range(18):
                if grid[row][col] == 5:
                    grid[row][col] = 0
        grid[0][0] = 5
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input for the selected Racket authority."""
    _validate_call(difficulty, overrides)
    effective = dict(overrides)
    texture = effective.pop("texture", None)

    if "barrier_profile" not in effective:
        effective["barrier_profile"] = schedule_profile(seed, sample_index, difficulty)

    # Half of ordinary draws use one of the four exact public dimension pairs,
    # anchoring every band to canonical scale without freezing the distribution.
    if (
        sample_index % 4 in (0, 3)
        and "grid_h" not in effective
        and "grid_w" not in effective
    ):
        canonical_h, canonical_w = _CANONICAL_DIMS[(seed + sample_index) % 4]
        effective["grid_h"] = canonical_h
        effective["grid_w"] = canonical_w

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    if texture is not None:
        return _draw_from_degenerate(texture, ctx)
    return _build_valid(ctx)


def _recolor_traces(
    grid: list[list[int]],
    *,
    red_ignore_gray: bool = False,
    red_ignore_corner_pair: bool = False,
    red_corner_pairs_upward_only: bool = False,
    yellow_ignore_gray: bool = False,
    yellow_straight: bool = False,
    yellow_diagonal_stop_before_intermediate: bool = False,
) -> list[list[int]]:
    """Parameterized shortcut family used only for adversarial evidence."""
    coerced, scene, errors = _extract_scene(grid)
    if errors or coerced is None:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    box = scene["box"]
    for spec in _red_specs(box):
        cells, _ = _red_trace(
            coerced,
            *spec,
            ignore_gray=red_ignore_gray,
            ignore_corner_pair=(red_ignore_corner_pair or (red_corner_pairs_upward_only and spec[1] > 0)),
        )
        for row, col in cells:
            output[row][col] = 2

    if yellow_straight:
        height, width = len(coerced), len(coerced[0])
        for corner, dr, dc in _yellow_specs(box):
            row, col = corner[0] + dr, corner[1] + dc
            while _in_bounds(row, col, height, width) and (
                yellow_ignore_gray or coerced[row][col] != 5
            ):
                output[row][col] = 4
                row += dr
                col += dc
    else:
        for spec in _yellow_specs(box):
            cells, _ = _yellow_trace(
                coerced,
                *spec,
                ignore_gray=yellow_ignore_gray,
                diagonal_stop_before_intermediate=yellow_diagonal_stop_before_intermediate,
            )
            for row, col in cells:
                output[row][col] = 4
    return output


def _rival_ignore_all_gray(grid):
    return _recolor_traces(grid, red_ignore_gray=True, yellow_ignore_gray=True)


def _rival_red_direct_only(grid):
    return _recolor_traces(grid, red_ignore_corner_pair=True)


def _rival_yellow_straight_diagonal(grid):
    return _recolor_traces(grid, yellow_straight=True)


def _rival_yellow_stops_before_diagonal_step(grid):
    return _recolor_traces(grid, yellow_diagonal_stop_before_intermediate=True)


def _rival_upward_corner_pairs_only(grid):
    """Fits all four public canonical pairs and every v4.0 ordinary draw."""
    return _recolor_traces(grid, red_corner_pairs_upward_only=True)


def _rival_omit_red_rays(grid):
    """Keep the yellow staircases but omit the entire red ray family."""
    output = rule_mirror(grid)
    return [[grid[r][c] if value == 2 else value for c, value in enumerate(row)]
            for r, row in enumerate(output)]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "omit all red rays": _rival_omit_red_rays,
    "red corner pairs stop only upward rays": _rival_upward_corner_pairs_only,
    "ignore all gray blockers": _rival_ignore_all_gray,
    "red stops only on a diagonal gray cell": _rival_red_direct_only,
    "yellow is a straight diagonal rather than a staircase": _rival_yellow_straight_diagonal,
    "yellow diagonal blocker erases the preceding intermediate step": _rival_yellow_stops_before_diagonal_step,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "red corner pairs stop only upward rays": _rival_upward_corner_pairs_only,
}


def _features_for_witness(grid: list[list[int]]) -> dict[str, Any]:
    coerced, scene, errors = _extract_scene(grid)
    if errors or coerced is None:
        return {"red_reasons": [], "yellow_reasons": [], "red": [], "yellow": []}
    return _trace_features(coerced, scene["box"])


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "red_open_to_edge": lambda grid: "edge" in _features_for_witness(grid)["red_reasons"],
    "red_direct_gray_stop": lambda grid: "direct_gray" in _features_for_witness(grid)["red_reasons"],
    "red_downward_corner_pair_stop": lambda grid: any(
        reason == "corner_pair"
        for _cells, reason in _features_for_witness(grid)["red"][2:]
    ),
    "red_corner_pair_stop": lambda grid: "corner_pair" in _features_for_witness(grid)["red_reasons"],
    "yellow_open_staircase": lambda grid: any(
        reason == "edge" and len(cells) >= 4
        for cells, reason in _features_for_witness(grid)["yellow"]
    ),
    "yellow_start_gray_stop": lambda grid: "start_gray" in _features_for_witness(grid)["yellow_reasons"],
    "yellow_intermediate_gray_stop": lambda grid: "intermediate_gray" in _features_for_witness(grid)["yellow_reasons"],
    "yellow_diagonal_gray_keeps_step": lambda grid: "diagonal_gray" in _features_for_witness(grid)["yellow_reasons"],
}

WITNESS_RIVALS = {
    "red_open_to_edge": ["omit all red rays"],
    "red_downward_corner_pair_stop": ["red corner pairs stop only upward rays"],
    "red_direct_gray_stop": ["ignore all gray blockers"],
    "red_corner_pair_stop": ["red stops only on a diagonal gray cell"],
    "yellow_open_staircase": ["yellow is a straight diagonal rather than a staircase"],
    "yellow_start_gray_stop": ["ignore all gray blockers"],
    "yellow_intermediate_gray_stop": ["ignore all gray blockers"],
    "yellow_diagonal_gray_keeps_step": [
        "yellow diagonal blocker erases the preceding intermediate step"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a named shortcut viable."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is not in the teaching grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the selected ray rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(
                    f"demonstrations leave rival answer-equivalent on this query: {name}"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Five structural impostors used by strict mutation and focused tests."""
    return [
        (
            name,
            generate(index + 1, index + 1, difficulty="medium", texture=name),
        )
        for index, name in enumerate(DEGENERATE_TEXTURES)
    ]
