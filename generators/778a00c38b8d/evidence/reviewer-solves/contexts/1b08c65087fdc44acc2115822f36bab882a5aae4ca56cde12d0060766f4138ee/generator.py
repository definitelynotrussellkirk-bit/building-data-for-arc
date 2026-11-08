"""Generator for arc_additional_puzzle_bank_volume8:E55.

Rule: recolor every whole red (2) 4-connected component that contains an exact
grid-corner cell to green (3).  Red components that merely touch another part
of the border remain red, as do fully interior red components.  Color 5 is an
inert distractor.

The four-sample lesson schedule deliberately alternates selected/unselected
component sizes and rotates the occupied corners and border decoy.  Every
ordinary scene therefore refutes the plausible corner-cell-only, all-border,
and all-red shortcuts, while every four-demo sliding window also refutes fixed
corner and fixed-size rules.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "778a00c38b8d"
TASK_ID = GENERATOR_ID
RULE_HASH = "f1e155724595"  # sha256[:12] of whitespace-normalized selected rule
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Recolor whole red (2) 4-connected components that contain an exact grid "
    "corner to green (3); preserve interior and non-corner-border red "
    "components, and preserve the inert color-5 distractor."
)

INVARIANTS = [
    "the grid is 8..10 by 8..10 with modal background 0",
    "the input palette is exactly {0, 2, 5} with one interior color-5 cell",
    "at least one red component contains a grid corner and extends beyond it",
    "at least one red component is fully interior",
    "ordinary draws include a red border component that contains no corner",
    "red components are separate 4-connected objects of size 1..4",
]

CORNER_NAMES = ("TL", "TR", "BR", "BL")
BORDER_SIDES = ("top", "right", "bottom", "left")
CANONICAL_DIMS = ((8, 9), (9, 10), (9, 8), (10, 8))
SCHEDULE_PROFILES = (0, 1, 2, 3)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-dimension lesson-block schedule",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-dimension lesson-block schedule",
        "valid": "8..10",
    },
    "n_corner_components": {
        "type": "int",
        "default": "four-sample schedule 2|2|3|4",
        "valid": "2..4",
    },
    "n_interior_components": {
        "type": "int",
        "default": "four-sample schedule 2|3|2|2 (includes one border decoy)",
        "valid": "2..3",
    },
    "corner_size": {
        "type": "int",
        "default": "four-sample schedule 2|2|3|3",
        "valid": "2..3",
    },
    "interior_size": {
        "type": "int",
        "default": "four-sample schedule 2|3|2|3",
        "valid": "2..3",
    },
}


# ---------------------------------------------------------------------------
# Structural analysis
# ---------------------------------------------------------------------------


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components_of_color(grid: Sequence[Sequence[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _corner_positions(height: int, width: int) -> dict[str, tuple[int, int]]:
    return {
        "TL": (0, 0),
        "TR": (0, width - 1),
        "BR": (height - 1, width - 1),
        "BL": (height - 1, 0),
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 10 and 8 <= width <= 10):
        errors.append(f"grid dimensions must lie in 8..10, found {height}x{width}")

    values = [value for row in grid for value in row]
    palette = set(values)
    if palette != {0, 2, 5}:
        errors.append(f"input palette must be exactly {{0, 2, 5}}, found {sorted(palette)}")
    if values.count(0) <= max(values.count(2), values.count(5)):
        errors.append("zero must be the unique modal background")

    distractors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    if len(distractors) != 1:
        errors.append(f"expected exactly one color-5 distractor cell, found {len(distractors)}")
    elif distractors[0][0] in (0, height - 1) or distractors[0][1] in (0, width - 1):
        errors.append("the color-5 distractor must be strictly interior")

    corners_by_name = _corner_positions(height, width)
    corners = set(corners_by_name.values())
    red_components = _components_of_color(grid, 2)
    if not (2 <= len(red_components) <= 7):
        errors.append(f"expected 2..7 red components, found {len(red_components)}")

    corner_components = [component for component in red_components if component & corners]
    noncorner_components = [component for component in red_components if not component & corners]
    if not corner_components:
        errors.append("at least one red component must contain a grid corner")
    if not noncorner_components:
        errors.append("at least one red component must avoid every grid corner")
    if corner_components and not any(len(component) > 1 for component in corner_components):
        errors.append("a corner component must extend beyond the corner cell")

    for index, component in enumerate(red_components):
        if not (1 <= len(component) <= 4):
            errors.append(f"red component {index} must have size 1..4, found {len(component)}")
        touched = component & corners
        if len(touched) > 1:
            errors.append(f"red component {index} spans multiple grid corners")

    fully_interior = [
        component
        for component in noncorner_components
        if all(
            row not in (0, height - 1) and col not in (0, width - 1)
            for row, col in component
        )
    ]
    if not fully_interior:
        errors.append("at least one non-corner red component must be fully interior")

    border_decoys = [
        component
        for component in noncorner_components
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in component
        )
    ]

    corner_names = tuple(
        name
        for name, position in corners_by_name.items()
        if any(position in component for component in corner_components)
    )
    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "palette": palette,
        "distractors": distractors,
        "red_components": red_components,
        "corner_components": corner_components,
        "noncorner_components": noncorner_components,
        "fully_interior": fully_interior,
        "border_decoys": border_decoys,
        "corner_names": corner_names,
        "corner_sizes": tuple(sorted(len(component) for component in corner_components)),
        "interior_sizes": tuple(sorted(len(component) for component in noncorner_components)),
        "n_corner_components": len(corner_components),
        "n_interior_components": len(noncorner_components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, broader only in corner/count symmetry."""
    facts = _analyze(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if (facts["grid_h"], facts["grid_w"]) not in CANONICAL_DIMS:
        reasons.append("dimensions are outside the four canonical input profiles")
    if any(len(component) > 3 for component in facts["red_components"]):
        reasons.append("canonical red components have size at most three")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a generated grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(facts["errors"]))
    if len(set(facts["corner_sizes"])) != 1:
        raise ValueError("generated corner components do not share one observable size")
    if len(set(facts["interior_sizes"])) != 1:
        raise ValueError("generated non-corner components do not share one observable size")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_corner_components": facts["n_corner_components"],
        "n_interior_components": facts["n_interior_components"],
        "corner_size": facts["corner_sizes"][0],
        "interior_size": facts["interior_sizes"][0],
    }


