"""Generator for ARC task 693aba8e59d8 — color-coded rotate and stamp.

A connected color-6 base object is shown near the middle of the input.  Four
single-cell anchors use colors 1, 2, 3, and 4 as rotation codes: identity,
clockwise 90 degrees, 180 degrees, and counterclockwise 90 degrees.  The output
contains only centered color-6 copies at those anchors.

The public curriculum deliberately permutes anchor colors over the canonical
north/east/south/west positions.  Without that contrast, the three canonical
training examples are all solved by a false position-based shortcut.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import product
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "693aba8e59d8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "60c823b90a2d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Use the connected color-6 object as a template.  At each of the four "
    "single-cell anchors, stamp a centered copy rotated according to the anchor "
    "color: 1 = identity, 2 = clockwise 90°, 3 = 180°, 4 = counterclockwise "
    "90°.  Output only the four color-6 stamps."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are 1, 2, 3, 4, and 6",
    "exactly one connected nontrivial color-6 base object has four or five cells",
    "each anchor color 1, 2, 3, and 4 occurs exactly once in a cardinal cross",
    "all four centered rotated stamps fit, remain disjoint, and avoid the source base",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "11..13"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "11..13"},
    "shape_kind": {
        "type": "str",
        "default": "four-shape schedule",
        "valid": "l4|v5|w5|p5",
    },
    "base_orientation": {
        "type": "str",
        "default": "four-orientation schedule",
        "valid": "r0|r90|r180|r270",
    },
    "anchor_phase": {
        "type": "int",
        "default": "0,1,2,3 cycle",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ALLOWED_DIFFICULTIES = frozenset(("easy", "medium", "hard"))
_ALLOWED_OVERRIDES = frozenset(AXES)
_SHAPE_NAMES = ("l4", "v5", "w5", "p5")
_ORIENTATIONS = ("r0", "r90", "r180", "r270")
_ORIENTATION_TURNS = {name: turns for turns, name in enumerate(_ORIENTATIONS)}
_PHASE_COLORS = (
    (1, 2, 3, 4),
    (2, 3, 4, 1),
    (3, 4, 1, 2),
    (4, 1, 2, 3),
)
_DIMENSION_PROFILES = ((11, 11), (13, 13), (11, 13))
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}

# Four free polyominoes, all with a four-element rotational orbit.  Their
# rotational signatures are pairwise disjoint, making both shape and current
# orientation recoverable from pixels rather than hidden metadata.
_SHAPE_CELLS = {
    "l4": frozenset(((0, 0), (1, 0), (2, 0), (2, 1))),
    "v5": frozenset(((0, 0), (0, 1), (0, 2), (1, 0), (2, 0))),
    "w5": frozenset(((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))),
    "p5": frozenset(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),
}


def _normalize_cells(cells: Sequence[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    materialized = tuple(cells)
    if not materialized:
        return frozenset()
    top = min(row for row, _ in materialized)
    left = min(col for _, col in materialized)
    return frozenset((row - top, col - left) for row, col in materialized)


def _rotate_cells_cw(cells: Sequence[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    normalized = _normalize_cells(cells)
    height = max(row for row, _ in normalized) + 1
    return _normalize_cells((col, height - 1 - row) for row, col in normalized)


def _rotate_cells(cells: Sequence[tuple[int, int]], turns: int) -> frozenset[tuple[int, int]]:
    result = _normalize_cells(cells)
    for _ in range(turns % 4):
        result = _rotate_cells_cw(result)
    return result


_SIGNATURE_TO_AXIS: dict[frozenset[tuple[int, int]], tuple[str, str]] = {}
for _shape_name, _shape_cells in _SHAPE_CELLS.items():
    for _orientation_name, _turns in _ORIENTATION_TURNS.items():
        _signature = _rotate_cells(_shape_cells, _turns)
        if _signature in _SIGNATURE_TO_AXIS:
            raise AssertionError("shape/orientation signatures must be unique")
        _SIGNATURE_TO_AXIS[_signature] = (_shape_name, _orientation_name)


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    if difficulty is None:
        band = "medium"
    elif type(difficulty) is str and difficulty in _ALLOWED_DIFFICULTIES:
        band = difficulty
    else:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (not bool)")
        if not 11 <= value <= 13:
            raise ValueError(f"{name} must be in 11..13")

    if "shape_kind" in overrides and overrides["shape_kind"] is not None:
        value = overrides["shape_kind"]
        if type(value) is not str:
            raise TypeError("shape_kind must be a string")
        if value not in _SHAPE_NAMES:
            raise ValueError(f"shape_kind must be one of {_SHAPE_NAMES}")

    if "base_orientation" in overrides and overrides["base_orientation"] is not None:
        value = overrides["base_orientation"]
        if type(value) is not str:
            raise TypeError("base_orientation must be a string")
        if value not in _ORIENTATIONS:
            raise ValueError(f"base_orientation must be one of {_ORIENTATIONS}")

    if "anchor_phase" in overrides and overrides["anchor_phase"] is not None:
        value = overrides["anchor_phase"]
        if type(value) is not int:
            raise TypeError("anchor_phase must be an exact integer (not bool)")
        if not 0 <= value <= 3:
            raise ValueError("anchor_phase must be in 0..3")
    return band


def _draw_int_axis(ctx, name: str, full: tuple[int, int], default: int) -> int:
    lo, hi = full if ctx.overrides.get(name) is not None else (default, default)
    return ctx.draw_int_strict(name, lo, hi)


def _draw_choice_axis(ctx, name: str, domain: Sequence[str], default: str) -> str:
    options = tuple(domain) if ctx.overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


SCHEDULE_PROFILES = tuple(range(64))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the complete 64-step shape/orientation/phase curriculum period."""
    del difficulty
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    return sample_index % 64


