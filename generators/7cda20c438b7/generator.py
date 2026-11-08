"""Generator for arc_puzzle_bank_third_21_bundle:easy_16_fill_x_centers.

Rule: every black cell with four green diagonal neighbors becomes yellow.
Ordinary lessons deliberately include overlapping X motifs with shared arms so
an "isolated X only" shortcut cannot fit the generated curriculum.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7cda20c438b7"
VERSION = "2.2.0"
TASK_ID = "7cda20c438b7"
RULE_HASH = "ac623b9aa2f6"
SUMMARY = (
    "0-background grid with two or three color-3 diagonal X motifs. Their black "
    "centers become color 4. Ordinary scenes use a horizontal or vertical chain "
    "whose neighboring motifs share green arm cells, so the local rule must work "
    "for overlapping as well as isolated Xs."
)

INVARIANTS = [
    "background is 0",
    "each marked center is black with four color-3 diagonal neighbors",
    "ordinary scenes contain two or three valid centers",
    "at least one pair of generated X motifs shares arm cells",
]

# Remove the old palette/texture declarations: they were ignored, and each listed
# degenerate produced an identity or self-invalid lesson. These are the controls
# the generator can actually honor and expose from its returned grid.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 7..10", "valid": "7..10"},
    "centers": {"type": "int", "default": "difficulty-aware rng 2..3", "valid": "2..3"},
}


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unsupported/unknown override(s): " + ", ".join(sorted(unknown)))


def _draw_axis(ctx, label, global_low, global_high, default_low, default_high):
    """Honor the full declared domain even when a difficulty narrows defaults."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, global_low, global_high)
    return ctx.draw_int(label, default_low, default_high)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the local canonical predicate without narrowing it to one sampler."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integer colors 0..9"]
    if not any(value == 3 for row in grid for value in row):
        return ["expected >=1 color-3 (green) X-arm cell; found none"]
    if not _x_centers(grid):
        return ["expected >=1 valid green-diagonal X center; found none"]
    return []


def _x_centers(grid):
    """All black cells whose four diagonal neighbors are green (3)."""
    height, width = len(grid), len(grid[0])
    result = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if grid[r][c] == 0 and all(
                grid[r + dr][c + dc] == 3
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
            ):
                result.append((r, c))
    return result


def observe_overrides(grid):
    """Recover every declared exact axis from a generated input."""
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "centers": len(_x_centers(grid))}


def _chain_centers(rng, height, width, count):
    """Construct a horizontal or vertical spacing-2 chain with shared arms."""
    extent = 2 * (count - 1)
    if rng.choice(("horizontal", "vertical")) == "horizontal":
        row = rng.randint(1, height - 2)
        first_column = rng.randint(1, width - 2 - extent)
        return [(row, first_column + 2 * index) for index in range(count)]
    first_row = rng.randint(1, height - 2 - extent)
    column = rng.randint(1, width - 2)
    return [(first_row + 2 * index, column) for index in range(count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        height = _draw_axis(ctx, "grid_h", 7, 9, 7, 8)
        width = _draw_axis(ctx, "grid_w", 7, 10, 7, 8)
        target = _draw_axis(ctx, "centers", 2, 3, 2, 2)
    elif difficulty == "hard":
        height = _draw_axis(ctx, "grid_h", 7, 9, 8, 9)
        width = _draw_axis(ctx, "grid_w", 7, 10, 9, 10)
        target = _draw_axis(ctx, "centers", 2, 3, 3, 3)
    else:
        height = _draw_axis(ctx, "grid_h", 7, 9, 7, 9)
        width = _draw_axis(ctx, "grid_w", 7, 10, 7, 10)
        target = _draw_axis(ctx, "centers", 2, 3, 2, 3)

    rng = ctx.draw_rng("layout")
    centers = _chain_centers(rng, height, width, target)
    grid = full_grid(height, width, 0)
    for r, c in centers:
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            grid[r + dr][c + dc] = 3

    realized = _x_centers(grid)
    if sorted(realized) != sorted(centers):
        raise ValueError(f"constructed {len(realized)} X centers; expected {target}")
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid X lesson: " + "; ".join(errors))
    return grid
