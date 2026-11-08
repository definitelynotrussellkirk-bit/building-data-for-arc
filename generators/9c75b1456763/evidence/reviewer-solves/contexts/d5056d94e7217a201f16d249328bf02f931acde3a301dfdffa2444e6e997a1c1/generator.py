"""Generator for ARC task 09c534e7 / content hash 9c75b1456763.

The input is a black canvas containing two or three disconnected blue networks.
Each network is made from thick rectangular rooms joined by one-cell corridors
and contains exactly one non-blue marker cell.  The rule recolors every cell
whose complete 8-neighbourhood is nonzero with that network's marker color.

The constructor deliberately places several separated 5x3 rooms in every
network.  Consequently, the marker in one room must propagate to remote rooms;
a solver cannot succeed by filling only the marked rectangle or by using one
global marker color.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9c75b1456763"
TASK_ID = "9c75b1456763"
VERSION = "2.0.0"
RULE_HASH = "58004efe7e78"

SUMMARY = (
    "Two or three disconnected blue(1) room-and-corridor networks each have "
    "one unique marker color.  Within each network, repaint every cell whose "
    "eight neighbours are all nonzero with that network's marker color."
)

INVARIANTS = [
    "the canvas matches one of the four canonical shape/palette profiles",
    "there are exactly two or three nonzero 4-connected networks",
    "each network contains exactly one marker cell and otherwise uses blue(1)",
    "each marker lies in a thick room and every network has multiple separated thick-room interiors",
    "one-cell corridors connect the rooms without themselves creating false 3x3 interiors",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

PROFILES = ("p18_5", "p20_5", "p30_4", "p30_5")
SCHEDULE_PROFILES = PROFILES
LAYOUTS = ("straight", "bent")

# name -> (height, width, component count, palette size, stripe centre rows)
_PROFILE_INFO = {
    "p18_5": (18, 18, 3, 5, (2, 8, 14)),
    "p20_5": (20, 20, 3, 5, (2, 9, 16)),
    "p30_4": (30, 30, 2, 4, (7, 21)),
    "p30_5": (30, 30, 3, 5, (3, 14, 25)),
}
_PROFILE_BY_SIGNATURE = {
    (height, width, palette_size): name
    for name, (height, width, _components, palette_size, _rows) in _PROFILE_INFO.items()
}
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}

AXES = {
    "profile": {
        "type": "str",
        "default": "scheduled across all four canonical shape/palette profiles",
        "valid": "p18_5|p20_5|p30_4|p30_5",
    },
    "nodes_per_network": {
        "type": "int",
        "default": "difficulty-aware draw in 2..4",
        "valid": "2..4",
    },
    "layout": {
        "type": "str",
        "default": "rng",
        "valid": "straight|bent",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_OFFSETS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle through every canonical profile in every difficulty band."""
    del seed
    band = _band(difficulty)
    return PROFILES[(int(sample_index) + _BAND_OFFSETS[band]) % len(PROFILES)]


def _validate_requested_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        if not isinstance(value, str) or value not in PROFILES:
            raise ValueError(f"unknown profile: {value!r}")

    if "nodes_per_network" in overrides and overrides["nodes_per_network"] is not None:
        value = overrides["nodes_per_network"]
        if isinstance(value, bool) or not isinstance(value, int) or not 2 <= value <= 4:
            raise ValueError("nodes_per_network must be an integer in 2..4")

    if "layout" in overrides and overrides["layout"] is not None:
        value = overrides["layout"]
        if not isinstance(value, str) or value not in LAYOUTS:
            raise ValueError(f"unknown layout: {value!r}")


