"""Inputs for opposite-corner borders, including first-appearance occlusion.

Racket remains the label authority. _predict and the declared alternatives are
pure authoring diagnostics, never returned as generated labels. The two-step
curriculum alternates paired-only scenes with singleton/triple distractors.
"""
from __future__ import annotations

from collections import defaultdict
from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "874aa60956cc"
TASK_ID = GENERATOR_ID
RULE_HASH = "8f9f3652469e"
VERSION = "2.0.0"
SUMMARY = "Draw each exactly-twice color's bounding border in first-appearance order."
INVARIANTS = [
    "integer colors 0..9 on a 5..18 by 5..18 background-0 canvas",
    "1..6 colors occur twice with distinct rows and columns",
    "0..1 singleton colors and 0..1 triple colors are inert under the reference",
    "overlapping borders may overwrite earlier colors, including original clues",
]
AXES = {
    "grid_h": {"type": "int", "default": "5..18, canonical anchor 9", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "5..18, canonical anchor 10", "valid": "5..18"},
    "rectangles": {"type": "int", "default": "3..6, favors 3", "valid": "1..6"},
    "singletons": {"type": "int", "default": "sample_index modulo 2", "valid": "0..1"},
    "triples": {"type": "int", "default": "sample_index modulo 2", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_TRAIN_PAIRS = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("paired", "multiplicity")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _groups(grid):
    result = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                result[color].append((r, c))
    return result


def _predict(grid, policy="intended"):
    """Python diagnostic only; public Racket execution supplies all labels."""
    groups = _groups(grid)
    ordered = list(groups)
    if policy == "completion_order":
        ordered.sort(key=lambda color: groups[color][-1])
    out = [list(row) for row in grid]
    for color in ordered:
        cells = groups[color]
        if len(cells) != 2 and not (policy == "bounding_boxes_for_many" and len(cells) >= 2):
            continue
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        if policy == "positive_diagonal_only" and cells[0][1] > cells[-1][1]:
            continue
        if policy == "min_side_three" and min(r1-r0+1, c1-c0+1) < 3:
            continue
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    if policy == "restore_clues":
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color:
                    out[r][c] = color
    return out


def _distinguishes(grid, policy):
    return _predict(grid) != _predict(grid, policy)


# All five fit the five supplied canonical labeled pairs. This is verified by
# the retained workspace probe and the shared Racket-backed semantic gate.
LESSON_COMPETITORS = {
    name: partial(_predict, policy=name)
    for name in ("positive_diagonal_only", "min_side_three", "completion_order",
                 "restore_clues", "bounding_boxes_for_many")
}
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {
    name: partial(_distinguishes, policy=name) for name in LESSON_COMPETITORS
}
WITNESS_RIVALS = {name: [name] for name in LESSON_COMPETITORS}


def _axis(ctx, name, lo, hi, defaults):
    # Explicit controls always retain the full declared domain. A scheduled
    # default is recorded as the actual choice, never drawn and then replaced.
    values = list(range(lo, hi+1)) if name in ctx.overrides else defaults
    return ctx.draw_choice(name, values)


def _scaffold(h, w, rng):
    # Random positions and spans; the short first row gap provides a 2-cell
    # side. No canonical grid or fixed palette is embedded in this sampler.
    top = rng.randrange(h-4)
    rows = [top, top+1] + sorted(rng.sample(range(top+2, h), 3))
    cols = sorted(rng.sample(range(w), 5))
    pairs = [((rows[0], cols[0]), (rows[4], cols[2])),
             ((rows[0], cols[4]), (rows[1], cols[3])),
             ((rows[1], cols[2]), (rows[3], cols[4]))]
    # Horizontal reflection changes first-appearance ordering as well as
    # diagonal direction. The semantic acceptance below checks the witnesses.
    if rng.randrange(2):
        pairs = [tuple((r, w-1-c) for r, c in pair) for pair in pairs]
    return pairs


def _candidate(h, w, number, singles, triples, rng):
    pairs = _scaffold(h, w, rng) if number >= 3 else []
    used = {point for pair in pairs for point in pair}
    positions = [(r, c) for r in range(h) for c in range(w)]
    # A finite constructive fill realizes every requested pair. With at most
    # 12 occupied cells on a >=5x5 canvas, a non-collinear pair always remains.
    for _ in range(number-len(pairs)):
        free = [p for p in positions if p not in used]
        rng.shuffle(free)
        found = None
        for first in free:
            partners = [p for p in free if p[0] != first[0] and p[1] != first[1]]
            if partners:
                found = first, rng.choice(partners)
                break
        if found is None:
            raise RuntimeError("no non-collinear corner pair; refusing a shortened draw")
        pairs.append(found)
        used.update(found)
    groups = [list(pair) for pair in pairs]
    free = [p for p in positions if p not in used]
    noise = rng.sample(free, singles + 3*triples)
    if singles:
        groups.append([noise.pop()])
    if triples:
        groups.append(noise)
    colors = rng.sample(range(1, 10), len(groups))
    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, groups):
        for r, c in cells:
            grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for key, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{key} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Difficulty changes the distribution, not the legal override domain.
    # All bands keep a substantial exact canonical-shape component.
    h_favored = [8]*15 if difficulty == "easy" else ([14]*15 if difficulty == "hard" else [])
    w_favored = [9]*15 if difficulty == "easy" else ([16]*15 if difficulty == "hard" else [])
    pair_weight = 16 if difficulty == "easy" else (4 if difficulty == "hard" else 12)
    h = _axis(ctx, "grid_h", 5, 18, list(range(5,19)) + [9]*80 + h_favored)
    w = _axis(ctx, "grid_w", 5, 18, list(range(5,19)) + [10]*80 + w_favored)
    number = _axis(ctx, "rectangles", 1, 6, [3]*pair_weight + [4,5,6])
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    singles = _axis(ctx, "singletons", 0, 1, [phase])
    triples = _axis(ctx, "triples", 0, 1, [phase])
    rng = ctx.draw_rng("layout")
    # Controls expose the wider exact structural domain. Unconstrained
    # production lessons additionally require the genuine teaching witnesses.
    required = list(LESSON_COMPETITORS) if triples else list(LESSON_COMPETITORS)[:-1]
    for _ in range(256):
        grid = _candidate(h, w, number, singles, triples, rng)
        if overrides or all(_distinguishes(grid, name) for name in required):
            return grid
    raise RuntimeError("teaching witnesses were masked in 256 draws; no partial lesson emitted")


def observe_overrides(grid):
    counts = [len(cells) for cells in _groups(grid).values()]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "rectangles": counts.count(2), "singletons": counts.count(1),
            "triples": counts.count(3)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (5 <= h <= 18 and 5 <= w <= 18):
        return ["canvas outside declared 5..18 domain"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9"]
    errors = []
    groups = _groups(grid)
    for color, cells in groups.items():
        if len(cells) not in (1, 2, 3):
            errors.append(f"color {color} has {len(cells)} cells; expected 1, 2 or 3")
        if len(cells) == 2 and (cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]):
            errors.append(f"color {color} corners must differ in both row and column")
    counts = observe_overrides(grid)
    if not 1 <= counts["rectangles"] <= 6:
        errors.append("expected 1..6 paired colors")
    if counts["singletons"] > 1 or counts["triples"] > 1:
        errors.append("at most one singleton and one triple color")
    return errors


def strict_canonical_like(grid):
    """Task's structural manifold, allowing lawful overlaps and inert groups."""
    return self_check(grid)
