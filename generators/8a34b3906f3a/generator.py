"""Generator for the canonical fourfold rotational-completion family.

The source ARC task shows three copies of a red motif around a unique central
maroon marker.  The output completes the absent 90-degree rotation.  Inputs are
odd square grids so the canonical integer center is the geometric center and no
rotation can clip.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a34b3906f3a"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "bf849a2eb805"
SUMMARY = (
    "Odd square {0,2,9} scenes contain a central color-9 marker and three of "
    "four rotated copies of a color-2 motif; complete the missing quadrant."
)

INVARIANTS = [
    "background is 0 and the only non-background colors are 2 and 9",
    "the board is odd, square, and 9..29 cells on a side",
    "one color-9 marker is at the geometric center",
    "every color-2 rotational orbit has three or four members",
    "all incomplete orbits omit the same strict quadrant",
]

_ODD_SIZES = tuple(range(9, 30, 2))
_PROFILES = ("interior", "boundary", "mixed")
_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-keyed odd choice; ordinary draws favor 9..15",
        "valid": "odd 9..29",
    },
    "n_orbits": {
        "type": "int",
        "default": "difficulty-keyed draw; ordinary 3..6",
        "valid": "3..12 subject to profile capacity",
    },
    "missing_quadrant": {
        "type": "int",
        "default": "rng 0..3 (NE,SE,SW,NW)",
        "valid": "0..3",
    },
    "n_complete_orbits": {
        "type": "int",
        "default": "rng 0..min(2,n_orbits-1)",
        "valid": "0..2 and less than n_orbits",
    },
    "profile": {
        "type": "str",
        "default": "rng interior|mixed; hard may use boundary",
        "valid": "interior|boundary|mixed",
    },
}


def _strict_int(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool or a coercible value)")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")
    return value


def _validate_call(difficulty: object, overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis: " + ", ".join(unknown))
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    if "grid_size" in overrides:
        value = overrides["grid_size"]
        if type(value) is not int or value not in _ODD_SIZES:
            raise TypeError("grid_size must be an exact odd integer in 9..29")
    if "n_orbits" in overrides:
        _strict_int(overrides["n_orbits"], "n_orbits", 3, 12)
    if "missing_quadrant" in overrides:
        _strict_int(overrides["missing_quadrant"], "missing_quadrant", 0, 3)
    if "n_complete_orbits" in overrides:
        _strict_int(overrides["n_complete_orbits"], "n_complete_orbits", 0, 2)
    if "profile" in overrides:
        value = overrides["profile"]
        if type(value) is not str or value not in _PROFILES:
            raise TypeError("profile must be interior, boundary, or mixed")


def _rotate(cell: tuple[int, int], center: int) -> tuple[int, int]:
    r, c = cell
    dr, dc = r - center, c - center
    return center + dc, center - dr


def _orbit(cell: tuple[int, int], center: int) -> tuple[tuple[int, int], ...]:
    cells = []
    current = cell
    for _ in range(4):
        cells.append(current)
        current = _rotate(current, center)
    return tuple(cells)


def _quadrant(cell: tuple[int, int], center: int) -> int | None:
    r, c = cell
    dr, dc = r - center, c - center
    if dr < 0 and dc > 0:
        return 0  # NE
    if dr > 0 and dc > 0:
        return 1  # SE
    if dr > 0 and dc < 0:
        return 2  # SW
    if dr < 0 and dc < 0:
        return 3  # NW
    return None


def _grid_error(grid: object) -> str | None:
    if type(grid) is not list or not grid:
        return "grid must be a nonempty list"
    if type(grid[0]) is not list or not grid[0]:
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return "grid cells must be exact integer colors 0..9"
    return None


def analyze_scene(grid: object) -> dict[str, Any]:
    """Return a deterministic structural analysis; raise on malformed grids.

    This helper is intentionally stricter than a visual census.  It exposes the
    orbit-level intermediate used by tests and future audits without supplying
    any hidden episode setting.
    """
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    assert isinstance(grid, list)
    h, w = len(grid), len(grid[0])
    center = h // 2
    palette = sorted({cell for row in grid for cell in row})
    marker_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}

    orbit_map: dict[tuple[tuple[int, int], ...], set[tuple[int, int]]] = {}
    for cell in red:
        key = tuple(sorted(set(_orbit(cell, center))))
        orbit_map.setdefault(key, set()).add(cell)

    rows = []
    missing_quadrants: list[int] = []
    for key in sorted(orbit_map):
        present = sorted(orbit_map[key])
        missing = sorted(set(key) - set(present))
        if len(missing) == 1:
            q = _quadrant(missing[0], center)
            if q is not None:
                missing_quadrants.append(q)
        rows.append({
            "orbit": [list(cell) for cell in key],
            "present": [list(cell) for cell in present],
            "missing": list(missing[0]) if len(missing) == 1 else [list(cell) for cell in missing],
            "present_count": len(present),
        })

    if red:
        r0 = min(r for r, _ in red)
        r1 = max(r for r, _ in red)
        c0 = min(c for _, c in red)
        c1 = max(c for _, c in red)
        bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    else:
        bbox_h = bbox_w = 0
    unique_missing = sorted(set(missing_quadrants))
    return {
        "height": h,
        "width": w,
        "size": h if h == w else None,
        "center": [center, center],
        "palette": palette,
        "marker_cells": [list(cell) for cell in marker_cells],
        "red_count": len(red),
        "orbit_count": len(rows),
        "complete_orbits": sum(row["present_count"] == 4 for row in rows),
        "incomplete_orbits": sum(row["present_count"] == 3 for row in rows),
        "missing_quadrants": unique_missing,
        "missing_quadrant": unique_missing[0] if len(unique_missing) == 1 else None,
        "touches_boundary": any(r in (0, h - 1) or c in (0, w - 1) for r, c in red),
        "red_bbox_height": bbox_h,
        "red_bbox_width": bbox_w,
        "orbits": rows,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return violations of the admitted canonical input grammar."""
    errors: list[str] = []
    malformed = _grid_error(grid)
    if malformed:
        return [malformed]
    scene = analyze_scene(grid)
    h, w = scene["height"], scene["width"]
    if h != w:
        errors.append(f"board must be square, got {h}x{w}")
    if h not in _ODD_SIZES:
        errors.append("board side must be an odd integer in 9..29")
    if scene["palette"] != [0, 2, 9]:
        errors.append(f"palette must be exactly [0, 2, 9], got {scene['palette']}")
    expected_marker = [[h // 2, w // 2]]
    if scene["marker_cells"] != expected_marker:
        errors.append("there must be exactly one color-9 marker at the geometric center")
    if not 3 <= scene["orbit_count"] <= 12:
        errors.append("scene must contain 3..12 rotational orbits")
    bad_counts = [row["present_count"] for row in scene["orbits"] if row["present_count"] not in (3, 4)]
    if bad_counts:
        errors.append("every red rotational orbit must contain exactly three or four members")
    if scene["incomplete_orbits"] < 1:
        errors.append("at least one rotational orbit must be incomplete")
    if len(scene["missing_quadrants"]) != 1:
        errors.append("all incomplete orbits must omit the same strict quadrant")
    if scene["complete_orbits"] > 2:
        errors.append("at most two complete red orbits are admitted")
    return errors


def _band_values(difficulty: object) -> tuple[tuple[int, ...], tuple[int, int], tuple[str, ...]]:
    if difficulty == "easy":
        return (9, 11), (3, 4), ("interior", "mixed")
    if difficulty == "medium":
        return (9, 11, 13, 15), (3, 6), ("interior", "mixed")
    if difficulty == "hard":
        return (15, 17, 19, 21, 23, 25, 27, 29), (6, 12), _PROFILES
    return (9, 11, 13), (3, 5), ("interior", "mixed")


def _draw_choice(ctx, label: str, default_options: tuple[Any, ...], all_options: tuple[Any, ...], overrides: dict[str, object]):
    return ctx.draw_choice(label, all_options if label in overrides else default_options)


def _select_offsets(
    *, size: int, count: int, profile: str, rng
) -> list[tuple[int, int]]:
    center = size // 2
    all_cells = [(a, b) for a in range(1, center + 1) for b in range(1, center + 1)]
    boundary = [(a, b) for a, b in all_cells if a == center or b == center]
    interior = [(a, b) for a, b in all_cells if a < center and b < center]
    if profile == "interior":
        if count > len(interior):
            raise ValueError(
                f"n_orbits={count} exceeds interior capacity {len(interior)} for grid_size={size}"
            )
        chosen = rng.sample(interior, count)
    else:
        required = [rng.choice(boundary)]
        if profile == "mixed":
            if not interior:
                raise ValueError("mixed profile needs at least one interior orbit")
            required.append(rng.choice(interior))
        remaining = [cell for cell in all_cells if cell not in required]
        if count < len(required):
            raise ValueError(f"profile {profile} requires at least {len(required)} orbits")
        chosen = required + rng.sample(remaining, count - len(required))
    rng.shuffle(chosen)
    return chosen


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
    size_options, orbit_bounds, profile_options = _band_values(difficulty)
    size = _draw_choice(ctx, "grid_size", size_options, _ODD_SIZES, overrides)
    n_orbits = ctx.draw_int_strict(
        "n_orbits",
        3 if "n_orbits" in overrides else orbit_bounds[0],
        12 if "n_orbits" in overrides else orbit_bounds[1],
    )
    missing = ctx.draw_int_strict("missing_quadrant", 0, 3)
    profile = _draw_choice(ctx, "profile", profile_options, _PROFILES, overrides)
    complete = ctx.draw_int_strict("n_complete_orbits", 0, min(2, n_orbits - 1))
    if complete >= n_orbits:
        raise ValueError("n_complete_orbits must be less than n_orbits")

    offsets = _select_offsets(
        size=size,
        count=n_orbits,
        profile=profile,
        rng=ctx.draw_rng("orbit_layout"),
    )
    complete_indices = set(ctx.draw_rng("complete_orbits").sample(range(n_orbits), complete))
    center = size // 2
    grid = full_grid(size, size, 0)
    grid[center][center] = 9
    for index, (a, b) in enumerate(offsets):
        cells = list(_orbit((center - a, center + b), center))
        for quadrant, (r, c) in enumerate(cells):
            if index not in complete_indices and quadrant == missing:
                continue
            grid[r][c] = 2

    violations = self_check(grid, difficulty=difficulty)
    if violations:
        raise ValueError("constructed invalid rotational scene: " + "; ".join(violations))
    return grid
