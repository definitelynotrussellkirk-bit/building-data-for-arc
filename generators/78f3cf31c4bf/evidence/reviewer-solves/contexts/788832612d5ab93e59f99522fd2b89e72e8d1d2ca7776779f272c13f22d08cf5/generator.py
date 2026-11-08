"""Generator for ``Missing 2x2 Corner`` (78f3cf31c4bf).

The authoritative rule is local and simultaneous: every 2x2 window containing
three equal non-zero cells and one zero receives that colour in its missing
corner.  The curriculum preserves the canonical isolated motifs while adding
connected multi-window components, repeated colours, mixed-colour near-matches,
and one-pass/closure contrasts.  These controls separate the exact rule from
several shortcuts that happen to fit all four canonical pairs.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78f3cf31c4bf"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # exact axes plus adversarial local-rule curriculum
RULE_HASH = "4954a1b1ccb4"  # normalized canonical program_solution

SUMMARY = (
    "Find every 2x2 window with exactly three cells of one non-background "
    "colour and one zero, then fill that zero with the same colour. Windows "
    "are evaluated from the original input in one simultaneous pass. Scenes "
    "include canonical-profile isolated motifs, connected multi-window "
    "components, repeated colours, and mixed-colour near-matches."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all other values are ARC colours 1..9",
    "every generated scene contains 3..6 unambiguous local 2x2 completions",
    "the missing cells use 2..4 different corner positions within each scene",
    "connected scenes contain one larger same-colour component with two local holes",
    "isolated repeated-colour scenes refute one-component/one-colour shortcuts",
    "multicolour connected scenes contain an ignored mixed-colour near-match",
    "every connected scene distinguishes one simultaneous pass from closure",
    "any three consecutive default indices contain all declared semantic controls",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three canonical-profile anchors; otherwise difficulty-skewed",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "three canonical-profile anchors; otherwise difficulty-skewed",
        "valid": "8..16",
    },
    "target_count": {
        "type": "int",
        "default": "six-step lesson schedule",
        "valid": "3..6",
    },
    "color_count": {
        "type": "int",
        "default": "six-step lesson schedule",
        "valid": "1..3",
    },
    "layout_mode": {
        "type": "str",
        "default": "six-step lesson schedule",
        "valid": "isolated|connected",
    },
    "corner_diversity": {
        "type": "int",
        "default": "six-step lesson schedule",
        "valid": "2..4",
    },
}

# Every boundary combination above is supported; declaring the empty strict
# matrix prevents an undeclared ValueError from being mistaken for intent.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = (
    {"target_count": 3, "corner_diversity": 4},
    {"target_count": 3, "color_count": 3, "layout_mode": "connected"},
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Cell = tuple[int, int]
Target = tuple[int, int, int, Cell, int]

# A six-slot cyclic curriculum.  The first three slots anchor three of the
# selected task's four public profiles: 6x8/palette 3, 7x8/palette 4, and
# 6x9/palette 3.  Every three consecutive slots include a connected
# multicolour control, which simultaneously refutes component-bbox,
# colour-agreement, and repeat-until-stable shortcuts; each three-slot lesson
# also contains a repeated-colour counterexample.
_SCHEDULE = (
    {"name": "anchor_connected_6x8", "target_count": 4, "color_count": 2,
     "layout_mode": "connected", "corner_diversity": 3, "grid_h": 6, "grid_w": 8},
    {"name": "anchor_canonical_7x8", "target_count": 3, "color_count": 3,
     "layout_mode": "isolated", "corner_diversity": 3, "grid_h": 7, "grid_w": 8},
    {"name": "anchor_repeated_6x9", "target_count": 3, "color_count": 2,
     "layout_mode": "isolated", "corner_diversity": 2, "grid_h": 6, "grid_w": 9},
    {"name": "expanded_connected", "target_count": 6, "color_count": 2,
     "layout_mode": "connected", "corner_diversity": 4},
    {"name": "expanded_repeated", "target_count": 4, "color_count": 2,
     "layout_mode": "isolated", "corner_diversity": 3},
    {"name": "expanded_single_connected", "target_count": 5, "color_count": 1,
     "layout_mode": "connected", "corner_diversity": 2},
)
SCHEDULE_PROFILES = tuple(slot["name"] for slot in _SCHEDULE)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]["name"]


def _target_windows(grid: list[list[int]]) -> list[Target]:
    """Return (row, col, colour, missing_cell, missing_corner_index)."""
    height, width = len(grid), len(grid[0])
    targets: list[Target] = []
    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                missing_index = values.index(0)
                targets.append(
                    (row, col, nonzero[0], cells[missing_index], missing_index)
                )
    return targets


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    components: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        colour = grid[start[0]][start[1]]
        queue = deque([start])
        remaining.remove(start)
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbour = row + drow, col + dcol
                if neighbour in remaining and grid[neighbour[0]][neighbour[1]] == colour:
                    remaining.remove(neighbour)
                    cells.add(neighbour)
                    queue.append(neighbour)
        components.append({"color": colour, "cells": cells})
    return components


def _valid_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limits: {len(grid)}x{width}")
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("grid values must be integer ARC colours 0..9")
                return errors
    return errors


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid_errors(grid)
    if errors:
        return {"errors": errors, "targets": [], "components": []}

    targets = _target_windows(grid)
    if not targets:
        errors.append("expected at least one local three-of-four 2x2 completion")

    by_missing: dict[Cell, set[int]] = defaultdict(set)
    for _, _, colour, missing, _ in targets:
        by_missing[missing].add(colour)
    conflicts = {
        cell: sorted(colours)
        for cell, colours in by_missing.items()
        if len(colours) > 1
    }
    if conflicts:
        errors.append(f"a missing cell is claimed by multiple colours: {conflicts}")

    # Near-matches are useful negatives when genuine targets are also present.
    # A mixed-only scene remains outside this positive-lesson grammar. The
    # unchanged target detector still requires three EQUAL nonzero cells.
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            values = [
                grid[row][col], grid[row][col + 1],
                grid[row + 1][col], grid[row + 1][col + 1],
            ]
            nonzero = [value for value in values if value != 0]
            if not targets and len(nonzero) == 3 and len(set(nonzero)) > 1:
                errors.append(
                    f"mixed-colour-only scene: three-of-four window at ({row},{col})"
                )
                break
        if any("mixed-colour" in error for error in errors):
            break

    colours = sorted({value for row in grid for value in row if value != 0})
    target_colours = {target[2] for target in targets}
    unused_colours = sorted(set(colours) - target_colours)
    if unused_colours:
        errors.append(
            f"non-background colours without any local completion: {unused_colours}"
        )

    components = _components(grid)
    target_cells_by_component: list[int] = []
    for component in components:
        cells = component["cells"]
        count = sum(
            colour == component["color"]
            and any(cell in cells for cell in ((row, col), missing))
            for row, col, colour, missing, _ in targets
        )
        target_cells_by_component.append(count)

    return {
        "errors": errors,
        "height": len(grid),
        "width": len(grid[0]),
        "targets": targets,
        "target_count": len(targets),
        "colors": colours,
        "color_count": len(colours),
        "corner_diversity": len({target[4] for target in targets}),
        "components": components,
        "layout_mode": (
            "connected"
            if any(len(component["cells"]) > 3 for component in components)
            else "isolated"
        ),
    }


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "target_count": analysis["target_count"],
        "color_count": analysis["color_count"],
        "layout_mode": analysis["layout_mode"],
        "corner_diversity": analysis["corner_diversity"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-local input grammar while accepting canonical inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
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
    """Strict linked predicate for canonical and generated lesson scenes."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if not 2 <= analysis["target_count"] <= 6:
        errors.append(
            f"expected 2..6 local completion targets, got {analysis['target_count']}"
        )
    if not 1 <= analysis["color_count"] <= 3:
        errors.append(f"expected 1..3 target colours, got {analysis['color_count']}")
    if analysis["corner_diversity"] < 2:
        errors.append("at least two missing-corner positions are required")
    if rule_mirror(grid) == grid:
        errors.append("the authoritative transformation must change the grid")
    return errors


