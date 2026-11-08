"""Semantic curriculum generator for ARC task ``e942ce41cbf5``.

Two separated masks are normalized to the same origin.  A bottom-left control
selects union/intersection/xor; a bottom-right control selects identity,
clockwise rotation, or horizontal reflection of the red mask.  The selected
boolean result is cropped and recolored cyan.

The generator deliberately teaches the *dictionaries*, not just the marginal
shape distribution: every three consecutive examples contain every operation
control and every transform control.  Each generated mask pair is checked so
all operation and transform alternatives produce distinct outputs.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "e942ce41cbf5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7aa66cd7d9ab"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Normalize the blue(1) mask and red(2) mask. The bottom-left control "
    "chooses union(3), intersection(4), or xor(6); the bottom-right control "
    "chooses identity(7), clockwise rotation(8), or horizontal reflection(9) "
    "for the red mask. Crop the chosen result and recolor it cyan(8). Every "
    "three-example lesson covers all operation and transform controls, and "
    "generated sparse connected masks make every branch observationally distinct."
)

INVARIANTS = [
    "the palette is exactly background 0, masks 1/2, one operation control, and one transform control",
    "the operation control is the unique 3/4/6 cell at bottom-left",
    "the transform control is the unique 7/8/9 cell at bottom-right",
    "both masks are sparse connected polyominoes placed in separate source panels",
    "after the selected transform the masks have a nonempty overlap and each has exclusive cells",
    "the cropped cyan output changes when either control is changed",
]

_OPERATION_CONTROLS = (3, 4, 6)
_TRANSFORM_CONTROLS = (7, 8, 9)
_CANONICAL_SHAPES = ((10, 11), (10, 13), (11, 11), (11, 12))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical height 10|11",
        "valid": "10|11",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical width 11|12|13",
        "valid": "11|12|13",
    },
    "op_control": {
        "type": "int",
        "default": "three-example cycle 3|4|6",
        "valid": "3|4|6",
    },
    "transform_control": {
        "type": "int",
        "default": "seed-phased three-example cycle 7|8|9",
        "valid": "7|8|9",
    },
}

# All declared axes are independent and every Cartesian combination is valid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = tuple(
    f"op{op}_tr{transform}"
    for op in _OPERATION_CONTROLS
    for transform in _TRANSFORM_CONTROLS
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic profile for one draw.

    Operation index is ``sample_index mod 3``.  Transform index is the same
    cycle with a seed-selected phase.  Thus every three consecutive draws
    cover all three values of both dictionaries, while different lesson seeds
    cover all nine operation/transform pairings.
    """
    _band(difficulty)
    op = _OPERATION_CONTROLS[int(sample_index) % 3]
    transform = _TRANSFORM_CONTROLS[(int(sample_index) + int(seed)) % 3]
    return f"op{op}_tr{transform}"


def _scheduled_controls(seed: int, sample_index: int) -> tuple[int, int]:
    op = _OPERATION_CONTROLS[int(sample_index) % 3]
    transform = _TRANSFORM_CONTROLS[(int(sample_index) + int(seed)) % 3]
    return op, transform


def _scheduled_shape(seed: int, sample_index: int, band: str) -> tuple[int, int]:
    band_phase = {"easy": 0, "medium": 1, "hard": 2}[band]
    return _CANONICAL_SHAPES[(int(seed) + int(sample_index) + band_phase) % len(_CANONICAL_SHAPES)]


