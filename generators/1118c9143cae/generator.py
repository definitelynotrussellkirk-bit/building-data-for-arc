"""Semantic generator for ARC task 1118c9143cae.

The canonical rule preserves every input cell and echoes each nonzero cell at
its 180-degree (point-reflected) position.  Generated inputs contain at most
one source from each nontrivial half-turn orbit, so the label is unambiguous
and no source overwrites another source's echo.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1118c9143cae"
TASK_ID = "1118c9143cae"
VERSION = "2.0.0"
RULE_HASH = "3c7019266d5c"
EXAMPLES_NEEDED = 3
ALLOW_IDENTITY_OUTPUT = False

CANONICAL_PROGRAM = """(rule!
 ;; Overlay the 180-degree ROTATION onto the grid: every non-zero cell also
 ;; lands at its point-mirrored position.
 (overlay g (rotate-180 g)))"""

SUMMARY = (
    "Preserve every source cell and add a same-color echo at its 180-degree "
    "point reflection (h-1-r, w-1-c)."
)

INVARIANTS = [
    "background is ARC color 0",
    "at least three source cells and at least two source colors are present",
    "at most one source occupies each nontrivial half-turn orbit",
    "at least one source is not a half-turn fixed point",
    "the output keeps originals and adds same-color half-turn echoes",
]

SCENE_PROFILES = ("interior", "boundary", "fixed_point")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw in 5..30",
        "valid": "5..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw in 5..30",
        "valid": "5..30",
    },
    "cell_count": {
        "type": "int",
        "default": "difficulty-aware lawful draw in 3..40",
        "valid": "3..40",
    },
    "n_colors": {
        "type": "int",
        "default": "lawful draw in 2..8",
        "valid": "2..8",
    },
    "scene_profile": {
        "type": "str",
        "default": "scheduled interior|boundary|fixed_point",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_DIFFICULTY_DIMENSIONS = {
    None: (5, 30),
    "easy": (5, 13),
    "medium": (11, 22),
    "hard": (20, 30),
}
_DIFFICULTY_COUNTS = {
    None: (4, 24),
    "easy": (3, 9),
    "medium": (7, 22),
    "hard": (14, 40),
}


def _reflect(height: int, width: int, row: int, col: int) -> tuple[int, int]:
    return height - 1 - row, width - 1 - col


def _is_boundary(height: int, width: int, cell: tuple[int, int]) -> bool:
    row, col = cell
    return row in (0, height - 1) or col in (0, width - 1)


def _incompatible(message: str, *axes: str) -> None:
    error = ValueError(message)
    error.incompatible_axes = tuple(dict.fromkeys(axes))
    raise error


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30x30"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC integer colors 0..9 (bool is not a color)"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "height": None,
            "width": None,
            "sources": (),
            "colors": (),
            "boundary_count": 0,
            "scene_profile": None,
        }

    height, width = len(grid), len(grid[0])
    sources = tuple(
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    )
    if len(sources) < 3:
        errors.append("grid needs at least three nonzero source cells")
    colors = tuple(sorted({value for _, _, value in sources}))
    if len(colors) < 2:
        errors.append("grid needs at least two distinct nonzero source colors")

    source_cells = {(row, col) for row, col, _ in sources}
    nonfixed = 0
    for row, col, _ in sources:
        reflected = _reflect(height, width, row, col)
        if reflected == (row, col):
            continue
        nonfixed += 1
        if reflected in source_cells:
            errors.append(
                f"source ({row},{col}) and its 180-degree reflection "
                f"({reflected[0]},{reflected[1]}) are both nonzero"
            )
            break
    if sources and nonfixed == 0:
        errors.append("at least one source must move under the half-turn")

    boundary_count = sum(
        _is_boundary(height, width, (row, col)) for row, col, _ in sources
    )
    center_occupied = (
        height % 2 == 1
        and width % 2 == 1
        and grid[height // 2][width // 2] != 0
    )
    if center_occupied:
        scene_profile = "fixed_point"
    elif sources and boundary_count >= min(4, len(sources)):
        scene_profile = "boundary"
    elif sources and boundary_count == 0:
        scene_profile = "interior"
    else:
        # Canonical inputs with one boundary source are lawful, but do not claim
        # to realize one of the deliberately stronger generated profiles.
        scene_profile = None

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "sources": sources,
        "colors": colors,
        "boundary_count": boundary_count,
        "scene_profile": scene_profile,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Return an input-pure Python mirror of the exact canonical rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0:
                reflected_row, reflected_col = _reflect(height, width, row, col)
                output[reflected_row][reflected_col] = value
    return output


def _echo_horizontal(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                output[row][width - 1 - col] = grid[row][col]
    return output


def _echo_vertical(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                output[height - 1 - row][col] = grid[row][col]
    return output


def _rotate_only(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _echo_first_color(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    first_color = next(
        (
            grid[row][col]
            for row in range(height)
            for col in range(width)
            if grid[row][col] != 0
        ),
        None,
    )
    output = [list(row) for row in grid]
    if first_color is None:
        return output
    for row in range(height):
        for col in range(width):
            if grid[row][col] == first_color:
                reflected_row, reflected_col = _reflect(height, width, row, col)
                output[reflected_row][reflected_col] = first_color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "horizontal_echo": _echo_horizontal,
    "vertical_echo": _echo_vertical,
    "rotate_only": _rotate_only,
    "first_color_only": _echo_first_color,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _witness_center_fixed_point(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return (
        height % 2 == 1
        and width % 2 == 1
        and grid[height // 2][width // 2] != 0
    )


def _witness_boundary_sources(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        grid[row][col] != 0
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _witness_multi_color(grid: list[list[int]]) -> bool:
    return len({value for row in grid for value in row if value != 0}) >= 2


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "center_fixed_point": _witness_center_fixed_point,
    "boundary_sources": _witness_boundary_sources,
    "multi_color": _witness_multi_color,
}
WITNESS_RIVALS = {
    "center_fixed_point": ("rotate_only",),
    "boundary_sources": ("horizontal_echo", "vertical_echo"),
    "multi_color": ("first_color_only",),
}


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept canonical and generated sparse scenes, reject shortcut fixtures."""
    return list(_analysis(grid)["errors"])


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate source geometry and, when supplied, exact observed overrides."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors or not meta or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides")
    if not isinstance(requested, dict):
        return errors
    observed = _observed_from_analysis(analysis)
    for name, expected in requested.items():
        if name in AXES and observed.get(name) != expected:
            errors.append(
                f"requested override {name}={expected!r} was not realized "
                f"(observed {observed.get(name)!r})"
            )
    return errors


