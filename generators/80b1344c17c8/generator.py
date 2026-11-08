"""Generator for ARC task 80b1344c17c8 — counted quarter-turn orbit.

Row 0 is a tally: its number of nonzero cells is ``k``.  The remaining
rows contain one color-9 anchor and a small monochrome shape.  The oracle
removes the tally row and unions the first ``k`` clockwise quarter-turn
orientations of every shape cell around the anchor, preserving the anchor.

The generated grammar deliberately varies tally placement while keeping the
count authoritative, uses both cardinal and diagonal offsets, and schedules all
four values of ``k`` across consecutive lesson examples.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80b1344c17c8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.2"
RULE_HASH = "d19ea091585d"

SUMMARY = (
    "Count the nonzero cells in row 0 to obtain k. Remove that header row, "
    "then rotate each monochrome shape cell clockwise around the unique "
    "color-9 anchor and union its first k quarter-turn orientations."
)

INVARIANTS = [
    "row 0 contains exactly 1..4 color-1 tally cells and otherwise zeros",
    "the body contains exactly one color-9 anchor with a one-cell margin",
    "the body contains 2..6 cells of one color in 2..8, all adjacent to the anchor",
    "the shape occupies a non-closed subset of one-step anchor offsets",
    "for k>1, at least one rotated cell is newly added",
]

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded within 5..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded within 6..12",
        "valid": "6..12",
    },
    "k_rot": {
        "type": "int",
        "default": "scheduled 1,2,3,4 across sample_index",
        "valid": "1..4",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-banded within 2..6",
        "valid": "2..6",
    },
    "shape_color": {
        "type": "color",
        "default": "keyed draw from 2..8",
        "valid": "2..8",
    },
}

_CARDINAL = ((-1, 0), (0, 1), (1, 0), (0, -1))
_DIAGONAL = ((-1, 1), (1, 1), (1, -1), (-1, -1))
_ALL_OFFSETS = _CARDINAL + _DIAGONAL


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _rotate_cw(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return dc, -dr


def _rotate_ccw(offset: tuple[int, int]) -> tuple[int, int]:
    dr, dc = offset
    return -dc, dr


def _rotations(
    offset: tuple[int, int], count: int, *, clockwise: bool = True
) -> list[tuple[int, int]]:
    turn = _rotate_cw if clockwise else _rotate_ccw
    values: list[tuple[int, int]] = []
    current = offset
    for _ in range(count):
        values.append(current)
        current = turn(current)
    return values


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    header = list(grid[0])
    body = [list(row) for row in grid[1:]]
    body_h = len(body)

    if not (5 <= h <= 12 and 6 <= w <= 12):
        errors.append(f"dims {h}x{w} outside declared envelope 5..12 x 6..12")
    if any(value not in (0, 1) for value in header):
        errors.append("header may contain only 0 and tally color 1")
    k = sum(value != 0 for value in header)
    if not 1 <= k <= 4:
        errors.append(f"header tally count must be 1..4, found {k}")

    anchors = [
        (r, c)
        for r in range(body_h)
        for c in range(w)
        if body[r][c] == 9
    ]
    if len(anchors) != 1:
        errors.append(f"body must contain exactly one color-9 anchor, found {len(anchors)}")
        anchor = None
    else:
        anchor = anchors[0]
        ar, ac = anchor
        if not (1 <= ar < body_h - 1 and 1 <= ac < w - 1):
            errors.append("anchor must have a one-cell body margin")

    shape_cells = [
        (r, c, body[r][c])
        for r in range(body_h)
        for c in range(w)
        if body[r][c] not in (0, 9)
    ]
    shape_colors = sorted({value for _, _, value in shape_cells})
    if not 2 <= len(shape_cells) <= 6:
        errors.append(f"shape must contain 2..6 cells, found {len(shape_cells)}")
    if len(shape_colors) != 1 or not shape_colors or not 2 <= shape_colors[0] <= 8:
        errors.append("shape must be monochrome with one color in 2..8")

    offsets: list[tuple[int, int]] = []
    if anchor is not None:
        ar, ac = anchor
        offsets = [(r - ar, c - ac) for r, c, _ in shape_cells]
        if any(offset not in _ALL_OFFSETS for offset in offsets):
            errors.append("every shape cell must be one king-step from the anchor")
        cardinal_count = sum(offset in _CARDINAL for offset in offsets)
        diagonal_count = sum(offset in _DIAGONAL for offset in offsets)
        if 2 <= k <= 4:
            expanded = {
                rotated
                for offset in offsets
                for rotated in _rotations(offset, k)
            }
            if expanded <= set(offsets):
                errors.append("k>1 shape must gain at least one rotated cell")
    else:
        cardinal_count = diagonal_count = 0

    palette = {value for row in grid for value in row}
    if shape_colors and palette != {0, 1, 9, shape_colors[0]}:
        errors.append("grid must use exactly background, tally, anchor, and shape colors")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "k_rot": k,
        "shape_size": len(shape_cells),
        "shape_color": shape_colors[0] if len(shape_colors) == 1 else None,
        "header": header,
        "body": body,
        "anchor": anchor,
        "offsets": offsets,
        "cardinal_count": cardinal_count,
        "diagonal_count": diagonal_count,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding counted-rotation lessons."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar intentionally stays on the canonical manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "k_rot": analysis["k_rot"],
        "shape_size": analysis["shape_size"],
        "shape_color": analysis["shape_color"],
    }


def _draw_axis(
    ctx,
    label: str,
    valid_lo: int,
    valid_hi: int,
    default_lo: int,
    default_hi: int,
) -> int:
    """Draw a banded default while accepting the full declared override range."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _header_positions(k: int, w: int, mode: int, rng) -> list[int]:
    if mode == 0:
        return list(range(k))
    if mode == 1:
        return list(range(w - k, w))
    if mode == 2:
        if k == 1:
            return [w // 2]
        return sorted(round(i * (w - 1) / (k - 1)) for i in range(k))

    # Mixed edge/interior placement: deliberately not a prefix or suffix.
    if k == 1:
        return [1 + rng.randrange(w - 2)]
    chosen = {0, w - 1}
    interior = list(range(1, w - 1))
    chosen.update(rng.sample(interior, k - 2))
    return sorted(chosen)


def _choose_shape_offsets(rng, shape_size: int, k: int) -> list[tuple[int, int]]:
    min_cardinal = max(1, shape_size - len(_DIAGONAL))
    max_cardinal = min(len(_CARDINAL), shape_size - 1)
    for _ in range(64):
        n_cardinal = rng.randint(min_cardinal, max_cardinal)
        n_diagonal = shape_size - n_cardinal
        offsets = rng.sample(_CARDINAL, n_cardinal) + rng.sample(_DIAGONAL, n_diagonal)
        rng.shuffle(offsets)
        if k == 1:
            return offsets
        expanded = {
            rotated
            for offset in offsets
            for rotated in _rotations(offset, k)
        }
        if expanded <= set(offsets):
            continue
        # k=2 and k=3 are the only demonstrations that can establish turn
        # direction.  Make each such example individually distinguish
        # clockwise from counter-clockwise expansion, so every five-example
        # lesson rebuts the mirror-direction shortcut deterministically.
        direction_can_differ = not (k == 3 and shape_size == 6)
        if k in (2, 3) and direction_can_differ:
            counterclockwise = {
                rotated
                for offset in offsets
                for rotated in _rotations(offset, k, clockwise=False)
            }
            if expanded == counterclockwise:
                continue
        return offsets
    raise AssertionError("could not construct an asymmetric shape")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # Every difficulty band retains a deterministic canonical-scale anchor
    # branch.  The remaining draws expand scale by band, so difficulty changes
    # visual search load without abandoning the task's observed manifold.
    canonical_anchor = (
        "grid_h" not in overrides
        and "grid_w" not in overrides
        and int(sample_index) % 5 == 0
    )
    if canonical_anchor:
        canonical_profile = (5, 6) if (int(sample_index) // 5) % 2 == 0 else (6, 7)
        h = ctx.draw_choice("grid_h", (canonical_profile[0],))
        w = ctx.draw_choice("grid_w", (canonical_profile[1],))
    elif band == "easy":
        h = _draw_axis(ctx, "grid_h", 5, 12, 5, 6)
        w = _draw_axis(ctx, "grid_w", 6, 12, 6, 7)
    elif band == "hard":
        h = _draw_axis(ctx, "grid_h", 5, 12, 8, 12)
        w = _draw_axis(ctx, "grid_w", 6, 12, 9, 12)
    else:
        h = _draw_axis(ctx, "grid_h", 5, 12, 6, 9)
        w = _draw_axis(ctx, "grid_w", 6, 12, 7, 10)

    if band == "easy":
        shape_size = _draw_axis(ctx, "shape_size", 2, 6, 2, 3)
    elif band == "hard":
        shape_size = _draw_axis(ctx, "shape_size", 2, 6, 3, 6)
    else:
        shape_size = _draw_axis(ctx, "shape_size", 2, 6, 2, 5)

    if "k_rot" in overrides and overrides["k_rot"] is not None:
        k = ctx.draw_int("k_rot", 1, 4)
    else:
        # Sequential lessons see 1,2,3,4,1,..., guaranteeing all rule branches.
        k = ctx.draw_choice("k_rot", (1 + int(sample_index) % 4,))
    shape_color = ctx.draw_int("shape_color", 2, 8)
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    header_mode = (int(sample_index) + int(sample_index) // 4 + seed) % 4
    for column in _header_positions(k, w, header_mode, rng):
        grid[0][column] = 1

    body_h = h - 1
    anchor_body_r = rng.randint(1, body_h - 2)
    anchor_c = rng.randint(1, w - 2)
    anchor_grid_r = anchor_body_r + 1
    grid[anchor_grid_r][anchor_c] = 9

    offsets = _choose_shape_offsets(rng, shape_size, k)
    for dr, dc in offsets:
        grid[anchor_grid_r + dr][anchor_c + dc] = shape_color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid counted-rotation lesson: " + "; ".join(errors))
    return grid


def _solve(grid: list[list[int]], *, clockwise: bool = True, forced_k: int | None = None) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    body = analysis["body"]
    body_h, width = len(body), len(body[0])
    ar, ac = analysis["anchor"]
    k = analysis["k_rot"] if forced_k is None else forced_k
    out = full_grid(body_h, width, 0)
    out[ar][ac] = 9
    color = analysis["shape_color"]
    for offset in analysis["offsets"]:
        for dr, dc in _rotations(offset, min(k, 4), clockwise=clockwise):
            r, c = ar + dr, ac + dc
            if 0 <= r < body_h and 0 <= c < width:
                out[r][c] = color
    return out


def _witness_k(expected: int):
    return lambda grid: not _analysis(grid)["errors"] and _analysis(grid)["k_rot"] == expected


def _is_prefix(header: Iterable[int]) -> bool:
    values = list(header)
    k = sum(value != 0 for value in values)
    return values == [1] * k + [0] * (len(values) - k)


SEMANTIC_WITNESSES = {
    "k_1": _witness_k(1),
    "k_2": _witness_k(2),
    "k_3": _witness_k(3),
    "k_4": _witness_k(4),
    "prefix_tally": lambda grid: not _analysis(grid)["errors"]
    and _is_prefix(_analysis(grid)["header"]),
    "nonprefix_tally": lambda grid: not _analysis(grid)["errors"]
    and not _is_prefix(_analysis(grid)["header"]),
    "cardinal_and_diagonal_offsets": lambda grid: not _analysis(grid)["errors"]
    and _analysis(grid)["cardinal_count"] > 0
    and _analysis(grid)["diagonal_count"] > 0,
    "visible_rotation_growth": lambda grid: not _analysis(grid)["errors"]
    and (
        _analysis(grid)["k_rot"] == 1
        or _solve(grid) != _analysis(grid)["body"]
    ),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require examples that disambiguate count, direction, and crop behavior."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        inp = pair.get("input")
        out = pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        expected = _solve(inp)
        if out != expected:
            reasons.append(f"demo {index} does not match counted clockwise rotation")
        analyses.append(analysis)

    if {analysis["k_rot"] for analysis in analyses} != {1, 2, 3, 4}:
        reasons.append("demonstrations must cover every k value 1..4")
    if not any(_is_prefix(analysis["header"]) for analysis in analyses):
        reasons.append("no prefix tally demonstration")
    if not any(not _is_prefix(analysis["header"]) for analysis in analyses):
        reasons.append("no non-prefix tally demonstration")

    # Competing rules must disagree with at least one official demonstration.
    if analyses and all(
        pair.get("output") == analysis["body"]
        for pair, analysis in zip(demos, analyses)
    ):
        reasons.append("body-copy shortcut is not rebutted")
    if analyses and all(
        pair.get("output") == _solve(pair["input"], forced_k=4)
        for pair in demos
    ):
        reasons.append("always-four-turn shortcut is not rebutted")
    if analyses and all(
        pair.get("output") == _solve(pair["input"], clockwise=False)
        for pair in demos
    ):
        reasons.append("counter-clockwise shortcut is not rebutted")

    query_analysis = _analysis(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside teaching grammar")
    return reasons
