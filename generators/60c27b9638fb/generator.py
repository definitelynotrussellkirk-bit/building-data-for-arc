"""Generator for ``60c27b9638fb`` — crop a motif and obey a corner command.

The top-left cell is a command.  Clear that cell, crop every remaining nonzero
cell as one motif (which may have one or two components), then transform the
crop: 1=clockwise rotation, 2=180-degree rotation, 3=left-right reflection,
and 4=transpose.  Each standard three-demo/one-query episode repeats the
query command in the demonstrations; seed modulo four rotates every command
through the query role.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "60c27b9638fb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "73df2925e9f2"  # sha256[:12] of whitespace-normalized canonical rule
SUMMARY = (
    "Read the command at (0,0), clear it, crop all remaining nonzero content, "
    "then transform the crop: 1=rotate CW, 2=rotate 180, 3=flip LR, "
    "4=transpose."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "(0,0) is exactly one command in {1,2,3,4}",
    "the payload starts at row>=2 and col>=2 and matches a declared linked profile",
    "the payload uses 2..4 colors and may contain one or two components",
    "all four command transforms of the colored crop are pairwise distinct",
    "every three-demo/one-query window has three distinct demo commands and repeats the first command as the query",
    "seed modulo four rotates commands 1,2,3,4 through the supported query role",
]

# Five profiles reproduce the complete canonical linked dimension/mask manifold.
# Five controlled extrapolations prevent fixed-size, fixed-mask, and one-component
# shortcuts while retaining the same crop-and-transform grammar.
PROFILE_SPECS = {
    "canonical_split4_8x9": {
        "dims": (8, 9),
        "cells": ((0, 0), (0, 2), (1, 0), (1, 1)),
        "canonical": True,
    },
    "canonical_fork5_9x10": {
        "dims": (9, 10),
        "cells": ((0, 0), (0, 2), (1, 1), (1, 2), (2, 1)),
        "canonical": True,
    },
    "canonical_zig5_8x11": {
        "dims": (8, 11),
        "cells": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        "canonical": True,
    },
    "canonical_zig5_10x10": {
        "dims": (10, 10),
        "cells": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        "canonical": True,
    },
    "canonical_split6_9x12": {
        "dims": (9, 12),
        "cells": ((0, 0), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2)),
        "canonical": True,
    },
    "generalized_hook6_9x9": {
        "dims": (9, 9),
        "cells": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
        "canonical": False,
    },
    "generalized_branch7_10x12": {
        "dims": (10, 12),
        "cells": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
        "canonical": False,
    },
    "generalized_islands6_11x9": {
        "dims": (11, 9),
        "cells": ((0, 0), (0, 1), (1, 1), (2, 3), (3, 2), (3, 3)),
        "canonical": False,
    },
    "generalized_stair7_12x11": {
        "dims": (12, 11),
        "cells": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
        "canonical": False,
    },
    "generalized_notch8_11x11": {
        "dims": (11, 11),
        "cells": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2)),
        "canonical": False,
    },
}
PROFILE_NAMES = tuple(PROFILE_SPECS)
CANONICAL_PROFILES = tuple(
    name for name, spec in PROFILE_SPECS.items() if spec["canonical"]
)
_GENERALIZED_A = (
    "generalized_hook6_9x9",
    "generalized_islands6_11x9",
    "generalized_notch8_11x11",
)
_GENERALIZED_B = (
    "generalized_branch7_10x12",
    "generalized_stair7_12x11",
)

# Exactly six of eight ordinary draws in each band lie on the strict canonical
# linked manifold.  Grouped generalized slots retain random nuisance variation.
_PROFILE_SCHEDULES = {
    "easy": (
        "canonical_split4_8x9",
        "canonical_fork5_9x10",
        "canonical_zig5_8x11",
        "canonical_zig5_10x10",
        "canonical_split6_9x12",
        "canonical_split4_8x9",
        _GENERALIZED_A,
        _GENERALIZED_B,
    ),
    "medium": (
        "canonical_zig5_8x11",
        "canonical_zig5_10x10",
        "canonical_split6_9x12",
        "canonical_fork5_9x10",
        _GENERALIZED_A,
        "canonical_split4_8x9",
        _GENERALIZED_B,
        "canonical_zig5_8x11",
    ),
    "hard": (
        _GENERALIZED_B,
        "canonical_split6_9x12",
        "canonical_zig5_10x10",
        _GENERALIZED_A,
        "canonical_zig5_8x11",
        "canonical_fork5_9x10",
        "canonical_split6_9x12",
        "canonical_split4_8x9",
    ),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-linked sample_index schedule",
        "valid": (
            "canonical_split4_8x9|canonical_fork5_9x10|"
            "canonical_zig5_8x11|canonical_zig5_10x10|"
            "canonical_split6_9x12|generalized_hook6_9x9|"
            "generalized_branch7_10x12|generalized_islands6_11x9|"
            "generalized_stair7_12x11|generalized_notch8_11x11"
        ),
    },
    "cmd": {"type": "int", "default": "seed/sample_index supported-query schedule", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "sample_index cycle", "valid": "2..4"},
    "command_in_payload": {
        "type": "bool",
        "default": "true once per four-example command cycle",
        "valid": "false|true",
    },
}

_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_BODY_MIN_ROW = 2
_BODY_MIN_COL = 2


def _norm_cells(cells):
    cells = tuple(cells)
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _rotate_cells_cw(cells):
    cells = _norm_cells(cells)
    height = max(row for row, _ in cells) + 1
    return _norm_cells((col, height - 1 - row) for row, col in cells)


def _d4_variants(cells):
    base = _norm_cells(cells)
    variants = set()
    for reflected in (False, True):
        current = base
        if reflected:
            width = max(col for _, col in current) + 1
            current = _norm_cells((row, width - 1 - col) for row, col in current)
        for _ in range(4):
            variants.add(_norm_cells(current))
            current = _rotate_cells_cw(current)
    return tuple(sorted(variants))


_PROFILE_VARIANTS = {
    name: frozenset(_d4_variants(spec["cells"]))
    for name, spec in PROFILE_SPECS.items()
}


def _validate_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append("cells must be integer ARC colors 0..9")
                return errors, height, width
    return errors, height, width


def _components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in _DIR4:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _crop(grid, cells):
    r1 = min(row for row, _ in cells)
    c1 = min(col for _, col in cells)
    r2 = max(row for row, _ in cells)
    c2 = max(col for _, col in cells)
    return [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _transform_outputs(crop):
    return {
        1: _rotate_cw(crop),
        2: _rotate_180(crop),
        3: _flip_lr(crop),
        4: _transpose(crop),
    }


def _profile_for(height, width, cells):
    normalized = _norm_cells(cells)
    matches = [
        name
        for name, spec in PROFILE_SPECS.items()
        if spec["dims"] == (height, width)
        and normalized in _PROFILE_VARIANTS[name]
    ]
    return matches[0] if len(matches) == 1 else None


def _analyze(grid):
    errors, height, width = _validate_grid(grid)
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "cmd": None,
        "cells": (),
        "colors": (),
        "palette_size": 0,
        "command_in_payload": False,
        "component_count": 0,
        "scene_profile": None,
        "crop": None,
        "outputs": {},
        "output": None,
    }
    if errors:
        return result

    cmd = grid[0][0]
    result["cmd"] = cmd
    if cmd not in (1, 2, 3, 4):
        errors.append("command at (0,0) must be 1, 2, 3, or 4")

    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) != (0, 0) and grid[row][col] != 0
    }
    if not cells:
        errors.append("a nonzero payload motif is required")
        return result

    colors = tuple(sorted({grid[row][col] for row, col in cells}))
    components = _components(cells)
    result.update(
        {
            "cells": tuple(sorted(cells)),
            "colors": colors,
            "palette_size": len(colors),
            "command_in_payload": cmd in colors,
            "component_count": len(components),
        }
    )
    if min(row for row, _ in cells) < _BODY_MIN_ROW:
        errors.append("payload must start at row 2 or below")
    if min(col for _, col in cells) < _BODY_MIN_COL:
        errors.append("payload must start at column 2 or farther right")
    if not 2 <= len(colors) <= 4:
        errors.append(f"payload must use 2..4 colors, found {len(colors)}")

    profile = _profile_for(height, width, cells)
    result["scene_profile"] = profile
    if profile is None:
        errors.append("dimension/payload morphology is outside the declared linked profiles")

    crop = _crop(grid, cells)
    outputs = _transform_outputs(crop)
    result["crop"] = crop
    result["outputs"] = outputs
    if cmd in outputs:
        result["output"] = outputs[cmd]
    if len({repr(output) for output in outputs.values()}) != 4:
        errors.append("colored crop must have four pairwise-distinct command transforms")
    return result


def observe_overrides(grid):
    """Recover every exact declared semantic axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "cmd": analysis["cmd"],
        "palette_size": analysis["palette_size"],
        "command_in_payload": analysis["command_in_payload"],
    }


