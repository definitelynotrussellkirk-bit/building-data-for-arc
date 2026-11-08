"""Generator for ARC task f5aa3634 / 70c33a3391ac.

The input is a sparse zero-background scene of separated multicolor connected
components.  Exactly one complete colored component crop occurs twice; every
other complete crop occurs once.  The output is that duplicated crop.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "70c33a3391ac"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "4fc872f50360"

SUMMARY = (
    "Find all four-connected nonzero components, crop each component to its "
    "bounding box while preserving every color and internal zero, and compare "
    "the complete crops exactly. Exactly one crop occurs twice; output that "
    "duplicated colored crop. Geometry alone, palette alone, cell count, size, "
    "position, and modal color are insufficient."
)

INVARIANTS = [
    "background is zero and the grid is rectangular",
    "there are four through six separated multicolor connected components",
    "exactly one complete colored component crop occurs exactly twice",
    "every distractor complete crop occurs exactly once",
    "the duplicated crop contains at least two colors and five through ten cells",
    "normal draws mix exact canonical-profile scenes with generalized shortcut-rebutting scenes",
]

DUPLICATE_RANKS = ("smallest", "middle", "largest")
PALETTE_RELATIONS = ("private", "shared")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "canonical_prior": {
        "type": "bool",
        "default": "one third true on ordinary draws",
        "valid": "false|true",
    },
    "n_components": {
        "type": "int",
        "default": "band-weighted draw over 4..6",
        "valid": "4..6",
    },
    "duplicate_rank": {
        "type": "str",
        "default": "rng smallest|middle|largest",
        "valid": "|".join(DUPLICATE_RANKS),
    },
    "duplicate_palette_relation": {
        "type": "str",
        "default": "rng private|shared",
        "valid": "|".join(PALETTE_RELATIONS),
    },
}
_EXACT_AXES = tuple(AXES)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))

# The canonical-prior branch can only realize the four exact profiles below.
# These minimal declarations classify every multi-axis request that is
# intentionally rejected instead of letting an arbitrary ValueError pass under
# the override checker's legacy compatibility policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"canonical_prior": True, "duplicate_rank": "smallest"},
    {
        "canonical_prior": True,
        "duplicate_rank": "middle",
        "n_components": (4, 6),
    },
    {
        "canonical_prior": True,
        "duplicate_rank": "middle",
        "duplicate_palette_relation": "private",
    },
    {
        "canonical_prior": True,
        "n_components": 4,
        "duplicate_palette_relation": "private",
    },
    {
        "canonical_prior": True,
        "n_components": 6,
        "duplicate_palette_relation": "private",
    },
    {
        "canonical_prior": True,
        "n_components": 5,
        "duplicate_rank": "largest",
        "duplicate_palette_relation": "shared",
    },
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

# Every unique official input, represented as canvas size plus exact component
# placements and crops.  Values are abstract color labels: canonical draws
# apply a fresh injective ARC-color remapping, preserving all equality/linkage
# facts while preventing literal color memorization.
_CANONICAL_SCENES = (
    (
        15,
        13,
        (
            (1, 1, ((0, 1, 1), (2, 2, 8), (3, 2, 8), (3, 0, 0))),
            (4, 6, ((0, 1, 1), (1, 2, 0), (0, 2, 0))),
            (6, 2, ((0, 8, 0), (8, 8, 8), (5, 5, 5))),
            (10, 8, ((0, 0, 8), (0, 6, 8), (6, 6, 8), (0, 4, 4), (0, 4, 0))),
            (11, 2, ((0, 8, 0), (8, 8, 8), (5, 5, 5))),
        ),
    ),
    (
        10,
        13,
        (
            (0, 1, ((0, 5, 8, 8), (3, 5, 3, 8), (0, 3, 3, 0))),
            (2, 9, ((0, 7, 0), (7, 7, 2), (0, 2, 2))),
            (5, 2, ((3, 5, 2), (2, 2, 0), (3, 2, 0))),
            (6, 8, ((0, 5, 8, 8), (3, 5, 3, 8), (0, 3, 3, 0))),
        ),
    ),
    (
        15,
        15,
        (
            (0, 1, ((0, 2, 8), (0, 8, 2), (8, 8, 0))),
            (0, 9, ((0, 0, 5, 9), (7, 7, 5, 9), (0, 5, 7, 0))),
            (4, 6, ((0, 0, 6), (0, 6, 6), (3, 3, 3))),
            (9, 1, ((0, 4, 0), (3, 4, 3), (0, 4, 0))),
            (11, 10, ((0, 0, 5, 9), (7, 7, 5, 9), (0, 5, 7, 0))),
        ),
    ),
    (
        15,
        15,
        (
            (1, 10, ((0, 0, 8, 8), (8, 5, 5, 8))),
            (2, 3, ((5, 5, 5), (5, 9, 5), (0, 9, 0))),
            (5, 7, ((3, 8, 3), (3, 4, 3), (0, 4, 0), (0, 4, 0))),
            (8, 1, ((2, 2, 0), (7, 2, 0), (0, 7, 7), (0, 0, 7))),
            (9, 11, ((3, 8, 3), (3, 4, 3), (0, 4, 0), (0, 4, 0))),
            (11, 7, ((0, 2), (1, 2), (1, 1))),
        ),
    ),
)


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty"]
    width = len(grid[0])
    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30x30")
    result = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        result.append(converted)
    return (None, errors) if errors else (result, [])


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _CARDINAL:
                    neighbor = (row + delta_row, col + delta_col)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] != 0
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            top = min(row for row, _col in cells)
            bottom = max(row for row, _col in cells)
            left = min(col for _row, col in cells)
            right = max(col for _row, col in cells)
            crop = tuple(
                tuple(grid[row][left : right + 1])
                for row in range(top, bottom + 1)
            )
            result.append(
                {
                    "bbox": (top, left, bottom, right),
                    "cells": tuple(cells),
                    "cell_count": len(cells),
                    "crop": crop,
                    "colors": frozenset(
                        value for crop_row in crop for value in crop_row if value
                    ),
                    "mask": tuple(
                        tuple(int(value != 0) for value in crop_row)
                        for crop_row in crop
                    ),
                }
            )
    return result


def _equality_signature(grid):
    color_map = {}
    next_label = 1
    result = []
    for row in grid:
        normalized_row = []
        for value in row:
            if value == 0:
                normalized_row.append(0)
                continue
            if value not in color_map:
                color_map[value] = next_label
                next_label += 1
            normalized_row.append(color_map[value])
        result.append(tuple(normalized_row))
    return tuple(result)


def _scene_grid(scene, color_map=None):
    height, width, placements = scene
    grid = full_grid(height, width, 0)
    mapping = color_map or {}
    for top, left, crop in placements:
        for row_offset, crop_row in enumerate(crop):
            for col_offset, value in enumerate(crop_row):
                if value:
                    grid[top + row_offset][left + col_offset] = mapping.get(value, value)
    return grid


_CANONICAL_SIGNATURES = frozenset(
    _equality_signature(_scene_grid(scene)) for scene in _CANONICAL_SCENES
)


def _analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert coerced is not None
    components = _components(coerced)
    groups = Counter(component["crop"] for component in components)
    duplicate_keys = [crop for crop, count in groups.items() if count == 2]
    if len(duplicate_keys) != 1 or any(count not in (1, 2) for count in groups.values()):
        return {
            "errors": ["expected exactly one complete component crop with multiplicity two"],
            "components": components,
            "groups": groups,
        }
    duplicate_key = duplicate_keys[0]
    duplicate = next(
        component for component in components if component["crop"] == duplicate_key
    )
    distractors = [
        component for component in components if component["crop"] != duplicate_key
    ]
    duplicate_count = duplicate["cell_count"]
    distractor_counts = [component["cell_count"] for component in distractors]
    if (
        distractor_counts
        and all(count >= duplicate_count for count in distractor_counts)
        and any(count > duplicate_count for count in distractor_counts)
    ):
        duplicate_rank = "smallest"
    elif (
        distractor_counts
        and all(count <= duplicate_count for count in distractor_counts)
        and any(count < duplicate_count for count in distractor_counts)
    ):
        duplicate_rank = "largest"
    elif (
        any(count < duplicate_count for count in distractor_counts)
        and any(count > duplicate_count for count in distractor_counts)
    ):
        duplicate_rank = "middle"
    else:
        duplicate_rank = "flat"
    palette_relation = (
        "shared"
        if any(duplicate["colors"] & component["colors"] for component in distractors)
        else "private"
    )
    return {
        "errors": [],
        "grid": coerced,
        "components": components,
        "groups": groups,
        "duplicate": duplicate,
        "distractors": distractors,
        "canonical_prior": _equality_signature(coerced) in _CANONICAL_SIGNATURES,
        "n_components": len(components),
        "duplicate_rank": duplicate_rank,
        "duplicate_palette_relation": palette_relation,
    }


_CANONICAL_FACTS = tuple(_analysis(_scene_grid(scene)) for scene in _CANONICAL_SCENES)


def observe_overrides(grid):
    """Recover every declared exact semantic axis from a lawful returned grid."""
    info = _analysis(grid)
    if info.get("errors"):
        return {}
    return {axis: info[axis] for axis in _EXACT_AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, degenerate, and rule-hiding inputs."""
    info = _analysis(grid)
    if info.get("errors"):
        return list(info["errors"])
    components = info["components"]
    duplicate = info["duplicate"]
    errors: list[str] = []
    if not 4 <= len(components) <= 6:
        errors.append("expected four through six nonzero connected components")
    if any(count != 1 for crop, count in info["groups"].items() if crop != duplicate["crop"]):
        errors.append("every distractor crop must occur exactly once")
    if not 5 <= duplicate["cell_count"] <= 10:
        errors.append("duplicated crop must contain five through ten foreground cells")
    if not 2 <= len(duplicate["colors"]) <= 3:
        errors.append("duplicated crop must contain two or three colors")
    palette_count = len({value for row in info["grid"] for value in row if value})
    if not 5 <= palette_count <= 8:
        errors.append("ordinary scenes must use five through eight foreground colors")
    if info["duplicate_rank"] not in DUPLICATE_RANKS:
        errors.append("duplicated crop must be observably smallest, middle, or largest by cell count")
    if any(len(component["colors"]) < 2 for component in components):
        errors.append("every component must be multicolor to block monochrome shortcuts")
    if meta:
        requested = meta.get("overrides", meta) if isinstance(meta, dict) else {}
        if isinstance(requested, dict):
            observed = observe_overrides(info["grid"])
            for axis in _EXACT_AXES:
                if axis in requested and requested[axis] is not None:
                    if observed.get(axis) != requested[axis]:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as "
                            f"{observed.get(axis)!r}"
                        )
    return errors


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer (bool/float/string are invalid)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if "canonical_prior" in overrides and overrides["canonical_prior"] is not None:
        if type(overrides["canonical_prior"]) is not bool:
            raise ValueError("canonical_prior must be a literal boolean")
    if "n_components" in overrides and overrides["n_components"] is not None:
        value = overrides["n_components"]
        if type(value) is not int or not 4 <= value <= 6:
            raise ValueError("n_components must be a literal integer in 4..6")
    if "duplicate_rank" in overrides and overrides["duplicate_rank"] is not None:
        value = overrides["duplicate_rank"]
        if type(value) is not str or value not in DUPLICATE_RANKS:
            raise ValueError(
                "duplicate_rank must be one of " + ", ".join(DUPLICATE_RANKS)
            )
    if (
        "duplicate_palette_relation" in overrides
        and overrides["duplicate_palette_relation"] is not None
    ):
        value = overrides["duplicate_palette_relation"]
        if type(value) is not str or value not in PALETTE_RELATIONS:
            raise ValueError(
                "duplicate_palette_relation must be one of "
                + ", ".join(PALETTE_RELATIONS)
            )


