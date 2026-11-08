"""Generator for ``overlap_after_guided_transform`` (H109).

The command in the upper-left selects one of the canonical dihedral
transform codes.  The right 3x3 occupancy mask is transformed, intersected
with the left mask, and the occupied intersection is painted orange (7).
Panel colors are distractors: only zero versus non-zero matters.
"""
from __future__ import annotations

import hashlib
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8862d66fbb3d"
TASK_ID = "8862d66fbb3d"
RULE_HASH = "6f140febdf35"
VERSION = "3.2.0"
SUMMARY = (
    "A fixed 4x7 input contains a command at (0,0), a left 3x3 motif, and a "
    "right 3x3 motif separated by a blank column. Transform the right motif "
    "according to the command, intersect its nonzero mask with the left "
    "nonzero mask, and output a 3x3 mask colored 7. Panel colors are "
    "irrelevant distractors and may be solid or multicolored."
)

INVARIANTS = [
    "the input is exactly 4x7, with only the command in the first row and a blank separator column",
    "the command is in 1..8 and uses the canonical transform table (commands 4 and 7 both transpose)",
    "each panel has 3..6 nonzero cells and one or two panel-local colors; the panel palettes are disjoint",
    "the commanded transformed-right mask has at least one occupied intersection with the left mask",
]

PALETTE_KINDS = (
    "solid",
    "left_multicolor",
    "right_multicolor",
    "both_multicolor",
)

AXES = {
    "cmd": {
        "type": "int",
        "default": "rng 1..8",
        "valid": "1..8",
    },
    "left_count": {
        "type": "int",
        "default": "feasible rng 3..6",
        "valid": "3..6",
    },
    "right_count": {
        "type": "int",
        "default": "feasible rng 3..6",
        "valid": "3..6",
    },
    "overlap_count": {
        "type": "int",
        "default": "feasible rng 1..4",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "solid|left_multicolor|right_multicolor|both_multicolor",
    },
}

_PANEL_CELLS = tuple((r, c) for r in range(3) for c in range(3))


def _transform_point(point: tuple[int, int], cmd: int) -> tuple[int, int]:
    """Apply the canonical command transform to a 3x3 coordinate."""
    r, c = point
    if cmd == 1:
        return r, c
    if cmd == 2:
        return c, 2 - r
    if cmd == 3:
        return 2 - r, 2 - c
    if cmd in (4, 7):
        return c, r
    if cmd == 5:
        return r, 2 - c
    if cmd == 6:
        return 2 - r, c
    return 2 - c, 2 - r


def _transform_mask(
    cells: Iterable[tuple[int, int]], cmd: int
) -> frozenset[tuple[int, int]]:
    return frozenset(_transform_point(point, cmd) for point in cells)


def _inverse_mask(
    transformed: Iterable[tuple[int, int]], cmd: int
) -> frozenset[tuple[int, int]]:
    inverse = {_transform_point(point, cmd): point for point in _PANEL_CELLS}
    return frozenset(inverse[point] for point in transformed)


def _coerce_override(overrides: dict, name: str, lo: int, hi: int) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, not bool")
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    return value


def _choose_counts(ctx, overrides: dict) -> tuple[int, int, int]:
    """Choose an exact feasible (left, right, overlap) occupancy triple."""
    requested = {
        "left_count": _coerce_override(overrides, "left_count", 3, 6),
        "right_count": _coerce_override(overrides, "right_count", 3, 6),
        "overlap_count": _coerce_override(overrides, "overlap_count", 1, 4),
    }
    feasible = [
        (left_count, right_count, overlap_count)
        for left_count in range(3, 7)
        for right_count in range(3, 7)
        for overlap_count in range(1, 5)
        if overlap_count < min(left_count, right_count)
        and left_count + right_count - overlap_count <= 9
        and all(
            requested[name] is None or requested[name] == value
            for name, value in (
                ("left_count", left_count),
                ("right_count", right_count),
                ("overlap_count", overlap_count),
            )
        )
    ]
    if not feasible:
        raise ValueError(
            "incompatible counts: require overlap_count < both panel counts "
            "and left_count + right_count - overlap_count <= 9"
        )

    if ctx.difficulty == "easy":
        preferred = [
            triple for triple in feasible
            if triple[2] >= 2 and triple[2] / min(triple[0], triple[1]) >= 0.5
        ]
    elif ctx.difficulty == "hard":
        preferred = [
            triple for triple in feasible
            if triple[2] <= 2 and triple[0] + triple[1] - triple[2] >= 7
        ]
    else:
        preferred = feasible
    pool = preferred or feasible
    band_key = str(ctx.difficulty or "mixed")
    triple = ctx.draw_rng(f"count_profile:{band_key}").choice(pool)
    left_count, right_count, overlap_count = triple
    # Record every exact semantic axis through GenCtx. Fixed bounds are used
    # because feasibility was resolved jointly before any value was committed.
    left_count = ctx.draw_int("left_count", left_count, left_count)
    right_count = ctx.draw_int("right_count", right_count, right_count)
    overlap_count = ctx.draw_int("overlap_count", overlap_count, overlap_count)
    return left_count, right_count, overlap_count


