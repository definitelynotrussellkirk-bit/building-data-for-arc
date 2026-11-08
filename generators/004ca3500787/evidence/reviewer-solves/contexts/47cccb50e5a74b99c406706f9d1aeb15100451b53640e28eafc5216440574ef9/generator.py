"""Generator for ARC task 004ca3500787 (dihedral odd-one-out).

THE RULE
========
Every non-background object is a red 4-connected component.  Components are
grouped by *free* polyomino shape: translations, rotations, and reflections do
not change a class.  Exactly one component belongs to a singleton class.  The
answer is that component's lexicographically canonical D4-normalized mask,
recolored cyan (8), on its tight bounding box.

TEACHING DESIGN
===============
The four-sample default schedule deliberately recombines the answer-bearing
factors.  Across every consecutive four examples it includes:

* repeated common shapes in visibly different poses;
* a chiral common pair whose equivalence requires reflection, not rotation;
* common and outlier shapes with the same cell count;
* non-canonical observed poses, so copying the raw crop is wrong;
* examples refuting fixed first/last-component and layout-based selection; and
* canonical and broader five-cell output classes (masks can repeat).

The reflection-teaching role swaps between the two broad profiles by seed.
Outlier ranks vary within each visible layout; the reflection witness excludes
first position and the former layout shortcut, while a canonical profile
guarantees a nonlast target. These constraints preserve four-example teaching
without letting component count and dimensions identify the target.

Malformed/no-rule scenes are exposed by ``mutation_fixtures`` for negative
checks.  They are not public generation modes: every declared AXES combination
that is not listed in ``INCOMPATIBLE_OVERRIDE_COMBINATIONS`` must produce a
lawful task instance.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "004ca3500787"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "18bdd6911037"
EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 11

SUMMARY = (
    "A 0-background grid contains 3-5 halo-separated red polyominoes. "
    "All but one are the same free shape under rotation/reflection; output "
    "the singleton class as its canonical cyan tight-bbox mask."
)

INVARIANTS = [
    "the grid is rectangular, uses only colors 0 and 2, and is 9..18 by 12..22",
    "there are 3..5 red 4-connected components, each with 3..5 cells",
    "different components are separated by a one-cell Chebyshev halo",
    "exactly two D4 shape classes occur with counts (n-1, 1)",
    "the output is the singleton class's lexicographically canonical D4 mask in cyan",
]

# All names below are distinct free-polyomino classes.  Shapes are kept to at
# most 5 cells so generated examples remain close to the five canonical pairs.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "I3": ((0, 0), (0, 1), (0, 2)),
    "L3": ((0, 0), (1, 0), (1, 1)),
    "I4": ((0, 0), (0, 1), (0, 2), (0, 3)),
    "L4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "O4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "S4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    # Nine distinct free pentominoes (including the chiral F shape).
    "F5": ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    "L5": ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "T5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "U5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "V5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "W5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "X5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "Z5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
}
_SHAPE_NAMES = tuple(sorted(_SHAPES))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "9..18",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/profile schedule",
        "valid": "12..22",
        "doc": "Input grid width.",
    },
    "num_components": {
        "type": "int",
        "default": "profile schedule spanning 3..5",
        "valid": "3..5",
        "doc": "Total red components, including the singleton outlier.",
    },
    "common_shape": {
        "type": "enum",
        "default": "profile schedule",
        "valid": "F5|I3|I4|L3|L4|L5|O4|P5|S4|T4|T5|U5|V5|W5|X5|Z5",
        "doc": "Free-polyomino class repeated num_components-1 times.",
    },
    "outlier_shape": {
        "type": "enum",
        "default": "profile schedule",
        "valid": "F5|I3|I4|L3|L4|L5|O4|P5|S4|T4|T5|U5|V5|W5|X5|Z5",
        "doc": "Free-polyomino class occurring exactly once.",
    },
    "size_relation": {
        "type": "enum",
        "default": "derived from the two selected classes",
        "valid": "same|different",
        "doc": "Whether common and outlier have equal cell counts.",
    },
}

PALETTE_KINDS: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


# ------------------------------------------------------------------ D4 math

def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rot90(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _norm(cells)
    height = max(r for r, _ in norm) + 1
    return _norm((c, height - 1 - r) for r, c in norm)


def _reflect_v(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _norm(cells)
    width = max(c for _, c in norm) + 1
    return _norm((r, width - 1 - c) for r, c in norm)


def _rotation_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: list[tuple[tuple[int, int], ...]] = []
    cur = _norm(cells)
    for _ in range(4):
        if cur not in variants:
            variants.append(cur)
        cur = _rot90(cur)
    return tuple(sorted(variants))


def _d4_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    direct = list(_rotation_variants(cells))
    mirrored = list(_rotation_variants(_reflect_v(cells)))
    return tuple(sorted(set(direct + mirrored)))


def _d4_canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    variants = _d4_variants(cells)
    return variants[0] if variants else ()


def _rotation_canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    variants = _rotation_variants(cells)
    return variants[0] if variants else ()


_CLASS_TO_NAME = {_d4_canonical(cells): name for name, cells in _SHAPES.items()}
if len(_CLASS_TO_NAME) != len(_SHAPES):
    raise AssertionError("_SHAPES contains duplicate D4 classes")


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _mask(cells: Iterable[tuple[int, int]], color: int = 8) -> list[list[int]]:
    norm = _norm(cells)
    if not norm:
        return []
    height, width = _shape_dims(norm)
    result = full_grid(height, width, 0)
    for row, col in norm:
        result[row][col] = color
    return result


# -------------------------------------------------------------- grid analysis

def _rectangular_grid_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) and row for row in grid):
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(not isinstance(value, int) or isinstance(value, bool) for row in grid for value in row):
        return "grid cells must be integers"
    return None


def _components_4(grid: list[list[int]], color: int = 2) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(sorted(component))
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    rectangular_error = _rectangular_grid_error(grid)
    if rectangular_error:
        return {"errors": [rectangular_error], "components": []}

    height = len(grid)
    width = len(grid[0])
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2}:
        errors.append("palette must be a subset of {0, 2}")
    if 2 not in palette:
        errors.append("at least one red component is required")

    components = _components_4(grid, 2)
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 red components, got {len(components)}")

    records: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        norm = _norm(component)
        canonical = _d4_canonical(component)
        records.append(
            {
                "index": index,
                "cells": tuple(component),
                "norm": norm,
                "canonical": canonical,
                "rotation_canonical": _rotation_canonical(component),
                "name": _CLASS_TO_NAME.get(canonical),
                "size": len(component),
                "top_left": min(component),
            }
        )
        if not 3 <= len(component) <= 5:
            errors.append(
                f"component {index} must contain 3..5 cells, got {len(component)}"
            )

    owner: dict[tuple[int, int], int] = {}
    for index, component in enumerate(components):
        for cell in component:
            owner[cell] = index
    for (row, col), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = owner.get((row + dr, col + dc))
                if other is not None and other != index:
                    errors.append("different red components must be halo-separated")
                    # One example is enough; avoid quadratic duplicate findings.
                    dr = dc = 2
                    break
            else:
                continue
            break
        if errors and errors[-1] == "different red components must be halo-separated":
            break

    class_counts = Counter(record["canonical"] for record in records)
    singleton_classes = [key for key, count in class_counts.items() if count == 1]
    majority_classes = [key for key, count in class_counts.items() if count == len(records) - 1]
    if len(class_counts) != 2 or len(singleton_classes) != 1 or len(majority_classes) != 1:
        errors.append("expected exactly two D4 classes with counts (n-1, 1)")

    outlier = None
    common = None
    if len(singleton_classes) == 1:
        outlier = next(
            (record for record in records if record["canonical"] == singleton_classes[0]),
            None,
        )
    if len(majority_classes) == 1:
        common = next(
            (record for record in records if record["canonical"] == majority_classes[0]),
            None,
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": records,
        "class_counts": class_counts,
        "common": common,
        "outlier": outlier,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if not errors:
        height = analysis["height"]
        width = analysis["width"]
        if not 9 <= height <= 18:
            errors.append(f"generated grid height must be 9..18, got {height}")
        if not 12 <= width <= 22:
            errors.append(f"generated grid width must be 12..22, got {width}")
        if any(record["name"] is None for record in analysis["components"]):
            errors.append("every component must belong to the declared shape bank")
    return errors


# ---------------------------------------------------------- canonical profile

def canonical_profile_signature(grid) -> tuple[int, str, str] | None:
    """Return the task-linked (component count, majority class, odd class)."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None or analysis["outlier"] is None:
        return None
    common_name = analysis["common"]["name"]
    outlier_name = analysis["outlier"]["name"]
    if common_name is None or outlier_name is None:
        return None
    return len(analysis["components"]), common_name, outlier_name


