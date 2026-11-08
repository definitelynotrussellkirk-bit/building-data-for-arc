"""Source-bound generator for ARC task ``f151fbd31cb2``.

The input contains two singleton keys and several disconnected GREEN objects:

* shape key 1 selects L-triominoes; shape key 4 selects plus-pentominoes;
* color key 2, 6, or 8 supplies the replacement color;
* every object in the selected family is recolored and every other cell is
  preserved.

The canonical examples accidentally make the selected family the more numerous
(and larger-area) family.  The natural three-slot teaching schedule includes a
selected-minority case so those two answer-equivalent canonical shortcuts cannot
survive every three consecutive examples.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f151fbd31cb2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "33294c3c6e8b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A singleton shape key (1=L, 4=plus) chooses one of two GREEN object "
    "families, while a singleton color key (2/6/8) gives the replacement "
    "color. Recolor every object of the selected family and preserve the "
    "other family. A cyclic three-profile curriculum includes selected-family "
    "minority counterexamples to the canonical majority-family shortcut."
)

INVARIANTS = [
    "the background is color 0 and all object cells begin as color 3",
    "exactly one singleton shape key is present: 1 selects L, 4 selects plus",
    "exactly one singleton color key is present: one of 2, 6, or 8",
    "there are one or two disconnected objects from each family",
    "the output recolors exactly the family selected by the shape key",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled / difficulty-aware", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled / difficulty-aware", "valid": "11..20"},
    "shape_key": {"type": "int", "default": "rng 1|4", "valid": "1|4"},
    "color_key": {"type": "int", "default": "rng 2|6|8", "valid": "2|6|8"},
    "n_l": {"type": "int", "default": "scheduled 1|2", "valid": "1|2"},
    "n_plus": {"type": "int", "default": "scheduled 1|2", "valid": "1|2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_majority",
    "selected_minority",
    "balanced",
)

_SHAPE_KEYS = (1, 4)
_COLOR_KEYS = (2, 6, 8)
_L_ORIENTS = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_L_NORMALIZED = frozenset(_L_ORIENTS)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SIZES = ((9, 11), (10, 12), (11, 12))
_ALLOWED_COLORS = frozenset((0, 1, 2, 3, 4, 6, 8))
_AXIS_DOMAINS = {
    "grid_h": tuple(range(9, 19)),
    "grid_w": tuple(range(11, 21)),
    "shape_key": _SHAPE_KEYS,
    "color_key": _COLOR_KEYS,
    "n_l": (1, 2),
    "n_plus": (1, 2),
}
_DIFFICULTY_SIZES = {
    "easy": ((9, 12), (11, 14)),
    "medium": ((11, 16), (13, 18)),
    "hard": ((14, 18), (16, 20)),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic curriculum slot for one natural sample."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"override {name!r} must be an integer, got {type(value).__name__}")
        if value not in _AXIS_DOMAINS[name]:
            raise ValueError(
                f"override {name!r}={value!r} is outside declared domain {_AXIS_DOMAINS[name]!r}"
            )


def _axis_choice(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    """Record a scheduled default while preserving the full exact override domain."""
    options: Iterable[int]
    if name in overrides and overrides[name] is not None:
        options = _AXIS_DOMAINS[name]
    else:
        options = (default,)
    return int(ctx.draw_choice(name, tuple(options)))


def _default_size(ctx, profile: str, difficulty: str) -> tuple[int, int]:
    if profile in ("canonical_majority", "selected_minority"):
        return ctx.draw_rng("canonical_size_default").choice(_CANONICAL_SIZES)
    (h_lo, h_hi), (w_lo, w_hi) = _DIFFICULTY_SIZES[difficulty]
    rng = ctx.draw_rng("broad_size_default")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _default_counts(profile: str, shape_key: int) -> tuple[int, int]:
    selected_is_l = shape_key == 1
    if profile == "canonical_majority":
        selected, other = 2, 1
    elif profile == "selected_minority":
        selected, other = 1, 2
    else:
        selected = other = 2
    return (selected, other) if selected_is_l else (other, selected)


def _paint(grid: list[list[int]], top: int, left: int, cells: Iterable[tuple[int, int]], color: int) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _zones(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Four isolated quadrants, separated by one blank row and one blank column."""
    split_r = height // 2
    split_c = width // 2
    row_ranges = ((0, split_r), (split_r + 1, height))
    col_ranges = ((0, split_c), (split_c + 1, width))
    return tuple((r0, r1, c0, c1) for r0, r1 in row_ranges for c0, c1 in col_ranges)


