"""Reviewed generator for ARC task 55312177dae6.

A zero-background grid contains three or four isolated blue objects.  Exactly
one translation-normalized shape class occurs twice *up to rotation*; the two
copies have different orientations.  Every other object belongs to its own
rotation class.  The answer is the lexicographically least normalized rotation
of the repeated class, cropped and recolored cyan.

The four-profile curriculum supplies direct counterexamples to tempting rules
that select the first/largest/smallest object, require an exact-orientation
repeat, identify shapes up to reflection, or select the modal object area.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "55312177dae6"
TASK_ID = "55312177dae6"
VERSION = "4.0.0"
RULE_HASH = "39919c9ecf3d"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
# All 18 four-orientation free polyomino classes of area 3..5 are reachable.
EXPECTED_OUTPUT_CODOMAIN = 18

SUMMARY = (
    "A 0-background grid contains three or four separated blue objects. "
    "Exactly two objects share one shape up to rotation, in visibly different "
    "orientations; every distractor has a unique rotational shape class. "
    "Normalize all rotations, select the repeated class, render its "
    "lexicographically least rotation alone in cyan, and crop to its bbox."
)

INVARIANTS = [
    "background is 0 and every foreground cell is blue (1)",
    "there are exactly two copies of one rotation-normalized shape class",
    "the matching copies have different normalized orientations",
    "every distractor belongs to a distinct singleton rotation class",
    "all objects are 4-connected and separated even under 8-connectivity",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "linked schedule", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "linked schedule", "valid": "10..18"},
    "n_distractors": {"type": "int", "default": "2", "valid": "1..2"},
    "target_area": {"type": "int", "default": "profile-linked", "valid": "3..5"},
    "match_rotation": {
        "type": "int",
        "default": "cycles through quarter-turn offsets",
        "valid": "1..3",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "reflection_and_order",
    "target_largest",
    "target_smallest",
    "area_frequency_tie",
)

_SIZE_PROFILES = ((8, 10), (9, 11), (10, 12), (11, 13), (13, 15), (16, 18))
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}

Point = tuple[int, int]
Shape = tuple[Point, ...]


def _norm(cells: Iterable[Point]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _rot90(shape: Shape) -> Shape:
    shape = _norm(shape)
    if not shape:
        return ()
    height = max(row for row, _ in shape) + 1
    return _norm((col, height - 1 - row) for row, col in shape)


def _rotate(shape: Shape, turns: int) -> Shape:
    current = _norm(shape)
    for _ in range(turns % 4):
        current = _rot90(current)
    return current


def _rotation_forms(shape: Shape) -> tuple[Shape, ...]:
    forms: list[Shape] = []
    current = _norm(shape)
    for _ in range(4):
        if current not in forms:
            forms.append(current)
        current = _rot90(current)
    return tuple(forms)


def _canonical_rotation(shape: Shape) -> Shape:
    return min(_rotation_forms(shape))


def _reflect(shape: Shape) -> Shape:
    shape = _norm(shape)
    if not shape:
        return ()
    width = max(col for _, col in shape) + 1
    return _norm((row, width - 1 - col) for row, col in shape)


def _dihedral_canonical(shape: Shape) -> Shape:
    return min(_canonical_rotation(shape), _canonical_rotation(_reflect(shape)))


def _fixed_polyominoes(min_size: int = 2, max_size: int = 5) -> tuple[Shape, ...]:
    """Enumerate oriented, 4-connected shapes with at most a 4x4 bbox."""
    level: set[Shape] = {((0, 0),)}
    collected: set[Shape] = set()
    for size in range(1, max_size + 1):
        if size >= min_size:
            collected.update(
                shape
                for shape in level
                if max(row for row, _ in shape) < 4
                and max(col for _, col in shape) < 4
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
    return tuple(sorted(collected, key=lambda item: (len(item), item)))


_FIXED_SHAPES = _fixed_polyominoes()
_ROTATION_KEYS = tuple(sorted({_canonical_rotation(shape) for shape in _FIXED_SHAPES}, key=lambda item: (len(item), item)))
_KEYS_BY_AREA = {
    area: tuple(key for key in _ROTATION_KEYS if len(key) == area)
    for area in range(2, 6)
}
_TARGET_KEYS_BY_AREA = {
    area: tuple(key for key in _KEYS_BY_AREA[area] if len(_rotation_forms(key)) == 4)
    for area in range(3, 6)
}
_REFLECTION_TARGETS_BY_AREA = {
    area: tuple(
        key
        for key in _TARGET_KEYS_BY_AREA[area]
        if _canonical_rotation(_reflect(key)) != key
        and key > _canonical_rotation(_reflect(key))
    )
    for area in range(3, 6)
}


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid must be a list or tuple")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                result.append([int(value) for value in row])
            except ValueError as exc:
                raise ValueError("grid strings must contain decimal digits") from exc
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _components(grid: list[list[int]]) -> list[tuple[Point, ...]]:
    remaining = {
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0
    }
    found: list[tuple[Point, ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    cells.append(neighbor)
        found.append(tuple(sorted(cells)))
    return sorted(found, key=lambda cells: cells[0])


def _turn_index(shape: Shape, canonical: Shape) -> int:
    current = canonical
    for turn in range(4):
        if current == _norm(shape):
            return turn
        current = _rot90(current)
    raise ValueError("shape is not rotation-equivalent to the canonical form")


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
    if any(type(value) is not int or not 0 <= value <= 9 for row in values for value in row):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}
    wrong = [
        (row, col, value)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value not in (0, 1)
    ]
    if wrong:
        errors.append(f"foreground must use only blue (1), found {wrong[:3]!r}")

    components = _components(values)
    if len(components) not in (3, 4):
        errors.append("expected exactly three or four blue objects")
    if any(not 2 <= len(cells) <= 8 for cells in components):
        errors.append("each object must contain 2..8 cells")

    owner: dict[Point, int] = {}
    for index, cells in enumerate(components):
        owner.update({cell: index for cell in cells})
    touching: set[tuple[int, int]] = set()
    for (row, col), index in owner.items():
        for drow in (-1, 0, 1):
            for dcol in (-1, 0, 1):
                other = owner.get((row + drow, col + dcol))
                if other is not None and other != index:
                    touching.add(tuple(sorted((index, other))))
    if touching:
        errors.append(f"objects must be separated under 8-connectivity, found {sorted(touching)!r}")

    signatures = tuple(_norm(cells) for cells in components)
    rotation_keys = tuple(_canonical_rotation(shape) for shape in signatures)
    counts = Counter(rotation_keys)
    repeated = [key for key, count in counts.items() if count == 2]
    other_bad_counts = [count for count in counts.values() if count not in (1, 2)]
    if len(repeated) != 1:
        errors.append("expected exactly one rotation-normalized class occurring twice")
    if other_bad_counts:
        errors.append(f"rotation classes must occur once or twice, got {sorted(other_bad_counts)!r}")
    if counts and sum(1 for count in counts.values() if count == 1) < 1:
        errors.append("expected at least one distractor rotation class")

    target_key = repeated[0] if len(repeated) == 1 else ()
    target_indices = tuple(index for index, key in enumerate(rotation_keys) if key == target_key) if target_key else ()
    turns: tuple[int, ...] = ()
    match_rotation = None
    if len(target_indices) == 2:
        try:
            turns = tuple(_turn_index(signatures[index], target_key) for index in target_indices)
            match_rotation = (turns[1] - turns[0]) % 4
            if match_rotation == 0:
                errors.append("the matching objects must have different normalized orientations")
        except ValueError as exc:
            errors.append(str(exc))

    distractor_indices = tuple(index for index in range(len(components)) if index not in target_indices)
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "components": tuple(components),
        "signatures": signatures,
        "rotation_keys": rotation_keys,
        "counts": counts,
        "target_key": target_key,
        "target_indices": target_indices,
        "target_turns": turns,
        "match_rotation": match_rotation,
        "target_area": len(target_key),
        "distractor_indices": distractor_indices,
        "n_distractors": len(distractor_indices),
        "object_top_lefts": tuple(min(cells) for cells in components),
        "areas": tuple(len(cells) for cells in components),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_distractors": analysis["n_distractors"],
        "target_area": analysis["target_area"],
        "match_rotation": analysis["match_rotation"],
    }
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
        "n_distractors": analysis["n_distractors"],
        "target_area": analysis["target_area"],
        "match_rotation": analysis["match_rotation"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if not 8 <= analysis["height"] <= 16 or not 10 <= analysis["width"] <= 18:
        errors.append("grid dimensions fall outside the canonical-linked envelope")
    if analysis["target_area"] not in (3, 4, 5):
        errors.append("the repeated target must have area 3..5")
    if any(not 2 <= area <= 5 for area in analysis["areas"]):
        errors.append("canonical-linked objects have area 2..5")
    if analysis["n_distractors"] not in (1, 2):
        errors.append("canonical-linked scenes use one or two distractors")
    return errors


def _shape_grid(shape: Shape) -> list[list[int]]:
    shape = _norm(shape)
    if not shape:
        return []
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    output = full_grid(height, width, 0)
    for row, col in shape:
        output[row][col] = 8
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid repeated-rotation scene: " + "; ".join(analysis["errors"]))
    return _shape_grid(analysis["target_key"])


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(key for key in overrides if key not in AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    bounds = {
        "grid_h": (8, 16),
        "grid_w": (10, 18),
        "n_distractors": (1, 2),
        "target_area": (3, 5),
        "match_rotation": (1, 3),
    }
    for name, (lower, upper) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lower <= value <= upper:
            raise ValueError(f"{name} must be in [{lower}, {upper}]")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_int_or_default(ctx, overrides: dict[str, Any], name: str, default: int, lower: int, upper: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lower, upper)
    return ctx.draw_int(name, default, default)


def _pick(rng, choices: Iterable[Shape]) -> Shape:
    options = tuple(sorted(set(choices), key=lambda item: (len(item), item)))
    if not options:
        raise ValueError("shape constraints left no candidates")
    return options[rng.randrange(len(options))]


def _preferred_distractors(profile: str, target_key: Shape) -> tuple[Shape, ...]:
    target_area = len(target_key)
    all_other = tuple(key for key in _ROTATION_KEYS if key != target_key)
    if profile == "reflection_and_order":
        reflected = _canonical_rotation(_reflect(target_key))
        preferred = [reflected] if reflected != target_key else []
        preferred.extend(key for key in all_other if key != reflected)
        return tuple(preferred)
    if profile == "target_largest":
        return tuple(key for key in all_other if len(key) < target_area) + all_other
    if profile == "target_smallest":
        return tuple(key for key in all_other if len(key) > target_area) + all_other
    if profile == "area_frequency_tie":
        larger_same_band = tuple(key for key in all_other if len(key) > target_area)
        same_area = tuple(key for key in all_other if len(key) == target_area)
        return larger_same_band + same_area + all_other
    return all_other


def _choose_shapes(rng, profile: str, target_area: int, n_distractors: int) -> tuple[Shape, list[Shape]]:
    target_candidates = _TARGET_KEYS_BY_AREA[target_area]
    if profile == "reflection_and_order" and _REFLECTION_TARGETS_BY_AREA[target_area]:
        target_candidates = _REFLECTION_TARGETS_BY_AREA[target_area]
    target_key = _pick(rng, target_candidates)

    preferred = list(_preferred_distractors(profile, target_key))
    distractors: list[Shape] = []
    if profile == "reflection_and_order":
        reflected = _canonical_rotation(_reflect(target_key))
        if reflected != target_key:
            distractors.append(reflected)
    while len(distractors) < n_distractors:
        candidates = [
            key for key in preferred
            if key != target_key and key not in distractors
        ]
        if not candidates:
            raise RuntimeError("not enough distinct distractor rotation classes")
        distractors.append(_pick(rng, candidates))
    return target_key, distractors


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
    return all(
        (row + drow, col + dcol) not in occupied
        for row, col in absolute
        for drow in (-1, 0, 1)
        for dcol in (-1, 0, 1)
    )


def _candidate_positions(
    shape: Shape,
    height: int,
    width: int,
    occupied: set[Point],
    after_anchor: Point | None,
    rng,
) -> list[tuple[int, int, Point]]:
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    candidates: list[tuple[int, int, Point]] = []
    for top in range(height - shape_height + 1):
        for left in range(width - shape_width + 1):
            absolute = tuple((top + row, left + col) for row, col in shape)
            anchor = min(absolute)
            if after_anchor is not None and anchor <= after_anchor:
                continue
            if _fits_with_clearance(occupied, shape, top, left, height, width):
                candidates.append((top, left, anchor))
    rng.shuffle(candidates)
    return candidates


def _search_placements(
    specs: list[tuple[str, Shape]],
    index: int,
    height: int,
    width: int,
    occupied: set[Point],
    first_anchor: Point,
    target_a_anchor: Point | None,
    rng,
    placed: list[tuple[Shape, int, int]],
) -> list[tuple[Shape, int, int]] | None:
    if index == len(specs):
        return list(placed)
    label, shape = specs[index]
    after = target_a_anchor if label == "target_b" else first_anchor
    for top, left, anchor in _candidate_positions(
        shape, height, width, occupied, after, rng
    ):
        cells = {(top + row, left + col) for row, col in shape}
        occupied.update(cells)
        placed.append((shape, top, left))
        result = _search_placements(
            specs,
            index + 1,
            height,
            width,
            occupied,
            first_anchor,
            anchor if label == "target_a" else target_a_anchor,
            rng,
            placed,
        )
        if result is not None:
            return result
        placed.pop()
        occupied.difference_update(cells)
    return None


def _place_scene(
    height: int,
    width: int,
    target_key: Shape,
    distractor_keys: list[Shape],
    match_rotation: int,
    rng,
) -> list[list[int]]:
    base_turns = list(range(4))
    rng.shuffle(base_turns)
    first_turns = list(range(len(_rotation_forms(distractor_keys[0]))))
    rng.shuffle(first_turns)
    second_turns = [0]
    if len(distractor_keys) == 2:
        second_turns = list(range(len(_rotation_forms(distractor_keys[1]))))
        rng.shuffle(second_turns)

    # Exhaust the small orientation space.  Placement itself is exact
    # backtracking, so no retry cap or invalid fallback can escape the contract.
    for base_turn in base_turns:
        target_a = _rotate(target_key, base_turn)
        target_b = _rotate(target_key, base_turn + match_rotation)
        for first_turn in first_turns:
            first_distractor = _rotate(distractor_keys[0], first_turn)
            first_height = max(row for row, _ in first_distractor) + 1
            first_width = max(col for _, col in first_distractor) + 1
            if first_height > height or first_width > width:
                continue
            first_top = 0
            first_left = 0
            first_cells = {
                (first_top + row, first_left + col)
                for row, col in first_distractor
            }
            first_anchor = min(first_cells)
            for second_turn in second_turns:
                specs: list[tuple[str, Shape]] = [
                    ("target_a", target_a),
                    ("target_b", target_b),
                ]
                if len(distractor_keys) == 2:
                    specs.append(("distractor", _rotate(distractor_keys[1], second_turn)))
                result = _search_placements(
                    specs,
                    0,
                    height,
                    width,
                    set(first_cells),
                    first_anchor,
                    None,
                    rng,
                    [],
                )
                if result is None:
                    continue
                grid = full_grid(height, width, 0)
                all_placements = [(first_distractor, first_top, first_left)] + result
                for shape, top, left in all_placements:
                    for row, col in shape:
                        grid[top + row][left + col] = 1
                return grid
    raise RuntimeError(
        f"could not place {2 + len(distractor_keys)} separated objects "
        f"in {height}x{width}"
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
    profile = schedule_profile(seed, sample_index, difficulty)
    size_index = (sample_index + _BAND_OFFSETS[difficulty]) % len(_SIZE_PROFILES)
    default_h, default_w = _SIZE_PROFILES[size_index]
    height = _draw_int_or_default(ctx, overrides, "grid_h", default_h, 8, 16)
    width = _draw_int_or_default(ctx, overrides, "grid_w", default_w, 10, 18)
    n_distractors = _draw_int_or_default(ctx, overrides, "n_distractors", 2, 1, 2)
    default_area = {
        "reflection_and_order": 4,
        "target_largest": 5,
        "target_smallest": 3,
        "area_frequency_tie": 4,
    }[profile]
    target_area = _draw_int_or_default(ctx, overrides, "target_area", default_area, 3, 5)
    default_rotation = 1 + (sample_index % 3)
    match_rotation = _draw_int_or_default(ctx, overrides, "match_rotation", default_rotation, 1, 3)

    shape_rng = ctx.draw_rng(
        f"shapes|profile={profile}|target_area={target_area}|distractors={n_distractors}"
    )
    layout_rng = ctx.draw_rng(
        f"layout|profile={profile}|dims={height}x{width}|rotation={match_rotation}"
    )
    target_key, distractor_keys = _choose_shapes(
        shape_rng, profile, target_area, n_distractors
    )
    grid = _place_scene(
        height, width, target_key, distractor_keys, match_rotation, layout_rng
    )
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_distractors": n_distractors,
        "target_area": target_area,
        "match_rotation": match_rotation,
    }
    errors = self_check(grid, meta=requested)
    if errors:
        raise AssertionError("generated invalid repeated-rotation scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-local rival rules and semantic witnesses.
# ---------------------------------------------------------------------------


def _blank_output() -> list[list[int]]:
    return [[0]]


def _safe_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _rival_first_component(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis or not analysis["components"]:
        return _blank_output()
    return _shape_grid(_canonical_rotation(analysis["signatures"][0]))


def _rival_largest_component(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis:
        return _blank_output()
    index = min(
        range(len(analysis["components"])),
        key=lambda idx: (-analysis["areas"][idx], analysis["object_top_lefts"][idx]),
    )
    return _shape_grid(_canonical_rotation(analysis["signatures"][index]))


def _rival_smallest_component(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis:
        return _blank_output()
    index = min(
        range(len(analysis["components"])),
        key=lambda idx: (analysis["areas"][idx], analysis["object_top_lefts"][idx]),
    )
    return _shape_grid(_canonical_rotation(analysis["signatures"][index]))


def _rival_exact_repeat(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis:
        return _blank_output()
    counts = Counter(analysis["signatures"])
    repeated = [shape for shape, count in counts.items() if count >= 2]
    return _shape_grid(min(repeated)) if repeated else _blank_output()


def _rival_dihedral_repeat(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis:
        return _blank_output()
    keys = [_dihedral_canonical(shape) for shape in analysis["signatures"]]
    counts = Counter(keys)
    repeated = [key for key, count in counts.items() if count >= 2]
    return _shape_grid(min(repeated)) if repeated else _blank_output()


def _rival_modal_area(grid: Any) -> list[list[int]]:
    analysis = _safe_analysis(grid)
    if not analysis:
        return _blank_output()
    area_counts = Counter(analysis["areas"])
    chosen_area = max(area_counts, key=lambda area: (area_counts[area], area))
    index = next(index for index, area in enumerate(analysis["areas"]) if area == chosen_area)
    return _shape_grid(_canonical_rotation(analysis["signatures"][index]))


def _rival_disagrees(rival: Callable[[Any], list[list[int]]], grid: Any) -> bool:
    analysis = _safe_analysis(grid)
    return bool(analysis and rival(grid) != rule_mirror(grid))


def _w_reflection_trap(grid: Any) -> bool:
    return _rival_disagrees(_rival_dihedral_repeat, grid)


def _w_target_not_first(grid: Any) -> bool:
    analysis = _safe_analysis(grid)
    return bool(analysis and analysis["target_indices"] and analysis["target_indices"][0] != 0)


def _w_target_not_largest(grid: Any) -> bool:
    analysis = _safe_analysis(grid)
    return bool(analysis and analysis["target_area"] < max(analysis["areas"]))


def _w_target_not_smallest(grid: Any) -> bool:
    analysis = _safe_analysis(grid)
    return bool(analysis and analysis["target_area"] > min(analysis["areas"]))


def _w_rotation_not_exact(grid: Any) -> bool:
    return _rival_disagrees(_rival_exact_repeat, grid)


def _w_area_frequency_trap(grid: Any) -> bool:
    return _rival_disagrees(_rival_modal_area, grid)


SEMANTIC_RIVALS = {
    "first_component": _rival_first_component,
    "largest_component": _rival_largest_component,
    "smallest_component": _rival_smallest_component,
    "exact_orientation_repeat": _rival_exact_repeat,
    "dihedral_repeat": _rival_dihedral_repeat,
    "modal_area": _rival_modal_area,
}

SEMANTIC_WITNESSES = {
    "reflection_trap_refutes_dihedral_repeat": _w_reflection_trap,
    "target_not_first_refutes_first_component": _w_target_not_first,
    "target_not_largest_refutes_largest_component": _w_target_not_largest,
    "target_not_smallest_refutes_smallest_component": _w_target_not_smallest,
    "rotated_pair_refutes_exact_orientation_repeat": _w_rotation_not_exact,
    "area_frequency_tie_refutes_modal_area": _w_area_frequency_trap,
}

WITNESS_RIVALS = {
    "reflection_trap_refutes_dihedral_repeat": ["dihedral_repeat"],
    "target_not_first_refutes_first_component": ["first_component"],
    "target_not_largest_refutes_largest_component": ["largest_component"],
    "target_not_smallest_refutes_smallest_component": ["smallest_component"],
    "rotated_pair_refutes_exact_orientation_repeat": ["exact_orientation_repeat"],
    "area_frequency_tie_refutes_modal_area": ["modal_area"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "first_component": _rival_first_component,
    "modal_area": _rival_modal_area,
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require a four-demo window to distinguish every declared rival rule."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    valid_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed: {analysis['errors'][:2]!r}")
            continue
        try:
            output = _coerce_grid(pair["output"])
        except ValueError as exc:
            errors.append(f"demo {index} output is malformed: {exc}")
            continue
        if output != rule_mirror(pair["input"]):
            errors.append(f"demo {index} output does not select the repeated rotation class")
            continue
        valid_pairs.append(pair)

    if len(valid_pairs) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if not any(rival(pair["input"]) != pair["output"] for pair in valid_pairs):
                errors.append(f"demonstrations do not distinguish rival rule {name!r}")
        output_keys = {
            tuple(tuple(row) for row in pair["output"])
            for pair in valid_pairs
        }
        if len(output_keys) < 3:
            errors.append("demonstration answers vary too little for a fixed-output shortcut")
        size_keys = {
            (len(pair["input"]), len(pair["input"][0]))
            for pair in valid_pairs
        }
        if len(size_keys) < 3:
            errors.append("demonstrations vary too little in grid size")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    elif _analyze(query["input"]).get("errors"):
        errors.append("query input is malformed")
    return errors
