"""Generate varied component-ranking lessons for task ``351de765e33f``.

The canonical rule finds monochrome 4-connected nonzero objects, sorts them by
size descending and then by top-left reading order, and recolors the second
object in that total order to cyan (8).  The linked scene profiles below cover
all three public size signatures plus strict, repeated-rank, and all-equal
extrapolations.  Object colors, shapes, positions, and canvas dimensions vary
independently inside each profile.
"""
from __future__ import annotations

from copy import deepcopy
from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "351de765e33f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # linked-profile rebuild: canonical sizes, tie branches, honest axis
RULE_HASH = "f074243a0544"  # sha256 of whitespace-normalized canonical rule
SUMMARY = (
    "Sort separated monochrome nonzero objects by size descending, breaking "
    "ties by top-left reading order, and recolor the second object cyan (8)."
)
INVARIANTS = [
    "three to six separated monochrome nonzero objects are present",
    "cyan (8) is absent from the input, so the selected object always changes",
    "the second rank is determined by size then top-left reading order",
    "normal draws cover strict sizes, second-rank ties, largest ties, and all-equal sizes",
]

Grid = list[list[int]]
COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


class SceneSpec(NamedTuple):
    sizes: tuple[int, ...]
    h_range: tuple[int, int]
    w_range: tuple[int, int]
    public: bool = False


SCENE_SPECS = {
    # Exact linked size signatures from the two demonstrations and held-out input.
    "canonical_644": SceneSpec((6, 4, 4), (8, 12), (9, 13), True),
    "canonical_942": SceneSpec((9, 4, 2), (8, 12), (9, 13), True),
    "canonical_864": SceneSpec((8, 6, 4), (9, 13), (10, 14), True),
    # Lawful extrapolations isolate comparator branches and count generalization.
    "strict_four": SceneSpec((7, 5, 3, 1), (9, 14), (9, 14)),
    "strict_six": SceneSpec((6, 5, 4, 3, 2, 1), (10, 16), (10, 16)),
    "tie_second_four": SceneSpec((7, 5, 5, 2), (9, 14), (9, 14)),
    "tie_largest_four": SceneSpec((6, 6, 4, 2), (9, 14), (9, 14)),
    "all_equal_five": SceneSpec((3, 3, 3, 3, 3), (9, 14), (9, 14)),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
PUBLIC_PROFILES = tuple(name for name, spec in SCENE_SPECS.items() if spec.public)
_PROFILE_BY_SIZES = {
    tuple(sorted(spec.sizes, reverse=True)): name
    for name, spec in SCENE_SPECS.items()
}

# Each 16-sample band schedule contains every semantic profile at least once.
# Repetition shifts the emphasis without making a branch unreachable.
_PROFILE_SCHEDULES = {
    "easy": (
        "canonical_644", "canonical_942", "canonical_864", "strict_four",
        "canonical_644", "canonical_942", "strict_four", "canonical_864",
        "tie_second_four", "tie_largest_four", "all_equal_five", "strict_six",
        "canonical_644", "canonical_942", "canonical_864", "strict_four",
    ),
    "medium": (
        "canonical_644", "canonical_942", "canonical_864", "strict_four",
        "strict_six", "tie_second_four", "tie_largest_four", "all_equal_five",
        "canonical_644", "tie_second_four", "canonical_942", "tie_largest_four",
        "canonical_864", "all_equal_five", "strict_four", "strict_six",
    ),
    "hard": (
        "strict_six", "tie_second_four", "tie_largest_four", "all_equal_five",
        "strict_four", "strict_six", "tie_second_four", "tie_largest_four",
        "all_equal_five", "canonical_644", "canonical_942", "canonical_864",
        "strict_six", "tie_second_four", "tie_largest_four", "all_equal_five",
    ),
    "all": SCENE_PROFILES + SCENE_PROFILES,
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted linked component-size profile",
        "valid": "canonical_644|canonical_942|canonical_864|strict_four|strict_six|tie_second_four|tie_largest_four|all_equal_five",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-identity component-ranking input."""
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
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    rng = ctx.draw_rng(f"component_scene_{profile}_{band}")
    grid = _construct_scene(SCENE_SPECS[profile], rng, band)
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["profile"] != profile:
        raise RuntimeError(
            f"constructed {profile!r}, observed {analysis['profile']!r}: "
            + "; ".join(analysis["errors"])
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful input grammar and selected-rank semantics."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    profile = analysis["profile"]
    requested = (meta or {}).get("scene_profile") if isinstance(meta, dict) else None
    if requested is not None and requested != profile:
        errors.append(f"scene_profile metadata {requested!r} != observed {profile!r}")

    components = analysis["components"]
    colors = [obj["color"] for obj in components]
    if len(set(colors)) != len(colors):
        errors.append("each object must use a distinct nonzero color")
    if 8 in colors:
        errors.append("input contains reserved output color 8")
    if _components_touch(components):
        errors.append("objects must have a one-cell background moat")

    spec = SCENE_SPECS[profile]
    height, width = analysis["height"], analysis["width"]
    if not (spec.h_range[0] <= height <= spec.h_range[1]):
        errors.append(f"height {height} outside profile range {spec.h_range}")
    if not (spec.w_range[0] <= width <= spec.w_range[1]):
        errors.append(f"width {width} outside profile range {spec.w_range}")

    changed = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != analysis["output"][row][col]
    }
    target_cells = set(components[1]["cells"])
    if changed != target_cells:
        errors.append("test mirror does not change exactly the second-ranked object")
    return errors


def observe_overrides(grid):
    """Recover the exact linked scene profile from object count and sizes."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["profile"] is None:
        return {}
    return {"scene_profile": analysis["profile"]}


def canonical_profile_index(grid):
    """Return the public linked-profile index, or ``None`` for extrapolations."""
    profile = observe_overrides(grid).get("scene_profile")
    return PUBLIC_PROFILES.index(profile) if profile in PUBLIC_PROFILES else None


def rule_mirror(grid: Grid) -> Grid:
    """Test-only Python mirror; the canonical Racket rule remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["output"])


def semantic_signature(grid):
    """Expose linked audit facts without making them generation parameters."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    target = analysis["components"][1]
    return {
        "scene_profile": analysis["profile"],
        "object_count": len(analysis["components"]),
        "sizes": tuple(obj["size"] for obj in analysis["components"]),
        "target_size": target["size"],
        "target_top_left": (target["r1"], target["c1"]),
        "target_color": target["color"],
    }


def _difficulty_band(difficulty) -> str:
    if difficulty is None:
        return "all"
    if isinstance(difficulty, str):
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError(f"invalid difficulty: {difficulty!r}")
        return difficulty
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)):
        raise ValueError(f"invalid difficulty: {difficulty!r}")
    value = max(0.0, min(1.0, float(difficulty)))
    return "easy" if value < 1 / 3 else "medium" if value < 2 / 3 else "hard"