def _place_objects(
    grid: list[list[int]],
    ctx,
    n_l: int,
    n_plus: int,
) -> None:
    object_specs: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    orient_rng = ctx.draw_rng("l_orientations")
    object_specs.extend(("L", orient_rng.choice(_L_ORIENTS)) for _ in range(n_l))
    object_specs.extend(("PLUS", _PLUS) for _ in range(n_plus))

    assignment_rng = ctx.draw_rng("object_assignment")
    assignment_rng.shuffle(object_specs)
    slots = list(_zones(len(grid), len(grid[0])))
    assignment_rng.shuffle(slots)

    position_rng = ctx.draw_rng("object_positions")
    for (_, cells), (r0, r1, c0, c1) in zip(object_specs, slots):
        obj_h = max(row for row, _ in cells) + 1
        obj_w = max(col for _, col in cells) + 1
        top = position_rng.randint(r0, r1 - obj_h)
        left = position_rng.randint(c0, c1 - obj_w)
        _paint(grid, top, left, cells, 3)


def _place_keys(grid: list[list[int]], ctx, shape_key: int, color_key: int) -> None:
    free = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    ]
    key_cells = ctx.draw_rng("key_positions").sample(free, 2)
    (shape_r, shape_c), (color_r, color_c) = key_cells
    grid[shape_r][shape_c] = shape_key
    grid[color_r][color_c] = color_key


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; the pinned Racket rule owns output."""
    _validate_call(seed, sample_index, difficulty, overrides)
    difficulty_name = "medium" if difficulty is None else difficulty
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _default_size(ctx, profile, difficulty_name)
    grid_h = _axis_choice(ctx, overrides, "grid_h", default_h)
    grid_w = _axis_choice(ctx, overrides, "grid_w", default_w)
    default_shape_key = ctx.draw_rng("shape_key_default").choice(_SHAPE_KEYS)
    default_color_key = ctx.draw_rng("color_key_default").choice(_COLOR_KEYS)
    shape_key = _axis_choice(ctx, overrides, "shape_key", default_shape_key)
    color_key = _axis_choice(ctx, overrides, "color_key", default_color_key)
    default_n_l, default_n_plus = _default_counts(profile, shape_key)
    n_l = _axis_choice(ctx, overrides, "n_l", default_n_l)
    n_plus = _axis_choice(ctx, overrides, "n_plus", default_n_plus)

    grid = full_grid(grid_h, grid_w, 0)
    _place_objects(grid, ctx, n_l, n_plus)
    _place_keys(grid, ctx, shape_key, color_key)
    findings = self_check(grid)
    if findings:  # deterministic construction: this is an internal invariant failure
        raise RuntimeError(f"constructed invalid f151fbd31cb2 grid: {findings}")
    return grid


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(row for row, _ in cells)
    min_c = min(col for _, col in cells)
    return tuple(sorted((row - min_r, col - min_c) for row, col in cells))


def _green_components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    }
    components: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return components


def _analyze(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)):
        return ["grid must be a list or tuple of rows"], None
    if not grid:
        return ["grid must contain at least one row"], None
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a list or tuple"], None
    width = len(grid[0])
    if width == 0:
        return ["grid rows must be non-empty"], None
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    height = len(grid)
    if not 9 <= height <= 18:
        errors.append(f"grid height {height} is outside 9..18")
    if not 11 <= width <= 20:
        errors.append(f"grid width {width} is outside 11..20")

    copied: list[list[int]] = []
    for row_index, row in enumerate(grid):
        copied_row: list[int] = []
        for col_index, value in enumerate(row):
            if type(value) is not int:
                errors.append(f"cell ({row_index},{col_index}) is not an integer")
                continue
            copied_row.append(value)
            if value not in _ALLOWED_COLORS:
                errors.append(f"cell ({row_index},{col_index}) uses unsupported color {value}")
        copied.append(copied_row)
    if errors:
        return errors, None

    shape_cells = [(r, c, copied[r][c]) for r in range(height) for c in range(width) if copied[r][c] in _SHAPE_KEYS]
    color_cells = [(r, c, copied[r][c]) for r in range(height) for c in range(width) if copied[r][c] in _COLOR_KEYS]
    if len(shape_cells) != 1:
        errors.append(f"expected exactly one shape-key cell (1 or 4), found {len(shape_cells)}")
    if len(color_cells) != 1:
        errors.append(f"expected exactly one color-key cell (2, 6, or 8), found {len(color_cells)}")

    records: list[dict[str, Any]] = []
    for cells in _green_components(copied):
        normalized = _normalize(cells)
        if normalized in _L_NORMALIZED:
            family = "L"
        elif normalized == _PLUS:
            family = "PLUS"
        else:
            family = "OTHER"
            errors.append(
                "green component at "
                f"{cells[0]} has unsupported normalized shape {normalized}"
            )
        records.append({"cells": cells, "family": family, "size": len(cells)})

    n_l = sum(record["family"] == "L" for record in records)
    n_plus = sum(record["family"] == "PLUS" for record in records)
    if n_l not in (1, 2):
        errors.append(f"expected one or two L-triominoes, found {n_l}")
    if n_plus not in (1, 2):
        errors.append(f"expected one or two plus-pentominoes, found {n_plus}")
    if errors:
        return errors, None

    facts = {
        "grid_h": height,
        "grid_w": width,
        "shape_key": shape_cells[0][2],
        "color_key": color_cells[0][2],
        "n_l": n_l,
        "n_plus": n_plus,
        "records": records,
    }
    return [], facts


def self_check(grid: Any) -> list[str]:
    """Return structural diagnostics; an empty list means distribution-valid."""
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """All ordinary samples intentionally remain inside the canonical grammar."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    errors, facts = _analyze(grid)
    if errors or facts is None:
        raise ValueError(f"cannot observe malformed f151fbd31cb2 grid: {errors}")
    return {name: int(facts[name]) for name in AXES}


