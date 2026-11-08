"""Canonical-profiled sampler for ARC task c3052979ff96.

The selected Racket rule is the output authority.  Inputs contain one connected
cyan (8) source object, one maroon (9) pivot, one control cell in 1..4, and
three or four unrelated objects in colors 5..7.  The control means identity,
clockwise quarter-turn, half-turn, or counter-clockwise quarter-turn around the
pivot; the transformed source cells are stamped red (2) over an unchanged copy
of the input.

The five-position curriculum schedule emits control codes {1,1,2,3,4}.  The
repeated identity example is deliberate: canonical data contains no code-1
example, so one identity demonstration must remain even when any pair is held
out as the query.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3052979ff96"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "a9dc0b2876d4"

SUMMARY = (
    "One connected color-8 source is rotated around the unique color-9 pivot. "
    "The unique control value 1,2,3,4 means identity, 90 degrees clockwise, "
    "180 degrees, or 90 degrees counter-clockwise. Stamp the transformed cells "
    "as color 2 while preserving the source, control, pivot, and unrelated "
    "color-5/6/7 objects except where a red stamp overlaps them."
)

INVARIANTS = [
    "the canvas is one of the four canonical dimension profiles",
    "exactly one connected 2..4-cell color-8 source object and one color-9 pivot",
    "exactly one control cell in {1,2,3,4}; every transformed source cell is in bounds",
    "three to five unrelated color-5/6/7 components are present and preserved by the rule",
    "ordinary draws use the canonical palette cardinality for their dimension profile",
]

GRID_PROFILES = ("11x13", "12x14", "13x13", "14x14")
_PROFILE_DIMS = {
    "11x13": (11, 13),
    "12x14": (12, 14),
    "13x13": (13, 13),
    "14x14": (14, 14),
}
_PROFILE_PALETTE_SIZE = {
    "11x13": 6,
    "12x14": 7,
    "13x13": 6,
    "14x14": 6,
}

# Exact normalized orientations.  IDs 0, 2 and 4 occur in the canonical data;
# the remaining connected 2..4-cell forms add lawful geometric variation.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
)
_SHAPE_TO_ID = {shape: index for index, shape in enumerate(_SHAPES)}

AXES = {
    "grid_profile": {
        "type": "str",
        "default": "five-position canonical-profile schedule",
        "valid": "11x13|12x14|13x13|14x14",
    },
    "code_value": {
        "type": "int",
        "default": "five-position schedule 1,2,1,3,4",
        "valid": "1..4",
    },
    "shape_id": {
        "type": "int",
        "default": "seed-shifted five-position schedule",
        "valid": "0..9",
    },
    "source_quadrant": {
        "type": "int",
        "default": "five-position schedule over all four strict quadrants",
        "valid": "0..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "five-position schedule over 3..4",
        "valid": "3..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))

_PROFILE_SCHEDULE = ("13x13", "12x14", "14x14", "11x13", "12x14")
_CODE_SCHEDULE = (1, 2, 1, 3, 4)
_QUADRANT_SCHEDULE = (0, 1, 2, 3, 0)
_DISTRACTOR_SCHEDULE = (3, 4, 3, 4, 3)
_SHAPE_OFFSETS = (0, 2, 4, 6, 8)
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}

Grid = list[list[int]]
Point = tuple[int, int]


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))

    if "grid_profile" in overrides:
        value = overrides["grid_profile"]
        if type(value) is not str:
            raise TypeError("grid_profile override must be a string")
        if value not in GRID_PROFILES:
            raise ValueError(f"grid_profile override must be one of {GRID_PROFILES}")
    ranges = {
        "code_value": (1, 4),
        "shape_id": (0, len(_SHAPES) - 1),
        "source_quadrant": (0, 3),
        "n_distractors": (3, 5),
    }
    for name, (low, high) in ranges.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"{name} override must be in {low}..{high}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the exact residue controlling the five-pair teaching schedule."""
    _validate_call(seed, sample_index, difficulty, {})
    return (sample_index + seed % LESSON_SCHEDULE_PERIOD + _DIFFICULTY_OFFSETS[difficulty]) % LESSON_SCHEDULE_PERIOD


