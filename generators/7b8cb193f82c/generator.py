"""Generator for arc_additional_puzzle_bank_volume5:H35.

Each closed rectangular color-8 frame contains a rectangular zero hole.  The
hole is painted by inward depth: depth 1 is color 2, depth 2 is color 3, then
2/3 continue alternating.  Every five consecutive ordinary examples include a combined thickness-2
multi-frame shallow case plus depths 2/3/4/5, so the lesson cannot collapse to
a one- or two-ring lookup table.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7b8cb193f82c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # exact overrides, canonical anchoring, semantic schedule
RULE_HASH = "5791d4c7a1b1"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A black grid contains 1-3 disjoint closed rectangular color-8 frames. "
    "For each frame, fill its rectangular zero interior by inward layer depth: "
    "the outer layer becomes red (2), the next green (3), then red/green "
    "continue alternating. Frame thickness, position, count, canvas size, and "
    "maximum demonstrated depth are exact observable axes."
)

INVARIANTS = [
    "the input uses only colors 0 and 8",
    "there are exactly 1-3 disjoint complete rectangular color-8 annuli",
    "all frames in one instance have the same thickness, either 1 or 2",
    "every frame encloses a nonempty rectangular zero hole",
    "the output changes only hole cells, alternating 2/3 by local inward depth",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-residue canonical/generalized schedule",
        "valid": "9..24",
    },
    "grid_w": {
        "type": "int",
        "default": "five-residue canonical/generalized schedule",
        "valid": "10..24",
    },
    "n_frames": {
        "type": "int",
        "default": "1, with 2- and 3-frame scheduled witnesses",
        "valid": "1..3",
    },
    "thickness": {
        "type": "int",
        "default": "1, with a scheduled thickness-2 distractor",
        "valid": "1..2",
    },
    "max_depth": {
        "type": "int",
        "default": "scheduled depths 1 through 5",
        "valid": "1..5",
    },
}

_AXIS_RANGES = {
    "grid_h": (9, 24),
    "grid_w": (10, 24),
    "n_frames": (1, 3),
    "thickness": (1, 2),
    "max_depth": (1, 5),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

# Declaring the matrix opts into strict rejection accounting.  Feasible tuples
# are accepted; genuinely impossible full tuples raise IncompatibleOverrides
# with the exact fixed axis names attached.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


class IncompatibleOverrides(ValueError):
    """A valid-axis tuple that cannot fit on its exact requested canvas."""

    def __init__(self, values: dict[str, int]):
        self.incompatible_axes = tuple(sorted(values))
        rendered = ", ".join(f"{key}={values[key]}" for key in sorted(values))
        super().__init__(f"incompatible overrides: {rendered}")


def _validate_public_scalars(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    _validate_public_scalars(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Five-residue curriculum; every five-demo window covers every branch."""
    _validate_public_scalars(seed, sample_index, difficulty)
    return sample_index % 5


SCHEDULE_PROFILES = tuple(range(5))


def _scheduled_defaults(sample_index: int, difficulty: Any) -> dict[str, int]:
    residue = int(sample_index) % 5
    if residue == 0:
        # One profile carries both controls that do not affect the rule:
        # multiple frames and a common thickness-2 wall. Eight hole cells keep
        # the transformation visible (>4% of this canonical-height canvas).
        return {"grid_h": 9, "grid_w": 22, "n_frames": 3, "thickness": 2, "max_depth": 1}
    if residue == 1:
        return {"grid_h": 10, "grid_w": 10, "n_frames": 1, "thickness": 1, "max_depth": 2}
    if residue == 2:
        return {"grid_h": 10, "grid_w": 12, "n_frames": 1, "thickness": 1, "max_depth": 3}
    if residue == 3:
        return {"grid_h": 11, "grid_w": 11, "n_frames": 1, "thickness": 1, "max_depth": 4}
    h, w = {
        "easy": (13, 15),
        "medium": (17, 19),
        "hard": (21, 23),
    }.get(difficulty, (17, 19))
    return {"grid_h": h, "grid_w": w, "n_frames": 1, "thickness": 1, "max_depth": 5}


def _frame_holes(n_frames: int, max_depth: int, *, rotated: bool) -> list[tuple[int, int]]:
    if max_depth == 1:
        holes = [(1, 4)] + [(1, 2)] * (n_frames - 1)
    else:
        holes = [(2 * max_depth - 1, 2 * max_depth)] + [(1, 2)] * (n_frames - 1)
    if rotated:
        holes = [(width, height) for height, width in holes]
    return holes


