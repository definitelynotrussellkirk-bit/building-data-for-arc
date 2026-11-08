"""Generator for ARC task c05faa9b2b85 — Chamber Seed Fill.

Color 1 is a wall.  Consider every 4-connected region of cells whose color is
not 1.  If such a region contains exactly one distinct marker color (>1), fill
all of that region's zero cells with that color.  Regions with no marker color
or with two marker colors are unchanged.

The published examples only contain rectangular one-seed chambers.  The
ordinary curriculum therefore cycles through one canonical rectangular profile
and two lawful non-rectangular profiles.  Each semantic profile includes both a
mixed-color chamber and a chamber with two same-color markers, jointly refuting
the strongest shortcuts: "fill only rectangle interiors", "pick one seed when
a chamber is mixed", and "fill only chambers with exactly one marker cell."
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c05faa9b2b85"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "080731f15c8c"

SUMMARY = (
    "Treat color 1 as walls. For every 4-connected non-wall region, fill its "
    "zero cells with the region's unique marker color when exactly one distinct "
    "marker color is present; leave seedless and mixed-color regions unchanged."
)

INVARIANTS = [
    "background is 0 and wall cells are color 1",
    "there are two to four enclosed 4-connected non-wall chambers",
    "each marker color belongs to exactly one chamber",
    "each chamber contains one or two distinct marker colors in one or two cells",
    "at most one chamber is mixed-color; every other chamber has one seed color",
    "semantic profiles have one mixed-color chamber and one two-cell same-color chamber",
    "at least one one-seed chamber contains zero cells, so the rule is nonidentity",
    "every three-sample schedule window contains rectangular, one-notch, and two-notch scenes",
]

SCENE_PROFILES = ("canonical_rectangles", "single_notch", "double_notch")
CANVAS_PROFILES = ("canonical_10x14", "canonical_11x15", "canonical_12x16")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled modulo 3",
        "valid": "|".join(SCENE_PROFILES),
    },
    "canvas_profile": {
        "type": "str",
        "default": "easy=10x14, medium=11x15, hard=12x16; rng when unset",
        "valid": "|".join(CANVAS_PROFILES),
    },
    "n_rooms": {
        "type": "int",
        "default": "rng 2..4",
        "valid": "2..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

_CANVAS_DIMS = {
    "canonical_10x14": (10, 14),
    "canonical_11x15": (11, 15),
    "canonical_12x16": (12, 16),
}
_DIMS_CANVAS = {dims: name for name, dims in _CANVAS_DIMS.items()}

# Each box is inclusive (r0, c0, r1, c1).  The smallest box is 4x5, so
# its 2x3 interior remains connected and has room for two seeds after either
# one corner or two opposite corners are converted to wall cells.
_SLOT_BOXES = {
    "canonical_10x14": (
        (1, 1, 4, 5),
        (1, 8, 4, 12),
        (5, 1, 8, 5),
        (5, 8, 8, 12),
    ),
    "canonical_11x15": (
        (1, 1, 4, 5),
        (1, 9, 4, 13),
        (6, 1, 9, 5),
        (6, 9, 9, 13),
    ),
    "canonical_12x16": (
        (1, 1, 5, 6),
        (1, 9, 5, 14),
        (7, 1, 10, 6),
        (7, 9, 10, 14),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact scene profile used by the default curriculum."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _components_non_wall(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 1 or (row, col) in seen:
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
                        and grid[nr][nc] != 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cell_set = set(cells)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            rectangle = {
                (r, c)
                for r in range(r0, r1 + 1)
                for c in range(c0, c1 + 1)
            }
            marker_cells = [(r, c) for r, c in cells if grid[r][c] > 1]
            colors = sorted({grid[r][c] for r, c in marker_cells})
            color_counts = {
                color: sum(grid[r][c] == color for r, c in marker_cells)
                for color in colors
            }
            zeros = [(r, c) for r, c in cells if grid[r][c] == 0]
            components.append(
                {
                    "cells": cells,
                    "cell_set": cell_set,
                    "touches_edge": any(
                        r in (0, height - 1) or c in (0, width - 1)
                        for r, c in cells
                    ),
                    "marker_cells": marker_cells,
                    "colors": colors,
                    "color_counts": color_counts,
                    "zeros": zeros,
                    "bbox": (r0, c0, r1, c1),
                    "rectangular": cell_set == rectangle,
                    "bbox_deficit": len(rectangle) - len(cell_set),
                }
            )
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                return {"errors": errors}

    components = _components_non_wall(grid)
    border = [component for component in components if component["touches_edge"]]
    enclosed = [component for component in components if not component["touches_edge"]]
    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "components": components,
        "border": border,
        "enclosed": enclosed,
        "wall_count": sum(value == 1 for row in grid for value in row),
    }


def _grammar_errors(analysis: dict[str, Any], grid: Sequence[Sequence[int]]) -> list[str]:
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["wall_count"] == 0:
        errors.append("at least one color-1 wall cell is required")
    if len(analysis["border"]) != 1:
        errors.append(
            f"expected one connected exterior non-wall region, found {len(analysis['border'])}"
        )
    elif analysis["border"][0]["colors"]:
        errors.append("the exterior non-wall region must be seedless")

    enclosed = analysis["enclosed"]
    if not 2 <= len(enclosed) <= 4:
        errors.append(f"expected two to four enclosed chambers, found {len(enclosed)}")

    mixed = 0
    repeated_same_color = 0
    active = 0
    for index, component in enumerate(enclosed):
        n_colors = len(component["colors"])
        marker_count = len(component["marker_cells"])
        if n_colors not in (1, 2):
            errors.append(
                f"chamber {index} must contain one or two marker colors, found {n_colors}"
            )
        elif n_colors == 1 and marker_count not in (1, 2):
            errors.append(
                f"one-color chamber {index} must contain one or two marker cells, found {marker_count}"
            )
        elif n_colors == 2 and marker_count != 2:
            errors.append(
                f"two-color chamber {index} must contain exactly two marker cells, found {marker_count}"
            )
        if not component["zeros"]:
            errors.append(f"chamber {index} must contain at least one zero cell")
        if n_colors == 2:
            mixed += 1
        if n_colors == 1 and marker_count == 2:
            repeated_same_color += 1
        if n_colors == 1 and component["zeros"]:
            active += 1
    if mixed > 1:
        errors.append(f"at most one mixed-color chamber is allowed, found {mixed}")
    if repeated_same_color > 1:
        errors.append(
            "at most one two-cell same-color chamber is allowed, "
            f"found {repeated_same_color}"
        )
    if active == 0:
        errors.append("at least one one-seed chamber with fillable zero cells is required")

    color_components: dict[int, list[int]] = {}
    for index, component in enumerate(enclosed):
        for color in component["colors"]:
            color_components.setdefault(color, []).append(index)
    shared_colors = sorted(
        color for color, component_indices in color_components.items()
        if len(component_indices) != 1
    )
    if shared_colors:
        errors.append(
            "each marker color must belong to exactly one chamber; shared colors "
            + str(shared_colors)
        )
    return errors


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful generated-input grammar."""
    del difficulty
    analysis = _analyze(grid)
    errors = _grammar_errors(analysis, grid) if not analysis["errors"] else list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the published rectangular, exactly-one-seed chamber grammar."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analyze(grid)
    for index, component in enumerate(analysis["enclosed"]):
        if len(component["colors"]) != 1:
            reasons.append(f"canonical chamber {index} has more than one marker color")
        if len(component["marker_cells"]) != 1:
            reasons.append(f"canonical chamber {index} has more than one marker cell")
        if not component["rectangular"]:
            reasons.append(f"canonical chamber {index} is not rectangular")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; the pinned Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    output = _copy_grid(grid)
    for component in analysis["components"]:
        if len(component["colors"]) == 1:
            color = component["colors"][0]
            for row, col in component["zeros"]:
                output[row][col] = color
    return output