_CANONICAL_SIGNATURES = {
    (3, "L3", "I3"),
    (3, "T4", "S4"),
    (3, "L4", "T4"),
    (3, "S4", "I3"),
    (3, "L3", "S4"),
}
MIN_STRICT_FRAC = 0.45


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"profile {signature!r} is not one of the five canonical class pairings"]
    return []


# ------------------------------------------------------------ generation plan
# Profiles 0 and 3 always draw one of the five exact canonical class/count
# signatures.  Profiles 1 and 2 broaden count, output class, and chirality while
# preserving the same shortcut-rebutting role.  The private pair choice varies
# by seed/sample-index so the stream is not four fixed templates.
_CANONICAL_PAIRS = tuple(sorted((common, outlier) for _, common, outlier in _CANONICAL_SIGNATURES))
_PROFILE_ROWS = (
    {"count": 3},
    {"count": 4},
    {"count": 5},
    {"count": 3},
)
SCHEDULE_PROFILES = (0, 1, 2, 3)
LESSON_SCHEDULE_PERIOD = 4


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return difficulty


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % len(_PROFILE_ROWS)


def _reflection_profile(seed) -> int:
    # The role must stay constant across sample indices, including windows
    # straddling a period boundary. Each broad layout can have either role.
    role_ctx = gen_ctx(
        seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID,
        difficulty=None,
    )
    return role_ctx.draw_rng("reflection_profile").choice((1, 2))