# ---------------------------------------------------------------------------
# Rule mirror and named rival rules
# ---------------------------------------------------------------------------


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    corners = set(_corner_positions(height, width).values())
    output = [list(row) for row in grid]
    for component in _components_of_color(grid, 2):
        if component & corners:
            for row, col in component:
                output[row][col] = 3
    return output


def _rival_corner_cells_only(grid) -> list[list[int]]:
    output = [list(row) for row in grid]
    for row, col in _corner_positions(len(grid), len(grid[0])).values():
        if output[row][col] == 2:
            output[row][col] = 3
    return output


def _rival_all_border_touching(grid) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for component in _components_of_color(grid, 2):
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in component
        ):
            for row, col in component:
                output[row][col] = 3
    return output


def _rival_all_red(grid) -> list[list[int]]:
    return [[3 if value == 2 else value for value in row] for row in grid]


def _rival_corner_subset(grid, names: set[str]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    selected = {_corner_positions(height, width)[name] for name in names}
    output = [list(row) for row in grid]
    for component in _components_of_color(grid, 2):
        if component & selected:
            for row, col in component:
                output[row][col] = 3
    return output


def _rival_size_only(grid, size: int) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _components_of_color(grid, 2):
        if len(component) == size:
            for row, col in component:
                output[row][col] = 3
    return output


SEMANTIC_RIVALS = {
    "corner_cells_only": _rival_corner_cells_only,
    "all_border_touching_red": _rival_all_border_touching,
    "all_red": _rival_all_red,
}

CANONICAL_SHORTCUTS = {
    "all_border_touching_red": _rival_all_border_touching,
}

LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "top_corners_only": lambda grid: _rival_corner_subset(grid, {"TL", "TR"}),
    "left_corners_only": lambda grid: _rival_corner_subset(grid, {"TL", "BL"}),
    "size_two_only": lambda grid: _rival_size_only(grid, 2),
    "size_three_only": lambda grid: _rival_size_only(grid, 3),
}


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _witness_whole_component_extension(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and any(len(component) > 1 for component in facts["corner_components"]))


def _witness_noncorner_border_decoy(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["border_decoys"])


def _witness_interior_red_preserved(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["fully_interior"])


SEMANTIC_WITNESSES = {
    "whole_component_extension": _witness_whole_component_extension,
    "noncorner_border_decoy": _witness_noncorner_border_decoy,
    "interior_red_preserved": _witness_interior_red_preserved,
}

WITNESS_RIVALS = {
    "whole_component_extension": ["corner_cells_only"],
    "noncorner_border_decoy": ["all_border_touching_red"],
    "interior_red_preserved": ["all_red"],
}