def _transform(cells: Iterable[Cell], transform: int) -> frozenset[Cell]:
    """Apply one of the eight D4 transforms and normalize to (0,0)."""
    points = list(cells)
    transformed: list[Cell] = []
    for row, col in points:
        if transform == 0:
            point = (row, col)
        elif transform == 1:
            point = (col, -row)
        elif transform == 2:
            point = (-row, -col)
        elif transform == 3:
            point = (-col, row)
        elif transform == 4:
            point = (row, -col)
        elif transform == 5:
            point = (-row, col)
        elif transform == 6:
            point = (col, row)
        else:
            point = (-col, -row)
        transformed.append(point)
    row0 = min(row for row, _ in transformed)
    col0 = min(col for _, col in transformed)
    return frozenset((row - row0, col - col0) for row, col in transformed)


def _pattern_grid(cells: frozenset[Cell]) -> list[list[int]]:
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    grid = full_grid(height, width, 0)
    for row, col in cells:
        grid[row][col] = 1
    return grid


def _pattern_corner_set(cells: frozenset[Cell]) -> frozenset[int]:
    return frozenset(target[4] for target in _target_windows(_pattern_grid(cells)))


def _unique_transforms(cells: Iterable[Cell]) -> tuple[frozenset[Cell], ...]:
    unique = {_transform(cells, index) for index in range(8)}
    return tuple(sorted(unique, key=lambda item: (max(r for r, _ in item), sorted(item))))


