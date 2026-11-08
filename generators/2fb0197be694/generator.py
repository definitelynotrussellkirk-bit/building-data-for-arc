"""Generator for arc_puzzle_bank_21_set22_s:S22_E7.

A (2, 3, 4) marker triad defines a local coordinate frame.  Color 8 may
occupy any non-empty subset of four named local offsets.  The Racket rule emits
a 1x4 strip whose cells report those four occupancies in canonical order.

The default motif-mask schedule is deliberately lesson-aware: every three
consecutive examples toggle every output position both on and off, and the
following query uses a fourth distinct mask.  This prevents count-only and
position-conflation shortcuts while preserving all 15 lawful non-empty strips.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import draw_marker_frame, gpos

GENERATOR_ID = "2fb0197be694"
TASK_ID = "2fb0197be694"
VERSION = "3.0.0"
RULE_HASH = "eb3e8f5d9da4"
EXPECTED_OUTPUT_CODOMAIN = 15

SUMMARY = (
    "A 6-16 cell rectangular 0-background grid contains exactly one local "
    "coordinate frame: color 2 is the origin, color 3 marks local (1,0), and "
    "color 4 marks local (0,1).  The orthogonal unit basis may use any of the "
    "eight directed D4 orientations.  A non-empty subset of the four local "
    "offsets (2,0), (0,2), (1,1), and (2,2) is colored 8.  Output is a 1x4 "
    "strip in that fixed offset order, using 8 for occupied and 0 for empty. "
    "Default episodes use a cyclic 15-mask curriculum whose every three "
    "consecutive demonstrations toggle all four strip positions."
)

INVARIANTS = [
    "background is 0 and the only non-background colors are 2, 3, 4, and 8",
    "exactly one orthogonal unit local frame is marked by colors 2, 3, and 4",
    "one to four color-8 cells occupy only the four canonical local offsets",
    "the output codomain is the 15 non-empty binary occupancy strips of width 4",
]

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "rng centered_9x9|free_rectangular",
        "valid": "centered_9x9|free_rectangular",
    },
    "motif_mask": {
        "type": "int",
        "default": "lesson-aware cyclic schedule",
        "valid": "1..15",
    },
    "frame_orientation": {
        "type": "str",
        "default": "rng over all directed orthogonal bases",
        "valid": (
            "north_east|north_west|south_east|south_west|"
            "east_north|east_south|west_north|west_south"
        ),
    },
}

CANON = ((2, 0), (0, 2), (1, 1), (2, 2))
MASK_SCHEDULE = (1, 2, 12, 3, 4, 9, 6, 15, 8, 7, 13, 10, 5, 11, 14)
FRAME_ORIENTATIONS = {
    "north_east": ((-1, 0), (0, 1)),
    "north_west": ((-1, 0), (0, -1)),
    "south_east": ((1, 0), (0, 1)),
    "south_west": ((1, 0), (0, -1)),
    "east_north": ((0, 1), (-1, 0)),
    "east_south": ((0, 1), (1, 0)),
    "west_north": ((0, -1), (-1, 0)),
    "west_south": ((0, -1), (1, 0)),
}
_ORIENTATION_BY_VECTORS = {
    vectors: name for name, vectors in FRAME_ORIENTATIONS.items()
}
_REQUIRED_LOCAL_POINTS = set(CANON) | {(0, 0), (1, 0), (0, 1)}


def _fitting_origins(h, w, vx, vy, *, exclude=frozenset()):
    origins = []
    for r in range(h):
        for c in range(w):
            origin = (r, c)
            if origin in exclude:
                continue
            cells = [gpos(origin, vx, vy, u, v) for u, v in _REQUIRED_LOCAL_POINTS]
            if all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                origins.append(origin)
    return origins


def _draw_layout(ctx, layout_profile, vx, vy):
    rng = ctx.draw_rng("layout")
    if layout_profile == "centered_9x9":
        h = w = 9
        origin = (4, 4)
        if origin not in _fitting_origins(h, w, vx, vy):
            raise ValueError(
                f"centered_9x9 is incompatible with orientation {(vx, vy)}"
            )
        return h, w, origin

    if layout_profile != "free_rectangular":
        raise ValueError(f"unknown layout_profile {layout_profile!r}")

    ranges = {
        "easy": (6, 9),
        "medium": (8, 12),
        "hard": (10, 16),
    }
    lo, hi = ranges.get(ctx.difficulty, (6, 16))
    for _ in range(256):
        h = rng.randint(lo, hi)
        w = rng.randint(lo, hi)
        excluded = {(4, 4)} if h == 9 and w == 9 else set()
        origins = _fitting_origins(h, w, vx, vy, exclude=excluded)
        if origins:
            return h, w, rng.choice(origins)
    raise ValueError(
        f"free_rectangular could not place orientation {(vx, vy)} in {lo}..{hi}"
    )


def _draw_motif_mask(ctx, overrides):
    if "motif_mask" in overrides and overrides["motif_mask"] is not None:
        return ctx.draw_int("motif_mask", 1, 15)
    offset = stable_rng(
        ctx.seed, f"{TASK_ID}|mask_schedule_offset", VERSION
    ).randrange(len(MASK_SCHEDULE))
    scheduled = MASK_SCHEDULE[(ctx.sample_index + offset) % len(MASK_SCHEDULE)]
    # A singleton keyed choice records the exact scheduled semantic value in
    # GenCtx without allowing an explicit override to be silently clamped.
    return ctx.draw_choice("motif_mask", (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_profile = ctx.draw_choice(
        "layout_profile",
        ("centered_9x9", "free_rectangular", "free_rectangular", "free_rectangular"),
    )
    frame_orientation = ctx.draw_choice(
        "frame_orientation", tuple(FRAME_ORIENTATIONS)
    )
    motif_mask = _draw_motif_mask(ctx, overrides)

    vx, vy = FRAME_ORIENTATIONS[frame_orientation]
    h, w, origin = _draw_layout(ctx, layout_profile, vx, vy)
    grid = full_grid(h, w, 0)
    draw_marker_frame(grid, origin, vx, vy, (2, 3, 4))
    for index, (u, v) in enumerate(CANON):
        if motif_mask & (1 << index):
            r, c = gpos(origin, vx, vy, u, v)
            grid[r][c] = 8
    return grid


def _analyze(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a nonempty list of rows"]}
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"]}
    h = len(grid)
    if not (6 <= h <= 16 and 6 <= w <= 16):
        errors.append(f"grid dimensions must each be in 6..16, got {h}x{w}")

    positions = {
        color: [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        for color in (2, 3, 4)
    }
    for color in (2, 3, 4):
        if len(positions[color]) != 1:
            errors.append(
                f"expected exactly one frame marker color {color}, "
                f"got {len(positions[color])}"
            )
    unexpected = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or value not in (0, 2, 3, 4, 8)
        },
        key=repr,
    )
    if unexpected:
        errors.append(f"unexpected cell values present: {unexpected}")
    if errors:
        return {"errors": errors, "height": h, "width": w}

    origin = positions[2][0]
    vx = (
        positions[3][0][0] - origin[0],
        positions[3][0][1] - origin[1],
    )
    vy = (
        positions[4][0][0] - origin[0],
        positions[4][0][1] - origin[1],
    )
    orientation = _ORIENTATION_BY_VECTORS.get((vx, vy))
    if orientation is None:
        return {
            "errors": [f"bad local frame vectors vx={vx} vy={vy}"],
            "height": h,
            "width": w,
            "origin": origin,
        }

    canon_cells = []
    for uv in CANON:
        r, c = gpos(origin, vx, vy, *uv)
        if not (0 <= r < h and 0 <= c < w):
            errors.append(f"canonical offset {uv} is out of bounds at {(r, c)}")
        canon_cells.append((r, c))
    if errors:
        return {
            "errors": errors,
            "height": h,
            "width": w,
            "origin": origin,
            "vx": vx,
            "vy": vy,
            "frame_orientation": orientation,
        }

    eights = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    if not eights:
        errors.append("motif must contain at least one color-8 cell")
    if len(eights) > len(CANON):
        errors.append(f"motif has too many color-8 cells: {len(eights)}")
    outside = sorted(eights - set(canon_cells))
    if outside:
        errors.append(f"color-8 cells outside canonical offsets: {outside}")

    motif_mask = 0
    for index, cell in enumerate(canon_cells):
        if cell in eights:
            motif_mask |= 1 << index
    layout_profile = (
        "centered_9x9"
        if h == 9 and w == 9 and origin == (4, 4)
        else "free_rectangular"
    )
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "origin": origin,
        "vx": vx,
        "vy": vy,
        "frame_orientation": orientation,
        "canon_cells": canon_cells,
        "motif_mask": motif_mask,
        "n_motif": len(eights),
        "layout_profile": layout_profile,
    }


def observe_overrides(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return {
        "layout_profile": facts["layout_profile"],
        "motif_mask": facts["motif_mask"],
        "frame_orientation": facts["frame_orientation"],
    }


def rule_mirror(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    mask = facts["motif_mask"]
    return [[8 if mask & (1 << index) else 0 for index in range(4)]]


def canonical_profile_signature(grid):
    """D4-quotiented strict empirical-manifold signature, or None."""
    facts = _analyze(grid)
    if facts.get("errors"):
        return None
    if (
        facts["height"] == 9
        and facts["width"] == 9
        and facts["origin"] == (4, 4)
        and facts["n_motif"] in (2, 3)
    ):
        return (9, 9, "centered_frame", facts["n_motif"])
    return None


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid).get("errors", []))
