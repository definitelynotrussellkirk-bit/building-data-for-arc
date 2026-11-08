"""Semantic generator for ARC task 5f6fdf4f9900.

Let N be the number of distinct nonzero input colors.  Enlarge every input
cell to an N x N block.  A nonzero cell becomes a solid block of its color.
For a zero cell, inspect diagonal neighbours in NW, NE, SW, SE order.  The
first diagonal nonzero neighbour whose two intervening orthogonal cells are
zero marks a concave corner: draw a red main or anti diagonal through that
cell's output block, according to the direction of the neighbour.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5f6fdf4f9900"
TASK_ID = "5f6fdf4f9900"
VERSION = "3.0.0"
RULE_HASH = "9c543a96623c"
SUMMARY = "Scale each cell by the nonzero-color count and draw red diagonals in zero blocks at concave diagonal corners."
INVARIANTS = [
    "the input is a 4 through 6 row/column grid with zero background and no red cells",
    "two through five distinct nonzero colors determine scale factor N",
    "every nonzero input cell becomes a solid N by N block of its original color",
    "a zero cell is a corner only when a diagonal neighbour is nonzero and both intervening orthogonal neighbours are zero",
    "eligible diagonal neighbours are considered in NW, NE, SW, SE order",
    "NW or SE draws a red main diagonal; NE or SW draws a red anti diagonal",
    "non-corner zero cells remain zero blocks",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = tuple(
    f"n{count}_{density}"
    for count in range(2, 6)
    for density in ("sparse", "balanced", "dense")
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve recoverable color-count/density lessons",
        "valid": "public_1|public_2|public_3|public_4|n2_sparse|n2_balanced|n2_dense|n3_sparse|n3_balanced|n3_dense|n4_sparse|n4_balanced|n4_dense|n5_sparse|n5_balanced|n5_dense",
    }
}

_PUBLIC_ROWS = (
    "00007/44007/44006/00006/77666",
    "00003/08803/08803/00003/33333",
    "00009/01109/01103/00003/99334",
    "06608/06608/00001/00007/88179",
)
_DIAGONAL_DELTAS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ORTHOGONAL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTE = (1, 3, 4, 5, 6, 7, 8, 9)
_FOREGROUND_RATIOS = {"sparse": 0.44, "balanced": 0.52, "dense": 0.60}
_DIMENSIONS = {
    "easy": ((4, 4), (4, 5), (5, 4), (5, 5)),
    "medium": ((4, 5), (5, 4), (5, 5), (5, 5), (5, 6), (6, 5)),
    "hard": ((5, 5), (5, 6), (6, 5), (6, 6)),
    None: ((4, 4), (4, 5), (5, 4), (5, 5), (5, 5), (5, 6), (6, 5), (6, 6)),
}


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 4 <= len(grid) <= 6:
        return ["input must contain four through six rows"]
    if not isinstance(grid[0], (list, tuple)) or not 4 <= len(grid[0]) <= 6:
        return ["input must contain four through six columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal integers from zero through nine"]
    if any(value == 2 for row in grid for value in row):
        return ["red (2) is reserved for output corner annotations"]
    return []


def _corner_direction(grid, row, col):
    """Return the canonical first eligible diagonal direction, if any."""
    if grid[row][col] != 0:
        return None
    height, width = len(grid), len(grid[0])
    for delta_row, delta_col in _DIAGONAL_DELTAS:
        neighbour_row, neighbour_col = row + delta_row, col + delta_col
        if not (0 <= neighbour_row < height and 0 <= neighbour_col < width):
            continue
        if (
            grid[neighbour_row][neighbour_col] != 0
            and grid[neighbour_row][col] == 0
            and grid[row][neighbour_col] == 0
        ):
            return delta_row, delta_col
    return None


def _corner_orientation(direction):
    return "main" if direction[0] == direction[1] else "anti"


def rule_mirror(grid):
    """Exact Python mirror of the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    colors = {value for row in grid for value in row if value != 0}
    scale = len(colors)
    if scale == 0:
        raise ValueError("at least one nonzero input color is required")
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width * scale)] for _ in range(height * scale)]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            direction = _corner_direction(grid, row, col) if value == 0 else None
            for local_row in range(scale):
                for local_col in range(scale):
                    out_row, out_col = row * scale + local_row, col * scale + local_col
                    if value != 0:
                        output[out_row][out_col] = value
                    elif direction is not None:
                        main = direction[0] == direction[1]
                        on_diagonal = local_row == local_col if main else local_row == scale - 1 - local_col
                        output[out_row][out_col] = 2 if on_diagonal else 0
    return output


