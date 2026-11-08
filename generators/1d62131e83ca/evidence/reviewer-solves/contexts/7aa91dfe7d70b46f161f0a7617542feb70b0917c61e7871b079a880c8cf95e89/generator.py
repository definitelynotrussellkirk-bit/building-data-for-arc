"""Generator for ARC task 5c0a986e / task_id 1d62131e83ca.

The input contains one solid blue (1) 2x2 block and one solid red (2) 2x2
block.  The oracle extends a one-cell diagonal ray up-left from the blue
block's top-left corner and down-right from the red block's bottom-right
corner.  Both rays continue to the grid edge.

Ordinary draws retain a 35% linked prior over the four official geometry
profiles.  The remaining draws vary canvas size, all four relative block
placements, equal and unequal ray lengths, and collision-free translations.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid


GENERATOR_ID = "1d62131e83ca"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "7a695100f4e0"

SUMMARY = (
    "A 0-background grid contains one solid blue 2x2 block and one solid red "
    "2x2 block. Paint a blue diagonal ray up-left from the blue block's "
    "top-left corner and a red diagonal ray down-right from the red block's "
    "bottom-right corner, continuing each ray to the edge."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are blue 1 and red 2",
    "there is exactly one solid 2x2 block of each foreground color",
    "both diagonal rays are nonempty and remain visible",
    "the two rays do not cross either source block or one another",
    "all four strict relative block placements are lawful teaching cases",
]

RELATIVE_POSITIONS = ("NW", "NE", "SW", "SE")
TRAIL_BALANCES = ("equal", "blue_longer", "red_longer")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "35% linked 10x10 canonical prior; otherwise difficulty-aware 6..18",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "35% linked 10x10 canonical prior; otherwise difficulty-aware 6..18",
        "valid": "6..18",
    },
    "relative_position": {
        "type": "str",
        "default": "rng over all four strict blue-relative-to-red quadrants",
        "valid": "NW|NE|SW|SE",
    },
    "trail_balance": {
        "type": "str",
        "default": "difficulty-weighted equal|blue_longer|red_longer",
        "valid": "equal|blue_longer|red_longer",
    },
}

# Executably extracted from all three train inputs and the held-out test input.
# Coordinates and literal translations are nuisance factors; the linked
# (relative placement, blue ray length, red ray length) profile is retained.
_CANONICAL_PROFILES = (
    ("SE", 6, 6),
    ("NW", 2, 2),
    ("SW", 3, 3),
    ("NE", 3, 3),
)
_CANONICAL_PROFILE_SET = set(_CANONICAL_PROFILES)
_CANONICAL_PRIOR_RATE = 0.35

_DEFAULT_DIMENSIONS = {
    "easy": ((6, 10), (6, 10)),
    "medium": ((9, 14), (9, 14)),
    "hard": ((13, 18), (13, 18)),
}
_BALANCE_WEIGHTS = {
    "easy": {"equal": 4, "blue_longer": 1, "red_longer": 1},
    "medium": {"equal": 2, "blue_longer": 2, "red_longer": 2},
    "hard": {"equal": 1, "blue_longer": 3, "red_longer": 3},
}


def _band(difficulty: Any) -> str:
    return difficulty if difficulty in _DEFAULT_DIMENSIONS else "medium"


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], 0, 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC color integers 0 through 9"], len(grid), width
    return [], len(grid), width


def _solid_2x2_origin(grid: Any, color: int) -> tuple[int, int] | None:
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    if len(cells) != 4:
        return None
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    expected = {
        (row0, col0),
        (row0 + 1, col0),
        (row0, col0 + 1),
        (row0 + 1, col0 + 1),
    }
    return (row0, col0) if cells == expected else None


def _blue_ray(origin: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    row, col = origin[0] - 1, origin[1] - 1
    cells = []
    while row >= 0 and col >= 0:
        cells.append((row, col))
        row -= 1
        col -= 1
    return tuple(cells)


def _red_ray(
    origin: tuple[int, int], height: int, width: int
) -> tuple[tuple[int, int], ...]:
    row, col = origin[0] + 2, origin[1] + 2
    cells = []
    while row < height and col < width:
        cells.append((row, col))
        row += 1
        col += 1
    return tuple(cells)


def _relative_position(
    blue: tuple[int, int], red: tuple[int, int]
) -> str | None:
    if blue[0] == red[0] or blue[1] == red[1]:
        return None
    vertical = "N" if blue[0] < red[0] else "S"
    horizontal = "W" if blue[1] < red[1] else "E"
    return vertical + horizontal


def _trail_balance(blue_length: int, red_length: int) -> str:
    if blue_length == red_length:
        return "equal"
    return "blue_longer" if blue_length > red_length else "red_longer"


def _analysis(grid: Any) -> dict[str, Any]:
    errors, height, width = _validate_grid(grid)
    facts: dict[str, Any] = {"height": height, "width": width}
    if errors:
        return {"errors": errors, "facts": facts}

    if not 6 <= height <= 18 or not 6 <= width <= 18:
        errors.append(f"teaching grid must be 6..18 by 6..18, got {height}x{width}")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2}:
        errors.append(f"unexpected colors outside {{0,1,2}}: {sorted(palette - {0, 1, 2})}")

    blue = _solid_2x2_origin(grid, 1)
    red = _solid_2x2_origin(grid, 2)
    if blue is None:
        errors.append("color 1 must form exactly one solid 2x2 block")
    if red is None:
        errors.append("color 2 must form exactly one solid 2x2 block")
    if blue is None or red is None:
        return {"errors": errors, "facts": facts}

    relative = _relative_position(blue, red)
    if relative is None:
        errors.append("block origins must differ in both row and column")

    blue_block = {
        (blue[0], blue[1]),
        (blue[0] + 1, blue[1]),
        (blue[0], blue[1] + 1),
        (blue[0] + 1, blue[1] + 1),
    }
    red_block = {
        (red[0], red[1]),
        (red[0] + 1, red[1]),
        (red[0], red[1] + 1),
        (red[0] + 1, red[1] + 1),
    }
    if blue_block & red_block:
        errors.append("the two source blocks overlap")

    blue_ray = set(_blue_ray(blue))
    red_ray = set(_red_ray(red, height, width))
    if not blue_ray:
        errors.append("blue block must leave a nonempty up-left ray")
    if not red_ray:
        errors.append("red block must leave a nonempty down-right ray")
    if blue_ray & red_block:
        errors.append("blue ray would pass through the red source block")
    if red_ray & blue_block:
        errors.append("red ray would pass through the blue source block")
    if blue_ray & red_ray:
        errors.append("blue and red rays would collide")

    blue_length = len(blue_ray)
    red_length = len(red_ray)
    facts.update(
        {
            "blue_origin": blue,
            "red_origin": red,
            "relative_position": relative,
            "blue_trail_length": blue_length,
            "red_trail_length": red_length,
            "trail_balance": _trail_balance(blue_length, red_length),
            "palette": tuple(sorted(palette)),
        }
    )
    return {"errors": errors, "facts": facts}


def profile_signature(grid: Any):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        facts["relative_position"],
        facts["blue_trail_length"],
        facts["red_trail_length"],
    )


def canonical_profile_signature(grid: Any):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    linked = (
        facts["relative_position"],
        facts["blue_trail_length"],
        facts["red_trail_length"],
    )
    if facts["height"] == 10 and facts["width"] == 10 and linked in _CANONICAL_PROFILE_SET:
        return linked
    return None


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid lesson: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "relative_position": facts["relative_position"],
        "trail_balance": facts["trail_balance"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar without mutating ``grid``."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    overrides = _meta_overrides(meta)
    for axis in ("relative_position", "trail_balance"):
        requested = overrides.get(axis)
        if requested is not None and facts[axis] != requested:
            errors.append(f"{axis} requested {requested!r}, realized {facts[axis]!r}")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python test mirror; canonical Racket remains the output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid lesson: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = [list(row) for row in grid]
    for row, col in _blue_ray(facts["blue_origin"]):
        output[row][col] = 1
    for row, col in _red_ray(facts["red_origin"], facts["height"], facts["width"]):
        output[row][col] = 2
    return output


def _block_cells(origin: tuple[int, int]) -> frozenset[tuple[int, int]]:
    row, col = origin
    return frozenset(
        {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
    )


@lru_cache(maxsize=None)
def _candidate_origins(
    height: int,
    width: int,
    relative: str,
    balance: str,
    target_blue_length: int | None = None,
    target_red_length: int | None = None,
) -> tuple[tuple[int, int, int, int, int, int], ...]:
    candidates = []
    for blue_row in range(1, height - 1):
        for blue_col in range(1, width - 1):
            blue = (blue_row, blue_col)
            blue_block = _block_cells(blue)
            blue_ray = frozenset(_blue_ray(blue))
            blue_length = len(blue_ray)
            if target_blue_length is not None and blue_length != target_blue_length:
                continue
            for red_row in range(0, height - 2):
                for red_col in range(0, width - 2):
                    red = (red_row, red_col)
                    if _relative_position(blue, red) != relative:
                        continue
                    red_block = _block_cells(red)
                    if blue_block & red_block:
                        continue
                    red_ray = frozenset(_red_ray(red, height, width))
                    red_length = len(red_ray)
                    if target_red_length is not None and red_length != target_red_length:
                        continue
                    if _trail_balance(blue_length, red_length) != balance:
                        continue
                    if blue_ray & red_block or red_ray & blue_block or blue_ray & red_ray:
                        continue
                    candidates.append(
                        (
                            blue_row,
                            blue_col,
                            red_row,
                            red_col,
                            blue_length,
                            red_length,
                        )
                    )
    return tuple(candidates)


def _draw_global_or_default(ctx, name: str, default: tuple[int, int]) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, 6, 18)
    return ctx.draw_int(name, *default)


def _choose_semantic_pair(ctx, height: int, width: int, band: str):
    requested_relative = ctx.overrides.get("relative_position")
    requested_balance = ctx.overrides.get("trail_balance")
    if requested_relative is not None and requested_relative not in RELATIVE_POSITIONS:
        raise ValueError(f"invalid relative_position override: {requested_relative!r}")
    if requested_balance is not None and requested_balance not in TRAIL_BALANCES:
        raise ValueError(f"invalid trail_balance override: {requested_balance!r}")

    feasible = []
    for relative in RELATIVE_POSITIONS:
        if requested_relative is not None and relative != requested_relative:
            continue
        for balance in TRAIL_BALANCES:
            if requested_balance is not None and balance != requested_balance:
                continue
            if _candidate_origins(height, width, relative, balance):
                feasible.append((relative, balance))
    if not feasible:
        raise ValueError(
            "incompatible dimensions/relative_position/trail_balance combination"
        )

    weighted = []
    for relative, balance in feasible:
        weighted.extend([(relative, balance)] * _BALANCE_WEIGHTS[band][balance])
    selected_relative, selected_balance = ctx.draw_rng("semantic_pair").choice(weighted)
    # Record both exact semantic axes through GenCtx, including partially
    # overridden paths.  The singleton domains are the already-filtered
    # feasible values, so no recorded value can be replaced later.
    selected_relative = ctx.draw_choice("relative_position", [selected_relative])
    selected_balance = ctx.draw_choice("trail_balance", [selected_balance])
    return selected_relative, selected_balance


def _select_candidate(ctx, candidates, band: str):
    ordered = sorted(candidates, key=lambda item: (item[4] + item[5], item))
    if band == "easy":
        pool = ordered[: max(1, (len(ordered) + 2) // 3)]
    elif band == "hard":
        pool = ordered[-max(1, (len(ordered) + 2) // 3) :]
    else:
        pool = ordered
    return ctx.draw_rng("placement").choice(pool)


def _paint_scene(height: int, width: int, candidate) -> list[list[int]]:
    blue_row, blue_col, red_row, red_col, _, _ = candidate
    grid = full_grid(height, width, 0)
    draw_rect(grid, blue_row, blue_col, 2, 2, 1)
    draw_rect(grid, red_row, red_col, 2, 2, 2)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # The prior is default-only: every explicit semantic control bypasses it.
    use_canonical_prior = (
        not overrides
        and ctx.draw_rng(f"canonical_prior|{band}").random() < _CANONICAL_PRIOR_RATE
    )
    if use_canonical_prior:
        relative, blue_length, red_length = ctx.draw_choice(
            "canonical_profile", _CANONICAL_PROFILES
        )
        height = ctx.draw_int("grid_h", 10, 10)
        width = ctx.draw_int("grid_w", 10, 10)
        relative = ctx.draw_choice("relative_position", [relative])
        balance = ctx.draw_choice("trail_balance", ["equal"])
        candidates = _candidate_origins(
            height,
            width,
            relative,
            balance,
            blue_length,
            red_length,
        )
    else:
        height_bounds, width_bounds = _DEFAULT_DIMENSIONS[band]
        height = _draw_global_or_default(ctx, "grid_h", height_bounds)
        width = _draw_global_or_default(ctx, "grid_w", width_bounds)
        relative, balance = _choose_semantic_pair(ctx, height, width, band)
        candidates = _candidate_origins(height, width, relative, balance)

    if not candidates:
        raise ValueError("no collision-free placement satisfies the requested lesson")
    candidate = _select_candidate(ctx, candidates, band)
    grid = _paint_scene(height, width, candidate)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise AssertionError("constructed invalid lesson: " + "; ".join(errors))
    return grid
