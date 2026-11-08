"""Canonical-linked generator for ARC task 1d9a320d33c0.

Each nonzero object is a two-cell same-color domino. A horizontal domino
completes the 2x2 square immediately below it; a vertical domino completes the
2x2 square immediately to its right. Ordinary lessons always contain both
orientations so neither one-branch shortcut can solve a generated example.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d9a320d33c0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "528b7a20c766"

SUMMARY = (
    "A 7..10 by 8..12 zero-background grid contains 2..4 distinct-color "
    "two-cell dominoes, including at least one horizontal and one vertical "
    "domino. Objects may be diagonally adjacent, as in the canonical data, "
    "but their input cells are never edge-adjacent and their 2x2 growth "
    "footprints never overlap. Horizontal dominoes grow one row down; vertical "
    "dominoes grow one column right, completing a solid 2x2 square per object."
)

INVARIANTS = [
    "background is literal ARC color 0",
    "there are 2..4 straight two-cell dominoes in pairwise-distinct colors",
    "every ordinary lesson contains horizontal and vertical dominoes",
    "all growth targets are in bounds, zero, and pairwise non-overlapping",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7..10", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "scheduled 8..12", "valid": "8..12"},
    "domino_count": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}

_CANONICAL_PROFILES = {
    (7, 9, 3),
    (8, 8, 3),
    (7, 10, 3),
    (8, 9, 3),
}
_CANONICAL_SCHEDULE = (
    ("canonical_7x9_3", 7, 9, 3),
    ("canonical_8x8_3", 8, 8, 3),
    ("canonical_7x10_3", 7, 10, 3),
    ("canonical_8x9_3", 8, 9, 3),
)
SCHEDULE_PROFILES = tuple(name for name, *_ in _CANONICAL_SCHEDULE) + (
    "controlled_extrapolation",
)
MIN_STRICT_FRAC = 0.40
EXAMPLES_NEEDED = 3

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_BOUNDS = {
    "grid_h": (7, 10),
    "grid_w": (8, 12),
    "domino_count": (2, 4),
}

# These are explicit negative fixtures for contract tests. They are not axes and
# cannot enter ordinary training data through generate().
DEGENERATE_TEXTURES = ("no_dominoes", "single_cell", "growth_blocked")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic ordinary curriculum branch.

    Four of every eight sample-index residues are exact canonical profiles; the
    other four are bounded scale/count extrapolations. ``seed`` is accepted for
    the shared schedule contract but intentionally does not control branch mass.
    """
    del seed, difficulty
    residue = sample_index % 8
    if residue < len(_CANONICAL_SCHEDULE):
        return _CANONICAL_SCHEDULE[residue][0]
    return "controlled_extrapolation"


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of {sorted(x for x in _ALLOWED_DIFFICULTIES if x is not None)} "
            f"or None, got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _default_axes(ctx, seed: int, sample_index: int, difficulty) -> tuple[int, int, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    for name, height, width, count in _CANONICAL_SCHEDULE:
        if profile == name:
            return height, width, count

    rng = ctx.draw_rng("curriculum_axes")
    height = rng.randint(7, 10)
    width = rng.randint(8, 12)
    count_options = {
        "easy": (2, 3),
        "medium": (2, 3, 4),
        "hard": (3, 4),
        None: (2, 3, 4),
    }[difficulty]
    count = count_options[rng.randrange(len(count_options))]
    return height, width, count


def _draw_axis(ctx, overrides: dict, name: str, default: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    # Record the scheduled value through the same public provenance channel as
    # an override, without randomizing it a second time.
    return ctx.draw_int(name, default, default)


def _input_cells(orientation: str, row: int, col: int) -> frozenset[tuple[int, int]]:
    if orientation == "h":
        return frozenset(((row, col), (row, col + 1)))
    return frozenset(((row, col), (row + 1, col)))


def _footprint(row: int, col: int) -> frozenset[tuple[int, int]]:
    return frozenset(((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)))


def _orthogonally_adjacent(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]) -> bool:
    return any(abs(r1 - r2) + abs(c1 - c2) == 1 for r1, c1 in left for r2, c2 in right)


def _diagonally_adjacent(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]) -> bool:
    return any(abs(r1 - r2) == 1 and abs(c1 - c2) == 1 for r1, c1 in left for r2, c2 in right)


