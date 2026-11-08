"""Generator for E119, "Mark the midpoint".

The selected Racket authority fills the empty midpoint of every same-color pair
whose two cells are aligned on one row or one column and have an even, nonzero
span.  This module generates inputs only; labels remain source-bound to the
canonical Racket rule.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e26763a6f70"
TASK_ID = GENERATOR_ID
RULE_HASH = "dffe1ada0168"
VERSION = "2.0.0"

SUMMARY = (
    "Each nonzero color occurs at two aligned endpoints with an empty integer "
    "midpoint; the rule fills every such midpoint with the endpoint color."
)

INVARIANTS = [
    "background is integer color 0",
    "1..5 distinct active colors each occur exactly twice",
    "each same-color pair is horizontal or vertical with a positive even span",
    "every pair midpoint is initially background and pair endpoint/midpoint cells do not overlap",
    "every generated input contains at least one lawful span other than four",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 5..12; exact canonical anchor every third sample",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 6..14; exact canonical anchor every third sample",
        "valid": "6..14",
    },
    "pairs": {
        "type": "int",
        "default": "difficulty-weighted 1..5; one on canonical anchor samples",
        "valid": "1..5",
    },
}

# Every advertised boundary combination is constructive, including 5x6 with
# five pairs.  Unknown override keys are rejected explicitly in generate().
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CANONICAL_PROFILES = ((5, 7), (7, 6), (7, 7))
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Candidate: (orientation, span, endpoint_a, endpoint_b, midpoint)
_Candidate = tuple[str, int, tuple[int, int], tuple[int, int], tuple[int, int]]


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _has_override(overrides: dict, name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _draw_weighted_int(ctx, name: str, lo: int, hi: int, favored: Iterable[int]) -> int:
    """Strict exact override, otherwise a keyed weighted integer choice."""
    if _has_override(ctx.overrides, name):
        return ctx.draw_int_strict(name, lo, hi)
    options = list(range(lo, hi + 1)) + list(favored)
    return ctx.draw_choice(name, options)


def _draw_axes(ctx, sample_index: int) -> tuple[int, int, int]:
    # A deterministic schedule anchor gives every band exact canonical shape and
    # palette-size support without narrowing any explicit override domain.
    anchor = sample_index % 3 == 0
    if anchor:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h = (
            ctx.draw_int_strict("grid_h", 5, 12)
            if _has_override(ctx.overrides, "grid_h")
            else ctx.draw_choice("grid_h", (profile[0],))
        )
        w = (
            ctx.draw_int_strict("grid_w", 6, 14)
            if _has_override(ctx.overrides, "grid_w")
            else ctx.draw_choice("grid_w", (profile[1],))
        )
        pairs = (
            ctx.draw_int_strict("pairs", 1, 5)
            if _has_override(ctx.overrides, "pairs")
            else ctx.draw_choice("pairs", (1,))
        )
        return h, w, pairs

    if ctx.difficulty == "easy":
        h_favored = (5, 5, 6, 6, 7)
        w_favored = (6, 7, 7, 8)
        pair_favored = (1, 1, 1, 2)
    elif ctx.difficulty == "hard":
        h_favored = (9, 10, 11, 12, 12)
        w_favored = (11, 12, 13, 14, 14)
        pair_favored = (3, 4, 5, 5)
    elif ctx.difficulty == "medium":
        h_favored = (7, 8, 8, 9)
        w_favored = (8, 9, 10, 10)
        pair_favored = (2, 2, 3, 4)
    else:
        h_favored = ()
        w_favored = ()
        pair_favored = ()

    return (
        _draw_weighted_int(ctx, "grid_h", 5, 12, h_favored),
        _draw_weighted_int(ctx, "grid_w", 6, 14, w_favored),
        _draw_weighted_int(ctx, "pairs", 1, 5, pair_favored),
    )


def _all_candidates(h: int, w: int) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for span in range(2, w, 2):
        half = span // 2
        for r in range(h):
            for c in range(w - span):
                candidates.append(
                    ("horizontal", span, (r, c), (r, c + span), (r, c + half))
                )
    for span in range(2, h, 2):
        half = span // 2
        for c in range(w):
            for r in range(h - span):
                candidates.append(
                    ("vertical", span, (r, c), (r + span, c), (r + half, c))
                )
    return candidates


def _candidate_cells(candidate: _Candidate) -> frozenset[tuple[int, int]]:
    return frozenset(candidate[2:])


def _select_candidates(ctx, h: int, w: int, pairs: int) -> list[_Candidate]:
    """Find exactly ``pairs`` disjoint endpoint/midpoint triples.

    The first pair always has span two, which is a lawful counterexample to the
    span-four-only shortcut fitting every canonical demonstration.  With at
    least two pairs, the second has span four in the opposite orientation.  A
    small backtracking search makes all advertised override combinations exact,
    rather than silently dropping pairs after a capped rejection loop.
    """
    first_orientation = "horizontal" if ctx.sample_index % 2 == 0 else "vertical"
    specifications: list[tuple[str | None, int | None]] = [(first_orientation, 2)]
    if pairs >= 2:
        second_orientation = "vertical" if first_orientation == "horizontal" else "horizontal"
        specifications.append((second_orientation, 4))
    specifications.extend([(None, None)] * (pairs - len(specifications)))

    candidates = _all_candidates(h, w)
    ctx.draw_rng("layout").shuffle(candidates)

    def search(
        depth: int,
        occupied: frozenset[tuple[int, int]],
        selected: tuple[_Candidate, ...],
    ) -> tuple[_Candidate, ...] | None:
        if depth == len(specifications):
            return selected
        required_orientation, required_span = specifications[depth]
        for candidate in candidates:
            orientation, span = candidate[0], candidate[1]
            if required_orientation is not None and orientation != required_orientation:
                continue
            if required_span is not None and span != required_span:
                continue
            cells = _candidate_cells(candidate)
            if occupied.isdisjoint(cells):
                result = search(depth + 1, occupied | cells, selected + (candidate,))
                if result is not None:
                    return result
        return None

    result = search(0, frozenset(), ())
    if result is None:  # Defensive: 5x6 has a constructive five-pair packing.
        raise RuntimeError(f"could not place {pairs} midpoint pairs in {h}x{w}")
    return list(result)


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
    h, w, pair_count = _draw_axes(ctx, sample_index)
    placements = _select_candidates(ctx, h, w, pair_count)
    colors = ctx.draw_distinct_colors("colors", n=pair_count, exclude={0})

    grid = full_grid(h, w, 0)
    for color, candidate in zip(colors, placements):
        _orientation, _span, first, second, _midpoint = candidate
        grid[first[0]][first[1]] = color
        grid[second[0]][second[1]] = color
    return grid


def _pair_cells(grid) -> dict[int, list[tuple[int, int]]]:
    cells: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                cells[value].append((r, c))
    return dict(cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the rule-bearing input structure, not just color counts."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (not bool)"]

    cells = _pair_cells(grid)
    if not cells:
        return ["expected at least one nonzero endpoint pair"]

    errors: list[str] = []
    for color in sorted(cells):
        points = cells[color]
        if len(points) != 2:
            errors.append(f"color {color} appears {len(points)} times, expected exactly twice")
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            span = abs(c2 - c1)
            midpoint = (r1, (c1 + c2) // 2)
        elif c1 == c2:
            span = abs(r2 - r1)
            midpoint = ((r1 + r2) // 2, c1)
        else:
            errors.append(f"color {color} endpoints are not row/column aligned")
            continue
        if span <= 0 or span % 2:
            errors.append(f"color {color} has nonpositive or odd endpoint span {span}")
            continue
        mr, mc = midpoint
        if grid[mr][mc] != 0:
            errors.append(f"color {color} midpoint {(mr, mc)} is not background")
    return errors


def strict_canonical_like(grid):
    """Generated-domain validator used by the semantic gate."""
    errors = list(self_check(grid))
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    pair_count = len(_pair_cells(grid))
    if not 5 <= h <= 12:
        errors.append(f"grid_h={h} outside generated domain 5..12")
    if not 6 <= w <= 14:
        errors.append(f"grid_w={w} outside generated domain 6..14")
    if not 1 <= pair_count <= 5:
        errors.append(f"pairs={pair_count} outside generated domain 1..5")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact advertised controls from returned pixels."""
    if self_check(grid):
        raise ValueError("cannot observe overrides on an invalid midpoint-pair grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "pairs": len(_pair_cells(grid)),
    }


