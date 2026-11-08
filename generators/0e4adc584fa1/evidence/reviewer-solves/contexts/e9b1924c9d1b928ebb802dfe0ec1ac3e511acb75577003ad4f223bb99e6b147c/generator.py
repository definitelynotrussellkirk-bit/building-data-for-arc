"""Rotate one cropped object according to an isolated color-coded marker.

The selected Racket rule is authoritative.  This module owns a deliberately
small, observable input grammar and supplies review-only Python mirrors,
semantic rivals, and witnesses.  Four consecutive default samples cover the
full transform table: 1=identity, 2=clockwise, 3=half-turn, 4=counterclockwise.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "0e4adc584fa1"
VERSION = "2.0.0"
RULE_HASH = "314b2cc8cd15"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "A 0-background grid contains one connected 5..9-colored object and one "
    "isolated control marker.  Marker colors 1,2,3,4 request identity, 90° "
    "clockwise, 180°, and 90° counterclockwise transforms.  Crop the object "
    "tightly and apply the requested transform.  Consecutive four-example "
    "windows cover all four codes; canonical-size anchors remain in every band."
)

INVARIANTS = [
    "rectangular ARC grid, height 8..12 and width 9..14, background 0",
    "exactly one isolated color-1..4 control marker",
    "one 4-connected multi-cell object in one to three colors from 5..9",
    "control marker is separated from the object and lies before or after it in row-major order",
    "generated object crops have four distinct quarter-turn orientations",
]

SHAPE_PROFILES = (
    "canonical_3x3",
    "wide_3x4",
    "tall_4x3",
    "large_4x4",
)
MARKER_ORDERS = ("before", "after")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical height",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical width",
        "valid": "9..14",
    },
    "control_code": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
    },
    "shape_profile": {
        "type": "str",
        "default": "band-aware schedule",
        "valid": "|".join(SHAPE_PROFILES),
    },
    "shape_colors": {
        "type": "int",
        "default": "2",
        "valid": "1..3",
    },
    "marker_order": {
        "type": "str",
        "default": "balanced before/after",
        "valid": "|".join(MARKER_ORDERS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = ((9, 11), (10, 10), (8, 12), (9, 9), (10, 12))
_CANONICAL_SIZE_CODE = {
    (9, 11): 2,
    (10, 10): 3,
    (8, 12): 4,
    (9, 9): 1,
    (10, 12): 2,
}
_PROFILE_DIMS = {
    "canonical_3x3": (3, 3),
    "wide_3x4": (3, 4),
    "tall_4x3": (4, 3),
    "large_4x4": (4, 4),
}

# Every template is 4-connected, spans its advertised bbox, and has four
# distinct C4 orientations even before colors are assigned.
_TEMPLATES: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {
    "canonical_3x3": (
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
        ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
    "wide_3x4": (
        ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 2), (2, 3)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 3)),
    ),
    "tall_4x3": (
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
    ),
    "large_4x4": (
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3)),
        ((0, 3), (1, 1), (1, 2), (1, 3), (2, 1), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (3, 2), (3, 3)),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the scheduled control code; any four consecutive indexes cover 1..4."""
    del difficulty
    return (int(seed) + int(sample_index)) % 4 + 1


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _rotate(grid: Sequence[Sequence[int]], turns: int) -> list[list[int]]:
    result = [list(row) for row in grid]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _orbit_size(grid: Sequence[Sequence[int]]) -> int:
    return len({_freeze(_rotate(grid, turns)) for turns in range(4)})


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be literal ARC integers 0..9"]
    return []