def canonical_profile_signature(grid):
    profile = observe_overrides(grid).get("scene_profile")
    return profile if profile in CANONICAL_PROFILES else None


def semantic_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    cells = analysis["cells"]
    r1 = min(row for row, _ in cells)
    c1 = min(col for _, col in cells)
    r2 = max(row for row, _ in cells)
    c2 = max(col for _, col in cells)
    return {
        "scene_profile": analysis["scene_profile"],
        "canonical_like": analysis["scene_profile"] in CANONICAL_PROFILES,
        "cmd": analysis["cmd"],
        "palette_size": analysis["palette_size"],
        "command_in_payload": analysis["command_in_payload"],
        "payload_cells": len(cells),
        "component_count": analysis["component_count"],
        "payload_bbox": (r2 - r1 + 1, c2 - c1 + 1),
        "payload_top_left": (r1, c1),
        "normalized_mask": _norm_cells(cells),
        "grid_dims": (analysis["height"], analysis["width"]),
    }


def rule_mirror(grid):
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the lawful linked lesson grammar and reject shortcut scenes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = {name: meta[name] for name in AXES if name in meta}
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and observed.get(name) != value:
                errors.append(
                    f"{name} metadata requested {value!r}, observed "
                    f"{observed.get(name)!r}"
                )
    return errors


