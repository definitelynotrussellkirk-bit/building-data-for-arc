"""Generator for ``connect_each_pair_with_the_clear_elbow_path``.

Color 5 is an inert blocker.  Every other nonzero color appears at exactly two
non-collinear endpoints.  Of the two possible one-cell-wide L paths between a
pair, exactly one is clear in generated lessons; paint that clear path in the
pair color and leave blockers unchanged.  A blocker may sit at the blocked
route's elbow or farther along either leg, so the complete route must be checked.

The ordinary four-slot schedule alternates which route is blocked, blocker
position, and pair count.  Every three-demo subset of a four-sample lesson
contains a mixed scene that refutes an elbow-only clearance shortcut, while the
two-pair scenes continue to refute treating the two blockers as another pair.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7c9b61d5a51"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "82200d439ef3"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

BLOCKER_COLOR = 5
PAIR_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
GRID_HEIGHTS = (9, 10, 11)
GRID_WIDTHS = (9, 10, 11, 12)
PAIR_COUNTS = (2, 3)
ROUTE_PATTERNS = ("first", "second", "mixed")
BLOCKER_PATTERNS = ("elbow", "leg", "mixed")

SUMMARY = (
    "On a 0-background grid, color 5 cells are inert blockers and every other "
    "nonzero color marks exactly two endpoints in different rows and columns. "
    "For each endpoint pair, try the two possible L-shaped Manhattan paths. "
    "Exactly one route is clear of blockers and other endpoints in generated "
    "lessons; paint that route in the endpoint color and never connect color 5."
)

INVARIANTS = [
    "background is 0 and blocker color is 5",
    "there are 2-3 distinct pair colors selected from 1..9 excluding 5",
    "each pair color appears exactly twice in different rows and columns",
    "each generated pair has exactly one clear elbow route",
    "the blocked route for each pair contains a color-5 blocker",
    "ordinary lessons place blockers both at elbows and along route legs",
    "chosen paths are nontrivial and pairwise disjoint",
    "the Racket oracle, not the Python mirror, is the output authority",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9 for canonical anchors; otherwise difficulty-aware 9..11",
        "valid": "9|10|11",
    },
    "grid_w": {
        "type": "int",
        "default": "9 for canonical anchors; otherwise difficulty-aware 9..12",
        "valid": "9|10|11|12",
    },
    "pair_count": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "2|3",
    },
    "route_pattern": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "first|second|mixed",
    },
}

SCHEDULE_PROFILES = (
    "first_two_leg",
    "mixed_two_mixed",
    "second_three_elbow",
    "mixed_three_mixed",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose route orientation, pair count, and blocker-position curriculum."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    domains = {
        "grid_h": GRID_HEIGHTS,
        "grid_w": GRID_WIDTHS,
        "pair_count": PAIR_COUNTS,
        "route_pattern": ROUTE_PATTERNS,
    }
    for label, domain in domains.items():
        value = overrides.get(label)
        if value is not None and value not in domain:
            allowed = ", ".join(map(str, domain))
            raise ValueError(f"{label} must be one of: {allowed}")
    return "medium" if difficulty is None else difficulty


def _line_cells(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    if a[0] == b[0]:
        lo, hi = sorted((a[1], b[1]))
        return tuple((a[0], col) for col in range(lo, hi + 1))
    if a[1] == b[1]:
        lo, hi = sorted((a[0], b[0]))
        return tuple((row, a[1]) for row in range(lo, hi + 1))
    raise ValueError(f"line endpoints are not axis-aligned: {a}, {b}")


def _route_cells(
    a: tuple[int, int], b: tuple[int, int], route_index: int
) -> tuple[tuple[int, int], ...]:
    """Return route 0 via (a.row,b.col), route 1 via (b.row,a.col)."""
    elbow = _route_elbow(a, b, route_index)
    cells = set(_line_cells(a, elbow)) | set(_line_cells(elbow, b))
    return tuple(sorted(cells))


def _route_elbow(
    a: tuple[int, int], b: tuple[int, int], route_index: int
) -> tuple[int, int]:
    if route_index == 0:
        return (a[0], b[1])
    if route_index == 1:
        return (b[0], a[1])
    raise ValueError(f"route index must be 0 or 1, found {route_index}")


def _route_is_clear(
    grid: list[list[int]],
    cells: tuple[tuple[int, int], ...],
    color: int,
) -> bool:
    return all(grid[row][col] in (0, color) for row, col in cells)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "pairs": []}

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    if height not in GRID_HEIGHTS:
        errors.append(f"height must be one of {GRID_HEIGHTS}, found {height}")
    if width not in GRID_WIDTHS:
        errors.append(f"width must be one of {GRID_WIDTHS}, found {width}")

    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(normalized):
        for col, value in enumerate(values):
            if value != 0:
                positions.setdefault(value, []).append((row, col))

    blocker_cells = positions.get(BLOCKER_COLOR, [])
    if not blocker_cells:
        errors.append("at least one color-5 blocker is required")

    pair_colors = sorted(color for color in positions if color != BLOCKER_COLOR)
    if len(pair_colors) not in PAIR_COUNTS:
        errors.append(f"expected 2-3 pair colors, found {len(pair_colors)}")

    pairs: list[dict[str, Any]] = []
    for color in pair_colors:
        cells = sorted(positions[color])
        if len(cells) != 2:
            errors.append(f"pair color {color} appears {len(cells)} times (expected 2)")
            continue
        a, b = cells
        if a[0] == b[0] or a[1] == b[1]:
            errors.append(
                f"pair color {color} endpoints must differ in row and column: {a}, {b}"
            )
            continue
        routes = (_route_cells(a, b, 0), _route_cells(a, b, 1))
        clear = tuple(_route_is_clear(normalized, route, color) for route in routes)
        if not any(clear):
            errors.append(f"pair color {color} has no clear elbow route")
        selected = 0 if clear[0] else (1 if clear[1] else None)
        blocked_by_5 = tuple(
            any(normalized[row][col] == BLOCKER_COLOR for row, col in route)
            for route in routes
        )
        blocked_index = None if selected is None else 1 - selected
        blocked_elbow = (
            None if blocked_index is None else _route_elbow(a, b, blocked_index)
        )
        blocker_hits = (
            ()
            if blocked_index is None
            else tuple(
                cell
                for cell in routes[blocked_index]
                if normalized[cell[0]][cell[1]] == BLOCKER_COLOR
            )
        )
        blocker_position = None
        if blocked_elbow is not None and blocked_elbow in blocker_hits:
            blocker_position = "elbow"
        elif blocker_hits:
            blocker_position = "leg"
        pairs.append(
            {
                "color": color,
                "cells": (a, b),
                "routes": routes,
                "clear": clear,
                "selected": selected,
                "blocked_by_5": blocked_by_5,
                "blocked_index": blocked_index,
                "blocked_elbow": blocked_elbow,
                "blocker_hits": blocker_hits,
                "blocker_position": blocker_position,
            }
        )

    unique_selected = [
        pair["selected"]
        for pair in pairs
        if pair["selected"] is not None and sum(pair["clear"]) == 1
    ]
    route_pattern = None
    if len(unique_selected) == len(pairs) and pairs:
        if all(index == 0 for index in unique_selected):
            route_pattern = "first"
        elif all(index == 1 for index in unique_selected):
            route_pattern = "second"
        elif {0, 1} <= set(unique_selected):
            route_pattern = "mixed"

    blocker_positions = [pair["blocker_position"] for pair in pairs]
    blocker_pattern = None
    if pairs and all(position in ("elbow", "leg") for position in blocker_positions):
        if all(position == "elbow" for position in blocker_positions):
            blocker_pattern = "elbow"
        elif all(position == "leg" for position in blocker_positions):
            blocker_pattern = "leg"
        else:
            blocker_pattern = "mixed"

    selected_paths = [
        set(pair["routes"][pair["selected"]])
        for pair in pairs
        if pair["selected"] is not None
    ]
    overlaps: set[tuple[int, int]] = set()
    for index, path in enumerate(selected_paths):
        for other in selected_paths[index + 1 :]:
            overlaps.update(path & other)

    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": height,
        "grid_w": width,
        "positions": positions,
        "blocker_cells": tuple(sorted(blocker_cells)),
        "blocker_count": len(blocker_cells),
        "pair_colors": tuple(pair_colors),
        "pair_count": len(pair_colors),
        "pairs": pairs,
        "route_pattern": route_pattern,
        "blocker_pattern": blocker_pattern,
        "selected_path_overlaps": tuple(sorted(overlaps)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the blocker/pair input grammar while accepting all canonicals."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] is not None:
                    if requested[axis] != observed[axis]:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as "
                            f"{observed[axis]!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the linked teaching grammar, not merely executable pair markers."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    if analysis["blocker_count"] != analysis["pair_count"]:
        errors.append(
            "strict lessons require one blocker per pair: "
            f"{analysis['blocker_count']} blockers for {analysis['pair_count']} pairs"
        )
    for pair in analysis["pairs"]:
        if sum(pair["clear"]) != 1:
            errors.append(
                f"pair color {pair['color']} must have exactly one clear route, "
                f"got {pair['clear']}"
            )
            continue
        blocked_index = 1 - pair["selected"]
        if not pair["blocked_by_5"][blocked_index]:
            errors.append(
                f"pair color {pair['color']} blocked route lacks a color-5 witness"
            )
    if analysis["selected_path_overlaps"]:
        errors.append(
            "selected pair paths overlap at "
            f"{list(analysis['selected_path_overlaps'])[:4]}"
        )
    if analysis["route_pattern"] not in ROUTE_PATTERNS:
        errors.append("route pattern is not uniquely observable")
    if analysis["blocker_pattern"] not in BLOCKER_PATTERNS:
        errors.append("blocker position pattern is not uniquely observable")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analyze(grid)
    strict_errors = strict_canonical_like(grid)
    if strict_errors:
        raise ValueError("cannot observe invalid teaching scene: " + "; ".join(strict_errors))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "pair_count": analysis["pair_count"],
        "route_pattern": analysis["route_pattern"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in analysis["grid"]]
    for pair in analysis["pairs"]:
        selected = pair["selected"]
        if selected is None:
            continue
        for row, col in pair["routes"][selected]:
            output[row][col] = pair["color"]
    return output


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = rule_mirror(grid)
    added_by_color = {
        pair["color"]: sum(
            output[row][col] == pair["color"] and analysis["grid"][row][col] == 0
            for row in range(analysis["grid_h"])
            for col in range(analysis["grid_w"])
        )
        for pair in analysis["pairs"]
    }
    return {
        **observe_overrides(grid),
        "pair_colors": list(analysis["pair_colors"]),
        "blocker_cells": [list(cell) for cell in analysis["blocker_cells"]],
        "selected_routes": [pair["selected"] for pair in analysis["pairs"]],
        "blocker_pattern": analysis["blocker_pattern"],
        "blocker_positions": [
            pair["blocker_position"] for pair in analysis["pairs"]
        ],
        "added_by_color": added_by_color,
    }


def _paint_route_choice(grid, chooser: Callable[[dict[str, Any]], int | None]):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in analysis["grid"]]
    for pair in analysis["pairs"]:
        route_index = chooser(pair)
        if route_index is None:
            continue
        for row, col in pair["routes"][route_index]:
            output[row][col] = pair["color"]
    return output


def _rival_always_first(grid):
    return _paint_route_choice(grid, lambda pair: 0)


def _rival_always_second(grid):
    return _paint_route_choice(grid, lambda pair: 1)


def _rival_elbow_only_clearance(grid):
    """Wrong shortcut: inspect only each candidate elbow, not the whole route."""

    def choose(pair: dict[str, Any]) -> int | None:
        a, b = pair["cells"]
        for route_index in (0, 1):
            row, col = _route_elbow(a, b, route_index)
            if grid[row][col] in (0, pair["color"]):
                return route_index
        return None

    return _paint_route_choice(grid, choose)


def _rival_connect_color_five(grid):
    """Wrong color-blind rule: connect every color occurring exactly twice."""
    output = rule_mirror(grid)
    blocker_cells = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == BLOCKER_COLOR
    )
    if len(blocker_cells) != 2:
        return output
    a, b = blocker_cells
    if a[0] == b[0] or a[1] == b[1]:
        route = _line_cells(a, b)
    else:
        routes = (_route_cells(a, b, 0), _route_cells(a, b, 1))
        route = next(
            (candidate for candidate in routes if _route_is_clear(grid, candidate, BLOCKER_COLOR)),
            (),
        )
    for row, col in route:
        output[row][col] = BLOCKER_COLOR
    return output


SEMANTIC_RIVALS = {
    "always_first_elbow": _rival_always_first,
    "always_second_elbow": _rival_always_second,
    "elbow_only_clearance": _rival_elbow_only_clearance,
    "connect_color_five": _rival_connect_color_five,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "blocked_first_requires_second": lambda grid: _witness(
        grid, lambda facts: any(pair["selected"] == 1 for pair in facts["pairs"])
    ),
    "blocked_second_requires_first": lambda grid: _witness(
        grid, lambda facts: any(pair["selected"] == 0 for pair in facts["pairs"])
    ),
    "blocker_color_is_inert": lambda grid: _witness(
        grid,
        lambda facts: facts["blocker_count"] == 2
        and _rival_connect_color_five(grid) != rule_mirror(grid),
    ),
    "off_elbow_blocker_requires_full_path_scan": lambda grid: _witness(
        grid,
        lambda facts: any(
            pair["blocker_position"] == "leg" for pair in facts["pairs"]
        )
        and _rival_elbow_only_clearance(grid) != rule_mirror(grid),
    ),
}

WITNESS_RIVALS = {
    "blocked_first_requires_second": ["always_first_elbow"],
    "blocked_second_requires_first": ["always_second_elbow"],
    "blocker_color_is_inert": ["connect_color_five"],
    "off_elbow_blocker_requires_full_path_scan": ["elbow_only_clearance"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible shortcut survives all demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    prepared = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        strict_errors = strict_canonical_like(demo["input"])
        if strict_errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the clear-elbow rule")
            continue
        prepared.append(demo)
    if reasons:
        return sorted(set(reasons))

    if strict_canonical_like(query["input"]):
        return ["query input is outside the teaching grammar"]
    truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in prepared):
            if competitor(query["input"]) != truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but answers the query differently"
                )
    return sorted(set(reasons))


def _scheduled_pair_count(sample_index: int) -> int:
    return (2, 2, 3, 3)[sample_index % 4]


def _scheduled_route_pattern(sample_index: int) -> str:
    return ("first", "mixed", "second", "mixed")[sample_index % 4]


def _scheduled_blocker_pattern(sample_index: int) -> str:
    return ("leg", "mixed", "elbow", "mixed")[sample_index % 4]


def _route_sequence(pattern: str, count: int) -> tuple[int, ...]:
    if pattern == "first":
        return (0,) * count
    if pattern == "second":
        return (1,) * count
    return tuple(index % 2 for index in range(count))


def _blocker_sequence(pattern: str, count: int) -> tuple[str, ...]:
    if pattern == "elbow":
        return ("elbow",) * count
    if pattern == "leg":
        return ("leg",) * count
    if pattern == "mixed":
        return tuple("elbow" if index % 2 == 0 else "leg" for index in range(count))
    raise ValueError(f"unknown blocker pattern: {pattern!r}")


def _band_height_options(band: str) -> tuple[int, ...]:
    return {
        "easy": (9, 10),
        "medium": (9, 10, 11),
        "hard": (10, 11),
    }[band]


def _band_width_options(band: str) -> tuple[int, ...]:
    return {
        "easy": (9, 10),
        "medium": (9, 10, 11),
        "hard": (10, 11, 12),
    }[band]


def _build_scene(
    *,
    height: int,
    width: int,
    colors: tuple[int, ...],
    route_pattern: str,
    blocker_pattern: str,
    rng,
) -> list[list[int]]:
    route_modes = _route_sequence(route_pattern, len(colors))
    blocker_modes = _blocker_sequence(blocker_pattern, len(colors))

    for _global_attempt in range(500):
        placements: list[dict[str, Any]] = []
        occupied: set[tuple[int, int]] = set()
        selected_cells: set[tuple[int, int]] = set()

        for color, route_mode, blocker_mode in zip(
            colors, route_modes, blocker_modes
        ):
            placed = None
            for _pair_attempt in range(600):
                row_lo, row_hi = sorted(rng.sample(range(height), 2))
                col_lo, col_hi = sorted(rng.sample(range(width), 2))
                if row_hi - row_lo < 2 or col_hi - col_lo < 2:
                    continue

                if rng.randrange(2) == 0:
                    endpoints = ((row_lo, col_lo), (row_hi, col_hi))
                else:
                    endpoints = ((row_lo, col_hi), (row_hi, col_lo))
                a, b = sorted(endpoints)
                routes = (_route_cells(a, b, 0), _route_cells(a, b, 1))
                chosen = set(routes[route_mode])
                blocked = set(routes[1 - route_mode])
                blocked_elbow = _route_elbow(a, b, 1 - route_mode)
                if blocker_mode == "elbow":
                    blocker = blocked_elbow
                else:
                    leg_cells = sorted(blocked - {a, b, blocked_elbow})
                    if not leg_cells:
                        continue
                    blocker = rng.choice(leg_cells)
                new_occupied = {a, b, blocker}

                if len(chosen) <= 3:
                    continue
                if len(new_occupied) != 3:
                    continue
                if new_occupied & occupied:
                    continue
                if new_occupied & selected_cells:
                    continue
                if chosen & occupied:
                    continue
                if chosen & selected_cells:
                    continue
                if blocker not in blocked or blocker in chosen:
                    continue

                placed = {
                    "color": color,
                    "a": a,
                    "b": b,
                    "blocker": blocker,
                    "chosen": chosen,
                }
                break

            if placed is None:
                placements = []
                break
            placements.append(placed)
            occupied.update({placed["a"], placed["b"], placed["blocker"]})
            selected_cells.update(placed["chosen"])

        if len(placements) != len(colors):
            continue

        grid = full_grid(height, width, 0)
        for placement in placements:
            color = placement["color"]
            for row, col in (placement["a"], placement["b"]):
                grid[row][col] = color
            row, col = placement["blocker"]
            grid[row][col] = BLOCKER_COLOR

        if strict_canonical_like(grid):
            continue
        analysis = _analyze(grid)
        if analysis["blocker_pattern"] != blocker_pattern:
            continue
        if (
            blocker_pattern == "mixed"
            and route_pattern != "first"
            and _rival_elbow_only_clearance(grid) == rule_mirror(grid)
        ):
            continue
        if len(colors) == 2:
            blockers = analysis["blocker_cells"]
            if blockers[0][0] == blockers[1][0] or blockers[0][1] == blockers[1][1]:
                continue
            if _rival_connect_color_five(grid) == rule_mirror(grid):
                continue
        return grid

    raise ValueError(
        f"could not place {len(colors)} blocker-controlled elbow pairs on "
        f"{height}x{width} after 500 attempts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    pair_options = (
        PAIR_COUNTS
        if overrides.get("pair_count") is not None
        else (_scheduled_pair_count(sample_index),)
    )
    pair_count = ctx.draw_choice("pair_count", pair_options)

    route_options = (
        ROUTE_PATTERNS
        if overrides.get("route_pattern") is not None
        else (_scheduled_route_pattern(sample_index),)
    )
    route_pattern = ctx.draw_choice("route_pattern", route_options)
    blocker_pattern = _scheduled_blocker_pattern(sample_index)

    any_size_override = any(
        overrides.get(label) is not None for label in ("grid_h", "grid_w")
    )
    if any_size_override:
        height_options = GRID_HEIGHTS
        width_options = GRID_WIDTHS
    elif pair_count == 2:
        # This high-frequency canonical anchor is exactly 9x9 with four colors
        # including background: the official task profile in every band.
        height_options = (9,)
        width_options = (9,)
    else:
        height_options = _band_height_options(band)
        width_options = _band_width_options(band)

    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    colors = tuple(
        ctx.draw_rng("palette").sample(list(PAIR_COLORS), pair_count)
    )
    grid = _build_scene(
        height=height,
        width=width,
        colors=colors,
        route_pattern=route_pattern,
        blocker_pattern=blocker_pattern,
        rng=ctx.draw_rng("layout"),
    )
    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("generated invalid clear-elbow scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for label, expected in ctx.recorded_draws().items():
        if label in AXES and observed[label] != expected:
            raise AssertionError(
                f"keyed axis {label}={expected!r} realized as {observed[label]!r}"
            )
    return grid
