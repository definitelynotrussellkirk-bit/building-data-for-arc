"""Generator for ``80a3c4f25880`` — rotate a cropped object by a corner key.

The cell at ``(0, 0)`` is a control key: 1 means clockwise, 2 means 180
degrees, and 3 means counter-clockwise.  After clearing that key, crop the
single colored object and rotate the crop.  Normal generation uses a linked
profile schedule: four profiles reproduce every canonical dimension/morphology
combination while eight asymmetric extrapolations prevent shape memorization.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "80a3c4f25880"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "17e5167b1aa3"  # sha256[:12] of whitespace-normalized canonical rule
SUMMARY = (
    "Read the key at (0,0), clear it, crop the one separated monochrome "
    "object, and rotate the crop: 1=CW, 2=180 degrees, 3=CCW."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "(0,0) is a key in {1,2,3}, distinct from the object color",
    "one 4-connected monochrome object is separated from the key by a moat",
    "the linked canvas-dimension/object-shape profile is declared and observable",
    "the keyed rotation changes the cropped bitmap",
    "sequential sample indices 0,1,2 expose keys 1,2,3",
]

# Profiles are linked facts, not independent ranges.  The first four are the
# complete strict empirical manifold from the three train pairs and one held-out
# pair.  Shapes are recognized modulo D4 because orientation is not the rule.
PROFILE_SPECS = {
    "canonical_l4_7x7": {
        "dims": (7, 7),
        "cells": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "canonical": True,
    },
    "canonical_l4_8x8": {
        "dims": (8, 8),
        "cells": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "canonical": True,
    },
    "canonical_t4_7x9": {
        "dims": (7, 9),
        "cells": ((0, 0), (0, 1), (0, 2), (1, 1)),
        "canonical": True,
    },
    "canonical_v5_8x8": {
        "dims": (8, 8),
        "cells": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        "canonical": True,
    },
    "generalized_hook6_9x10": {
        "dims": (9, 10),
        "cells": ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (2, 1)),
        "canonical": False,
    },
    "generalized_branch7_10x9": {
        "dims": (10, 9),
        "cells": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
        "canonical": False,
    },
    "generalized_zig6_9x10": {
        "dims": (9, 10),
        "cells": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
        "canonical": False,
    },
    "generalized_fork6_10x9": {
        "dims": (10, 9),
        "cells": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)),
        "canonical": False,
    },
    "generalized_notch7_9x10": {
        "dims": (9, 10),
        "cells": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (3, 1)),
        "canonical": False,
    },
    "generalized_snake7_10x9": {
        "dims": (10, 9),
        "cells": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (3, 3)),
        "canonical": False,
    },
    "generalized_cap7_9x10": {
        "dims": (9, 10),
        "cells": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2), (3, 2)),
        "canonical": False,
    },
    "generalized_spur8_10x9": {
        "dims": (10, 9),
        "cells": ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (1, 2), (2, 2), (2, 3)),
        "canonical": False,
    },
}
PROFILE_NAMES = tuple(PROFILE_SPECS)
CANONICAL_PROFILES = tuple(
    name for name, spec in PROFILE_SPECS.items() if spec["canonical"]
)

_GENERALIZED_GROUP_A = (
    "generalized_hook6_9x10",
    "generalized_zig6_9x10",
    "generalized_fork6_10x9",
    "generalized_notch7_9x10",
)
_GENERALIZED_GROUP_B = (
    "generalized_branch7_10x9",
    "generalized_snake7_10x9",
    "generalized_cap7_9x10",
    "generalized_spur8_10x9",
)

# Six of eight ordinary draws per band stay on the strict canonical manifold.
# Each generalized slot draws among four linked profiles, increasing answer-space
# coverage without changing the exact 75% canonical-manifold rate.
_PROFILE_SCHEDULES = {
    "easy": (
        "canonical_l4_7x7", "canonical_t4_7x9",
        "canonical_v5_8x8", "canonical_l4_8x8",
        "canonical_l4_7x7", "canonical_t4_7x9",
        _GENERALIZED_GROUP_A, _GENERALIZED_GROUP_B,
    ),
    "medium": (
        "canonical_l4_8x8", "canonical_v5_8x8",
        "canonical_l4_7x7", "canonical_t4_7x9",
        _GENERALIZED_GROUP_A, "canonical_l4_8x8",
        _GENERALIZED_GROUP_B, "canonical_v5_8x8",
    ),
    "hard": (
        _GENERALIZED_GROUP_B, "canonical_v5_8x8",
        "canonical_t4_7x9", _GENERALIZED_GROUP_A,
        "canonical_l4_8x8", "canonical_l4_7x7",
        "canonical_v5_8x8", "canonical_t4_7x9",
    ),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-linked sample_index schedule",
        "valid": (
            "canonical_l4_7x7|canonical_l4_8x8|canonical_t4_7x9|"
            "canonical_v5_8x8|generalized_hook6_9x10|"
            "generalized_branch7_10x9|generalized_zig6_9x10|"
            "generalized_fork6_10x9|generalized_notch7_9x10|"
            "generalized_snake7_10x9|generalized_cap7_9x10|"
            "generalized_spur8_10x9"
        ),
    },
    "key": {"type": "int", "default": "sample_index cycle", "valid": "1..3"},
    "blob_color": {"type": "color", "default": "rng excluding 0 and key", "valid": "1..9"},
}

_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_KEY_MOAT = {(0, 0), (0, 1), (1, 0), (1, 1)}


def _norm_cells(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cells_cw(cells):
    cells = _norm_cells(cells)
    height = max(r for r, _ in cells) + 1
    return _norm_cells((c, height - 1 - r) for r, c in cells)


def _d4_variants(cells):
    base = _norm_cells(cells)
    variants = set()
    for reflected in (False, True):
        current = base
        if reflected:
            width = max(c for _, c in current) + 1
            current = _norm_cells((r, width - 1 - c) for r, c in current)
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
        errors.append("grid must be rectangular")
        return errors, height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                return errors, height, width
    return errors, height, width


def _components(cells):
    remaining = set(cells)
    out = []
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
        out.append(component)
    return out


def _crop(grid, cells):
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    return [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]


def _rotate_grid_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_grid_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_grid_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


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
        "key": None,
        "blob_color": None,
        "cells": (),
        "scene_profile": None,
        "crop": None,
        "output": None,
    }
    if errors:
        return result

    key = grid[0][0]
    result["key"] = key
    if key not in (1, 2, 3):
        errors.append("key at (0,0) must be 1, 2, or 3")

    colored = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if (row, col) != (0, 0) and grid[row][col] != 0
    ]
    if not colored:
        errors.append("one nonzero object is required")
        return result

    colors = {color for _, _, color in colored}
    if len(colors) != 1:
        errors.append(f"object must be monochrome, found colors {sorted(colors)}")
        return result
    blob_color = next(iter(colors))
    cells = {(row, col) for row, col, _ in colored}
    result.update({"blob_color": blob_color, "cells": tuple(sorted(cells))})

    if blob_color == key:
        errors.append("object color must differ from the key")
    components = _components(cells)
    if len(components) != 1:
        errors.append(f"expected one 4-connected object, found {len(components)}")
    if cells & _KEY_MOAT:
        errors.append("object must not occupy the key's 2x2 moat")

    profile = _profile_for(height, width, cells)
    result["scene_profile"] = profile
    if profile is None:
        errors.append("dimension/object morphology is outside the declared linked profiles")

    crop = _crop(grid, cells)
    result["crop"] = crop
    if key == 1:
        output = _rotate_grid_cw(crop)
    elif key == 2:
        output = _rotate_grid_180(crop)
    elif key == 3:
        output = _rotate_grid_ccw(crop)
    else:
        output = None
    result["output"] = output
    if output is not None and output == crop:
        errors.append("keyed rotation must visibly change the cropped bitmap")
    return result


def observe_overrides(grid):
    """Recover every exact declared semantic axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "key": analysis["key"],
        "blob_color": analysis["blob_color"],
    }