def _nominal_columns(width: int, count: int) -> list[int]:
    """Evenly spread 3x3 room centres with at least one gap column."""
    left, right = 2, width - 3
    if count == 1:
        return [(left + right) // 2]
    span = right - left
    return [round(left + index * span / (count - 1)) for index in range(count)]


def _jittered_columns(width: int, count: int, rng) -> list[int]:
    """Construct legal room centres directly; never reject or silently underfill."""
    nominals = _nominal_columns(width, count)
    centres: list[int] = []
    right = width - 3
    for index, nominal in enumerate(nominals):
        remaining = count - index - 1
        lo = max(2, nominal - 1, centres[-1] + 4 if centres else 2)
        hi = min(right, nominal + 1, right - 4 * remaining)
        if lo > hi:  # Defensive: the supported profiles make this unreachable.
            raise RuntimeError(
                f"cannot place {count} room centres constructively in width {width}"
            )
        centres.append(rng.randint(lo, hi))
    return centres


def _paint_room(grid: list[list[int]], row: int, col: int) -> None:
    """Paint a 5x3 room whose three-cell vertical core is fillable."""
    for dr in (-2, -1, 0, 1, 2):
        for dc in (-1, 0, 1):
            grid[row + dr][col + dc] = 1


def _paint_connector(
    grid: list[list[int]],
    start: tuple[int, int],
    end: tuple[int, int],
    layout: str,
    bend_sign: int,
) -> None:
    """Join equal-row rooms by a straight centreline or an edge detour."""
    row0, col0 = start
    row1, col1 = end
    if row0 != row1:
        raise RuntimeError("network room centres must share a row")
    if layout == "straight":
        route_row = row0
    else:
        route_row = row0 + 2 * bend_sign
    for row in range(min(row0, route_row), max(row0, route_row) + 1):
        grid[row][col0] = 1
        grid[row][col1] = 1
    for col in range(min(col0, col1), max(col0, col1) + 1):
        grid[route_row][col] = 1


def _network_centres(
    *, width: int, base_row: int, row_phase: int, count: int, rng
) -> list[tuple[int, int]]:
    columns = _jittered_columns(width, count, rng)
    row = base_row + row_phase
    return [(row, col) for col in columns]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one exact-contract room-network scene."""
    _validate_requested_overrides(overrides)
    band = _band(difficulty)

    requested_profile = overrides.get("profile")
    selected_profile = requested_profile or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # The scheduled singleton still goes through GenCtx so override provenance is
    # keyed and auditable.  The two other axes expose their complete domains.
    profile = ctx.draw_choice("profile", [selected_profile])
    nodes_per_network = ctx.draw_int_diff("nodes_per_network", 2, 4)
    layout = ctx.draw_choice("layout", LAYOUTS)

    height, width, component_count, _palette_size, stripe_rows = _PROFILE_INFO[profile]
    marker_colors = ctx.draw_distinct_colors(
        "marker_colors", n=component_count, exclude=(0, 1)
    )
    grid = full_grid(height, width, 0)
    row_phase = ctx.draw_rng("shared_vertical_phase").randint(0, 1)

    for network_index, (base_row, marker_color) in enumerate(
        zip(stripe_rows, marker_colors)
    ):
        rng = ctx.draw_rng(f"network_{network_index}_geometry")
        centres = _network_centres(
            width=width,
            base_row=base_row,
            row_phase=row_phase,
            count=nodes_per_network,
            rng=rng,
        )
        for row, col in centres:
            _paint_room(grid, row, col)
        for segment_index, (start, end) in enumerate(zip(centres, centres[1:])):
            route_rng = ctx.draw_rng(f"network_{network_index}_route_{segment_index}")
            bend_sign = -1 if route_rng.randint(0, 1) == 0 else 1
            _paint_connector(grid, start, end, layout, bend_sign)

        marker_rng = ctx.draw_rng(f"network_{network_index}_marker_room")
        room_row, marker_col = centres[marker_rng.randrange(len(centres))]
        marker_row = room_row + marker_rng.choice((-1, 0, 1))
        grid[marker_row][marker_col] = marker_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator produced invalid grid: " + "; ".join(errors[:4]))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular with non-empty rows"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["grid values must be integer ARC colors in 0..9"]
    return []


def _components4(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                component.append(current)
                r0, c0 = current
                for dr, dc in _CARDINAL:
                    nxt = (r0 + dr, c0 + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(component)
    return components


def _position_components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        first = remaining.pop()
        group = {first}
        stack = [first]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    stack.append(nxt)
        result.append(group)
    return result


def _fillable_cells(
    grid: Sequence[Sequence[int]], component: Sequence[tuple[int, int]]
) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return {
        (row, col)
        for row, col in component
        if 0 < row < height - 1
        and 0 < col < width - 1
        and all(grid[row + dr][col + dc] != 0 for dr, dc in _EIGHT)
    }


def _sealed_holes(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0
        and all(grid[row + dr][col + dc] != 0 for dr, dc in _EIGHT)
    ]


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    palette = sorted({value for row in grid for value in row})
    profile = _PROFILE_BY_SIGNATURE.get((height, width, len(palette)))
    if profile is None:
        errors.append(
            f"shape/palette profile {(height, width, len(palette))} is outside canonical profiles"
        )

    if 0 not in palette or 1 not in palette:
        errors.append("grid must contain both background 0 and blue body color 1")

    holes = _sealed_holes(grid)
    if holes:
        errors.append(f"sealed zero hole inside a thick body at {holes[0]}")

    components = _components4(grid)
    expected_components = _PROFILE_INFO[profile][2] if profile is not None else None
    if expected_components is not None and len(components) != expected_components:
        errors.append(
            f"profile {profile} requires {expected_components} nonzero components, found {len(components)}"
        )
    elif not 2 <= len(components) <= 3:
        errors.append(f"expected two or three nonzero components, found {len(components)}")

    component_rows: list[dict[str, Any]] = []
    marker_colors: list[int] = []
    for index, component in enumerate(components):
        markers = [
            (row, col, grid[row][col])
            for row, col in component
            if grid[row][col] not in (0, 1)
        ]
        if len(markers) != 1:
            errors.append(
                f"component {index} must contain exactly one marker cell, found {len(markers)}"
            )
            marker = None
        else:
            marker = markers[0]
            marker_colors.append(marker[2])

        colors = {grid[row][col] for row, col in component}
        if marker is not None and colors != {1, marker[2]}:
            errors.append(
                f"component {index} must use only blue and its marker color, found {sorted(colors)}"
            )

        fillable = _fillable_cells(grid, component)
        fillable_groups = _position_components(fillable)
        if len(fillable) < 2:
            errors.append(
                f"component {index} needs at least two 8-neighbour-surrounded cells, found {len(fillable)}"
            )
        if len(fillable_groups) < 2:
            errors.append(
                f"component {index} needs at least two separated thick-room interiors"
            )
        if marker is not None:
            marker_pos = (marker[0], marker[1])
            if marker_pos not in fillable:
                errors.append(f"component {index} marker must lie in a thick-room interior")
            if fillable and not any(
                max(abs(row - marker[0]), abs(col - marker[1])) >= 4
                for row, col in fillable
            ):
                errors.append(
                    f"component {index} lacks a remote interior requiring marker propagation"
                )

        component_rows.append(
            {
                "cells": component,
                "marker": marker,
                "fillable": fillable,
                "fillable_groups": fillable_groups,
            }
        )

    if len(marker_colors) != len(set(marker_colors)):
        errors.append("marker colors must be distinct across components")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "profile": profile,
        "components": component_rows,
        "holes": holes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not express the canonical network grammar."""
    del difficulty, meta
    return list(_analysis(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """The generated family is a strict, canonical-profile task manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | int]:
    """Recover every declared exact axis from a generated grid."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return {}

    group_counts = [
        len(component["fillable_groups"]) for component in analysis["components"]
    ]
    if not group_counts or len(set(group_counts)) != 1 or group_counts[0] not in (2, 3, 4):
        return {}
    nodes_per_network = group_counts[0]

    component_layouts: list[str] = []
    for component in analysis["components"]:
        representatives = []
        for group in component["fillable_groups"]:
            rows = sorted(row for row, _col in group)
            cols = sorted(col for _row, col in group)
            representatives.append((rows[len(rows) // 2], cols[len(cols) // 2]))
        representatives.sort(key=lambda cell: cell[1])
        segment_is_straight = [
            all(grid[row0][col] != 0 for col in range(col0, col1 + 1))
            for (row0, col0), (row1, col1) in zip(
                representatives, representatives[1:]
            )
            if row0 == row1
        ]
        if len(segment_is_straight) != nodes_per_network - 1:
            return {}
        if all(segment_is_straight):
            component_layouts.append("straight")
        elif not any(segment_is_straight):
            component_layouts.append("bent")
        else:
            return {}
    if len(set(component_layouts)) != 1:
        return {}
    layout = component_layouts[0]

    return {
        "profile": analysis["profile"],
        "nodes_per_network": nodes_per_network,
        "layout": layout,
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the authoritative Racket rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid network input: " + "; ".join(analysis["errors"][:4]))
    output = [list(row) for row in grid]
    for component in analysis["components"]:
        marker = component["marker"]
        assert marker is not None
        marker_color = marker[2]
        for row, col in component["fillable"]:
            output[row][col] = marker_color
    return output


def _rival_local_marker_room(grid) -> list[list[int]]:
    """Wrong shortcut: recolor only interiors close to the marker's room."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid network input")
    output = [list(row) for row in grid]
    for component in analysis["components"]:
        marker = component["marker"]
        assert marker is not None
        mr, mc, color = marker
        for row, col in component["fillable"]:
            if max(abs(row - mr), abs(col - mc)) <= 2:
                output[row][col] = color
    return output


def _rival_first_component_only(grid) -> list[list[int]]:
    """Wrong shortcut: apply the operation only to the first network."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid network input")
    output = [list(row) for row in grid]
    component = analysis["components"][0]
    marker = component["marker"]
    assert marker is not None
    for row, col in component["fillable"]:
        output[row][col] = marker[2]
    return output


def _rival_global_first_marker(grid) -> list[list[int]]:
    """Wrong shortcut: use one global marker color for every network."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid network input")
    output = [list(row) for row in grid]
    first_marker = analysis["components"][0]["marker"]
    assert first_marker is not None
    color = first_marker[2]
    for component in analysis["components"]:
        for row, col in component["fillable"]:
            output[row][col] = color
    return output


SEMANTIC_RIVALS = {
    "local_marker_room_only": _rival_local_marker_room,
    "first_component_only": _rival_first_component_only,
    "global_first_marker": _rival_global_first_marker,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# None of the named rivals reproduces every canonical example, so there is no
# canonical-only ambiguity to declare here.
CANONICAL_SHORTCUTS: dict[str, Any] = {}


def _rival_differs(grid, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _remote_propagation_witness(grid) -> bool:
    return not self_check(grid) and _rival_differs(grid, "local_marker_room_only")


def _all_components_witness(grid) -> bool:
    return not self_check(grid) and _rival_differs(grid, "first_component_only")


def _component_color_witness(grid) -> bool:
    return not self_check(grid) and _rival_differs(grid, "global_first_marker")


SEMANTIC_WITNESSES = {
    "marker_propagates_to_remote_rooms": _remote_propagation_witness,
    "every_network_is_transformed": _all_components_witness,
    "networks_keep_distinct_marker_colors": _component_color_witness,
}
WITNESS_RIVALS = {
    "marker_propagates_to_remote_rooms": ["local_marker_room_only"],
    "every_network_is_transformed": ["first_component_only"],
    "networks_keep_distinct_marker_colors": ["global_first_marker"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Verify that demonstrations expose the authority and refute named rivals."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    surviving = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        input_grid = demo["input"]
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[:2]}")
            continue
        expected = rule_mirror(input_grid)
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the authority mirror")
        for name in list(surviving):
            if LESSON_COMPETITORS[name](input_grid) != demo["output"]:
                surviving.remove(name)

    if surviving:
        reasons.append(f"named rival rules survive every demonstration: {sorted(surviving)}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query is outside the teaching grammar: {query_errors[:2]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the authority mirror")
    return reasons
