"""Input sampler for ARC task 2dbcb80623f9: connect clear diagonal pairs.

The unchanged Racket rule is label authority.  This module constructs input
scenes only: each nonzero color appears at two endpoints.  Clear 45-degree
pairs are connectable; non-diagonal pairs are lawful distractors and remain
unchanged.  Axis-aligned distractors are scheduled often enough to refute the
plausible "connect every straight pair" shortcut in every four-pair lesson.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from functools import lru_cache
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2dbcb80623f9"
TASK_ID = GENERATOR_ID
RULE_HASH = "1c2557609ca3"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background 8..14 by 8..14 grid contains 1..4 separated clear "
    "45-degree endpoint pairs and 0..2 non-diagonal same-color distractor "
    "pairs. Each nonzero color occurs exactly twice. For every color whose "
    "two cells lie on a clear 45-degree diagonal, fill the inclusive segment "
    "with that color; leave non-diagonal pairs unchanged. Default lessons "
    "use three foreground colors and regularly include a clear axis-aligned "
    "distractor to distinguish the rule from connecting all straight pairs."
)

INVARIANTS = [
    "background is color 0 and every foreground color appears exactly twice",
    "1..4 endpoint pairs lie on separated 45-degree diagonals with clear interiors",
    "0..2 endpoint pairs are non-diagonal distractors",
    "connectable diagonal footprints are pairwise disjoint and contain no other endpoint",
    "all exact override axes are recoverable from the returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-shape schedule", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "canonical-shape schedule", "valid": "8..14"},
    "n_pairs": {"type": "int", "default": "2 or 3; three foreground colors total", "valid": "1..4"},
    "n_distractors": {"type": "int", "default": "0 or 1; periodic semantic witness", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_SHAPES = ((9, 12), (10, 10), (10, 13), (11, 11))
_BAND_OFFSET = {None: 0, "easy": 1, "medium": 2, "hard": 3}
_AXIS_BOUNDS = {
    "grid_h": (8, 14),
    "grid_w": (8, 14),
    "n_pairs": (1, 4),
    "n_distractors": (0, 2),
}

Point = tuple[int, int]
Segment = tuple[Point, Point, tuple[Point, ...]]
Grid = list[list[int]]


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name: str, default: int) -> int:
    """Record a deterministic scheduled default, but honor the full exact domain."""
    lo, hi = _AXIS_BOUNDS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _segment(a: Point, b: Point) -> Segment:
    dr = (b[0] > a[0]) - (b[0] < a[0])
    dc = (b[1] > a[1]) - (b[1] < a[1])
    cells: list[Point] = [a]
    r, c = a
    while (r, c) != b:
        r += dr
        c += dc
        cells.append((r, c))
    return a, b, tuple(cells)


@lru_cache(maxsize=98)
def _candidate_segments(h: int, w: int, kind: str) -> tuple[Segment, ...]:
    """All unique separated diagonal or axis segments in a canvas."""
    candidates: list[Segment] = []
    if kind == "diagonal":
        directions = ((1, 1), (1, -1))  # unordered segments; both slopes
    elif kind == "axis":
        directions = ((0, 1), (1, 0))
    else:  # pragma: no cover - private misuse guard
        raise ValueError(f"unknown segment kind: {kind}")
    for r in range(h):
        for c in range(w):
            for dr, dc in directions:
                for steps in range(2, 7):
                    b = (r + dr * steps, c + dc * steps)
                    if 0 <= b[0] < h and 0 <= b[1] < w:
                        candidates.append(_segment((r, c), b))
    return tuple(candidates)


def _ordered_candidates(ctx, h: int, w: int, kind: str, preferred_steps: int) -> list[Segment]:
    candidates = list(_candidate_segments(h, w, kind))
    rng = ctx.draw_rng(f"{kind}_segments")
    rng.shuffle(candidates)
    # Stable sort retains the keyed random order among equally preferred lengths.
    candidates.sort(key=lambda seg: abs((len(seg[2]) - 1) - preferred_steps))
    return candidates


def _choose_disjoint(ctx, h: int, w: int, n_pairs: int, n_distractors: int,
                     preferred_steps: int) -> list[tuple[str, Segment]]:
    pools = {
        "diagonal": _ordered_candidates(ctx, h, w, "diagonal", preferred_steps),
        "axis": _ordered_candidates(ctx, h, w, "axis", preferred_steps),
    }
    requested = ["diagonal"] * n_pairs + ["axis"] * n_distractors
    chosen: list[tuple[str, Segment]] = []
    used: set[Point] = set()

    def search(index: int) -> bool:
        if index == len(requested):
            return True
        kind = requested[index]
        for segment in pools[kind]:
            footprint = set(segment[2])
            if footprint & used:
                continue
            chosen.append((kind, segment))
            used.update(footprint)
            if search(index + 1):
                return True
            chosen.pop()
            used.difference_update(footprint)
        return False

    if not search(0):  # Finite exhaustive search; all declared combinations are constructive.
        raise ValueError(
            f"could not construct {n_pairs} diagonal and {n_distractors} distractor pairs "
            f"in {h}x{w}"
        )
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w = _SHAPES[(sample_index + _BAND_OFFSET[difficulty]) % len(_SHAPES)]
    default_distractors = 0 if sample_index % 3 == 0 else 1
    default_pairs = 3 - default_distractors
    h = _draw_axis(ctx, "grid_h", default_h)
    w = _draw_axis(ctx, "grid_w", default_w)
    n_pairs = _draw_axis(ctx, "n_pairs", default_pairs)
    n_distractors = _draw_axis(ctx, "n_distractors", default_distractors)

    preferred_steps = {None: 3, "easy": 2, "medium": 4, "hard": 5}[difficulty]
    segments = _choose_disjoint(ctx, h, w, n_pairs, n_distractors, preferred_steps)
    colors = ctx.draw_rng("colors").sample(range(1, 10), len(segments))
    grid = full_grid(h, w, 0)
    for color, (_kind, (a, b, _footprint)) in zip(colors, segments):
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
    return grid


def _positions(grid: Grid) -> dict[int, list[Point]]:
    found: dict[int, list[Point]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                found[value].append((r, c))
    return dict(found)


def _diagonal_path(a: Point, b: Point) -> tuple[Point, ...] | None:
    dr, dc = b[0] - a[0], b[1] - a[1]
    if dr == 0 or abs(dr) != abs(dc):
        return None
    return _segment(a, b)[2]


def _clear_interior(grid: Grid, path: Iterable[Point]) -> bool:
    cells = tuple(path)
    return all(grid[r][c] == 0 for r, c in cells[1:-1])


def _analyze(grid: Grid) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a nonempty rectangle"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid must be a nonempty rectangle"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {}, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {}, ["cells must be integer colors 0..9 (not booleans)"]
    h = len(grid)
    if not (8 <= h <= 14 and 8 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 8..14")

    groups = _positions(grid)
    n_pairs = 0
    n_distractors = 0
    diagonal_footprints: list[set[Point]] = []
    for color, cells in sorted(groups.items()):
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times (expected exactly 2)")
            continue
        a, b = cells
        path = _diagonal_path(a, b)
        if path is None:
            n_distractors += 1
            continue
        if len(path) < 3:
            errors.append(f"color {color} diagonal endpoints must be separated by background")
            continue
        if not _clear_interior(grid, path):
            errors.append(f"color {color} diagonal interior is not background-only")
            continue
        n_pairs += 1
        diagonal_footprints.append(set(path))

    if not (1 <= n_pairs <= 4):
        errors.append(f"expected 1..4 clear diagonal pairs, found {n_pairs}")
    if not (0 <= n_distractors <= 2):
        errors.append(f"expected 0..2 non-diagonal distractors, found {n_distractors}")

    used: set[Point] = set()
    for footprint in diagonal_footprints:
        overlap = used & footprint
        if overlap:
            errors.append(f"diagonal paths overlap at {sorted(overlap)[:3]}")
            break
        used.update(footprint)

    return {
        "grid_h": h,
        "grid_w": w,
        "n_pairs": n_pairs,
        "n_distractors": n_distractors,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generated/canonical input manifold, including lawful distractors."""
    _stats, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    stats, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return stats