def _observed_from_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    if analysis["errors"]:
        return {}
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "cell_count": len(analysis["sources"]),
        "n_colors": len(analysis["colors"]),
    }
    if analysis["scene_profile"] is not None:
        observed["scene_profile"] = analysis["scene_profile"]
    return observed


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every live generated axis; return {} for invalid impostors."""
    return _observed_from_analysis(_analysis(grid))


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Flag declared rivals that fit every demonstration but fail the query."""
    errors: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"{name} fits all demonstrations but fails the query")
    return errors


def _orbit_representatives(height: int, width: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    seen: set[tuple[int, int]] = set()
    orbits: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            cell = (row, col)
            if cell in seen:
                continue
            reflected = _reflect(height, width, row, col)
            seen.add(cell)
            seen.add(reflected)
            if reflected != cell:
                orbits.append(tuple(sorted((cell, reflected))))
    return tuple(orbits)


def _dimension_options(difficulty: str | None, profile: str) -> tuple[int, ...]:
    lo, hi = _DIFFICULTY_DIMENSIONS[difficulty]
    options = tuple(range(lo, hi + 1))
    if profile == "fixed_point":
        options = tuple(value for value in options if value % 2 == 1)
    return options


def _draw_dimension(ctx, label: str, difficulty: str | None, profile: str, overrides: dict[str, Any]) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, 5, 30)
    return ctx.draw_choice(label, _dimension_options(difficulty, profile))


def _candidate_orbits(
    height: int,
    width: int,
    profile: str,
) -> tuple[
    tuple[tuple[tuple[int, int], tuple[int, int]], ...],
    tuple[tuple[tuple[int, int], tuple[int, int]], ...],
]:
    all_orbits = _orbit_representatives(height, width)
    interior = tuple(
        orbit
        for orbit in all_orbits
        if not any(_is_boundary(height, width, cell) for cell in orbit)
    )
    boundary = tuple(
        orbit
        for orbit in all_orbits
        if all(_is_boundary(height, width, cell) for cell in orbit)
    )
    if profile in ("interior", "fixed_point"):
        return interior, ()
    return all_orbits, boundary


