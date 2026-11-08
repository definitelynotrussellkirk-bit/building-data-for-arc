"""Input sampler for ARC task 2038a3a66886, Fill Matching Row Spans.

The selected Racket rule processes every row independently.  For each nonzero
color occurring at least twice in the *input* row, it paints the inclusive span
from that color's leftmost occurrence to its rightmost occurrence.  The
sampler keeps repeated-color spans disjoint so the lesson is order-independent,
then deliberately rotates through triple occurrences, multiple pairs, and
singleton distractors that refute two strong shortcuts fitting every canonical
pair.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2038a3a66886"
TASK_ID = GENERATOR_ID
RULE_HASH = "aefdabd461d1"
VERSION = "3.0.0"
SUMMARY = (
    "In each row independently, every nonzero color appearing at least twice "
    "fills its inclusive leftmost-to-rightmost span. Singleton colors stay "
    "unchanged. Generated repeated-color spans are disjoint and include a gap."
)

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors 0..9",
    "1..6 active rows occur in a 6..18 by 9..22 grid",
    "all active rows use one declared semantic pattern",
    "every repeated color has a zero gap inside its span",
    "different repeated-color spans in one row are disjoint",
    "singleton distractors lie outside repeated-color spans",
]

ROW_PATTERNS = (
    "canonical",
    "triple",
    "multi_pair",
    "distractor",
    "combined",
)
# Lesson assembly consumes consecutive sample indexes.  In every cyclic window
# of three entries there is (a) a color occurring 3x and (b) either two repeated
# colors or a singleton distractor.  Thus every three-demo lesson challenges
# both declared canonical-fitting rivals, independent of its start offset.
SCHEDULE_PROFILES = ROW_PATTERNS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6..18; strongly anchored to a canonical profile",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "9..22; strongly anchored to a canonical profile",
        "valid": "9..22",
    },
    "rows": {
        "type": "int",
        "default": "1..6; strongly anchored to a canonical profile",
        "valid": "1..6",
    },
    "row_pattern": {
        "type": "str",
        "default": "five-entry semantic lesson schedule",
        "valid": "|".join(ROW_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

# (height, width, active rows).  With the canonical row pattern, each active row
# uses a distinct color, so these reproduce all five canonical (h,w,palette)
# profiles exactly without replaying any canonical grid.
_CANONICAL_PROFILES = (
    (7, 10, 3),
    (8, 12, 3),
    (6, 9, 2),
    (9, 11, 3),
    (7, 13, 3),
)
_PATTERN_BY_COUNTS = {
    (2,): "canonical",
    (3,): "triple",
    (2, 2): "multi_pair",
    (1, 2): "distractor",
    (2, 3): "combined",
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic branch for an ordinary draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_options(difficulty) -> tuple[tuple[int, int, int], ...]:
    # Difficulty changes which canonical scale is emphasized, not which
    # advertised overrides are legal.  Every axis domain remains constructive.
    if difficulty == "easy":
        weights = (8, 5, 8, 2, 5)
    elif difficulty == "hard":
        weights = (3, 7, 2, 8, 7)
    else:
        weights = (5, 5, 5, 5, 5)
    return tuple(
        profile
        for profile, weight in zip(_CANONICAL_PROFILES, weights)
        for _ in range(weight)
    )


def _weighted_axis(ctx, name: str, lo: int, hi: int, anchor: int) -> int:
    # The complete range is present in every band; duplicate anchors provide a
    # canonical-scale component while preserving exact override semantics.
    return ctx.draw_choice(name, tuple(range(lo, hi + 1)) + (anchor,) * 80)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "rows"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
    value = overrides.get("row_pattern")
    if value is not None and type(value) is not str:
        raise ValueError(
            f"row_pattern must be a string, not {type(value).__name__}"
        )


@lru_cache(maxsize=70)
def _layouts(width: int, pattern: str):
    """All constructive, order-independent column-role layouts."""
    result: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    if pattern == "canonical":
        result.extend(((a, b), ()) for a, b in combinations(range(width), 2)
                      if b - a >= 2)
    elif pattern == "triple":
        result.extend(((a, b, c), ()) for a, b, c in combinations(range(width), 3)
                      if c - a >= 3)
    elif pattern == "multi_pair":
        result.extend(((a, b), (c, d))
                      for a, b, c, d in combinations(range(width), 4)
                      if b - a >= 2 and d - c >= 2)
    elif pattern == "distractor":
        for a, b, c in combinations(range(width), 3):
            if c - b >= 2:  # singleton left, repeated color on the right
                result.append(((b, c), (a,)))
            if b - a >= 2:  # repeated color left, singleton on the right
                result.append(((a, b), (c,)))
    elif pattern == "combined":
        for a, b, c, d, e in combinations(range(width), 5):
            if b - a >= 2 and e - c >= 3:
                result.append(((a, b), (c, d, e)))
            if c - a >= 3 and e - d >= 2:
                result.append(((d, e), (a, b, c)))
    else:  # defensive: public validation should make this unreachable
        raise ValueError(f"unknown row pattern: {pattern!r}")
    if not result:
        raise ValueError(f"grid width {width} cannot realize {pattern!r}")
    return tuple(result)


def _put_row_pattern(row, pattern: str, color_a: int, color_b: int, rng) -> None:
    first, second = rng.choice(_layouts(len(row), pattern))
    for col in first:
        row[col] = color_a
    for col in second:
        row[col] = color_b


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    target_h, target_w, target_rows = ctx.draw_choice(
        "curriculum_profile", _profile_options(difficulty)
    )
    height = _weighted_axis(ctx, "grid_h", 6, 18, target_h)
    width = _weighted_axis(ctx, "grid_w", 9, 22, target_w)
    n_rows = _weighted_axis(ctx, "rows", 1, 6, target_rows)

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("row_pattern") is not None:
        pattern = ctx.draw_choice("row_pattern", ROW_PATTERNS)
    else:
        pattern = ctx.draw_choice("row_pattern", (scheduled,))

    grid = full_grid(height, width, 0)
    active_rows = ctx.draw_rng("active_rows").sample(range(height), n_rows)
    colors = ctx.draw_rng("row_colors").sample(list(range(1, 10)), 9)
    for index, row_index in enumerate(active_rows):
        if pattern in {"canonical", "triple"}:
            # One distinct row color reproduces the canonical palette counts
            # (background + active rows) for the one-color row families.
            color_a = colors[index]
            color_b = colors[(index + n_rows) % len(colors)]
        else:
            # Reuse a shuffled two-color palette across rows. This keeps the
            # richer semantic families inside canonical palette scale instead
            # of coupling palette size to 2 * active_rows.
            color_a, color_b = colors[:2]
        _put_row_pattern(
            grid[row_index],
            pattern,
            color_a,
            color_b,
            ctx.draw_rng(f"row_layout_{index}"),
        )
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _row_pattern(row) -> str:
    counts = tuple(sorted(Counter(value for value in row if value != 0).values()))
    if counts not in _PATTERN_BY_COUNTS:
        raise ValueError(f"unsupported active-row multiplicities: {counts}")
    return _PATTERN_BY_COUNTS[counts]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors: list[str] = []
    if not 6 <= height <= 18:
        errors.append(f"grid_h={height} outside [6,18]")
    if not 9 <= width <= 22:
        errors.append(f"grid_w={width} outside [9,22]")
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    patterns: list[str] = []
    for row_index, row in enumerate(grid):
        nonzero = [value for value in row if value != 0]
        if not nonzero:
            continue
        try:
            pattern = _row_pattern(row)
        except ValueError as exc:
            errors.append(f"row {row_index}: {exc}")
            continue
        patterns.append(pattern)

        positions = {
            color: [col for col, value in enumerate(row) if value == color]
            for color in dict.fromkeys(nonzero)
        }
        spans = []
        for color, cols in positions.items():
            if len(cols) >= 2:
                lo, hi = cols[0], cols[-1]
                if not any(row[col] == 0 for col in range(lo, hi + 1)):
                    errors.append(
                        f"row {row_index}: color {color} span has no zero gap"
                    )
                spans.append((lo, hi, color))
        spans.sort()
        for left, right in zip(spans, spans[1:]):
            if left[1] >= right[0]:
                errors.append(
                    f"row {row_index}: repeated-color spans overlap "
                    f"({left[2]} and {right[2]})"
                )
        singleton_cols = [
            cols[0] for cols in positions.values() if len(cols) == 1
        ]
        for col in singleton_cols:
            if any(lo <= col <= hi for lo, hi, _ in spans):
                errors.append(
                    f"row {row_index}: singleton lies inside a repeated-color span"
                )

    if not 1 <= len(patterns) <= 6:
        errors.append(f"active rows={len(patterns)} outside [1,6]")
    if len(set(patterns)) > 1:
        errors.append(f"mixed row patterns: {sorted(set(patterns))}")
    return errors


def strict_canonical_like(grid):
    """Return [] exactly for lawful instances in this sampler's manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover all public axis values from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    active = [row for row in grid if any(value != 0 for value in row)]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rows": len(active),
        "row_pattern": _row_pattern(active[0]),
    }