def _band_int(rng, lo: int, hi: int, band: str) -> int:
    if band == "easy":
        return rng.randint(lo, lo + (hi - lo) // 2)
    if band == "hard":
        return rng.randint(lo + (hi - lo + 1) // 2, hi)
    return rng.randint(lo, hi)


def _construct_scene(spec: SceneSpec, rng, band: str) -> Grid:
    height = _band_int(rng, *spec.h_range, band)
    width = _band_int(rng, *spec.w_range, band)
    grid = full_grid(height, width, 0)
    count = len(spec.sizes)
    row_parts, col_parts = (2, 2) if count <= 4 else (2, 3)
    slots = [
        (r0, r1, c0, c1)
        for r0, r1 in _axis_bands(height, row_parts)
        for c0, c1 in _axis_bands(width, col_parts)
    ]
    rng.shuffle(slots)
    slots = slots[:count]
    colors = rng.sample(COLORS, count)
    styles = ["rectangle", "polyomino", "line"] * ((count + 2) // 3)
    styles = styles[:count]
    rng.shuffle(styles)

    for size, color, style, (r0, r1, c0, c1) in zip(
        spec.sizes, colors, styles, slots
    ):
        slot_h, slot_w = r1 - r0, c1 - c0
        cells = _shape_cells(slot_h, slot_w, size, style, rng)
        for row, col in cells:
            grid[r0 + row][c0 + col] = color
    return grid


def _axis_bands(length: int, parts: int) -> list[tuple[int, int]]:
    usable = length - (parts - 1)
    base, extra = divmod(usable, parts)
    sizes = [base + int(index < extra) for index in range(parts)]
    bands = []
    start = 0
    for size in sizes:
        bands.append((start, start + size))
        start += size + 1
    return bands


def _shape_cells(height: int, width: int, size: int, style: str, rng):
    if size < 1 or size > height * width:
        raise ValueError(f"shape size {size} does not fit {height}x{width} slot")

    if style == "rectangle":
        factors = [
            (shape_h, size // shape_h)
            for shape_h in range(1, height + 1)
            if size % shape_h == 0 and size // shape_h <= width
        ]
        if factors:
            shape_h, shape_w = rng.choice(factors)
            top = rng.randint(0, height - shape_h)
            left = rng.randint(0, width - shape_w)
            return {
                (top + row, left + col)
                for row in range(shape_h)
                for col in range(shape_w)
            }

    if style == "line":
        orientations = []
        if size <= width:
            orientations.append("horizontal")
        if size <= height:
            orientations.append("vertical")
        if orientations:
            orientation = rng.choice(orientations)
            if orientation == "horizontal":
                row = rng.randrange(height)
                left = rng.randint(0, width - size)
                return {(row, left + col) for col in range(size)}
            top = rng.randint(0, height - size)
            col = rng.randrange(width)
            return {(top + row, col) for row in range(size)}

    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier = {
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in _DIR4
            if 0 <= row + dr < height
            and 0 <= col + dc < width
            and (row + dr, col + dc) not in cells
        }
        if not frontier:
            raise RuntimeError("connected-shape frontier exhausted before target size")
        cells.add(rng.choice(sorted(frontier)))
    return cells


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"], 0, 0
    height, width = len(grid), len(grid[0])
    errors = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return errors, height, width
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors, height, width


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _DIR4:
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "r1": min(cell[0] for cell in cells),
                    "c1": min(cell[1] for cell in cells),
                }
            )
    return sorted(components, key=lambda obj: (-obj["size"], obj["r1"], obj["c1"]))


def _components_touch(components) -> bool:
    owner = {
        cell: index
        for index, obj in enumerate(components)
        for cell in obj["cells"]
    }
    for cell, index in owner.items():
        for dr, dc in _DIR8:
            neighbor = cell[0] + dr, cell[1] + dc
            if neighbor in owner and owner[neighbor] != index:
                return True
    return False


def _analyze(grid):
    errors, height, width = _validate_grid(grid)
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "profile": None,
        "components": (),
        "output": None,
    }
    if errors:
        return result

    components = _components(grid)
    if len(components) < 2:
        errors.append(f"expected at least two objects, found {len(components)}")
        return result
    sizes = tuple(obj["size"] for obj in components)
    profile = _PROFILE_BY_SIZES.get(sizes)
    if profile is None:
        errors.append(f"unrecognized linked component-size signature: {sizes}")
    output = [list(row) for row in grid]
    for row, col in components[1]["cells"]:
        output[row][col] = 8
    result.update(profile=profile, components=tuple(components), output=output)
    return result
