"""Generator for H106 — infer TL→TR transform and apply it to BL.

A central maroon cross divides an odd square into four equal panels.  The
bottom-right panel is blank.  The top-right panel is exactly one canonical
(non-identity) dihedral transform of a deliberately asymmetric top-left
panel.  The same transform applied to the independent bottom-left panel is
the answer.

The canonical Racket rule searches id/cw/180/transpose/lr/ud/transpose/anti
in that order; there is no counter-clockwise branch.  This generator samples
only the six non-identity semantic branches the rule can identify uniquely.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "673e85a3c1cb"
VERSION = "4.0.0"  # exact axes + structural self_check + shortcut-resistant scenes
TASK_ID = "673e85a3c1cb"
RULE_HASH = "22b126827594"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "An odd 7x7, 9x9, or 11x11 grid is split into four equal square panels "
    "by one full central color-9 row and column. TOP-RIGHT is one uniquely "
    "identifiable non-identity transform of a D4-asymmetric TOP-LEFT panel "
    "(clockwise rotation, 180 rotation, transpose, left-right flip, "
    "up-down flip, or anti-transpose). BOTTOM-LEFT is an independent pattern "
    "with the same palette and occupancy; BOTTOM-RIGHT is blank. Output the "
    "same transform applied to BOTTOM-LEFT. Grid size, command, palette size, "
    "occupancy, colors, and both spatial patterns vary independently."
)

INVARIANTS = [
    "exactly one full central color-9 row and column create four equal square panels",
    "top-right has exactly one match among the canonical rule's seven semantic transforms of top-left",
    "top-left is asymmetric under every transform the canonical rule compares",
    "bottom-left is independent of top-left/top-right and changes under the inferred transform",
    "bottom-right is empty and top-left/bottom-left use the same nonzero palette and occupancy count",
]

# All axes below are exact-or-loud.  observe_overrides() recovers every value
# from the returned grid, and generate() rejects unknown or invalid overrides.
AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-weighted",
        "valid": "7|9|11",
    },
    "command": {
        "type": "str",
        "default": "varies",
        "valid": "cw|180|transpose|lr|ud|anti",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-weighted",
        "valid": "1..3",
    },
    "occupancy": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "sparse|balanced|dense",
    },
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)
_COMMANDS = ("cw", "180", "transpose", "lr", "ud", "anti")
_RULE_OPS = ("id",) + _COMMANDS
_OCCUPANCIES = ("sparse", "balanced", "dense")
_GRID_SIZES = (7, 9, 11)


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _T(grid, op):
    """Apply one semantic transform from the canonical rule's search set."""
    n = len(grid)
    if op == "id":
        return [row[:] for row in grid]
    if op == "cw":
        return [[grid[n - 1 - column][row] for column in range(n)] for row in range(n)]
    if op == "180":
        return [
            [grid[n - 1 - row][n - 1 - column] for column in range(n)]
            for row in range(n)
        ]
    if op == "transpose":
        return [[grid[column][row] for column in range(n)] for row in range(n)]
    if op == "lr":
        return [list(reversed(row)) for row in grid]
    if op == "ud":
        return [row[:] for row in reversed(grid)]
    if op == "anti":
        return [
            [grid[n - 1 - column][n - 1 - row] for column in range(n)]
            for row in range(n)
        ]
    raise ValueError(f"unknown transform {op!r}")


def _matching_ops(source, target):
    return [op for op in _RULE_OPS if _T(source, op) == target]


def _all_rule_images_distinct(grid):
    return len({_grid_key(_T(grid, op)) for op in _RULE_OPS}) == len(_RULE_OPS)


def _palette(grid):
    return {value for row in grid for value in row if value not in (0, 9)}


def _nonzero_count(grid):
    return sum(value != 0 for row in grid for value in row)


