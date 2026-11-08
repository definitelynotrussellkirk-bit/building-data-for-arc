"""Generator for ARC task ffdc0ddb44bd: crop the repeated shape.

The task compares same-colour connected objects by translation-normalized shape.
The unique most frequent shape is cropped from its first row-major occurrence
and recoloured cyan (8).  Colour and position are deliberately non-semantic.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "ffdc0ddb44bd"
TASK_ID = "ffdc0ddb44bd"
VERSION = "3.0.1"
RULE_HASH = "29652af15048"

SUMMARY = (
    "A 0-background grid contains three to five isolated objects, each in a "
    "different colour from 2 through 6. Exactly one translation-normalized "
    "shape occurs two to four times; one differently shaped object is a "
    "decoy. Crop the first row-major occurrence of the repeated shape to its "
    "bounding box and recolour its cells 8. A four-profile lesson schedule "
    "varies whether colour 2 and the first object are winner or decoy, so "
    "neither colour nor position identifies the answer."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is rectangular, 9..18 by 14..22, with 0 background",
    "three to five isolated candidate objects use distinct colours from 2..6",
    "exactly one normalized shape occurs 2..4 times",
    "exactly one differently shaped decoy object is present",
    "colour and row-major position do not determine semantic role",
]

AXES = {
    "height": {
        "type": "int",
        "default": "deterministic broad schedule retaining canonical 9x16 and 10x16 profiles",
        "valid": "9..18",
    },
    "width": {
        "type": "int",
        "default": "deterministic broad schedule retaining canonical width 16",
        "valid": "14..22",
    },
    "majority_count": {
        "type": "int",
        "default": "scheduled 2|3|4 with canonical 2-vs-1 emphasized",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (0, 1, 2, 3)

_HEIGHT_CYCLES = {
    "easy": (9, 10, 11, 12, 13, 14, 15, 16, 17, 18),
    "medium": (9, 10, 12, 14, 16, 18, 11, 13, 15, 17),
    "hard": (10, 9, 18, 17, 16, 15, 14, 13, 12, 11),
}
_WIDTH_CYCLES = {
    "easy": (16, 14, 15, 17, 18, 19, 20, 21, 22),
    "medium": (16, 18, 14, 20, 15, 22, 17, 19, 21),
    "hard": (16, 22, 21, 20, 19, 18, 17, 15, 14),
}
_MAJORITY_CYCLES = {
    "easy": (2, 2, 3, 2, 4, 2, 3, 2),
    "medium": (2, 3, 2, 4, 3, 2, 4, 2),
    "hard": (2, 4, 3, 4, 2, 4, 3, 2),
}

# (colour 2 is decoy, first row-major object is decoy)
_PROFILE_FLAGS = {
    0: (True, True),
    1: (False, False),
    2: (True, False),
    3: (False, True),
}

_CANDIDATE_COLORS = (2, 3, 4, 5, 6)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the finite semantic-role schedule state for one sample."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "height": (9, 18),
        "width": (14, 22),
        "majority_count": (2, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _scheduled_int(ctx, name, lo, hi, scheduled):
    """Use a scheduled default while keeping the complete exact override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _normalize(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _random_polyomino(rng, size):
    """Draw an exact-size connected polyomino contained in a 3x3 box."""
    cells = {(rng.randrange(3), rng.randrange(3))}
    while len(cells) < size:
        frontier = {
            (row + drow, col + dcol)
            for row, col in cells
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= row + drow < 3 and 0 <= col + dcol < 3
            and (row + drow, col + dcol) not in cells
        }
        if not frontier:  # unreachable before filling the 3x3 box
            raise RuntimeError("polyomino growth unexpectedly exhausted its frontier")
        cells.add(rng.choice(sorted(frontier)))
    return list(_normalize(cells))


def _different_polyomino(rng, excluded, *, sizes):
    for _ in range(128):
        candidate = _random_polyomino(rng, rng.choice(tuple(sizes)))
        if _normalize(candidate) not in excluded:
            return candidate
    # Deterministic connected fallbacks make the constructor total.
    fallbacks = (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    )
    for candidate in fallbacks:
        if _normalize(candidate) not in excluded:
            return list(candidate)
    raise RuntimeError("could not construct a normalized-distinct decoy")


def _dimension_defaults(sample_index, band):
    # Four consecutive canonical-profile defaults followed by four broad ones.
    # This keeps each semantic role profile available both at canonical scale
    # and off it, while giving the native off-diagonal profile census ample
    # exact support in every difficulty band.
    phase = sample_index % 8
    block = sample_index // 8
    if phase < len(SCHEDULE_PROFILES):
        return (9 + ((block + phase) % 2), 16, 2)
    broad_offset = block + phase - len(SCHEDULE_PROFILES)
    return (
        _HEIGHT_CYCLES[band][broad_offset % len(_HEIGHT_CYCLES[band])],
        _WIDTH_CYCLES[band][broad_offset % len(_WIDTH_CYCLES[band])],
        _MAJORITY_CYCLES[band][broad_offset % len(_MAJORITY_CYCLES[band])],
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input; all randomness is label-keyed and reproducible."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_majority = _dimension_defaults(sample_index, band)
    height = _scheduled_int(ctx, "height", 9, 18, default_h)
    width = _scheduled_int(ctx, "width", 14, 22, default_w)
    majority_count = _scheduled_int(
        ctx, "majority_count", 2, 4, default_majority
    )

    rng = ctx.draw_rng("scene")
    profile = schedule_profile(seed, sample_index, difficulty)
    color_two_is_decoy, first_is_decoy = _PROFILE_FLAGS[profile]
    candidate_count = majority_count + 1

    # Six 3x3 slots fit even the minimum 9x14 grid with a one-cell moat.
    top = rng.randrange(height - 7)
    left = rng.randrange(width - 12)
    all_slots = [(top + row_delta, left + col_delta)
                 for row_delta in (0, 5)
                 for col_delta in (0, 5, 10)]
    slots = sorted(rng.sample(all_slots, candidate_count))

    if first_is_decoy:
        decoy_slot = slots[0]
    else:
        decoy_slot = rng.choice(slots[1:])
    majority_slots = [slot for slot in slots if slot != decoy_slot]

    colors = [2] + rng.sample(list(_CANDIDATE_COLORS[1:]), candidate_count - 1)
    color_by_slot = {}
    if color_two_is_decoy:
        color_by_slot[decoy_slot] = 2
    else:
        color_by_slot[rng.choice(majority_slots)] = 2
    remaining_slots = [slot for slot in slots if slot not in color_by_slot]
    remaining_colors = [color for color in colors if color != 2]
    rng.shuffle(remaining_colors)
    color_by_slot.update(zip(remaining_slots, remaining_colors))

    majority_sizes = {
        "easy": (4, 4, 5),
        "medium": (4, 5, 5, 6),
        "hard": (5, 5, 6, 6),
    }[band]
    majority_shape = _random_polyomino(rng, rng.choice(majority_sizes))
    majority_norm = _normalize(majority_shape)
    decoy_shape = _different_polyomino(
        rng,
        {majority_norm},
        sizes={"easy": (3, 4), "medium": (3, 4, 5), "hard": (4, 5, 6)}[band],
    )

    grid = full_grid(height, width, 0)
    for slot in slots:
        shape = decoy_shape if slot == decoy_slot else majority_shape
        paint_at(grid, slot[0], slot[1], shape, color_by_slot[slot])
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or value not in {0, 2, 3, 4, 5, 6}
        for row in grid
        for value in row
    ):
        return ["grid may use only background 0 and candidate colours 2..6"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 18:
        errors.append(f"height must be 9..18, got {height}")
    if not 14 <= width <= 22:
        errors.append(f"width must be 14..22, got {width}")

    comps = sorted(
        components(grid, colors=set(_CANDIDATE_COLORS)),
        key=lambda comp: (comp["bbox"][0], comp["bbox"][1]),
    )
    if not 3 <= len(comps) <= 5:
        errors.append(f"expected 3..5 candidate objects, got {len(comps)}")
    colors = [comp["color"] for comp in comps]
    if len(set(colors)) != len(colors):
        errors.append("each candidate object must use a distinct colour")
    if comps and not components_have_clearance(grid, comps):
        errors.append("candidate objects must have a one-cell moat")
    for index, comp in enumerate(comps):
        r1, c1, r2, c2 = comp["bbox"]
        if not 3 <= len(comp["cells"]) <= 6:
            errors.append(f"candidate {index} must contain 3..6 cells")
        if r2 - r1 + 1 > 3 or c2 - c1 + 1 > 3:
            errors.append(f"candidate {index} must fit a 3x3 bounding box")

    shape_counts = Counter(comp["norm"] for comp in comps)
    ordered = sorted(shape_counts.values(), reverse=True)
    majority_count = ordered[0] if ordered else 0
    winner = None
    if len(shape_counts) != 2:
        errors.append(
            f"expected exactly one repeated shape and one decoy shape, got {len(shape_counts)} shapes"
        )
    elif ordered[1] != 1 or not 2 <= ordered[0] <= 4:
        errors.append(
            "shape multiplicities must be one strict majority (2..4 copies) plus one decoy"
        )
    else:
        winner = next(shape for shape, count in shape_counts.items()
                      if count == majority_count)

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": comps,
        "shape_counts": shape_counts,
        "majority_count": majority_count,
        "winner": winner,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    candidate = nested if isinstance(nested, dict) else meta
    return {name: value for name, value in candidate.items() if name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concrete invariant violations; [] means a lawful task input."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis directly from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "majority_count": analysis["majority_count"],
    }


def _crop_component(comp):
    r1, c1, r2, c2 = comp["bbox"]
    cells = set(comp["cells"])
    return [
        [8 if (row, col) in cells else 0 for col in range(c1, c2 + 1)]
        for row in range(r1, r2 + 1)
    ]


def rule_mirror(grid):
    """Independent Python oracle for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid repeated-shape scene: " + "; ".join(analysis["errors"]))
    winner = analysis["winner"]
    selected = next(
        comp for comp in analysis["components"] if comp["norm"] == winner
    )
    return _crop_component(selected)


def strict_canonical_like(grid) -> list[str]:
    """Lawful manifold containing every canonical and generated input."""
    return list(self_check(grid))


def _rival_color_two(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    selected = next(
        (comp for comp in analysis["components"] if comp["color"] == 2),
        None,
    )
    return _crop_component(selected) if selected is not None else None


def _rival_first_object(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        return None
    return _crop_component(analysis["components"][0])


def _witness_color_two_is_decoy(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    color_two = next(
        (comp for comp in analysis["components"] if comp["color"] == 2),
        None,
    )
    return color_two is not None and color_two["norm"] != analysis["winner"]


def _witness_first_object_is_decoy(grid) -> bool:
    analysis = _analysis(grid)
    return bool(
        not analysis["errors"]
        and analysis["components"]
        and analysis["components"][0]["norm"] != analysis["winner"]
    )


SEMANTIC_WITNESSES = {
    "color_2_is_decoy": _witness_color_two_is_decoy,
    "first_object_is_decoy": _witness_first_object_is_decoy,
}
SEMANTIC_RIVALS = {
    "color_2_object": _rival_color_two,
    "first_object": _rival_first_object,
}
WITNESS_RIVALS = {
    "color_2_is_decoy": ("color_2_object",),
    "first_object_is_decoy": ("first_object",),
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a canonical shortcut viable."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(deepcopy(pair["input"]))
        except Exception as exc:
            reasons.append(f"demo {index} is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the repeated-shape rule")

    try:
        query_answer = rule_mirror(deepcopy(query["input"]))
    except Exception as exc:
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the repeated-shape rule")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output")
            for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