def _scheduled_axes(sample_index: int, band: str) -> tuple[int, int, str, str, int]:
    profile = sample_index % 64
    grid_h, grid_w = _DIMENSION_PROFILES[(profile // 4) % len(_DIMENSION_PROFILES)]
    offset = _BAND_OFFSETS[band]
    shape_kind = _SHAPE_NAMES[((profile // 16) + offset) % len(_SHAPE_NAMES)]
    base_orientation = _ORIENTATIONS[((profile // 4) + 2 * offset) % len(_ORIENTATIONS)]
    anchor_phase = profile % 4
    return grid_h, grid_w, shape_kind, base_orientation, anchor_phase


def _bbox_size(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize_cells(cells)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _stamped_cells(
    base_cells: Sequence[tuple[int, int]],
    code: int,
    anchor: tuple[int, int],
) -> frozenset[tuple[int, int]]:
    rotated = _rotate_cells(base_cells, code - 1)
    height, width = _bbox_size(rotated)
    top = anchor[0] - height // 2
    left = anchor[1] - width // 2
    return frozenset((top + row, left + col) for row, col in rotated)


@lru_cache(maxsize=None)
def _layout_candidates(
    height: int,
    width: int,
    base_cells: frozenset[tuple[int, int]],
) -> tuple[tuple[frozenset[tuple[int, int]], dict[str, tuple[int, int]]], ...]:
    base_norm = _normalize_cells(base_cells)
    base_h, base_w = _bbox_size(base_norm)
    candidates = []
    for center_row in range(4, height - 4):
        for center_col in range(4, width - 4):
            base_top = center_row - base_h // 2
            base_left = center_col - base_w // 2
            placed_base = frozenset(
                (base_top + row, base_left + col) for row, col in base_norm
            )
            if any(not (0 <= row < height and 0 <= col < width) for row, col in placed_base):
                continue
            for top_margin, bottom_margin, left_margin, right_margin in product((1, 2), repeat=4):
                anchors = {
                    "north": (top_margin, center_col),
                    "east": (center_row, width - 1 - right_margin),
                    "south": (height - 1 - bottom_margin, center_col),
                    "west": (center_row, left_margin),
                }
                if len(set(anchors.values())) != 4:
                    continue
                if not (
                    anchors["north"][0] < center_row < anchors["south"][0]
                    and anchors["west"][1] < center_col < anchors["east"][1]
                ):
                    continue
                if any(
                    min(abs(ar - br) + abs(ac - bc) for br, bc in placed_base) < 2
                    for ar, ac in anchors.values()
                ):
                    continue
                safe_for_every_phase = True
                for phase_colors in _PHASE_COLORS:
                    stamps = []
                    for code, name in zip(phase_colors, ("north", "east", "south", "west")):
                        stamp = _stamped_cells(base_norm, code, anchors[name])
                        if any(not (0 <= row < height and 0 <= col < width) for row, col in stamp):
                            safe_for_every_phase = False
                            break
                        stamps.append(stamp)
                    if not safe_for_every_phase:
                        break
                    if any(stamp & placed_base for stamp in stamps):
                        safe_for_every_phase = False
                        break
                    if any(stamps[i] & stamps[j] for i in range(4) for j in range(i + 1, 4)):
                        safe_for_every_phase = False
                        break
                if safe_for_every_phase:
                    candidates.append((placed_base, anchors))
    return tuple(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a strict canonical-like rotate-and-stamp input grid."""
    band = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_h, scheduled_w, scheduled_shape, scheduled_orientation, scheduled_phase = (
        _scheduled_axes(sample_index, band)
    )
    height = _draw_int_axis(ctx, "grid_h", (11, 13), scheduled_h)
    width = _draw_int_axis(ctx, "grid_w", (11, 13), scheduled_w)
    shape_kind = _draw_choice_axis(ctx, "shape_kind", _SHAPE_NAMES, scheduled_shape)
    base_orientation = _draw_choice_axis(
        ctx, "base_orientation", _ORIENTATIONS, scheduled_orientation
    )
    anchor_phase = _draw_int_axis(ctx, "anchor_phase", (0, 3), scheduled_phase)

    base_norm = _rotate_cells(
        _SHAPE_CELLS[shape_kind], _ORIENTATION_TURNS[base_orientation]
    )
    candidates = _layout_candidates(height, width, base_norm)
    if not candidates:
        raise ValueError("no valid centered cross layout for requested axes")
    placed_base, anchors = ctx.draw_rng("layout").choice(candidates)

    grid = full_grid(height, width, 0)
    for row, col in placed_base:
        grid[row][col] = 6
    for name, color in zip(
        ("north", "east", "south", "west"), _PHASE_COLORS[anchor_phase]
    ):
        row, col = anchors[name]
        grid[row][col] = color

    expected = {
        "grid_h": height,
        "grid_w": width,
        "shape_kind": shape_kind,
        "base_orientation": base_orientation,
        "anchor_phase": anchor_phase,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"constructed axes {observed!r} != requested axes {expected!r}")
    errors = self_check(grid)
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid cells must be exact ARC integers in 0..9"]
    return []


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    todo = [remaining.pop()]
    while todo:
        row, col = todo.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                todo.append(neighbor)
    return not remaining


def _cross_positions(anchors: list[tuple[int, int, int]]) -> tuple[dict[str, tuple[int, int]], str | None]:
    rows = sorted({row for row, _, _ in anchors})
    cols = sorted({col for _, col, _ in anchors})
    if len(anchors) != 4 or len(rows) != 3 or len(cols) != 3:
        return {}, "anchors must occupy a four-arm cardinal cross"
    top, middle_row, bottom = rows
    left, middle_col, right = cols
    expected = {
        "north": (top, middle_col),
        "east": (middle_row, right),
        "south": (bottom, middle_col),
        "west": (middle_row, left),
    }
    if {(row, col) for row, col, _ in anchors} != set(expected.values()):
        return {}, "anchors must occupy north/east/south/west cross positions"
    return expected, None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not 11 <= height <= 13:
        errors.append(f"grid height {height} is outside 11..13")
    if not 11 <= width <= 13:
        errors.append(f"grid width {width} is outside 11..13")

    palette = {value for row in grid for value in row}
    expected_palette = {0, 1, 2, 3, 4, 6}
    if palette != expected_palette:
        errors.append(f"palette {sorted(palette)} must equal {sorted(expected_palette)}")

    anchors = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (1, 2, 3, 4)
    ]
    counts = {color: sum(value == color for row in grid for value in row) for color in (1, 2, 3, 4)}
    if any(counts[color] != 1 for color in counts):
        errors.append(f"anchor colors must occur exactly once each; counts={counts}")
    positions, cross_error = _cross_positions(anchors)
    if cross_error:
        errors.append(cross_error)

    base_absolute = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    }
    if len(base_absolute) not in (4, 5):
        errors.append(f"color-6 base has {len(base_absolute)} cells; expected 4 or 5")
    if base_absolute and not _connected(base_absolute):
        errors.append("color-6 base must be one 4-connected component")
    base_norm = _normalize_cells(base_absolute)
    if base_norm:
        base_h, base_w = _bbox_size(base_norm)
        if base_h > 3 or base_w > 3:
            errors.append("color-6 base bounding box must fit within 3x3")
        orbit = {_rotate_cells(base_norm, turns) for turns in range(4)}
        if len(orbit) == 1:
            errors.append("color-6 base must not be rotationally invariant")
    else:
        orbit = set()

    shape_axis = _SIGNATURE_TO_AXIS.get(base_norm)
    position_colors: tuple[int, ...] | None = None
    anchor_phase: int | None = None
    if positions and len(anchors) == 4:
        by_position = {(row, col): value for row, col, value in anchors}
        position_colors = tuple(
            by_position[positions[name]] for name in ("north", "east", "south", "west")
        )
        if position_colors in _PHASE_COLORS:
            anchor_phase = _PHASE_COLORS.index(position_colors)

    stamp_sets: list[frozenset[tuple[int, int]]] = []
    if base_norm and len(anchors) == 4:
        for row, col, color in anchors:
            stamp = _stamped_cells(base_norm, color, (row, col))
            if any(not (0 <= rr < height and 0 <= cc < width) for rr, cc in stamp):
                errors.append(f"anchor color {color} would clip its centered stamp")
            stamp_sets.append(stamp)
        if any(stamp & base_absolute for stamp in stamp_sets):
            errors.append("stamped outputs must not overlap the source base")
        if any(stamp_sets[i] & stamp_sets[j] for i in range(len(stamp_sets)) for j in range(i + 1, len(stamp_sets))):
            errors.append("the four stamped outputs must be disjoint")

    if base_absolute and anchors:
        for row, col, color in anchors:
            if min(abs(row - br) + abs(col - bc) for br, bc in base_absolute) < 2:
                errors.append(f"anchor color {color} must be isolated from the base")

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "anchors": anchors,
        "positions": positions,
        "position_colors": position_colors,
        "anchor_phase": anchor_phase,
        "base_absolute": base_absolute,
        "base_norm": base_norm,
        "shape_axis": shape_axis,
        "stamp_sets": stamp_sets,
        "orbit_size": len(orbit),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["shape_axis"] is None:
        raise ValueError("base shape is lawful but outside the generated shape axis")
    if analysis["anchor_phase"] is None:
        raise ValueError("anchor colors are lawful but outside the cyclic phase axis")
    shape_kind, base_orientation = analysis["shape_axis"]
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "shape_kind": shape_kind,
        "base_orientation": base_orientation,
        "anchor_phase": analysis["anchor_phase"],
    }


def _rule_from_codes(grid, code_for_anchor: Callable[[int, int, int, dict[str, tuple[int, int]]], int]):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for row, col, color in sorted(analysis["anchors"]):
        code = code_for_anchor(row, col, color, analysis["positions"])
        for rr, cc in _stamped_cells(analysis["base_norm"], code, (row, col)):
            if 0 <= rr < analysis["grid_h"] and 0 <= cc < analysis["grid_w"]:
                output[rr][cc] = 6
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the selected Racket rule."""
    return _rule_from_codes(grid, lambda _row, _col, color, _positions: color)


def _position_encoded(grid) -> list[list[int]]:
    position_codes = {"north": 1, "east": 2, "south": 3, "west": 4}

    def code(row, col, _color, positions):
        for name, point in positions.items():
            if point == (row, col):
                return position_codes[name]
        raise ValueError("anchor is outside the cardinal cross")

    return _rule_from_codes(grid, code)


def _no_rotation(grid) -> list[list[int]]:
    return _rule_from_codes(grid, lambda _row, _col, _color, _positions: 1)


def _swap_quarter_turns(grid) -> list[list[int]]:
    mapping = {1: 1, 2: 4, 3: 3, 4: 2}
    return _rule_from_codes(grid, lambda _row, _col, color, _positions: mapping[color])


SEMANTIC_RIVALS: dict[str, Callable] = {
    "position_encoded": _position_encoded,
    "no_rotation": _no_rotation,
    "swap_quarter_turns": _swap_quarter_turns,
}
CANONICAL_SHORTCUTS: dict[str, Callable] = {
    "position_encoded": _position_encoded,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_permuted_anchor_roles(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["position_colors"] != _PHASE_COLORS[0]


def _has_all_four_rotation_codes(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and {color for _, _, color in analysis["anchors"]} == {1, 2, 3, 4}
        and analysis["orbit_size"] == 4
    )


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "permuted_anchor_roles": _has_permuted_anchor_roles,
    "all_four_rotation_codes": _has_all_four_rotation_codes,
}
WITNESS_RIVALS = {
    "permuted_anchor_roles": ("position_encoded",),
    "all_four_rotation_codes": ("no_rotation", "swap_quarter_turns"),
}


def _pair_errors(pair: Any, label: str, *, output_required: bool = False) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} is missing an input grid"]
    if output_required and pair.get("output") is None:
        return [f"{label} is missing an output grid"]
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError) as exc:
        return [f"{label} is outside the task grammar: {exc}"]
    if pair.get("output") is not None and pair["output"] != expected:
        return [f"{label} output disagrees with the color-coded rotation rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a declared shortcut survives every demo."""
    if not isinstance(demos, list):
        return ["demonstrations must be a list"]
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"at least {EXAMPLES_NEEDED} demonstrations are required")
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}", output_required=True))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"declared competitor {name!r} survives every demonstration")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Return named malformed near-misses for validator regression tests."""
    base = generate(991, 0, difficulty="medium")
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_anchor = deepcopy(base)
    for row, values in enumerate(missing_anchor):
        for col, value in enumerate(values):
            if value == 4:
                missing_anchor[row][col] = 0
    fixtures.append(("missing_anchor_4", missing_anchor))

    duplicate_anchor = deepcopy(base)
    for row, values in enumerate(duplicate_anchor):
        for col, value in enumerate(values):
            if value == 4:
                duplicate_anchor[row][col] = 1
    fixtures.append(("duplicate_anchor_color", duplicate_anchor))

    disconnected = deepcopy(base)
    base_cells = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 6]
    row, col = base_cells[-1]
    disconnected[row][col] = 0
    for candidate in ((0, 0), (0, len(disconnected[0]) - 1), (len(disconnected) - 1, 0)):
        if disconnected[candidate[0]][candidate[1]] == 0:
            disconnected[candidate[0]][candidate[1]] = 6
            break
    fixtures.append(("disconnected_base", disconnected))

    symmetric = deepcopy(base)
    for row, values in enumerate(symmetric):
        for col, value in enumerate(values):
            if value == 6:
                symmetric[row][col] = 0
    center_row, center_col = len(symmetric) // 2, len(symmetric[0]) // 2
    for dr, dc in ((-1, -1), (-1, 0), (0, -1), (0, 0)):
        symmetric[center_row + dr][center_col + dc] = 6
    fixtures.append(("rotationally_symmetric_base", symmetric))

    clipped = deepcopy(base)
    old = next((r, c) for r, row in enumerate(clipped) for c, value in enumerate(row) if value == 1)
    clipped[old[0]][old[1]] = 0
    clipped[0][0] = 1
    fixtures.append(("clipped_stamp", clipped))

    extra_color = deepcopy(base)
    extra_color[0][0] = 9
    fixtures.append(("extra_color", extra_color))
    return fixtures