def _command_equivalents(cmd: int) -> set[int]:
    return {4, 7} if cmd in (4, 7) else {cmd}


def _scheduled_cmd(seed, sample_index: int) -> int:
    """Give every standard lesson three witnessed transform classes.

    The sequence repeats every three samples, so a query at index 3 (three
    demonstrations) repeats index 0 and a query at index 4 (four
    demonstrations) repeats index 1.  The seed selects three distinct canonical
    transform classes; transpose uses command 4 or 7 per seed so both duplicate
    codes retain corpus support.
    """
    digest = hashlib.sha256(f"{TASK_ID}|{VERSION}|{seed!r}".encode()).digest()
    classes = (1, 2, 0, 3, 5, 6, 8)  # 0 denotes the shared transpose class.
    offset = int.from_bytes(digest[:8], "big") % len(classes)
    command = classes[(offset + (int(sample_index) % 3)) % len(classes)]
    if command == 0:
        return 4 if digest[8] % 2 == 0 else 7
    return command


def _choose_masks(
    *,
    cmd: int,
    left_count: int,
    right_count: int,
    overlap_count: int,
    rng,
) -> tuple[
    frozenset[tuple[int, int]],
    frozenset[tuple[int, int]],
    frozenset[tuple[int, int]],
]:
    """Construct masks with an exact, command-dependent intersection.

    Returned generated instances are deliberately stronger than the canonical
    minimum: the overlap is a proper subset of both motifs, the non-identity
    command visibly moves the right mask, and no non-equivalent command yields
    the same output mask. Canonical answer-equivalent ambiguities remain valid
    and are accepted by ``self_check``; we simply avoid generating new ones.
    """
    all_cells = list(_PANEL_CELLS)
    equivalent = _command_equivalents(cmd)
    for _ in range(512):
        overlap = frozenset(rng.sample(all_cells, overlap_count))
        remaining = [point for point in all_cells if point not in overlap]
        left_only = frozenset(rng.sample(remaining, left_count - overlap_count))
        remaining = [point for point in remaining if point not in left_only]
        transformed_only = frozenset(
            rng.sample(remaining, right_count - overlap_count)
        )
        left = overlap | left_only
        transformed_right = overlap | transformed_only
        right = _inverse_mask(transformed_right, cmd)

        if cmd != 1 and right == transformed_right:
            continue
        outputs = {
            code: left & _transform_mask(right, code) for code in range(1, 9)
        }
        if any(
            outputs[code] == overlap
            for code in range(1, 9)
            if code not in equivalent
        ):
            continue
        return frozenset(left), frozenset(right), overlap
    raise ValueError(
        "could not construct a command-discriminating mask for the requested axes"
    )


def _palette_sizes(kind: str) -> tuple[int, int]:
    return (
        2 if kind in ("left_multicolor", "both_multicolor") else 1,
        2 if kind in ("right_multicolor", "both_multicolor") else 1,
    )


def _choose_palettes(kind: str, rng) -> tuple[tuple[int, ...], tuple[int, ...]]:
    left_size, right_size = _palette_sizes(kind)
    total = left_size + right_size
    non_answer = [1, 2, 3, 4, 5, 6, 8, 9]
    answer_role = rng.choice(("absent", "left", "right"))
    if answer_role == "absent":
        chosen = rng.sample(non_answer, total)
        return tuple(chosen[:left_size]), tuple(chosen[left_size:])

    other = rng.sample(non_answer, total - 1)
    if answer_role == "left":
        left = [7] + other[: left_size - 1]
        right = other[left_size - 1 :]
    else:
        left = other[:left_size]
        right = [7] + other[left_size:]
    rng.shuffle(left)
    rng.shuffle(right)
    return tuple(left), tuple(right)