def _norm(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple((int(row), int(col)) for row, col in cells)
    if not cells:
        return frozenset()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rot_cw(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _norm(cells)
    if not cells:
        return frozenset()
    height = max(row for row, _ in cells) + 1
    return _norm((col, height - 1 - row) for row, col in cells)


def _flip_horizontal(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _norm(cells)
    if not cells:
        return frozenset()
    max_col = max(col for _, col in cells)
    return _norm((row, max_col - col) for row, col in cells)


def _transform(cells: Iterable[tuple[int, int]], control: int) -> frozenset[tuple[int, int]]:
    if control == 7:
        return _norm(cells)
    if control == 8:
        return _rot_cw(cells)
    if control == 9:
        return _flip_horizontal(cells)
    raise ValueError(f"unknown transform control: {control!r}")


def _combine(
    blue: Iterable[tuple[int, int]],
    red: Iterable[tuple[int, int]],
    control: int,
) -> frozenset[tuple[int, int]]:
    blue_set, red_set = frozenset(blue), frozenset(red)
    if control == 3:
        return blue_set | red_set
    if control == 4:
        return blue_set & red_set
    if control == 6:
        return blue_set ^ red_set
    raise ValueError(f"unknown operation control: {control!r}")


def _bbox_shape(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    if not cells:
        return (0, 0)
    return (
        max(row for row, _ in cells) - min(row for row, _ in cells) + 1,
        max(col for _, col in cells) - min(col for _, col in cells) + 1,
    )


def _is_solid_bbox(cells: Iterable[tuple[int, int]]) -> bool:
    cells = frozenset(cells)
    height, width = _bbox_shape(cells)
    return bool(cells) and min(height, width) >= 2 and len(cells) == height * width


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == remaining


def _grow_shape(rng, height: int, width: int, size: int) -> frozenset[tuple[int, int]]:
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier: set[tuple[int, int]] = set()
        for row, col in cells:
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    0 <= neighbor[0] < height
                    and 0 <= neighbor[1] < width
                    and neighbor not in cells
                ):
                    frontier.add(neighbor)
        if not frontier:
            break
        cells.add(rng.choice(sorted(frontier)))
    return _norm(cells)


def _teaching_pair(blue: frozenset[tuple[int, int]], red_raw: frozenset[tuple[int, int]]) -> bool:
    if not (_connected(blue) and _connected(red_raw)):
        return False
    red_variants = tuple(_transform(red_raw, control) for control in _TRANSFORM_CONTROLS)
    if len(set(red_variants)) != 3:
        return False

    for red in red_variants:
        if not (blue & red and blue - red and red - blue):
            return False
        outputs = tuple(_combine(blue, red, control) for control in _OPERATION_CONTROLS)
        if len({_norm(result) for result in outputs}) != 3:
            return False
        if any(not result or _is_solid_bbox(result) for result in outputs):
            return False

    for operation in _OPERATION_CONTROLS:
        transformed_outputs = tuple(
            _combine(blue, red, operation) for red in red_variants
        )
        if len({_norm(result) for result in transformed_outputs}) != 3:
            return False
    return True


def _draw_mask_pair(rng, band: str) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    if band == "easy":
        box_h, box_w, min_size, max_size = 3, 3, 4, 6
    elif band == "hard":
        box_h, box_w, min_size, max_size = 4, 4, 5, 8
    else:
        box_h, box_w, min_size, max_size = 3, 4, 4, 7

    for _ in range(512):
        blue = _grow_shape(rng, box_h, box_w, rng.randint(min_size, max_size))
        red_raw = _grow_shape(rng, box_h, box_w, rng.randint(min_size, max_size))
        if _teaching_pair(blue, red_raw):
            return blue, red_raw
    raise ValueError("could not draw a branch-distinguishing sparse mask pair")


def _validate_requested(name: str, value: Any, legal: Sequence[int]) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer, got {value!r}") from exc
    if normalized not in legal:
        raise ValueError(f"{name} override {normalized!r} not in {tuple(legal)!r}")
    return normalized


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    default_h, default_w = _scheduled_shape(seed, sample_index, band)
    default_op, default_transform = _scheduled_controls(seed, sample_index)

    requested_h = _validate_requested("grid_h", overrides.get("grid_h", default_h), (10, 11))
    requested_w = _validate_requested("grid_w", overrides.get("grid_w", default_w), (11, 12, 13))
    requested_op = _validate_requested(
        "op_control", overrides.get("op_control", default_op), _OPERATION_CONTROLS
    )
    requested_transform = _validate_requested(
        "transform_control",
        overrides.get("transform_control", default_transform),
        _TRANSFORM_CONTROLS,
    )

    # Single-option draws retain keyed-draw provenance while preserving the
    # deterministic lesson schedule; explicit caller overrides still pass the
    # same finite-domain validation above.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_choice("grid_h", [requested_h])
    width = ctx.draw_choice("grid_w", [requested_w])
    op_control = ctx.draw_choice("op_control", [requested_op])
    transform_control = ctx.draw_choice("transform_control", [requested_transform])

    layout_rng = ctx.draw_rng("sparse-mask-pair")
    blue, red_raw = _draw_mask_pair(layout_rng, band)
    blue_h, blue_w = _bbox_shape(blue)
    red_h, red_w = _bbox_shape(red_raw)

    max_gap = width - (1 + blue_w + red_w)
    if max_gap < 1:
        raise ValueError("requested grid is too narrow for separated mask panels")
    gap = layout_rng.randint(1, min(2, max_gap))
    top_limit = min(3, height - max(blue_h, red_h) - 1)
    top = layout_rng.randint(1, max(1, top_limit))
    blue_left = 1
    red_left = blue_left + blue_w + gap

    grid = full_grid(height, width, 0)
    paint_at(grid, top, blue_left, sorted(blue), 1)
    paint_at(grid, top, red_left, sorted(red_raw), 2)
    grid[height - 1][0] = op_control
    grid[height - 1][width - 1] = transform_control
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular sequence"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid must contain nonempty rows"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"]}
    if height not in (10, 11):
        errors.append(f"grid_h {height} is outside 10|11")
    if width not in (11, 12, 13):
        errors.append(f"grid_w {width} is outside 11|12|13")

    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid color {value!r} at {(row_index, col_index)}")
                continue
            positions.setdefault(value, []).append((row_index, col_index))

    op_hits = [
        (color, cell)
        for color in _OPERATION_CONTROLS
        for cell in positions.get(color, [])
    ]
    transform_hits = [
        (color, cell)
        for color in _TRANSFORM_CONTROLS
        for cell in positions.get(color, [])
    ]
    op_control = op_hits[0][0] if len(op_hits) == 1 else None
    transform_control = transform_hits[0][0] if len(transform_hits) == 1 else None
    if len(op_hits) != 1:
        errors.append(f"expected exactly one operation control, found {len(op_hits)}")
    elif op_hits[0][1] != (height - 1, 0):
        errors.append("operation control must be at bottom-left")
    if len(transform_hits) != 1:
        errors.append(f"expected exactly one transform control, found {len(transform_hits)}")
    elif transform_hits[0][1] != (height - 1, width - 1):
        errors.append("transform control must be at bottom-right")

    blue_cells = positions.get(1, [])
    red_cells = positions.get(2, [])
    if not blue_cells:
        errors.append("missing blue(1) mask")
    if not red_cells:
        errors.append("missing red(2) mask")
    if blue_cells and not _connected(blue_cells):
        errors.append("blue(1) mask must be 4-connected")
    if red_cells and not _connected(red_cells):
        errors.append("red(2) mask must be 4-connected")
    if any(row == height - 1 for row, _ in blue_cells + red_cells):
        errors.append("mask cells may not occupy the control row")

    allowed = {0, 1, 2}
    if op_control is not None:
        allowed.add(op_control)
    if transform_control is not None:
        allowed.add(transform_control)
    unexpected = sorted(color for color in positions if color not in allowed)
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")
    if 0 not in positions:
        errors.append("background color 0 is missing")

    blue = _norm(blue_cells) if blue_cells else frozenset()
    red_raw = _norm(red_cells) if red_cells else frozenset()
    red = (
        _transform(red_raw, transform_control)
        if red_raw and transform_control is not None
        else frozenset()
    )
    result = (
        _combine(blue, red, op_control)
        if blue and red and op_control is not None
        else frozenset()
    )
    if blue and red:
        if not blue & red:
            errors.append("normalized masks must overlap after the selected transform")
        if not blue - red:
            errors.append("blue mask needs a cell outside the transformed red mask")
        if not red - blue:
            errors.append("transformed red mask needs a cell outside the blue mask")
    if blue and red and op_control is not None:
        if not result:
            errors.append("selected operation result is empty")
        elif _is_solid_bbox(result):
            errors.append("selected operation result is a featureless solid rectangle")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "op_control": op_control,
        "transform_control": transform_control,
        "blue": blue,
        "red_raw": red_raw,
        "red": red,
        "result": result,
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "op_control": analysis["op_control"],
        "transform_control": analysis["transform_control"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name not in AXES:
            continue
        try:
            expected = int(requested)
        except (TypeError, ValueError):
            expected = requested
        if observed.get(name) != expected:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def _render(
    blue: frozenset[tuple[int, int]],
    red_raw: frozenset[tuple[int, int]],
    op_control: int,
    transform_control: int,
) -> list[list[int]]:
    red = _transform(red_raw, transform_control)
    result = _norm(_combine(blue, red, op_control))
    if not result:
        return [[0]]
    height, width = _bbox_shape(result)
    output = full_grid(height, width, 0)
    for row, col in result:
        output[row][col] = 8
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; synchronized Racket remains the authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _render(
        analysis["blue"],
        analysis["red_raw"],
        analysis["op_control"],
        analysis["transform_control"],
    )


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_SHAPES:
        errors.append("grid shape is outside the canonical dimension profiles")
    if not 3 <= len(analysis["blue"]) <= 8:
        errors.append("blue mask size is outside the canonical sparse range 3..8")
    if not 3 <= len(analysis["red_raw"]) <= 8:
        errors.append("red mask size is outside the canonical sparse range 3..8")
    return errors


def _rival_with_aliases(
    grid: Sequence[Sequence[int]],
    *,
    op_alias: dict[int, int] | None = None,
    transform_alias: dict[int, int] | None = None,
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    op = (op_alias or {}).get(analysis["op_control"], analysis["op_control"])
    transform = (transform_alias or {}).get(
        analysis["transform_control"], analysis["transform_control"]
    )
    return _render(analysis["blue"], analysis["red_raw"], op, transform)


def _make_op_alias(source: int, target: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: _rival_with_aliases(grid, op_alias={source: target})


def _make_transform_alias(source: int, target: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: _rival_with_aliases(grid, transform_alias={source: target})


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "control_3_as_intersection": _make_op_alias(3, 4),
    "control_3_as_xor": _make_op_alias(3, 6),
    "control_4_as_union": _make_op_alias(4, 3),
    "control_4_as_xor": _make_op_alias(4, 6),
    "control_6_as_union": _make_op_alias(6, 3),
    "control_6_as_intersection": _make_op_alias(6, 4),
    "control_7_as_rotate_cw": _make_transform_alias(7, 8),
    "control_7_as_flip": _make_transform_alias(7, 9),
    "control_8_as_identity": _make_transform_alias(8, 7),
    "control_8_as_flip": _make_transform_alias(8, 9),
    "control_9_as_identity": _make_transform_alias(9, 7),
    "control_9_as_rotate_cw": _make_transform_alias(9, 8),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The four canonical demonstrations never use transform control 7, so both
# aliases below fit every visible demonstration while disagreeing on the
# canonical query.  Scheduled generated lessons include a discriminating 7
# example in every three-demo window.
CANONICAL_SHORTCUTS = {
    "control_7_as_rotate_cw": SEMANTIC_RIVALS["control_7_as_rotate_cw"],
    "control_7_as_flip": SEMANTIC_RIVALS["control_7_as_flip"],
}


def _branch_witness(axis: str, control: int, rivals: Sequence[str]):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        if analysis["errors"] or analysis[axis] != control:
            return False
        truth = rule_mirror(grid)
        return all(SEMANTIC_RIVALS[name](grid) != truth for name in rivals)

    return witness


SEMANTIC_WITNESSES = {
    "operation_3_dictionary": _branch_witness(
        "op_control", 3, ("control_3_as_intersection", "control_3_as_xor")
    ),
    "operation_4_dictionary": _branch_witness(
        "op_control", 4, ("control_4_as_union", "control_4_as_xor")
    ),
    "operation_6_dictionary": _branch_witness(
        "op_control", 6, ("control_6_as_union", "control_6_as_intersection")
    ),
    "transform_7_dictionary": _branch_witness(
        "transform_control", 7, ("control_7_as_rotate_cw", "control_7_as_flip")
    ),
    "transform_8_dictionary": _branch_witness(
        "transform_control", 8, ("control_8_as_identity", "control_8_as_flip")
    ),
    "transform_9_dictionary": _branch_witness(
        "transform_control", 9, ("control_9_as_identity", "control_9_as_rotate_cw")
    ),
}
WITNESS_RIVALS = {
    "operation_3_dictionary": ["control_3_as_intersection", "control_3_as_xor"],
    "operation_4_dictionary": ["control_4_as_union", "control_4_as_xor"],
    "operation_6_dictionary": ["control_6_as_union", "control_6_as_intersection"],
    "transform_7_dictionary": ["control_7_as_rotate_cw", "control_7_as_flip"],
    "transform_8_dictionary": ["control_8_as_identity", "control_8_as_flip"],
    "transform_9_dictionary": ["control_9_as_identity", "control_9_as_rotate_cw"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors}")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the intended rule")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors}")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:  # defensive: contracts must report, not crash.
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits:
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
