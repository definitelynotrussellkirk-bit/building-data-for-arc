"""Constructive sampler for the template-at-every-mask stamping task.

The unchanged Racket authority extracts the tightly normalized color-2 shape,
places that shape in color 8 with its bounding-box origin at every color-3
cell, unions all stamp cells on a fresh blank canvas, and discards the input
objects.  This source generates inputs only; :func:`rule_mirror` is an
independent test oracle for source-bound regression and semantic probes.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "93b39d8c4da4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d20fb64e7b01"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains one connected color-2 template and 2..7 "
    "isolated color-3 mask cells. Tight-normalize the template by its bounding "
    "box. On a fresh blank canvas, stamp that shape in color 8 with offset "
    "(0,0) at every mask cell; keep the union when stamps overlap. Discard the "
    "original template and mask cells."
)

INVARIANTS = [
    "grid is rectangular, 12..18 rows by 14..20 columns, using only 0, 2, and 3",
    "exactly one 4-connected color-2 template from the declared 3..5-cell bank",
    "2..7 pairwise 4-neighbor-isolated color-3 mask cells, separate from the template",
    "the normalized template fits in-bounds at every mask and its input stamp area avoids the template",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical size or full-domain difficulty weighting",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical size or full-domain difficulty weighting",
        "valid": "14..20",
    },
    "template_id": {
        "type": "int",
        "default": "scheduled canonical/offset/full-bank choice",
        "valid": "0..17",
    },
    "n_marks": {
        "type": "int",
        "default": "3..4 normally; 5..7 on the many-marks profile",
        "valid": "2..7",
    },
    "layout_mode": {
        "type": "str",
        "default": "overlap on the overlap profile; separated otherwise",
        "valid": "separated|overlap",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# All shapes are tight-normalized, unique, and 4-connected.  The first five
# are the five canonical training shapes.  Several shapes intentionally omit
# (0,0): this distinguishes bounding-box anchoring from anchoring the first
# occupied template cell.
TEMPLATE_BANK: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
)
_TEMPLATE_TO_ID = {shape: index for index, shape in enumerate(TEMPLATE_BANK)}
_CANONICAL_TEMPLATE_IDS = (0, 1, 2, 3, 4)
_OFFSET_TEMPLATE_IDS = tuple(
    index for index, shape in enumerate(TEMPLATE_BANK) if (0, 0) not in shape
)
_CANONICAL_SIZES = ((12, 14), (12, 15), (12, 16), (13, 15), (13, 16), (14, 16))
_LAYOUT_MODES = ("separated", "overlap")

SCHEDULE_PROFILES = (
    "canonical_profile",
    "offset_anchor",
    "many_marks",
    "overlap",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle source-bound profiles; every four consecutive slots cover all."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    integer_bounds = {
        "grid_h": (12, 18),
        "grid_w": (14, 20),
        "template_id": (0, len(TEMPLATE_BANK) - 1),
        "n_marks": (2, 7),
    }
    for name, (lo, hi) in integer_bounds.items():
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if value is not None and not (lo <= value <= hi):
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    layout = overrides.get("layout_mode")
    if layout is not None and type(layout) is not str:
        raise ValueError("layout_mode must be a string")
    if layout is not None and layout not in _LAYOUT_MODES:
        raise ValueError(
            f"layout_mode override {layout!r} outside {_LAYOUT_MODES!r}"
        )


def _weighted_values(lo: int, hi: int, difficulty: str | None) -> tuple[int, ...]:
    values = list(range(lo, hi + 1))
    if difficulty == "easy":
        values.extend(range(lo, min(hi, lo + 2) + 1))
    elif difficulty == "hard":
        values.extend(range(max(lo, hi - 2), hi + 1))
    return tuple(values)


def _draw_int_axis(
    ctx,
    label: str,
    lo: int,
    hi: int,
    *,
    default: int | None = None,
    difficulty: str | None = None,
) -> int:
    """Honor exact overrides against full bounds; otherwise record a real draw."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    if default is not None:
        return int(ctx.draw_choice(label, (default,)))
    return int(ctx.draw_choice(label, _weighted_values(lo, hi, difficulty)))