def _draw_axis(ctx, label: str, legal: tuple[Any, ...], scheduled: Any) -> Any:
    options = legal if label in ctx.overrides else (scheduled,)
    return ctx.draw_choice(label, options)


def _rotate_point(pivot: Point, point: Point, code: int) -> Point:
    prow, pcol = pivot
    row, col = point
    drow, dcol = row - prow, col - pcol
    if code == 1:
        return prow + drow, pcol + dcol
    if code == 2:
        return prow + dcol, pcol - drow
    if code == 3:
        return prow - drow, pcol - dcol
    return prow - dcol, pcol + drow


def _strict_quadrant(cells: set[Point] | frozenset[Point], pivot: Point) -> int | None:
    prow, pcol = pivot
    tests = (
        all(row < prow and col < pcol for row, col in cells),
        all(row < prow and col > pcol for row, col in cells),
        all(row > prow and col > pcol for row, col in cells),
        all(row > prow and col < pcol for row, col in cells),
    )
    hits = [index for index, matched in enumerate(tests) if matched]
    return hits[0] if len(hits) == 1 else None


@lru_cache(maxsize=1024)
def _geometry_candidates(
    height: int,
    width: int,
    shape_id: int,
    code: int,
    quadrant: int,
) -> tuple[tuple[Point, tuple[Point, ...], tuple[Point, ...]], ...]:
    """Enumerate immutable lawful source/pivot placements for one exact request."""
    shape = _SHAPES[shape_id]
    shape_height = 1 + max(row for row, _col in shape)
    shape_width = 1 + max(col for _row, col in shape)
    # A full Cartesian override probe touches up to 640 geometry keys.  Keeping
    # every lawful placement would retain about one million nested tuples and
    # can push the checker into memory thrashing.  A deterministic reservoir
    # preserves broad positional support while bounding each cache entry.
    reservoir_limit = 64
    candidates: list[tuple[Point, tuple[Point, ...], tuple[Point, ...]]] = []
    seen = 0
    salt = (
        height * 1_000_003
        + width * 10_007
        + shape_id * 503
        + code * 37
        + quadrant
    )
    for anchor_row in range(height - shape_height + 1):
        for anchor_col in range(width - shape_width + 1):
            source = tuple((anchor_row + row, anchor_col + col) for row, col in shape)
            source_set = frozenset(source)
            for pivot_row in range(1, height - 1):
                for pivot_col in range(1, width - 1):
                    pivot = (pivot_row, pivot_col)
                    if _strict_quadrant(source_set, pivot) != quadrant:
                        continue
                    target = tuple(_rotate_point(pivot, point, code) for point in source)
                    if any(not (0 <= row < height and 0 <= col < width) for row, col in target):
                        continue
                    target_set = frozenset(target)
                    if pivot in target_set:
                        continue
                    if code != 1 and source_set & target_set:
                        continue
                    candidate = (pivot, source, target)
                    seen += 1
                    if len(candidates) < reservoir_limit:
                        candidates.append(candidate)
                        continue
                    # Stable reservoir replacement without Python's process-
                    # randomized hash() or any global random state.
                    mixed = (seen * 2_654_435_761 + salt * 2_246_822_519) & 0xFFFFFFFF
                    replacement = mixed % seen
                    if replacement < reservoir_limit:
                        candidates[replacement] = candidate
    return tuple(candidates)


def _distractor_components(grid: Grid) -> list[set[Point]]:
    found: list[set[Point]] = []
    for color in (5, 6, 7):
        found.extend(_components(grid, color))
    return found


_DISTRACTOR_SHAPES: tuple[tuple[Point, ...], ...] = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def _place_code(grid: Grid, code: int, blocked: set[Point], rng) -> Point:
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0 and (row, col) not in blocked
    ]
    if not candidates:
        raise RuntimeError("constructive placement left no location for the control cell")
    point = rng.choice(candidates)
    grid[point[0]][point[1]] = code
    return point