def _frame_sizes(
    n_frames: int, thickness: int, max_depth: int, *, rotated: bool
) -> list[tuple[int, int]]:
    return [
        (hole_h + 2 * thickness, hole_w + 2 * thickness)
        for hole_h, hole_w in _frame_holes(n_frames, max_depth, rotated=rotated)
    ]


def _layout_modes(
    h: int, w: int, n_frames: int, thickness: int, max_depth: int
) -> list[tuple[str, bool, list[tuple[int, int]]]]:
    modes: list[tuple[str, bool, list[tuple[int, int]]]] = []
    for rotated in (False, True):
        sizes = _frame_sizes(n_frames, thickness, max_depth, rotated=rotated)
        if max(fh for fh, _fw in sizes) <= h and sum(fw for _fh, fw in sizes) + n_frames - 1 <= w:
            modes.append(("horizontal", rotated, sizes))
        if sum(fh for fh, _fw in sizes) + n_frames - 1 <= h and max(fw for _fh, fw in sizes) <= w:
            modes.append(("vertical", rotated, sizes))
    return modes


def _ordered_values(name: str, preferred: int, fixed: int | None) -> list[int]:
    if fixed is not None:
        return [fixed]
    lo, hi = _AXIS_RANGES[name]
    return sorted(range(lo, hi + 1), key=lambda value: (abs(value - preferred), value))


def _resolve_axes(defaults: dict[str, int], overrides: dict[str, Any]) -> dict[str, int]:
    fixed = {
        name: int(value)
        for name, value in overrides.items()
        if value is not None
    }
    if not fixed:
        values = dict(defaults)
        if not _layout_modes(**{
            "h": values["grid_h"],
            "w": values["grid_w"],
            "n_frames": values["n_frames"],
            "thickness": values["thickness"],
            "max_depth": values["max_depth"],
        }):
            raise RuntimeError(f"scheduled defaults are not packable: {values}")
        return values

    orders = {
        name: _ordered_values(name, defaults[name], fixed.get(name))
        for name in AXES
    }
    # Shape controls are tried before canvas expansion so an isolated size
    # override remains exact while unspecified curriculum details adapt.
    for n_frames, thickness, max_depth, grid_h, grid_w in product(
        orders["n_frames"],
        orders["thickness"],
        orders["max_depth"],
        orders["grid_h"],
        orders["grid_w"],
    ):
        if _layout_modes(grid_h, grid_w, n_frames, thickness, max_depth):
            return {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "n_frames": n_frames,
                "thickness": thickness,
                "max_depth": max_depth,
            }
    raise IncompatibleOverrides(fixed)


def _draw_axis(ctx, overrides: dict[str, Any], name: str, selected: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if overrides.get(name) is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, selected, selected))


def _random_composition(total: int, slots: int, rng) -> list[int]:
    """Uniform-enough deterministic composition used only for surface placement."""
    if slots <= 1:
        return [total]
    cuts = sorted(rng.randint(0, total) for _ in range(slots - 1))
    points = [0, *cuts, total]
    return [points[index + 1] - points[index] for index in range(slots)]


