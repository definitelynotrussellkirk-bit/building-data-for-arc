"""Generator for S9_E1 — singleton seeds sprout cyan orthogonal halos.

The canonical rule is unchanged: preserve every nonzero input cell and paint
background cells at Manhattan distance exactly one from at least one seed cyan
(8).  Ordinary scenes use distinct source colors and non-overlapping halos;
position profiles make clipping behavior observable without changing the rule.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad8f89160989"
VERSION = "3.2.1"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A 0-background grid ordinarily contains 2-6 distinct-colored singleton "
    "seeds from {2,3,4,6,7,9}; the strict n_seeds override also supports the "
    "one-seed boundary. Seeds are at pairwise Manhattan distance at least 3, so "
    "their radius-one orthogonal halos do not overlap or erase another seed. "
    "Preserve the seeds and paint every in-bounds orthogonal background "
    "neighbor cyan (8). Position profiles exercise interior, edge, corner, "
    "and mixed clipping cases."
)

EXAMPLES_NEEDED = 3
SEED_COLORS = (2, 3, 4, 6, 7, 9)
POSITION_PROFILES = ("interior", "edge", "corner", "mixed")
HELPFUL_TEXTURES = POSITION_PROFILES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INVARIANTS = [
    "background is 0 and color 8 never appears in an input",
    "ordinary inputs contain distinct-colored singleton seeds",
    "seed centers are at pairwise Manhattan distance at least 3",
    "the output preserves seeds and paints only orthogonal background neighbors 8",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 7..14", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 7..14", "valid": "5..14"},
    "n_seeds": {"type": "int", "default": "difficulty-aware rng 2..6", "valid": "1..6"},
    "position_bias": {"type": "str", "default": "rng profile", "valid": "|".join(POSITION_PROFILES)},
    "texture": {"type": "str", "default": "alias for position_bias", "valid": "|".join(HELPFUL_TEXTURES)},
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "n_seeds", "position_bias", "texture"}


def _exact_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty and rectangular")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return len(grid), width


def _seed_cells(grid) -> list[tuple[int, int, int]]:
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def _far_enough(cells: Iterable[tuple[int, int]], row: int, column: int) -> bool:
    return all(abs(row - old_row) + abs(column - old_column) >= 3 for old_row, old_column in cells)


def _categories(height: int, width: int) -> dict[str, list[tuple[int, int]]]:
    corners = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    corner_set = set(corners)
    edges = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r in (0, height - 1) or c in (0, width - 1)) and (r, c) not in corner_set
    ]
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    noncorner = [*edges, *interior]
    return {"corner": corners, "edge": edges, "interior": interior, "noncorner": noncorner}


def _role_candidates(height: int, width: int, count: int, profile: str) -> list[list[tuple[int, int]]]:
    categories = _categories(height, width)
    if profile == "interior":
        return [categories["interior"] for _ in range(count)]
    if profile == "edge":
        return [categories["edge"] for _ in range(count)]
    if profile == "corner":
        return [categories["corner"], *[categories["noncorner"] for _ in range(count - 1)]]
    if profile == "mixed":
        if count < 2:
            raise ValueError("position_bias='mixed' requires at least two seeds")
        return [categories["edge"], categories["interior"], *[categories["noncorner"] for _ in range(count - 2)]]
    raise ValueError(f"position_bias must be one of {POSITION_PROFILES}")


def _place_positions(rng, height: int, width: int, count: int, profile: str) -> list[tuple[int, int]]:
    roles = _role_candidates(height, width, count, profile)
    shuffled: list[list[tuple[int, int]]] = []
    for index, candidates in enumerate(roles):
        options = list(candidates)
        # A role-specific shuffle avoids coupling later roles to the number of
        # candidates tried by earlier roles while remaining local-RNG pure.
        local = list(options)
        rng.shuffle(local)
        if index:
            offset = index % max(1, len(local))
            local = local[offset:] + local[:offset]
        shuffled.append(local)

    def search(index: int, selected: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
        if index == len(shuffled):
            return list(selected)
        for row, column in shuffled[index]:
            if (row, column) in selected or not _far_enough(selected, row, column):
                continue
            selected.append((row, column))
            result = search(index + 1, selected)
            if result is not None:
                return result
            selected.pop()
        return None

    result = search(0, [])
    if result is None:
        raise ValueError(
            f"could not place {count} seeds with position_bias={profile!r} "
            f"in a {height}x{width} grid"
        )
    return result


def observe_profile(grid) -> str:
    """Classify the generated seed placement into the declared profile."""
    height, width = _exact_grid(grid)
    seeds = _seed_cells(grid)
    if not seeds:
        raise ValueError("profile requires at least one seed")
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    positions = {(r, c) for r, c, _ in seeds}
    if positions & corners:
        return "corner"
    boundary = {p for p in positions if p[0] in (0, height - 1) or p[1] in (0, width - 1)}
    if boundary and len(boundary) < len(positions):
        return "mixed"
    if boundary:
        return "edge"
    return "interior"


def _solve_official(grid):
    """Pure Python mirror of the exact canonical Racket update order."""
    height, width = _exact_grid(grid)
    source = deepcopy(grid)
    output = deepcopy(grid)
    seeds = [(r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value != 0]
    for row, column in seeds:
        for dr, dc in _DIRS4:
            rr, cc = row + dr, column + dc
            if 0 <= rr < height and 0 <= cc < width and output[rr][cc] == 0:
                output[rr][cc] = 8
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    texture = overrides.get("texture")
    if texture is not None:
        if type(texture) is not str or texture not in HELPFUL_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")
        if overrides.get("position_bias") not in (None, texture):
            raise ValueError("texture and position_bias must name the same profile")
        overrides = dict(overrides)
        overrides["position_bias"] = texture

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    bands = {
        "easy": ((7, 8), (7, 8), (2, 2)),
        "medium": ((8, 11), (8, 11), (2, 4)),
        "hard": ((10, 14), (10, 14), (4, 6)),
        None: ((7, 10), (7, 10), (2, 4)),
    }
    if difficulty not in bands:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    height_band, width_band, count_band = bands[difficulty]
    height = ctx.draw_int_strict(
        "grid_h", *((5, 14) if "grid_h" in overrides else height_band)
    )
    width = ctx.draw_int_strict(
        "grid_w", *((5, 14) if "grid_w" in overrides else width_band)
    )
    count = ctx.draw_int_strict(
        "n_seeds", *((1, 6) if "n_seeds" in overrides else count_band)
    )

    profile = ctx.draw_choice("position_bias", POSITION_PROFILES)
    colors = ctx.draw_distinct_colors("seed_colors", n=count, exclude={0, 1, 5, 8})
    positions = _place_positions(ctx.draw_rng("layout"), height, width, count, profile)
    grid = full_grid(height, width, 0)
    for (row, column), color in zip(positions, colors):
        grid[row][column] = color
    errors = self_check(grid, difficulty=difficulty, meta={"position_bias": profile})
    if errors:
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        height, width = _exact_grid(grid)
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    if not (5 <= height <= 14 and 5 <= width <= 14):
        errors.append(f"grid dimensions must be in 5..14, got {height}x{width}")
    seeds = _seed_cells(grid)
    if not (1 <= len(seeds) <= 6):
        errors.append(f"expected 1..6 seed cells, got {len(seeds)}")
    colors = [value for _, _, value in seeds]
    if any(value == 8 for value in colors):
        errors.append("color 8 must not appear in an input")
    if any(value not in SEED_COLORS for value in colors):
        errors.append(f"seed colors must come from {SEED_COLORS}")
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct")
    for index, (row, column, _) in enumerate(seeds):
        for old_row, old_column, _ in seeds[:index]:
            distance = abs(row - old_row) + abs(column - old_column)
            if distance < 3:
                errors.append(
                    f"seed centers must have Manhattan distance at least 3; "
                    f"found {distance} between {(old_row, old_column)} and {(row, column)}"
                )
                break
    requested = (meta or {}).get("position_bias")
    if requested in POSITION_PROFILES and seeds:
        observed = observe_profile(grid)
        if observed != requested:
            errors.append(f"position_bias {requested!r} was not realized; observed {observed!r}")
    return errors
