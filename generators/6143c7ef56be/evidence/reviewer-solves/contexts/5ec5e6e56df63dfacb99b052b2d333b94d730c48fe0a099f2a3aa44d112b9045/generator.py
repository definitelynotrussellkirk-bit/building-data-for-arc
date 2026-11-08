"""Generator for ARC task d89b689b / content hash 6143c7ef56be.

A valid input contains one solid 2x2 cyan block and four distinct singleton
markers, one in each strict quadrant around that block.  The canonical rule
clears the scene and writes the quadrant colors into the corresponding cells
of the former cyan block.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6143c7ef56be"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9c659fa323b2"

SUMMARY = (
    "A 0-background grid contains exactly one solid 2x2 cyan (8) block and "
    "four distinct non-{0,8} singleton markers. Relative to the cyan block's "
    "top-left cell, exactly one marker lies in each strict quadrant: above-"
    "left, above-right, below-left, and below-right. Marker positions vary "
    "within their quadrants and need not be symmetric or equidistant. The "
    "rule returns an otherwise blank grid whose former cyan 2x2 cells contain "
    "the four marker colors in TL/TR/BL/BR order; the original marker cells "
    "and all cyan cells are cleared."
)

INVARIANTS = [
    "rectangular 8..18 by 8..18 grid with background color 0",
    "exactly four cyan(8) cells forming one solid 2x2 block",
    "exactly four singleton non-{0,8} cells with pairwise-distinct colors",
    "exactly one marker occurs in each strict quadrant around the cyan block",
    "output is blank except for the former 2x2 block, colored TL/TR/BL/BR",
]

MARKER_LAYOUTS = ("independent", "row_aligned", "column_aligned", "corners")
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "8..18",
    },
    "block_row": {
        "type": "int",
        "default": "keyed draw with two rows available above and below",
        "valid": "2..h-4",
    },
    "block_col": {
        "type": "int",
        "default": "keyed draw with two columns available left and right",
        "valid": "2..w-4",
    },
    "marker_layout": {
        "type": "str",
        "default": "keyed draw",
        "valid": "independent|row_aligned|column_aligned|corners",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "block_row", "block_col"):
        if name in overrides and (
            not isinstance(overrides[name], int) or isinstance(overrides[name], bool)
        ):
            raise ValueError(f"{name} override must be an integer")
    if "marker_layout" in overrides and not isinstance(overrides["marker_layout"], str):
        raise ValueError("marker_layout override must be a string")


def _layout_name(
    positions: dict[str, tuple[int, int]], height: int, width: int
) -> str:
    if positions == {
        "tl": (0, 0),
        "tr": (0, width - 1),
        "bl": (height - 1, 0),
        "br": (height - 1, width - 1),
    }:
        return "corners"
    if (
        positions["tl"][0] == positions["tr"][0]
        and positions["bl"][0] == positions["br"][0]
    ):
        return "row_aligned"
    if (
        positions["tl"][1] == positions["bl"][1]
        and positions["tr"][1] == positions["br"][1]
    ):
        return "column_aligned"
    return "independent"


def _marker_positions(
    *,
    height: int,
    width: int,
    block_row: int,
    block_col: int,
    layout: str,
    rng,
) -> dict[str, tuple[int, int]]:
    top_rows = list(range(block_row))
    bottom_rows = list(range(block_row + 2, height))
    left_cols = list(range(block_col))
    right_cols = list(range(block_col + 2, width))

    if layout == "corners":
        return {
            "tl": (0, 0),
            "tr": (0, width - 1),
            "bl": (height - 1, 0),
            "br": (height - 1, width - 1),
        }

    if layout == "row_aligned":
        top = rng.choice(top_rows)
        bottom = rng.choice(bottom_rows)
        positions = {
            "tl": (top, rng.choice(left_cols)),
            "tr": (top, rng.choice(right_cols)),
            "bl": (bottom, rng.choice(left_cols)),
            "br": (bottom, rng.choice(right_cols)),
        }
        # Keep the requested observable profile distinct from exact corners.
        if _layout_name(positions, height, width) == "corners":
            positions["tl"] = (top, left_cols[1])
        return positions

    if layout == "column_aligned":
        left = rng.choice(left_cols)
        right = rng.choice(right_cols)
        tl_row = rng.choice(top_rows)
        tr_row = rng.choice([row for row in top_rows if row != tl_row])
        positions = {
            "tl": (tl_row, left),
            "tr": (tr_row, right),
            "bl": (rng.choice(bottom_rows), left),
            "br": (rng.choice(bottom_rows), right),
        }
        return positions

    # General teaching distribution: vary all four locations independently and
    # reject the three named shortcut profiles.  A deterministic fallback makes
    # the postcondition total even if an unlucky keyed RNG repeats profiles.
    domains = {
        "tl": (top_rows, left_cols),
        "tr": (top_rows, right_cols),
        "bl": (bottom_rows, left_cols),
        "br": (bottom_rows, right_cols),
    }
    for _ in range(64):
        positions = {
            name: (rng.choice(rows), rng.choice(cols))
            for name, (rows, cols) in domains.items()
        }
        if _layout_name(positions, height, width) == "independent":
            return positions
    return {
        "tl": (top_rows[0], left_cols[0]),
        "tr": (top_rows[-1], right_cols[0]),
        "bl": (bottom_rows[0], left_cols[-1]),
        "br": (bottom_rows[-1], right_cols[-1]),
    }


def _analyze(grid) -> dict[str, Any]:
    result: dict[str, Any] = {"errors": []}
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid:
        errors.append("grid is empty or is not a list")
        return result
    if not all(isinstance(row, list) and row for row in grid):
        errors.append("every row must be a non-empty list")
        return result

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid is ragged")
        return result
    if not (8 <= height <= 18 and 8 <= width <= 18):
        errors.append(f"grid dimensions must be within 8..18, got {height}x{width}")
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(f"grid contains invalid ARC color {value!r}")
                return result

    cyan = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    }
    if len(cyan) != 4:
        errors.append(f"expected exactly four cyan cells, got {len(cyan)}")
        return result
    block_row = min(row for row, _ in cyan)
    block_col = min(col for _, col in cyan)
    expected_cyan = {
        (block_row, block_col),
        (block_row, block_col + 1),
        (block_row + 1, block_col),
        (block_row + 1, block_col + 1),
    }
    if cyan != expected_cyan:
        errors.append("the four cyan cells do not form one solid 2x2 block")
        return result
    if not (2 <= block_row <= height - 4 and 2 <= block_col <= width - 4):
        errors.append("cyan block must leave at least two rows/columns in every direction")

    marker_cells = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    if len(marker_cells) != 4:
        errors.append(f"expected exactly four marker cells, got {len(marker_cells)}")
        return result
    colors = [color for _, _, color in marker_cells]
    if len(set(colors)) != 4:
        errors.append("marker colors must be pairwise distinct")

    positions: dict[str, tuple[int, int]] = {}
    quadrant_colors: dict[str, int] = {}
    for row, col, color in marker_cells:
        vertical = "t" if row < block_row else "b" if row > block_row + 1 else None
        horizontal = "l" if col < block_col else "r" if col > block_col + 1 else None
        if vertical is None or horizontal is None:
            errors.append(
                f"marker at ({row}, {col}) is not in a strict block-relative quadrant"
            )
            continue
        quadrant = vertical + horizontal
        if quadrant in positions:
            errors.append(f"more than one marker lies in quadrant {quadrant}")
            continue
        positions[quadrant] = (row, col)
        quadrant_colors[quadrant] = color
    missing = [name for name in ("tl", "tr", "bl", "br") if name not in positions]
    if missing:
        errors.append(f"missing marker quadrant(s): {', '.join(missing)}")

    result.update(
        {
            "height": height,
            "width": width,
            "block_row": block_row,
            "block_col": block_col,
            "marker_positions": positions,
            "quadrant_colors": quadrant_colors,
        }
    )
    if not errors:
        result["marker_layout"] = _layout_name(positions, height, width)
    return result


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
    # A placement override by itself is a complete request: expand the
    # dependent canvas as needed rather than making its legality depend on an
    # unrelated random dimension draw. Explicitly incompatible paired
    # overrides still reject through the same GenCtx validity gate.
    min_height = max(8, int(overrides.get("block_row", 4)) + 4)
    min_width = max(8, int(overrides.get("block_col", 4)) + 4)
    height = ctx.draw_int_diff("grid_h", min_height, 18)
    width = ctx.draw_int_diff("grid_w", min_width, 18)
    block_row = ctx.draw_int("block_row", 2, height - 4)
    block_col = ctx.draw_int("block_col", 2, width - 4)
    layout = ctx.draw_choice("marker_layout", MARKER_LAYOUTS)
    colors = ctx.draw_distinct_colors("marker_colors", n=4, exclude={0, 8})
    positions = _marker_positions(
        height=height,
        width=width,
        block_row=block_row,
        block_col=block_col,
        layout=layout,
        rng=ctx.draw_rng("marker_positions"),
    )

    grid = full_grid(height, width, 0)
    for row in (block_row, block_row + 1):
        for col in (block_col, block_col + 1):
            grid[row][col] = 8
    for name, color in zip(("tl", "tr", "bl", "br"), colors):
        row, col = positions[name]
        grid[row][col] = color

    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "block_row": block_row,
        "block_col": block_col,
        "marker_layout": layout,
    }
    if observed != expected:
        raise AssertionError(f"generated scene drifted: expected {expected}, got {observed}")
    return [list(row) for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or semantically ambiguous teaching scenes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = (meta or {}).get("overrides") or {}
    if not errors:
        observed = observe_overrides(grid)
        for axis in AXES:
            if axis in requested and observed[axis] != requested[axis]:
                errors.append(
                    f"override {axis}={requested[axis]!r} observed as {observed[axis]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "block_row": analysis["block_row"],
        "block_col": analysis["block_col"],
        "marker_layout": analysis["marker_layout"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Testing mirror of the canonical Racket rule; never output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    row = analysis["block_row"]
    col = analysis["block_col"]
    colors = analysis["quadrant_colors"]
    output[row][col] = colors["tl"]
    output[row][col + 1] = colors["tr"]
    output[row + 1][col] = colors["bl"]
    output[row + 1][col + 1] = colors["br"]
    return output
