"""Mark blue horizontal/vertical line intersections red.

The canonical rule is local: a blue cell becomes red exactly when all four
cardinal neighbours are blue.  The curriculum deliberately includes crosses
with several arm lengths and T-junction near misses; isolated unit pluses alone
would teach the wrong component-size rule.
"""
from __future__ import annotations

import copy
from itertools import product
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "cf09cffb4663"
VERSION = "3.0.0"
RULE_HASH = "4584c31c95ef"
SUMMARY = (
    "On a zero-background grid, recolor a blue(1) cell red(2) exactly when "
    "its up, down, left, and right neighbours are all blue. Generated scenes "
    "contain one or two separated blue line crosses with varied arm lengths, "
    "plus a straight-line or T-junction decoy that must remain unchanged."
)
INVARIANTS = [
    "cells are exactly background 0 and blue 1",
    "one or two blue crossing cells satisfy the four-cardinal-neighbour rule",
    "target components are clean horizontal/vertical crosses with varied arm lengths",
    "one disconnected straight-line or T-junction decoy remains blue",
]

EXAMPLES_NEEDED = 3
CANONICAL_SHAPES = ((8, 10), (9, 9), (9, 11), (10, 10))
SCHEDULE_PROFILES = ("small_t", "canonical_line", "mixed_t")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "one of the canonical heights 8..10",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "one of the canonical widths 9..11",
        "valid": "9..11",
    },
    "n_crosses": {
        "type": "int",
        "default": "scheduled 1|1|2",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_request(difficulty, overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    bounds = {"grid_h": (8, 10), "grid_w": (9, 11), "n_crosses": (1, 2)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive sample indices cover every teaching profile."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    return SCHEDULE_PROFILES[(int(sample_index) + offsets.get(difficulty, 0)) % 3]


def _draw_axis(ctx, name: str, default: int, lo: int, hi: int) -> int:
    """Record a correlated default while preserving the full override domain."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _arm_tuples(size: int) -> list[tuple[int, int, int, int]]:
    """All positive up/down/left/right arm lengths, capped at three."""
    return [
        values
        for values in product(range(1, 4), repeat=4)
        if sum(values) == size - 1
    ]


def _cross_candidates(h: int, w: int, size: int):
    candidates = []
    for up, down, left, right in _arm_tuples(size):
        for r in range(up, h - down):
            for c in range(left, w - right):
                cells = {(r, c)}
                cells.update((r - step, c) for step in range(1, up + 1))
                cells.update((r + step, c) for step in range(1, down + 1))
                cells.update((r, c - step) for step in range(1, left + 1))
                cells.update((r, c + step) for step in range(1, right + 1))
                candidates.append(frozenset(cells))
    return candidates


def _t_candidates(h: int, w: int):
    candidates = []
    for missing in range(4):
        directions = [direction for index, direction in enumerate(CARDINAL) if index != missing]
        for r in range(h):
            for c in range(w):
                cells = {(r, c)} | {(r + dr, c + dc) for dr, dc in directions}
                if all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                    candidates.append(frozenset(cells))
    return candidates


def _line_candidates(h: int, w: int, length: int):
    candidates = []
    for r in range(h):
        for c in range(w - length + 1):
            candidates.append(frozenset((r, c + step) for step in range(length)))
    for c in range(w):
        for r in range(h - length + 1):
            candidates.append(frozenset((r + step, c) for step in range(length)))
    return candidates


def _halo(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = set(cells)
    return cells | {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in CARDINAL
    }


def _place_components(h: int, w: int, target_sizes, decoy_kind: str, rng):
    pools = [_cross_candidates(h, w, size) for size in target_sizes]
    if decoy_kind == "t":
        pools.append(_t_candidates(h, w))
    else:
        pools.append(_line_candidates(h, w, rng.choice((2, 3))))
    for pool in pools:
        rng.shuffle(pool)

    chosen: list[frozenset[tuple[int, int]]] = []

    def search(index: int, forbidden: set[tuple[int, int]]) -> bool:
        if index == len(pools):
            return True
        for cells in pools[index]:
            if cells & forbidden:
                continue
            chosen.append(cells)
            if search(index + 1, forbidden | _halo(cells)):
                return True
            chosen.pop()
        return False

    if not search(0, set()):
        raise RuntimeError(
            f"no layout for h={h}, w={w}, targets={tuple(target_sizes)}, decoy={decoy_kind}"
        )
    return chosen


def _target_sizes(profile: str, n_crosses: int, rng) -> list[int]:
    if profile == "small_t":
        return [rng.choice((6, 7, 8)) for _ in range(n_crosses)]
    if profile == "canonical_line":
        if n_crosses == 1:
            return [rng.choice((9, 10, 11, 12, 13))]
        return [9, rng.choice((9, 10))]
    if n_crosses == 1:
        return [rng.choice((7, 8, 10))]
    sizes = [rng.choice((6, 7, 8)), rng.choice((9, 10))]
    rng.shuffle(sizes)
    return sizes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_shape = ctx.draw_rng("canonical_shape").choice(CANONICAL_SHAPES)
    h = _draw_axis(ctx, "grid_h", default_shape[0], 8, 10)
    w = _draw_axis(ctx, "grid_w", default_shape[1], 9, 11)
    default_count = {"small_t": 1, "canonical_line": 1, "mixed_t": 2}[profile]
    n_crosses = _draw_axis(ctx, "n_crosses", default_count, 1, 2)
    rng = ctx.draw_rng("layout")
    sizes = _target_sizes(profile, n_crosses, rng)
    decoy = "line" if profile == "canonical_line" else "t"
    components = _place_components(h, w, sizes, decoy, rng)
    grid = full_grid(h, w, 0)
    for component in components:
        for r, c in component:
            grid[r][c] = 1
    return grid


def _shape_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be sequences"]
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["empty or ragged grid"]
    if not 8 <= len(grid) <= 10 or not 9 <= w <= 11:
        return ["grid dimensions outside the supported 8..10 by 9..11 domain"]
    if any(type(value) is not int for row in grid for value in row):
        return ["cells must be integers (not booleans or floats)"]
    if any(value not in (0, 1) for row in grid for value in row):
        return ["palette must be exactly background 0 and blue 1"]
    if not any(value == 0 for row in grid for value in row):
        return ["background 0 is absent"]
    return []


def _blue_components(grid):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    }
    groups = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        group = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    group.add(point)
                    stack.append(point)
        groups.append(group)
    return groups


def _degree(grid, point) -> int:
    r, c = point
    h, w = len(grid), len(grid[0])
    return sum(
        0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 1
        for dr, dc in CARDINAL
    )


def _target_centers(grid):
    h, w = len(grid), len(grid[0])
    return {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 1
        and all(grid[r + dr][c + dc] == 1 for dr, dc in CARDINAL)
    }


def _is_clean_cross(group, center) -> bool:
    r, c = center
    if not all(rr == r or cc == c for rr, cc in group):
        return False
    for dr, dc in CARDINAL:
        step = 1
        if (r + dr, c + dc) not in group:
            return False
        while (r + step * dr, c + step * dc) in group:
            step += 1
        if any(
            (rr - r) * dr + (cc - c) * dc >= step
            and ((dc == 0 and cc == c) or (dr == 0 and rr == r))
            for rr, cc in group
        ):
            return False
    return True


def _is_line(group) -> bool:
    rows = {r for r, _ in group}
    cols = {c for _, c in group}
    if not 2 <= len(group) <= 3:
        return False
    if len(rows) == 1:
        values = sorted(c for _, c in group)
    elif len(cols) == 1:
        values = sorted(r for r, _ in group)
    else:
        return False
    return values == list(range(values[0], values[-1] + 1))


def _is_t_junction(grid, group) -> bool:
    return len(group) == 4 and sorted(_degree(grid, point) for point in group) == [1, 1, 1, 3]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    groups = _blue_components(grid)
    centers = _target_centers(grid)
    errors = []
    if not 1 <= len(centers) <= 2:
        errors.append(f"expected 1..2 four-way blue intersections, found {len(centers)}")
    if not 2 <= len(groups) <= 3:
        errors.append(f"expected 2..3 disconnected blue components, found {len(groups)}")

    target_groups = []
    for group in groups:
        owned = group & centers
        if owned:
            target_groups.append(group)
            if len(owned) != 1:
                errors.append("a target component must contain exactly one four-way intersection")
            elif not _is_clean_cross(group, next(iter(owned))):
                errors.append("target component is not a clean horizontal/vertical cross")
            if not 5 <= len(group) <= 13:
                errors.append(f"target component size {len(group)} outside 5..13")
    if len(target_groups) != len(centers):
        errors.append("intersection centers and target components do not correspond one-to-one")

    decoys = [group for group in groups if not (group & centers)]
    if len(decoys) > 1:
        errors.append(f"expected at most one decoy component, found {len(decoys)}")
    for group in decoys:
        if not (_is_line(group) or _is_t_junction(grid, group)):
            errors.append("decoy must be a length-2/3 straight line or a unit T-junction")
    return errors


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_crosses": len(_target_centers(grid)),
    }


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in CANONICAL_SHAPES:
        return ["shape is not one of the four canonical profiles"]
    groups = _blue_components(grid)
    centers = _target_centers(grid)
    target_sizes = [len(group) for group in groups if group & centers]
    if any(size < 9 for size in target_sizes):
        return ["canonical target lines have connected size at least 9"]
    decoys = [group for group in groups if not (group & centers)]
    if any(not _is_line(group) for group in decoys):
        return ["canonical distractors are straight lines, not branchpoints"]
    return []


def rule_mirror(grid):
    """Executable mirror of the selected local rule; does not mutate input."""
    out = copy.deepcopy(grid)
    if not grid or not grid[0]:
        return out
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 1 and all(
                grid[r + dr][c + dc] == 1 for dr, dc in CARDINAL
            ):
                out[r][c] = 2
    return out


def _component_limited_rule(grid, predicate):
    out = copy.deepcopy(grid)
    for group in _blue_components(grid):
        if not predicate(group):
            continue
        for r, c in group & _target_centers(grid):
            out[r][c] = 2
    return out


def rival_exact_five_component(grid):
    """Wrong historical shortcut: only isolated five-cell pluses count."""
    return _component_limited_rule(grid, lambda group: len(group) == 5)


def rival_large_component_only(grid):
    """Wrong canonical-compatible shortcut: only components of size >=9 count."""
    return _component_limited_rule(grid, lambda group: len(group) >= 9)


def rival_degree_at_least_three(grid):
    """Wrong canonical-compatible shortcut: mark T-junctions as well."""
    out = copy.deepcopy(grid)
    if not grid or not grid[0]:
        return out
    for group in _blue_components(grid):
        for point in group:
            if _degree(grid, point) >= 3:
                out[point[0]][point[1]] = 2
    return out


SEMANTIC_RIVALS = {
    "exact_five_component": rival_exact_five_component,
    "large_component_only": rival_large_component_only,
    "degree_at_least_three": rival_degree_at_least_three,
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: rival(grid) != rule_mirror(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
CANONICAL_SHORTCUTS = {
    "large_component_only": rival_large_component_only,
    "degree_at_least_three": rival_degree_at_least_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} outside task grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        valid_demos.append(pair)
    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"competitor {name!r} survives every demonstration")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query outside task grammar: {errors[0]}")
        elif "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the selected rule")
    return reasons


def mutation_fixtures():
    blank = full_grid(9, 9, 0)
    wrong_color = full_grid(9, 9, 0); wrong_color[4][4] = 9
    lone_plus = full_grid(9, 9, 0)
    for dr, dc in ((0, 0),) + CARDINAL:
        lone_plus[4 + dr][4 + dc] = 1
    t_only = full_grid(9, 9, 0)
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1)):
        t_only[4 + dr][4 + dc] = 1
    block = full_grid(9, 9, 0)
    for r in range(3, 6):
        for c in range(3, 6):
            block[r][c] = 1
    return [
        ("blank", blank),
        ("wrong_color", wrong_color),
        ("lone_plus", lone_plus),
        ("t_without_target", t_only),
        ("solid_block", block),
    ]