def _canonical_candidates(overrides):
    candidates = []
    for index, facts in enumerate(_CANONICAL_FACTS):
        if overrides.get("n_components") is not None and overrides["n_components"] != facts["n_components"]:
            continue
        if overrides.get("duplicate_rank") is not None and overrides["duplicate_rank"] != facts["duplicate_rank"]:
            continue
        if (
            overrides.get("duplicate_palette_relation") is not None
            and overrides["duplicate_palette_relation"]
            != facts["duplicate_palette_relation"]
        ):
            continue
        candidates.append(index)
    return candidates


def _draw_canonical_prior(ctx, overrides, sample_index):
    if overrides.get("canonical_prior") is not None:
        return ctx.draw_choice("canonical_prior", (False, True))
    # A semantic override is always a valid request on its own.  When it cannot
    # be represented by one of the four exact canonical profiles, record the
    # canonical-prior axis as false instead of letting a random default branch
    # turn an otherwise valid override into a sporadic rejection.
    semantic_override = any(
        overrides.get(axis) is not None
        for axis in ("n_components", "duplicate_rank", "duplicate_palette_relation")
    )
    if semantic_override and not _canonical_candidates(overrides):
        return ctx.draw_choice("canonical_prior", (False,))
    # Sequential episodes use three demonstrations.  Pinning exactly one of
    # every three ordinary sample indices to the canonical prior guarantees
    # that every demo window also contains two generalized counterexamples.
    return ctx.draw_choice("canonical_prior", (sample_index % 3 == 0,))


