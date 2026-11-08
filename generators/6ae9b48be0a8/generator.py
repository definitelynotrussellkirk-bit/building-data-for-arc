"""Reviewed generator for ARC task 6ae9b48be0a8.

The input contains exactly three separated green objects.  Two have the same
translation-normalized shape and the third is the exact-shape singleton.  The
canonical Racket rule leaves the input in place and draws a yellow one-cell
rectangular border around the singleton object's bounding box.

The four-profile schedule deliberately includes a rotated singleton and a
same-area singleton, plus cases where the singleton is smaller and larger than
the repeated shape.  Those profiles refute tempting shortcuts based on
orientation-invariant shape, area, size, object order, or a fixed border size.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6ae9b48be0a8"
TASK_ID = "6ae9b48be0a8"
VERSION = "4.0.0"
RULE_HASH = "fb2ac8057665"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains exactly three separated green objects. "
    "Two have the same translation-normalized shape and one is the singleton. "
    "Draw a yellow one-cell rectangular border just outside the singleton's "
    "bounding box while leaving all green cells unchanged.  A four-profile "
    "curriculum cycles a rotation-equivalent singleton, a same-area but "
    "shape-different singleton, a smaller singleton, and a larger singleton; "
    "the singleton also cycles through first/middle/last spatial order."
)

INVARIANTS = [
    "background is 0 and every input foreground cell is green (3)",
    "exactly three 4-connected objects are present",
    "one translation-normalized shape occurs twice and exactly one occurs once",
    "the singleton bbox has an in-bounds clear one-cell ring for the yellow border",
    "all objects are separated, and each object has the same placement margin policy",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band-linked schedule",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "band-linked schedule",
        "valid": "12..18",
    },
    "unique_relation": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "rotated_pair|same_area|smaller|larger",
    },
    "target_rank": {
        "type": "str",
        "default": "three-profile schedule",
        "valid": "first|middle|last",
    },
}

_RELATIONS = ("rotated_pair", "same_area", "smaller", "larger")
_TARGET_RANKS = ("first", "middle", "last")
SCHEDULE_PROFILES = _RELATIONS
_BAND_SIZES = {
    None: ((12, 14), (14, 15), (15, 16), (13, 17)),
    "easy": ((12, 14), (10, 12), (11, 13)),
    "medium": ((14, 15), (12, 14), (13, 16)),
    "hard": ((15, 16), (14, 17), (16, 18)),
}

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
    """Enumerate small oriented connected shapes deterministically."""
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
_ROTATABLE = tuple(shape for shape in _SHAPES if _rot90(shape) != shape)


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


def _border_cells(cells: Iterable[Point], height: int, width: int) -> tuple[Point, ...]:
    pts = tuple(cells)
    if not pts:
        return ()
    min_row = min(row for row, _ in pts) - 1
    max_row = max(row for row, _ in pts) + 1
    min_col = min(col for _, col in pts) - 1
    max_col = max(col for _, col in pts) + 1
    if min_row < 0 or min_col < 0 or max_row >= height or max_col >= width:
        return ()
    return tuple(
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
        if row in (min_row, max_row) or col in (min_col, max_col)
    )


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
        if value not in (0, 3)
    ]
    if wrong_colors:
        errors.append(f"input foreground must use only green (3), found {wrong_colors[:3]!r}")

    components = _components(values)
    if len(components) != 3:
        errors.append(f"expected exactly 3 green objects, got {len(components)}")
    signatures = [_norm(cells) for cells in components]
    frequencies = Counter(signatures)
    singleton_signatures = [signature for signature, count in frequencies.items() if count == 1]
    repeated_signatures = [signature for signature, count in frequencies.items() if count == 2]
    if len(singleton_signatures) != 1 or len(repeated_signatures) != 1:
        errors.append(
            "expected one translation-normalized shape with frequency 2 and one with frequency 1"
        )
    bad_counts = sorted(count for count in frequencies.values() if count not in (1, 2))
    if bad_counts:
        errors.append(f"shape frequencies must be exactly 2 and 1, got {bad_counts!r}")
    if any(len(cells) < 2 or len(cells) > 8 for cells in components):
        errors.append("each object must contain 2..8 cells")

    target_index = None
    target_signature: Shape = ()
    common_signature: Shape = ()
    if len(singleton_signatures) == 1:
        target_signature = singleton_signatures[0]
        target_index = signatures.index(target_signature)
    if len(repeated_signatures) == 1:
        common_signature = repeated_signatures[0]
    target = components[target_index] if target_index is not None else ()
    border = _border_cells(target, height, width) if target else ()
    if target and not border:
        errors.append("singleton bbox must have a full one-cell in-bounds border")
    if border:
        occupied_border = [
            (row, col)
            for row, col in border
            if values[row][col] != 0
        ]
        if occupied_border:
            errors.append(
                "singleton border ring must be clear of input foreground; "
                f"found {occupied_border[:3]!r}"
            )

    relation = None
    if target_signature and common_signature:
        if _d4_canonical(target_signature) == _d4_canonical(common_signature):
            relation = "rotated_pair"
        elif len(target_signature) == len(common_signature):
            relation = "same_area"
        elif len(target_signature) < len(common_signature):
            relation = "smaller"
        else:
            relation = "larger"

    object_top_lefts = [min(cells) for cells in components]
    target_top_left = min(target) if target else None
    target_rank = None
    if target_top_left is not None and len(object_top_lefts) == 3:
        rank = sorted(object_top_lefts).index(target_top_left)
        target_rank = _TARGET_RANKS[rank]

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "components": tuple(components),
        "signatures": tuple(signatures),
        "frequencies": frequencies,
        "target_index": target_index,
        "target": tuple(target),
        "target_signature": target_signature,
        "common_signature": common_signature,
        "target_area": len(target),
        "common_area": len(common_signature),
        "border": border,
        "unique_relation": relation,
        "target_rank": target_rank,
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
        "unique_relation": analysis["unique_relation"],
        "target_rank": analysis["target_rank"],
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
        "unique_relation": analysis["unique_relation"],
        "target_rank": analysis["target_rank"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if not 10 <= analysis["height"] <= 16 or not 12 <= analysis["width"] <= 18:
        errors.append("grid dimensions fall outside the canonical-linked envelope")
    if any(len(signature) not in (3, 4, 5) for signature in analysis["signatures"]):
        errors.append("canonical-linked objects have area 3..5")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid odd-one-out scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in analysis["grid"]]
    for row, col in analysis["border"]:
        output[row][col] = 4
    return output


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_SIZES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(
        key for key, value in overrides.items()
        if value is not None and key not in AXES
    )
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    if overrides.get("unique_relation") is not None and overrides["unique_relation"] not in _RELATIONS:
        raise ValueError(f"unique_relation must be one of {_RELATIONS!r}")
    if overrides.get("target_rank") is not None and overrides["target_rank"] not in _TARGET_RANKS:
        raise ValueError(f"target_rank must be one of {_TARGET_RANKS!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return _RELATIONS[int(sample_index) % len(_RELATIONS)]


def _draw_int_or_default(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
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


def _choose_shapes(rng, relation: str) -> tuple[Shape, Shape]:
    if relation == "rotated_pair":
        common = _pick(rng, _ROTATABLE)
        rotations: list[Shape] = []
        current = _rot90(common)
        for _ in range(3):
            if current != common:
                rotations.append(current)
            current = _rot90(current)
        target = _pick(rng, rotations)
    elif relation == "same_area":
        area = 3 + rng.randrange(3)
        common = _pick(rng, _SHAPES_BY_AREA[area])
        target = _pick(
            rng,
            (
                shape
                for shape in _SHAPES_BY_AREA[area]
                if _d4_canonical(shape) != _d4_canonical(common)
            ),
        )
    elif relation == "smaller":
        common = _pick(rng, _SHAPES_BY_AREA[5])
        target = _pick(rng, _SHAPES_BY_AREA[3])
    else:
        common = _pick(rng, _SHAPES_BY_AREA[3])
        target = _pick(rng, _SHAPES_BY_AREA[5])
    if target == common:
        raise AssertionError("shape chooser produced a non-singleton target")
    return common, target


def _absolute(shape: Shape, top: int, left: int) -> tuple[Point, ...]:
    return tuple(sorted((top + row, left + col) for row, col in shape))


def _candidate_positions(shape: Shape, height: int, width: int) -> list[tuple[int, int]]:
    max_row = max(row for row, _ in shape)
    max_col = max(col for _, col in shape)
    # Give every object the same one-cell edge margin.  The singleton is not
    # identifiable merely because it is the only object that could be bordered.
    return [
        (top, left)
        for top in range(1, height - max_row - 1)
        for left in range(1, width - max_col - 1)
    ]


def _separated(cells: Iterable[Point], occupied: set[Point], clearance: int = 2) -> bool:
    for row, col in cells:
        for drow in range(-clearance, clearance + 1):
            for dcol in range(-clearance, clearance + 1):
                if (row + drow, col + dcol) in occupied:
                    return False
    return True


def _place_scene(
    height: int,
    width: int,
    common: Shape,
    target: Shape,
    target_rank: str,
    rng,
) -> list[list[int]]:
    target_positions = _candidate_positions(target, height, width)
    rng.shuffle(target_positions)
    common_positions = _candidate_positions(common, height, width)
    rng.shuffle(common_positions)

    for target_top, target_left in target_positions:
        target_cells = _absolute(target, target_top, target_left)
        target_anchor = min(target_cells)
        viable: list[tuple[Point, tuple[Point, ...]]] = []
        target_set = set(target_cells)
        for top, left in common_positions:
            cells = _absolute(common, top, left)
            if _separated(cells, target_set):
                viable.append((min(cells), cells))
        before = [item for item in viable if item[0] < target_anchor]
        after = [item for item in viable if item[0] > target_anchor]
        rng.shuffle(before)
        rng.shuffle(after)

        if target_rank == "first":
            first_pool, second_pool = after, after
        elif target_rank == "last":
            first_pool, second_pool = before, before
        else:
            first_pool, second_pool = before, after
        if not first_pool or not second_pool:
            continue

        for _, first_cells in first_pool[:80]:
            occupied = target_set | set(first_cells)
            for _, second_cells in second_pool[:80]:
                if second_cells == first_cells:
                    continue
                if not _separated(second_cells, occupied):
                    continue
                anchors = sorted((target_anchor, min(first_cells), min(second_cells)))
                if _TARGET_RANKS[anchors.index(target_anchor)] != target_rank:
                    continue
                grid = full_grid(height, width, 0)
                for row, col in target_cells + first_cells + second_cells:
                    grid[row][col] = 3
                return grid
    raise RuntimeError(
        f"could not place three separated objects in {height}x{width} "
        f"with target_rank={target_rank!r}"
    )


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size_options = _BAND_SIZES[difficulty]
    default_h, default_w = size_options[int(sample_index) % len(size_options)]
    height = _draw_int_or_default(ctx, overrides, "grid_h", default_h, 10, 16)
    width = _draw_int_or_default(ctx, overrides, "grid_w", default_w, 12, 18)
    relation = _draw_choice_or_default(
        ctx,
        overrides,
        "unique_relation",
        schedule_profile(seed, sample_index, difficulty),
        _RELATIONS,
    )
    default_rank = _TARGET_RANKS[int(sample_index) % len(_TARGET_RANKS)]
    target_rank = _draw_choice_or_default(
        ctx,
        overrides,
        "target_rank",
        default_rank,
        _TARGET_RANKS,
    )

    last_error: Exception | None = None
    for attempt in range(48):
        shape_rng = ctx.draw_rng(f"shapes|attempt={attempt}|relation={relation}")
        layout_rng = ctx.draw_rng(
            f"layout|attempt={attempt}|dims={height}x{width}|relation={relation}|rank={target_rank}"
        )
        try:
            common, target = _choose_shapes(shape_rng, relation)
            grid = _place_scene(height, width, common, target, target_rank, layout_rng)
        except (RuntimeError, ValueError) as exc:
            last_error = exc
            continue
        errors = self_check(
            grid,
            meta={
                "grid_h": height,
                "grid_w": width,
                "unique_relation": relation,
                "target_rank": target_rank,
            },
        )
        if errors:
            last_error = AssertionError("; ".join(errors))
            continue
        return grid
    raise RuntimeError(
        "could not generate a valid odd-one-out-border scene after 48 attempts"
    ) from last_error


# ---------------------------------------------------------------------------
# Task-local rival rules and semantic witnesses.
# ---------------------------------------------------------------------------


def _paint_border_for(grid: Any, cells: Iterable[Point]) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = [list(row) for row in values]
    border = _border_cells(tuple(cells), len(values), len(values[0]))
    if not border:
        return output
    for row, col in border:
        output[row][col] = 4
    return output


def _frequency_rival(grid: Any, key: Callable[[Shape], Any]) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    keyed = [key(_norm(cells)) for cells in components]
    counts = Counter(keyed)
    singletons = [index for index, value in enumerate(keyed) if counts[value] == 1]
    if len(singletons) != 1:
        return [list(row) for row in values]
    return _paint_border_for(values, components[singletons[0]])


def _rival_dihedral_frequency(grid: Any) -> list[list[int]]:
    return _frequency_rival(grid, _d4_canonical)


def _rival_unique_area(grid: Any) -> list[list[int]]:
    return _frequency_rival(grid, len)


def _rival_first_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    return _paint_border_for(values, components[0]) if components else values


def _rival_largest_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    if not components:
        return values
    target = min(components, key=lambda cells: (-len(cells), min(cells)))
    return _paint_border_for(values, target)


def _rival_smallest_object(grid: Any) -> list[list[int]]:
    values = _coerce_grid(grid)
    components = _components(values)
    if not components:
        return values
    target = min(components, key=lambda cells: (len(cells), min(cells)))
    return _paint_border_for(values, target)


def _analysis_ok(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _w_rotation_unique(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "rotated_pair")


def _w_same_area_unique(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "same_area")


def _w_target_not_first(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["target_rank"] != "first")


def _w_target_smaller(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "smaller")


def _w_target_larger(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["unique_relation"] == "larger")


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
    "target_not_first_refutes_first_object": _w_target_not_first,
    "smaller_target_refutes_largest_object": _w_target_smaller,
    "larger_target_refutes_smallest_object": _w_target_larger,
}

WITNESS_RIVALS = {
    "rotation_unique_refutes_dihedral_frequency": ["dihedral_frequency"],
    "same_area_unique_refutes_unique_area": ["unique_area"],
    "target_not_first_refutes_first_object": ["first_object"],
    "smaller_target_refutes_largest_object": ["largest_object"],
    "larger_target_refutes_smallest_object": ["smallest_object"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "dihedral_frequency": _rival_dihedral_frequency,
    "unique_area": _rival_unique_area,
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
            errors.append(f"demo {index} output does not border the exact-shape singleton")
            continue
        analyses.append(analysis)
        outputs.append(tuple(tuple(row) for row in actual))

    if len(analyses) == len(demos):
        relations = {item["unique_relation"] for item in analyses}
        if "rotated_pair" not in relations:
            errors.append("demonstrations do not refute dihedral-invariant shape frequency")
        if "same_area" not in relations:
            errors.append("demonstrations do not refute unique-area selection")
        if "smaller" not in relations:
            errors.append("demonstrations do not refute largest-object selection")
        if "larger" not in relations:
            errors.append("demonstrations do not refute smallest-object selection")
        if not any(item["target_rank"] != "first" for item in analyses):
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
