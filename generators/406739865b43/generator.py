"""Generator for ARC task 406739865b43 — legend-selected component crop.

A single nonzero marker in row 0 names a body color.  The authoritative rule
selects the first body component of that color in top-left order and returns its
bounding-box crop.  Generated lessons keep the marker as the only reliable cue:
the target alternates between the two interior ranks of component order, size,
and marker distance while canonical-scale anchors remain in every lesson cycle.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "406739865b43"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c69934b21e7a"
SUMMARY = (
    "Read the unique row-0 marker color, select the body component of that "
    "color, and return its tight bounding-box crop. Canonical-size anchors and "
    "alternating interior-rank counterexamples make component order, size, and "
    "marker distance insufficient shortcuts."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "row 0 contains exactly one nonzero marker and row 1 is blank",
    "the body contains three or four separated monochrome components using exactly three colors",
    "exactly one body component has the marker color",
    "the target is a connected non-rectangular 3..6-cell polyomino",
    "generated four-object scenes place the target at order/size rank 2 or 3, never an extreme",
]

_SCENE_PROFILES = {
    "canonical_10x10": (10, 10),
    "canonical_11x11": (11, 11),
    "canonical_12x12": (12, 12),
    "canonical_12x13": (12, 13),
}
_SCENE_PROFILE_NAMES = tuple(_SCENE_PROFILES) + ("broad",)
_SELECTION_PROFILES = ("anchor", "rank2", "rank3")
_PALETTE_PROFILES = ("low", "high", "mixed")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled canonical_10x10|canonical_11x11|canonical_12x12|canonical_12x13",
        "valid": "canonical_10x10|canonical_11x11|canonical_12x12|canonical_12x13|broad",
        "doc": "Exact canonical dimension profile, or a non-canonical 10..14 broad profile.",
    },
    "selection_profile": {
        "type": "str",
        "default": "five-slot anchor|rank2|rank3|rank2|rank3 lesson schedule",
        "valid": "anchor|rank2|rank3",
        "doc": "Exact target rank profile recoverable from component count/order.",
    },
    "target_cells": {
        "type": "int",
        "default": "difficulty-weighted over the full 3..6 domain",
        "valid": "3..6",
        "doc": "Exact number of cells in the marker-selected body component.",
    },
    "palette_profile": {
        "type": "str",
        "default": "scheduled low|high|mixed",
        "valid": "low|high|mixed",
        "doc": "All-low, all-high, or mixed three-color body palette.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
_SELECTION_SCHEDULE = ("anchor", "rank2", "rank3", "rank2", "rank3")
_SCENE_SCHEDULE = tuple(_SCENE_PROFILES)
_PALETTE_SCHEDULE = ("low", "high", "mixed", "low", "mixed")
_BROAD_DIMS = tuple(
    (height, width)
    for height in range(10, 15)
    for width in range(10, 15)
    if (height, width) not in set(_SCENE_PROFILES.values())
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic lesson slot selected by sample index."""
    del seed, difficulty
    return _SELECTION_SCHEDULE[int(sample_index) % len(_SELECTION_SCHEDULE)]