def _outermost_nonzero(grid):
    """RIVAL: paint one span per row using its leftmost nonzero color."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        cols = [col for col, value in enumerate(row) if value != 0]
        if len(cols) >= 2:
            color = row[cols[0]]
            for col in range(cols[0], cols[-1] + 1):
                out[row_index][col] = color
    return out


def _exact_pair_only(grid):
    """RIVAL: fill colors appearing exactly twice; ignore 3+ occurrences."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [col for col, value in enumerate(row) if value == color]
                for col in range(cols[0], cols[-1] + 1):
                    out[row_index][col] = color
    return out


def _has_mixed_row(grid) -> bool:
    return any(
        tuple(sorted(Counter(value for value in row if value != 0).values()))
        in {(2, 2), (1, 2), (2, 3)}
        for row in grid
    )


def _has_triple_occurrence(grid) -> bool:
    return any(
        any(count >= 3 for count in Counter(value for value in row if value != 0).values())
        for row in grid
    )


SEMANTIC_WITNESSES = {
    "mixed_row": _has_mixed_row,
    "triple_occurrence": _has_triple_occurrence,
}
SEMANTIC_RIVALS = {
    "outermost_nonzero": _outermost_nonzero,
    "exact_pair_only": _exact_pair_only,
}
WITNESS_RIVALS = {
    "mixed_row": ["outermost_nonzero"],
    "triple_occurrence": ["exact_pair_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