# Five cells in a 2x4 bbox create two adjacent local holes but leave one bbox
# zero untouched by the real rule.  Every transform remains one 4-connected
# component and is a decisive counterexample to component-bbox completion.
_CONNECTED_BASE = {(0, 0), (0, 1), (0, 2), (0, 3), (1, 1)}
_CONNECTED_PATTERNS = tuple(
    pattern
    for pattern in _unique_transforms(_CONNECTED_BASE)
    if len(_target_windows(_pattern_grid(pattern))) == 2
    and len(_pattern_corner_set(pattern)) == 2
)


# A longer bar leaves a zero that is both (a) next to a mixed-colour L in
# the input and (b) fillable only on a second pass. Its accent colour is reused
# by a genuine isolated target, so colour_count still means participating
# colours, not an extra decorative palette slot. Reserving the accent together
# with the main cells prevents cross-module interactions during placement.
_DECOY_MAIN_BASE = {(0, col) for col in range(5)} | {(1, 1)}
_DECOY_ACCENT_BASE = {(1, 4)}
_DECOY_ACCENTS: dict[frozenset[Cell], Cell] = {}
for _index in range(8):
    _main = _transform(_DECOY_MAIN_BASE, _index)
    _support = _transform(_DECOY_MAIN_BASE | _DECOY_ACCENT_BASE, _index)
    _DECOY_ACCENTS[_main] = next(iter(_support - _main))
_DECOY_PATTERNS = tuple(sorted(
    _DECOY_ACCENTS,
    key=lambda item: (max(r for r, _ in item), sorted(item)),
))


def _isolated_pattern(missing_corner: int) -> frozenset[Cell]:
    cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    cells.remove(((0, 0), (0, 1), (1, 0), (1, 1))[missing_corner])
    return frozenset(cells)


def _halo(cells: Iterable[Cell], height: int, width: int) -> set[Cell]:
    result: set[Cell] = set()
    for row, col in cells:
        for drow in (-1, 0, 1):
            for dcol in (-1, 0, 1):
                neighbour = row + drow, col + dcol
                if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width:
                    result.add(neighbour)
    return result


def _candidate_placements(
    pattern: frozenset[Cell], height: int, width: int, rng
) -> list[frozenset[Cell]]:
    pattern_h = max(row for row, _ in pattern) + 1
    pattern_w = max(col for _, col in pattern) + 1
    candidates = [
        frozenset((top + row, left + col) for row, col in pattern)
        for top in range(height - pattern_h + 1)
        for left in range(width - pattern_w + 1)
    ]
    rng.shuffle(candidates)
    return candidates


def _place_patterns(
    patterns: list[frozenset[Cell]], height: int, width: int, rng
) -> list[frozenset[Cell]]:
    ordered = sorted(
        enumerate(patterns),
        key=lambda item: (
            -(max(row for row, _ in item[1]) + 1) * (max(col for _, col in item[1]) + 1),
            item[0],
        ),
    )
    candidates = {
        index: _candidate_placements(pattern, height, width, rng)
        for index, pattern in ordered
    }
    placed: dict[int, frozenset[Cell]] = {}

    def search(position: int, reserved: set[Cell]) -> bool:
        if position == len(ordered):
            return True
        original_index, _ = ordered[position]
        for cells in candidates[original_index]:
            if cells & reserved:
                continue
            placed[original_index] = cells
            if search(position + 1, reserved | _halo(cells, height, width)):
                return True
            del placed[original_index]
        return False

    if not search(0, set()):
        raise ValueError(
            f"cannot place {len(patterns)} separated modules in {height}x{width}"
        )
    return [placed[index] for index in range(len(patterns))]