def _place_frames(
    h: int,
    w: int,
    sizes: list[tuple[int, int]],
    mode: str,
    rng,
) -> list[tuple[int, int, int, int]]:
    n_frames = len(sizes)
    placed: list[tuple[int, int, int, int]] = []
    if mode == "horizontal":
        spare = w - sum(fw for _fh, fw in sizes) - (n_frames - 1)
        spacing = _random_composition(spare, n_frames + 1, rng)
        left = spacing[0]
        for index, (fh, fw) in enumerate(sizes):
            top = rng.randint(0, h - fh)
            placed.append((top, left, fh, fw))
            left += fw
            if index + 1 < n_frames:
                left += 1 + spacing[index + 1]
        return placed

    spare = h - sum(fh for fh, _fw in sizes) - (n_frames - 1)
    spacing = _random_composition(spare, n_frames + 1, rng)
    top = spacing[0]
    for index, (fh, fw) in enumerate(sizes):
        left = rng.randint(0, w - fw)
        placed.append((top, left, fh, fw))
        top += fh
        if index + 1 < n_frames:
            top += 1 + spacing[index + 1]
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; canonical Racket is output authority."""
    _validate_call(seed, sample_index, difficulty, overrides)
    defaults = _scheduled_defaults(sample_index, difficulty)
    selected = _resolve_axes(defaults, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    values = {
        name: _draw_axis(ctx, overrides, name, selected[name])
        for name in AXES
    }
    modes = _layout_modes(
        values["grid_h"],
        values["grid_w"],
        values["n_frames"],
        values["thickness"],
        values["max_depth"],
    )
    if not modes:
        fixed = {
            name: int(value)
            for name, value in overrides.items()
            if value is not None
        }
        raise IncompatibleOverrides(fixed)
    layout_rng = ctx.draw_rng("frame_layout")
    mode, rotated, sizes = layout_rng.choice(modes)
    placements = _place_frames(
        values["grid_h"], values["grid_w"], sizes, mode, layout_rng
    )

    grid = full_grid(values["grid_h"], values["grid_w"], 0)
    thickness = values["thickness"]
    for top, left, frame_h, frame_w in placements:
        for row in range(top, top + frame_h):
            for col in range(left, left + frame_w):
                grid[row][col] = 8
        for row in range(top + thickness, top + frame_h - thickness):
            for col in range(left + thickness, left + frame_w - thickness):
                grid[row][col] = 0
    return grid


def _neighbors4(row: int, col: int) -> Iterable[tuple[int, int]]:
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _components_of_eight(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 8
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for next_row, next_col in _neighbors4(row, col):
                point = (next_row, next_col)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def _matching_thickness(
    component: set[tuple[int, int]],
    bbox: tuple[int, int, int, int],
) -> int | None:
    r1, c1, r2, c2 = bbox
    frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
    for thickness in (1, 2):
        if frame_h <= 2 * thickness or frame_w <= 2 * thickness:
            continue
        expected = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
            if min(row - r1, r2 - row, col - c1, c2 - col) < thickness
        }
        if component == expected:
            return thickness
    return None


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]
    height = len(grid)
    palette = {value for row in grid for value in row}
    if not palette <= {0, 8}:
        errors.append(f"input palette must be a subset of {{0,8}}, got {sorted(palette)}")
    if not (9 <= height <= 24):
        errors.append(f"grid height must be 9..24, got {height}")
    if not (10 <= width <= 24):
        errors.append(f"grid width must be 10..24, got {width}")

    components = _components_of_eight(grid)
    if not (1 <= len(components) <= 3):
        errors.append(f"expected 1..3 color-8 frame components, found {len(components)}")

    frames: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        rows = [row for row, _col in component]
        cols = [col for _row, col in component]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        thickness = _matching_thickness(component, bbox)
        if thickness is None:
            errors.append(f"component {index} is not a complete thickness-1/2 rectangular annulus")
            continue
        r1, c1, r2, c2 = bbox
        hole_h = r2 - r1 + 1 - 2 * thickness
        hole_w = c2 - c1 + 1 - 2 * thickness
        hole_cells = {
            (row, col)
            for row in range(r1 + thickness, r2 - thickness + 1)
            for col in range(c1 + thickness, c2 - thickness + 1)
        }
        if not hole_cells or any(grid[row][col] != 0 for row, col in hole_cells):
            errors.append(f"component {index} must enclose a nonempty all-zero rectangular hole")
            continue
        frames.append({
            "bbox": bbox,
            "thickness": thickness,
            "hole_h": hole_h,
            "hole_w": hole_w,
            "hole_cells": frozenset(hole_cells),
            "max_depth": (min(hole_h, hole_w) + 1) // 2,
            "hole_area": hole_h * hole_w,
        })

    thicknesses = {frame["thickness"] for frame in frames}
    if len(thicknesses) > 1:
        errors.append("all frames in one instance must have the same thickness")
    facts = {
        "grid_h": height,
        "grid_w": width,
        "palette": palette,
        "frames": frames,
        "n_frames": len(frames),
        "thickness": next(iter(thicknesses)) if len(thicknesses) == 1 else None,
        "max_depth": max((frame["max_depth"] for frame in frames), default=0),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "n_frames": int(facts["n_frames"]),
        "thickness": int(facts["thickness"]),
        "max_depth": int(facts["max_depth"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full input grammar and any exact requested axes."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors and requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and requested[name] is not None and observed.get(name) != requested[name]:
                errors.append(
                    f"override {name} requested {requested[name]!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generator's closed-frame grammar is the lawful task manifold."""
    return self_check(grid)


