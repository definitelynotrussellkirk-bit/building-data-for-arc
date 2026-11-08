"""Generator for ARC task ca8de6ea.

Rule: the input is 5 x 5.  The output is a 3 x 3 grid made from nine
fixed input coordinates (the four corners, the center, and four inner
diagonal positions).  Every other input cell is a decoy.

The default distribution deliberately places foreground decoys outside the
sampled coordinates.  This prevents the canonical sparse presentation from
teaching the shortcut "compress all non-background cells" instead of the
fixed-coordinate rule.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b2f8fcc010d5"
TASK_ID = "b2f8fcc010d5"
VERSION = "2.1.0"  # exact observable axes, structural checker, decoy-rich lessons
RULE_HASH = "f524e4ea450b"

SUMMARY = (
    "Read nine fixed cells from a 5 x 5 grid into a 3 x 3 output; all other "
    "cells are decoys."
)
INVARIANTS = [
    "input is exactly 5 x 5",
    "all nine sampled positions are foreground cells",
    "the sampled positions contain every foreground color used by the input",
    "the output is the sampled positions in fixed row-major order",
]

SAMPLED_POSITIONS = (
    (0, 0), (1, 1), (0, 4),
    (1, 3), (2, 2), (3, 1),
    (4, 0), (3, 3), (4, 4),
)
_SAMPLED_SET = frozenset(SAMPLED_POSITIONS)
_DECOY_POSITIONS = tuple(
    (r, c) for r in range(5) for c in range(5) if (r, c) not in _SAMPLED_SET
)
# These four unsampled cells share the sampled checkerboard parity and are
# therefore 4-disconnected from every sampled cell and from each other.
_ISOLATED_DECOY_POSITIONS = tuple(
    (r, c) for r, c in _DECOY_POSITIONS if (r + c) % 2 == 0
)
_CONNECTING_DECOY_POSITIONS = tuple(
    (r, c) for r, c in _DECOY_POSITIONS if (r + c) % 2 == 1
)

SAMPLED_KINDS = ("corner_anchor", "cross_anchor", "row_anchor")
_ANCHOR_PRIORITIES = {
    "corner_anchor": (0, 8, 2, 6, 1, 7, 3, 5, 4),
    "cross_anchor": (4, 1, 3, 5, 7, 0, 2, 6, 8),
    "row_anchor": tuple(range(9)),
}

AXES = {
    "palette_size": {
        "type": "int",
        "default": "difficulty-skewed 5..9 total colors including background",
        "valid": "5..9",
    },
    "sampled_kind": {
        "type": "str",
        "default": "rng anchor-equality pattern",
        "valid": "|".join(SAMPLED_KINDS),
    },
    "decoy_count": {
        "type": "int",
        "default": "difficulty-skewed 2..5 non-background decoys",
        "valid": "0..15",
    },
}


def _validate_controls(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _draw_decoy_count(ctx, difficulty: str | None) -> int:
    """Draw an exact, grid-observable count while keeping defaults pedagogical."""
    label = "decoy_count"
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = int(ctx.overrides[label])
        if not 0 <= value <= 15:
            raise ValueError(f"{label} override {value} outside [0, 15]")
        return int(ctx._record(label, value, from_override=True))
    lo, hi = {
        "easy": (2, 3),
        "medium": (3, 4),
        "hard": (4, 5),
        None: (2, 5),
    }[difficulty]
    value = ctx.draw_rng(label).randint(lo, hi)
    return int(ctx._record(label, value, from_override=False))


def _sampled_values(kind: str, foreground: list[int]) -> list[int]:
    """Return nine values with an observable equality signature.

    Every foreground color appears at least once.  The first foreground color
    fills 10-m positions, where m is the foreground-palette size; the positions
    of that repeated anchor color encode ``kind``.  Remaining positions receive
    the other colors once each.  Thus the kind is recoverable from the grid
    without hidden metadata for all palette sizes 5..9.
    """
    m = len(foreground)
    anchor_count = 10 - m
    anchor_positions = set(_ANCHOR_PRIORITIES[kind][:anchor_count])
    result: list[int | None] = [None] * 9
    for index in anchor_positions:
        result[index] = foreground[0]
    remaining_colors = iter(foreground[1:])
    for index in range(9):
        if result[index] is None:
            result[index] = next(remaining_colors)
    return [int(value) for value in result]


def _rebut_nonzero_compression(grid: list[list[int]], foreground: list[int]) -> None:
    """Make the decoy shortcut observably wrong without changing any axis.

    A rare color coincidence can make the first nine row-major non-background
    values equal the fixed-coordinate answer even when decoys are present.  In
    that case, recolor the first participating decoy with another already-used
    foreground color.  Shape, palette, decoy count, and sampled semantics stay
    unchanged while the shortcut is deterministically falsified.
    """
    output = [value for row in rule_mirror(grid) for value in row]
    nonzero_positions = [
        (r, c) for r in range(5) for c in range(5) if grid[r][c] != 0
    ]
    if len(nonzero_positions) < 9:
        return
    first_nine = [grid[r][c] for r, c in nonzero_positions[:9]]
    if first_nine != output:
        return
    for index, (r, c) in enumerate(nonzero_positions[:9]):
        if (r, c) in _SAMPLED_SET:
            continue
        replacement = next(color for color in foreground if color != output[index])
        grid[r][c] = replacement
        return
    raise AssertionError("decoys present but none participated in first nine nonzero cells")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    palette_size = int(ctx.draw_int_diff("palette_size", 5, 9))
    sampled_kind = str(ctx.draw_choice("sampled_kind", SAMPLED_KINDS))
    decoy_count = _draw_decoy_count(ctx, difficulty)

    foreground = list(
        ctx.draw_distinct_colors(
            "foreground_palette", n=palette_size - 1, exclude={0}
        )
    )
    grid = full_grid(5, 5, 0)
    for (r, c), value in zip(
        SAMPLED_POSITIONS,
        _sampled_values(sampled_kind, foreground),
        strict=True,
    ):
        grid[r][c] = value

    # Keep at least one background cell so palette_size and decoy_count remain
    # exactly observable. Default bands always create at least two decoys.
    layout_rng = ctx.draw_rng("decoy_layout")
    if decoy_count <= len(_ISOLATED_DECOY_POSITIONS):
        chosen = layout_rng.sample(list(_ISOLATED_DECOY_POSITIONS), decoy_count)
    else:
        chosen = list(_ISOLATED_DECOY_POSITIONS)
        chosen.extend(layout_rng.sample(
            list(_CONNECTING_DECOY_POSITIONS),
            decoy_count - len(_ISOLATED_DECOY_POSITIONS),
        ))
        layout_rng.shuffle(chosen)
    color_order = list(foreground)
    layout_rng.shuffle(color_order)
    for index, (r, c) in enumerate(chosen):
        grid[r][c] = color_order[index % len(color_order)]
    if decoy_count:
        _rebut_nonzero_compression(grid, foreground)
    return grid


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the Racket program remains output authority."""
    values = [grid[r][c] for r, c in SAMPLED_POSITIONS]
    return [values[0:3], values[3:6], values[6:9]]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or len(grid) != 5:
        return ["input must be a 5x5 list-of-lists grid"]
    if any(not isinstance(row, list) or len(row) != 5 for row in grid):
        return ["input must be a 5x5 list-of-lists grid"]
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if bad:
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked teaching grammar without mutating ``grid``.

    Canonical examples are accepted despite having no decoys.  Default generated
    examples additionally contain decoys, but decoy_count=0 remains a lawful
    explicit boundary case.  Minimal marker/line/block impostors fail because all nine
    sampled coordinates and the full foreground palette must be present.
    """
    errors = _grid_errors(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 must remain present")
    if not 5 <= len(palette) <= 9:
        errors.append("input must use 5..9 total colors including background")

    sampled = [grid[r][c] for r, c in SAMPLED_POSITIONS]
    if any(value == 0 for value in sampled):
        errors.append("all nine sampled positions must be non-background")
    sampled_colors = set(sampled)
    foreground = palette - {0}
    if sampled_colors != foreground:
        errors.append("sampled positions must contain every foreground color and no background")
    if len(sampled_colors) < 4:
        errors.append("sampled positions must contain at least four distinct colors")
    return errors


def _infer_sampled_kind(grid: list[list[int]], palette_size: int) -> str:
    sampled = [grid[r][c] for r, c in SAMPLED_POSITIONS]
    counts = Counter(sampled)
    max_count = max(counts.values())
    anchors = [color for color, count in counts.items() if count == max_count]
    if len(anchors) != 1 or max_count != 11 - palette_size:
        raise ValueError("sampled equality pattern does not encode one declared sampled_kind")
    positions = {index for index, value in enumerate(sampled) if value == anchors[0]}
    for kind, priority in _ANCHOR_PRIORITIES.items():
        if positions == set(priority[:max_count]):
            return kind
    raise ValueError("sampled equality pattern does not match a declared sampled_kind")


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette_size = len({value for row in grid for value in row})
    return {
        "palette_size": palette_size,
        "sampled_kind": _infer_sampled_kind(grid, palette_size),
        "decoy_count": sum(grid[r][c] != 0 for r, c in _DECOY_POSITIONS),
    }


def mutation_fixtures():
    """Task-local must-reject near-misses used by the strict defect lint."""
    base = generate(90210, 17, difficulty="medium", palette_size=6,
                    sampled_kind="corner_anchor", decoy_count=8)

    sampled_hole = [row[:] for row in base]
    r, c = SAMPLED_POSITIONS[0]
    sampled_hole[r][c] = 0

    unsampled_only_color = [row[:] for row in base]
    used = {value for row in base for value in row}
    new_color = next(color for color in range(1, 10) if color not in used)
    r, c = _DECOY_POSITIONS[0]
    unsampled_only_color[r][c] = new_color

    too_few_sampled_colors = [row[:] for row in base]
    for index, (r, c) in enumerate(SAMPLED_POSITIONS):
        too_few_sampled_colors[r][c] = 1 + (index % 3)
    for r, c in _DECOY_POSITIONS:
        if too_few_sampled_colors[r][c] not in (0, 1, 2, 3):
            too_few_sampled_colors[r][c] = 1

    no_background = [row[:] for row in base]
    for r in range(5):
        for c in range(5):
            if no_background[r][c] == 0:
                no_background[r][c] = base[SAMPLED_POSITIONS[0][0]][SAMPLED_POSITIONS[0][1]]

    return [
        ("sampled_position_erased", sampled_hole),
        ("foreground_color_only_in_decoys", unsampled_only_color),
        ("sampled_palette_collapsed", too_few_sampled_colors),
        ("background_removed", no_background),
    ]