def _draw_canonical(ctx, overrides):
    candidates = _canonical_candidates(overrides)
    if not candidates:
        raise ValueError("no canonical profile satisfies the requested semantic-axis combination")
    profile_index = ctx.draw_choice("canonical_profile", tuple(candidates))
    facts = _CANONICAL_FACTS[profile_index]
    ctx.draw_int("n_components", facts["n_components"], facts["n_components"])
    ctx.draw_choice("duplicate_rank", (facts["duplicate_rank"],))
    ctx.draw_choice(
        "duplicate_palette_relation",
        (facts["duplicate_palette_relation"],),
    )
    labels = sorted(
        {
            value
            for _top, _left, crop in _CANONICAL_SCENES[profile_index][2]
            for row in crop
            for value in row
            if value
        }
    )
    colors = ctx.draw_distinct_colors(
        "canonical_colors", n=len(labels), exclude={0}
    )
    color_map = dict(zip(labels, colors))
    return _scene_grid(_CANONICAL_SCENES[profile_index], color_map)


def _draw_general_axes(ctx, overrides, band, sample_index):
    if overrides.get("n_components") is not None:
        n_components = ctx.draw_int("n_components", 4, 6)
    elif sample_index % 3 == 2:
        # Four distractors: D4 transform, same-mask recolor, smaller, larger.
        n_components = ctx.draw_int("n_components", 6, 6)
    elif sample_index % 3 == 1:
        # Three distractors: D4 transform, same-mask recolor, rank witness.
        n_components = ctx.draw_int("n_components", 5, 6)
    elif band == "easy":
        n_components = ctx.draw_int("n_components", 4, 5)
    elif band == "hard":
        n_components = ctx.draw_int("n_components", 5, 6)
    else:
        n_components = ctx.draw_int("n_components", 4, 6)
    if overrides.get("duplicate_rank") is not None:
        duplicate_rank = ctx.draw_choice("duplicate_rank", DUPLICATE_RANKS)
    elif sample_index % 3 == 1:
        duplicate_rank = ctx.draw_choice("duplicate_rank", ("smallest", "largest"))
    elif sample_index % 3 == 2:
        duplicate_rank = ctx.draw_choice("duplicate_rank", ("middle",))
    else:
        duplicate_rank = ctx.draw_choice("duplicate_rank", DUPLICATE_RANKS)
    if overrides.get("duplicate_palette_relation") is not None:
        palette_relation = ctx.draw_choice(
            "duplicate_palette_relation", PALETTE_RELATIONS
        )
    elif sample_index % 3 in (1, 2):
        palette_relation = ctx.draw_choice(
            "duplicate_palette_relation", ("shared",)
        )
    else:
        palette_relation = ctx.draw_choice(
            "duplicate_palette_relation", PALETTE_RELATIONS
        )
    return n_components, duplicate_rank, palette_relation


