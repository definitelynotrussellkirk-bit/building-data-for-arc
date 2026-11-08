"""Constructive sampler for ARC task 3ef5f8be2639.

The canonical Racket authority selects the first color-2 cell and the first
color-3 cell in row-major order, grows a clipped 3x3 square around each, and
paints only their intersection with color 8 on a blank canvas.

The sampler deliberately includes later same-color distractors.  They make the
scan-order selection observable while preserving exact, independently
recoverable override controls.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "3ef5f8be2639"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "020757caefaf"

SUMMARY = (
    "Select the first color-2 and first color-3 cells in row-major order, "
    "grow each to its full 3x3 Chebyshev-radius-1 neighborhood, and paint "
    "their intersection color 8 on a blank canvas. Later color-2/3 cells "
    "are distractors and do not change the selected centers."
)
EXAMPLES_NEEDED = 3

# Every declared axis is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical support plus keyed 7..14 variation",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical support plus keyed 7..14 variation",
        "valid": "7..14",
    },
    "offset_id": {
        "type": "int",
        "default": "scheduled Chebyshev distance 1/2 offset",
        "valid": "0..23",
    },
    "num_2_seeds": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "num_3_seeds": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Stable public offset indexing: the eight distance-1 offsets, then the
# sixteen distance-2 offsets, each in row-major delta order.
OFFSETS: tuple[Cell, ...] = tuple(
    (dr, dc)
    for distance in (1, 2)
    for dr in range(-distance, distance + 1)
    for dc in range(-distance, distance + 1)
    if max(abs(dr), abs(dc)) == distance
)
_OFFSET_TO_ID = {offset: index for index, offset in enumerate(OFFSETS)}

INVARIANTS = [
    "grid dimensions are 7..14",
    "only colors 0, 2, and 3 occur in the input",
    "there are one or two cells of each seed color",
    "the first color-2 and first color-3 cells are interior and at Chebyshev distance 1 or 2",
]


def _validate_grid_shape(grid: Any) -> tuple[int, int, list[str]]:
    issues: list[str] = []
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return 0, 0, ["every row must be a list"]
    width = len(grid[0])
    if width == 0:
        return len(grid), 0, ["grid rows must be non-empty"]
    if any(len(row) != width for row in grid):
        issues.append("grid is ragged")
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool):
                issues.append("grid cells must be integer ARC colors, not booleans")
                return len(grid), width, issues
            if not 0 <= value <= 9:
                issues.append(f"grid contains color outside 0..9: {value}")
                return len(grid), width, issues
    return len(grid), width, issues


def _points(grid: Grid, color: int) -> list[Cell]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _grown(height: int, width: int, center: Cell) -> set[Cell]:
    row, col = center
    return {
        (r, c)
        for r in range(row - 1, row + 2)
        for c in range(col - 1, col + 2)
        if 0 <= r < height and 0 <= c < width
    }


def _paint(height: int, width: int, cells: set[Cell]) -> Grid:
    return [
        [8 if (r, c) in cells else 0 for c in range(width)]
        for r in range(height)
    ]


def _first_pair_output(grid: Grid) -> Grid:
    """Independent Python mirror of the selected Racket rule."""
    height, width = len(grid), len(grid[0])
    two = _points(grid, 2)[0]
    three = _points(grid, 3)[0]
    return _paint(height, width, _grown(height, width, two) & _grown(height, width, three))


def _all_pairs_output(grid: Grid) -> Grid:
    """Plausible rival: grow every 2/3 pair rather than the first pair."""
    height, width = len(grid), len(grid[0])
    cells: set[Cell] = set()
    for two in _points(grid, 2):
        for three in _points(grid, 3):
            cells |= _grown(height, width, two) & _grown(height, width, three)
    return _paint(height, width, cells)


def _distance_two_only_output(grid: Grid) -> Grid:
    """Plausible canonical shortcut: only solve the seen distance-2 case."""
    height, width = len(grid), len(grid[0])
    two = _points(grid, 2)[0]
    three = _points(grid, 3)[0]
    distance = max(abs(two[0] - three[0]), abs(two[1] - three[1]))
    if distance != 2:
        return full_grid(height, width, 0)
    return _first_pair_output(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task-local input domain without raising."""
    del difficulty, meta
    height, width, issues = _validate_grid_shape(grid)
    if issues:
        return issues
    assert isinstance(grid, list)

    if not 7 <= height <= 14:
        issues.append(f"height {height} outside supported range 7..14")
    if not 7 <= width <= 14:
        issues.append(f"width {width} outside supported range 7..14")

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 2, 3})
    if unexpected:
        issues.append(f"unexpected input colors: {unexpected}; expected only 0, 2, 3")

    twos = _points(grid, 2)
    threes = _points(grid, 3)
    if not 1 <= len(twos) <= 2:
        issues.append(f"expected 1..2 color-2 seeds, found {len(twos)}")
    if not 1 <= len(threes) <= 2:
        issues.append(f"expected 1..2 color-3 seeds, found {len(threes)}")
    if not twos or not threes:
        return issues

    two, three = twos[0], threes[0]
    for name, (row, col) in (("first color-2", two), ("first color-3", three)):
        if not (1 <= row < height - 1 and 1 <= col < width - 1):
            issues.append(f"{name} seed {row, col} must have a full 3x3 neighborhood")

    delta = (three[0] - two[0], three[1] - two[1])
    if delta not in _OFFSET_TO_ID:
        issues.append(
            "the selected seed centers must differ by Chebyshev distance 1 or 2; "
            f"observed delta {delta}"
        )
    return issues