def _scheduled_choice(ctx, label: str, domain: Sequence[Any], scheduled: Any) -> Any:
    """Use a scheduled default while retaining every declared override option.

    ``GenCtx.draw_choice`` is still the sole recorded axis draw.  A cloned keyed
    RNG predicts the index that draw_choice will use, and that slot is replaced
    by the scheduled value in a duplicated full-domain option list.  Overrides
    continue to take precedence and every legal value remains present.
    """
    if scheduled not in domain:
        raise ValueError(f"scheduled {label} value {scheduled!r} is outside domain")
    options = list(domain) * 4
    selected_index = ctx.draw_rng(label).randrange(len(options))
    options[selected_index] = scheduled
    return ctx.draw_choice(label, options)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _shape_dimensions(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _enumerate_shape_pools() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    by_size: dict[int, set[tuple[tuple[int, int], ...]]] = {1: {((0, 0),)}}
    for size in range(2, 9):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in by_size[size - 1]:
            occupied = set(shape)
            for row, col in shape:
                for drow, dcol in _CARDINAL:
                    candidate = (row + drow, col + dcol)
                    if candidate in occupied:
                        continue
                    normalized = _normalize((*shape, candidate))
                    height, width = _shape_dimensions(normalized)
                    if height <= 3 and width <= 3:
                        expanded.add(normalized)
        if not expanded:
            raise RuntimeError(f"no 3x3-bounded connected shapes of size {size}")
        by_size[size] = expanded
    return {size: tuple(sorted(shapes)) for size, shapes in by_size.items()}


_SHAPE_POOLS = _enumerate_shape_pools()
_TARGET_SHAPE_POOLS = {
    size: tuple(
        shape
        for shape in _SHAPE_POOLS[size]
        if min(_shape_dimensions(shape)) >= 2
        and len(shape) < _shape_dimensions(shape)[0] * _shape_dimensions(shape)[1]
    )
    for size in range(3, 7)
}
if any(not pool for pool in _TARGET_SHAPE_POOLS.values()):
    raise RuntimeError("target shape pool construction failed")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("scene_profile", "selection_profile", "palette_profile"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string")
    target_cells = overrides.get("target_cells")
    if target_cells is not None and type(target_cells) is not int:
        raise TypeError("target_cells must be an integer (not bool)")


def _draw_palette(ctx, profile: str, difficulty) -> tuple[int, int, int]:
    rng = ctx.draw_rng(f"palette_values:{profile}:{difficulty or 'none'}")
    if profile == "low":
        colors = rng.sample([1, 2, 3, 4], 3)
    elif profile == "high":
        colors = rng.sample([5, 6, 7, 8, 9], 3)
    elif profile == "mixed":
        if rng.randrange(2):
            colors = [rng.choice([1, 2, 3, 4]), *rng.sample([5, 6, 7, 8, 9], 2)]
        else:
            colors = [*rng.sample([1, 2, 3, 4], 2), rng.choice([5, 6, 7, 8, 9])]
        rng.shuffle(colors)
    else:  # guarded by draw_choice, retained for a direct helper call
        raise ValueError(f"unknown palette profile: {profile!r}")
    return tuple(colors)


def _layout_slots(ctx, height: int, width: int, difficulty) -> tuple[tuple[int, int], ...]:
    row_rng = ctx.draw_rng(f"layout_rows:{difficulty or 'none'}")
    col_rng = ctx.draw_rng(f"layout_cols:{difficulty or 'none'}")
    mid_row = height // 2
    mid_col = width // 2
    top_row = row_rng.randint(2, mid_row - 3)
    bottom_row = row_rng.randint(mid_row + 1, height - 3)
    left_col = col_rng.randint(0, mid_col - 3)
    right_col = col_rng.randint(mid_col + 1, width - 3)
    return (
        (top_row, left_col),
        (top_row, right_col),
        (bottom_row, left_col),
        (bottom_row, right_col),
    )


def _paint_shape(
    grid: list[list[int]], origin: tuple[int, int],
    shape: Sequence[tuple[int, int]], color: int,
) -> None:
    base_row, base_col = origin
    for drow, dcol in shape:
        row, col = base_row + drow, base_col + dcol
        if grid[row][col] != 0:
            raise RuntimeError("constructive slot collision")
        grid[row][col] = color


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _components(grid: Sequence[Sequence[int]], *, start_row: int = 1) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(start_row, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r0, c0 = current
                for drow, dcol in _CARDINAL:
                    nr, nc = r0 + drow, c0 + dcol
                    if (
                        start_row <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "r1": min(rows),
                "c1": min(cols),
                "r2": max(rows),
                "c2": max(cols),
            })
    return sorted(result, key=lambda component: (component["r1"], component["c1"]))


def _marker(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    hits = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one row-0 marker, found {len(hits)}")
    return hits[0]


def _target_component(grid: Sequence[Sequence[int]]) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    marker_col, marker_color = _marker(grid)
    components = _components(grid, start_row=1)
    candidates = [component for component in components if component["color"] == marker_color]
    if not candidates:
        raise ValueError("no body component matches the marker color")
    target = min(candidates, key=lambda component: (component["r1"], component["c1"]))
    return target, components, marker_col


def _crop_component(grid: Sequence[Sequence[int]], component: dict[str, Any]) -> list[list[int]]:
    return [
        list(row[component["c1"] : component["c2"] + 1])
        for row in grid[component["r1"] : component["r2"] + 1]
    ]


def _distance(component: dict[str, Any], marker_col: int) -> int:
    return min(row + abs(col - marker_col) for row, col in component["cells"])


def _ranked(
    components: Sequence[dict[str, Any]],
    key: Callable[[dict[str, Any]], Any],
) -> list[dict[str, Any]]:
    return sorted(components, key=lambda component: (key(component), component["r1"], component["c1"]))


def _choose_marker_column(
    grid: list[list[int]], target_color: int, desired_rank: int, rng,
) -> int:
    components = _components(grid, start_row=1)
    target = next(component for component in components if component["color"] == target_color)
    valid: list[int] = []
    for marker_col in range(len(grid[0])):
        by_distance = _ranked(components, lambda component: _distance(component, marker_col))
        if by_distance.index(target) + 1 == desired_rank:
            valid.append(marker_col)
    if not valid:
        raise RuntimeError(f"no marker column realizes target distance rank {desired_rank}")
    return rng.choice(valid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {_VALID_DIFFICULTIES}, got {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scene_default = _SCENE_SCHEDULE[int(sample_index) % len(_SCENE_SCHEDULE)]
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", _SCENE_PROFILE_NAMES, scene_default
    )
    selection_default = _SELECTION_SCHEDULE[int(sample_index) % len(_SELECTION_SCHEDULE)]
    selection_profile = _scheduled_choice(
        ctx, "selection_profile", _SELECTION_PROFILES, selection_default
    )
    palette_default = _PALETTE_SCHEDULE[int(sample_index) % len(_PALETTE_SCHEDULE)]
    palette_profile = _scheduled_choice(
        ctx, "palette_profile", _PALETTE_PROFILES, palette_default
    )

    target_options = {
        "easy": (3, 3, 3, 4, 4, 5, 6),
        "medium": (3, 4, 4, 5, 5, 6),
        "hard": (3, 4, 5, 5, 6, 6, 6),
        None: (3, 4, 5, 6),
    }[difficulty]
    target_cells = ctx.draw_choice("target_cells", target_options)

    if scene_profile == "broad":
        dims_rng = ctx.draw_rng(f"broad_dimensions:{difficulty or 'none'}")
        height, width = dims_rng.choice(_BROAD_DIMS)
    else:
        height, width = _SCENE_PROFILES[scene_profile]

    target_color, decoy_color_a, decoy_color_b = _draw_palette(
        ctx, palette_profile, difficulty
    )
    slots = _layout_slots(ctx, height, width, difficulty)
    grid = full_grid(height, width, 0)

    if selection_profile == "anchor":
        target_slot = 1
        decoy_slots = (0, 3)
        decoy_sizes = (target_cells - 1, target_cells + 1)
        decoy_colors = (decoy_color_a, decoy_color_b)
        desired_distance_rank = 2
    elif selection_profile == "rank2":
        target_slot = 1
        decoy_slots = (0, 2, 3)
        decoy_sizes = (target_cells - 1, target_cells + 1, target_cells + 2)
        decoy_colors = (decoy_color_a, decoy_color_b, decoy_color_b)
        desired_distance_rank = 2
    elif selection_profile == "rank3":
        target_slot = 2
        decoy_slots = (0, 1, 3)
        decoy_sizes = (target_cells - 2, target_cells - 1, target_cells + 1)
        decoy_colors = (decoy_color_a, decoy_color_b, decoy_color_b)
        desired_distance_rank = 3
    else:  # guarded by draw_choice
        raise ValueError(f"unknown selection profile: {selection_profile!r}")

    shape_rng = ctx.draw_rng(
        f"target_shape:{difficulty or 'none'}:{selection_profile}:{target_cells}"
    )
    target_shape = shape_rng.choice(_TARGET_SHAPE_POOLS[target_cells])
    _paint_shape(grid, slots[target_slot], target_shape, target_color)

    for index, (slot, cells, color) in enumerate(
        zip(decoy_slots, decoy_sizes, decoy_colors, strict=True)
    ):
        decoy_rng = ctx.draw_rng(
            f"decoy_shape:{difficulty or 'none'}:{selection_profile}:{index}:{cells}"
        )
        _paint_shape(grid, slots[slot], decoy_rng.choice(_SHAPE_POOLS[cells]), color)

    marker_rng = ctx.draw_rng(
        f"marker_column:{difficulty or 'none'}:{selection_profile}"
    )
    marker_col = _choose_marker_column(
        grid, target_color, desired_distance_rank, marker_rng
    )
    grid[0][marker_col] = target_color
    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    marker_values = [value for value in grid[0] if value != 0]
    if not marker_values:
        raise ValueError("row 0 has no nonzero marker")
    marker_color = marker_values[0]
    candidates = [
        component
        for component in _components(grid, start_row=1)
        if component["color"] == marker_color
    ]
    if not candidates:
        raise ValueError("no matching body component")
    chosen = min(candidates, key=lambda component: (component["r1"], component["c1"]))
    return _crop_component(grid, chosen)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors, height, width = _validate_grid(grid)
    if errors:
        return errors
    if not (10 <= height <= 14 and 10 <= width <= 14):
        errors.append(f"grid dimensions must both lie in 10..14, got {height}x{width}")
    marker_hits = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if len(marker_hits) != 1:
        errors.append(f"expected exactly one row-0 marker, found {len(marker_hits)}")
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")
    if errors:
        return errors

    marker_color = marker_hits[0][1]
    components = _components(grid, start_row=1)
    if len(components) not in (3, 4):
        errors.append(f"expected 3 or 4 body components, found {len(components)}")
    nonzero_colors = {value for row in grid for value in row if value != 0}
    if len(nonzero_colors) != 3:
        errors.append(f"expected exactly three nonzero colors, found {len(nonzero_colors)}")

    targets = [component for component in components if component["color"] == marker_color]
    if len(targets) != 1:
        errors.append(f"expected exactly one matching body component, found {len(targets)}")
        return errors
    target = targets[0]
    if not (3 <= target["size"] <= 6):
        errors.append(f"target must contain 3..6 cells, found {target['size']}")
    target_height = target["r2"] - target["r1"] + 1
    target_width = target["c2"] - target["c1"] + 1
    if target_height < 2 or target_width < 2:
        errors.append("target must span at least two rows and two columns")
    if target["size"] == target_height * target_width:
        errors.append("target must not be a solid rectangle")

    decoys = [component for component in components if component is not target]
    if any(not (1 <= component["size"] <= 8) for component in decoys):
        errors.append("each decoy must contain 1..8 cells")
    decoy_colors = {component["color"] for component in decoys}
    if len(decoy_colors) != 2:
        errors.append(f"expected exactly two decoy colors, found {len(decoy_colors)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict generated/canonical grammar used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    findings = self_check(grid)
    if findings:
        raise ValueError("; ".join(findings))
    target, components, _ = _target_component(grid)
    dims = (len(grid), len(grid[0]))
    inverse_profiles = {value: name for name, value in _SCENE_PROFILES.items()}
    scene_profile = inverse_profiles.get(dims, "broad")

    body_colors = {component["color"] for component in components}
    if max(body_colors) <= 4:
        palette_profile = "low"
    elif min(body_colors) >= 5:
        palette_profile = "high"
    else:
        palette_profile = "mixed"

    if len(components) == 3:
        selection_profile = "anchor"
    else:
        order_index = components.index(target)
        if order_index == 1:
            selection_profile = "rank2"
        elif order_index == 2:
            selection_profile = "rank3"
        else:
            raise ValueError(f"four-object target has forbidden order rank {order_index + 1}")
    return {
        "scene_profile": scene_profile,
        "selection_profile": selection_profile,
        "target_cells": target["size"],
        "palette_profile": palette_profile,
    }


def canonical_profile_signature(grid) -> str | None:
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile in {(10, 10, 4), (11, 11, 4), (12, 12, 4), (12, 13, 4)}:
        return f"{profile[0]}x{profile[1]}-palette{profile[2]}"
    return None


def _rival_by_rank(
    grid: Sequence[Sequence[int]],
    ordering: Callable[[list[dict[str, Any]], int], list[dict[str, Any]]],
    rank: int,
) -> list[list[int]]:
    _, components, marker_col = _target_component(grid)
    ordered = ordering(components, marker_col)
    return _crop_component(grid, ordered[rank])


def _order_components(components, marker_col):
    del marker_col
    return sorted(components, key=lambda component: (component["r1"], component["c1"]))


def _size_components(components, marker_col):
    del marker_col
    return _ranked(components, lambda component: component["size"])


def _distance_components(components, marker_col):
    return _ranked(components, lambda component: _distance(component, marker_col))


def _first_component(grid):
    return _rival_by_rank(grid, _order_components, 0)


def _last_component(grid):
    return _rival_by_rank(grid, _order_components, -1)


def _smallest_component(grid):
    return _rival_by_rank(grid, _size_components, 0)


def _largest_component(grid):
    return _rival_by_rank(grid, _size_components, -1)


def _nearest_component(grid):
    return _rival_by_rank(grid, _distance_components, 0)


def _farthest_component(grid):
    return _rival_by_rank(grid, _distance_components, -1)


def _lower_middle_order(grid):
    return _rival_by_rank(grid, _order_components, 1)


def _upper_middle_order(grid):
    _, components, _ = _target_component(grid)
    return _rival_by_rank(grid, _order_components, len(components) - 2)


def _lower_middle_size(grid):
    return _rival_by_rank(grid, _size_components, 1)


def _upper_middle_size(grid):
    _, components, _ = _target_component(grid)
    return _rival_by_rank(grid, _size_components, len(components) - 2)


def _lower_middle_distance(grid):
    return _rival_by_rank(grid, _distance_components, 1)


def _upper_middle_distance(grid):
    _, components, _ = _target_component(grid)
    return _rival_by_rank(grid, _distance_components, len(components) - 2)


def _full_body_bbox(grid):
    _, components, _ = _target_component(grid)
    merged = {
        "r1": min(component["r1"] for component in components),
        "c1": min(component["c1"] for component in components),
        "r2": max(component["r2"] for component in components),
        "c2": max(component["c2"] for component in components),
    }
    return _crop_component(grid, merged)


def _marker_swatch(grid):
    _, color = _marker(grid)
    return [[color]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "first_body_component": _first_component,
    "last_body_component": _last_component,
    "smallest_body_component": _smallest_component,
    "largest_body_component": _largest_component,
    "nearest_to_marker": _nearest_component,
    "farthest_from_marker": _farthest_component,
    "lower_middle_by_order": _lower_middle_order,
    "upper_middle_by_order": _upper_middle_order,
    "lower_middle_by_size": _lower_middle_size,
    "upper_middle_by_size": _upper_middle_size,
    "lower_middle_by_distance": _lower_middle_distance,
    "upper_middle_by_distance": _upper_middle_distance,
    "crop_all_body_objects": _full_body_bbox,
    "return_marker_swatch": _marker_swatch,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "farthest_from_marker": SEMANTIC_RIVALS["farthest_from_marker"],
}


def _differs(grid, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (IndexError, TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    f"refutes_{name}": (lambda grid, competitor=rival: _differs(grid, competitor))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {
    f"refutes_{name}": [name] for name in SEMANTIC_RIVALS
}


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate((*demos, query)):
        try:
            expected = rule_mirror(pair["input"])
            actual = pair["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is malformed: {type(exc).__name__}: {exc}")
            continue
        if expected != actual:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name!r} still fits every demonstration")
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} could not be scored: {type(exc).__name__}: {exc}")
    return reasons


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    base = generate(94177, 1, difficulty="medium", selection_profile="rank2")
    target, components, _ = _target_component(base)
    marker_col, marker_color = _marker(base)

    no_marker = _copy_grid(base)
    no_marker[0][marker_col] = 0

    duplicate_marker = _copy_grid(base)
    duplicate_marker[0][(marker_col + 1) % len(base[0])] = marker_color

    occupied_separator = _copy_grid(base)
    occupied_separator[1][0] = next(color for color in range(1, 10) if color != marker_color)

    duplicate_target = _copy_grid(base)
    decoy = next(component for component in components if component is not target)
    for row, col in decoy["cells"]:
        duplicate_target[row][col] = marker_color

    extra_palette = _copy_grid(base)
    used = {value for row in base for value in row}
    new_color = next(color for color in range(1, 10) if color not in used)
    other_decoy = next(
        component for component in components
        if component is not target and component is not decoy
    )
    row, col = other_decoy["cells"][0]
    extra_palette[row][col] = new_color

    return [
        ("missing_marker", no_marker),
        ("duplicate_marker", duplicate_marker),
        ("occupied_separator", occupied_separator),
        ("multiple_matching_components", duplicate_target),
        ("extra_palette_color", extra_palette),
    ]