def _corner_plan(
    target_count: int, corner_diversity: int, layout_mode: str, rng, *, colour_decoy: bool = False
) -> tuple[frozenset[Cell] | None, list[int]]:
    if layout_mode == "isolated":
        chosen = rng.sample(range(4), corner_diversity)
        corners = chosen + [chosen[index % len(chosen)] for index in range(target_count - len(chosen))]
        rng.shuffle(corners)
        return None, corners

    connected = rng.choice(_DECOY_PATTERNS if colour_decoy else _CONNECTED_PATTERNS)
    anchor_corners = sorted(_pattern_corner_set(connected))
    chosen = list(anchor_corners)
    remaining = [corner for corner in range(4) if corner not in chosen]
    rng.shuffle(remaining)
    chosen.extend(remaining[: corner_diversity - len(chosen)])
    isolated_count = target_count - 2
    # Ensure every additional requested corner appears before filling remaining
    # isolated modules from the same exact corner set.
    must_use = [corner for corner in chosen if corner not in anchor_corners]
    corners = must_use + [chosen[index % len(chosen)] for index in range(isolated_count - len(must_use))]
    rng.shuffle(corners)
    return connected, corners


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    slot = _SCHEDULE[sample_index % len(_SCHEDULE)]
    effective = dict(overrides)
    for name in (
        "target_count", "color_count", "layout_mode", "corner_diversity",
        "grid_h", "grid_w",
    ):
        if name in slot:
            effective.setdefault(name, slot[name])

    # Keep every single-axis override independently realizable.  Only an
    # explicitly requested impossible joint tuple is rejected and declared in
    # INCOMPATIBLE_OVERRIDE_COMBINATIONS above.
    if effective["target_count"] == 3 and effective["corner_diversity"] == 4:
        if "target_count" not in overrides:
            effective["target_count"] = 4
        elif "corner_diversity" not in overrides:
            effective["corner_diversity"] = 3
        else:
            raise ValueError(
                "incompatible overrides: target_count=3 and corner_diversity=4"
            )
    if (
        effective["target_count"] == 3
        and effective["color_count"] == 3
        and effective["layout_mode"] == "connected"
    ):
        if "target_count" not in overrides:
            effective["target_count"] = 4
        elif "color_count" not in overrides:
            effective["color_count"] = 2
        elif "layout_mode" not in overrides:
            effective["layout_mode"] = "isolated"
        else:
            raise ValueError(
                "incompatible overrides: target_count=3, color_count=3, "
                "layout_mode=connected"
            )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_diff("grid_h", 6, 14)
    width = ctx.draw_int_diff("grid_w", 8, 16)
    target_count = ctx.draw_int("target_count", 3, 6)
    color_count = ctx.draw_int("color_count", 1, 3)
    layout_mode = ctx.draw_choice("layout_mode", ("isolated", "connected"))
    corner_diversity = ctx.draw_int("corner_diversity", 2, 4)

    layout_rng = ctx.draw_rng("layout")
    connected, isolated_corners = _corner_plan(
        target_count, corner_diversity, layout_mode, layout_rng,
        colour_decoy=color_count >= 2,
    )
    patterns: list[frozenset[Cell]] = []
    if connected is not None:
        patterns.append(connected)
    patterns.extend(_isolated_pattern(corner) for corner in isolated_corners)

    accent = _DECOY_ACCENTS.get(connected) if connected is not None else None
    supports = list(patterns)
    if accent is not None:
        supports[0] = supports[0] | {accent}
    placed = _place_patterns(supports, height, width, layout_rng)
    colors = list(
        ctx.draw_distinct_colors("colors", n=color_count, exclude={0})
    )
    assignments = colors + [colors[index % color_count] for index in range(len(patterns) - color_count)]
    layout_rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    for colour, cells in zip(assignments, placed):
        for row, col in cells:
            grid[row][col] = colour
    if accent is not None:
        top = min(row for row, _ in placed[0])
        left = min(col for _, col in placed[0])
        accent_colour = layout_rng.choice([colour for colour in colors if colour != assignments[0]])
        grid[top + accent[0]][left + accent[1]] = accent_colour

    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "target_count": target_count,
        "color_count": color_count,
        "layout_mode": layout_mode,
        "corner_diversity": corner_diversity,
    }
    if observed != requested:
        raise ValueError(
            f"placement changed exact axes: requested={requested}, observed={observed}"
        )
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure simultaneous mirror of the pinned Racket authority."""
    output = [list(row) for row in grid]
    for _, _, colour, missing, _ in _target_windows(grid):
        output[missing[0]][missing[1]] = colour
    return output


def _component_bbox_rival(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _components(grid):
        cells = component["cells"]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = component["color"]
    return output


def _one_completion_per_color_rival(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    seen: set[int] = set()
    for _, _, colour, missing, _ in _target_windows(grid):
        if colour in seen:
            continue
        seen.add(colour)
        output[missing[0]][missing[1]] = colour
    return output


def _three_cells_per_color_rival(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    counts = defaultdict(int)
    for row in grid:
        for colour in row:
            if colour != 0:
                counts[colour] += 1
    for _, _, colour, missing, _ in _target_windows(grid):
        if counts[colour] == 3:
            output[missing[0]][missing[1]] = colour
    return output


def _ignore_colour_agreement_rival(grid: list[list[int]]) -> list[list[int]]:
    """Fill any three-of-four window using its majority colour, even if mixed."""
    output = [list(row) for row in grid]
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            cells = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3:
                colour = min(set(nonzero), key=lambda value: (-nonzero.count(value), value))
                r, c = cells[values.index(0)]
                output[r][c] = colour
    return output


def _repeat_until_stable_rival(grid: list[list[int]]) -> list[list[int]]:
    """Incorrectly use newly completed corners as evidence for later passes."""
    output = [list(row) for row in grid]
    # Each changing pass consumes at least one zero; the bound is exact enough
    # for every supported ARC grid and makes a future rule regression visible.
    for _ in range(len(grid) * len(grid[0]) + 1):
        updated = rule_mirror(output)
        if updated == output:
            return output
        output = updated
    raise RuntimeError("completion did not converge within the grid-area bound")


def _has_colour_agreement_counterexample(grid) -> bool:
    return _ignore_colour_agreement_rival(grid) != rule_mirror(grid)


def _has_simultaneous_counterexample(grid) -> bool:
    return _repeat_until_stable_rival(grid) != rule_mirror(grid)


def _has_connected_counterexample(grid) -> bool:
    return (
        observe_overrides(grid)["layout_mode"] == "connected"
        and _component_bbox_rival(grid) != rule_mirror(grid)
    )


def _has_repeated_color_counterexample(grid) -> bool:
    analysis = _analysis(grid)
    return (
        analysis["target_count"] > analysis["color_count"]
        and _one_completion_per_color_rival(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    # Keep semantic witnesses claim-bearing: every entry has an explicit rival
    # that agrees with the canonical examples and is separated by this input.
    # Distribution/profile coverage is audited independently by the census.
    "connected_component_counterexample": _has_connected_counterexample,
    "repeated_color_counterexample": _has_repeated_color_counterexample,
    "colour_agreement_counterexample": _has_colour_agreement_counterexample,
    "simultaneous_update_counterexample": _has_simultaneous_counterexample,
}

SEMANTIC_RIVALS = {
    "component_bbox_completion": _component_bbox_rival,
    "one_completion_per_color": _one_completion_per_color_rival,
    "require_exactly_three_cells_per_color": _three_cells_per_color_rival,
    "ignore_colour_agreement": _ignore_colour_agreement_rival,
    "repeat_until_stable": _repeat_until_stable_rival,
}
WITNESS_RIVALS = {
    "colour_agreement_counterexample": ["ignore_colour_agreement"],
    "simultaneous_update_counterexample": ["repeat_until_stable"],
    "connected_component_counterexample": ["component_bbox_completion"],
    "repeated_color_counterexample": [
        "one_completion_per_color",
        "require_exactly_three_cells_per_color",
    ],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named canonical-fitting shortcut survives demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the local 2x2 rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            rival_query = competitor(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