def _layout_shortcut_rank(count: int, height: int, width: int) -> int:
    """The exact target-selection shortcut admitted by version 4.0.0."""
    if count == 4:
        return 3
    if count == 5:
        return 2
    return 1 if (height, width) in ((9, 12), (10, 13), (11, 13)) else 0


_DIMENSIONS = {
    "easy": ((9, 12), (10, 13), (11, 14), (12, 15)),
    "medium": ((10, 13), (15, 19), (16, 20), (11, 14)),
    "hard": ((11, 13), (17, 21), (18, 22), (10, 12)),
}


def _draw_int_with_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_with_default(ctx, label: str, options: Sequence[str], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _relation(a: str, b: str) -> str:
    return "same" if len(_SHAPES[a]) == len(_SHAPES[b]) else "different"


def _first_compatible(other: str, relation: str) -> str:
    candidates = [
        name
        for name in _SHAPE_NAMES
        if name != other and _relation(name, other) == relation
    ]
    if not candidates:
        raise ValueError(f"no {relation}-sized distinct class exists for {other}")
    return candidates[0]


def _resolve_classes(ctx, profile: dict[str, Any]) -> tuple[str, str, str]:
    common_override = ctx.overrides.get("common_shape")
    outlier_override = ctx.overrides.get("outlier_shape")
    relation_override = ctx.overrides.get("size_relation")

    if relation_override is not None and relation_override not in ("same", "different"):
        # Consume through GenCtx so the ordinary override validation owns the message.
        ctx.draw_choice("size_relation", ("same", "different"))
        raise AssertionError("unreachable")

    target_relation = relation_override
    common_default = profile["common"]
    outlier_default = profile["outlier"]

    if common_override is not None and common_override not in _SHAPES:
        ctx.draw_choice("common_shape", _SHAPE_NAMES)
        raise AssertionError("unreachable")
    if outlier_override is not None and outlier_override not in _SHAPES:
        ctx.draw_choice("outlier_shape", _SHAPE_NAMES)
        raise AssertionError("unreachable")

    # Select defaults around whichever sides the caller pinned.  A single-axis
    # override is always realizable; only explicit contradictory tuples reject.
    if common_override is not None:
        common_default = common_override
    if outlier_override is not None:
        outlier_default = outlier_override

    if common_override is not None and outlier_override is None:
        relation_wanted = target_relation or _relation(profile["common"], profile["outlier"])
        if outlier_default == common_default or _relation(common_default, outlier_default) != relation_wanted:
            outlier_default = _first_compatible(common_default, relation_wanted)
    elif outlier_override is not None and common_override is None:
        relation_wanted = target_relation or _relation(profile["common"], profile["outlier"])
        if common_default == outlier_default or _relation(common_default, outlier_default) != relation_wanted:
            common_default = _first_compatible(outlier_default, relation_wanted)
    elif common_override is None and outlier_override is None and target_relation is not None:
        if _relation(common_default, outlier_default) != target_relation:
            outlier_default = _first_compatible(common_default, target_relation)

    common_name = _draw_choice_with_default(ctx, "common_shape", _SHAPE_NAMES, common_default)
    outlier_name = _draw_choice_with_default(ctx, "outlier_shape", _SHAPE_NAMES, outlier_default)

    if common_name == outlier_name:
        raise ValueError(
            "incompatible overrides common_shape/outlier_shape: classes must be distinct"
        )

    actual_relation = _relation(common_name, outlier_name)
    relation_name = _draw_choice_with_default(
        ctx, "size_relation", ("same", "different"), actual_relation
    )
    if relation_name != actual_relation:
        raise ValueError(
            "incompatible overrides common_shape/outlier_shape/size_relation: "
            f"{common_name} and {outlier_name} are {actual_relation}-sized"
        )
    return common_name, outlier_name, relation_name


# Explicitly document every rejected public tuple.  Single-axis requests are
# never rejected; only same-class pairs or a relation contradicted by two
# explicitly pinned classes are incompatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"common_shape": name, "outlier_shape": name}
    for name in _SHAPE_NAMES
] + [
    {
        "common_shape": common,
        "outlier_shape": outlier,
        "size_relation": requested,
    }
    for common in _SHAPE_NAMES
    for outlier in _SHAPE_NAMES
    if common != outlier
    for requested in ("same", "different")
    if requested != _relation(common, outlier)
]


