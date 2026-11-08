"""Generator for 26f02d922ca0 — source shape or horizontal mirror.

The color-2 object is the source/key. Candidate objects use distinct colours
from 3, 4, 5, and 6 and are read in top-left order. The output is a one-row
indicator grid: 8 when a candidate's normalized cell mask equals the key or
its left/right mirror, otherwise 0.

The three canonical demonstrations all happen to place colours 3 and 4 first
and label them 8, while colours 5 and 6 are labelled 0. This implementation
therefore schedules explicit colour-role, reading-order, mirror-only, and
candidate-count conflicts rather than merely generating random variants that
might preserve those shortcuts by accident.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import permutations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "26f02d922ca0"
TASK_ID = "26f02d922ca0"
VERSION = "3.0.0"
RULE_HASH = "2ec8ce6b9b7f"

SUMMARY = (
    "A 0-background grid contains one color-2 source shape and 2-4 isolated "
    "candidate shapes in distinct colours from {3,4,5,6}. Candidates are read "
    "by top-left position and receive 8 exactly when their normalized mask is "
    "the source or its horizontal mirror, otherwise 0. A four-profile schedule "
    "anchors the canonical 9x16 six-colour scale while refuting fixed-colour, "
    "first-two, exact-only, and fixed-four-output shortcuts."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
EXPECTED_OUTPUT_CODOMAIN = 21

INVARIANTS = [
    "background is 0; foreground colours are limited to 2,3,4,5,6",
    "there is exactly one connected color-2 key and 2-4 single-component candidates",
    "ordinary lessons contain at least one source/mirror match and one non-match",
    "candidate order is top-left reading order, independent of candidate colour",
    "generated objects occupy separated 3x3 slots and never overlap",
]

# Only controls that are exact, independently meaningful, and observable from
# the returned grid are public axes. Shape size, candidate count, relation
# pattern, colour assignment, and placement remain sampled curriculum choices.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 9..18; profile 0 pins 9",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 12..24; profile 0 pins 16",
        "valid": "12..24",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_PROFILE_CANONICAL_COLOR = "canonical_color_conflict"
_PROFILE_ORDER = "nonprefix_order_conflict"
_PROFILE_MIRROR = "mirror_only_match"
_PROFILE_COUNT = "variable_candidate_count"
SCHEDULE_PROFILES = (
    _PROFILE_CANONICAL_COLOR,
    _PROFILE_ORDER,
    _PROFILE_MIRROR,
    _PROFILE_COUNT,
)

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED = {0, 2, 3, 4, 5, 6}
_CANDIDATE_COLOURS = (3, 4, 5, 6)

Coord = tuple[int, int]
Shape = tuple[Coord, ...]
Grid = list[list[int]]


def _normalize(cells: Iterable[Coord]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return tuple(sorted((row - row0, col - col0) for row, col in points))


def _shape_dims(cells: Iterable[Coord]) -> tuple[int, int]:
    shape = _normalize(cells)
    if not shape:
        return (0, 0)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _mirror(cells: Iterable[Coord]) -> Shape:
    shape = _normalize(cells)
    if not shape:
        return ()
    _, width = _shape_dims(shape)
    return _normalize((row, width - 1 - col) for row, col in shape)


def _connected4(cells: Iterable[Coord]) -> bool:
    points = set(cells)
    if not points:
        return False
    start = min(points)
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for drow, dcol in _DIR4:
            neighbor = (row + drow, col + dcol)
            if neighbor in points and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(points)


def _build_shape_library() -> dict[int, tuple[Shape, ...]]:
    """All normalized connected subsets of a 3x3 box, grouped by area.

    Enumerating 2**9 masks at import time is cheap, deterministic, and avoids
    hash-order-sensitive random walks or placement retries. Reflections remain
    separate shapes because the task explicitly distinguishes exact from mirror.
    """
    by_size: dict[int, set[Shape]] = {size: set() for size in range(3, 8)}
    cells = tuple((row, col) for row in range(3) for col in range(3))
    for mask in range(1, 1 << len(cells)):
        size = mask.bit_count()
        if size not in by_size:
            continue
        chosen = tuple(cells[index] for index in range(9) if mask & (1 << index))
        if _connected4(chosen):
            by_size[size].add(_normalize(chosen))
    result = {size: tuple(sorted(shapes)) for size, shapes in by_size.items()}
    if any(not shapes for shapes in result.values()):
        raise AssertionError("connected 3x3 shape library is incomplete")
    return result


_SHAPES_BY_SIZE = _build_shape_library()
_ASYMMETRIC_BY_SIZE = {
    size: tuple(shape for shape in shapes if _mirror(shape) != shape)
    for size, shapes in _SHAPES_BY_SIZE.items()
}
if any(not shapes for shapes in _ASYMMETRIC_BY_SIZE.values()):
    raise AssertionError("asymmetric shape library is incomplete")


def _component_record(colour: int, cells: Iterable[Coord]) -> dict[str, Any]:
    points = tuple(sorted(cells))
    norm = _normalize(points)
    height, width = _shape_dims(norm)
    return {
        "colour": colour,
        "color": colour,
        "cells": points,
        "norm": norm,
        "top": min(row for row, _ in points),
        "left": min(col for _, col in points),
        "height": height,
        "width": width,
        "area": len(points),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    """Parse the authority grammar without imposing curriculum marginals."""
    result: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "palette": set(),
        "key": None,
        "candidates": [],
    }
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("empty or non-grid input")
        return result
    height, width = len(grid), len(grid[0])
    result["height"], result["width"] = height, width
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("ragged or non-list row")
        return result
    nonints = sorted({repr(value) for row in grid for value in row if not isinstance(value, int)})
    if nonints:
        errors.append(f"non-integer cell values {nonints[:4]}")
        return result
    palette = {value for row in grid for value in row}
    result["palette"] = palette
    bad = sorted(palette - _ALLOWED)
    if bad:
        errors.append(f"unexpected colours {bad}")

    seen: set[Coord] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            colour = grid[start_row][start_col]
            start = (start_row, start_col)
            if colour == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: list[Coord] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    neighbor = (row + drow, col + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == colour
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(_component_record(colour, cells))

    by_colour: dict[int, list[dict[str, Any]]] = {}
    for component in components:
        by_colour.setdefault(component["colour"], []).append(component)

    keys = by_colour.get(2, [])
    if len(keys) != 1:
        errors.append(f"expected exactly one color-2 key component, found {len(keys)}")
    else:
        result["key"] = keys[0]

    candidates: list[dict[str, Any]] = []
    for colour in _CANDIDATE_COLOURS:
        same_colour = by_colour.get(colour, [])
        if len(same_colour) > 1:
            errors.append(
                f"candidate colour {colour} is split into {len(same_colour)} components"
            )
        candidates.extend(same_colour)
    candidates.sort(key=lambda component: (component["top"], component["left"]))
    result["candidates"] = candidates
    if not (2 <= len(candidates) <= 4):
        errors.append(f"expected 2..4 candidate components, found {len(candidates)}")
    return result


def rule_mirror(grid: Grid) -> Grid:
    """Python mirror of the selected Racket rule, used only for diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    key = analysis["key"]["norm"]
    accepted = {key, _mirror(key)}
    return [[8 if candidate["norm"] in accepted else 0 for candidate in analysis["candidates"]]]


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate a useful ordinary lesson in the task's executable grammar."""
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    flags = rule_mirror(grid)[0]
    if 8 not in flags:
        errors.append("no candidate matches the key or its horizontal mirror")
    if 0 not in flags:
        errors.append("all candidates match; missing a 0-flag distractor")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Empirical canonical manifold, narrower than the executable grammar."""
    reasons = self_check(grid)
    if reasons:
        return [f"teaching grammar: {reason}" for reason in reasons]
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) != (9, 16):
        reasons.append("canonical canvas is exactly 9x16")
    if analysis["palette"] != {0, 2, 3, 4, 5, 6}:
        reasons.append("canonical palette is exactly {0,2,3,4,5,6}")
    if len(analysis["candidates"]) != 4:
        reasons.append("canonical examples contain four candidates")
    key = analysis["key"]
    if key and key["area"] not in {4, 5}:
        reasons.append("canonical key area is 4 or 5")
    for candidate in analysis["candidates"]:
        if candidate["area"] not in {4, 5}:
            reasons.append("canonical candidate areas are 4 or 5")
            break
    for component in ([key] if key else []) + analysis["candidates"]:
        if component["height"] > 3 or component["width"] > 3:
            reasons.append("canonical object bounding boxes fit inside 3x3")
            break
    if rule_mirror(grid)[0].count(8) != 2:
        reasons.append("canonical examples contain exactly two positive candidates")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive examples cover all shortcut-killing profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_or_pin_int(ctx, label: str, lo: int, hi: int, pinned: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if pinned is not None:
        return ctx.draw_int(label, pinned, pinned)
    return ctx.draw_int_diff(label, lo, hi)


def _choose_key_shape(rng, sizes: tuple[int, ...]) -> Shape:
    size = rng.choice(list(sizes))
    return rng.choice(list(_ASYMMETRIC_BY_SIZE[size]))


def _different_shape(
    rng,
    key: Shape,
    allowed_sizes: tuple[int, ...],
) -> Shape:
    mirror = _mirror(key)
    options = [
        shape
        for size in allowed_sizes
        for shape in _SHAPES_BY_SIZE[size]
        if shape not in {key, mirror}
    ]
    if not options:
        raise AssertionError("no non-matching candidate shape available")
    return rng.choice(options)


def _key_sizes(profile: str, difficulty: Any) -> tuple[int, ...]:
    if profile == _PROFILE_CANONICAL_COLOR:
        return (4, 5)
    if difficulty == "easy":
        return (3, 4)
    if difficulty == "hard":
        return (5, 6, 7)
    return (4, 5, 6)


def _mixed_bit_patterns(length: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        bits
        for mask in range(1, (1 << length) - 1)
        for bits in [tuple((mask >> index) & 1 for index in range(length))]
    )


def _roles_from_bits(bits: tuple[int, ...], rng, *, require_mirror: bool) -> tuple[str, ...]:
    match_indexes = [index for index, bit in enumerate(bits) if bit]
    mirror_index = rng.choice(match_indexes) if require_mirror else None
    roles: list[str] = []
    for index, bit in enumerate(bits):
        if not bit:
            roles.append("different")
        elif index == mirror_index:
            roles.append("mirror")
        else:
            roles.append(rng.choice(["key", "mirror"]))
    return tuple(roles)


def _profile_roles(profile: str, rng) -> tuple[tuple[int, ...], tuple[str, ...]]:
    """Return candidate colours and shape roles in top-left reading order."""
    if profile == _PROFILE_CANONICAL_COLOR:
        # Preserve the canonical 2-positive marginal but invert both salient
        # canonical shortcuts. There are many lawful choices, so this anchor
        # does not collapse every fourth output to one fixed vector.
        candidates = []
        for bits in _mixed_bit_patterns(4):
            if sum(bits) != 2 or bits == (1, 1, 0, 0):
                continue
            for colours in permutations(_CANDIDATE_COLOURS):
                colour_bits = tuple(int(colour in {3, 4}) for colour in colours)
                if colour_bits != bits:
                    candidates.append((tuple(colours), bits))
        colours, bits = rng.choice(candidates)
        return colours, _roles_from_bits(bits, rng, require_mirror=True)
    if profile == _PROFILE_ORDER:
        colours = tuple(rng.sample(list(_CANDIDATE_COLOURS), 4))
        patterns = tuple(
            bits for bits in _mixed_bit_patterns(4) if bits != (1, 1, 0, 0)
        )
        bits = rng.choice(patterns)
        return colours, _roles_from_bits(bits, rng, require_mirror=False)
    if profile == _PROFILE_MIRROR:
        colours = tuple(rng.sample(list(_CANDIDATE_COLOURS), 3))
        bits = rng.choice(_mixed_bit_patterns(3))
        return colours, _roles_from_bits(bits, rng, require_mirror=True)
    count = rng.choice((2, 3))
    colours = tuple(rng.sample(list(_CANDIDATE_COLOURS), count))
    bits = rng.choice(_mixed_bit_patterns(count))
    return colours, _roles_from_bits(bits, rng, require_mirror=True)


def _slot_grid(height: int, width: int) -> list[Coord]:
    """3x3 slots separated by a full blank row and column."""
    rows = list(range(0, height - 2, 4))
    cols = list(range(0, width - 2, 4))
    return [(row, col) for row in rows for col in cols]


def _choose_slots(rng, height: int, width: int, count: int) -> tuple[Coord, list[Coord]]:
    slots = _slot_grid(height, width)
    if len(slots) < count:
        raise ValueError(
            f"grid {height}x{width} cannot hold {count} separated 3x3 slots"
        )
    chosen = rng.sample(slots, count)
    key_index = rng.randrange(len(chosen))
    key_slot = chosen[key_index]
    candidate_slots = sorted(
        chosen[:key_index] + chosen[key_index + 1 :],
        key=lambda position: (position[0], position[1]),
    )
    return key_slot, candidate_slots


def _candidate_shapes(
    profile: str,
    rng,
    key: Shape,
    roles: tuple[str, ...],
) -> list[Shape]:
    if profile == _PROFILE_CANONICAL_COLOR:
        diff_sizes = (4, 5)
    else:
        key_area = len(key)
        diff_sizes = tuple(
            size for size in range(max(3, key_area - 1), min(7, key_area + 1) + 1)
        )
    shapes: list[Shape] = []
    for role in roles:
        if role == "key":
            shapes.append(key)
        elif role == "mirror":
            shapes.append(_mirror(key))
        else:
            shapes.append(_different_shape(rng, key, diff_sizes))
    return shapes


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    canonical_pin = profile == _PROFILE_CANONICAL_COLOR
    height = _draw_or_pin_int(ctx, "grid_h", 9, 18, 9 if canonical_pin else None)
    width = _draw_or_pin_int(ctx, "grid_w", 12, 24, 16 if canonical_pin else None)

    shape_rng = ctx.draw_rng(f"{profile}:shapes")
    role_rng = ctx.draw_rng(f"{profile}:roles")
    layout_rng = ctx.draw_rng(f"{profile}:layout")

    key = _choose_key_shape(shape_rng, _key_sizes(profile, difficulty))
    colours, roles = _profile_roles(profile, role_rng)
    shapes = _candidate_shapes(profile, shape_rng, key, roles)
    key_slot, candidate_slots = _choose_slots(
        layout_rng, height, width, len(colours) + 1
    )

    grid = full_grid(height, width, 0)
    paint_at(grid, key_slot[0], key_slot[1], key, 2)
    for (top, left), shape, colour in zip(candidate_slots, shapes, colours):
        paint_at(grid, top, left, shape, colour)

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructor violated scene contract: " + "; ".join(errors))
    return grid


def _rival_colors_3_and_4(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [[8 if candidate["colour"] in {3, 4} else 0 for candidate in analysis["candidates"]]]


def _rival_first_two(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [[8 if index < 2 else 0 for index, _ in enumerate(analysis["candidates"])]]


def _rival_fixed_canonical_vector(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [[8, 8, 0, 0]]


def _rival_exact_key_only(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    key = analysis["key"]["norm"]
    return [[8 if candidate["norm"] == key else 0 for candidate in analysis["candidates"]]]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "colors_3_and_4_are_matches": _rival_colors_3_and_4,
    "first_two_candidates_match": _rival_first_two,
    "fixed_canonical_vector": _rival_fixed_canonical_vector,
    "exact_key_only": _rival_exact_key_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "colors_3_and_4_are_matches": _rival_colors_3_and_4,
    "first_two_candidates_match": _rival_first_two,
    "fixed_canonical_vector": _rival_fixed_canonical_vector,
}


def _valid_analysis(grid: Grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _color_role_conflict(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and {candidate["colour"] for candidate in analysis["candidates"]}
        == set(_CANDIDATE_COLOURS)
        and _rival_colors_3_and_4(grid) != rule_mirror(grid)
    )


def _nonprefix_match_pattern(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _rival_first_two(grid) != rule_mirror(grid))


def _mirror_only_match(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    key = analysis["key"]["norm"]
    mirror = _mirror(key)
    return key != mirror and any(
        candidate["norm"] == mirror and candidate["norm"] != key
        for candidate in analysis["candidates"]
    )


def _variable_candidate_count(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["candidates"]) != 4)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "color_role_conflict": _color_role_conflict,
    "nonprefix_match_pattern": _nonprefix_match_pattern,
    "mirror_only_match": _mirror_only_match,
    "variable_candidate_count": _variable_candidate_count,
}
WITNESS_RIVALS = {
    "color_role_conflict": ["colors_3_and_4_are_matches"],
    "nonprefix_match_pattern": ["first_two_candidates_match"],
    "mirror_only_match": ["exact_key_only"],
    "variable_candidate_count": ["fixed_canonical_vector"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Finite-rival diagnostic for a four-example generated lesson."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    witness_hits = {name: False for name in SEMANTIC_WITNESSES}
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the source-or-mirror rule")
            continue
        valid_demos.append(demo)
        for name, predicate in SEMANTIC_WITNESSES.items():
            witness_hits[name] |= predicate(demo["input"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the source-or-mirror rule")
    if reasons:
        return reasons

    for name, hit in witness_hits.items():
        if not hit:
            reasons.append(f"demonstrations do not include witness {name}")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            if rival(query["input"]) != query_answer:
                reasons.append(f"{name} fits all demos but changes the query answer")
    return reasons
