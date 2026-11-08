"""Canonical-linked curriculum for ARC task ``e3c21120e3d1``.

The selected Racket rule is exact matrix transposition.  The curriculum keeps
canonical scale and sparse-component morphology while requiring every generated
input to distinguish transpose from the other seven dihedral transforms.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "e3c21120e3d1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "f5d00e3992ee"

SUMMARY = (
    "Transpose the whole sparse rectangular grid across its main diagonal: "
    "output[c][r] = input[r][c].  A four-profile curriculum mirrors the "
    "canonical one-color points, two compact blobs, and one blob plus two "
    "same-color singleton distractors, while each input refutes every other "
    "dihedral transform."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "cells are literal ARC integers 0..9 and background is 0",
    "canvas dimensions are 3..8 in each direction",
    "four to six nonzero cells form two to four sparse same-color components",
    "one or two nonzero colors occur",
    "transpose differs from identity, rotations, flips, and anti-transpose",
    "the canonical Racket program remains the label authority",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "3..8",
        "doc": "Exact input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "3..8",
        "doc": "Exact input-grid width.",
    },
    "n_colors": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "1..2",
        "doc": "Exact number of distinct nonzero colors.",
    },
}

# Every Cartesian product of the three declared axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]
Cell = tuple[int, int]
ComponentSpec = tuple[int, int]  # symbolic color index, component size


# The four canonical input profiles, without copied pixels or labels.
_PROFILE_TABLE: dict[str, tuple[int, int, int, str, tuple[ComponentSpec, ...]]] = {
    "two_blobs_4x7": (4, 7, 2, "two_blobs", ((0, 3), (1, 2))),
    "blob_plus_points_5x6": (
        5,
        6,
        2,
        "blob_plus_points",
        ((0, 4), (1, 1), (1, 1)),
    ),
    "mono_points_3x8": (3, 8, 1, "mono_points", ((0, 1),) * 4),
    "blob_plus_points_6x4": (
        6,
        4,
        2,
        "blob_plus_points",
        ((0, 4), (1, 1), (1, 1)),
    ),
}
SCHEDULE_PROFILES = tuple(_PROFILE_TABLE)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_AXIS_LIMITS = {"grid_h": (3, 8), "grid_w": (3, 8), "n_colors": (1, 2)}

# Fixed connected polyomino seeds.  Rotations/reflections are derived below.
_BASE_SHAPES: dict[int, tuple[tuple[Cell, ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)),),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
}


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Fresh-output Python mirror used only by tests and semantic diagnostics."""
    return [list(row) for row in zip(*grid)]


def _identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _rotate_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: Grid) -> Grid:
    return [list(row) for row in reversed(grid)]


def _anti_transpose(grid: Grid) -> Grid:
    return _rotate_180(rule_mirror(grid))


SEMANTIC_RIVALS: dict[str, Rival] = {
    "identity": _identity,
    "rotate_cw": _rotate_cw,
    "rotate_ccw": _rotate_ccw,
    "rotate_180": _rotate_180,
    "flip_left_right": _flip_lr,
    "flip_up_down": _flip_ud,
    "anti_transpose": _anti_transpose,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Rival] = {}


def schedule_profile(seed, sample_index, difficulty=None):
    """Visit all four canonical-scale profiles in every four-example window."""
    del seed
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    position = (int(sample_index) + _BAND_OFFSET[difficulty]) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[position]


def _normalize(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _rotate_shape(cells: Sequence[Cell]) -> tuple[Cell, ...]:
    return _normalize((col, -row) for row, col in cells)


def _reflect_shape(cells: Sequence[Cell]) -> tuple[Cell, ...]:
    return _normalize((row, -col) for row, col in cells)


@lru_cache(maxsize=None)
def _shape_variants(size: int) -> tuple[tuple[Cell, ...], ...]:
    variants: set[tuple[Cell, ...]] = set()
    for base in _BASE_SHAPES[size]:
        current = _normalize(base)
        for _ in range(4):
            variants.add(current)
            variants.add(_reflect_shape(current))
            current = _rotate_shape(current)
    return tuple(sorted(variants))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[Cell] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (row + drow, col + dcol)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _morphology(grid: Grid) -> str:
    components = _components(grid)
    sizes = sorted(len(component["cells"]) for component in components)
    n_colors = len({component["color"] for component in components})
    if n_colors == 1 and sizes == [1, 1, 1, 1]:
        return "mono_points"
    if n_colors == 2 and sizes == [2, 3]:
        return "two_blobs"
    if n_colors == 2 and sizes == [1, 1, 4]:
        return "blob_plus_points"
    return "sparse_components"


def observe_overrides(grid: Grid) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len({value for row in grid for value in row if value != 0}),
    }