def _isolated_controls(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    controls = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] not in (1, 2, 3, 4):
                continue
            if all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] == 0
                for dr, dc in _DIR4
            ):
                controls.append((row, col))
    return controls


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    start = min(cells)
    seen, todo = {start}, [start]
    while todo:
        row, col = todo.pop()
        for dr, dc in _DIR4:
            neighbor = row + dr, col + dc
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen == cells


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    controls = _isolated_controls(grid)
    control_set = set(controls)
    shape_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in control_set
    }
    result: dict[str, Any] = {
        "errors": [],
        "height": height,
        "width": width,
        "controls": controls,
        "shape_cells": shape_cells,
    }
    if controls:
        row, col = controls[-1]
        result["control_code"] = grid[row][col]
    if shape_cells:
        r0 = min(row for row, _ in shape_cells)
        r1 = max(row for row, _ in shape_cells)
        c0 = min(col for _, col in shape_cells)
        c1 = max(col for _, col in shape_cells)
        crop = [list(grid[row][c0:c1 + 1]) for row in range(r0, r1 + 1)]
        dims = (r1 - r0 + 1, c1 - c0 + 1)
        profile = next((name for name, value in _PROFILE_DIMS.items() if value == dims), None)
        flat_shape = sorted(row * width + col for row, col in shape_cells)
        marker_order = None
        if len(controls) == 1:
            marker_flat = controls[0][0] * width + controls[0][1]
            if marker_flat < flat_shape[0]:
                marker_order = "before"
            elif marker_flat > flat_shape[-1]:
                marker_order = "after"
            else:
                marker_order = "interleaved"
        result.update(
            {
                "bbox": (r0, c0, r1, c1),
                "crop": crop,
                "shape_profile": profile,
                "shape_colors": len({grid[row][col] for row, col in shape_cells}),
                "shape_palette": sorted({grid[row][col] for row, col in shape_cells}),
                "marker_order": marker_order,
            }
        )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the documented generator domain without rejecting canonical symmetry."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    height, width = analysis["height"], analysis["width"]
    if not 8 <= height <= 12:
        errors.append(f"height must be in 8..12, got {height}")
    if not 9 <= width <= 14:
        errors.append(f"width must be in 9..14, got {width}")
    controls = analysis["controls"]
    if len(controls) != 1:
        errors.append(f"expected exactly one isolated color-1..4 control marker, found {len(controls)}")
    shape_cells = analysis["shape_cells"]
    if not 5 <= len(shape_cells) <= 10:
        errors.append(f"object must contain 5..10 cells, found {len(shape_cells)}")
    if shape_cells and not _connected(shape_cells):
        errors.append("all non-control foreground cells must form one 4-connected object")
    if shape_cells:
        palette = analysis["shape_palette"]
        if not set(palette) <= set(range(5, 10)):
            errors.append(f"object colors must come from 5..9, got {palette}")
        if not 1 <= analysis["shape_colors"] <= 3:
            errors.append("object must use one to three distinct colors")
        if analysis["shape_profile"] is None:
            bbox = analysis["bbox"]
            errors.append(
                "object bbox must be one of 3x3, 3x4, 4x3, or 4x4; "
                f"got {bbox[2] - bbox[0] + 1}x{bbox[3] - bbox[1] + 1}"
            )
    if len(controls) == 1 and shape_cells:
        marker = controls[0]
        if any(max(abs(marker[0] - row), abs(marker[1] - col)) <= 1 for row, col in shape_cells):
            errors.append("control marker must be separated from the object by a one-cell moat")
        if analysis["marker_order"] not in MARKER_ORDERS:
            errors.append("control marker must be before or after the object in row-major order")
    return errors


def _draw_exact_int(ctx, name: str, default: int, low: int, high: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default, default)


def _draw_exact_choice(ctx, name: str, default: str, options: Sequence[str]) -> str:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, tuple(options))
    return ctx.draw_choice(name, (default,))


