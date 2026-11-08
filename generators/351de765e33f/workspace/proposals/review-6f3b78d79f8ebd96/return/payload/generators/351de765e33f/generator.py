"""Generate varied component-ranking lessons for task ``351de765e33f``.

The canonical rule finds monochrome 4-connected nonzero objects, sorts them by
size descending and then by top-left reading order, and recolors the second
object in that total order to cyan (8).  The linked scene profiles below cover
all three public size signatures plus strict, repeated-rank, and all-equal
extrapolations.  Different-colored objects may be separated, diagonally touch,
or edge-touch; this is deliberate because the authority segments by color.
"""
from __future__ import annotations

from copy import deepcopy
from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "351de765e33f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"  # canonical topology, contact witnesses, identifiable schedule
RULE_HASH = "f074243a0544"  # sha256 of whitespace-normalized canonical rule
SUMMARY = (
    "Sort monochrome 4-connected nonzero objects by size descending, breaking "
    "ties by top-left reading order, and recolor the second object cyan (8)."
)
INVARIANTS = [
    "three to six distinct-colored monochrome 4-connected objects are present",
    "different-colored objects may be separated, diagonally touch, or edge-touch",
    "cyan (8) is absent from the input, so the selected object always changes",
    "the second rank is determined by size then top-left reading order",
    "every five-example schedule window contains tie and colorblind-rival witnesses",
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

# The finite semantic schedule is declared for exhaustive lesson-census replay.
# Repeated-largest and all-equal witnesses are four positions apart, so every
# cyclic five-demonstration window refutes the second-largest-distinct-size rival.
LESSON_SCHEDULE_PERIOD = 8
_PROFILE_SEQUENCE = (
    "tie_largest_four",
    "canonical_644",
    "canonical_942",
    "strict_four",
    "all_equal_five",
    "canonical_864",
    "strict_six",
    "tie_second_four",
)
_PROFILE_SCHEDULES = {
    band: _PROFILE_SEQUENCE for band in ("easy", "medium", "hard", "all")
}

# Edge contacts occur frequently enough that every cyclic five-example window
# refutes a colorblind 4-connected grouping shortcut.  A seed-dependent cyclic
# shift avoids binding a topology to one size profile while preserving coverage.
_TOPOLOGY_SEQUENCE = (
    "edge_contact",
    "separated",
    "diagonal_contact",
    "edge_contact",
    "separated",
    "edge_contact",
    "diagonal_contact",
    "edge_contact",
)
_TOPOLOGIES = frozenset(_TOPOLOGY_SEQUENCE)
_PUBLIC_DIMENSIONS = {
    "canonical_644": (8, 9),
    "canonical_942": (8, 9),
    "canonical_864": (9, 10),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted linked component-size profile",
        "valid": "canonical_644|canonical_942|canonical_864|strict_four|strict_six|tie_second_four|tie_largest_four|all_equal_five",
    },
}


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    profile = overrides.get("scene_profile")
    if profile is not None and (
        type(profile) is not str or profile not in SCENE_PROFILES
    ):
        raise ValueError(f"invalid scene_profile: {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-identity component-ranking input."""
    _validate_call(seed, sample_index, difficulty, overrides)
    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_profile = overrides.get("scene_profile") is None
    if default_profile:
        scheduled = _PROFILE_SCHEDULES[band][
            sample_index % LESSON_SCHEDULE_PERIOD
        ]
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    topology = _TOPOLOGY_SEQUENCE[
        (sample_index + seed) % LESSON_SCHEDULE_PERIOD
    ]
    rng = ctx.draw_rng(f"component_scene_{profile}_{topology}_{band}")
    grid = _construct_scene(
        profile,
        SCENE_SPECS[profile],
        rng,
        band,
        topology,
        use_public_anchor=default_profile and profile in PUBLIC_PROFILES,
    )
    analysis = _analyze(grid)
    observed_topology = _contact_kind(analysis["components"])
    if (
        analysis["errors"]
        or analysis["profile"] != profile
        or observed_topology != topology
    ):
        raise RuntimeError(
            f"constructed {profile!r}/{topology!r}, observed "
            f"{analysis['profile']!r}/{observed_topology!r}: "
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
        "contact_kind": _contact_kind(analysis["components"]),
    }


def _difficulty_band(difficulty) -> str:
    if difficulty is None:
        return "all"
    if type(difficulty) is str and difficulty in {"easy", "medium", "hard"}:
        return difficulty
    raise ValueError(
        "difficulty must be None, 'easy', 'medium', or 'hard'"
    )


def _band_int(rng, lo: int, hi: int, band: str) -> int:
    if band == "easy":
        return rng.randint(lo, lo + (hi - lo) // 2)
    if band == "hard":
        return rng.randint(lo + (hi - lo + 1) // 2, hi)
    return rng.randint(lo, hi)


def _construct_scene(
    profile: str,
    spec: SceneSpec,
    rng,
    band: str,
    topology: str,
    *,
    use_public_anchor: bool,
) -> Grid:
    if topology not in _TOPOLOGIES:
        raise ValueError(f"unknown topology: {topology!r}")
    if use_public_anchor:
        height, width = _PUBLIC_DIMENSIONS[profile]
    else:
        height = _band_int(rng, *spec.h_range, band)
        width = _band_int(rng, *spec.w_range, band)

    grid = full_grid(height, width, 0)
    count = len(spec.sizes)
    row_parts, col_parts = (2, 2) if count <= 4 else (2, 3)
    row_bands = _axis_bands(height, row_parts)
    col_bands = _axis_bands(width, col_parts)
    slots = [
        (r0, r1, c0, c1)
        for r0, r1 in row_bands
        for c0, c1 in col_bands
    ]
    colors = rng.sample(COLORS, count)
    styles = ["rectangle", "polyomino", "line"] * ((count + 2) // 3)
    styles = styles[:count]
    rng.shuffle(styles)
    assignments = list(zip(spec.sizes, colors, styles))

    if topology == "separated":
        rng.shuffle(slots)
        for (size, color, style), slot in zip(assignments, slots):
            _paint_slot_shape(grid, size, color, style, slot, rng)
        return grid

    # The two highest-ranked size entries occupy the left and middle slots in
    # the first row.  Their deliberate contact changes a colorblind grouping
    # rival's rank order while distinct colors keep the canonical objects apart.
    pair_slots = (
        (row_bands[0][0], row_bands[0][1], col_bands[0][0], col_bands[0][1]),
        (row_bands[0][0], row_bands[0][1], col_bands[1][0], col_bands[1][1]),
    )
    _paint_contact_pair(
        grid,
        assignments[0],
        assignments[1],
        pair_slots[0],
        pair_slots[1],
        topology,
        rng,
    )
    remaining_slots = [slot for slot in slots if slot not in pair_slots]
    rng.shuffle(remaining_slots)
    for (size, color, style), slot in zip(assignments[2:], remaining_slots):
        _paint_slot_shape(grid, size, color, style, slot, rng)
    return grid


def _paint_slot_shape(grid, size, color, style, slot, rng) -> None:
    r0, r1, c0, c1 = slot
    cells = _shape_cells(r1 - r0, c1 - c0, size, style, rng)
    for row, col in cells:
        grid[r0 + row][c0 + col] = color


def _grow_shape(allowed, size: int, required, rng):
    cells = set(required)
    if not cells or not cells <= allowed:
        raise ValueError("required cells must be a nonempty subset of allowed cells")
    if len(cells) > size:
        raise ValueError("required cells exceed requested shape size")
    while len(cells) < size:
        frontier = {
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in _DIR4
            if (row + dr, col + dc) in allowed
            and (row + dr, col + dc) not in cells
        }
        if not frontier:
            raise RuntimeError("anchored-shape frontier exhausted before target size")
        cells.add(rng.choice(sorted(frontier)))
    return cells


def _paint_contact_pair(
    grid,
    left_assignment,
    right_assignment,
    left_slot,
    right_slot,
    topology: str,
    rng,
) -> None:
    left_size, left_color, _ = left_assignment
    right_size, right_color, _ = right_assignment
    r0, r1, c0, c1 = left_slot
    rr0, rr1, rc0, rc1 = right_slot
    if (r0, r1) != (rr0, rr1) or rc0 != c1 + 1:
        raise RuntimeError("contact slots must be horizontally adjacent with one gap")

    gap_col = c1
    left_allowed = {
        (row, col)
        for row in range(r0, r1)
        for col in range(c0, c1)
    }
    right_allowed = {
        (row, col)
        for row in range(rr0, rr1)
        for col in range(rc0, rc1)
    }

    if topology == "edge_contact":
        left_contact = (r0, gap_col)
        right_contact = (r0, rc0)
        left_required = {left_contact, (r0, gap_col - 1)}
    elif topology == "diagonal_contact":
        left_contact = (r0 + 1, gap_col)
        right_contact = (r0, rc0)
        left_required = {
            left_contact,
            (r0 + 1, gap_col - 1),
            (r0, gap_col - 1),
        }
    else:
        raise ValueError(f"contact topology required, got {topology!r}")

    left_cells = _grow_shape(
        left_allowed | {left_contact}, left_size, left_required, rng
    )
    if topology == "diagonal_contact":
        right_allowed = {
            cell
            for cell in right_allowed
            if all(
                abs(cell[0] - other[0]) + abs(cell[1] - other[1]) != 1
                for other in left_cells
            )
        }
    right_cells = _grow_shape(
        right_allowed, right_size, {right_contact}, rng
    )

    for row, col in left_cells:
        grid[row][col] = left_color
    for row, col in right_cells:
        if grid[row][col] != 0:
            raise RuntimeError("contact construction overlapped objects")
        grid[row][col] = right_color

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



def _contact_kind(components) -> str:
    owner = {
        cell: index
        for index, obj in enumerate(components)
        for cell in obj["cells"]
    }
    diagonal = False
    for cell, index in owner.items():
        for dr, dc in _DIR8:
            neighbor = cell[0] + dr, cell[1] + dc
            other = owner.get(neighbor)
            if other is None or other == index:
                continue
            if abs(dr) + abs(dc) == 1:
                return "edge_contact"
            diagonal = True
    return "diagonal_contact" if diagonal else "separated"


def _paint_target(grid, cells) -> Grid:
    output = [list(row) for row in grid]
    for row, col in cells:
        output[row][col] = 8
    return output


def _second_largest_distinct_size(grid: Grid) -> Grid:
    """Rival: rank distinct sizes, not individual objects."""
    components = _components(grid)
    sizes = sorted({obj["size"] for obj in components}, reverse=True)
    if len(sizes) < 2:
        return [list(row) for row in grid]
    target_size = sizes[1]
    target = next(obj for obj in components if obj["size"] == target_size)
    return _paint_target(grid, target["cells"])


def _multicolor_components(grid: Grid, connectivity: int):
    deltas = _DIR4 if connectivity == 4 else _DIR8
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in deltas:
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] != 0
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "r1": min(cell[0] for cell in cells),
                    "c1": min(cell[1] for cell in cells),
                }
            )
    return sorted(components, key=lambda obj: (-obj["size"], obj["r1"], obj["c1"]))


def _colorblind_rank_two(grid: Grid, connectivity: int) -> Grid:
    components = _multicolor_components(grid, connectivity)
    if not components:
        return [list(row) for row in grid]
    target = components[1] if len(components) >= 2 else components[0]
    return _paint_target(grid, target["cells"])


def _colorblind_4_connected(grid: Grid) -> Grid:
    """Rival: ignore colors and use 4-connected nonzero blobs."""
    return _colorblind_rank_two(grid, 4)


def _colorblind_8_connected(grid: Grid) -> Grid:
    """Rival: ignore colors and use 8-connected nonzero blobs."""
    return _colorblind_rank_two(grid, 8)

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



def _witness_distinct_size(grid: Grid) -> bool:
    return rule_mirror(grid) != _second_largest_distinct_size(grid)


def _witness_colorblind_4(grid: Grid) -> bool:
    return rule_mirror(grid) != _colorblind_4_connected(grid)


def _witness_colorblind_8(grid: Grid) -> bool:
    return rule_mirror(grid) != _colorblind_8_connected(grid)


strict_canonical_like = self_check
SEMANTIC_WITNESSES = {
    "repeated_largest_or_all_equal": _witness_distinct_size,
    "edge_contact": _witness_colorblind_4,
    "cross_color_contact": _witness_colorblind_8,
}
SEMANTIC_RIVALS = {
    "second_largest_distinct_size": _second_largest_distinct_size,
    "colorblind_4_connected": _colorblind_4_connected,
    "colorblind_8_connected": _colorblind_8_connected,
}
WITNESS_RIVALS = {
    "repeated_largest_or_all_equal": ["second_largest_distinct_size"],
    "edge_contact": ["colorblind_4_connected"],
    "cross_color_contact": ["colorblind_8_connected"],
}
CANONICAL_SHORTCUTS = {
    "second_largest_distinct_size": _second_largest_distinct_size,
    "colorblind_4_connected": _colorblind_4_connected,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