def _target_nonzero(q, palette_size, occupancy):
    if occupancy == "sparse":
        return max(q, palette_size)
    if occupancy == "balanced":
        return max(palette_size, (q * q + 1) // 2)
    if occupancy == "dense":
        return max(palette_size, q * q - q)
    raise ValueError(f"unknown occupancy {occupancy!r}")


def _sample_pattern(rng, q, colors, nonzero_count):
    """Return a random q×q pattern that uses every requested color."""
    positions = list(range(q * q))
    rng.shuffle(positions)
    chosen = positions[:nonzero_count]
    assignments = list(colors)
    assignments.extend(rng.choice(colors) for _ in range(nonzero_count - len(colors)))
    rng.shuffle(assignments)
    grid = [[0] * q for _ in range(q)]
    for index, color in zip(chosen, assignments):
        row, column = divmod(index, q)
        grid[row][column] = color
    return grid


def _make_top_left(rng, q, colors, nonzero_count):
    for _ in range(512):
        candidate = _sample_pattern(rng, q, colors, nonzero_count)
        if _all_rule_images_distinct(candidate):
            return candidate
    raise RuntimeError("could not sample a transform-identifiable top-left panel")


def _make_bottom_left(rng, q, colors, nonzero_count, command, forbidden):
    forbidden_keys = {_grid_key(grid) for grid in forbidden}
    for _ in range(512):
        candidate = _sample_pattern(rng, q, colors, nonzero_count)
        transformed = _T(candidate, command)
        candidate_key = _grid_key(candidate)
        transformed_key = _grid_key(transformed)
        if candidate_key == transformed_key:
            continue
        if candidate_key in forbidden_keys or transformed_key in forbidden_keys:
            continue
        return candidate
    raise RuntimeError("could not sample an independent transform-sensitive bottom-left panel")


def _band_options(difficulty):
    if difficulty == "easy":
        return {
            "grid_size": (7, 9),
            "palette_size": (1, 2),
            "occupancy": ("sparse", "balanced"),
        }
    if difficulty == "hard":
        return {
            "grid_size": (9, 11),
            "palette_size": (2, 3),
            "occupancy": ("balanced", "dense"),
        }
    return {
        "grid_size": _GRID_SIZES,
        "palette_size": (1, 2, 3),
        "occupancy": _OCCUPANCIES,
    }


def _draw_choice(ctx, label, full_options, default_options):
    options = full_options if ctx.overrides.get(label) is not None else default_options
    return ctx.draw_choice(label, options)


def _grid_shape_error(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "grid must be a non-empty list of rows"
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular and non-empty"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid colors must be integers in 0..9"
    return None


def _analyze_scene(grid):
    """Return structural facts and errors for canonical or generated scenes."""
    result = {"errors": []}
    shape_error = _grid_shape_error(grid)
    if shape_error:
        result["errors"].append(shape_error)
        return result

    height, width = len(grid), len(grid[0])
    result.update({"height": height, "width": width})
    if height != width or height not in _GRID_SIZES:
        result["errors"].append("grid must be a 7x7, 9x9, or 11x11 square")
        return result

    full_rows = [row for row in range(height) if all(value == 9 for value in grid[row])]
    full_columns = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(full_rows) != 1 or len(full_columns) != 1:
        result["errors"].append(
            "scene must contain exactly one full color-9 row and one full color-9 column"
        )
        return result

    divider_row, divider_column = full_rows[0], full_columns[0]
    q = height // 2
    if divider_row != q or divider_column != q:
        result["errors"].append("the color-9 cross must be centered")
        return result
    if any(
        grid[row][column] == 9 and row != q and column != q
        for row in range(height)
        for column in range(width)
    ):
        result["errors"].append("color 9 may occur only on the divider cross")

    top_left = [row[:q] for row in grid[:q]]
    top_right = [row[q + 1 :] for row in grid[:q]]
    bottom_left = [row[:q] for row in grid[q + 1 :]]
    bottom_right = [row[q + 1 :] for row in grid[q + 1 :]]
    result.update(
        {
            "q": q,
            "top_left": top_left,
            "top_right": top_right,
            "bottom_left": bottom_left,
            "bottom_right": bottom_right,
        }
    )

    if any(value != 0 for row in bottom_right for value in row):
        result["errors"].append("bottom-right panel must be entirely zero")

    top_left_palette = _palette(top_left)
    bottom_left_palette = _palette(bottom_left)
    top_left_count = _nonzero_count(top_left)
    bottom_left_count = _nonzero_count(bottom_left)
    result.update(
        {
            "top_left_palette": top_left_palette,
            "bottom_left_palette": bottom_left_palette,
            "top_left_count": top_left_count,
            "bottom_left_count": bottom_left_count,
        }
    )
    if not top_left_palette or not bottom_left_palette:
        result["errors"].append("top-left and bottom-left panels must both contain colored cells")
    if top_left_palette != bottom_left_palette:
        result["errors"].append("top-left and bottom-left panels must use the same nonzero palette")
    if top_left_count != bottom_left_count:
        result["errors"].append("top-left and bottom-left panels must have equal occupancy")
    if not (2 <= top_left_count < q * q) or not (2 <= bottom_left_count < q * q):
        result["errors"].append("source panels must be nonempty, non-solid spatial patterns")

    if not _all_rule_images_distinct(top_left):
        result["errors"].append("top-left panel must be asymmetric under the canonical transform set")

    matches = _matching_ops(top_left, top_right)
    result["matching_ops"] = matches
    if len(matches) != 1:
        result["errors"].append(
            f"top-right must identify exactly one canonical transform, found {matches}"
        )
        return result
    command = matches[0]
    result["command"] = command
    if command == "id":
        result["errors"].append("identity top-left to top-right examples are not teaching instances")

    transformed_bottom_left = _T(bottom_left, command)
    result["expected_output"] = transformed_bottom_left
    if bottom_left in (top_left, top_right):
        result["errors"].append("bottom-left must be spatially independent of the top panels")
    if transformed_bottom_left == bottom_left:
        result["errors"].append("the inferred transform must visibly change bottom-left")
    if transformed_bottom_left in (top_left, top_right):
        result["errors"].append("the answer must not be copyable from either top panel")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-prone teaching scenes."""
    del difficulty, meta
    return list(_analyze_scene(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact AXES value from a valid returned grid."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    palette_size = len(analysis["top_left_palette"])
    occupancy_matches = [
        occupancy
        for occupancy in _OCCUPANCIES
        if analysis["top_left_count"]
        == _target_nonzero(analysis["q"], palette_size, occupancy)
        and analysis["bottom_left_count"]
        == _target_nonzero(analysis["q"], palette_size, occupancy)
    ]
    if len(occupancy_matches) != 1:
        raise ValueError(
            "scene occupancy does not encode exactly one declared occupancy axis: "
            f"{occupancy_matches}"
        )
    return {
        "grid_size": analysis["height"],
        "command": analysis["command"],
        "palette_size": palette_size,
        "occupancy": occupancy_matches[0],
    }


def rule_mirror(grid):
    """Test-only mirror of the canonical rule; Racket remains output authority."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["expected_output"]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None/easy/medium/hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _band_options(difficulty)
    grid_size = _draw_choice(ctx, "grid_size", _GRID_SIZES, defaults["grid_size"])
    command = ctx.draw_choice("command", _COMMANDS)
    palette_size = _draw_choice(
        ctx,
        "palette_size",
        (1, 2, 3),
        defaults["palette_size"],
    )
    occupancy = _draw_choice(
        ctx,
        "occupancy",
        _OCCUPANCIES,
        defaults["occupancy"],
    )

    q = (grid_size - 1) // 2
    colors = tuple(ctx.draw_rng("palette").sample(_COLORS, palette_size))
    nonzero_count = _target_nonzero(q, palette_size, occupancy)
    top_left = _make_top_left(
        ctx.draw_rng("top_left"),
        q,
        colors,
        nonzero_count,
    )
    top_right = _T(top_left, command)
    bottom_left = _make_bottom_left(
        ctx.draw_rng("bottom_left"),
        q,
        colors,
        nonzero_count,
        command,
        (top_left, top_right),
    )

    grid = full_grid(grid_size, grid_size, 0)
    for index in range(grid_size):
        grid[q][index] = 9
        grid[index][q] = 9
    for row in range(q):
        for column in range(q):
            grid[row][column] = top_left[row][column]
            grid[row][q + 1 + column] = top_right[row][column]
            grid[q + 1 + row][column] = bottom_left[row][column]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid
