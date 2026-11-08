"""Reviewed generator for ARC task 1f8b5c5d1756.

The input contains one or more *paired* yellow shapes: every repeated
translation-normalized shape appears exactly twice.  Exactly one yellow shape
is unpaired.  The canonical Racket rule keeps that singleton in place,
recolors it cyan, and clears every other cell.

The schedule deliberately includes a rotated singleton and a same-area
singleton.  Those cases distinguish the exact translation-normalized rule
from two tempting shortcuts: grouping shapes up to dihedral symmetry and
selecting an object by unique area.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1f8b5c5d1756"
TASK_ID = "1f8b5c5d1756"
VERSION = "4.0.0"
RULE_HASH = "d67f50454e7f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains one or two paired families of yellow "
    "objects.  Each repeated translation-normalized shape appears exactly "
    "twice, and exactly one shape appears once.  Keep only that unpaired "
    "object at its original position and recolor it cyan.  The curriculum "
    "cycles rotation-equivalent, same-area, smaller-target, and larger-target "
    "cases so shape frequency—not orientation-invariant shape, area, size, "
    "position, or object order—determines the answer."
)

INVARIANTS = [
    "background is 0 and every foreground cell is yellow (4)",
    "there are one or two repeated exact-shape families plus one singleton",
    "every repeated translation-normalized signature occurs exactly twice",
    "exactly one translation-normalized signature occurs once",
    "objects are spatially separated and the singleton is observable from the input",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked schedule",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "linked schedule",
        "valid": "13..18",
    },
    "pair_families": {
        "type": "int",
        "default": "schedule: 1 or 2",
        "valid": "1..2",
    },
    "unique_relation": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "rotated_pair|same_area|different_area",
    },
    "unique_location": {
        "type": "str",
        "default": "alternating edge/interior",
        "valid": "edge|interior",
    },
}

_RELATIONS = ("rotated_pair", "same_area", "different_area")
_LOCATIONS = ("edge", "interior")
_SIZE_PROFILES = ((9, 13), (10, 14), (11, 15), (12, 16), (14, 18))
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}
SCHEDULE_PROFILES = (
    "rotation_exactness",
    "same_area",
    "target_smaller",
    "target_larger",
)

Point = tuple[int, int]
Shape = tuple[Point, ...]


def _norm(cells: Iterable[Point]) -> Shape:
    pts = tuple(cells)
    if not pts:
        return ()
    min_row = min(row for row, _ in pts)
    min_col = min(col for _, col in pts)
    return tuple(sorted((row - min_row, col - min_col) for row, col in pts))


def _rot90(shape: Shape) -> Shape:
    if not shape:
        return ()
    height = max(row for row, _ in shape) + 1
    return _norm((col, height - 1 - row) for row, col in shape)


def _reflect(shape: Shape) -> Shape:
    if not shape:
        return ()
    width = max(col for _, col in shape) + 1
    return _norm((row, width - 1 - col) for row, col in shape)


def _d4_canonical(shape: Shape) -> Shape:
    forms: list[Shape] = []
    current = _norm(shape)
    for base in (current, _reflect(current)):
        rotated = base
        for _ in range(4):
            forms.append(rotated)
            rotated = _rot90(rotated)
    return min(forms)


def _fixed_polyominoes(min_size: int = 3, max_size: int = 5) -> tuple[Shape, ...]:
    """Enumerate small oriented connected shapes, deterministically."""
    level: set[Shape] = {((0, 0),)}
    collected: list[Shape] = []
    for size in range(1, max_size + 1):
        if size >= min_size:
            collected.extend(
                shape
                for shape in sorted(level)
                if max(row for row, _ in shape) < 3
                and max(col for _, col in shape) < 3
            )
        if size == max_size:
            break
        next_level: set[Shape] = set()
        for shape in level:
            cells = set(shape)
            for row, col in shape:
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    candidate = set(cells)
                    candidate.add((row + drow, col + dcol))
                    if len(candidate) == size + 1:
                        next_level.add(_norm(candidate))
        level = next_level
    return tuple(sorted(set(collected), key=lambda item: (len(item), item)))


_SHAPES = _fixed_polyominoes()
_SHAPES_BY_AREA = {
    area: tuple(shape for shape in _SHAPES if len(shape) == area)
    for area in range(3, 6)
}
_ROTATABLE = tuple(
    shape
    for shape in _SHAPES
    if any(_rot90(shape) != shape for _ in (0,))
)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list):
        raise ValueError("grid must be a list")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _components(grid: list[list[int]]) -> list[tuple[Point, ...]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    components: list[tuple[Point, ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + drow, col + dcol)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        components.append(tuple(sorted(cells)))
    return sorted(components, key=lambda cells: cells[0])


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be non-empty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    if height > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30x30")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}
    wrong_colors = [
        (row, col, value)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value not in (0, 4)
    ]
    if wrong_colors:
        errors.append(f"foreground must use only yellow (4), found {wrong_colors[:3]!r}")

    components = _components(values)
    if not components:
        errors.append("expected yellow objects")
    if len(components) not in (3, 5, 7):
        errors.append("expected 3, 5, or 7 objects (paired families plus one singleton)")
    signatures = [_norm(cells) for cells in components]
    frequencies = Counter(signatures)
    singleton_signatures = [signature for signature, count in frequencies.items() if count == 1]
    bad_counts = sorted(count for count in frequencies.values() if count not in (1, 2))
    if len(singleton_signatures) != 1:
        errors.append(
            "expected exactly one translation-normalized shape signature with frequency 1"
        )
    if bad_counts:
        errors.append(f"every non-singleton signature must occur exactly twice, got {bad_counts!r}")
    if frequencies and len(frequencies) - len(singleton_signatures) < 1:
        errors.append("expected at least one repeated shape family")
    sizes = [len(cells) for cells in components]
    if any(size < 2 or size > 8 for size in sizes):
        errors.append("each object must contain 2..8 cells")

    target_index = None
    if len(singleton_signatures) == 1:
        target_signature = singleton_signatures[0]
        target_index = signatures.index(target_signature)
    target = components[target_index] if target_index is not None else ()
    repeated_signatures = tuple(
        signature for signature, count in sorted(frequencies.items()) if count == 2
    )
    relation = None
    if target:
        target_signature = signatures[target_index]
        if any(
            _d4_canonical(target_signature) == _d4_canonical(signature)
            for signature in repeated_signatures
        ):
            relation = "rotated_pair"
        elif any(len(target_signature) == len(signature) for signature in repeated_signatures):
            relation = "same_area"
        else:
            relation = "different_area"
    location = None
    if target:
        location = (
            "edge"
            if any(
                row in (0, height - 1) or col in (0, width - 1)
                for row, col in target
            )
            else "interior"
        )
    target_top_left = min(target) if target else None
    object_top_lefts = [min(cells) for cells in components]
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "components": tuple(components),
        "signatures": tuple(signatures),
        "frequencies": frequencies,
        "pair_families": sum(1 for count in frequencies.values() if count == 2),
        "target_index": target_index,
        "target": tuple(target),
        "target_signature": signatures[target_index] if target_index is not None else (),
        "target_area": len(target),
        "repeated_signatures": repeated_signatures,
        "repeated_areas": tuple(len(signature) for signature in repeated_signatures),
        "unique_relation": relation,
        "unique_location": location,
        "target_top_left": target_top_left,
        "object_top_lefts": tuple(object_top_lefts),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "pair_families": analysis["pair_families"],
        "unique_relation": analysis["unique_relation"],
        "unique_location": analysis["unique_location"],
    }
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    for name, actual in observed.items():
        expected = requested.get(name)
        if expected is not None and expected != actual:
            errors.append(f"meta {name} requested {expected!r}, observed {actual!r}")
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "pair_families": analysis["pair_families"],
        "unique_relation": analysis["unique_relation"],
        "unique_location": analysis["unique_location"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["pair_families"] not in (1, 2):
        errors.append("canonical-linked grammar uses one or two repeated families")
    if not 8 <= analysis["height"] <= 16 or not 10 <= analysis["width"] <= 18:
        errors.append("grid dimensions fall outside the canonical-linked envelope")
    if any(len(signature) not in (3, 4, 5) for signature in analysis["signatures"]):
        errors.append("canonical-linked objects have area 3..5")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid odd-one-out scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row, col in analysis["target"]:
        output[row][col] = 8
    return output


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(key for key, value in overrides.items() if value is not None and key not in AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in ("grid_h", "grid_w", "pair_families"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    if overrides.get("unique_relation") is not None and overrides["unique_relation"] not in _RELATIONS:
        raise ValueError(f"unique_relation must be one of {_RELATIONS!r}")
    if overrides.get("unique_location") is not None and overrides["unique_location"] not in _LOCATIONS:
        raise ValueError(f"unique_location must be one of {_LOCATIONS!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_int_or_default(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice_or_default(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: str,
    options: tuple[str, ...],
) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _pick(rng, choices: Iterable[Shape]) -> Shape:
    options = tuple(sorted(set(choices)))
    if not options:
        raise ValueError("shape constraints left no candidates")
    return options[rng.randrange(len(options))]


def _choose_shapes(rng, pair_families: int, relation: str, profile: str) -> tuple[list[Shape], Shape]:
    if relation == "rotated_pair":
        first = _pick(rng, _ROTATABLE)
        rotations = []
        current = _rot90(first)
        for _ in range(3):
            if current != first:
                rotations.append(current)
            current = _rot90(current)
        target = _pick(rng, rotations)
    elif relation == "same_area":
        area = 3 + rng.randrange(3)
        first = _pick(rng, _SHAPES_BY_AREA[area])
        target = _pick(
            rng,
            (
                shape
                for shape in _SHAPES_BY_AREA[area]
                if _d4_canonical(shape) != _d4_canonical(first)
            ),
        )
    else:
        target_area = 3 if profile == "target_smaller" else 5
        pair_area = 5 if target_area == 3 else 3
        first = _pick(rng, _SHAPES_BY_AREA[pair_area])
        target = _pick(rng, _SHAPES_BY_AREA[target_area])

    pairs = [first]
    while len(pairs) < pair_families:
        if relation == "same_area":
            candidates = _SHAPES_BY_AREA[len(target)]
        elif relation == "different_area":
            candidates = tuple(
                shape for shape in _SHAPES if len(shape) != len(target)
            )
        else:
            candidates = _SHAPES
        candidate = _pick(
            rng,
            (
                shape
                for shape in candidates
                if shape != target and shape not in pairs
                and not (
                    relation == "rotated_pair"
                    and _d4_canonical(shape) == _d4_canonical(first)
                )
                and not (
                    relation == "same_area"
                    and _d4_canonical(shape) == _d4_canonical(target)
                )
            ),
        )
        pairs.append(candidate)
    return pairs, target


def _fits_with_clearance(
    occupied: set[Point],
    shape: Shape,
    top: int,
    left: int,
    height: int,
    width: int,
) -> bool:
    absolute = {(top + row, left + col) for row, col in shape}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in absolute):
        return False
    for row, col in absolute:
        for drow in (-1, 0, 1):
            for dcol in (-1, 0, 1):
                if (row + drow, col + dcol) in occupied:
                    return False
    return True


def _candidate_positions(shape: Shape, height: int, width: int, location: str | None) -> list[Point]:
    max_row = max(row for row, _ in shape)
    max_col = max(col for _, col in shape)
    positions: list[Point] = []
    for top in range(height - max_row):
        for left in range(width - max_col):
            cells = tuple((top + row, left + col) for row, col in shape)
            on_edge = any(
                row in (0, height - 1) or col in (0, width - 1)
                for row, col in cells
            )
            if location == "edge" and not on_edge:
                continue
            if location == "interior" and on_edge:
                continue
            positions.append((top, left))
    return positions


def _place_scene(
    height: int,
    width: int,
    pair_shapes: list[Shape],
    target: Shape,
    target_location: str,
    rng,
) -> list[list[int]]:
    target_positions = _candidate_positions(target, height, width, target_location)
    rng.shuffle(target_positions)
    other_shapes = [shape for pair in pair_shapes for shape in (pair, pair)]
    for target_top, target_left in target_positions:
        occupied: set[Point] = set()
        placements: list[tuple[Shape, int, int, bool]] = []
        if not _fits_with_clearance(
            occupied, target, target_top, target_left, height, width
        ):
            continue
        target_cells = {
            (target_top + row, target_left + col) for row, col in target
        }
        occupied.update(target_cells)
        placements.append((target, target_top, target_left, True))
        success = True
        ordered = list(other_shapes)
        rng.shuffle(ordered)
        for shape in ordered:
            candidates = _candidate_positions(shape, height, width, None)
            rng.shuffle(candidates)
            placed = False
            for top, left in candidates:
                if _fits_with_clearance(occupied, shape, top, left, height, width):
                    occupied.update((top + row, left + col) for row, col in shape)
                    placements.append((shape, top, left, False))
                    placed = True
                    break
            if not placed:
                success = False
                break
        if not success:
            continue
        target_anchor = min(target_cells)
        other_anchors = [
            (top + min(row for row, _ in shape), left + min(col for _, col in shape))
            for shape, top, left, is_target in placements
            if not is_target
        ]
        # Always provide a direct counterexample to "choose the first object".
        if not other_anchors or min(other_anchors) >= target_anchor:
            continue
        grid = full_grid(height, width, 0)
        for shape, top, left, _ in placements:
            for row, col in shape:
                grid[top + row][left + col] = 4
        return grid
    raise RuntimeError(
        f"could not place {1 + 2 * len(pair_shapes)} separated objects "
        f"in {height}x{width} with target_location={target_location!r}"
    )


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_offset = _BAND_OFFSETS[difficulty]
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _SIZE_PROFILES[(sample_index + band_offset) % len(_SIZE_PROFILES)]
    height = _draw_int_or_default(ctx, overrides, "grid_h", default_h, 9, 16)
    width = _draw_int_or_default(ctx, overrides, "grid_w", default_w, 13, 18)

    default_pairs = 2 if profile in ("same_area", "target_larger") else 1
    pair_families = _draw_int_or_default(
        ctx, overrides, "pair_families", default_pairs, 1, 2
    )
    default_relation = {
        "rotation_exactness": "rotated_pair",
        "same_area": "same_area",
        "target_smaller": "different_area",
        "target_larger": "different_area",
    }[profile]
    relation = _draw_choice_or_default(
        ctx, overrides, "unique_relation", default_relation, _RELATIONS
    )
    default_location = "edge" if sample_index % 2 == 0 else "interior"
    location = _draw_choice_or_default(
        ctx, overrides, "unique_location", default_location, _LOCATIONS
    )

    shape_rng = ctx.draw_rng(
        f"shapes|profile={profile}|pairs={pair_families}|relation={relation}"
    )
    layout_rng = ctx.draw_rng(
        f"layout|profile={profile}|dims={height}x{width}|pairs={pair_families}|"
        f"relation={relation}|location={location}"
    )
    pair_shapes, target = _choose_shapes(
        shape_rng, pair_families, relation, profile
    )
    grid = _place_scene(
        height, width, pair_shapes, target, location, layout_rng
    )
    errors = self_check(
        grid,
        meta={
            "grid_h": height,
            "grid_w": width,
            "pair_families": pair_families,
            "unique_relation": relation,
            "unique_location": location,
        },
    )
    if errors:
        raise AssertionError("generated invalid odd-one-out scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-local rival rules and semantic witnesses.
# ---------------------------------------------------------------------------


def _paint_object(grid: Any, cells: Iterable[Point]) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = full_grid(len(values), len(values[0]), 0)
    for row, col in cells:
        output[row][col] = 8
    return output


def _blank_like(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    return full_grid(len(values), len(values[0]), 0)


def _frequency_rival(grid: Any, key: Callable[[Shape], Any]) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    keyed = [key(_norm(cells)) for cells in components]
    counts = Counter(keyed)
    singletons = [index for index, value in enumerate(keyed) if counts[value] == 1]
    if len(singletons) != 1:
        return _blank_like(values)
    return _paint_object(values, components[singletons[0]])


def _rival_dihedral_frequency(grid: Any) -> list[list[int]]:
    return _frequency_rival(grid, _d4_canonical)


def _rival_unique_area(grid: Any) -> list[list[int]]:
    return _frequency_rival(grid, len)


def _rival_first_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    return _paint_object(values, components[0]) if components else _blank_like(values)


def _rival_largest_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    if not components:
        return _blank_like(values)
    target = min(components, key=lambda cells: (-len(cells), min(cells)))
    return _paint_object(values, target)


def _rival_smallest_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    if not components:
        return _blank_like(values)
    target = min(components, key=lambda cells: (len(cells), min(cells)))
    return _paint_object(values, target)


def _analysis_ok(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _w_rotation_unique(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "rotated_pair")


def _w_same_area_unique(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "same_area")


def _w_target_not_top_left(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and analysis["target_top_left"] != min(analysis["object_top_lefts"])
    )


def _w_target_not_largest(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and analysis["target_area"] < max(len(cells) for cells in analysis["components"])
    )


def _w_target_not_smallest(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and analysis["target_area"] > min(len(cells) for cells in analysis["components"])
    )


SEMANTIC_RIVALS = {
    "dihedral_frequency": _rival_dihedral_frequency,
    "unique_area": _rival_unique_area,
    "first_object": _rival_first_object,
    "largest_object": _rival_largest_object,
    "smallest_object": _rival_smallest_object,
}

SEMANTIC_WITNESSES = {
    "rotation_unique_refutes_dihedral_frequency": _w_rotation_unique,
    "same_area_unique_refutes_unique_area": _w_same_area_unique,
    "target_not_top_left_refutes_first_object": _w_target_not_top_left,
    "target_not_largest_refutes_largest_object": _w_target_not_largest,
    "target_not_smallest_refutes_smallest_object": _w_target_not_smallest,
}

WITNESS_RIVALS = {
    "rotation_unique_refutes_dihedral_frequency": ["dihedral_frequency"],
    "same_area_unique_refutes_unique_area": ["unique_area"],
    "target_not_top_left_refutes_first_object": ["first_object"],
    "target_not_largest_refutes_largest_object": ["largest_object"],
    "target_not_smallest_refutes_smallest_object": ["smallest_object"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "dihedral_frequency": _rival_dihedral_frequency,
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require each four-demo window to kill the named shortcut family."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    analyses: list[dict[str, Any]] = []
    outputs: list[tuple[tuple[int, ...], ...]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed: {analysis['errors'][:2]!r}")
            continue
        expected = rule_mirror(pair["input"])
        actual = _coerce_grid(pair["output"])
        if expected != actual:
            errors.append(f"demo {index} output does not select the exact-shape singleton")
            continue
        analyses.append(analysis)
        outputs.append(tuple(tuple(row) for row in actual))

    if len(analyses) == len(demos):
        if not any(item["unique_relation"] == "rotated_pair" for item in analyses):
            errors.append("demonstrations do not refute dihedral-invariant shape frequency")
        if not any(item["unique_relation"] == "same_area" for item in analyses):
            errors.append("demonstrations do not refute unique-area selection")
        if not any(
            item["target_area"] < max(len(cells) for cells in item["components"])
            for item in analyses
        ):
            errors.append("demonstrations do not refute largest-object selection")
        if not any(
            item["target_area"] > min(len(cells) for cells in item["components"])
            for item in analyses
        ):
            errors.append("demonstrations do not refute smallest-object selection")
        if not any(
            item["target_top_left"] != min(item["object_top_lefts"])
            for item in analyses
        ):
            errors.append("demonstrations do not refute first-object selection")
        if len(set(outputs)) < 3:
            errors.append("demonstration answers vary too little for a fixed-answer shortcut")
        if len({(item["height"], item["width"]) for item in analyses}) < 3:
            errors.append("demonstrations vary too little in grid size")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    else:
        query_analysis = _analyze(query["input"])
        if query_analysis.get("errors"):
            errors.append("query input is malformed")
    return errors
