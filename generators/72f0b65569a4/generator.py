"""Generator for ``arc_additional_puzzles_21_set2:M10``.

Inside one hollow blue frame, yellow cells are reflected across the frame's
vertical axis.  Empty mirror targets become orange; occupied mirror targets and
axis-aligned yellow cells remain unchanged.  The canonical Racket program is
the sole output authority.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "72f0b65569a4"
VERSION = "3.1.0"  # profile support, redundant lessons, executable rivals
TASK_ID = "72f0b65569a4"
RULE_HASH = "64f526c95424"
SUMMARY = (
    "A black grid contains exactly one hollow blue (1) rectangular frame and "
    "1-7 yellow (4) cells strictly inside it. For every yellow cell, reflect "
    "its column across the frame's vertical axis. If that mirror cell is empty, "
    "the Racket rule paints it orange (7); a yellow mirror partner or a yellow "
    "cell on the axis is left unchanged. Ordinary draws always include at "
    "least one empty, off-axis mirror target. Alternating ordinary draws "
    "teach occupied-pair and center-axis preservation; every third draw "
    "retains a canonical canvas size in every difficulty band."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 90  # lcm(2 branch, 9 canvas profile, 5 origin, 3 mark count)

INVARIANTS = [
    "grid is 7..18 rows by 9..20 columns with colors drawn only from {0,1,4}",
    "exactly one complete hollow blue rectangular frame of size 4..12 by 5..14",
    "exactly 1..7 yellow marks, all strictly inside the frame",
    "at least one yellow mark is off-axis and has an empty horizontal mirror target",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-scheduled within the declared range",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-scheduled within the declared range",
        "valid": "9..20",
    },
    "frame_h": {
        "type": "int",
        "default": "difficulty-scheduled, jointly fitted to the canvas",
        "valid": "4..12",
    },
    "frame_w": {
        "type": "int",
        "default": "difficulty-scheduled, jointly fitted to the canvas",
        "valid": "5..14",
    },
    "n_marks": {
        "type": "int",
        "default": "3..4 easy, 4..5 medium, 5..7 hard",
        "valid": "1..7",
    },
}

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_RANGES = {
    "grid_h": (7, 18),
    "grid_w": (9, 20),
    "frame_h": (4, 12),
    "frame_w": (5, 14),
    "n_marks": (1, 7),
}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any,
                   overrides: dict[str, Any]) -> None:
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int or value < 0:
            raise ValueError(f"{name} must be a nonnegative Python integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")


def _requested_int(overrides: dict[str, Any], name: str) -> int | None:
    value = overrides.get(name)
    return None if value is None else int(value)


def _draw_scheduled_int(ctx, label: str, scheduled: int) -> int:
    """Record a scheduled default while honoring the full declared range."""
    lo, hi = _AXIS_RANGES[label]
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _desired_defaults(ctx, difficulty: Any, sample_index: int) -> dict[str, int]:
    band = "medium" if difficulty is None else difficulty
    ranges = {
        "easy": {
            "grid_h": (7, 10), "grid_w": (9, 12),
            "frame_h": (4, 6), "frame_w": (5, 8),
            "n_marks": (3, 4),
        },
        "medium": {
            "grid_h": (10, 14), "grid_w": (12, 16),
            "frame_h": (5, 9), "frame_w": (7, 11),
            "n_marks": (4, 5),
        },
        "hard": {
            "grid_h": (14, 18), "grid_w": (16, 20),
            "frame_h": (8, 12), "frame_w": (10, 14),
            "n_marks": (5, 7),
        },
    }[band]
    desired: dict[str, int] = {}
    for label, (lo, hi) in ranges.items():
        rng = ctx.draw_rng(f"{label}_default")
        desired[label] = rng.randint(lo, hi)

    # Four consecutive pairs contain two occupied-pair draws and two axis
    # draws, so holding out any one pair leaves both branches in three demos.
    if band == "easy":
        desired["n_marks"] = (3, 4)[sample_index % 2]
    elif band == "medium":
        desired["n_marks"] = (4, 5)[sample_index % 2]
    else:
        desired["n_marks"] = (5, 6, 7)[sample_index % 3]

    # Keep extrapolation and canonical-scale support in every band. Explicit
    # axis controls still take precedence and may expand an anchor canvas.
    if sample_index % 3 == 0:
        h, w = ((9, 11), (10, 12), (11, 13))[(sample_index // 3) % 3]
        desired["grid_h"], desired["grid_w"] = h, w
        desired["frame_h"] = min(desired["frame_h"], h - 2)
        desired["frame_w"] = min(desired["frame_w"], w - 4)
    return desired


def _choose_frame_size(
    ctx,
    *,
    desired_h: int,
    desired_w: int,
    n_marks: int,
    fixed_grid_h: int | None,
    fixed_grid_w: int | None,
    fixed_frame_h: int | None,
    fixed_frame_w: int | None,
    prefer_odd_width: bool,
    require_orientation_room: bool,
    require_near_yellow_target: bool,
) -> tuple[int, int]:
    candidates: list[tuple[int, int, int]] = []
    for frame_h in range(_AXIS_RANGES["frame_h"][0], _AXIS_RANGES["frame_h"][1] + 1):
        if fixed_frame_h is not None and frame_h != fixed_frame_h:
            continue
        if fixed_grid_h is not None and frame_h > fixed_grid_h - 2:
            continue
        for frame_w in range(_AXIS_RANGES["frame_w"][0], _AXIS_RANGES["frame_w"][1] + 1):
            if fixed_frame_w is not None and frame_w != fixed_frame_w:
                continue
            if fixed_grid_w is not None and frame_w > fixed_grid_w - 2:
                continue
            # An axis yellow can be one step from a productive target while
            # every blue border is at least two steps away. This teaches that
            # reflection is not restricted to targets nearest the blue frame.
            if require_near_yellow_target and (
                frame_h < 5 or frame_w < 7 or frame_w % 2 == 0
            ):
                continue
            # Two interior rows with one mirror orbit per row cannot show
            # both an occupied pair and a direction-distinguishing singleton.
            if require_orientation_room and (frame_h, frame_w) == (4, 5):
                continue
            interior_capacity = (frame_h - 2) * (frame_w - 2)
            # One empty mirror target must remain after placing all marks.
            if interior_capacity < n_marks + 1:
                continue
            score = 8 * abs(frame_h - desired_h) + 5 * abs(frame_w - desired_w)
            if prefer_odd_width and frame_w % 2 == 0:
                score += 100
            candidates.append((score, frame_h, frame_w))
    if not candidates:
        fixed = {
            key: value
            for key, value in {
                "grid_h": fixed_grid_h,
                "grid_w": fixed_grid_w,
                "frame_h": fixed_frame_h,
                "frame_w": fixed_frame_w,
                "n_marks": n_marks,
            }.items()
            if value is not None
        }
        raise ValueError(
            "requested axes cannot fit a frame with one empty mirror target: "
            f"{fixed}"
        )
    best_score = min(score for score, _fh, _fw in candidates)
    best = [(fh, fw) for score, fh, fw in candidates if score == best_score]
    return ctx.draw_rng("frame_size_tiebreak").choice(best)


def _frame_origin(ctx, sample_index: int, h: int, w: int, fh: int, fw: int) -> tuple[int, int]:
    max_r0 = h - fh - 1
    max_c0 = w - fw - 1
    mode = sample_index % 5
    if mode == 0:
        return 1, 1
    if mode == 1:
        return 1, max_c0
    if mode == 2:
        return max_r0, 1
    if mode == 3:
        return max_r0, max_c0
    rng = ctx.draw_rng("frame_origin")
    columns = [c for c in range(1, max_c0 + 1) if 2 * c + fw - 1 != w - 1]
    return rng.randint(1, max_r0), rng.choice(columns or [1])


def _place_marks(
    ctx,
    sample_index: int,
    *,
    r0: int,
    c0: int,
    fh: int,
    fw: int,
    n_marks: int,
    grid_w: int,
    require_direction_contrast: bool,
    require_near_yellow_target: bool,
) -> set[tuple[int, int]]:
    c1, c2 = c0, c0 + fw - 1
    interior = [
        (row, col)
        for row in range(r0 + 1, r0 + fh - 1)
        for col in range(c0 + 1, c0 + fw - 1)
    ]
    mirror_pairs = [
        ((row, col), (row, c1 + c2 - col))
        for row, col in interior
        if col < c1 + c2 - col
    ]
    if not mirror_pairs:
        raise ValueError("frame interior has no off-axis mirror pair")

    rng = ctx.draw_rng("mark_layout")
    rng.shuffle(mirror_pairs)
    # Reserve a productive target and, when capacity permits, the distinct
    # source a whole-grid reflection would need to paint that same target.
    # This creates actual prediction disagreement, not just an off-center box.
    contrast = c1 + c2 != grid_w - 1 and len(interior) >= n_marks + 2
    branch_mode = sample_index % 2
    for left, right in mirror_pairs:
        choices = [(left, right), (right, left)]
        rng.shuffle(choices)
        for primary, reserved_empty in choices:
            center_col = (c1 + c2) // 2
            if require_near_yellow_target and (
                not r0 + 2 <= primary[0] <= r0 + fh - 3
                or abs(primary[1] - center_col) != 1
            ):
                continue
            blocked = {reserved_empty}
            if contrast:
                blocked.add((primary[0], grid_w - 1 - reserved_empty[1]))
            if require_direction_contrast:
                blocked.add((2 * r0 + fh - 1 - primary[0], reserved_empty[1]))
            marks = {primary}
            if branch_mode == 0 and n_marks >= 3:
                pairs = [pair for pair in mirror_pairs
                         if not (set(pair) & (marks | blocked))]
                if not pairs:
                    continue
                marks.update(rng.choice(pairs))
            elif branch_mode == 1 and n_marks >= 2 and fw % 2 == 1:
                centers = [cell for cell in interior
                           if cell[1] == center_col and cell not in blocked
                           and (not require_near_yellow_target or cell[0] == primary[0])]
                if not centers:
                    continue
                marks.add(rng.choice(centers))
            fill = [cell for cell in interior if cell not in marks | blocked]
            needed = n_marks - len(marks)
            if needed < 0 or needed > len(fill):
                continue
            rng.shuffle(fill)
            marks.update(fill[:needed])
            return marks
    raise ValueError(f"cannot place exactly {n_marks} marks with the requested branches")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket remains output authority."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    desired = _desired_defaults(ctx, difficulty, sample_index)
    fixed_h = _requested_int(overrides, "grid_h")
    fixed_w = _requested_int(overrides, "grid_w")
    fixed_fh = _requested_int(overrides, "frame_h")
    fixed_fw = _requested_int(overrides, "frame_w")
    profile_draw = sample_index % 3 == 0
    ordinary = not any(value is not None for value in overrides.values())
    fitted_h = fixed_h
    fitted_w = fixed_w
    if profile_draw:
        if fitted_h is None and (fixed_fh is None or fixed_fh <= desired["grid_h"] - 2):
            fitted_h = desired["grid_h"]
        if fitted_w is None and (fixed_fw is None or fixed_fw <= desired["grid_w"] - 2):
            fitted_w = desired["grid_w"]

    n_marks = _draw_scheduled_int(
        ctx,
        "n_marks",
        _requested_int(overrides, "n_marks") or desired["n_marks"],
    )
    frame_h_scheduled, frame_w_scheduled = _choose_frame_size(
        ctx,
        desired_h=desired["frame_h"],
        desired_w=desired["frame_w"],
        n_marks=n_marks,
        fixed_grid_h=fitted_h,
        fixed_grid_w=fitted_w,
        fixed_frame_h=fixed_fh,
        fixed_frame_w=fixed_fw,
        prefer_odd_width=(sample_index % 2 == 1 and fixed_fw is None),
        require_orientation_room=(ordinary and sample_index % 2 == 0 and n_marks >= 3),
        require_near_yellow_target=(ordinary and sample_index % 2 == 1),
    )
    frame_h = _draw_scheduled_int(ctx, "frame_h", frame_h_scheduled)
    frame_w = _draw_scheduled_int(ctx, "frame_w", frame_w_scheduled)

    margin = 2 if profile_draw else 4
    scheduled_h = max(desired["grid_h"], frame_h + margin)
    scheduled_w = max(desired["grid_w"], frame_w + margin)
    scheduled_h = min(_AXIS_RANGES["grid_h"][1], scheduled_h)
    scheduled_w = min(_AXIS_RANGES["grid_w"][1], scheduled_w)
    grid_h = _draw_scheduled_int(ctx, "grid_h", fixed_h or scheduled_h)
    grid_w = _draw_scheduled_int(ctx, "grid_w", fixed_w or scheduled_w)

    if frame_h > grid_h - 2 or frame_w > grid_w - 2:
        raise ValueError(
            "frame dimensions require a one-cell exterior margin: "
            f"grid={grid_h}x{grid_w}, frame={frame_h}x{frame_w}"
        )
    if (frame_h - 2) * (frame_w - 2) < n_marks + 1:
        raise ValueError(
            "frame interior lacks capacity for the requested marks plus one "
            "empty mirror target"
        )

    r0, c0 = _frame_origin(ctx, sample_index, grid_h, grid_w, frame_h, frame_w)
    grid = full_grid(grid_h, grid_w, 0)
    draw_frame(grid, r0, c0, r0 + frame_h - 1, c0 + frame_w - 1, 1)
    for row, col in _place_marks(
        ctx,
        sample_index,
        r0=r0,
        c0=c0,
        fh=frame_h,
        fw=frame_w,
        n_marks=n_marks,
        grid_w=grid_w,
        require_direction_contrast=ordinary,
        require_near_yellow_target=(ordinary and sample_index % 2 == 1),
    ):
        grid[row][col] = 4
    return grid


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]

    h, w = len(grid), width
    if not 7 <= h <= 18:
        errors.append(f"grid height must be 7..18, got {h}")
    if not 9 <= w <= 20:
        errors.append(f"grid width must be 9..20, got {w}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value not in {0, 1, 4}
        for row in grid
        for value in row
    ):
        errors.append("input colors must be exactly from {0,1,4}")

    blue = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    if not blue:
        return {}, errors + ["missing blue frame"]
    rows = [r for r, _c in blue]
    cols = [c for _r, c in blue]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    frame_h, frame_w = r2 - r1 + 1, c2 - c1 + 1
    if not 4 <= frame_h <= 12:
        errors.append(f"frame height must be 4..12, got {frame_h}")
    if not 5 <= frame_w <= 14:
        errors.append(f"frame width must be 5..14, got {frame_w}")
    if r1 < 1 or c1 < 1 or r2 >= h - 1 or c2 >= w - 1:
        errors.append("frame must have a one-cell exterior margin")

    expected_blue = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    missing_blue = expected_blue - blue
    extra_blue = blue - expected_blue
    if missing_blue:
        errors.append(f"blue frame border is broken at {len(missing_blue)} cell(s)")
    if extra_blue:
        errors.append(f"found {len(extra_blue)} blue cell(s) off the frame border")

    marks = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    outside_marks = {
        (r, c) for r, c in marks if not (r1 < r < r2 and c1 < c < c2)
    }
    if outside_marks:
        errors.append(f"found {len(outside_marks)} yellow mark(s) outside the frame interior")
    if not 1 <= len(marks) <= 7:
        errors.append(f"yellow mark count must be 1..7, got {len(marks)}")

    # An invalid outside mark can reflect beyond the row bounds. Diagnose the
    # grammar first; never index the reflected coordinate of an invalid scene.
    if errors:
        return {}, errors

    productive = {
        (r, c)
        for r, c in marks
        if c != c1 + c2 - c and grid[r][c1 + c2 - c] == 0
    }
    if not productive:
        errors.append("no yellow mark has an empty off-axis mirror target")

    paired_orbits = {
        tuple(sorted(((r, c), (r, c1 + c2 - c))))
        for r, c in marks
        if c != c1 + c2 - c and (r, c1 + c2 - c) in marks
    }
    center_marks = {
        (r, c) for r, c in marks if c == c1 + c2 - c
    }
    facts = {
        "grid_h": h,
        "grid_w": w,
        "frame_h": frame_h,
        "frame_w": frame_w,
        "n_marks": len(marks),
        "frame": (r1, c1, r2, c2),
        "marks": frozenset(marks),
        "productive_count": len(productive),
        "paired_orbit_count": len(paired_orbits),
        "center_mark_count": len(center_marks),
        "frame_off_global_axis": (c1 + c2) != (w - 1),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "frame_h": int(facts["frame_h"]),
        "frame_w": int(facts["frame_w"]),
        "n_marks": int(facts["n_marks"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full teaching grammar and exact override realization."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors and requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and requested[name] is not None and observed.get(name) != requested[name]:
                errors.append(
                    f"override {name} requested {requested[name]!r}, "
                    f"observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator's teaching grammar is the task's canonical manifold."""
    _facts, errors = _analyze(grid)
    return errors