def _slots(height: int, width: int, count: int) -> tuple[tuple[int, int], ...]:
    """Reading-order slots with a guaranteed one-cell halo at minimum size."""
    bottom = height - 4
    right = width - 3
    if count == 3:
        return ((0, 0), (0, right), (bottom, (width - 3) // 2))
    if count == 4:
        return ((0, 0), (0, right), (bottom, 0), (bottom, right))
    if count == 5:
        return ((0, 0), (0, 4), (0, right), (bottom, 2), (bottom, width - 5))
    raise ValueError(f"unsupported component count: {count}")


def _fitting_variants(shape_name: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = tuple(
        variant
        for variant in _d4_variants(_SHAPES[shape_name])
        if _shape_dims(variant)[0] <= 4 and _shape_dims(variant)[1] <= 3
    )
    if not variants:
        raise ValueError(f"shape {shape_name} has no orientation fitting a 4x3 slot")
    return variants


def _reflection_pair(shape_name: str) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]] | None:
    direct = _rotation_variants(_SHAPES[shape_name])
    direct_classes = set(direct)
    for mirrored in _rotation_variants(_reflect_v(_SHAPES[shape_name])):
        if mirrored not in direct_classes and _shape_dims(mirrored)[0] <= 4 and _shape_dims(mirrored)[1] <= 3:
            first = next(
                (variant for variant in direct if _shape_dims(variant)[0] <= 4 and _shape_dims(variant)[1] <= 3),
                None,
            )
            if first is not None:
                return first, mirrored
    return None


_DEFAULT_BROAD_OUTLIERS = (
    "F5", "L5", "P5", "T5", "U5", "V5", "W5", "Z5",
)
_BROAD_SAME_SIZE_PAIRS = tuple(
    (common, outlier)
    for common in _SHAPE_NAMES
    for outlier in _DEFAULT_BROAD_OUTLIERS
    if common != outlier
    and _relation(common, outlier) == "same"
    and len(_fitting_variants(common)) >= 2
    and len(_fitting_variants(outlier)) >= 2
)
_REFLECTION_SAME_SIZE_PAIRS = tuple(
    (common, outlier)
    for common, outlier in _BROAD_SAME_SIZE_PAIRS
    if _reflection_pair(common) is not None
)
if not _REFLECTION_SAME_SIZE_PAIRS:
    raise AssertionError("shape bank lacks a reflection-only teaching pair")


def _profile_defaults(ctx, profile_index: int, reflection_index: int) -> dict[str, Any]:
    # A keyed RNG avoids modular aliasing between seed and sample-index strides
    # while keeping exact replay.  The finite default codomain is separately
    # declared and exhaustively checked by the diversity probe.
    rng = ctx.draw_rng("profile_pair_variation")
    if profile_index in (0, 3):
        pair = rng.choice(_CANONICAL_PAIRS)
    elif profile_index == reflection_index:
        pair = rng.choice(_REFLECTION_SAME_SIZE_PAIRS)
    else:
        pair = rng.choice(_BROAD_SAME_SIZE_PAIRS)
    row = dict(_PROFILE_ROWS[profile_index])
    row["common"], row["outlier"] = pair
    return row


def _common_orientations(
    shape_name: str,
    count: int,
    *,
    force_reflection: bool,
    rng=None,
) -> list[tuple[tuple[int, int], ...]]:
    variants = list(_fitting_variants(shape_name))
    if force_reflection:
        pair = _reflection_pair(shape_name)
        if pair is not None:
            direct_class = _rotation_canonical(pair[0])
            direct = [
                variant for variant in variants
                if _rotation_canonical(variant) == direct_class
            ]
            mirrored = [
                variant for variant in variants
                if _rotation_canonical(variant) != direct_class
            ]
            if rng is not None:
                rng.shuffle(direct)
                rng.shuffle(mirrored)
            # One mirrored common is a rotation-only singleton, followed by
            # ordinary rotations of the same *free* shape.  The true outlier
            # therefore cannot be found without admitting reflection.
            return [mirrored[0]] + [
                direct[index % len(direct)] for index in range(count - 1)
            ]
    # Start with distinct poses when the class permits them.  Keyed shuffling
    # gives seed/sample-index diversity without weakening the four-profile
    # semantic schedule.
    canonical = _d4_canonical(_SHAPES[shape_name])
    variants.sort(key=lambda variant: (variant == canonical, variant))
    if rng is not None:
        rng.shuffle(variants)
    return [variants[index % len(variants)] for index in range(count)]


def _outlier_orientation(shape_name: str, rng=None) -> tuple[tuple[int, int], ...]:
    canonical = _d4_canonical(_SHAPES[shape_name])
    variants = list(_fitting_variants(shape_name))
    noncanonical = [variant for variant in variants if variant != canonical]
    choices = noncanonical or variants
    return rng.choice(choices) if rng is not None else choices[-1]


def _paint_component(
    grid: list[list[int]], origin: tuple[int, int], cells: Sequence[tuple[int, int]]
) -> None:
    row0, col0 = origin
    for row, col in cells:
        if grid[row0 + row][col0 + col] != 0:
            raise ValueError("internal placement overlap")
        grid[row0 + row][col0 + col] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    # Keep the real instance context last for public draw-provenance observers.
    reflection_index = _reflection_profile(seed)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_index = schedule_profile(seed, sample_index, band)
    profile = _profile_defaults(ctx, profile_index, reflection_index)
    default_h, default_w = _DIMENSIONS[band][profile_index]
    height = _draw_int_with_default(ctx, "grid_h", 9, 18, default_h)
    width = _draw_int_with_default(ctx, "grid_w", 12, 22, default_w)
    count = _draw_int_with_default(ctx, "num_components", 3, 5, profile["count"])
    common_name, outlier_name, _ = _resolve_classes(ctx, profile)

    # Preserve actual witnesses while removing the old layout-to-target map.
    # Swapping the reflection role lets both broad layouts realize every rank
    # across seeds; a nonwitness profile has no position restriction.
    reflection_role = profile_index == reflection_index
    ranks = list(range(count))
    if reflection_role:
        former_rank = _layout_shortcut_rank(count, height, width)
        ranks = [rank for rank in ranks if rank != 0 and rank != former_rank]
    elif profile_index == 3:
        ranks = ranks[:-1]
    outlier_rank = ctx.draw_rng("outlier_rank_variation").choice(ranks)
    slots = _slots(height, width, count)
    force_reflection = reflection_role and _reflection_pair(common_name) is not None
    pose_rng = ctx.draw_rng("pose_variation")
    common_poses = _common_orientations(
        common_name,
        count - 1,
        force_reflection=force_reflection,
        rng=pose_rng,
    )
    outlier_pose = _outlier_orientation(outlier_name, pose_rng)

    grid = full_grid(height, width, 0)
    common_cursor = 0
    for rank, origin in enumerate(slots):
        if rank == outlier_rank:
            cells = outlier_pose
        else:
            cells = common_poses[common_cursor]
            common_cursor += 1
        _paint_component(grid, origin, cells)

    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError(f"internal generator contract violation: {errors}")
    return grid


# ------------------------------------------------------- override observation

def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None or analysis["outlier"] is None:
        return {"errors": list(analysis["errors"])}
    common_name = analysis["common"]["name"]
    outlier_name = analysis["outlier"]["name"]
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "num_components": len(analysis["components"]),
        "common_shape": common_name,
        "outlier_shape": outlier_name,
        "size_relation": (
            "same"
            if analysis["common"]["size"] == analysis["outlier"]["size"]
            else "different"
        ),
    }


