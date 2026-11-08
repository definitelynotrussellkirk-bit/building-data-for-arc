"""Constructive curriculum for ARC task c59d7541b22e.

The canonical operation is one simultaneous scan of every 2x2 window.  When a
window contains exactly three copies of one nonzero color and one black cell,
the black cell is filled with that color.  The scan always reads the original
input, so newly filled cells never trigger a second completion in the same
application.

Default lessons alternate between canonical two-L scenes and a witness scene.
The witness combines an overlapping two-window zigzag with a one-pass cascade
trap.  It therefore refutes three tempting rules: fill each component's
bounding box, iterate completions to a fixed point, or fill only one corner per
component.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c59d7541b22e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.2"
RULE_HASH = "014f3ef40cee"

SUMMARY = (
    "Complete every same-color three-of-four 2x2 window in one simultaneous "
    "pass. Alternating canonical and witness profiles expose overlapping "
    "windows and distinguish one-pass behavior from iterative closure."
)

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = ("canonical", "witness")
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors at 7 or 8; witness profile spans 7..14",
        "valid": "7..14",
        "doc": "Exact input height; every value works in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors at 7 or 8; witness profile spans 7..16",
        "valid": "7..16",
        "doc": "Exact input width; every value works in every difficulty band.",
    },
    "profile": {
        "type": "enum",
        "default": "alternates canonical|witness by seed and sample_index",
        "valid": "canonical|witness",
        "doc": "Canonical L pairs or a shortcut-refuting two-component witness.",
    },
}

INVARIANTS = [
    "background is black(0)",
    "ordinary inputs contain two separated monochrome components",
    "each component contains at least one eligible three-of-four 2x2 window",
    "all completions are computed simultaneously from the original input",
    "witness scenes refute bounding-box, iterative, and one-fill shortcuts",
]

# Normalized motifs.  All D4 transforms are permitted.
_BASE_SHAPES: dict[str, frozenset[tuple[int, int]]] = {
    "l": frozenset({(0, 0), (0, 1), (1, 0)}),
    # Two overlapping eligible windows; both must be completed simultaneously.
    "multi": frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    # The left window is eligible now.  Filling it makes the right window
    # eligible only on a forbidden second pass.
    "cascade": frozenset({(0, 0), (0, 1), (0, 2), (1, 0)}),
}


def _normalize(points: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(points)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _d4_variants(points: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    cells = tuple(points)
    variants = set()
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for row, col in cells:
                x, y = row, -col if reflected else col
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {name: _d4_variants(shape) for name, shape in _BASE_SHAPES.items()}
_SHAPE_KIND = {
    variant: name
    for name, variants in _SHAPE_VARIANTS.items()
    for variant in variants
}


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9; booleans are invalid"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    result: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        todo = [start]
        cells = {start}
        while todo:
            row, col = todo.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = row + dr, col + dc
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        signature = _normalize(cells)
        result.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "signature": signature,
                "kind": _SHAPE_KIND.get(signature),
            }
        )
    return result


def _eligible_windows(grid: list[list[int]]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                target = next(point for point, value in zip(cells, values) if value == 0)
                windows.append(
                    {
                        "top": row,
                        "left": col,
                        "cells": cells,
                        "target": target,
                        "color": nonzero[0],
                    }
                )
    return windows


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned one-pass Racket authority."""
    errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    for window in _eligible_windows(grid):
        row, col = window["target"]
        out[row][col] = window["color"]
    return out


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    return rule_mirror(grid)