def _normalize_cells(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _random_cells(rng, count, *, max_span=5):
    for _attempt in range(200):
        cells = {(0, 0)}
        while len(cells) < count:
            row, col = rng.choice(tuple(cells))
            delta_row, delta_col = rng.choice(_CARDINAL)
            cells.add((row + delta_row, col + delta_col))
        normalized = _normalize_cells(cells)
        height = max(row for row, _col in normalized) + 1
        width = max(col for _row, col in normalized) + 1
        if height <= max_span and width <= max_span:
            return normalized
    raise ValueError(f"could not create connected {count}-cell shape within {max_span}x{max_span}")


def _pattern_from_cells(cells, colors, rng):
    cells = tuple(sorted(cells))
    colors = tuple(colors)
    if len(colors) < 2 or len(colors) > len(cells):
        raise ValueError("pattern needs two or more colors and enough cells")
    assignments = list(colors)
    assignments.extend(rng.choice(colors) for _ in range(len(cells) - len(colors)))
    rng.shuffle(assignments)
    height = max(row for row, _col in cells) + 1
    width = max(col for _row, col in cells) + 1
    pattern = full_grid(height, width, 0)
    for (row, col), color in zip(cells, assignments):
        pattern[row][col] = color
    return tuple(tuple(row) for row in pattern)


def _pattern_cells(pattern):
    return tuple(
        (row, col)
        for row, pattern_row in enumerate(pattern)
        for col, value in enumerate(pattern_row)
        if value
    )


def _pattern_colors(pattern):
    return frozenset(value for row in pattern for value in row if value)


def _rotate_cw(pattern):
    """Rotate a rectangular crop clockwise without changing its cell values."""
    height = len(pattern)
    width = len(pattern[0])
    return tuple(
        tuple(pattern[height - 1 - row][col] for row in range(height))
        for col in range(width)
    )


def _mirror_lr(pattern):
    return tuple(tuple(reversed(row)) for row in pattern)


def _d4_variants(pattern):
    frozen = tuple(tuple(row) for row in pattern)
    variants = []
    for seed in (frozen, _mirror_lr(frozen)):
        current = seed
        for _turn in range(4):
            variants.append(current)
            current = _rotate_cw(current)
    return tuple(dict.fromkeys(variants))


def _d4_key(pattern):
    return min(_d4_variants(pattern))


def _nontrivial_d4_variant(pattern, rng):
    frozen = tuple(tuple(row) for row in pattern)
    options = tuple(variant for variant in _d4_variants(frozen) if variant != frozen)
    return rng.choice(options) if options else None


def _first_repeated_crop(grid, key_fn):
    groups = {}
    order = []
    for component in _components(grid):
        key = key_fn(component)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(component)
    for key in order:
        if len(groups[key]) >= 2:
            return [list(row) for row in groups[key][0]["crop"]]
    raise ValueError("no repeated component class for rival rule")


def _d4_equivalent_crop_first(grid):
    """Wrong shortcut: compare complete colored crops modulo the D4 group."""
    return _first_repeated_crop(grid, lambda component: _d4_key(component["crop"]))


def _shape_only_first(grid):
    """Wrong shortcut: compare only occupancy masks, ignoring component colors."""
    return _first_repeated_crop(grid, lambda component: component["mask"])


def _palette_only_first(grid):
    """Wrong shortcut: compare only the set of colors in each component."""
    return _first_repeated_crop(
        grid, lambda component: tuple(sorted(component["colors"]))
    )


def rule_mirror(grid):
    """Independent Python mirror used only by focused tests and lesson hooks."""
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid duplicated-crop input: " + "; ".join(info["errors"]))
    return [list(row) for row in info["duplicate"]["crop"]]


def strict_canonical_like(grid):
    """Accept exactly the four color-renaming-invariant canonical profiles."""
    info = _analysis(grid)
    if info.get("errors"):
        return list(info["errors"])
    if _equality_signature(info["grid"]) not in _CANONICAL_SIGNATURES:
        return ["input is outside the four exact canonical equality profiles"]
    return []


_SEMANTIC_RIVAL_FUNCTIONS = {
    "d4_equivalent_crop_first": _d4_equivalent_crop_first,
    "shape_only_first": _shape_only_first,
    "palette_only_first": _palette_only_first,
}


def _witness_for(rival):
    def witness(grid):
        info = _analysis(grid)
        if info.get("errors"):
            return False
        try:
            return rival(grid) != [list(row) for row in info["duplicate"]["crop"]]
        except (KeyError, TypeError, ValueError):
            return False

    return witness


SEMANTIC_RIVALS = dict(_SEMANTIC_RIVAL_FUNCTIONS)
LESSON_COMPETITORS = dict(_SEMANTIC_RIVAL_FUNCTIONS)
CANONICAL_SHORTCUTS = dict(_SEMANTIC_RIVAL_FUNCTIONS)
SEMANTIC_WITNESSES = {
    name: _witness_for(rival) for name, rival in _SEMANTIC_RIVAL_FUNCTIONS.items()
}
WITNESS_RIVALS = {name: [name] for name in _SEMANTIC_RIVAL_FUNCTIONS}


def lesson_identifiable(demos, query):
    """Require demonstrations to falsify each canonical-compatible shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain labeled input and output grids"]

    reasons = []
    validated_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain labeled input and output grids")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the teaching grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not the exact duplicated crop")
            continue
        validated_demos.append(pair)

    try:
        query_expected = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        query_expected = None
    if query_expected is not None and query["output"] != query_expected:
        reasons.append("query output is not the exact duplicated crop")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        fits_every_demo = True
        for pair in validated_demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    fits_every_demo = False
                    break
            except (KeyError, TypeError, ValueError):
                fits_every_demo = False
                break
        if fits_every_demo:
            detail = ""
            try:
                if rival(query["input"]) != query["output"]:
                    detail = " and changes the query answer"
            except (KeyError, TypeError, ValueError):
                pass
            reasons.append(f"demonstrations do not refute {name}{detail}")
    return reasons


def _make_unique_pattern(
    rng,
    cell_count,
    colors,
    forbidden,
    *,
    cells=None,
    forbidden_d4_keys=(),
):
    for _attempt in range(200):
        shape = tuple(cells) if cells is not None else _random_cells(rng, cell_count)
        pattern = _pattern_from_cells(shape, colors, rng)
        if pattern not in forbidden and _d4_key(pattern) not in forbidden_d4_keys:
            return pattern
    raise ValueError("could not make a unique colored component crop")


def _distractor_plan(rng, n_unique, rank, relation):
    """Return duplicate size plus semantically named distractor roles.

    A shared-palette scene gets a non-identical D4 copy whenever the requested
    component/rank combination leaves enough slots to preserve the advertised
    rank.  A same-mask recolor is added when another slot remains after the
    rank witnesses.  Default schedule positions 1 and 2 deliberately choose
    dimensions where both rivals fit.
    """
    if rank == "smallest":
        duplicate_count = rng.randint(5, 7)
        required_rank_slots = 1
    elif rank == "largest":
        duplicate_count = rng.randint(8, 10)
        required_rank_slots = 1
    else:
        duplicate_count = rng.randint(6, 9)
        required_rank_slots = 2

    plan = []
    can_include_d4 = relation == "shared" and (
        (rank != "middle" and n_unique >= 2)
        or (rank == "middle" and n_unique >= 3)
    )
    if can_include_d4:
        plan.append(("d4", duplicate_count))
    if n_unique - len(plan) > required_rank_slots:
        plan.append(("shape_recolor", duplicate_count))

    if rank == "smallest":
        while len(plan) < n_unique:
            plan.append(("larger", rng.randint(duplicate_count + 1, 10)))
    elif rank == "largest":
        while len(plan) < n_unique:
            plan.append(("smaller", rng.randint(5, duplicate_count - 1)))
    else:
        plan.extend(
            (
                ("smaller", rng.randint(5, duplicate_count - 1)),
                ("larger", rng.randint(duplicate_count + 1, 10)),
            )
        )
        while len(plan) < n_unique:
            plan.append(("other", rng.randint(5, 10)))
    return duplicate_count, plan[:n_unique]


def _distractor_palette(index, role, relation, duplicate_colors, extra_colors):
    if relation == "private":
        shift = index % len(extra_colors)
        rotated = extra_colors[shift:] + extra_colors[:shift]
        return tuple(rotated)
    # The D4 role keeps the duplicate's exact colors by transformation.  Every
    # authored non-D4 distractor uses at least one duplicate color plus all
    # extras, ensuring the declared shared relation and full five-color support.
    return tuple((duplicate_colors[0],) + extra_colors)


def _try_place_pattern(grid, pattern, rng, reserved, *, attempts=160):
    height = len(grid)
    width = len(grid[0])
    pattern_height = len(pattern)
    pattern_width = len(pattern[0])
    if pattern_height > height or pattern_width > width:
        return False
    for _attempt in range(attempts):
        top = rng.randint(0, height - pattern_height)
        left = rng.randint(0, width - pattern_width)
        if any(
            reserved[row][col]
            for row in range(top, top + pattern_height)
            for col in range(left, left + pattern_width)
        ):
            continue
        for row_offset, pattern_row in enumerate(pattern):
            for col_offset, value in enumerate(pattern_row):
                if value:
                    grid[top + row_offset][left + col_offset] = value
        # Reserve the complete crop rectangle plus a one-cell moat.  Merely
        # checking current nonzero cells allows a later disconnected component
        # to sit in an internal-zero corner of this crop, contaminating the
        # exact colored crop without joining the component.
        for row in range(max(0, top - 1), min(height, top + pattern_height + 1)):
            for col in range(max(0, left - 1), min(width, left + pattern_width + 1)):
                reserved[row][col] = True
        return True
    return False


def _draw_generalized(ctx, overrides, band, sample_index):
    n_components, duplicate_rank, relation = _draw_general_axes(
        ctx, overrides, band, sample_index
    )
    n_unique = n_components - 2
    structure_rng = ctx.draw_rng("general_structure")
    duplicate_count, distractor_plan = _distractor_plan(
        structure_rng, n_unique, duplicate_rank, relation
    )
    roles = {role for role, _count in distractor_plan}
    duplicate_color_count = 2 if structure_rng.random() < 0.45 else 3
    total_colors = 5
    all_colors = ctx.draw_distinct_colors("scene_colors", n=total_colors, exclude={0})
    duplicate_colors = tuple(all_colors[:duplicate_color_count])
    extra_colors = tuple(all_colors[duplicate_color_count:])
    if len(extra_colors) < 2:
        raise ValueError("generalized scene needs at least two non-duplicate palette colors")

    for scene_attempt in range(300):
        pattern_rng = ctx.draw_rng(f"general_patterns_{scene_attempt}")
        duplicate_cells = _random_cells(pattern_rng, duplicate_count)
        duplicate = _pattern_from_cells(
            duplicate_cells, duplicate_colors, pattern_rng
        )
        duplicate_d4_key = _d4_key(duplicate)
        d4_variant = (
            _nontrivial_d4_variant(duplicate, pattern_rng)
            if "d4" in roles
            else None
        )
        if "d4" in roles and d4_variant is None:
            # A fully D4-symmetric colored crop cannot make orientation
            # load-bearing, so resample the crop rather than documenting a cue
            # that changes no rival prediction.
            continue

        forbidden = {duplicate}
        distractors = []
        pattern_failed = False
        for index, (role, cell_count) in enumerate(distractor_plan):
            if role == "d4":
                pattern = d4_variant
                assert pattern is not None
                if pattern in forbidden:
                    pattern_failed = True
                    break
            else:
                palette = _distractor_palette(
                    index,
                    role,
                    relation,
                    duplicate_colors,
                    extra_colors,
                )
                cells = duplicate_cells if role == "shape_recolor" else None
                try:
                    pattern = _make_unique_pattern(
                        pattern_rng,
                        cell_count,
                        palette,
                        forbidden,
                        cells=cells,
                        forbidden_d4_keys={duplicate_d4_key},
                    )
                except ValueError:
                    pattern_failed = True
                    break
            forbidden.add(pattern)
            distractors.append(pattern)
        if pattern_failed:
            continue

        foreground = {
            value
            for pattern in (duplicate, *distractors)
            for row in pattern
            for value in row
            if value
        }
        if foreground != set(all_colors):
            continue

        full_teaching_scene = {"d4", "shape_recolor"} <= roles
        if full_teaching_scene:
            # Six bbox+moat reservations are intentionally roomier than the
            # canonical profiles; this avoids placement bias toward tiny crops.
            canvas_range = {
                "easy": (17, 20),
                "medium": (18, 22),
                "hard": (20, 24),
            }[band]
        elif band == "easy":
            canvas_range = (11, 15)
        elif band == "hard":
            canvas_range = (15, 21)
        else:
            canvas_range = (13, 18)
        layout_rng = ctx.draw_rng(f"general_layout_{scene_attempt}")
        height = layout_rng.randint(*canvas_range)
        width = layout_rng.randint(*canvas_range)
        patterns = [duplicate, duplicate, *distractors]
        layout_rng.shuffle(patterns)
        grid = full_grid(height, width, 0)
        reserved = full_grid(height, width, False)
        if not all(
            _try_place_pattern(grid, pattern, layout_rng, reserved)
            for pattern in patterns
        ):
            continue

        errors = self_check(grid, meta={"overrides": overrides})
        observed = observe_overrides(grid)
        if errors or observed.get("canonical_prior") is not False:
            continue
        info = _analysis(grid)
        duplicate_info = info["duplicate"]
        has_direct_rebuttal = any(
            distractor["mask"] == duplicate_info["mask"]
            or distractor["colors"] == duplicate_info["colors"]
            for distractor in info["distractors"]
        )
        # With exactly two private-palette distractors, the middle-rank lesson
        # cannot also include a same-mask tie.  Its smaller/larger bracket is
        # itself the direct rebuttal to count/extreme shortcuts.
        if not has_direct_rebuttal and info["duplicate_rank"] != "middle":
            continue

        required_witnesses = []
        if "d4" in roles:
            required_witnesses.extend(
                ("d4_equivalent_crop_first", "palette_only_first")
            )
        if "shape_recolor" in roles:
            required_witnesses.append("shape_only_first")
        if any(not SEMANTIC_WITNESSES[name](grid) for name in required_witnesses):
            # The right distractor must precede the exact duplicate class in
            # reading order. Presence without a changed prediction is not
            # teaching evidence.
            continue

        # Both ordinary generalized demonstrations independently refute fixed
        # first/last selectors, so any single-pair query rotation retains a
        # complete exact-equality lesson.
        if sample_index % 3 in (1, 2) and (
            info["components"][0]["crop"] == duplicate_info["crop"]
            or info["components"][-1]["crop"] == duplicate_info["crop"]
        ):
            continue
        return grid
    raise ValueError("could not construct a valid generalized duplicated-crop scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_prior = _draw_canonical_prior(ctx, overrides, sample_index)
    grid = _draw_canonical(ctx, overrides) if canonical_prior else _draw_generalized(
        ctx, overrides, difficulty or "medium", sample_index
    )
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid scene: " + "; ".join(errors))
    return [list(row) for row in grid]