def _facts_or_raise(grid: Any) -> dict[str, Any]:
    errors, facts = _analyze(grid)
    if errors or facts is None:
        raise ValueError(f"malformed f151fbd31cb2 grid: {errors}")
    return facts


def _recolor_family(grid: Any, family: str) -> list[list[int]]:
    facts = _facts_or_raise(grid)
    output = deepcopy(grid)
    output = [list(row) for row in output]
    for record in facts["records"]:
        if record["family"] == family:
            for row, col in record["cells"]:
                output[row][col] = facts["color_key"]
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent readable mirror of the pinned Racket semantics."""
    facts = _facts_or_raise(grid)
    selected = "L" if facts["shape_key"] == 1 else "PLUS"
    return _recolor_family(grid, selected)


def _majority_objects(grid: Any) -> list[list[int]]:
    facts = _facts_or_raise(grid)
    selected = "PLUS" if facts["n_plus"] > facts["n_l"] else "L"
    return _recolor_family(grid, selected)


def _larger_total_area(grid: Any) -> list[list[int]]:
    facts = _facts_or_raise(grid)
    l_area = sum(record["size"] for record in facts["records"] if record["family"] == "L")
    plus_area = sum(record["size"] for record in facts["records"] if record["family"] == "PLUS")
    selected = "PLUS" if plus_area > l_area else "L"
    return _recolor_family(grid, selected)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "majority_objects": _majority_objects,
    "larger_total_area": _larger_total_area,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _selected_family_is_minority(grid: Any) -> bool:
    facts = _facts_or_raise(grid)
    selected_count = facts["n_l"] if facts["shape_key"] == 1 else facts["n_plus"]
    other_count = facts["n_plus"] if facts["shape_key"] == 1 else facts["n_l"]
    return selected_count < other_count


def _balanced_families(grid: Any) -> bool:
    facts = _facts_or_raise(grid)
    return facts["n_l"] == facts["n_plus"]


SEMANTIC_WITNESSES = {
    "selected_family_is_minority": _selected_family_is_minority,
    "balanced_families": _balanced_families,
}
WITNESS_RIVALS = {
    "selected_family_is_minority": ["majority_objects", "larger_total_area"],
}
BRANCH_WITNESSES = {"balanced_families"}


def lesson_identifiable(demos, query) -> list[str]:
    """Offline finite-rival check over authoritative labeled pairs."""
    reasons: list[str] = []
    pairs = [*demos, query]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} must contain authoritative input and output grids")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"{role} input is not lawful: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with the pinned rule mirror")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"query-changing rival survives demonstrations: {name}")
    return reasons