def _component_separation_errors(components: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, first in enumerate(components):
        for second in components[index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in first["cells"]
                for r2, c2 in second["cells"]
            ):
                errors.append("foreground components must not share a 2x2 neighborhood")
    return errors


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_shape_errors(grid)
    if errors:
        return {"errors": errors, "profile": None}

    height, width = len(grid), len(grid[0])
    components = _components(grid)
    windows = _eligible_windows(grid)
    colors = {component["color"] for component in components}
    errors = []
    if not (7 <= height <= 30 and 7 <= width <= 30):
        errors.append(f"expected task-scale dimensions at least 7x7, found {height}x{width}")
    if 0 not in {value for row in grid for value in row}:
        errors.append("black(0) background is absent")
    if len(components) != 2:
        errors.append(f"expected exactly two foreground components, found {len(components)}")
    if len(colors) != len(components):
        errors.append("the two foreground components must use distinct colors")
    unknown = [component for component in components if component["kind"] is None]
    if unknown:
        errors.append("foreground component shape is outside the L/multi/cascade grammar")
    errors.extend(_component_separation_errors(components))

    targets: dict[tuple[int, int], set[int]] = {}
    for window in windows:
        targets.setdefault(window["target"], set()).add(window["color"])
    if not windows:
        errors.append("no eligible same-color three-of-four 2x2 window")
    if any(len(target_colors) > 1 for target_colors in targets.values()):
        errors.append("two eligible windows demand conflicting colors at one target")

    for component in components:
        if not any(
            window["color"] == component["color"]
            and any(point in component["cells"] for point in window["cells"])
            for window in windows
        ):
            errors.append(
                f"color {component['color']} component has no eligible completion window"
            )

    kinds = sorted(component["kind"] for component in components if component["kind"])
    if kinds == ["l", "l"]:
        profile = "canonical"
    elif kinds == ["cascade", "multi"]:
        profile = "witness"
    else:
        profile = None

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "windows": windows,
        "profile": profile,
    }


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """Recognize the narrow lawful grammar containing every official input."""
    return list(_analyze(grid)["errors"])


def self_check(
    grid: list[list[int]], *, difficulty: str | None = None, meta: Any = None
) -> list[str]:
    errors = strict_canonical_like(grid)
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unknown difficulty {difficulty!r}")
    expected = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(expected, dict) and expected and not errors:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"could not observe overrides: {exc}")
        else:
            for name, value in expected.items():
                if value is not None and observed.get(name) != value:
                    errors.append(
                        f"override {name!r} expected {value!r}, observed {observed.get(name)!r}"
                    )
    return errors


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    del difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lower, upper in (("grid_h", 7, 14), ("grid_w", 7, 16)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
        if not lower <= value <= upper:
            raise ValueError(f"{name} override {value} outside [{lower}, {upper}]")
    profile = overrides.get("profile")
    if profile is not None and profile not in SCHEDULE_PROFILES:
        raise ValueError(f"profile override must be one of {SCHEDULE_PROFILES}, got {profile!r}")


def _draw_scheduled_int(ctx: Any, label: str, low: int, high: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, low, high)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _scheduled_dimensions(ctx: Any, profile: str) -> tuple[int, int]:
    rng = ctx.draw_rng("dimension_schedule")
    if profile == "canonical":
        return ((7, 7), (8, 8))[rng.randrange(2)]
    bands = {
        None: ((7, 14), (7, 16)),
        "easy": ((7, 9), (7, 10)),
        "medium": ((9, 12), (9, 13)),
        "hard": ((11, 14), (13, 16)),
    }
    (h_low, h_high), (w_low, w_high) = bands[ctx.difficulty]
    return rng.randint(h_low, h_high), rng.randint(w_low, w_high)


def _translated(shape: tuple[tuple[int, int], ...], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + row, left + col) for row, col in shape}


def _separated(first: set[tuple[int, int]], second: set[tuple[int, int]]) -> bool:
    return all(
        max(abs(r1 - r2), abs(c1 - c2)) > 1
        for r1, c1 in first
        for r2, c2 in second
    )


def _candidate_placements(
    kind: str, height: int, width: int
) -> list[set[tuple[int, int]]]:
    result = []
    for shape in _SHAPE_VARIANTS[kind]:
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        for top in range(height - shape_h + 1):
            for left in range(width - shape_w + 1):
                result.append(_translated(shape, top, left))
    return result