# ---------------------------------------------------------------------------
# Lesson identifiability
# ---------------------------------------------------------------------------


def _grid_key(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to eliminate named plausible shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    facts_by_demo: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        facts = _analyze(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the selected corner rule")
            continue
        facts_by_demo.append(facts)

    query_facts = _analyze(query["input"])
    if query_facts["errors"]:
        reasons.append("query input is outside the teaching grammar")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the selected corner rule")

    if len(facts_by_demo) != len(demos) or query_facts["errors"]:
        return reasons

    covered_corners = {
        name for facts in facts_by_demo for name in facts["corner_names"]
    }
    if covered_corners != set(CORNER_NAMES):
        reasons.append(f"demonstrations cover corners {sorted(covered_corners)}, not all four")

    corner_sizes = {size for facts in facts_by_demo for size in facts["corner_sizes"]}
    interior_sizes = {size for facts in facts_by_demo for size in facts["interior_sizes"]}
    if corner_sizes != {2, 3} or interior_sizes != {2, 3}:
        reasons.append("demonstrations do not vary selected and unselected sizes across 2 and 3")

    size_relations = set()
    for facts in facts_by_demo:
        corner_size = facts["corner_sizes"][0]
        interior_size = facts["interior_sizes"][0]
        size_relations.add((corner_size > interior_size) - (corner_size < interior_size))
    if size_relations != {-1, 0, 1}:
        reasons.append("demonstrations do not show smaller/equal/larger selected-size relations")

    if any(not facts["border_decoys"] for facts in facts_by_demo):
        reasons.append("a demonstration lacks the non-corner border decoy")
    if any(not facts["fully_interior"] for facts in facts_by_demo):
        reasons.append("a demonstration lacks an interior red component")

    demo_inputs = {_grid_key(pair["input"]) for pair in demos}
    if _grid_key(query["input"]) in demo_inputs:
        reasons.append("query repeats a demonstration input instead of testing transfer")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(deepcopy(pair["input"])) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not refute rival {name}")

    return reasons


# ---------------------------------------------------------------------------
# Deterministic scene construction
# ---------------------------------------------------------------------------


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    del seed, difficulty
    return int(sample_index) % 4


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (8, 10),
        "grid_w": (8, 10),
        "n_corner_components": (2, 4),
        "n_interior_components": (2, 3),
        "corner_size": (2, 3),
        "interior_size": (2, 3),
    }
    for name, value in overrides.items():
        lower, upper = bounds[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
            raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def _corner_shape(name: str, size: int, variant: int, height: int, width: int) -> set[tuple[int, int]]:
    if size == 2:
        base_variants = (
            {(0, 0), (0, 1)},
            {(0, 0), (1, 0)},
        )
    elif size == 3:
        base_variants = (
            {(0, 0), (0, 1), (1, 0)},
            {(0, 0), (0, 1), (0, 2)},
            {(0, 0), (1, 0), (2, 0)},
        )
    else:
        raise ValueError(f"unsupported corner component size {size}")
    base = base_variants[variant % len(base_variants)]
    reflected = set()
    for row, col in base:
        if name in ("BL", "BR"):
            row = height - 1 - row
        if name in ("TR", "BR"):
            col = width - 1 - col
        reflected.add((row, col))
    return reflected


def _shape_variants(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    if size == 2:
        return (
            ((0, 0), (0, 1)),
            ((0, 0), (1, 0)),
        )
    if size == 3:
        return (
            ((0, 0), (0, 1), (1, 0)),
            ((0, 0), (0, 1), (0, 2)),
            ((0, 0), (1, 0), (2, 0)),
            ((0, 1), (1, 0), (1, 1)),
        )
    raise ValueError(f"unsupported component size {size}")


def _touches_existing_red(cells: Iterable[tuple[int, int]], red: set[tuple[int, int]]) -> bool:
    for row, col in cells:
        if (row, col) in red:
            return True
        if any(
            neighbor in red
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
        ):
            return True
    return False


def _translated_candidates(
    height: int,
    width: int,
    size: int,
    red: set[tuple[int, int]],
    *,
    role: str,
    side: str | None = None,
) -> list[set[tuple[int, int]]]:
    corners = set(_corner_positions(height, width).values())
    candidates: list[set[tuple[int, int]]] = []
    for shape in _shape_variants(size):
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        for top in range(height - shape_h + 1):
            for left in range(width - shape_w + 1):
                cells = {(top + row, left + col) for row, col in shape}
                if cells & corners or _touches_existing_red(cells, red):
                    continue
                if role == "interior":
                    if any(
                        row in (0, height - 1) or col in (0, width - 1)
                        for row, col in cells
                    ):
                        continue
                elif role == "border":
                    if side == "top" and not any(row == 0 for row, _ in cells):
                        continue
                    if side == "bottom" and not any(row == height - 1 for row, _ in cells):
                        continue
                    if side == "left" and not any(col == 0 for _, col in cells):
                        continue
                    if side == "right" and not any(col == width - 1 for _, col in cells):
                        continue
                else:
                    raise ValueError(f"unknown placement role {role!r}")
                candidates.append(cells)
    return candidates


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


def _build_scene(
    *,
    height: int,
    width: int,
    n_corner: int,
    n_interior: int,
    corner_size: int,
    interior_size: int,
    phase: int,
    block: int,
    seed: int,
    band_offset: int,
    rng,
) -> list[list[int]] | None:
    grid = full_grid(height, width, 0)
    red: set[tuple[int, int]] = set()

    rotation = (phase + block + seed + band_offset) % 4
    corner_order = CORNER_NAMES[rotation:] + CORNER_NAMES[:rotation]
    selected_corners = corner_order[:n_corner]
    for index, name in enumerate(selected_corners):
        cells = _corner_shape(name, corner_size, rng.randrange(12) + index, height, width)
        if _touches_existing_red(cells, red):
            return None
        _paint(grid, cells, 2)
        red.update(cells)

    side = BORDER_SIDES[(phase + block + seed + band_offset) % 4]
    border_candidates = _translated_candidates(
        height, width, interior_size, red, role="border", side=side
    )
    if not border_candidates:
        return None
    border_cells = rng.choice(border_candidates)
    _paint(grid, border_cells, 2)
    red.update(border_cells)

    for _ in range(n_interior - 1):
        interior_candidates = _translated_candidates(
            height, width, interior_size, red, role="interior"
        )
        if not interior_candidates:
            return None
        cells = rng.choice(interior_candidates)
        _paint(grid, cells, 2)
        red.update(cells)

    distractor_candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0
        and all(
            (row + dr, col + dc) not in red
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        )
    ]
    if not distractor_candidates:
        return None
    distractor = rng.choice(distractor_candidates)
    grid[distractor[0]][distractor[1]] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket owns output."""
    _validate_call(difficulty, overrides)
    phase = schedule_profile(seed, sample_index, difficulty)
    block = int(sample_index) // 4
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    dimension = CANONICAL_DIMS[
        (block + int(seed) + band_offset) % len(CANONICAL_DIMS)
    ]
    defaults = {
        "grid_h": dimension[0],
        "grid_w": dimension[1],
        "n_corner_components": (2, 2, 3, 4)[phase],
        "n_interior_components": (2, 3, 2, 2)[phase],
        "corner_size": (2, 2, 3, 3)[phase],
        "interior_size": (2, 3, 2, 3)[phase],
    }
    effective = {**defaults, **overrides}

    # Construct this context last: provenance audits inspect the most recent
    # GenCtx, and every declared exact axis is consumed through a typed draw.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int("grid_h", 8, 10)
    width = ctx.draw_int("grid_w", 8, 10)
    n_corner = ctx.draw_int("n_corner_components", 2, 4)
    n_interior = ctx.draw_int("n_interior_components", 2, 3)
    corner_size = ctx.draw_int("corner_size", 2, 3)
    interior_size = ctx.draw_int("interior_size", 2, 3)

    for attempt in range(64):
        grid = _build_scene(
            height=height,
            width=width,
            n_corner=n_corner,
            n_interior=n_interior,
            corner_size=corner_size,
            interior_size=interior_size,
            phase=phase,
            block=block,
            seed=int(seed),
            band_offset=band_offset,
            rng=ctx.draw_rng(f"placement_attempt_{attempt}"),
        )
        if grid is None:
            continue
        errors = self_check(grid, difficulty=difficulty)
        if errors:
            continue
        observed = observe_overrides(grid)
        requested = {
            "grid_h": height,
            "grid_w": width,
            "n_corner_components": n_corner,
            "n_interior_components": n_interior,
            "corner_size": corner_size,
            "interior_size": interior_size,
        }
        if observed != requested:
            continue
        return [row[:] for row in grid]

    raise ValueError(
        "could not place a lawful corner-component scene after 64 deterministic attempts"
    )