# ----------------------------------------------------------- authoritative mirror

def rule_mirror(grid) -> list[list[int]] | None:
    """Pure Python diagnostic mirror of the selected Racket rule."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return None
    return _mask(analysis["outlier"]["canonical"], 8)


def _record_to_mask(record: dict[str, Any], *, canonical: bool = True) -> list[list[int]]:
    return _mask(record["canonical"] if canonical else record["norm"], 8)


def _pick_first(records: Sequence[dict[str, Any]]) -> list[list[int]] | None:
    return _record_to_mask(records[0]) if records else None


def _pick_last(records: Sequence[dict[str, Any]]) -> list[list[int]] | None:
    return _record_to_mask(records[-1]) if records else None


def _rival_first_component(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else _pick_first(analysis["components"])


def _rival_last_component(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else _pick_last(analysis["components"])


def _rival_count_and_dimensions_target(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    rank = _layout_shortcut_rank(
        len(analysis["components"]), analysis["height"], analysis["width"]
    )
    return _record_to_mask(analysis["components"][rank])


def _rival_raw_observed_outlier_pose(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return None
    return _record_to_mask(analysis["outlier"], canonical=False)


def _odd_by_key(
    records: Sequence[dict[str, Any]], key: Callable[[dict[str, Any]], Any]
) -> dict[str, Any] | None:
    counts = Counter(key(record) for record in records)
    for record in records:
        if counts[key(record)] == 1:
            return record
    return records[0] if records else None


def _rival_exact_pose_odd(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    record = _odd_by_key(analysis["components"], lambda item: item["norm"])
    return _record_to_mask(record) if record is not None else None


def _rival_rotation_only_odd(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    record = _odd_by_key(
        analysis["components"], lambda item: item["rotation_canonical"]
    )
    return _record_to_mask(record) if record is not None else None


def _rival_unique_cell_count(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    record = _odd_by_key(analysis["components"], lambda item: item["size"])
    return _record_to_mask(record) if record is not None else None


SEMANTIC_RIVALS = {
    "first_component": _rival_first_component,
    "last_component": _rival_last_component,
    "raw_observed_outlier_pose": _rival_raw_observed_outlier_pose,
    "exact_pose_odd_one_out": _rival_exact_pose_odd,
    "rotation_only_odd_one_out": _rival_rotation_only_odd,
    "unique_cell_count": _rival_unique_cell_count,
    "count_and_dimensions_target": _rival_count_and_dimensions_target,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "last_component": _rival_last_component,
}


def _valid_and_differs(grid, rival_name: str) -> bool:
    answer = rule_mirror(grid)
    return answer is not None and SEMANTIC_RIVALS[rival_name](grid) != answer


def _common_pose_varies(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None:
        return False
    common_key = analysis["common"]["canonical"]
    poses = {
        record["norm"]
        for record in analysis["components"]
        if record["canonical"] == common_key
    }
    return len(poses) >= 2 and _valid_and_differs(grid, "exact_pose_odd_one_out")


def _common_requires_reflection(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None:
        return False
    common_key = analysis["common"]["canonical"]
    rotation_classes = {
        record["rotation_canonical"]
        for record in analysis["components"]
        if record["canonical"] == common_key
    }
    return len(rotation_classes) >= 2 and _valid_and_differs(grid, "rotation_only_odd_one_out")


def _same_size_refutes_counting(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["common"] is None or analysis["outlier"] is None:
        return False
    return (
        analysis["common"]["size"] == analysis["outlier"]["size"]
        and _valid_and_differs(grid, "unique_cell_count")
    )


def _noncanonical_outlier_refutes_crop(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return False
    return (
        analysis["outlier"]["norm"] != analysis["outlier"]["canonical"]
        and _valid_and_differs(grid, "raw_observed_outlier_pose")
    )


def _outlier_not_first(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return False
    return analysis["outlier"]["index"] != 0 and _valid_and_differs(grid, "first_component")


def _outlier_not_last(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["outlier"] is None:
        return False
    return (
        analysis["outlier"]["index"] != len(analysis["components"]) - 1
        and _valid_and_differs(grid, "last_component")
    )


def _layout_does_not_identify_target(grid) -> bool:
    return _valid_and_differs(grid, "count_and_dimensions_target")


SEMANTIC_WITNESSES = {
    "common_class_uses_multiple_observed_poses": _common_pose_varies,
    "common_class_requires_reflection_not_only_rotation": _common_requires_reflection,
    "equal_cell_counts_refute_size_shortcut": _same_size_refutes_counting,
    "noncanonical_outlier_pose_refutes_raw_crop": _noncanonical_outlier_refutes_crop,
    "outlier_not_first_refutes_first_object": _outlier_not_first,
    "outlier_not_last_refutes_last_object": _outlier_not_last,
    "layout_does_not_identify_target": _layout_does_not_identify_target,
}
WITNESS_RIVALS = {
    "common_class_uses_multiple_observed_poses": ["exact_pose_odd_one_out"],
    "common_class_requires_reflection_not_only_rotation": ["rotation_only_odd_one_out"],
    "equal_cell_counts_refute_size_shortcut": ["unique_cell_count"],
    "noncanonical_outlier_pose_refutes_raw_crop": ["raw_observed_outlier_pose"],
    "outlier_not_first_refutes_first_object": ["first_component"],
    "outlier_not_last_refutes_last_object": ["last_component"],
    "layout_does_not_identify_target": ["count_and_dimensions_target"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if expected is None:
            reasons.append(f"demo {index} is not a lawful task instance")
        elif pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the dihedral odd-one-out rule")

    query_answer = rule_mirror(query["input"])
    if query_answer is None:
        reasons.append("query is not a lawful task instance")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the dihedral odd-one-out rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair.get("output") for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


# ----------------------------------------------------------- negative fixtures

def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    base = generate(19, 0, difficulty="easy")

    wrong_color = [row[:] for row in base]
    first_red = next(
        (r, c)
        for r, row in enumerate(wrong_color)
        for c, value in enumerate(row)
        if value == 2
    )
    wrong_color[first_red[0]][first_red[1]] = 3

    all_same = full_grid(9, 12, 0)
    for origin, pose in zip(_slots(9, 12, 3), _common_orientations("L3", 3, force_reflection=False)):
        _paint_component(all_same, origin, pose)

    all_different = full_grid(9, 12, 0)
    for origin, name in zip(_slots(9, 12, 3), ("I3", "L3", "T4")):
        _paint_component(all_different, origin, _fitting_variants(name)[0])

    halo_touch = [row[:] for row in base]
    # Add a diagonal bridge-neighbor between the first two top-row objects.
    # It remains red but violates the visual separation contract.
    halo_touch[2][3] = 2

    disconnected_noise = [row[:] for row in base]
    disconnected_noise[-1][-1] = 2

    ragged = [row[:] for row in base]
    ragged[-1] = ragged[-1][:-1]

    return [
        ("wrong_nonbackground_color", wrong_color),
        ("no_singleton_all_same", all_same),
        ("no_majority_all_different", all_different),
        ("halo_touching_components", halo_touch),
        ("extra_singleton_component", disconnected_noise),
        ("ragged_grid", ragged),
    ]