def _midpoint_output(grid, *, allowed_spans: set[int] | None = None):
    """Pure task-local oracle used only for declared rival predictions."""
    out = [list(row) for row in grid]
    for color, points in _pair_cells(grid).items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2 and (c1 + c2) % 2 == 0:
            span = abs(c2 - c1)
            mr, mc = r1, (c1 + c2) // 2
        elif c1 == c2 and (r1 + r2) % 2 == 0:
            span = abs(r2 - r1)
            mr, mc = (r1 + r2) // 2, c1
        else:
            continue
        if span and grid[mr][mc] == 0 and (
            allowed_spans is None or span in allowed_spans
        ):
            out[mr][mc] = color
    return out


def _span_four_only(grid):
    """Rival: incorrectly fires only for the span seen in canonical examples."""
    return _midpoint_output(grid, allowed_spans={4})


def _has_non_four_span(grid) -> bool:
    for points in _pair_cells(grid).values():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            span = abs(c2 - c1)
        elif c1 == c2:
            span = abs(r2 - r1)
        else:
            continue
        if span > 0 and span % 2 == 0 and span != 4:
            return True
    return False


SEMANTIC_WITNESSES = {"non_four_span": _has_non_four_span}
SEMANTIC_RIVALS = {"span_four_only": _span_four_only}
WITNESS_RIVALS = {"non_four_span": ["span_four_only"]}
CANONICAL_SHORTCUTS = {"span_four_only": _span_four_only}
LESSON_COMPETITORS = {"span_four_only": _span_four_only}