def canonical_profile_signature(grid):
    profile = observe_overrides(grid).get("scene_profile")
    return profile if profile in CANONICAL_PROFILES else None


def semantic_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    cells = analysis["cells"]
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    return {
        "scene_profile": analysis["scene_profile"],
        "canonical_like": analysis["scene_profile"] in CANONICAL_PROFILES,
        "key": analysis["key"],
        "blob_color": analysis["blob_color"],
        "blob_cells": len(cells),
        "blob_bbox": (r2 - r1 + 1, c2 - c1 + 1),
        "blob_top_left": (r1, c1),
        "normalized_shape": _norm_cells(cells),
        "grid_dims": (analysis["height"], analysis["width"]),
    }


def rule_mirror(grid):
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the lawful linked input grammar and reject shortcut scenes."""
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
                    f"{name} metadata requested {value!r}, observed {observed.get(name)!r}"
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-identity keyed-rotation input grid."""
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
        scheduled_profile = _PROFILE_SCHEDULES[band][
            int(sample_index) % len(_PROFILE_SCHEDULES[band])
        ]
        scheduled_options = (
            (scheduled_profile,) if isinstance(scheduled_profile, str)
            else scheduled_profile
        )
        profile = ctx.draw_choice("scene_profile", scheduled_options)
    else:
        profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)

    if overrides.get("key") is None:
        scheduled_key = int(sample_index) % 3 + 1
        requested_color = overrides.get("blob_color")
        if requested_color is not None and int(requested_color) == scheduled_key:
            scheduled_key = scheduled_key % 3 + 1
        key = ctx.draw_choice("key", (scheduled_key,))
    else:
        key = ctx.draw_choice("key", (1, 2, 3))

    blob_color = ctx.draw_color("blob_color", exclude={0, key})
    spec = PROFILE_SPECS[profile]
    height, width = spec["dims"]
    rng = ctx.draw_rng(f"profile:{profile}")
    shape = rng.choice(tuple(_PROFILE_VARIANTS[profile]))
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    placements = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            placed = {(top + row, left + col) for row, col in shape}
            if not placed & _KEY_MOAT:
                placements.append((top, left, placed))
    if not placements:
        raise RuntimeError(f"no legal placement for profile {profile!r}")
    _, _, placed = rng.choice(placements)

    grid = full_grid(height, width, 0)
    grid[0][0] = key
    for row, col in placed:
        grid[row][col] = blob_color

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise RuntimeError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    observed = observe_overrides(grid)
    expected = {"scene_profile": profile, "key": key, "blob_color": blob_color}
    if observed != expected:
        raise RuntimeError(f"constructed {expected!r}, observed {observed!r}")
    return grid