def _paint_depths(grid, painter) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    output = deepcopy(grid)
    for frame in facts["frames"]:
        r1, c1, r2, c2 = frame["bbox"]
        thickness = frame["thickness"]
        inner_r1, inner_c1 = r1 + thickness, c1 + thickness
        inner_r2, inner_c2 = r2 - thickness, c2 - thickness
        for row in range(inner_r1, inner_r2 + 1):
            for col in range(inner_c1, inner_c2 + 1):
                depth = min(
                    row - inner_r1,
                    inner_r2 - row,
                    col - inner_c1,
                    inner_c2 - col,
                ) + 1
                output[row][col] = painter(depth)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror for tests; canonical Racket remains sole authority."""
    return _paint_depths(grid, lambda depth: 2 if depth % 2 == 1 else 3)


def _rival_identity(grid):
    return deepcopy(grid)


def _rival_all_red(grid):
    return _paint_depths(grid, lambda _depth: 2)


def _rival_outer_red_inner_green(grid):
    return _paint_depths(grid, lambda depth: 2 if depth == 1 else 3)


def _rival_canonical_depth_cap(grid):
    # All canonical holes stop at depth four. This rival agrees there but
    # falsely freezes every deeper layer at green instead of continuing 2/3.
    return _paint_depths(
        grid,
        lambda depth: (2 if depth % 2 == 1 else 3) if depth <= 4 else 3,
    )


def _rival_largest_frame_only(grid):
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid task input")
    output = deepcopy(grid)
    largest = max(facts["frames"], key=lambda frame: frame["hole_area"])
    r1, c1, r2, c2 = largest["bbox"]
    thickness = largest["thickness"]
    for row in range(r1 + thickness, r2 - thickness + 1):
        for col in range(c1 + thickness, c2 - thickness + 1):
            depth = min(
                row - (r1 + thickness),
                (r2 - thickness) - row,
                col - (c1 + thickness),
                (c2 - thickness) - col,
            ) + 1
            output[row][col] = 2 if depth % 2 == 1 else 3
    return output


def _rival_differs(grid, rival) -> bool:
    try:
        return rule_mirror(grid) != rival(grid)
    except ValueError:
        return False


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "all_red": _rival_all_red,
    "outer_red_inner_green": _rival_outer_red_inner_green,
    "canonical_depth_cap": _rival_canonical_depth_cap,
    "largest_frame_only": _rival_largest_frame_only,
}

SEMANTIC_WITNESSES = {
    "refutes_identity": lambda grid: _rival_differs(grid, _rival_identity),
    "refutes_all_red": lambda grid: _rival_differs(grid, _rival_all_red),
    "refutes_two_ring_lookup": lambda grid: _rival_differs(grid, _rival_outer_red_inner_green),
    "refutes_canonical_depth_cap": lambda grid: _rival_differs(grid, _rival_canonical_depth_cap),
    "refutes_single_largest_frame": lambda grid: _rival_differs(grid, _rival_largest_frame_only),
}

WITNESS_RIVALS = {
    "refutes_identity": ["identity"],
    "refutes_all_red": ["all_red"],
    "refutes_two_ring_lookup": ["outer_red_inner_green"],
    "refutes_canonical_depth_cap": ["canonical_depth_cap"],
    "refutes_single_largest_frame": ["largest_frame_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_depth_cap": _rival_canonical_depth_cap,
}


def semantic_signature(grid) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    if errors:
        return {"errors": errors}
    return {
        "n_frames": facts["n_frames"],
        "thickness": facts["thickness"],
        "max_depth": facts["max_depth"],
        "rivals_refuted": tuple(
            name for name, rival in SEMANTIC_RIVALS.items() if _rival_differs(grid, rival)
        ),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Require every five-demo lesson to kill each named plausible rival."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    valid_inputs = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a complete input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with alternating-depth rule")
            continue
        valid_inputs.append(pair["input"])
    if len(valid_inputs) != len(demos):
        return reasons

    for name, rival in SEMANTIC_RIVALS.items():
        if not any(_rival_differs(grid, rival) for grid in valid_inputs):
            reasons.append(f"rival {name!r} survives every demonstration")

    observed_depths = {observe_overrides(grid)["max_depth"] for grid in valid_inputs}
    if not {1, 2, 3, 4, 5} <= observed_depths:
        reasons.append(f"demonstrations expose depths {sorted(observed_depths)}, not 1..5")
    if not any(observe_overrides(grid)["n_frames"] >= 2 for grid in valid_inputs):
        reasons.append("demonstrations lack a multi-frame witness")
    if not any(observe_overrides(grid)["thickness"] == 2 for grid in valid_inputs):
        reasons.append("demonstrations lack a thickness-2 distractor")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not a pair with an input")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query invalid: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with alternating-depth rule")
    return reasons