def _compatible(candidate, placed, *, allow_diagonal: bool) -> bool:
    _, _, _, cells, footprint = candidate
    for _, _, _, other_cells, other_footprint in placed:
        if footprint & other_footprint:
            return False
        if _orthogonally_adjacent(cells, other_cells):
            return False
        if not allow_diagonal and _diagonally_adjacent(cells, other_cells):
            return False
    return True


def _orientation_plan(count: int, rng) -> list[str]:
    if count == 2:
        plan = ["h", "v"]
    elif count == 3:
        plan = ["h", "h", "v"] if rng.randrange(2) == 0 else ["h", "v", "v"]
    elif count == 4:
        plan = ["h", "h", "v", "v"]
    else:  # protected by request validation and retained as a local invariant.
        raise ValueError(f"unsupported domino_count {count}")
    rng.shuffle(plan)
    return plan


def _place_dominoes(
    height: int,
    width: int,
    orientations: list[str],
    *,
    want_diagonal: bool,
    rng,
):
    candidates: dict[str, list[tuple]] = {"h": [], "v": []}
    for row in range(height - 1):
        for col in range(width - 1):
            footprint = _footprint(row, col)
            for orientation in ("h", "v"):
                candidates[orientation].append(
                    (orientation, row, col, _input_cells(orientation, row, col), footprint)
                )
    for values in candidates.values():
        rng.shuffle(values)

    placed: list[tuple] = []

    def search(index: int, has_diagonal: bool) -> bool:
        if index == len(orientations):
            return has_diagonal if want_diagonal else True
        orientation = orientations[index]
        for candidate in candidates[orientation]:
            if not _compatible(candidate, placed, allow_diagonal=want_diagonal):
                continue
            creates_diagonal = any(
                _diagonally_adjacent(candidate[3], existing[3]) for existing in placed
            )
            # At the final choice of a diagonal-profile scene, do not explore a
            # branch that cannot satisfy the profile predicate.
            if want_diagonal and index == len(orientations) - 1 and not (
                has_diagonal or creates_diagonal
            ):
                continue
            placed.append(candidate)
            if search(index + 1, has_diagonal or creates_diagonal):
                return True
            placed.pop()
        return False

    if not search(0, False):
        mode = "diagonal" if want_diagonal else "fully separated"
        raise RuntimeError(
            f"could not place {len(orientations)} mixed dominoes in {height}x{width} ({mode})"
        )
    return placed


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
    default_h, default_w, default_count = _default_axes(
        ctx, seed, sample_index, difficulty
    )
    height = _draw_axis(ctx, overrides, "grid_h", default_h)
    width = _draw_axis(ctx, overrides, "grid_w", default_w)
    count = _draw_axis(ctx, overrides, "domino_count", default_count)

    layout_rng = ctx.draw_rng("layout")
    orientations = _orientation_plan(count, layout_rng)
    # Alternating sample-index parity gives both the canonical diagonal-contact
    # regime and a maximally separated regime without relying on chance.
    placements = _place_dominoes(
        height,
        width,
        orientations,
        want_diagonal=(sample_index % 2 == 0),
        rng=layout_rng,
    )
    colors = ctx.draw_rng("colors").sample(range(1, 10), count)

    grid = full_grid(height, width, 0)
    for color, candidate in zip(colors, placements):
        for row, col in candidate[3]:
            grid[row][col] = color
    return grid


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({row_index},{col_index}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _components(grid) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            result.append((color, tuple(sorted(cells))))
    return result


def _orientation(cells: tuple[tuple[int, int], ...]) -> str | None:
    if len(cells) != 2:
        return None
    (row1, col1), (row2, col2) = cells
    if row1 == row2 and col2 == col1 + 1:
        return "h"
    if col1 == col2 and row2 == row1 + 1:
        return "v"
    return None


def _analyze(grid) -> tuple[list[dict], list[str]]:
    height, width, errors = _validate_grid(grid)
    if errors:
        return [], errors
    if not 7 <= height <= 10:
        errors.append(f"height {height} outside 7..10")
    if not 8 <= width <= 12:
        errors.append(f"width {width} outside 8..12")

    raw_components = _components(grid)
    if not 2 <= len(raw_components) <= 4:
        errors.append(f"expected 2..4 domino components, found {len(raw_components)}")

    dominoes: list[dict] = []
    for color, cells in raw_components:
        orientation = _orientation(cells)
        if orientation is None:
            errors.append(
                f"color {color} component must be one straight adjacent two-cell domino, got {cells}"
            )
            continue
        row, col = cells[0]
        if orientation == "h":
            targets = ((row + 1, col), (row + 1, col + 1))
        else:
            targets = ((row, col + 1), (row + 1, col + 1))
        if any(not (0 <= r < height and 0 <= c < width) for r, c in targets):
            errors.append(f"color {color} {orientation} domino has an out-of-bounds growth target")
            continue
        occupied_targets = [(r, c) for r, c in targets if grid[r][c] != 0]
        if occupied_targets:
            errors.append(
                f"color {color} growth targets are occupied at {occupied_targets}"
            )
        dominoes.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "orientation": orientation,
                "targets": frozenset(targets),
                "footprint": frozenset(cells) | frozenset(targets),
            }
        )

    colors = [obj["color"] for obj in dominoes]
    if len(colors) != len(set(colors)):
        errors.append("each domino must use a distinct color")
    orientations = {obj["orientation"] for obj in dominoes}
    if dominoes and orientations != {"h", "v"}:
        errors.append("scene must contain both horizontal and vertical dominoes")

    for left, right in combinations(dominoes, 2):
        if left["footprint"] & right["footprint"]:
            errors.append(
                f"colors {left['color']} and {right['color']} have overlapping growth footprints"
            )
        if _orthogonally_adjacent(left["cells"], right["cells"]):
            errors.append(
                f"colors {left['color']} and {right['color']} touch orthogonally in the input"
            )
    return dominoes, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar and every growth precondition."""
    del difficulty
    dominoes, errors = _analyze(grid)
    if meta and isinstance(meta, dict):
        observed = {
            "grid_h": len(grid) if grid else 0,
            "grid_w": len(grid[0]) if grid and grid[0] else 0,
            "domino_count": len(dominoes),
        }
        for name in AXES:
            if name in meta and meta[name] != observed[name]:
                errors.append(
                    f"meta {name}={meta[name]!r} does not match observed {observed[name]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    dominoes, errors = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe axes on invalid grid: {errors[0]}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "domino_count": len(dominoes),
    }


def _apply_selected(grid, selected: set[str]):
    output = [list(row) for row in grid]
    dominoes, errors = _analyze(grid)
    if errors:
        raise ValueError(f"rule mirror requires a lawful input: {errors[0]}")
    for obj in dominoes:
        if obj["orientation"] in selected:
            for row, col in obj["targets"]:
                output[row][col] = obj["color"]
    return output


def rule_mirror(grid):
    """Independent Python mirror; canonical Racket remains execution authority."""
    return _apply_selected(grid, {"h", "v"})


def _horizontal_only(grid):
    return _apply_selected(grid, {"h"})


def _vertical_only(grid):
    return _apply_selected(grid, {"v"})


def _has_horizontal(grid) -> bool:
    dominoes, errors = _analyze(grid)
    return not errors and any(obj["orientation"] == "h" for obj in dominoes)


def _has_vertical(grid) -> bool:
    dominoes, errors = _analyze(grid)
    return not errors and any(obj["orientation"] == "v" for obj in dominoes)


SEMANTIC_RIVALS = {
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "has_horizontal": _has_horizontal,
    "has_vertical": _has_vertical,
}
WITNESS_RIVALS = {
    "has_horizontal": ["vertical_only"],
    "has_vertical": ["horizontal_only"],
}


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]), len(_components(grid)))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact domino-growth result")
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _draw_from_degenerate(name, rng):
    """Return a named malformed fixture for self-check power tests only."""
    del rng
    height, width = 8, 10
    grid = full_grid(height, width, 0)
    if name == "no_dominoes":
        return grid
    if name == "single_cell":
        grid[2][2] = 4
        grid[5][7] = 6
        grid[7][3] = 7
        return grid
    if name == "growth_blocked":
        grid[2][2] = 4
        grid[2][3] = 4
        grid[3][2] = 7
        grid[3][3] = 7
        return grid
    raise ValueError(f"unknown degenerate fixture {name!r}")