def semantic_observables(grid: Grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    truth = rule_mirror(grid)
    return {
        **observe_overrides(grid),
        "morphology": _morphology(grid),
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "component_sizes": sorted(
            len(component["cells"]) for component in _components(grid)
        ),
        "visible_transpose": truth != grid,
        "unique_among_d4": all(truth != rival(grid) for rival in SEMANTIC_RIVALS.values()),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    normalized = _copy_grid(grid)
    height, width = len(normalized), len(normalized[0])
    findings: list[str] = []
    if not (3 <= height <= 8 and 3 <= width <= 8):
        findings.append("canvas dimensions must each be in 3..8")

    nonzero = [value for row in normalized for value in row if value != 0]
    if not (4 <= len(nonzero) <= 6):
        findings.append("expected four to six nonzero cells")
    colors = set(nonzero)
    if not (1 <= len(colors) <= 2):
        findings.append("expected one or two distinct nonzero colors")
    if 0 not in {value for row in normalized for value in row}:
        findings.append("background color 0 must be present")

    components = _components(normalized)
    if not (2 <= len(components) <= 4):
        findings.append("expected two to four same-color connected components")
    if components and max(len(component["cells"]) for component in components) > 4:
        findings.append("connected components may contain at most four cells")

    truth = rule_mirror(normalized)
    if truth == normalized:
        findings.append("transpose must visibly change the input")
    for name, rival in SEMANTIC_RIVALS.items():
        if truth == rival(normalized):
            findings.append(f"transpose is ambiguous with rival {name}")
    return findings


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        low, high = _AXIS_LIMITS[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside declared range {low}..{high}")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: int) -> int:
    low, high = _AXIS_LIMITS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _candidate_placements(
    height: int,
    width: int,
    shape: Sequence[Cell],
    symbolic_color: int,
    occupied: dict[Cell, int],
) -> list[set[Cell]]:
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    candidates: list[set[Cell]] = []
    if shape_h > height or shape_w > width:
        return candidates
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            cells = {(top + row, left + col) for row, col in shape}
            if cells & occupied.keys():
                continue
            # Separate components carrying the same color.  Components of
            # different colors may touch, as in lawful canonical examples.
            if any(
                occupied.get((row + drow, col + dcol)) == symbolic_color
                for row, col in cells
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                continue
            candidates.append(cells)
    return candidates


def _construct_components(
    height: int,
    width: int,
    specs: Sequence[ComponentSpec],
    palette: Sequence[int],
    rng,
) -> Grid:
    for _attempt in range(128):
        occupied: dict[Cell, int] = {}
        complete = True
        for symbolic_color, size in specs:
            placements: list[set[Cell]] = []
            for shape in _shape_variants(size):
                placements.extend(
                    _candidate_placements(
                        height, width, shape, symbolic_color, occupied
                    )
                )
            if not placements:
                complete = False
                break
            chosen = rng.choice(placements)
            for cell in chosen:
                occupied[cell] = symbolic_color
        if not complete:
            continue

        grid = [[0 for _ in range(width)] for _ in range(height)]
        for (row, col), symbolic_color in occupied.items():
            grid[row][col] = palette[symbolic_color]
        if not self_check(grid):
            return grid
    raise RuntimeError(
        f"could not construct an unambiguous sparse transpose witness on {height}x{width}"
    )


def _generic_specs(n_colors: int) -> tuple[ComponentSpec, ...]:
    # These two compact contracts are feasible on every declared 3..8 canvas.
    if n_colors == 1:
        return ((0, 3), (0, 1))
    return ((0, 3), (1, 1))


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_colors, _morph, scheduled_specs = _PROFILE_TABLE[profile]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, overrides, "grid_h", scheduled_h)
    width = _draw_axis(ctx, overrides, "grid_w", scheduled_w)
    n_colors = _draw_axis(ctx, overrides, "n_colors", scheduled_colors)

    # Exact interventions take precedence over the curriculum profile.  The
    # generic construction is deliberately feasible for every Cartesian tuple.
    specs = _generic_specs(n_colors) if any(
        value is not None for value in overrides.values()
    ) else scheduled_specs

    palette = ctx.draw_distinct_colors("colors", n=n_colors, exclude={0})
    grid = _construct_components(
        height,
        width,
        specs,
        palette,
        ctx.draw_rng("layout"),
    )
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "n_colors": n_colors}
    if observed != expected:
        raise AssertionError(f"constructor failed exact axes: {observed!r} != {expected!r}")
    return _copy_grid(grid)


def _rival_disagrees(grid: Grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    f"transpose_not_{name}": (
        lambda grid, rival_name=name: _rival_disagrees(grid, rival_name)
    )
    for name in SEMANTIC_RIVALS
}
SEMANTIC_WITNESSES.update(
    {
        "branch_mono_points": lambda grid: _morphology(grid) == "mono_points",
        "branch_two_blobs": lambda grid: _morphology(grid) == "two_blobs",
        "branch_blob_plus_points": lambda grid: _morphology(grid) == "blob_plus_points",
    }
)
WITNESS_RIVALS = {
    f"transpose_not_{name}": [name] for name in SEMANTIC_RIVALS
}
BRANCH_WITNESSES = (
    "branch_mono_points",
    "branch_two_blobs",
    "branch_blob_plus_points",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite diagnostic: all declared D4 competitors must be refuted by demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Grid]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the transpose")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query outside teaching grammar: {query_errors[0]}")
    else:
        expected_query = rule_mirror(query["input"])
        if query.get("output") is not None and query["output"] != expected_query:
            reasons.append("query output is not the transpose")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if fits_demos and competitor(query["input"]) != rule_mirror(query["input"]):
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