def _rival_rectangular_regions_only(grid) -> list[list[int]]:
    """Wrong rule: only rectangular non-wall components can be flooded."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    output = _copy_grid(grid)
    for component in analysis["components"]:
        if component["rectangular"] and len(component["colors"]) == 1:
            color = component["colors"][0]
            for row, col in component["zeros"]:
                output[row][col] = color
    return output


def _rival_first_color_wins(grid) -> list[list[int]]:
    """Wrong rule: choose the smallest seed color even when a region is mixed."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    output = _copy_grid(grid)
    for component in analysis["components"]:
        if component["colors"]:
            color = component["colors"][0]
            for row, col in component["zeros"]:
                output[row][col] = color
    return output


def _rival_exactly_one_marker_cell(grid) -> list[list[int]]:
    """Wrong rule: a chamber is active only when it has one marker cell."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    output = _copy_grid(grid)
    for component in analysis["components"]:
        if len(component["colors"]) == 1 and len(component["marker_cells"]) == 1:
            color = component["colors"][0]
            for row, col in component["zeros"]:
                output[row][col] = color
    return output


LESSON_COMPETITORS: dict[str, Callable[[Any], list[list[int]]]] = {
    "rectangular_regions_only": _rival_rectangular_regions_only,
    "first_color_wins": _rival_first_color_wins,
    "exactly_one_marker_cell": _rival_exactly_one_marker_cell,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def _witness_irregular_active_region(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        not component["rectangular"]
        and len(component["colors"]) == 1
        and bool(component["zeros"])
        for component in analysis["enclosed"]
    )


def _witness_multi_color_region(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        len(component["colors"]) == 2 and bool(component["zeros"])
        for component in analysis["enclosed"]
    )


def _witness_repeated_same_color_markers(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        len(component["colors"]) == 1
        and len(component["marker_cells"]) == 2
        and bool(component["zeros"])
        for component in analysis["enclosed"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "irregular_active_region": _witness_irregular_active_region,
    "multi_color_region": _witness_multi_color_region,
    "repeated_same_color_markers": _witness_repeated_same_color_markers,
}
WITNESS_RIVALS = {
    "irregular_active_region": ["rectangular_regions_only"],
    "multi_color_region": ["first_color_wins"],
    "repeated_same_color_markers": ["exactly_one_marker_cell"],
}


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a valid generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"] or _grammar_errors(analysis, grid):
        return {}
    enclosed = analysis["enclosed"]
    color_counts = [len(component["colors"]) for component in enclosed]
    deficits = [component["bbox_deficit"] for component in enclosed]
    if all(component["rectangular"] for component in enclosed) and all(
        count == 1 for count in color_counts
    ):
        scene_profile: str | None = "canonical_rectangles"
    elif color_counts.count(2) == 1 and all(deficit == 1 for deficit in deficits):
        scene_profile = "single_notch"
    elif color_counts.count(2) == 1 and all(deficit == 2 for deficit in deficits):
        scene_profile = "double_notch"
    else:
        scene_profile = None
    return {
        "scene_profile": scene_profile,
        "canvas_profile": _DIMS_CANVAS.get((analysis["height"], analysis["width"])),
        "n_rooms": len(enclosed),
    }


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is invalid: {errors[0]}"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not follow the chamber-fill rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that jointly eliminate every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        pair_errors = _pair_errors(demo, f"demo {index}")
        reasons.extend(pair_errors)
        if not pair_errors:
            valid_demos.append(demo)
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {unknown}")
    if "n_rooms" in overrides and overrides["n_rooms"] is not None:
        value = overrides["n_rooms"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("n_rooms override must be an integer, not bool/float")
        if not 2 <= value <= 4:
            raise ValueError("n_rooms override must be in 2..4")


def _scheduled_choice(ctx, overrides, label: str, default: str, options: Sequence[str]) -> str:
    choices = options if overrides.get(label) is not None else (default,)
    return str(ctx.draw_choice(label, choices))


def _interior_cells(
    box: tuple[int, int, int, int],
    scene_profile: str,
    rng,
) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    cells = {
        (row, col)
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
    }
    corners = (
        (r0 + 1, c0 + 1),
        (r0 + 1, c1 - 1),
        (r1 - 1, c0 + 1),
        (r1 - 1, c1 - 1),
    )
    if scene_profile == "single_notch":
        cells.remove(rng.choice(corners))
    elif scene_profile == "double_notch":
        pair = rng.choice(((corners[0], corners[3]), (corners[1], corners[2])))
        cells.difference_update(pair)
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct a deterministic, rejection-free chamber scene."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_scene = schedule_profile(seed, sample_index, difficulty)
    scene_profile = _scheduled_choice(
        ctx, overrides, "scene_profile", scheduled_scene, SCENE_PROFILES
    )
    difficulty_canvas = {
        "easy": "canonical_10x14",
        "medium": "canonical_11x15",
        "hard": "canonical_12x16",
    }.get(difficulty)
    canvas_options = (
        CANVAS_PROFILES
        if overrides.get("canvas_profile") is not None or difficulty_canvas is None
        else (difficulty_canvas,)
    )
    canvas_profile = str(ctx.draw_choice("canvas_profile", canvas_options))
    n_rooms = ctx.draw_int("n_rooms", 2, 4)

    height, width = _CANVAS_DIMS[canvas_profile]
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("layout")
    boxes = list(_SLOT_BOXES[canvas_profile])
    rng.shuffle(boxes)
    boxes = boxes[:n_rooms]

    palette = list(range(2, 10))
    rng.shuffle(palette)
    mixed_room: int | None = None
    repeated_room: int | None = None
    if scene_profile != "canonical_rectangles":
        semantic_rooms = list(range(n_rooms))
        rng.shuffle(semantic_rooms)
        mixed_room, repeated_room = semantic_rooms[:2]
    color_cursor = 0

    for room_index, box in enumerate(boxes):
        r0, c0, r1, c1 = box
        interior = _interior_cells(box, scene_profile, rng)
        # Paint the whole room box as wall, then carve exactly the intended
        # connected component.  This makes notches observable rather than
        # relying on a fragile boundary-walk implementation.
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                grid[row][col] = 1
        for row, col in interior:
            grid[row][col] = 0

        marker_cells = sorted(interior)
        rng.shuffle(marker_cells)
        if room_index == mixed_room:
            for marker_index in range(2):
                row, col = marker_cells[marker_index]
                grid[row][col] = palette[color_cursor]
                color_cursor += 1
        elif room_index == repeated_room:
            color = palette[color_cursor]
            color_cursor += 1
            for marker_index in range(2):
                row, col = marker_cells[marker_index]
                grid[row][col] = color
        else:
            row, col = marker_cells[0]
            grid[row][col] = palette[color_cursor]
            color_cursor += 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid chamber scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": scene_profile,
        "canvas_profile": canvas_profile,
        "n_rooms": n_rooms,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    if scene_profile != "canonical_rectangles":
        required_witnesses = (
            "irregular_active_region",
            "multi_color_region",
            "repeated_same_color_markers",
        )
        missing = [
            name for name in required_witnesses
            if not SEMANTIC_WITNESSES[name](grid)
        ]
        if missing:
            raise RuntimeError(f"semantic profile is missing witnesses: {missing}")
    return grid
