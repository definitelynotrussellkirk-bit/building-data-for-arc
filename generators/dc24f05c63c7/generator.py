"""Generator for arc_puzzle_bank_21_set22_s:S22_M3.

A 2/3/4 corner triad defines the source coordinate frame and a 5/6/7
triad defines the target frame.  Color-8 cells form a sparse motif in one
signed source-frame quadrant.  The oracle fills the motif's local bounding
box and paints that rectangle through the target frame's basis.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc24f05c63c7"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "fb23b125dc4f"

SUMMARY = (
    "On a sparse 11..16 by 15..24 zero background, the unique 2/3/4 "
    "cardinal corner is a SOURCE coordinate frame and the unique 5/6/7 "
    "corner is a TARGET frame.  Read the sparse color-8 motif in signed "
    "source-local coordinates, take its complete local bounding rectangle, "
    "and fill that rectangle with 8 through the target frame.  Canvas size, "
    "both ordered bases, motif quadrant, motif shape, and placement vary."
)

INVARIANTS = [
    "exactly one cardinal 2/3/4 source frame and one cardinal 5/6/7 target frame",
    "the source motif is one recognized sparse pattern in one signed local quadrant within radius 3",
    "the motif bounding box contains at least one hole, so filling is distinguishable from sparse copying",
    "the complete target-frame bounding-box footprint is in bounds and empty in the input",
    "every four consecutive sample indexes cover all four motif quadrants, four motif shapes, and both same-basis and reoriented transfers",
]

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BASES = tuple(
    (vx, vy)
    for vx in _CARD
    for vy in _CARD
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)

# Absolute local-coordinate motifs.  Each has a genuine hole inside its bbox.
# The three canonical_* patterns are the normalized official motifs; diagonal_2
# is a compact counterexample to fixed-size and count-only rival rules.
_MOTIF_PATTERNS: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical_a": ((2, 1), (3, 1), (3, 3)),
    "canonical_b": ((1, 2), (2, 2), (3, 1)),
    "canonical_c": ((1, 2), (2, 3), (3, 1)),
    "diagonal_2": ((1, 1), (2, 2)),
}
_MOTIF_KIND_BY_PATTERN = {
    tuple(sorted(points)): name for name, points in _MOTIF_PATTERNS.items()
}
_QUADRANT_SIGNS: dict[str, tuple[int, int]] = {
    "pos_pos": (1, 1),
    "neg_pos": (-1, 1),
    "neg_neg": (-1, -1),
    "pos_neg": (1, -1),
}
_MOTIF_KINDS = tuple(_MOTIF_PATTERNS)
_QUADRANTS = tuple(_QUADRANT_SIGNS)
_RELATION_OFFSETS = (0, 1, 3, 5)

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical anchor or difficulty-banded", "valid": "11..16"},
    "grid_w": {"type": "int", "default": "scheduled canonical anchor or difficulty-banded", "valid": "15..24"},
    "source_basis": {"type": "int", "default": "cyclic with seed offset", "valid": "0..7"},
    "target_basis": {"type": "int", "default": "same/reoriented four-slot schedule", "valid": "0..7"},
    "motif_quadrant": {"type": "str", "default": "cyclic all quadrants", "valid": "pos_pos|neg_pos|neg_neg|pos_neg"},
    "motif_kind": {"type": "str", "default": "cyclic four sparse patterns", "valid": "canonical_a|canonical_b|canonical_c|diagonal_2"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unsupported difficulty: {difficulty!r}")


def _draw_scheduled_int(ctx, overrides, label, lo, hi, scheduled):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, tuple(scheduled))


def _draw_scheduled_choice(ctx, overrides, label, options, scheduled):
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, tuple(options))
    return ctx.draw_choice(label, (scheduled,))


def _glob(origin, vx, vy, u, v):
    return (
        origin[0] + u * vx[0] + v * vy[0],
        origin[1] + u * vx[1] + v * vy[1],
    )


def _lpos(frame, point):
    origin, vx, vy = frame
    dr = point[0] - origin[0]
    dc = point[1] - origin[1]
    return (
        dr * vx[0] + dc * vx[1],
        dr * vy[0] + dc * vy[1],
    )


def _frame_from_colors(grid, colors):
    positions = []
    for color in colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(cells) != 1:
            return None
        positions.append(cells[0])
    origin, px, py = positions
    vx = (px[0] - origin[0], px[1] - origin[1])
    vy = (py[0] - origin[0], py[1] - origin[1])
    if (vx, vy) not in _BASES:
        return None
    return origin, vx, vy


def _bbox_points(points):
    u0 = min(u for u, _ in points)
    u1 = max(u for u, _ in points)
    v0 = min(v for _, v in points)
    v1 = max(v for _, v in points)
    return tuple(
        (u, v)
        for u in range(u0, u1 + 1)
        for v in range(v0, v1 + 1)
    )


def _candidate_origins(h, w, vx, vy, local_cells):
    candidates = []
    for r in range(h):
        for c in range(w):
            cells = [_glob((r, c), vx, vy, u, v) for u, v in local_cells]
            if all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                candidates.append(((r, c), tuple(cells)))
    return candidates


def _clusters_separated(left, right):
    return all(
        max(abs(r1 - r2), abs(c1 - c2)) > 1
        for r1, c1 in left
        for r2, c2 in right
    )


def _choose_layout(h, w, source_basis, target_basis, motif_uvs, rng):
    svx, svy = _BASES[source_basis]
    tvx, tvy = _BASES[target_basis]
    source_local = ((0, 0), (1, 0), (0, 1), *motif_uvs)
    target_local = ((0, 0), (1, 0), (0, 1), *_bbox_points(motif_uvs))
    sources = _candidate_origins(h, w, svx, svy, source_local)
    targets = _candidate_origins(h, w, tvx, tvy, target_local)
    rng.shuffle(sources)
    rng.shuffle(targets)
    for source_origin, source_cells in sources:
        for target_origin, target_cells in targets:
            if _clusters_separated(source_cells, target_cells):
                return source_origin, target_origin
    raise RuntimeError(
        f"no separated layout for {h}x{w}, bases {source_basis}/{target_basis}, motif {motif_uvs}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    canonical_anchor = sample_index % 5 == 0
    h_choices = {
        "easy": range(11, 14),
        "medium": range(12, 16),
        "hard": range(13, 17),
    }[band]
    w_choices = {
        "easy": range(15, 20),
        "medium": range(17, 23),
        "hard": range(20, 25),
    }[band]
    h = _draw_scheduled_int(
        ctx, overrides, "grid_h", 11, 16, (12,) if canonical_anchor else h_choices
    )
    w = _draw_scheduled_int(
        ctx, overrides, "grid_w", 15, 24, (18,) if canonical_anchor else w_choices
    )

    basis_offset = stable_rng(seed, f"{TASK_ID}|basis_schedule_offset", VERSION).randrange(8)
    source_scheduled = (sample_index + basis_offset) % 8
    source_basis = _draw_scheduled_int(
        ctx, overrides, "source_basis", 0, 7, (source_scheduled,)
    )
    target_scheduled = (
        source_scheduled + _RELATION_OFFSETS[sample_index % 4]
    ) % 8
    target_basis = _draw_scheduled_int(
        ctx, overrides, "target_basis", 0, 7, (target_scheduled,)
    )

    quadrant_offset = stable_rng(seed, f"{TASK_ID}|quadrant_schedule_offset", VERSION).randrange(4)
    quadrant_scheduled = _QUADRANTS[(sample_index + quadrant_offset) % 4]
    motif_quadrant = _draw_scheduled_choice(
        ctx, overrides, "motif_quadrant", _QUADRANTS, quadrant_scheduled
    )
    motif_offset = stable_rng(seed, f"{TASK_ID}|motif_schedule_offset", VERSION).randrange(4)
    motif_scheduled = _MOTIF_KINDS[(sample_index + motif_offset) % 4]
    motif_kind = _draw_scheduled_choice(
        ctx, overrides, "motif_kind", _MOTIF_KINDS, motif_scheduled
    )

    sign_u, sign_v = _QUADRANT_SIGNS[motif_quadrant]
    motif_uvs = tuple(
        (sign_u * u, sign_v * v) for u, v in _MOTIF_PATTERNS[motif_kind]
    )
    rng = ctx.draw_rng("placement")
    source_origin, target_origin = _choose_layout(
        h, w, source_basis, target_basis, motif_uvs, rng
    )

    grid = full_grid(h, w, 0)
    svx, svy = _BASES[source_basis]
    tvx, tvy = _BASES[target_basis]
    source_frame = (
        source_origin,
        _glob(source_origin, svx, svy, 1, 0),
        _glob(source_origin, svx, svy, 0, 1),
    )
    target_frame = (
        target_origin,
        _glob(target_origin, tvx, tvy, 1, 0),
        _glob(target_origin, tvx, tvy, 0, 1),
    )
    for point, color in zip(source_frame, (2, 3, 4)):
        grid[point[0]][point[1]] = color
    for point, color in zip(target_frame, (5, 6, 7)):
        grid[point[0]][point[1]] = color
    for u, v in motif_uvs:
        r, c = _glob(source_origin, svx, svy, u, v)
        grid[r][c] = 8

    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError(f"constructed invalid instance: {errors}")
    return [row[:] for row in grid]


def _analyse(grid):
    info: dict[str, Any] = {}
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if not 11 <= h <= 16:
        errors.append(f"height {h} outside 11..16")
    if not 15 <= w <= 24:
        errors.append(f"width {w} outside 15..24")
    allowed = {0, 2, 3, 4, 5, 6, 7, 8}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value not in allowed
        for row in grid
        for value in row
    ):
        errors.append("cells must be ARC integers from {0,2,3,4,5,6,7,8}")
        return info, errors

    source = _frame_from_colors(grid, (2, 3, 4))
    target = _frame_from_colors(grid, (5, 6, 7))
    if source is None:
        errors.append("2/3/4 cells do not form one ordered cardinal source frame")
    if target is None:
        errors.append("5/6/7 cells do not form one ordered cardinal target frame")
    motif_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not 2 <= len(motif_cells) <= 3:
        errors.append(f"expected a 2- or 3-cell sparse motif, got {len(motif_cells)}")
    if errors:
        return info, errors

    assert source is not None and target is not None
    motif_uvs = tuple(sorted(_lpos(source, point) for point in motif_cells))
    if any(u == 0 or v == 0 or abs(u) > 3 or abs(v) > 3 for u, v in motif_uvs):
        errors.append("motif cells must have nonzero local coordinates within radius 3")
        return info, errors
    sign_us = {1 if u > 0 else -1 for u, _ in motif_uvs}
    sign_vs = {1 if v > 0 else -1 for _, v in motif_uvs}
    if len(sign_us) != 1 or len(sign_vs) != 1:
        errors.append("motif cells must occupy one signed local quadrant")
        return info, errors
    sign_pair = (next(iter(sign_us)), next(iter(sign_vs)))
    quadrant = next(
        (name for name, signs in _QUADRANT_SIGNS.items() if signs == sign_pair),
        None,
    )
    absolute_pattern = tuple(sorted((abs(u), abs(v)) for u, v in motif_uvs))
    motif_kind = _MOTIF_KIND_BY_PATTERN.get(absolute_pattern)
    if motif_kind is None:
        errors.append(f"unrecognized motif pattern {absolute_pattern}")
        return info, errors

    fill_uvs = _bbox_points(motif_uvs)
    if len(fill_uvs) <= len(motif_uvs):
        errors.append("motif bounding box has no missing cell; fill rule is hidden")
    target_cells = tuple(_glob(target[0], target[1], target[2], u, v) for u, v in fill_uvs)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in target_cells):
        errors.append("target bounding-box footprint leaves the grid")
    elif any(grid[r][c] != 0 for r, c in target_cells):
        errors.append("target bounding-box footprint must be empty in the input")

    source_basis = _BASES.index((source[1], source[2]))
    target_basis = _BASES.index((target[1], target[2]))
    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "source_frame": source,
            "target_frame": target,
            "source_basis": source_basis,
            "target_basis": target_basis,
            "motif_cells": tuple(motif_cells),
            "motif_uvs": motif_uvs,
            "motif_quadrant": quadrant,
            "motif_kind": motif_kind,
            "fill_uvs": fill_uvs,
            "target_cells": target_cells,
            "bbox_h": len({u for u, _ in fill_uvs}),
            "bbox_w": len({v for _, v in fill_uvs}),
        }
    )
    return info, errors


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return sorted(set(_analyse(grid)[1]))


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    for r, c in info["target_cells"]:
        out[r][c] = 8
    return out


def _rival_identity(grid):
    return deepcopy(grid)


def _rival_sparse_copy(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    target = info["target_frame"]
    for u, v in info["motif_uvs"]:
        r, c = _glob(target[0], target[1], target[2], u, v)
        out[r][c] = 8
    return out


def _rival_fixed_three_square(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    target = info["target_frame"]
    su, sv = _QUADRANT_SIGNS[info["motif_quadrant"]]
    for au in range(1, 4):
        for av in range(1, 4):
            r, c = _glob(target[0], target[1], target[2], su * au, sv * av)
            if 0 <= r < len(out) and 0 <= c < len(out[0]):
                out[r][c] = 8
    return out


def _rival_keep_source_orientation(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    target_origin = info["target_frame"][0]
    source = info["source_frame"]
    for u, v in info["fill_uvs"]:
        r, c = _glob(target_origin, source[1], source[2], u, v)
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity_no_target_fill": _rival_identity,
    "copy_sparse_motif_only": _rival_sparse_copy,
    "always_fill_fixed_3x3": _rival_fixed_three_square,
    "ignore_target_basis": _rival_keep_source_orientation,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_quadrant(name):
    def predicate(grid):
        info, errors = _analyse(grid)
        return not errors and info["motif_quadrant"] == name
    return predicate


def _witness_same_basis(grid):
    info, errors = _analyse(grid)
    return not errors and info["source_basis"] == info["target_basis"]


def _witness_reoriented(grid):
    info, errors = _analyse(grid)
    return not errors and info["source_basis"] != info["target_basis"]


def _witness_three_by_three(grid):
    info, errors = _analyse(grid)
    return not errors and (info["bbox_h"], info["bbox_w"]) == (3, 3)


def _witness_non_three_by_three(grid):
    info, errors = _analyse(grid)
    return not errors and (info["bbox_h"], info["bbox_w"]) != (3, 3)


def _witness_canonical_profile(grid):
    info, errors = _analyse(grid)
    return not errors and (info["grid_h"], info["grid_w"]) == (12, 18)


SEMANTIC_WITNESSES = {
    **{f"quadrant_{name}": _witness_quadrant(name) for name in _QUADRANTS},
    "same_source_target_basis": _witness_same_basis,
    "reoriented_target_basis": _witness_reoriented,
    "three_by_three_bbox": _witness_three_by_three,
    "non_three_by_three_bbox": _witness_non_three_by_three,
    "canonical_12x18_profile": _witness_canonical_profile,
}
WITNESS_RIVALS = {
    name: list(SEMANTIC_RIVALS) for name in SEMANTIC_WITNESSES
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    quadrants = set()
    motif_kinds = set()
    same_basis = False
    reoriented = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not fill the source-local bbox through the target frame")
        quadrants.add(info["motif_quadrant"])
        motif_kinds.add(info["motif_kind"])
        same_basis |= info["source_basis"] == info["target_basis"]
        reoriented |= info["source_basis"] != info["target_basis"]

    if quadrants != set(_QUADRANTS):
        reasons.append(f"demonstrations do not cover all four signed quadrants: {sorted(quadrants)}")
    if len(motif_kinds) < 4:
        reasons.append(f"demonstrations expose only {len(motif_kinds)} motif shapes")
    if not same_basis or not reoriented:
        reasons.append("demonstrations must include both same-basis and reoriented transfers")

    for name, rival in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"rival {name!r} matches every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        qinfo, qerrors = _analyse(query["input"])
        if qerrors:
            reasons.append(f"query malformed: {qerrors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative transform")
        elif not qinfo:
            reasons.append("query analysis unexpectedly produced no observables")
    return reasons
