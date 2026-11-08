"""Generator for bank task H117 / dcc5f8961845.

The first two cells contain ordered transform commands.  Clearing those
cells and cropping all remaining nonzero content yields a multicolor motif.
Command one is applied to that crop, then command two is applied to the
intermediate result.

All five public inputs use an 8x9 canvas and a translated 3x3 motif.  Two
motifs recur under different command pairs, which demonstrates that motif
and ordered commands must remain linked in a complete semantic profile.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "dcc5f8961845"
VERSION = "3.0.0"
TASK_ID = "dcc5f8961845"
RULE_HASH = "9f952248bd5f"

SUMMARY = (
    "Two header commands 0..5 are composed in order on one translated "
    "2..5 by 2..5 multicolor motif; the output is the transformed crop."
)

INVARIANTS = [
    "only (0,0) and (0,1) may be nonzero in the header row",
    "both command values are integers in 0..5",
    "one motif lies below a blank separator row and inside a one-cell margin",
    "the motif bbox is 2..5 by 2..5 and contains exactly 2..3 colors",
    "the output applies command one and then command two to the exact crop",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..16",
        "valid": "9..16",
    },
    "motif_h": {
        "type": "int",
        "default": "difficulty-aware rng 2..5",
        "valid": "2..5",
    },
    "motif_w": {
        "type": "int",
        "default": "difficulty-aware rng 2..5",
        "valid": "2..5",
    },
    "n_colors": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
    },
    "cmd1": {
        "type": "int",
        "default": "rng 0..5",
        "valid": "0..5",
    },
    "cmd2": {
        "type": "int",
        "default": "rng 0..5",
        "valid": "0..5",
    },
}

_VALID_H = (8, 14)
_VALID_W = (9, 16)
_VALID_MOTIF = (2, 5)
_VALID_COLORS = (2, 3)
_VALID_COMMAND = (0, 5)
_PROFILE_PRIOR = 0.06

# Canvas h/w, ordered commands, and the exact normalized cropped motif.
_PROFILE_SPECS = (
    (
        8,
        9,
        1,
        4,
        ((2, 3, 0), (2, 0, 3), (2, 2, 2)),
    ),
    (
        8,
        9,
        2,
        1,
        ((4, 5, 0), (4, 4, 0), (4, 0, 5)),
    ),
    (
        8,
        9,
        5,
        3,
        ((6, 0, 7), (0, 6, 0), (7, 6, 0)),
    ),
    (
        8,
        9,
        4,
        2,
        ((2, 3, 0), (2, 0, 3), (2, 2, 2)),
    ),
    (
        8,
        9,
        3,
        4,
        ((4, 5, 0), (4, 4, 0), (4, 0, 5)),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    h = len(grid)
    w = len(grid[0]) if grid else 0
    cmd1 = grid[0][0] if h and w else None
    cmd2 = grid[0][1] if h and w >= 2 else None
    cells = tuple(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and not (r == 0 and c in (0, 1))
    )
    if not cells:
        return {
            "grid": grid,
            "h": h,
            "w": w,
            "cmd1": cmd1,
            "cmd2": cmd2,
            "cells": (),
            "colors": (),
        }
    r0 = min(r for r, _, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    c1 = max(c for _, c, _ in cells)
    motif = tuple(
        tuple(grid[r][c] for c in range(c0, c1 + 1))
        for r in range(r0, r1 + 1)
    )
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "cmd1": cmd1,
        "cmd2": cmd2,
        "cells": cells,
        "colors": tuple(sorted({value for _, _, value in cells})),
        "r0": r0,
        "r1": r1,
        "c0": c0,
        "c1": c1,
        "motif_h": r1 - r0 + 1,
        "motif_w": c1 - c0 + 1,
        "motif": motif,
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 8..14")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 9..16")
    if any(
        type(value) is not int or not (0 <= value <= 9)
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
    if w < 2:
        return errors
    if not (
        type(coerced[0][0]) is int
        and _VALID_COMMAND[0] <= coerced[0][0] <= _VALID_COMMAND[1]
        and type(coerced[0][1]) is int
        and _VALID_COMMAND[0] <= coerced[0][1] <= _VALID_COMMAND[1]
    ):
        errors.append("both header commands must be integers in 0..5")
    if any(coerced[0][c] != 0 for c in range(2, w)):
        errors.append("only the first two header cells may be nonzero")
    scene = _analyze_scene(coerced)
    if not scene["cells"]:
        errors.append("missing motif beneath the command header")
        return errors
    if not (
        _VALID_MOTIF[0] <= scene["motif_h"] <= _VALID_MOTIF[1]
        and _VALID_MOTIF[0] <= scene["motif_w"] <= _VALID_MOTIF[1]
    ):
        errors.append("motif bounding box must be 2..5 by 2..5")
    if not (
        scene["r0"] >= 2
        and scene["r1"] <= h - 2
        and scene["c0"] >= 1
        and scene["c1"] <= w - 2
    ):
        errors.append(
            "motif must lie below a blank row and inside a one-cell margin"
        )
    if not (
        _VALID_COLORS[0] <= len(scene["colors"]) <= _VALID_COLORS[1]
    ):
        errors.append("motif must contain exactly 2..3 distinct colors")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "motif_h": scene["motif_h"],
        "motif_w": scene["motif_w"],
        "n_colors": len(scene["colors"]),
        "cmd1": scene["cmd1"],
        "cmd2": scene["cmd2"],
    }


def _transpose(grid):
    return tuple(
        tuple(grid[r][c] for r in range(len(grid)))
        for c in range(len(grid[0]))
    )


def _rotate_cw(grid):
    return tuple(
        tuple(grid[len(grid) - 1 - r][c] for r in range(len(grid)))
        for c in range(len(grid[0]))
    )


def _rotate_180(grid):
    return tuple(tuple(reversed(row)) for row in reversed(grid))


def _flip_lr(grid):
    return tuple(tuple(reversed(row)) for row in grid)


def _flip_ud(grid):
    return tuple(reversed(tuple(tuple(row) for row in grid)))


def _apply_transform(grid, command):
    grid = tuple(tuple(row) for row in grid)
    if command == 0:
        return grid
    if command == 1:
        return _rotate_cw(grid)
    if command == 2:
        return _rotate_180(grid)
    if command == 3:
        return _transpose(grid)
    if command == 4:
        return _flip_lr(grid)
    return _flip_ud(grid)


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    first = _apply_transform(scene["motif"], scene["cmd1"])
    result = _apply_transform(first, scene["cmd2"])
    return [list(row) for row in result]


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        scene["cmd1"],
        scene["cmd2"],
        scene["motif"],
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    (h, w, cmd1, cmd2, motif)
    for h, w, cmd1, cmd2, motif in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _paint_scene(h, w, cmd1, cmd2, motif, top, left):
    grid = full_grid(h, w, 0)
    grid[0][0] = cmd1
    grid[0][1] = cmd2
    for dr, row in enumerate(motif):
        for dc, value in enumerate(row):
            if value != 0:
                grid[top + dr][left + dc] = value
    return grid


def _draw_profile(profile, rng):
    h, w, cmd1, cmd2, motif = profile
    motif_h = len(motif)
    motif_w = len(motif[0])
    top = rng.randint(2, h - motif_h - 1)
    left = rng.randint(1, w - motif_w - 1)
    return _paint_scene(
        h,
        w,
        cmd1,
        cmd2,
        motif,
        top,
        left,
    )


def _draw_mask(motif_h, motif_w, minimum_cells, rng):
    cells = {
        (0, rng.randrange(motif_w)),
        (motif_h - 1, rng.randrange(motif_w)),
        (rng.randrange(motif_h), 0),
        (rng.randrange(motif_h), motif_w - 1),
    }
    density = rng.uniform(0.35, 0.8)
    for r in range(motif_h):
        for c in range(motif_w):
            if rng.random() < density:
                cells.add((r, c))
    remaining = [
        (r, c)
        for r in range(motif_h)
        for c in range(motif_w)
        if (r, c) not in cells
    ]
    rng.shuffle(remaining)
    while len(cells) < minimum_cells:
        cells.add(remaining.pop())
    return tuple(sorted(cells))


def _draw_motif(motif_h, motif_w, n_colors, rng):
    palette = tuple(rng.sample(range(1, 10), n_colors))
    cells = _draw_mask(motif_h, motif_w, n_colors, rng)
    values = [rng.choice(palette) for _ in cells]
    for index, color in enumerate(palette):
        values[index] = color
    motif = full_grid(motif_h, motif_w, 0)
    for (r, c), value in zip(cells, values):
        motif[r][c] = value
    return tuple(tuple(row) for row in motif)


def _draw_general(
    h,
    w,
    motif_h,
    motif_w,
    n_colors,
    cmd1,
    cmd2,
    rng,
):
    motif = _draw_motif(motif_h, motif_w, n_colors, rng)
    top = rng.randint(2, h - motif_h - 1)
    left = rng.randint(1, w - motif_w - 1)
    return _paint_scene(
        h,
        w,
        cmd1,
        cmd2,
        motif,
        top,
        left,
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
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, cmd1, cmd2, motif = profile
        colors = {value for row in motif for value in row if value != 0}
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("motif_h", len(motif), len(motif))
        ctx.draw_int("motif_w", len(motif[0]), len(motif[0]))
        ctx.draw_int("n_colors", len(colors), len(colors))
        ctx.draw_int("cmd1", cmd1, cmd1)
        ctx.draw_int("cmd2", cmd2, cmd2)
        grid = _draw_profile(profile, ctx.draw_rng("layout"))
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (8, 10),
                    "medium": (9, 12),
                    "hard": (11, 14),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (9, 11),
                    "medium": (10, 14),
                    "hard": (13, 16),
                }[band],
            )
        if overrides.get("motif_h") is not None:
            motif_h = ctx.draw_int("motif_h", *_VALID_MOTIF)
        else:
            motif_h = ctx.draw_int(
                "motif_h",
                *{
                    "easy": (2, 4),
                    "medium": (2, 4),
                    "hard": (3, 5),
                }[band],
            )
        if overrides.get("motif_w") is not None:
            motif_w = ctx.draw_int("motif_w", *_VALID_MOTIF)
        else:
            motif_w = ctx.draw_int(
                "motif_w",
                *{
                    "easy": (2, 4),
                    "medium": (2, 4),
                    "hard": (3, 5),
                }[band],
            )
        n_colors = ctx.draw_int("n_colors", *_VALID_COLORS)
        cmd1 = ctx.draw_int("cmd1", *_VALID_COMMAND)
        cmd2 = ctx.draw_int("cmd2", *_VALID_COMMAND)
        grid = _draw_general(
            h,
            w,
            motif_h,
            motif_w,
            n_colors,
            cmd1,
            cmd2,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
