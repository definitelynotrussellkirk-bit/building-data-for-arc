"""Constructive generator for ARC task ``ebff81ea3252``.

The selected authority scans every interior color-3 cell.  Whenever its four
cardinal neighbours are also color 3, those five cells are recolored to 7.
Crucially, the cross need not be an isolated five-cell connected component.
This generator therefore includes both isolated and one-cell-attached targets,
plus a five-cell non-cross decoy that refutes the tempting "recolor every
five-cell component" shortcut.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ebff81ea3252"
TASK_ID = GENERATOR_ID
RULE_HASH = "deb3ac96cc89"
VERSION = "3.0.0"
SUMMARY = (
    "An 8..11 by 9..11 zero-background grid contains one to three green "
    "cardinal crosses.  A target cross is either an isolated five-cell plus "
    "or has one additional connected corner cell, so component boundaries "
    "cannot be used as a proxy for the rule.  Every input also contains a "
    "separate five-cell green non-plus decoy.  The rule recolors exactly the "
    "center and four cardinal neighbours of every all-green cross from 3 to "
    "7, preserving attached and decoy cells.  Default sample indices alternate "
    "isolated and attached contexts, so every three-demo lesson contains a "
    "counterexample to the strongest canonical-fitting shortcut."
)

EXAMPLES_NEEDED = 3
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

CONTEXT_MODES = ("isolated", "attached")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed draw over 8..11",
        "valid": "8..11",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed draw over 9..11",
        "valid": "9..11",
    },
    "n_pluses": {
        "type": "int",
        "default": "deterministic 1|2|3 schedule by sample_index",
        "valid": "1..3",
    },
    "context_mode": {
        "type": "str",
        "default": "alternating isolated|attached schedule by sample_index",
        "valid": "|".join(CONTEXT_MODES),
    },
}

INVARIANTS = [
    "the input is a rectangular 8..11 by 9..11 grid using exactly integer colors 0 and 3",
    "one to three non-overlapping green cardinal crosses are present",
    "target components have size five (isolated) or six (one attached corner cell)",
    "a separate size-five green component is not a cardinal cross",
    "all advertised overrides are exact, constructive, and observable from the returned grid",
]

_H_LIMITS = (8, 11)
_W_LIMITS = (9, 11)
_N_LIMITS = (1, 3)
_PLUS = frozenset({(1, 1), (0, 1), (2, 1), (1, 0), (1, 2)})
_CORNERS = ((0, 0), (0, 2), (2, 0), (2, 2))


def _dihedral_variants(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    """Return the distinct rotations/reflections of a small normalized shape."""
    variants: set[frozenset[tuple[int, int]]] = set()
    original = tuple(cells)
    for reflected in (False, True):
        transformed = [(r, -c if reflected else c) for r, c in original]
        for turns in range(4):
            current = transformed
            for _ in range(turns):
                current = [(c, -r) for r, c in current]
            min_r = min(r for r, _ in current)
            min_c = min(c for _, c in current)
            variants.add(frozenset((r - min_r, c - min_c) for r, c in current))
    return tuple(sorted(variants, key=lambda shape: sorted(shape)))


# P-pentomino variants: five connected cells, none containing a cardinal cross.
_NONPLUS_PENTOMINOES = _dihedral_variants(
    {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}
)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "n_pluses"}:
            if type(value) is not int:
                raise ValueError(
                    f"{name} must be an integer, not {type(value).__name__}"
                )
            lo, hi = {
                "grid_h": _H_LIMITS,
                "grid_w": _W_LIMITS,
                "n_pluses": _N_LIMITS,
            }[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
        elif name == "context_mode":
            if type(value) is not str:
                raise ValueError(
                    f"context_mode must be a string, not {type(value).__name__}"
                )
            if value not in CONTEXT_MODES:
                raise ValueError(
                    f"context_mode={value!r} not in {list(CONTEXT_MODES)!r}"
                )


def _scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    """Use a pinned default without narrowing the explicit override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], scheduled: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _tile_origins(height: int, width: int) -> list[tuple[int, int]]:
    """3x3 motif boxes separated by a guaranteed zero row/column."""
    return [
        (row, col)
        for row in range(0, height - 2, 4)
        for col in range(0, width - 2, 4)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", *_H_LIMITS)
    width = ctx.draw_int_diff("grid_w", *_W_LIMITS)
    n_pluses = _scheduled_int(
        ctx, "n_pluses", *_N_LIMITS, 1 + sample_index % 3
    )
    context_mode = _scheduled_choice(
        ctx,
        "context_mode",
        CONTEXT_MODES,
        "attached" if sample_index % 2 == 0 else "isolated",
    )

    origins = _tile_origins(height, width)
    if len(origins) < n_pluses + 1:
        raise RuntimeError(
            f"grid {height}x{width} has only {len(origins)} motif slots for "
            f"{n_pluses} targets plus one decoy"
        )
    placement_rng = ctx.draw_rng("motif_placement")
    chosen = placement_rng.sample(origins, n_pluses + 1)
    target_origins, decoy_origin = chosen[:-1], chosen[-1]

    grid = full_grid(height, width, 0)
    corner_rng = ctx.draw_rng("attached_corners")
    for top, left in target_origins:
        cells = set(_PLUS)
        if context_mode == "attached":
            cells.add(corner_rng.choice(_CORNERS))
        for dr, dc in cells:
            grid[top + dr][left + dc] = 3

    decoy_rng = ctx.draw_rng("decoy_orientation")
    decoy = decoy_rng.choice(_NONPLUS_PENTOMINOES)
    top, left = decoy_origin
    for dr, dc in decoy:
        grid[top + dr][left + dc] = 3

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_pluses": n_pluses,
        "context_mode": context_mode,
    }
    if observed != expected:
        raise RuntimeError(
            f"constructive sampler produced unobservable axes: "
            f"expected {expected}, observed {observed}"
        )
    return grid