def _foreground_target(height, width, density):
    return int(height * width * _FOREGROUND_RATIOS[density] + 0.5)


def _profile_for(grid, color_count, foreground_count):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    height, width = len(grid), len(grid[0])
    density = next(
        (name for name in _FOREGROUND_RATIOS if _foreground_target(height, width, name) == foreground_count),
        None,
    )
    candidate = f"n{color_count}_{density}" if density else None
    return candidate if candidate in GENERAL_PROFILES else None


def _color_is_connected(grid, color):
    height, width = len(grid), len(grid[0])
    cells = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == color}
    if not cells:
        return False
    reached = {next(iter(cells))}
    frontier = list(reached)
    while frontier:
        row, col = frontier.pop()
        for delta_row, delta_col in _ORTHOGONAL_DELTAS:
            neighbour = row + delta_row, col + delta_col
            if neighbour in cells and neighbour not in reached:
                reached.add(neighbour)
                frontier.append(neighbour)
    return reached == cells


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}

    colors = tuple(sorted({value for row in grid for value in row if value != 0}))
    color_count = len(colors)
    zero_count = sum(value == 0 for row in grid for value in row)
    foreground_count = sum(value != 0 for row in grid for value in row)
    if not 2 <= color_count <= 5:
        errors.append("exactly two through five distinct nonzero colors are required")
    profile = _profile_for(grid, color_count, foreground_count)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared color-count/density profile")
    if profile in GENERAL_PROFILES and any(not _color_is_connected(grid, color) for color in colors):
        errors.append("each synthetic color region must be orthogonally connected")

    corners = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            direction = _corner_direction(grid, row, col)
            if direction is not None:
                corners.append((row, col, direction, _corner_orientation(direction)))
    orientations = {corner[3] for corner in corners}
    if orientations != {"main", "anti"}:
        errors.append("both main- and anti-diagonal concave-corner lessons are required")

    output = rule_mirror(grid) if color_count else None
    facts = {
        "colors": colors,
        "scale": color_count,
        "shape": (len(grid), len(grid[0])),
        "zero_count": zero_count,
        "foreground_count": foreground_count,
        "corners": tuple(corners),
        "corner_orientations": tuple(sorted(orientations)),
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _grow_scene(profile, difficulty, rng):
    count_text, density = profile.split("_", 1)
    color_count = int(count_text[1:])
    for _ in range(500):
        height, width = rng.choice(_DIMENSIONS[difficulty])
        foreground_target = _foreground_target(height, width, density)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        colors = rng.sample(_PALETTE, color_count)
        seeds = rng.sample(range(height * width), color_count)
        for color, cell in zip(colors, seeds):
            grid[cell // width][cell % width] = color

        foreground = color_count
        while foreground < foreground_target:
            candidates = []
            for row in range(height):
                for col in range(width):
                    color = grid[row][col]
                    if color == 0:
                        continue
                    for delta_row, delta_col in _ORTHOGONAL_DELTAS:
                        neighbour_row, neighbour_col = row + delta_row, col + delta_col
                        if 0 <= neighbour_row < height and 0 <= neighbour_col < width and grid[neighbour_row][neighbour_col] == 0:
                            candidates.append((color, neighbour_row, neighbour_col))
            if not candidates:
                break
            color, row, col = rng.choice(candidates)
            if grid[row][col] == 0:
                grid[row][col] = color
                foreground += 1

        analysis = _analysis(grid)
        corner_count = len(analysis["facts"]["corners"]) if analysis["facts"] else 0
        difficulty_matches = (
            difficulty not in ("easy", "hard")
            or (difficulty == "easy" and corner_count == 2)
            or (difficulty == "hard" and corner_count >= 3)
        )
        if not analysis["errors"] and analysis["scene_profile"] == profile and difficulty_matches:
            return grid
    raise AssertionError(f"could not construct scene profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_profiles = PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5
    profile = ctx.draw_choice("scene_profile", default_profiles)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _grow_scene(profile, difficulty, ctx.draw_rng("scene"))