def _witness_productive_empty_target(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["productive_count"] > 0


def _witness_occupied_mirror_pair(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["paired_orbit_count"] > 0


def _witness_center_axis_mark(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["center_mark_count"] > 0


def _witness_frame_local_axis(grid) -> bool:
    facts, errors = _analyze(grid)
    if errors or not facts["frame_off_global_axis"]:
        return False
    return _rival_transform(grid, "local_empty") != _rival_transform(grid, "whole_grid_empty")


def _witness_nearest_frame_not_required(grid) -> bool:
    _facts, errors = _analyze(grid)
    return not errors and (
        _rival_transform(grid, "local_empty")
        != _rival_transform(grid, "nearest_frame_with_ties")
    )


def _rival_transform(grid, mode: str):
    """Diagnostic hypotheses only. Authoritative labels still come from Racket."""
    out = [row[:] for row in grid]
    facts, errors = _analyze(grid)
    if errors or mode == "identity":
        return out
    r1, c1, r2, c2 = facts["frame"]
    for r, c in sorted(facts["marks"]):
        rr, cc = r, c1 + c2 - c
        if mode == "whole_grid_empty":
            cc = len(grid[0]) - 1 - c
        elif mode == "vertical_empty":
            rr, cc = r1 + r2 - r, c
        value = grid[rr][cc]
        if value == 0:
            if mode in ("nearest_frame_with_ties", "nearest_frame_strict"):
                frame_distance = min(rr - r1, r2 - rr, cc - c1, c2 - cc)
                yellow_distance = min(
                    abs(rr - mr) + abs(cc - mc) for mr, mc in facts["marks"]
                )
                if frame_distance > yellow_distance or (
                    mode == "nearest_frame_strict" and frame_distance == yellow_distance
                ):
                    continue
            out[rr][cc] = 4 if mode == "copy_yellow" else 7
        elif mode == "overwrite_nonaxis_yellow" and cc != c and value == 4:
            out[rr][cc] = 7
        elif mode == "recolor_axis_yellow" and cc == c:
            out[rr][cc] = 7
    return out


def _identity(grid):
    return _rival_transform(grid, "identity")


def _overwrite_nonaxis_yellow(grid):
    return _rival_transform(grid, "overwrite_nonaxis_yellow")


def _recolor_axis_yellow(grid):
    return _rival_transform(grid, "recolor_axis_yellow")


def _whole_grid_empty(grid):
    return _rival_transform(grid, "whole_grid_empty")


def _copy_yellow(grid):
    return _rival_transform(grid, "copy_yellow")


def _vertical_empty(grid):
    return _rival_transform(grid, "vertical_empty")


def _nearest_frame_with_ties(grid):
    return _rival_transform(grid, "nearest_frame_with_ties")


def _nearest_frame_strict(grid):
    return _rival_transform(grid, "nearest_frame_strict")


SEMANTIC_WITNESSES = {
    "productive_empty_target": _witness_productive_empty_target,
    "occupied_mirror_pair": _witness_occupied_mirror_pair,
    "center_axis_mark": _witness_center_axis_mark,
    "frame_local_not_global_axis": _witness_frame_local_axis,
    "nearest_frame_not_required": _witness_nearest_frame_not_required,
}

SEMANTIC_RIVALS = {
    "identity": _identity,
    "overwrite_nonaxis_yellow": _overwrite_nonaxis_yellow,
    "recolor_axis_yellow": _recolor_axis_yellow,
    "whole_grid_empty": _whole_grid_empty,
    "copy_yellow": _copy_yellow,
    "vertical_empty": _vertical_empty,
    "nearest_frame_with_ties": _nearest_frame_with_ties,
    "nearest_frame_strict": _nearest_frame_strict,
}
WITNESS_RIVALS = {
    "productive_empty_target": ["identity", "copy_yellow"],
    "occupied_mirror_pair": ["overwrite_nonaxis_yellow"],
    "center_axis_mark": ["recolor_axis_yellow"],
    "frame_local_not_global_axis": ["whole_grid_empty"],
    "nearest_frame_not_required": ["nearest_frame_with_ties", "nearest_frame_strict"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "overwrite_nonaxis_yellow", "recolor_axis_yellow", "whole_grid_empty",
        "nearest_frame_with_ties",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival fitting all demos but changing this query."""
    if (len(demos) < EXAMPLES_NEEDED or any(
            not isinstance(pair, dict) or "input" not in pair or "output" not in pair
            for pair in demos)):
        return [f"expected at least {EXAMPLES_NEEDED} complete demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["expected a complete labeled query for the authoring check"]
    return [
        f"rival {name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