def _placement_candidates(grid: Grid, shape: tuple[Point, ...], color: int, blocked: set[Point]) -> list[tuple[Point, ...]]:
    height, width = len(grid), len(grid[0])
    shape_height = 1 + max(row for row, _col in shape)
    shape_width = 1 + max(col for _row, col in shape)
    candidates: list[tuple[Point, ...]] = []
    for anchor_row in range(height - shape_height + 1):
        for anchor_col in range(width - shape_width + 1):
            cells = tuple((anchor_row + row, anchor_col + col) for row, col in shape)
            cell_set = set(cells)
            if any(point in blocked or grid[point[0]][point[1]] != 0 for point in cells):
                continue
            touches_same = False
            for row, col in cells:
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    other = (row + drow, col + dcol)
                    if other in cell_set:
                        continue
                    if 0 <= other[0] < height and 0 <= other[1] < width and grid[other[0]][other[1]] == color:
                        touches_same = True
                        break
                if touches_same:
                    break
            if not touches_same:
                candidates.append(cells)
    return candidates


def _place_distractors(grid: Grid, profile: str, count: int, blocked: set[Point], rng) -> None:
    palette_count = 3 if profile == "12x14" else 2
    palette = tuple(sorted(rng.sample((5, 6, 7), palette_count)))
    colors = list(palette)
    while len(colors) < count:
        colors.append(rng.choice(palette))
    rng.shuffle(colors)

    # Prefer canonical-like object sizes while retaining a singleton fallback.
    preferred_shapes = (1, 2, 3, 4, 0, 1, 2, 0)
    for index, color in enumerate(colors):
        start = rng.randrange(len(preferred_shapes))
        shape_ids = [preferred_shapes[(start + offset) % len(preferred_shapes)] for offset in range(len(preferred_shapes))]
        # Preserve order while removing duplicate shape IDs.
        shape_ids = list(dict.fromkeys(shape_ids))
        placed = False
        for shape_id in shape_ids:
            candidates = _placement_candidates(grid, _DISTRACTOR_SHAPES[shape_id], color, blocked)
            if not candidates:
                continue
            cells = rng.choice(candidates)
            for row, col in cells:
                grid[row][col] = color
            placed = True
            break
        if not placed:
            raise RuntimeError(f"could not place distractor {index + 1}/{count}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; selected Racket remains authority."""
    _validate_call(seed, sample_index, difficulty, overrides)
    slot = schedule_profile(seed, sample_index, difficulty)
    scheduled_shape = ((seed // LESSON_SCHEDULE_PERIOD) + _SHAPE_OFFSETS[slot]) % len(_SHAPES)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_axis(ctx, "grid_profile", GRID_PROFILES, _PROFILE_SCHEDULE[slot])
    code = _draw_axis(ctx, "code_value", (1, 2, 3, 4), _CODE_SCHEDULE[slot])
    shape_id = _draw_axis(ctx, "shape_id", tuple(range(len(_SHAPES))), scheduled_shape)
    quadrant = _draw_axis(ctx, "source_quadrant", (0, 1, 2, 3), _QUADRANT_SCHEDULE[slot])
    n_distractors = _draw_axis(ctx, "n_distractors", (3, 4, 5), _DISTRACTOR_SCHEDULE[slot])

    height, width = _PROFILE_DIMS[profile]
    candidates = _geometry_candidates(height, width, shape_id, code, quadrant)
    if not candidates:
        raise ValueError(
            f"no lawful geometry for profile={profile}, shape_id={shape_id}, "
            f"code_value={code}, source_quadrant={quadrant}"
        )
    pivot, source, target = ctx.draw_rng("geometry").choice(candidates)

    grid = full_grid(height, width, 0)
    grid[pivot[0]][pivot[1]] = 9
    for row, col in source:
        grid[row][col] = 8
    target_set = set(target)
    _place_code(grid, code, target_set, ctx.draw_rng("control_position"))
    _place_distractors(grid, profile, n_distractors, target_set, ctx.draw_rng("distractors"))

    requested = {
        "grid_profile": profile,
        "code_value": code,
        "shape_id": shape_id,
        "source_quadrant": quadrant,
        "n_distractors": n_distractors,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise AssertionError(f"constructed axes {requested!r} observed as {observed!r}")
    findings = self_check(grid, difficulty=difficulty, meta=requested)
    if findings:
        raise AssertionError("constructed grid failed self_check: " + "; ".join(findings))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Grid, color: int) -> list[set[Point]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    found: list[set[Point]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + drow, col + dcol)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        found.append(component)
    found.sort(key=lambda cells: min(cells))
    return found


def _normalized_shape(cells: set[Point]) -> tuple[Point, ...]:
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def analyze_grid(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    profile = next((name for name, dims in _PROFILE_DIMS.items() if dims == (height, width)), None)
    if profile is None:
        errors.append(f"dimensions {height}x{width} are not a canonical profile")

    pivots = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 9
    ]
    code_cells = [
        (row, col, value)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if 1 <= value <= 4
    ]
    source_components = _components(normalized, 8)
    distractors = _distractor_components(normalized)
    palette = {value for row in normalized for value in row}

    if len(pivots) != 1:
        errors.append(f"expected exactly one color-9 pivot, found {len(pivots)}")
    if len(code_cells) != 1:
        errors.append(f"expected exactly one control cell in 1..4, found {len(code_cells)}")
    if len(source_components) != 1:
        errors.append(f"expected exactly one connected color-8 source object, found {len(source_components)}")
    source = source_components[0] if len(source_components) == 1 else set()
    if source and not 2 <= len(source) <= 4:
        errors.append(f"color-8 source must contain 2..4 cells, found {len(source)}")
    shape = _normalized_shape(source) if source else ()
    shape_id = _SHAPE_TO_ID.get(shape)
    if source and shape_id is None:
        errors.append(f"color-8 source shape {shape!r} is outside the declared shape catalog")
    if not 3 <= len(distractors) <= 5:
        errors.append(f"expected 3..5 unrelated color-5/6/7 components, found {len(distractors)}")

    allowed = {0, 5, 6, 7, 8, 9}
    if len(code_cells) == 1:
        allowed.add(code_cells[0][2])
    foreign = sorted(palette - allowed)
    if foreign:
        errors.append(f"input contains undeclared colors {foreign}")
    if profile is not None:
        expected_palette = _PROFILE_PALETTE_SIZE[profile]
        if len(palette) != expected_palette:
            errors.append(
                f"profile {profile} requires palette size {expected_palette}, found {len(palette)}"
            )

    pivot = pivots[0] if len(pivots) == 1 else None
    code = code_cells[0][2] if len(code_cells) == 1 else None
    target: tuple[Point, ...] = ()
    if pivot is not None and code is not None and source:
        target = tuple(_rotate_point(pivot, point, code) for point in sorted(source))
        out_of_bounds = [
            point
            for point in target
            if not (0 <= point[0] < height and 0 <= point[1] < width)
        ]
        if out_of_bounds:
            errors.append(f"rotated target leaves the grid at {out_of_bounds[:3]}")

    return {
        "errors": errors,
        "grid": normalized,
        "height": height,
        "width": width,
        "grid_profile": profile,
        "palette": palette,
        "pivot": pivot,
        "code": code,
        "code_cell": code_cells[0][:2] if len(code_cells) == 1 else None,
        "source": source,
        "shape": shape,
        "shape_id": shape_id,
        "source_quadrant": _strict_quadrant(source, pivot) if source and pivot is not None else None,
        "target": target,
        "distractors": distractors,
        "n_distractors": len(distractors),
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = analyze_grid(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_profile": analysis["grid_profile"],
        "code_value": analysis["code"],
        "shape_id": analysis["shape_id"],
        "source_quadrant": analysis["source_quadrant"],
        "n_distractors": analysis["n_distractors"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = analyze_grid(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    analysis = analyze_grid(grid)
    if analysis["n_distractors"] not in (3, 4):
        return [
            "strict canonical-profile inputs contain three or four unrelated objects, "
            f"found {analysis['n_distractors']}"
        ]
    return []


def _core_parts(grid: Any) -> tuple[Grid, set[Point], Point, int]:
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError(errors[0])
    normalized = [list(row) for row in grid]
    source_components = _components(normalized, 8)
    pivots = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 9
    ]
    codes = [
        value
        for values in normalized
        for value in values
        if 1 <= value <= 4
    ]
    if len(source_components) != 1:
        raise ValueError(f"expected one color-8 source object, found {len(source_components)}")
    if len(pivots) != 1:
        raise ValueError(f"expected one color-9 pivot, found {len(pivots)}")
    if len(codes) != 1:
        raise ValueError(f"expected one control cell, found {len(codes)}")
    return normalized, source_components[0], pivots[0], codes[0]


def _apply_rotation(grid: Any, *, effective_code: int | None = None, strip_distractors: bool = False) -> Grid:
    normalized, source, pivot, code = _core_parts(grid)
    if effective_code is not None:
        code = effective_code
    output = [row[:] for row in normalized]
    if strip_distractors:
        for row, values in enumerate(output):
            for col, value in enumerate(values):
                if value in (5, 6, 7):
                    output[row][col] = 0
    for point in sorted(source):
        row, col = _rotate_point(pivot, point, code)
        if 0 <= row < len(output) and 0 <= col < len(output[0]):
            output[row][col] = 2
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; selected Racket remains authority."""
    return _apply_rotation(grid)


def _rival_code_one_is_clockwise(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: incorrectly maps the unseen code 1 to code 2."""
    _normalized, _source, _pivot, code = _core_parts(grid)
    return _apply_rotation(grid, effective_code=2 if code == 1 else code)


def _rival_strip_unrelated_objects(grid: Grid) -> Grid:
    """Wrong shortcut exposed by every canonical and generated distractor scene."""
    return _apply_rotation(grid, strip_distractors=True)


def _has_identity_code(grid: Any) -> bool:
    try:
        return _core_parts(grid)[3] == 1
    except (TypeError, ValueError):
        return False


def _has_preserved_unrelated_objects(grid: Any) -> bool:
    analysis = analyze_grid(grid)
    return not analysis.get("errors") and analysis.get("n_distractors", 0) > 0


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "code_one_is_clockwise": _rival_code_one_is_clockwise,
    "strip_unrelated_objects": _rival_strip_unrelated_objects,
}
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {
    "code_one_is_clockwise": _rival_code_one_is_clockwise,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "identity_code": _has_identity_code,
    "preserved_unrelated_objects": _has_preserved_unrelated_objects,
}
WITNESS_RIVALS = {
    "identity_code": ["code_one_is_clockwise"],
    "preserved_unrelated_objects": ["strip_unrelated_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared rival survives demos but changes query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} is outside the grammar: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Small malformed scenes retained for validator regression probes."""
    base = generate(910001, 1)
    fixtures: list[tuple[str, Grid]] = []

    extra_pivot = [row[:] for row in base]
    point = next(
        (row, col)
        for row, values in enumerate(extra_pivot)
        for col, value in enumerate(values)
        if value == 0
    )
    extra_pivot[point[0]][point[1]] = 9
    fixtures.append(("extra_pivot", extra_pivot))

    missing_source = [row[:] for row in base]
    for row, values in enumerate(missing_source):
        for col, value in enumerate(values):
            if value == 8:
                missing_source[row][col] = 0
    fixtures.append(("missing_source", missing_source))

    missing_distractors = [row[:] for row in base]
    for row, values in enumerate(missing_distractors):
        for col, value in enumerate(values):
            if value in (5, 6, 7):
                missing_distractors[row][col] = 0
    fixtures.append(("missing_distractors", missing_distractors))
    return fixtures