def _paint_cells(
    grid: list[list[int]],
    cells: frozenset[tuple[int, int]],
    palette: tuple[int, ...],
    *,
    row_offset: int,
    col_offset: int,
    overlap_cells: frozenset[tuple[int, int]],
    rng,
) -> None:
    ordered = list(cells)
    rng.shuffle(ordered)
    assignments: dict[tuple[int, int], int] = {}

    # When orange appears inside a panel, put one orange distractor outside the
    # true answer mask. This prevents "copy the orange cells" from solving the
    # generated pair while retaining canonical color-role variety.
    remaining_colors = list(palette)
    if 7 in remaining_colors:
        non_overlap = [point for point in ordered if point not in overlap_cells]
        chosen = rng.choice(non_overlap)
        assignments[chosen] = 7
        remaining_colors.remove(7)

    unused_points = [point for point in ordered if point not in assignments]
    for color, point in zip(remaining_colors, unused_points):
        assignments[point] = color
    for point in ordered:
        assignments.setdefault(point, rng.choice(palette))

    for (r, c), color in assignments.items():
        grid[row_offset + r][col_offset + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    cmd_override = _coerce_override(overrides, "cmd", 1, 8)
    scheduled_cmd = (
        cmd_override if cmd_override is not None else _scheduled_cmd(seed, sample_index)
    )
    cmd = ctx.draw_int("cmd", scheduled_cmd, scheduled_cmd)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    left_count, right_count, overlap_count = _choose_counts(ctx, overrides)
    left, right, overlap = _choose_masks(
        cmd=cmd,
        left_count=left_count,
        right_count=right_count,
        overlap_count=overlap_count,
        rng=ctx.draw_rng(f"mask_layout:{difficulty or 'mixed'}"),
    )

    left_palette, right_palette = _choose_palettes(
        palette_kind, ctx.draw_rng(f"palette:{difficulty or 'mixed'}")
    )
    grid = full_grid(4, 7, 0)
    grid[0][0] = cmd
    _paint_cells(
        grid,
        left,
        left_palette,
        row_offset=1,
        col_offset=0,
        overlap_cells=overlap,
        rng=ctx.draw_rng(f"left_texture:{difficulty or 'mixed'}"),
    )
    right_overlap = _inverse_mask(overlap, cmd)
    _paint_cells(
        grid,
        right,
        right_palette,
        row_offset=1,
        col_offset=4,
        overlap_cells=right_overlap,
        rng=ctx.draw_rng(f"right_texture:{difficulty or 'mixed'}"),
    )
    return grid


def _panel_state(grid: list[list[int]]) -> tuple[
    int,
    frozenset[tuple[int, int]],
    frozenset[tuple[int, int]],
    frozenset[int],
    frozenset[int],
]:
    cmd = grid[0][0]
    left = frozenset(
        (r, c)
        for r in range(3)
        for c in range(3)
        if grid[1 + r][c] != 0
    )
    right = frozenset(
        (r, c)
        for r in range(3)
        for c in range(3)
        if grid[1 + r][4 + c] != 0
    )
    left_colors = frozenset(grid[1 + r][c] for r, c in left)
    right_colors = frozenset(grid[1 + r][4 + c] for r, c in right)
    return cmd, left, right, left_colors, right_colors


def observe_overrides(grid):
    cmd, left, right, left_colors, right_colors = _panel_state(grid)
    if len(left_colors) == 1 and len(right_colors) == 1:
        palette_kind = "solid"
    elif len(left_colors) == 2 and len(right_colors) == 1:
        palette_kind = "left_multicolor"
    elif len(left_colors) == 1 and len(right_colors) == 2:
        palette_kind = "right_multicolor"
    elif len(left_colors) == 2 and len(right_colors) == 2:
        palette_kind = "both_multicolor"
    else:
        palette_kind = "invalid"
    overlap = left & _transform_mask(right, cmd)
    return {
        "cmd": cmd,
        "left_count": len(left),
        "right_count": len(right),
        "overlap_count": len(overlap),
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors: list[str] = []
    if (
        not isinstance(grid, list)
        or len(grid) != 4
        or any(not isinstance(row, list) or len(row) != 7 for row in grid)
    ):
        return ["grid must be exactly 4x7"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors
    if not 1 <= grid[0][0] <= 8:
        errors.append("cmd at (0,0) must be in 1..8")
    if any(grid[0][c] != 0 for c in range(1, 7)):
        errors.append("the first row may contain only the command at (0,0)")
    if any(grid[r][3] != 0 for r in range(1, 4)):
        errors.append("column 3 must remain the blank panel separator")
    if errors:
        return errors

    cmd, left, right, left_colors, right_colors = _panel_state(grid)
    if not 3 <= len(left) <= 6:
        errors.append("left panel must contain 3..6 nonzero cells")
    if not 3 <= len(right) <= 6:
        errors.append("right panel must contain 3..6 nonzero cells")
    if not 1 <= len(left_colors) <= 2:
        errors.append("left panel must use one or two nonzero colors")
    if not 1 <= len(right_colors) <= 2:
        errors.append("right panel must use one or two nonzero colors")
    if left_colors & right_colors:
        errors.append("left and right panel palettes must be disjoint")

    transformed_right = _transform_mask(right, cmd)
    if left and right and not (left & transformed_right):
        errors.append("commanded transformed-right mask must overlap the left mask")
    if cmd != 1 and right == transformed_right:
        errors.append("non-identity command must visibly transform the right mask")
    return errors