def _choose_positions(
    height: int,
    width: int,
    profile: str,
    cell_count: int,
    rng,
) -> list[tuple[int, int]]:
    all_candidates, boundary_candidates = _candidate_orbits(height, width, profile)
    fixed = [(height // 2, width // 2)] if profile == "fixed_point" else []
    moving_count = cell_count - len(fixed)

    if profile == "boundary":
        required_boundary = min(4, cell_count)
        selected_orbits = list(rng.sample(list(boundary_candidates), required_boundary))
        selected_set = set(selected_orbits)
        remainder = [orbit for orbit in all_candidates if orbit not in selected_set]
        selected_orbits.extend(rng.sample(remainder, moving_count - required_boundary))
    else:
        selected_orbits = list(rng.sample(list(all_candidates), moving_count))

    positions = [orbit[rng.randrange(2)] for orbit in selected_orbits]
    rng.shuffle(positions)
    # Keep a fixed point from becoming the only nonfixed evidence for a color.
    positions.extend(fixed)
    return positions


def _build_candidate(
    height: int,
    width: int,
    profile: str,
    cell_count: int,
    colors: tuple[int, ...],
    rng,
) -> list[list[int]]:
    positions = _choose_positions(height, width, profile, cell_count, rng)
    values = [colors[index % len(colors)] for index in range(cell_count)]
    rng.shuffle(values)
    grid = full_grid(height, width, 0)
    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def _capacity(height: int, width: int, profile: str) -> int:
    candidates, _ = _candidate_orbits(height, width, profile)
    return len(candidates) + (1 if profile == "fixed_point" else 0)


def _validate_requested_types(overrides: dict[str, Any]) -> None:
    for name in ("grid_h", "grid_w", "cell_count", "n_colors"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] is not None
        and not isinstance(overrides["scene_profile"], str)
    ):
        raise TypeError("scene_profile override must be a string")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, shortcut-resistant canonical input scene."""
    if difficulty not in _DIFFICULTY_DIMENSIONS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    _validate_requested_types(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_options = (
        SCENE_PROFILES
        if "scene_profile" in overrides and overrides["scene_profile"] is not None
        else (SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)],)
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    height = _draw_dimension(ctx, "grid_h", difficulty, profile, overrides)
    width = _draw_dimension(ctx, "grid_w", difficulty, profile, overrides)

    if profile == "fixed_point" and (height % 2 == 0 or width % 2 == 0):
        _incompatible(
            "fixed_point scene_profile requires odd grid_h and grid_w",
            "grid_h",
            "grid_w",
            "scene_profile",
        )

    capacity = _capacity(height, width, profile)
    if "cell_count" in overrides and overrides["cell_count"] is not None:
        cell_count = ctx.draw_int_strict("cell_count", 3, 40)
    else:
        low, high = _DIFFICULTY_COUNTS[difficulty]
        high = min(high, 40, capacity)
        low = min(low, high)
        cell_count = ctx.draw_int_strict("cell_count", low, high)
    if cell_count > capacity:
        _incompatible(
            f"cell_count={cell_count} exceeds {profile} capacity {capacity} "
            f"for grid_h={height}, grid_w={width}",
            "grid_h",
            "grid_w",
            "cell_count",
            "scene_profile",
        )

    if "n_colors" in overrides and overrides["n_colors"] is not None:
        n_colors = ctx.draw_int_strict("n_colors", 2, 8)
    else:
        n_colors = ctx.draw_int_strict("n_colors", 2, min(8, cell_count))
    if n_colors > cell_count:
        _incompatible(
            f"n_colors={n_colors} cannot exceed cell_count={cell_count}",
            "cell_count",
            "n_colors",
        )

    colors = ctx.draw_distinct_colors("source_colors", n=n_colors, exclude={0})
    rng = ctx.draw_rng("layout")
    requested = {
        "grid_h": height,
        "grid_w": width,
        "cell_count": cell_count,
        "n_colors": n_colors,
        "scene_profile": profile,
    }
    official: list[list[int]] | None = None
    for _ in range(160):
        grid = _build_candidate(height, width, profile, cell_count, colors, rng)
        if self_check(grid, meta={"overrides": requested}):
            continue
        official = rule_mirror(grid)
        if official == grid:
            continue
        if any(rival(grid) == official for rival in SEMANTIC_RIVALS.values()):
            continue
        if height == width == 30 and cell_count >= 40:
            rows = {row for row, _, _ in _analysis(grid)["sources"]}
            cols = {col for _, col, _ in _analysis(grid)["sources"]}
            if len(rows) < 10 or len(cols) < 10:
                continue
        return [row[:] for row in grid]
    raise AssertionError(
        "could not construct a lawful shortcut-resistant scene for "
        f"profile={profile!r}, grid={height}x{width}, cell_count={cell_count}"
    )
