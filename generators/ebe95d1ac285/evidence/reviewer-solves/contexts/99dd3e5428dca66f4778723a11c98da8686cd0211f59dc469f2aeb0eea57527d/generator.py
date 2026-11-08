"""Constructive sampler for anchor border-touch + symmetry selection.

The color-2 object is the anchor.  Every other monochrome 4-connected
object is selected exactly when it has BOTH the anchor's border-touch status
and its local bounding-box reflection-symmetry class:

    0 = neither row nor column symmetric
    1 = row symmetric only
    2 = column symmetric only
    3 = row and column symmetric

Selected non-anchor objects are recolored to 8 by the unchanged canonical
rule.  This module produces inputs only; the Racket rule remains label
authority.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ebe95d1ac285"
TASK_ID = GENERATOR_ID
RULE_HASH = "5aebf983dc54"
VERSION = "3.0.0"
SUMMARY = (
    "A unique color-2 anchor supplies a (border-touch, symmetry-class) key. "
    "Recolor every other object to 8 iff both parts of its key match the "
    "anchor.  Every generated lesson contains true matches plus touch-only "
    "and symmetry-only counterexamples."
)

INVARIANTS = [
    "exactly one 4-connected color-2 anchor and no color 8 in the input",
    "at least one non-anchor object matches both anchor attributes",
    "at least one same-touch/different-symmetry and one same-symmetry/opposite-touch distractor",
    "all objects have distinct nonzero colors, so object identity remains unambiguous even at contact",
]

AXES = {
    "grid_h": {"type": "int", "default": "12..24, difficulty weighted", "valid": "12..24"},
    "grid_w": {"type": "int", "default": "16..24, difficulty weighted", "valid": "16..24"},
    "anchor_sym": {"type": "int", "default": "scheduled across 0..3", "valid": "0|1|2|3"},
    "anchor_touch": {"type": "bool", "default": "scheduled false|true", "valid": "false|true"},
    "match_count": {"type": "int", "default": "1..2", "valid": "1|2"},
    "same_touch_distractors": {"type": "int", "default": "1..2", "valid": "1|2"},
    "same_sym_distractors": {"type": "int", "default": "1..2", "valid": "1|2"},
    "neutral_distractors": {"type": "int", "default": "0..1", "valid": "0|1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NON_ANCHOR_COLORS = (1, 3, 4, 5, 6, 7, 9)
_INT_DOMAINS = {
    "grid_h": tuple(range(12, 25)),
    "grid_w": tuple(range(16, 25)),
    "anchor_sym": (0, 1, 2, 3),
    "match_count": (1, 2),
    "same_touch_distractors": (1, 2),
    "same_sym_distractors": (1, 2),
    "neutral_distractors": (0, 1),
}


def _normalise(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _symmetry_class(cells: Iterable[tuple[int, int]]) -> int:
    shape = frozenset(_normalise(cells))
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    row_symmetric = all((height - 1 - row, col) in shape for row, col in shape)
    col_symmetric = all((row, width - 1 - col) in shape for row, col in shape)
    return 3 if row_symmetric and col_symmetric else 1 if row_symmetric else 2 if col_symmetric else 0


@lru_cache(maxsize=1)
def _shape_catalogue() -> tuple[tuple[tuple[tuple[int, int], ...], ...], ...]:
    """Enumerate small fixed polyominoes, sorted for hash-seed independence."""
    generation: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    by_class: dict[int, set[tuple[tuple[int, int], ...]]] = {index: set() for index in range(4)}
    for size in range(2, 7):
        next_generation: set[tuple[tuple[int, int], ...]] = set()
        for shape in sorted(generation):
            occupied = set(shape)
            for row, col in shape:
                for row_delta, col_delta in _CARDINAL:
                    candidate = (row + row_delta, col + col_delta)
                    if candidate not in occupied:
                        next_generation.add(_normalise((*shape, candidate)))
        generation = next_generation
        if size < 3:
            continue
        for shape in sorted(generation):
            height = max(row for row, _ in shape) + 1
            width = max(col for _, col in shape) + 1
            if height <= 3 and width <= 3:
                by_class[_symmetry_class(shape)].add(shape)
    catalogue = tuple(tuple(sorted(by_class[index], key=lambda shape: (len(shape), shape))) for index in range(4))
    if any(not shapes for shapes in catalogue):  # import-time invariant, not a random fallback
        raise RuntimeError("polyomino catalogue omitted a symmetry class")
    return catalogue



# One canonical-scale connected shape per symmetry class.  A sparse scheduled
# anchor uses these so the sampler reaches the official demonstrations' object
# scale without forcing every crowded boundary-matrix case to use large pieces.
_LARGE_SHAPES = (
    _normalise({
        (0, 2), (0, 3),
        (1, 0), (1, 1), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 2),
        (3, 1), (3, 2), (3, 3),
    }),
    _normalise(
        {(0, col) for col in range(5)}
        | {(2, col) for col in range(5)}
        | {(1, col) for col in (0, 1)}
    ),
    _normalise(
        {(col, row) for row, col in (
            {(0, col) for col in range(5)}
            | {(2, col) for col in range(5)}
            | {(1, col) for col in (0, 1)}
        )}
    ),
    _normalise({(row, col) for row in range(3) for col in range(4)}),
)

def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "anchor_touch":
            if type(value) is not bool:
                raise TypeError("anchor_touch must be a bool")
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float, or string)")
        if value not in _INT_DOMAINS[name]:
            domain = _INT_DOMAINS[name]
            raise ValueError(f"{name}={value!r} outside {domain[0]}..{domain[-1]}")


def _weighted_values(name: str, difficulty: str | None) -> tuple[int, ...]:
    domain = _INT_DOMAINS[name]
    if name == "grid_h":
        favoured = {
            "easy": tuple(range(12, 17)),
            "medium": tuple(range(15, 21)),
            "hard": tuple(range(19, 25)),
            None: tuple(range(12, 25)),
        }[difficulty]
    elif name == "grid_w":
        favoured = {
            "easy": tuple(range(16, 19)),
            "medium": tuple(range(18, 22)),
            "hard": tuple(range(21, 25)),
            None: tuple(range(16, 25)),
        }[difficulty]
    elif name in {"match_count", "same_touch_distractors", "same_sym_distractors"}:
        favoured = (1,) if difficulty == "easy" else (2,) if difficulty == "hard" else domain
    elif name == "neutral_distractors":
        favoured = (0,) if difficulty == "easy" else (1,) if difficulty == "hard" else domain
    else:
        favoured = domain
    # Keep the complete documented domain in draw provenance while weighting the band.
    return tuple(domain) + tuple(favoured) * 5


def _draw_axis(ctx, name: str, *, forced=None, difficulty=None):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        options = (False, True) if name == "anchor_touch" else _INT_DOMAINS[name]
    elif forced is not None:
        options = (forced,)
    elif name == "anchor_touch":
        options = (False, True)
    else:
        options = _weighted_values(name, difficulty)
    return ctx.draw_choice(name, options)


def _scheduled_axes(ctx, sample_index: int, difficulty: str | None) -> dict[str, int | bool]:
    """Draw every exact axis; two sparse slots guarantee canonical profiles."""
    signature = sample_index % 8
    forced_profile: dict[str, int] = {}
    if signature == 0:
        forced_profile = {
            "grid_h": 12,
            "grid_w": 16,
            "match_count": 1,
            "same_touch_distractors": 1,
            "same_sym_distractors": 1,
            "neutral_distractors": 0,
        }
    elif signature in (1, 2):
        forced_profile = {
            "grid_h": 12,
            "grid_w": 17,
            "match_count": 2,
            "same_touch_distractors": 1,
            "same_sym_distractors": 1,
            "neutral_distractors": 0,
        }
    values: dict[str, int | bool] = {}
    values["grid_h"] = _draw_axis(ctx, "grid_h", forced=forced_profile.get("grid_h"), difficulty=difficulty)
    values["grid_w"] = _draw_axis(ctx, "grid_w", forced=forced_profile.get("grid_w"), difficulty=difficulty)
    values["anchor_sym"] = _draw_axis(ctx, "anchor_sym", forced=(signature // 2) % 4, difficulty=difficulty)
    values["anchor_touch"] = _draw_axis(ctx, "anchor_touch", forced=bool(signature % 2), difficulty=difficulty)
    for name in ("match_count", "same_touch_distractors", "same_sym_distractors", "neutral_distractors"):
        values[name] = _draw_axis(ctx, name, forced=forced_profile.get(name), difficulty=difficulty)
    return values


def _different_symmetry(anchor_sym: int, ordinal: int) -> int:
    alternatives = tuple(value for value in range(4) if value != anchor_sym)
    return alternatives[ordinal % len(alternatives)]


def _object_specs(values: dict[str, int | bool], colors: tuple[int, ...]):
    anchor_sym = int(values["anchor_sym"])
    anchor_touch = bool(values["anchor_touch"])
    specs: list[dict[str, int | bool | str]] = [
        {"role": "anchor", "sym": anchor_sym, "touch": anchor_touch, "color": 2}
    ]
    color_index = 0
    for ordinal in range(int(values["match_count"])):
        specs.append({"role": "match", "sym": anchor_sym, "touch": anchor_touch, "color": colors[color_index]})
        color_index += 1
    for ordinal in range(int(values["same_touch_distractors"])):
        specs.append({
            "role": "same_touch", "sym": _different_symmetry(anchor_sym, ordinal),
            "touch": anchor_touch, "color": colors[color_index],
        })
        color_index += 1
    for ordinal in range(int(values["same_sym_distractors"])):
        specs.append({
            "role": "same_sym", "sym": anchor_sym, "touch": not anchor_touch,
            "color": colors[color_index],
        })
        color_index += 1
    for ordinal in range(int(values["neutral_distractors"])):
        specs.append({
            "role": "neutral", "sym": _different_symmetry(anchor_sym, ordinal + 1),
            "touch": not anchor_touch, "color": colors[color_index],
        })
        color_index += 1
    return specs


def _translated(shape, top: int, left: int) -> frozenset[tuple[int, int]]:
    return frozenset((top + row, left + col) for row, col in shape)


@lru_cache(maxsize=4096)
def _candidate_placements(shape, height: int, width: int, touch: bool):
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    placements = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            cells = _translated(shape, top, left)
            actual_touch = any(
                row in (0, height - 1) or col in (0, width - 1)
                for row, col in cells
            )
            if actual_touch == touch:
                placements.append(cells)
    return tuple(placements)


def _construct_layout(ctx, height: int, width: int, specs):
    """Greedily place small objects; distinct colors make contact lawful.

    Every candidate already has the requested border status.  With at most
    eight objects of at most six cells on the minimum 12x16 canvas, disjoint
    construction has ample capacity; bounded retries vary shapes and order but
    never return a shortened or invalid scene.
    """
    catalogue = _shape_catalogue()
    shape_rng = ctx.draw_rng("object_shapes")
    layout_rng = ctx.draw_rng("object_positions")
    constrained_order = tuple(
        sorted(range(len(specs)), key=lambda index: (not bool(specs[index]["touch"]), index))
    )
    for _attempt in range(32):
        occupied: set[tuple[int, int]] = set()
        placements: list[frozenset[tuple[int, int]] | None] = [None] * len(specs)
        success = True
        for index in constrained_order:
            spec = specs[index]
            shapes = catalogue[int(spec["sym"])]
            use_canonical_scale = index == 0 and ctx.sample_index % 7 == 2
            shape = _LARGE_SHAPES[int(spec["sym"])] if use_canonical_scale else shape_rng.choice(shapes)
            candidates = list(_candidate_placements(shape, height, width, bool(spec["touch"])))
            layout_rng.shuffle(candidates)
            chosen = next((cells for cells in candidates if occupied.isdisjoint(cells)), None)
            if chosen is None:
                success = False
                break
            placements[index] = chosen
            occupied.update(chosen)
        if success:
            return tuple(placements)
    raise RuntimeError(
        f"constructive placement failed for {height}x{width} with {len(specs)} objects"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    values = _scheduled_axes(ctx, sample_index, difficulty)
    object_count = (
        int(values["match_count"])
        + int(values["same_touch_distractors"])
        + int(values["same_sym_distractors"])
        + int(values["neutral_distractors"])
    )
    color_rng = ctx.draw_rng("object_colors")
    colors = tuple(color_rng.sample(list(_NON_ANCHOR_COLORS), object_count))
    specs = _object_specs(values, colors)
    placements = _construct_layout(ctx, int(values["grid_h"]), int(values["grid_w"]), specs)
    grid = full_grid(int(values["grid_h"]), int(values["grid_w"]), 0)
    for spec, cells in zip(specs, placements):
        if cells is None:  # guarded by _construct_layout, retained as a loud invariant
            raise RuntimeError("missing constructive placement")
        for row, col in cells:
            grid[row][col] = int(spec["color"])
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for row_delta, col_delta in _CARDINAL:
                    neighbor = (current[0] + row_delta, current[1] + col_delta)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append({"color": color, "cells": frozenset(cells)})
    return sorted(result, key=lambda obj: min(obj["cells"]))


def _touches_border(cells, height: int, width: int) -> bool:
    return any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells)


def _analysis(grid):
    height, width = len(grid), len(grid[0])
    regions = _components(grid)
    anchors = [obj for obj in regions if obj["color"] == 2]
    if len(anchors) != 1:
        raise ValueError(f"expected one color-2 anchor object, found {len(anchors)}")
    anchor = anchors[0]
    anchor_touch = _touches_border(anchor["cells"], height, width)
    anchor_sym = _symmetry_class(anchor["cells"])
    groups = {"match": [], "same_touch": [], "same_sym": [], "neutral": []}
    decorated = []
    for obj in regions:
        touch = _touches_border(obj["cells"], height, width)
        sym = _symmetry_class(obj["cells"])
        item = {**obj, "touch": touch, "sym": sym}
        decorated.append(item)
        if obj["color"] == 2:
            continue
        if touch == anchor_touch and sym == anchor_sym:
            groups["match"].append(item)
        elif touch == anchor_touch:
            groups["same_touch"].append(item)
        elif sym == anchor_sym:
            groups["same_sym"].append(item)
        else:
            groups["neutral"].append(item)
    return {
        "height": height,
        "width": width,
        "regions": decorated,
        "anchor": anchor,
        "anchor_touch": anchor_touch,
        "anchor_sym": anchor_sym,
        **groups,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return diagnostics for malformed or semantically uninformative inputs."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"]
    errors = []
    height = len(grid)
    if not (12 <= height <= 24 and 16 <= width <= 24):
        errors.append(f"grid dimensions {height}x{width} outside 12..24 by 16..24")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return errors + ["cells must be non-Boolean integer ARC colors 0..9"]
    if any(value == 8 for row in grid for value in row):
        errors.append("input must not contain output color 8")
    try:
        info = _analysis(grid)
    except ValueError as exc:
        return errors + [str(exc)]
    regions = info["regions"]
    colors = [obj["color"] for obj in regions]
    if len(colors) != len(set(colors)):
        errors.append("each nonzero color must form exactly one object")
    if not 4 <= len(regions) <= 8:
        errors.append(f"expected 4..8 objects, found {len(regions)}")
    for obj in regions:
        if not 3 <= len(obj["cells"]) <= 12:
            errors.append(f"color {obj['color']} object has unsupported size {len(obj['cells'])}")
    if not info["match"]:
        errors.append("at least one non-anchor object must match both anchor attributes")
    if not (info["same_touch"] or info["same_sym"] or info["neutral"]):
        errors.append("at least one non-matching object is required")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    info = _analysis(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "anchor_sym": info["anchor_sym"],
        "anchor_touch": info["anchor_touch"],
        "match_count": len(info["match"]),
        "same_touch_distractors": len(info["same_touch"]),
        "same_sym_distractors": len(info["same_sym"]),
        "neutral_distractors": len(info["neutral"]),
    }


def _apply_selector(grid, selector: Callable[[bool, int, bool, int], bool]):
    info = _analysis(grid)
    output = deepcopy(grid)
    for obj in info["regions"]:
        if obj["color"] == 2:
            continue
        if selector(obj["touch"], obj["sym"], info["anchor_touch"], info["anchor_sym"]):
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def _touch_only(grid):
    return _apply_selector(grid, lambda touch, sym, anchor_touch, anchor_sym: touch == anchor_touch)


def _symmetry_only(grid):
    return _apply_selector(grid, lambda touch, sym, anchor_touch, anchor_sym: sym == anchor_sym)


def _has_same_touch_wrong_sym(grid):
    return bool(_analysis(grid)["same_touch"])


def _has_same_sym_wrong_touch(grid):
    return bool(_analysis(grid)["same_sym"])


SEMANTIC_WITNESSES = {
    "same_touch_wrong_sym": _has_same_touch_wrong_sym,
    "same_sym_wrong_touch": _has_same_sym_wrong_touch,
}
SEMANTIC_RIVALS = {
    "touch_only": _touch_only,
    "symmetry_only": _symmetry_only,
}
WITNESS_RIVALS = {
    "same_touch_wrong_sym": ["touch_only"],
    "same_sym_wrong_touch": ["symmetry_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