def _default_profile(seed: int, sample_index: int, difficulty: str | None) -> str:
    patterns = {
        "easy": ("canonical_3x3", "canonical_3x3", "wide_3x4", "canonical_3x3"),
        "medium": ("canonical_3x3", "wide_3x4", "canonical_3x3", "tall_4x3"),
        "hard": ("canonical_3x3", "large_4x4", "canonical_3x3", "tall_4x3"),
    }
    pattern = patterns[difficulty or "medium"]
    return pattern[(int(seed) // 7 + int(sample_index)) % len(pattern)]


def _placement_candidates(
    height: int,
    width: int,
    cells: Sequence[tuple[int, int]],
    marker_order: str,
) -> list[tuple[int, int, int, int]]:
    shape_h = max(row for row, _ in cells) + 1
    shape_w = max(col for _, col in cells) + 1
    candidates = []
    for r0 in range(height - shape_h + 1):
        for c0 in range(width - shape_w + 1):
            placed = {(r0 + row, c0 + col) for row, col in cells}
            flat = sorted(row * width + col for row, col in placed)
            for marker_row in range(height):
                for marker_col in range(width):
                    marker = marker_row, marker_col
                    if marker in placed:
                        continue
                    marker_flat = marker_row * width + marker_col
                    if marker_order == "before" and marker_flat >= flat[0]:
                        continue
                    if marker_order == "after" and marker_flat <= flat[-1]:
                        continue
                    if any(
                        max(abs(marker_row - row), abs(marker_col - col)) <= 1
                        for row, col in placed
                    ):
                        continue
                    candidates.append((r0, c0, marker_row, marker_col))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown or removed override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "control_code", "shape_colors"):
        if overrides.get(name) is not None and (
            isinstance(overrides[name], bool) or not isinstance(overrides[name], int)
        ):
            raise TypeError(f"{name} must be an integer")
    for name in ("shape_profile", "marker_order"):
        if overrides.get(name) is not None and not isinstance(overrides[name], str):
            raise TypeError(f"{name} must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # A four-sample group shares one canonical canvas size while its code cycles
    # through all four transforms.  This directly breaks the canonical size→code
    # shortcut instead of hoping random sampling eventually does.
    dim_index = (3 * int(seed) + int(sample_index) // 4) % len(_CANONICAL_DIMS)
    default_height, default_width = _CANONICAL_DIMS[dim_index]
    height = _draw_exact_int(ctx, "grid_h", default_height, 8, 12)
    width = _draw_exact_int(ctx, "grid_w", default_width, 9, 14)
    code = _draw_exact_int(ctx, "control_code", schedule_profile(seed, sample_index), 1, 4)
    profile = _draw_exact_choice(
        ctx,
        "shape_profile",
        _default_profile(seed, sample_index, difficulty),
        SHAPE_PROFILES,
    )
    color_count = _draw_exact_int(ctx, "shape_colors", 2, 1, 3)
    default_order = MARKER_ORDERS[(int(seed) + int(sample_index) // 2) % 2]
    marker_order = _draw_exact_choice(ctx, "marker_order", default_order, MARKER_ORDERS)

    rng = ctx.draw_rng("layout")
    template = rng.choice(_TEMPLATES[profile])
    colors = rng.sample(range(5, 10), color_count)
    ordered_cells = list(template)
    rng.shuffle(ordered_cells)
    color_by_cell: dict[tuple[int, int], int] = {}
    for index, cell in enumerate(ordered_cells):
        # The first `color_count` cells force exact palette cardinality; the
        # rest vary without changing any advertised axis.
        color_by_cell[cell] = colors[index] if index < color_count else rng.choice(colors)

    candidates = _placement_candidates(height, width, template, marker_order)
    if not candidates:
        raise ValueError(
            f"no placement supports grid={height}x{width}, profile={profile}, "
            f"marker_order={marker_order}"
        )
    r0, c0, marker_row, marker_col = rng.choice(candidates)
    grid = full_grid(height, width, 0)
    for (row, col), color in color_by_cell.items():
        grid[r0 + row][c0 + col] = color
    grid[marker_row][marker_col] = code

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    crop = _analyze(grid)["crop"]
    if _orbit_size(crop) != 4:
        raise AssertionError("generated object crop is rotationally ambiguous")
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "control_code": analysis["control_code"],
        "shape_profile": analysis["shape_profile"],
        "shape_colors": analysis["shape_colors"],
        "marker_order": analysis["marker_order"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical scale/morphology without requiring its symmetries."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        errors.append("canvas dimensions are outside the five canonical profiles")
    if analysis["shape_profile"] != "canonical_3x3":
        errors.append("canonical object crop is 3x3")
    if analysis["shape_colors"] != 2:
        errors.append("canonical object uses exactly two colors")
    if not 5 <= len(analysis["shape_cells"]) <= 7:
        errors.append("canonical object has five to seven occupied cells")
    return errors


def _shape_crop(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if not analysis.get("shape_cells"):
        raise ValueError("grid has no object to crop")
    return [list(row) for row in analysis["crop"]]


def _control_code(grid) -> int:
    controls = _isolated_controls(grid)
    if not controls:
        raise ValueError("grid has no isolated control")
    row, col = controls[-1]
    return grid[row][col]


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; the selected Racket rule remains authoritative."""
    return _rotate(_shape_crop(grid), _control_code(grid) - 1)


def _identity_only(grid):
    return _shape_crop(grid)


def _clockwise_for_all_nonidentity(grid):
    return _rotate(_shape_crop(grid), 0 if _control_code(grid) == 1 else 1)


def _reverse_quarter_turns(grid):
    turns = {1: 0, 2: 3, 3: 2, 4: 1}[_control_code(grid)]
    return _rotate(_shape_crop(grid), turns)


def _off_by_one_rotation(grid):
    return _rotate(_shape_crop(grid), _control_code(grid))


def _canonical_size_to_code(grid):
    inferred = _CANONICAL_SIZE_CODE.get((len(grid), len(grid[0])), 1)
    return _rotate(_shape_crop(grid), inferred - 1)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity_only": _identity_only,
    "clockwise_for_all_nonidentity": _clockwise_for_all_nonidentity,
    "reverse_quarter_turns": _reverse_quarter_turns,
    "off_by_one_rotation": _off_by_one_rotation,
    "canonical_size_to_code": _canonical_size_to_code,
}
SEMANTIC_WITNESSES = {
    "code_1_identity": lambda grid: _control_code(grid) == 1,
    "code_2_clockwise": lambda grid: _control_code(grid) == 2,
    "code_3_half_turn": lambda grid: _control_code(grid) == 3,
    "code_4_counterclockwise": lambda grid: _control_code(grid) == 4,
    "size_code_decoupled": lambda grid: _control_code(grid)
    != _CANONICAL_SIZE_CODE.get((len(grid), len(grid[0])), 1),
}
WITNESS_RIVALS = {
    "code_1_identity": ["off_by_one_rotation"],
    "code_2_clockwise": ["identity_only", "reverse_quarter_turns"],
    "code_3_half_turn": ["identity_only", "clockwise_for_all_nonidentity"],
    "code_4_counterclockwise": ["identity_only", "reverse_quarter_turns"],
    "size_code_decoupled": ["canonical_size_to_code"],
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"canonical_size_to_code": _canonical_size_to_code}


def lesson_identifiable(demos, query) -> list[str]:
    """Check labels and finite identifiability against the declared rival class.

    This is intentionally a relative claim, not proof against every program.  A
    four-demo lesson must expose at least three code values and refute every
    declared rival that would change the query answer.  The production schedule
    exposes all four; the three-code floor keeps every held-out rotation useful.
    """
    errors: list[str] = []
    demo_codes: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo:
            errors.append(f"demo {index} is malformed")
            continue
        grid = demo["input"]
        findings = self_check(grid)
        if findings:
            errors.append(f"demo {index} is outside the generator domain: {findings[0]}")
            continue
        expected = rule_mirror(grid)
        if demo.get("output") != expected:
            errors.append(f"demo {index} label disagrees with the rotation rule")
        demo_codes.add(_control_code(grid))
    if len(demo_codes) < 3:
        errors.append(f"demos expose only {len(demo_codes)} distinct control codes; need at least 3")

    if not isinstance(query, dict) or "input" not in query:
        return errors + ["query is malformed"]
    query_grid = query["input"]
    findings = self_check(query_grid)
    if findings:
        return errors + [f"query is outside the generator domain: {findings[0]}"]
    expected = rule_mirror(query_grid)
    if query.get("output") is not None and query.get("output") != expected:
        errors.append("query label disagrees with the rotation rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo.get("output") for demo in demos):
            if rival(query_grid) != expected:
                errors.append(f"rival {name} fits all demos but changes the query answer")
    return errors


def mutation_fixtures():
    """Task-local malformed near-misses for self-check power regression."""
    good = generate(17, 0, difficulty="medium")
    analysis = _analyze(good)
    marker = analysis["controls"][0]
    shape = sorted(analysis["shape_cells"])
    fixtures = []

    no_control = deepcopy(good)
    no_control[marker[0]][marker[1]] = 0
    fixtures.append(("no_control", no_control))

    touching_marker = deepcopy(good)
    touching_marker[marker[0]][marker[1]] = 0
    adjacent = next(
        (row + dr, col + dc)
        for row, col in shape
        for dr, dc in _DIR4
        if 0 <= row + dr < len(good)
        and 0 <= col + dc < len(good[0])
        and touching_marker[row + dr][col + dc] == 0
    )
    touching_marker[adjacent[0]][adjacent[1]] = analysis["control_code"]
    fixtures.append(("control_touches_object", touching_marker))

    bad_object_color = deepcopy(good)
    row, col = shape[len(shape) // 2]
    bad_object_color[row][col] = 4
    fixtures.append(("object_uses_control_color", bad_object_color))

    disconnected = deepcopy(good)
    extra = next(
        (row, col)
        for row in range(len(good))
        for col in range(len(good[0]))
        if disconnected[row][col] == 0
        and (row, col) != marker
        and all(max(abs(row - rr), abs(col - cc)) > 1 for rr, cc in shape)
    )
    disconnected[extra[0]][extra[1]] = analysis["shape_palette"][0]
    fixtures.append(("disconnected_object_cell", disconnected))

    second_control = deepcopy(good)
    second_control[extra[0]][extra[1]] = 2 if analysis["control_code"] != 2 else 3
    fixtures.append(("second_isolated_control", second_control))

    ragged = deepcopy(good)
    ragged[-1] = ragged[-1][:-1]
    fixtures.append(("ragged_grid", ragged))
    return fixtures