def _difficulty_band(difficulty):
    if difficulty is None:
        return "medium"
    if isinstance(difficulty, str):
        if difficulty not in _PROFILE_SCHEDULES:
            raise ValueError(f"invalid difficulty: {difficulty!r}")
        return difficulty
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)):
        raise ValueError(f"invalid difficulty: {difficulty!r}")
    value = max(0.0, min(1.0, float(difficulty)))
    return "easy" if value < 1 / 3 else "medium" if value < 2 / 3 else "hard"


def _legal_placements(height, width, shape):
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    placements = []
    for top in range(_BODY_MIN_ROW, height - shape_h + 1):
        for left in range(_BODY_MIN_COL, width - shape_w + 1):
            placed = {(top + row, left + col) for row, col in shape}
            placements.append(placed)
    return placements


def _paint_distinguishable_payload(
    *, grid, placed, palette, cmd, rng, expected_profile
):
    ordered = sorted(placed)
    for _ in range(128):
        order = ordered[:]
        rng.shuffle(order)
        values = list(palette)
        rng.shuffle(values)
        assignment = {}
        for index, cell in enumerate(order):
            assignment[cell] = (
                values[index] if index < len(values) else rng.choice(values)
            )
        candidate = [row[:] for row in grid]
        for (row, col), value in assignment.items():
            candidate[row][col] = value
        analysis = _analyze(candidate)
        if not analysis["errors"] and analysis["scene_profile"] == expected_profile:
            return candidate
    raise RuntimeError(
        f"could not color profile {expected_profile!r} with palette {palette!r} "
        "while keeping all command outputs distinct"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, branch-identifying command-transform input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("scene_profile") is None:
        scheduled = _PROFILE_SCHEDULES[band][
            int(sample_index) % len(_PROFILE_SCHEDULES[band])
        ]
        options = (scheduled,) if isinstance(scheduled, str) else scheduled
        profile = ctx.draw_choice("scene_profile", options)
    else:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)

    if overrides.get("cmd") is None:
        # The production episode shape is three demonstrations plus one query.
        # A period-three sequence makes the query (slot 3) repeat demo slot 0,
        # while seed modulo four rotates every command through the query role.
        anchor = int(seed) % 4 + 1
        scheduled_cmd = (anchor - 1 + int(sample_index) % 3) % 4 + 1
        cmd = ctx.draw_choice("cmd", (scheduled_cmd,))
    else:
        cmd = ctx.draw_int("cmd", 1, 4)

    if overrides.get("palette_size") is None:
        scheduled_palette_size = 2 + (int(sample_index) % 3)
        palette_size = ctx.draw_choice(
            "palette_size", (scheduled_palette_size,)
        )
    else:
        palette_size = ctx.draw_int("palette_size", 2, 4)

    if overrides.get("command_in_payload") is None:
        scheduled_presence = int(sample_index) % 4 == 2
        command_in_payload = ctx.draw_choice(
            "command_in_payload", (scheduled_presence,)
        )
    else:
        command_in_payload = ctx.draw_choice(
            "command_in_payload", (False, True)
        )

    spec = PROFILE_SPECS[profile]
    height, width = spec["dims"]
    shape_rng = ctx.draw_rng(f"shape:{profile}")
    shape = shape_rng.choice(tuple(_PROFILE_VARIANTS[profile]))
    placements = _legal_placements(height, width, shape)
    if not placements:
        raise RuntimeError(f"no legal placement for profile {profile!r}")
    placed = shape_rng.choice(placements)

    palette_rng = ctx.draw_rng("payload_palette")
    if command_in_payload:
        other_colors = [color for color in range(1, 10) if color != cmd]
        palette = [cmd] + palette_rng.sample(other_colors, palette_size - 1)
    else:
        legal_colors = [color for color in range(1, 10) if color != cmd]
        palette = palette_rng.sample(legal_colors, palette_size)

    grid = full_grid(height, width, 0)
    grid[0][0] = cmd
    grid = _paint_distinguishable_payload(
        grid=grid,
        placed=placed,
        palette=palette,
        cmd=cmd,
        rng=ctx.draw_rng("payload_coloring"),
        expected_profile=profile,
    )

    observed = observe_overrides(grid)
    expected = {
        "scene_profile": profile,
        "cmd": cmd,
        "palette_size": palette_size,
        "command_in_payload": command_in_payload,
    }
    if observed != expected:
        raise RuntimeError(f"constructed {expected!r}, observed {observed!r}")
    return grid