def _solve_selected(grid: Grid, *, include_axis: bool) -> Grid:
    """Supplementary deterministic mirror for named rivals; Racket is authority."""
    out = deepcopy(grid)
    for color, cells in sorted(_positions(grid).items()):
        if len(cells) != 2:
            continue
        a, b = cells
        dr, dc = b[0] - a[0], b[1] - a[1]
        path: tuple[Point, ...] | None = None
        if dr != 0 and abs(dr) == abs(dc):
            path = _segment(a, b)[2]
        elif include_axis and ((dr == 0) ^ (dc == 0)):
            path = _segment(a, b)[2]
        if path is not None and _clear_interior(grid, path):
            for r, c in path:
                out[r][c] = color
    return out


def _axis_or_diagonal(grid: Grid) -> Grid:
    """Plausible wrong rule: connect clear horizontal/vertical pairs too."""
    return _solve_selected(grid, include_axis=True)


def _has_clear_axis_distractor(grid: Grid) -> bool:
    for cells in _positions(grid).values():
        if len(cells) != 2:
            continue
        a, b = cells
        dr, dc = b[0] - a[0], b[1] - a[1]
        if not ((dr == 0) ^ (dc == 0)):
            continue
        path = _segment(a, b)[2]
        if len(path) >= 3 and _clear_interior(grid, path):
            return True
    return False


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "axis_or_diagonal": _axis_or_diagonal,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "axis_distractor": _has_clear_axis_distractor,
}
WITNESS_RIVALS = {"axis_distractor": ["axis_or_diagonal"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite named-rival check; not a proof against arbitrary hypotheses."""
    return [
        f"{name} fits all demonstrations but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