def _draw_choice_axis(ctx, label: str, options: tuple[Any, ...], default: Any | None) -> Any:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    if default is not None:
        return ctx.draw_choice(label, (default,))
    return ctx.draw_choice(label, options)


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _stamp_cells(
    anchor: tuple[int, int], shape: tuple[tuple[int, int], ...]
) -> frozenset[tuple[int, int]]:
    r, c = anchor
    return frozenset((r + dr, c + dc) for dr, dc in shape)


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _candidate_anchors(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    template_cells: frozenset[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    th, tw = _shape_size(shape)
    candidates = []
    for r in range(h - th + 1):
        for c in range(w - tw + 1):
            anchor = (r, c)
            stamp = _stamp_cells(anchor, shape)
            if stamp & template_cells:
                continue
            if any(_manhattan(anchor, point) <= 1 for point in template_cells):
                continue
            candidates.append(anchor)
    return tuple(candidates)


def _marks_compatible(
    candidate: tuple[int, int],
    selected: tuple[tuple[int, int], ...],
    stamps: dict[tuple[int, int], frozenset[tuple[int, int]]],
    *,
    separated: bool,
) -> bool:
    if any(_manhattan(candidate, other) <= 1 for other in selected):
        return False
    if separated and any(stamps[candidate] & stamps[other] for other in selected):
        return False
    return True


def _extend_marks(
    selected: tuple[tuple[int, int], ...],
    pool: tuple[tuple[int, int], ...],
    n_marks: int,
    stamps: dict[tuple[int, int], frozenset[tuple[int, int]]],
    *,
    separated: bool,
) -> tuple[tuple[int, int], ...] | None:
    """First-solution bounded backtracking over a finite constructive domain."""
    if len(selected) == n_marks:
        return selected
    need = n_marks - len(selected)
    if len(pool) < need:
        return None
    for index, candidate in enumerate(pool):
        if not _marks_compatible(candidate, selected, stamps, separated=separated):
            continue
        result = _extend_marks(
            selected + (candidate,),
            pool[index + 1 :],
            n_marks,
            stamps,
            separated=separated,
        )
        if result is not None:
            return result
    return None


def _select_marks(
    candidates: tuple[tuple[int, int], ...],
    shape: tuple[tuple[int, int], ...],
    n_marks: int,
    layout_mode: str,
    rng,
) -> tuple[tuple[int, int], ...] | None:
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    ordered = tuple(shuffled)
    stamps = {anchor: _stamp_cells(anchor, shape) for anchor in ordered}

    if layout_mode == "separated":
        return _extend_marks((), ordered, n_marks, stamps, separated=True)

    overlap_pairs = [
        (a, b)
        for index, a in enumerate(ordered)
        for b in ordered[index + 1 :]
        if _manhattan(a, b) > 1 and stamps[a] & stamps[b]
    ]
    rng.shuffle(overlap_pairs)
    for a, b in overlap_pairs:
        remainder = tuple(point for point in ordered if point not in (a, b))
        result = _extend_marks((a, b), remainder, n_marks, stamps, separated=False)
        if result is not None:
            return result
    return None


def _construct_scene(
    ctx,
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    n_marks: int,
    layout_mode: str,
) -> list[list[int]]:
    th, tw = _shape_size(shape)
    origins = [(r, c) for r in range(h - th + 1) for c in range(w - tw + 1)]
    ctx.draw_rng("template_position").shuffle(origins)
    mark_rng = ctx.draw_rng("mark_positions")

    for r0, c0 in origins:
        template_cells = frozenset((r0 + dr, c0 + dc) for dr, dc in shape)
        candidates = _candidate_anchors(h, w, shape, template_cells)
        marks = _select_marks(candidates, shape, n_marks, layout_mode, mark_rng)
        if marks is None:
            continue
        grid = full_grid(h, w, 0)
        for r, c in template_cells:
            grid[r][c] = 2
        for r, c in marks:
            grid[r][c] = 3
        return grid
    raise RuntimeError(
        "constructive placement proof failed for a documented axis combination"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    canonical_size = None
    if profile == "canonical_profile":
        canonical_size = ctx.draw_rng("canonical_size").choice(_CANONICAL_SIZES)
    h = _draw_int_axis(
        ctx,
        "grid_h",
        12,
        18,
        default=canonical_size[0] if canonical_size else None,
        difficulty=difficulty,
    )
    w = _draw_int_axis(
        ctx,
        "grid_w",
        14,
        20,
        default=canonical_size[1] if canonical_size else None,
        difficulty=difficulty,
    )

    if profile == "canonical_profile":
        template_options = _CANONICAL_TEMPLATE_IDS
    elif profile == "offset_anchor":
        template_options = _OFFSET_TEMPLATE_IDS
    else:
        template_options = tuple(range(len(TEMPLATE_BANK)))
    template_id = int(
        _draw_choice_axis(
            ctx,
            "template_id",
            tuple(range(len(TEMPLATE_BANK))),
            ctx.draw_rng("scheduled_template").choice(template_options)
            if ctx.overrides.get("template_id") is None
            else None,
        )
    )

    if profile == "many_marks":
        scheduled_marks = ctx.draw_rng("scheduled_mark_count").choice((5, 6, 7))
    elif profile == "canonical_profile":
        scheduled_marks = ctx.draw_rng("scheduled_mark_count").choice((3, 4))
    else:
        scheduled_marks = ctx.draw_rng("scheduled_mark_count").choice((2, 3, 4))
    n_marks = _draw_int_axis(
        ctx,
        "n_marks",
        2,
        7,
        default=scheduled_marks,
        difficulty=difficulty,
    )

    scheduled_layout = "overlap" if profile == "overlap" else "separated"
    layout_mode = str(
        _draw_choice_axis(ctx, "layout_mode", _LAYOUT_MODES, scheduled_layout)
    )

    grid = _construct_scene(
        ctx, h, w, TEMPLATE_BANK[template_id], n_marks, layout_mode
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != expected[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={expected[axis]!r} "
                f"observed={observed[axis]!r}"
            )
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return None
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return None
    return len(grid), w


def _normalized_template(
    grid: list[list[int]],
) -> tuple[tuple[tuple[int, int], ...], tuple[int, int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not cells:
        raise ValueError("missing color-2 template")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    shape = tuple(sorted((r - r0, c - c0) for r, c in cells))
    return shape, (r0, c0)


def _marks(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    issues: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        issues.append(f"unknown difficulty {difficulty!r}")

    size = _grid_shape(grid)
    if size is None:
        return issues + ["grid must be a non-empty rectangular list of lists"]
    h, w = size
    if not (12 <= h <= 18):
        issues.append(f"grid height must be 12..18, got {h}")
    if not (14 <= w <= 20):
        issues.append(f"grid width must be 14..20, got {w}")

    foreign = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or value not in (0, 2, 3)
        },
        key=repr,
    )
    if foreign:
        issues.append(f"grid may use only colors 0, 2, and 3; found {foreign!r}")
        return issues

    comps2 = components(grid, colors={2}, same_color=True)
    if len(comps2) != 1:
        issues.append(f"expected one connected color-2 template, got {len(comps2)}")
        return issues

    cells2 = frozenset(tuple(cell) for cell in comps2[0]["cells"])
    if not (3 <= len(cells2) <= 5):
        issues.append(f"template size must be 3..5, got {len(cells2)}")
    shape, _ = _normalized_template(grid)
    if shape not in _TEMPLATE_TO_ID:
        issues.append(f"template shape is outside the declared bank: {shape!r}")

    marks = _marks(grid)
    if not (2 <= len(marks) <= 7):
        issues.append(f"expected 2..7 color-3 mask cells, got {len(marks)}")

    if shape in _TEMPLATE_TO_ID:
        th, tw = _shape_size(shape)
        for mark in marks:
            r, c = mark
            if r + th > h or c + tw > w:
                issues.append(f"mask {mark} cannot fit the normalized template in-bounds")
                continue
            if _stamp_cells(mark, shape) & cells2:
                issues.append(f"mask {mark}'s input stamp area overlaps the template")

    for index, mark in enumerate(marks):
        if any(_manhattan(mark, other) <= 1 for other in marks[index + 1 :]):
            issues.append("color-3 mask cells must be pairwise 4-neighbor isolated")
            break
    if any(_manhattan(mark, point) <= 1 for mark in marks for point in cells2):
        issues.append("color-3 masks must be 4-neighbor separated from the template")
    return issues


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """The advertised grammar is exactly the accepted training distribution."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    shape, _ = _normalized_template(grid)
    marks = _marks(grid)
    stamp_sets = [_stamp_cells(mark, shape) for mark in marks]
    overlaps = any(
        stamp_sets[i] & stamp_sets[j]
        for i in range(len(stamp_sets))
        for j in range(i + 1, len(stamp_sets))
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_id": _TEMPLATE_TO_ID[shape],
        "n_marks": len(marks),
        "layout_mode": "overlap" if overlaps else "separated",
    }


def _render(
    grid: list[list[int]],
    *,
    marks_limit: int | None = None,
    discard_overlaps: bool = False,
    anchor_first_occupied: bool = False,
) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("malformed stamping input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    shape, _ = _normalized_template(grid)
    offsets = shape
    if anchor_first_occupied:
        first_r, first_c = min(shape)
        offsets = tuple((r - first_r, c - first_c) for r, c in shape)
    marks = _marks(grid)
    if marks_limit is not None:
        marks = marks[:marks_limit]

    out = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()
    for anchor in marks:
        r0, c0 = anchor
        stamp = {
            (r0 + dr, c0 + dc)
            for dr, dc in offsets
            if 0 <= r0 + dr < h and 0 <= c0 + dc < w
        }
        if discard_overlaps and stamp & occupied:
            continue
        for r, c in stamp:
            out[r][c] = 8
        occupied |= stamp
    return out


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket transformation."""
    return _render(grid)


def _first_four_marks_only(grid):
    return _render(grid, marks_limit=4)


def _discard_overlapping_stamps(grid):
    return _render(grid, discard_overlaps=True)


def _anchor_first_occupied(grid):
    return _render(grid, anchor_first_occupied=True)


def _witness_fifth_mark_matters(grid) -> bool:
    try:
        return len(_marks(grid)) >= 5 and rule_mirror(grid) != _first_four_marks_only(grid)
    except (TypeError, ValueError):
        return False


def _witness_overlap_union_matters(grid) -> bool:
    try:
        return (
            observe_overrides(grid)["layout_mode"] == "overlap"
            and rule_mirror(grid) != _discard_overlapping_stamps(grid)
        )
    except (TypeError, ValueError):
        return False


def _witness_bbox_anchor_matters(grid) -> bool:
    try:
        shape, _ = _normalized_template(grid)
        return (0, 0) not in shape and rule_mirror(grid) != _anchor_first_occupied(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "fifth_mark_matters": _witness_fifth_mark_matters,
    "overlap_union_matters": _witness_overlap_union_matters,
    "bbox_anchor_matters": _witness_bbox_anchor_matters,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "first_four_marks_only": _first_four_marks_only,
    "discard_overlapping_stamps": _discard_overlapping_stamps,
    "anchor_first_occupied": _anchor_first_occupied,
}
WITNESS_RIVALS = {
    "fifth_mark_matters": ["first_four_marks_only"],
    "overlap_union_matters": ["discard_overlapping_stamps"],
    "bbox_anchor_matters": ["anchor_first_occupied"],
}

# These two rivals exactly reproduce all six public train/test pairs: the
# public data has at most four masks, and no public stamps overlap.
CANONICAL_SHORTCUTS = {
    "first_four_marks_only": _first_four_marks_only,
    "discard_overlapping_stamps": _discard_overlapping_stamps,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that fit every demo but alter the query answer."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    reasons: list[str] = []
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            reasons.append(f"{role} input is not lawful: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the template-stamping rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons
