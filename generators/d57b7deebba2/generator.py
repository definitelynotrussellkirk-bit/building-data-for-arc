"""Input sampler for ``Fill the Anti-Diagonal Spans`` (d57b7deebba2).

The unchanged Racket authority groups non-background cells by BOTH color and
anti-diagonal ``r+c`` and fills each group from its minimum to maximum row.
This sampler emits two or three empty-interior endpoint spans.  A scheduled
third of the stream reuses one color on separate anti-diagonals, which is a
lawful authority case and a concrete counterexample to the strongest shortcut
left by the public demonstrations: "each color is one global pair".

Outputs are never generated here.  See ``workspace/reference_probe.py`` for an
independent geometry oracle, fixed counterexample, and lesson census.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d57b7deebba2"
TASK_ID = GENERATOR_ID
RULE_HASH = "ed1603229043"
VERSION = "3.0.0"

SUMMARY = (
    "A 7..10 by 10..12 zero-background grid contains two or three colored "
    "endpoint pairs.  Each pair lies on one slope -1 anti-diagonal, has a "
    "length of 2..5, and has an empty interior.  Different spans use different "
    "anti-diagonals.  Colors may be reused across separate anti-diagonals.  "
    "The rule independently fills every color+anti-diagonal span between its "
    "two endpoints."
)

INVARIANTS = [
    "background is integer color 0 and endpoint colors are integers 1..9",
    "there are exactly two or three color+anti-diagonal endpoint groups",
    "each group has exactly two endpoints and span length 2..5",
    "span interiors are empty and spans do not overlap",
    "a color may name more than one span when those spans are on distinct anti-diagonals",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 7..10", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "canonical-weighted 10..12", "valid": "10..12"},
    "n_pairs": {"type": "int", "default": "canonical-weighted 2..3", "valid": "2..3"},
}
# Every advertised boundary and combination is constructively supported in
# every difficulty band.  Difficulty only biases the non-public span lengths.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# Anchors reproduce every public canonical shape/palette profile while still
# presenting full option domains to GenCtx.  Repetition is the established
# corpus pattern for a canonical-density component; the singleton domain values
# remain available and sample-index cycling gives each boundary a regular mass.
_PROFILE_ANCHORS = (
    (7, 12, 3),   # reused color -> palette size 3, exact public profile
    (8, 10, 3),   # distinct colors -> palette size 4
    (9, 11, 3),
    (7, 12, 3),   # reused color -> palette size 3
    (10, 10, 3),
    (7, 12, 2),   # distinct colors -> palette size 3
)
_AXIS_WEIGHT = 100


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum branch used by this sample index."""
    del seed, difficulty
    return "reused_color" if sample_index % 3 == 0 else "distinct_colors"


SCHEDULE_PROFILES = ("reused_color", "distinct_colors")
EXAMPLES_NEEDED = 3


def _weighted_axis(ctx, name: str, domain: range, anchor: int) -> int:
    # Duplicates bias the default but do not narrow override validity.  The
    # exact consumed value is recorded under the public axis name.
    return ctx.draw_choice(name, [anchor] * _AXIS_WEIGHT + list(domain))


@lru_cache(maxsize=12)
def _span_candidates(h: int, w: int):
    """Immutable candidates grouped by anti-diagonal.

    Different anti-diagonals are disjoint by definition, so choosing distinct
    keys is constructive and needs no capped rejection loop.
    """
    grouped: dict[int, list[tuple[tuple[int, int], ...]]] = {}
    for diag in range(h + w - 1):
        cells = tuple((r, diag - r) for r in range(h) if 0 <= diag - r < w)
        options = []
        for start in range(len(cells)):
            for length in range(2, 6):
                stop = start + length
                if stop < len(cells):
                    options.append(cells[start:stop + 1])
        if options:
            grouped[diag] = options
    return tuple((diag, tuple(options)) for diag, options in sorted(grouped.items()))


def _choose_span(options, rng, difficulty):
    by_length: dict[int, list] = {}
    for span in options:
        by_length.setdefault(len(span) - 1, []).append(span)
    lengths = sorted(by_length)
    if difficulty == "easy":
        weighted = lengths + [min(lengths)] * 8
    elif difficulty == "hard":
        weighted = lengths + [max(lengths)] * 8
    else:
        weighted = lengths
    length = rng.choice(weighted)
    return rng.choice(by_length[length])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    anchor_h, anchor_w, anchor_pairs = _PROFILE_ANCHORS[sample_index % len(_PROFILE_ANCHORS)]
    h = _weighted_axis(ctx, "grid_h", range(7, 11), anchor_h)
    w = _weighted_axis(ctx, "grid_w", range(10, 13), anchor_w)
    n_pairs = _weighted_axis(ctx, "n_pairs", range(2, 4), anchor_pairs)

    candidates = dict(_span_candidates(h, w))
    if len(candidates) < n_pairs:  # defensive; impossible in the declared domain
        raise RuntimeError(f"{h}x{w} cannot fit {n_pairs} anti-diagonal spans")
    layout_rng = ctx.draw_rng("layout")
    chosen_diags = layout_rng.sample(sorted(candidates), n_pairs)
    spans = [_choose_span(candidates[diag], layout_rng, difficulty) for diag in chosen_diags]

    color_rng = ctx.draw_rng("colors")
    if schedule_profile(seed, sample_index, difficulty) == "reused_color":
        palette = color_rng.sample(range(1, 10), 2 if n_pairs == 3 else 1)
        colors = [palette[0], palette[0]] + ([palette[1]] if n_pairs == 3 else [])
    else:
        colors = color_rng.sample(range(1, 10), n_pairs)

    grid = full_grid(h, w, 0)
    for color, span in zip(colors, spans):
        (r0, c0), (r1, c1) = span[0], span[-1]
        grid[r0][c0] = color
        grid[r1][c1] = color
    return grid


def _validated_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return None, ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]
    return [list(row) for row in grid], []


def _groups(grid: Iterable[Iterable[int]]):
    grouped: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                grouped.setdefault((color, r + c), []).append((r, c))
    return grouped


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(checked),
        "grid_w": len(checked[0]),
        "n_pairs": len(_groups(checked)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    checked, errors = _validated_grid(grid)
    if errors:
        return errors
    h, w = len(checked), len(checked[0])
    if not 7 <= h <= 10:
        errors.append("grid_h must be in 7..10")
    if not 10 <= w <= 12:
        errors.append("grid_w must be in 10..12")

    grouped = _groups(checked)
    if not 2 <= len(grouped) <= 3:
        errors.append(f"expected 2..3 color+anti-diagonal spans, found {len(grouped)}")

    occupied: set[tuple[int, int]] = set()
    for (color, diag), cells in sorted(grouped.items()):
        if len(cells) != 2:
            errors.append(
                f"color {color} anti-diagonal {diag} must have exactly two endpoints, found {len(cells)}"
            )
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        length = r1 - r0
        if not 2 <= length <= 5:
            errors.append(
                f"color {color} anti-diagonal {diag} span length {length} is outside 2..5"
            )
            continue
        span = [(r, diag - r) for r in range(r0, r1 + 1)]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in span):
            errors.append(f"color {color} anti-diagonal {diag} leaves the grid")
            continue
        overlap = occupied.intersection(span)
        if overlap:
            errors.append(f"anti-diagonal spans overlap at {sorted(overlap)[0]}")
        occupied.update(span)
        for r, c in span[1:-1]:
            if checked[r][c] != 0:
                errors.append(
                    f"color {color} anti-diagonal {diag} interior must be empty at {(r, c)}"
                )
                break
    return sorted(set(errors))


def strict_canonical_like(grid):
    """Lawful instances in the task's selected, generator-supported manifold."""
    return self_check(grid)


def _distinct_color_pairs_only(grid):
    """RIVAL: incorrectly assumes each color names at most one global pair."""
    source = [list(row) for row in grid]
    out = deepcopy(source)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, []).append((r, c))
    for color, cells in by_color.items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        if r0 + c0 != r1 + c1:
            continue
        diag = r0 + c0
        for r in range(r0, r1 + 1):
            out[r][diag - r] = color
    return out


def _has_reused_color(grid):
    counts = Counter(color for color, _diag in _groups(grid))
    return any(value >= 2 for value in counts.values())


SEMANTIC_WITNESSES = {"reused_color": _has_reused_color}
SEMANTIC_RIVALS = {"distinct_color_pairs_only": _distinct_color_pairs_only}
WITNESS_RIVALS = {"reused_color": ["distinct_color_pairs_only"]}
CANONICAL_SHORTCUTS = {"distinct_color_pairs_only": _distinct_color_pairs_only}
LESSON_COMPETITORS = {"distinct_color_pairs_only": _distinct_color_pairs_only}


def lesson_identifiable(demos, query):
    """Return reasons only when the declared canonical-fitting rival survives.

    The query output is available to the review hook.  A rival that fits all
    demos but gives the same query answer is answer-equivalent for that lesson;
    only a query-changing survivor makes the lesson ambiguous.
    """
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(demo["input"]) == demo["output"] for demo in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