def strict_canonical_like(grid) -> list[str]:
    """The lawful sampler domain is the intended canonical generalization."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def observe_overrides(grid: Grid) -> dict[str, int]:
    twos = _points(grid, 2)
    threes = _points(grid, 3)
    if not twos or not threes:
        raise ValueError("cannot observe selected-pair axes without both seed colors")
    delta = (threes[0][0] - twos[0][0], threes[0][1] - twos[0][1])
    if delta not in _OFFSET_TO_ID:
        raise ValueError(f"selected-pair delta {delta} is outside the declared offset domain")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "offset_id": _OFFSET_TO_ID[delta],
        "num_2_seeds": len(twos),
        "num_3_seeds": len(threes),
    }


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    bounds = {
        "grid_h": (7, 14),
        "grid_w": (7, 14),
        "offset_id": (0, len(OFFSETS) - 1),
        "num_2_seeds": (1, 2),
        "num_3_seeds": (1, 2),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"override {name!r} must be an exact integer, got {value!r}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _scheduled_int(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    # A singleton keyed draw records the exact schedule value, allowing the
    # contract checker to compare provenance with the returned grid.
    return ctx.draw_int(name, default, default)


def _dimension_defaults(ctx, sample_index: int, difficulty) -> tuple[int, int]:
    phase = int(sample_index) % 4
    if phase == 0:
        return 7, 7
    if phase == 1:
        return 8, 8
    if phase == 2:
        return (7, 8) if (int(sample_index) // 4) % 2 == 0 else (8, 7)

    ranges = {
        "easy": (7, 9),
        "medium": (8, 11),
        "hard": (10, 14),
        None: (7, 14),
    }
    lo, hi = ranges[difficulty]
    rng = ctx.draw_rng("dimension_schedule")
    return rng.randint(lo, hi), rng.randint(lo, hi)


def _offset_default(ctx, sample_index: int) -> int:
    distance = 1 if int(sample_index) % 2 == 0 else 2
    choices = [index for index, delta in enumerate(OFFSETS) if max(map(abs, delta)) == distance]
    return ctx.draw_rng("offset_schedule").choice(choices)


def _count_defaults(sample_index: int, offset: Cell) -> tuple[int, int]:
    # Every even draw carries one effective later distractor.  Put it in the
    # color whose selected center comes first in row-major order; that always
    # leaves a later near-opposite placement capable of refuting all-pairs.
    if int(sample_index) % 2:
        return 1, 1
    if offset > (0, 0):
        return 2, 1  # color 2 is the earlier selected center
    return 1, 2      # color 3 is the earlier selected center


def _effective_extra(
    candidate: Cell,
    opposite: Cell,
    authoritative: set[Cell],
    height: int,
    width: int,
) -> bool:
    overlap = _grown(height, width, candidate) & _grown(height, width, opposite)
    return bool(overlap - authoritative)


def _extra_candidates(
    *,
    primary: Cell,
    opposite: Cell,
    occupied: set[Cell],
    height: int,
    width: int,
    rng,
) -> list[Cell]:
    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) > primary and (r, c) not in occupied
    ]
    authoritative = _grown(height, width, primary) & _grown(height, width, opposite)
    effective = [
        cell
        for cell in candidates
        if _effective_extra(cell, opposite, authoritative, height, width)
    ]
    other = [cell for cell in candidates if cell not in set(effective)]
    rng.shuffle(effective)
    rng.shuffle(other)
    return effective + other


def _construct_grid(
    *,
    height: int,
    width: int,
    offset: Cell,
    num_2: int,
    num_3: int,
    rng,
    require_effective: bool,
) -> Grid:
    dr, dc = offset
    primary_pairs = [
        ((r, c), (r + dr, c + dc))
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if 1 <= r + dr < height - 1 and 1 <= c + dc < width - 1
    ]
    rng.shuffle(primary_pairs)

    for two, three in primary_pairs:
        occupied = {two, three}
        two_candidates: list[Cell | None]
        three_candidates: list[Cell | None]
        if num_2 == 2:
            two_candidates = _extra_candidates(
                primary=two,
                opposite=three,
                occupied=occupied,
                height=height,
                width=width,
                rng=rng,
            )
        else:
            two_candidates = [None]
        if num_3 == 2:
            three_candidates = _extra_candidates(
                primary=three,
                opposite=two,
                occupied=occupied,
                height=height,
                width=width,
                rng=rng,
            )
        else:
            three_candidates = [None]

        for extra_two, extra_three in product(two_candidates, three_candidates):
            if extra_two is not None and extra_two == extra_three:
                continue
            grid = full_grid(height, width, 0)
            grid[two[0]][two[1]] = 2
            grid[three[0]][three[1]] = 3
            if extra_two is not None:
                grid[extra_two[0]][extra_two[1]] = 2
            if extra_three is not None:
                grid[extra_three[0]][extra_three[1]] = 3

            # The candidate predicates should make these equalities tautological;
            # retaining the checks keeps the construction honest under edits.
            if _points(grid, 2)[0] != two or _points(grid, 3)[0] != three:
                continue
            if self_check(grid):
                continue
            if require_effective and _all_pairs_output(grid) == _first_pair_output(grid):
                continue
            return grid

    raise RuntimeError(
        "no constructive layout for "
        f"grid={height}x{width}, offset={offset}, counts=({num_2},{num_3}), "
        f"require_effective={require_effective}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _dimension_defaults(ctx, sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 7, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 7, 14)
    offset_id = _scheduled_int(
        ctx, overrides, "offset_id", _offset_default(ctx, sample_index), 0, len(OFFSETS) - 1
    )
    offset = OFFSETS[offset_id]
    default_num_2, default_num_3 = _count_defaults(sample_index, offset)
    num_2 = _scheduled_int(ctx, overrides, "num_2_seeds", default_num_2, 1, 2)
    num_3 = _scheduled_int(ctx, overrides, "num_3_seeds", default_num_3, 1, 2)

    explicit_count = any(
        name in overrides and overrides[name] is not None
        for name in ("num_2_seeds", "num_3_seeds")
    )
    require_effective = not explicit_count and num_2 + num_3 > 2
    grid = _construct_grid(
        height=height,
        width=width,
        offset=offset,
        num_2=num_2,
        num_3=num_3,
        rng=ctx.draw_rng("layout"),
        require_effective=require_effective,
    )

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "offset_id": offset_id,
        "num_2_seeds": num_2,
        "num_3_seeds": num_3,
    }
    if observed != expected:
        raise RuntimeError(f"observable-axis mismatch: expected {expected}, observed {observed}")
    return grid


def _valid(grid: Grid) -> bool:
    return not self_check(grid)


def _witness_scan_order_distractor(grid: Grid) -> bool:
    return _valid(grid) and _all_pairs_output(grid) != _first_pair_output(grid)


def _witness_distance_one(grid: Grid) -> bool:
    if not _valid(grid):
        return False
    two, three = _points(grid, 2)[0], _points(grid, 3)[0]
    return max(abs(two[0] - three[0]), abs(two[1] - three[1])) == 1


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "all_pairs": _all_pairs_output,
    "distance_two_only": _distance_two_only_output,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "scan_order_distractor": _witness_scan_order_distractor,
    "distance_one": _witness_distance_one,
}
WITNESS_RIVALS = {
    "scan_order_distractor": ["all_pairs"],
    "distance_one": ["distance_two_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to demonstrate both canonical-fitting distinctions."""
    issues: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        issues.append("query must contain an input grid")
    elif self_check(query["input"]):
        issues.append("query input is outside the lawful task domain")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            issues.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        errors = self_check(grid)
        if errors:
            issues.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = _first_pair_output(grid)
        if demo["output"] != expected:
            issues.append(f"demo {index} output does not match the first-pair rule")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(grid) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            issues.append(f"demonstrations do not refute rival {name}")
    return issues