def _exact_plus_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    centers: list[tuple[int, int]] = []
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            cells = (
                (row, col),
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if all(grid[r][c] == 3 for r, c in cells):
                centers.append((row, col))
    return centers


def _components(grid: list[list[int]], color: int = 3) -> list[set[tuple[int, int]]]:
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        components.append(component)
    return components


def _cross_cells(center: tuple[int, int]) -> set[tuple[int, int]]:
    row, col = center
    return {
        (row, col),
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    }


def _target_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    centers = set(_exact_plus_centers(grid))
    return [component for component in _components(grid) if component & centers]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostics for malformed/off-domain inputs; never raise."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["ragged grid"]

    height = len(grid)
    errors: list[str] = []
    if not _H_LIMITS[0] <= height <= _H_LIMITS[1]:
        errors.append(f"grid height {height} outside 8..11")
    if not _W_LIMITS[0] <= width <= _W_LIMITS[1]:
        errors.append(f"grid width {width} outside 9..11")
    if any(
        type(value) is not int or value not in {0, 3}
        for row in grid
        for value in row
    ):
        errors.append("cells must be exact integer colors 0 or 3")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    centers = _exact_plus_centers(grid)
    if not 1 <= len(centers) <= 3:
        errors.append(f"expected 1..3 green cardinal crosses, found {len(centers)}")
        return errors

    occupied_cross_cells: set[tuple[int, int]] = set()
    for center in centers:
        cells = _cross_cells(center)
        if occupied_cross_cells & cells:
            errors.append("green cardinal crosses must not share target cells")
            break
        occupied_cross_cells.update(cells)

    center_set = set(centers)
    for component in _components(grid):
        component_centers = component & center_set
        if len(component_centers) > 1:
            errors.append("a green component contains multiple cross centers")
        if component_centers and len(component) not in {5, 6}:
            errors.append(
                f"target component has size {len(component)}; expected five or six"
            )
        if not component_centers and len(component) > 5:
            errors.append(
                f"non-target green component has size {len(component)}; expected at most five"
            )
    return errors


def strict_canonical_like(grid):
    """The constructive domain is the canonical-backed task envelope."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    target_sizes = sorted(len(component) for component in _target_components(grid))
    if all(size == 5 for size in target_sizes):
        context_mode = "isolated"
    elif all(size == 6 for size in target_sizes):
        context_mode = "attached"
    else:
        raise ValueError(f"mixed or unsupported target component sizes: {target_sizes}")

    centers = _exact_plus_centers(grid)
    nonplus_fives = [
        component
        for component in _components(grid)
        if len(component) == 5 and not (component & set(centers))
    ]
    if len(nonplus_fives) != 1:
        raise ValueError(
            f"generated morphology should contain one size-five non-plus, "
            f"found {len(nonplus_fives)}"
        )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pluses": len(centers),
        "context_mode": context_mode,
    }


def _intended_output(grid):
    result = deepcopy(grid)
    for center in _exact_plus_centers(grid):
        for row, col in _cross_cells(center):
            result[row][col] = 7
    return result


def _component_exact_only(grid):
    """Wrong rival: recolor only isolated components equal to one cross."""
    result = deepcopy(grid)
    centers = _exact_plus_centers(grid)
    for component in _components(grid):
        if len(component) != 5:
            continue
        if any(component == _cross_cells(center) for center in centers):
            for row, col in component:
                result[row][col] = 7
    return result


def _size_five_components(grid):
    """Wrong rival: recolor every five-cell green connected component."""
    result = deepcopy(grid)
    for component in _components(grid):
        if len(component) == 5:
            for row, col in component:
                result[row][col] = 7
    return result


def _attached_target_witness(grid) -> bool:
    return any(len(component) > 5 for component in _target_components(grid))


def _five_cell_nonplus_witness(grid) -> bool:
    centers = set(_exact_plus_centers(grid))
    return any(
        len(component) == 5 and not (component & centers)
        for component in _components(grid)
    )


SEMANTIC_WITNESSES = {
    "attached_target": _attached_target_witness,
    "five_cell_nonplus": _five_cell_nonplus_witness,
}
SEMANTIC_RIVALS = {
    "component_exact_only": _component_exact_only,
    "size_five_components": _size_five_components,
}
WITNESS_RIVALS = {
    "attached_target": ["component_exact_only", "size_five_components"],
    "five_cell_nonplus": ["size_five_components"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(train_pairs, query_pair):
    """Return reasons when any declared rival still fits every demonstration."""
    del query_pair
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for pair in train_pairs:
            try:
                if rival(deepcopy(pair["input"])) != pair["output"]:
                    survived = False
                    break
            except Exception as exc:
                reasons.append(
                    f"competitor {name!r} raised {type(exc).__name__}: {exc}"
                )
                survived = False
                break
        if survived:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons


def mutation_fixtures():
    """Small/off-domain impostors that the executable contract must reject."""
    blank = [[0] * 9 for _ in range(8)]
    singleton = deepcopy(blank)
    singleton[3][3] = 3
    wrong_color = deepcopy(blank)
    wrong_color[3][3] = 1
    oversized = [[0] * 9 for _ in range(12)]
    overlapping = deepcopy(blank)
    for row, col in {
        (3, 2), (3, 3), (3, 4), (3, 5),
        (2, 3), (4, 3), (2, 4), (4, 4),
    }:
        overlapping[row][col] = 3
    return [
        ("all_background", blank),
        ("singleton", singleton),
        ("wrong_color", wrong_color),
        ("height_12", oversized),
        ("overlapping_crosses", overlapping),
    ]
