"""Generator for ARC task ``410fb6b72f16`` (Singleton Blue Selector).

The selected Racket rule recolors each blue (1) 4-connected component of size
one red (2) and leaves every larger blue component unchanged.  Ordinary draws
always contain both rule branches, a size-two boundary witness, and a larger
component.  Every third scheduled draw also includes an isolated green
singleton that the oracle leaves untouched; this prevents a color-blind
"recolor every singleton" shortcut from surviving a three-demo lesson.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "410fb6b72f16"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "286a8c0cd852"
MIN_STRICT_FRAC = 0.50
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a zero background, find 4-connected blue (1) components. Recolor only "
    "components of size exactly one red (2); preserve every larger blue "
    "component. Some generated lessons add an isolated green singleton that "
    "must remain green, making both the blue color condition and size-one "
    "condition observable."
)

INVARIANTS = [
    "background is 0",
    "every ordinary draw has at least two singleton blue components",
    "every ordinary draw has a blue domino and a blue component of size 3 or 4",
    "optional green distractors are isolated singletons and remain unchanged",
    "the output has the same shape and differs only at singleton blue cells",
]

COUNTER_HYPOTHESES = [
    "leave the input unchanged",
    "recolor every blue cell red",
    "recolor every blue component of size at most two",
    "recolor every singleton component regardless of color",
    "recolor fixed positions or one side of the grid",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "difficulty-weighted", "valid": "8..11"},
    "singleton_count": {"type": "int", "default": "difficulty-weighted", "valid": "2..4"},
    "large_size": {"type": "int", "default": "difficulty-weighted", "valid": "3..4"},
    "distractor_count": {"type": "int", "default": "sample_index schedule", "valid": "0..1"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
_INT_DOMAINS = {
    "grid_h": range(8, 11),
    "grid_w": range(8, 12),
    "singleton_count": range(2, 5),
    "large_size": range(3, 5),
    "distractor_count": range(0, 2),
}

_HEIGHTS_BY_BAND = {
    "easy": (8, 8, 9),
    "medium": (8, 9, 10),
    "hard": (9, 10, 10),
}
_WIDTHS_BY_BAND = {
    "easy": (8, 8, 9),
    "medium": (8, 9, 10),
    "hard": (9, 10, 10, 11),
}
_SINGLETONS_BY_BAND = {
    "easy": (2, 2, 3),
    "medium": (2, 3, 4),
    "hard": (3, 4, 4),
}
_LARGE_SIZES_BY_BAND = {
    "easy": (3, 3, 4),
    "medium": (3, 4),
    "hard": (4, 4, 3),
}

_DOMINOES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)
_SHAPES = {
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
    ),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_requested(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    for name, value in overrides.items():
        if not isinstance(value, int) or isinstance(value, bool) or value not in _INT_DOMAINS[name]:
            domain = _INT_DOMAINS[name]
            raise ValueError(
                f"override {name}={value!r} outside {domain.start}..{domain.stop - 1}"
            )


def _draw_int_axis(ctx, label: str, choices: tuple[int, ...], overrides: dict[str, Any]) -> int:
    domain = _INT_DOMAINS[label]
    if label in overrides:
        return ctx.draw_int(label, domain.start, domain.stop - 1)
    return ctx.draw_choice(label, choices)


def _normalize_shape(shape):
    min_r = min(r for r, _ in shape)
    min_c = min(c for _, c in shape)
    return tuple(sorted((r - min_r, c - min_c) for r, c in shape))


def _translated_candidates(height: int, width: int, shape):
    shape = _normalize_shape(shape)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    return [
        tuple((r0 + r, c0 + c) for r, c in shape)
        for r0 in range(height - sh + 1)
        for c0 in range(width - sw + 1)
    ]


def _orth_moat(cells, height: int, width: int):
    out = set(cells)
    for r, c in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width:
                out.add((nr, nc))
    return out


def _place_scene(height: int, width: int, singleton_count: int, large_size: int,
                 distractor_count: int, rng) -> list[list[int]]:
    """Backtracking placement with an orthogonal moat between all objects."""
    for attempt in range(120):
        domino = rng.choice(_DOMINOES)
        large = rng.choice(_SHAPES[large_size])
        scene_objects = [(1, domino), (1, large)]
        scene_objects += [(1, ((0, 0),)) for _ in range(singleton_count)]
        scene_objects += [(3, ((0, 0),)) for _ in range(distractor_count)]

        # Large objects first; randomize equal-size singleton order only through
        # candidate shuffles so replay remains deterministic.
        placements: list[tuple[int, tuple[tuple[int, int], ...]]] = []
        forbidden: set[tuple[int, int]] = set()
        success = True
        for color, shape in scene_objects:
            candidates = _translated_candidates(height, width, shape)
            rng.shuffle(candidates)
            chosen = next((cand for cand in candidates if not (set(cand) & forbidden)), None)
            if chosen is None:
                success = False
                break
            placements.append((color, chosen))
            forbidden |= _orth_moat(chosen, height, width)
        if not success:
            continue
        grid = full_grid(height, width, 0)
        for color, cells in placements:
            for r, c in cells:
                grid[r][c] = color
        return grid
    raise ValueError(
        "could not place the requested singleton/domino/large-component scene "
        f"on {height}x{width} after 120 deterministic attempts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_requested(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, "grid_h", _HEIGHTS_BY_BAND[band], overrides)
    width = _draw_int_axis(ctx, "grid_w", _WIDTHS_BY_BAND[band], overrides)
    singleton_count = _draw_int_axis(
        ctx, "singleton_count", _SINGLETONS_BY_BAND[band], overrides
    )
    large_size = _draw_int_axis(ctx, "large_size", _LARGE_SIZES_BY_BAND[band], overrides)
    scheduled_distractors = 1 if int(sample_index) % EXAMPLES_NEEDED == 0 else 0
    distractor_count = _draw_int_axis(
        ctx, "distractor_count", (scheduled_distractors,), overrides
    )
    return _place_scene(
        height,
        width,
        singleton_count,
        large_size,
        distractor_count,
        ctx.draw_rng("layout"),
    )


def _components(grid, color: int | None = None):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out = []
    for r in range(height):
        for c in range(width):
            value = grid[r][c]
            if value == 0 or (color is not None and value != color) or (r, c) in seen:
                continue
            cells = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append({"color": value, "cells": tuple(cells), "size": len(cells)})
    return out


def _analyze(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1, 3):
                errors.append(f"cell ({r},{c}) has unsupported input color {value!r}")
    if errors:
        return {"height": len(grid), "width": width, "errors": errors}
    components = _components(grid)
    blue = [component for component in components if component["color"] == 1]
    distractors = [component for component in components if component["color"] == 3]
    return {
        "height": len(grid),
        "width": width,
        "components": components,
        "blue": blue,
        "blue_singletons": [component for component in blue if component["size"] == 1],
        "blue_multi": [component for component in blue if component["size"] > 1],
        "distractors": distractors,
        "errors": errors,
    }


def observe_overrides(grid) -> dict[str, int]:
    info = _analyze(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "singleton_count": len(info["blue_singletons"]),
        "large_size": max(component["size"] for component in info["blue_multi"]),
        "distractor_count": len(info["distractors"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info.get("errors", []))
    if "height" not in info:
        return errors
    if errors:
        return errors
    if not 8 <= info["height"] <= 10:
        errors.append(f"grid height {info['height']} outside 8..10")
    if not 8 <= info["width"] <= 11:
        errors.append(f"grid width {info['width']} outside 8..11")
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected at least one background cell")
    if not info["blue_singletons"]:
        errors.append("expected at least one singleton blue component")
    if not info["blue_multi"]:
        errors.append("expected at least one multi-cell blue component")
    if any(component["size"] != 1 for component in info["distractors"]):
        errors.append("green distractors must be singleton components")

    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    info = _analyze(grid)
    if info["distractors"]:
        reasons.append("canonical rows contain only blue foreground objects")
    if not 2 <= len(info["blue_singletons"]) <= 4:
        reasons.append("canonical-like singleton count is within 2..4")
    if not 1 <= len(info["blue_multi"]) <= 2:
        reasons.append("canonical multi-component count is 1 or 2")
    if any(not 2 <= component["size"] <= 4 for component in info["blue_multi"]):
        reasons.append("canonical multi-component sizes are within 2..4")
    return reasons


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid singleton-blue scene: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for component in _components(grid, color=1):
        if component["size"] == 1:
            r, c = component["cells"][0]
            out[r][c] = 2
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_all_blue_red(grid):
    return [[2 if value == 1 else value for value in row] for row in grid]


def _rival_size_at_most_two(grid):
    out = [list(row) for row in grid]
    for component in _components(grid, color=1):
        if component["size"] <= 2:
            for r, c in component["cells"]:
                out[r][c] = 2
    return out


def _rival_all_singletons_any_color(grid):
    out = [list(row) for row in grid]
    for component in _components(grid):
        if component["size"] == 1:
            r, c = component["cells"][0]
            out[r][c] = 2
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _rival_identity,
    "all_blue_red": _rival_all_blue_red,
    "blue_size_at_most_two": _rival_size_at_most_two,
    "all_singletons_any_color": _rival_all_singletons_any_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_singleton(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and bool(info["blue_singletons"])


def _witness_multi(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and bool(info["blue_multi"])


def _witness_size_two(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and any(c["size"] == 2 for c in info["blue_multi"])


def _witness_nonblue_singleton(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and bool(info["distractors"])


SEMANTIC_WITNESSES = {
    "singleton_recolor_branch": _witness_singleton,
    "larger_component_preserve_branch": _witness_multi,
    "size_two_boundary_preserved": _witness_size_two,
    "nonblue_singleton_preserved": _witness_nonblue_singleton,
}
WITNESS_RIVALS = {
    "singleton_recolor_branch": ["identity"],
    "larger_component_preserve_branch": ["all_blue_red"],
    "size_two_boundary_preserved": ["blue_size_at_most_two"],
    "nonblue_singleton_preserved": ["all_singletons_any_color"],
}

SCHEDULE_PROFILES = ("distractor", "plain_after", "plain_before")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    has_nonblue_witness = False
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        truth = rule_mirror(grid)
        if pair.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with the selected rule")
        has_nonblue_witness |= _witness_nonblue_singleton(grid)
    if not has_nonblue_witness:
        reasons.append("demonstrations omit the nonblue singleton distractor witness")

    query_grid = query.get("input")
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query_grid)
    if query.get("output") is not None and query.get("output") != query_truth:
        reasons.append("query output disagrees with the selected rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query_grid) != query_truth:
                reasons.append(
                    f"competing rule '{name}' fits every demo but predicts a different query"
                )
    return reasons