def _place_components(
    grid: list[list[int]], kinds: tuple[str, str], colors: tuple[int, int], rng: Any
) -> None:
    height, width = len(grid), len(grid[0])
    first_candidates = _candidate_placements(kinds[0], height, width)
    second_candidates = _candidate_placements(kinds[1], height, width)
    rng.shuffle(first_candidates)
    rng.shuffle(second_candidates)
    chosen: tuple[set[tuple[int, int]], set[tuple[int, int]]] | None = None
    for first in first_candidates:
        for second in second_candidates:
            if _separated(first, second):
                chosen = first, second
                break
        if chosen is not None:
            break
    if chosen is None:
        raise ValueError(
            f"cannot place profile {kinds!r} on requested {height}x{width} canvas"
        )
    for cells, color in zip(chosen, colors):
        for row, col in cells:
            grid[row][col] = color


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("profile") is not None:
        profile = ctx.draw_choice("profile", SCHEDULE_PROFILES)
    else:
        profile = ctx.draw_choice("profile", (scheduled_profile,))
    scheduled_h, scheduled_w = _scheduled_dimensions(ctx, profile)
    height = _draw_scheduled_int(ctx, "grid_h", 7, 14, scheduled_h)
    width = _draw_scheduled_int(ctx, "grid_w", 7, 16, scheduled_w)
    colors = ctx.draw_distinct_colors("component_colors", n=2, exclude=(0,))
    rng = ctx.draw_rng("layout")

    kinds = ("l", "l") if profile == "canonical" else ("multi", "cascade")
    grid = full_grid(height, width, 0)
    _place_components(grid, kinds, colors, rng)

    findings = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.overrides_used()},
    )
    if findings:
        raise AssertionError("constructive generator violated its contract: " + "; ".join(findings))
    return grid


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    if analysis["profile"] not in SCHEDULE_PROFILES:
        raise ValueError("grid does not realize a declared exact profile")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "profile": analysis["profile"],
    }


def _rival_component_bounding_boxes(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for component in _components(grid):
        rows = [row for row, _ in component["cells"]]
        cols = [col for _, col in component["cells"]]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                out[row][col] = component["color"]
    return out


def _rival_iterate_until_stable(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for _ in range(len(grid) * len(grid[0])):
        nxt = rule_mirror(out)
        if nxt == out:
            return out
        out = nxt
    raise AssertionError("monotone completion failed to reach a fixed point")


def _rival_one_fill_per_component(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    components = _components(grid)
    owner = {
        point: index
        for index, component in enumerate(components)
        for point in component["cells"]
    }
    used: set[int] = set()
    for window in _eligible_windows(grid):
        source = next(point for point in window["cells"] if grid[point[0]][point[1]] != 0)
        component_index = owner[source]
        if component_index in used:
            continue
        used.add(component_index)
        row, col = window["target"]
        out[row][col] = window["color"]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "component_bounding_boxes": _rival_component_bounding_boxes,
    "iterate_until_stable": _rival_iterate_until_stable,
    "one_fill_per_component": _rival_one_fill_per_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "component_bounding_boxes": _rival_component_bounding_boxes,
    "iterate_until_stable": _rival_iterate_until_stable,
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def _witness_for(rival_name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        try:
            return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
        except (TypeError, ValueError):
            return False

    return predicate


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    name: _witness_for(name) for name in SEMANTIC_RIVALS
}


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Finite certificate that no declared competitor survives the demonstrations."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_demos: list[dict[str, list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labelled input/output pair")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task grammar: {'; '.join(errors)}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} label disagrees with the one-pass rule")
            continue
        valid_demos.append(pair)
    if reasons:
        return reasons

    survivors = [
        name
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in valid_demos)
    ]
    if survivors:
        reasons.append("declared competitors survive all demos: " + ", ".join(survivors))

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append("query is outside the task grammar: " + "; ".join(query_errors))
        elif "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query label disagrees with the one-pass rule")
    return reasons
