"""Semantic generator for ARC task 13d89a533e59.

The input contains one to three isolated 2x2 color-2 blocks.  Each block has
four distinct diagonal marker colors.  The authoritative rule rotates the
marker *values* one corner forward around every block (old TL -> new TR ->
new BR -> new BL -> new TL), then extends each rotated value outward along
that corner's diagonal through input-zero cells.

Extension normally stops at the edge or at any nonzero input cell.  The
canonical program also has one narrow near-block stop: if the candidate zero
cell lies horizontally beside a color-2 cell, exactly one further diagonal
zero remains, and a second further zero does not, the candidate is left zero
and that ray terminates.  The four-sample curriculum cycles through ordinary
edge extension, direct red-block stopping, an open pass beside a red block,
and this special blocked-skimmer case so the exception is taught rather than
hidden.
"""
from __future__ import annotations

import copy
import itertools
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "13d89a533e59"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Re-pinned after synchronizing the selected canonical Racket source.  The
# temporary placeholder is replaced by the task-local source-sync step.
RULE_HASH = "26b1f77320c5"

SUMMARY = (
    "Find every isolated 2x2 color-2 block and its four distinct diagonal "
    "markers. Rotate the marker values one corner forward around the block "
    "(TL->TR->BR->BL->TL), then extend each new corner value outward along "
    "its diagonal through cells that were 0 in the input. Stop at the edge "
    "or any nonzero input cell. A canonical near-block exception suppresses "
    "a candidate zero beside a color-2 cell when exactly one further "
    "diagonal zero remains before the following cell/edge; that ray stops "
    "without painting the candidate."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INTERACTION_MODES = (
    "edge",
    "red_stop",
    "open_skimmer",
    "blocked_skimmer",
)
MARKER_PALETTES = ("canonical", "alternate")
SCHEDULE_PROFILES = INTERACTION_MODES
_CANONICAL_MARKERS = (3, 6, 7, 8)
_ALTERNATE_MARKERS = (1, 4, 5, 9)
_PALETTE_VALUES = {
    "canonical": _CANONICAL_MARKERS,
    "alternate": _ALTERNATE_MARKERS,
}

INVARIANTS = [
    "0 is background and 2 is reserved for one to three isolated solid 2x2 blocks",
    "every block has exactly four in-bounds diagonal marker cells",
    "the four marker values around each block are nonzero, non-2, and pairwise distinct",
    "all nonzero input cells are block cells or diagonal markers; no stray foreground exists",
    "ordinary generated inputs use exactly four global marker colors and visibly trigger extension",
    "every four consecutive ordinary samples cover edge, red-stop, open-skimmer, and blocked-skimmer behavior",
]

# Public controls are deliberately limited to properties that are exact,
# consumed through GenCtx, and recoverable from the returned input itself.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot difficulty-aware schedule with canonical anchors",
        "valid": "8..15",
        "doc": "exact returned input height",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot difficulty-aware schedule with canonical anchors",
        "valid": "8..15",
        "doc": "exact returned input width",
    },
    "n_blocks": {
        "type": "int",
        "default": "difficulty/profile-aware 1..3",
        "valid": "1..3",
        "doc": "exact number of isolated 2x2 color-2 blocks",
    },
    "marker_palette": {
        "type": "str",
        "default": "scheduled canonical/alternate four-color marker palette",
        "valid": "|".join(MARKER_PALETTES),
        "doc": "canonical={3,6,7,8}; alternate={1,4,5,9}",
    },
    "interaction_mode": {
        "type": "str",
        "default": "four-slot semantic schedule",
        "valid": "|".join(INTERACTION_MODES),
        "doc": "observable ray interaction class, with blocked > red > open > edge precedence",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# With a single red block there is nothing for a ray to stop on or skim past.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_blocks": 1, "interaction_mode": mode}
    for mode in INTERACTION_MODES
    if mode != "edge"
]

# Geometry search results are deterministic and purely derived from dimensions,
# block count, and semantic mode.  The GenCtx RNG only chooses among the lawful
# cached layouts, so no process-global RNG state participates in generation.
_LAYOUT_CACHE: dict[
    tuple[int, int, int, str],
    tuple[tuple[tuple[int, int], ...], ...],
] = {}


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the cyclic semantic profile used by materialized lessons."""
    del seed, difficulty
    return INTERACTION_MODES[int(sample_index) % len(INTERACTION_MODES)]


def _incompatible(message: str, *axes: str) -> ValueError:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    return exc


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _normalize_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    for label in ("grid_h", "grid_w", "n_blocks"):
        if label in overrides and overrides[label] is not None:
            value = overrides[label]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{label} must be an integer")
    for label in ("marker_palette", "interaction_mode"):
        if label in overrides and overrides[label] is not None:
            if not isinstance(overrides[label], str):
                raise ValueError(f"{label} must be a string")

    if (
        overrides.get("n_blocks") == 1
        and overrides.get("interaction_mode") in INTERACTION_MODES[1:]
    ):
        raise _incompatible(
            "non-edge interaction modes require at least two blocks",
            "n_blocks",
            "interaction_mode",
        )
    return band


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(
    ctx, label: str, options: tuple[str, ...], scheduled: str
) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(
    profile: str, sample_index: int, band: str, overrides: dict[str, Any]
) -> dict[str, int | str]:
    # Slot 0 is an exact canonical profile in every band: canonical task
    # profiles are 8x8, 9x9, and 12x12 with six total colors.
    if profile == "edge":
        anchor = {
            "easy": (8, 8, 1),
            "medium": (9, 9, 1),
            "hard": (12, 12, 3),
        }[band]
        h, w, n_blocks = anchor
        palette = "canonical"
    else:
        lo, hi = {
            "easy": (8, 10),
            "medium": (9, 12),
            "hard": (11, 15),
        }[band]
        span = hi - lo + 1
        phase = int(sample_index) // len(INTERACTION_MODES)
        profile_index = INTERACTION_MODES.index(profile)
        h = lo + ((phase + profile_index) % span)
        w = lo + ((2 * phase + profile_index + 1) % span)
        n_blocks = 2 if band == "easy" else 2 + ((phase + profile_index) % 2)
        palette = "alternate" if profile == "open_skimmer" else "canonical"

    # Compatibility adaptation is allowed only for NON-overridden axes.  This
    # makes single-axis override probes constructive instead of turning a
    # lawful request into an accidental collision with the ordinary schedule.
    requested_mode = overrides.get("interaction_mode")
    requested_blocks = overrides.get("n_blocks")
    if requested_mode in INTERACTION_MODES[1:] and requested_blocks is None:
        n_blocks = max(2, n_blocks)
    if requested_blocks == 1 and requested_mode is None:
        profile = "edge"
    return {
        "grid_h": h,
        "grid_w": w,
        "n_blocks": n_blocks,
        "marker_palette": palette,
        "interaction_mode": profile,
    }


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None, ["grid rows must be nonempty sequences"]
    width = len(first)
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]

    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        out_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                out_row.append(0)
            else:
                out_row.append(value)
        converted.append(out_row)
    return (None, errors) if errors else (converted, [])


def _find_blocks(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
        if (
            grid[row][col] == 2
            and grid[row][col + 1] == 2
            and grid[row + 1][col] == 2
            and grid[row + 1][col + 1] == 2
        )
    ]


def _block_cells(row: int, col: int) -> tuple[tuple[int, int], ...]:
    return (
        (row, col),
        (row, col + 1),
        (row + 1, col),
        (row + 1, col + 1),
    )


def _corner_cells(row: int, col: int) -> tuple[tuple[int, int], ...]:
    # TL, TR, BL, BR
    return (
        (row - 1, col - 1),
        (row - 1, col + 2),
        (row + 2, col - 1),
        (row + 2, col + 2),
    )


def _ray_specs(row: int, col: int) -> tuple[tuple[int, int, int, int], ...]:
    # Starts are TL, TR, BL, BR markers; directions are outward diagonals.
    return (
        (row - 1, col - 1, -1, -1),
        (row - 1, col + 2, -1, 1),
        (row + 2, col - 1, 1, -1),
        (row + 2, col + 2, 1, 1),
    )


def _ray_statistics(
    grid: list[list[int]], blocks: Iterable[tuple[int, int]] | None = None
) -> dict[str, int]:
    height, width = len(grid), len(grid[0])
    stats = {
        "edge_stops": 0,
        "red_stops": 0,
        "marker_stops": 0,
        "blocked_skimmers": 0,
        "open_skimmers": 0,
        "painted_extension_cells": 0,
    }
    for row, col in (list(blocks) if blocks is not None else _find_blocks(grid)):
        for start_row, start_col, drow, dcol in _ray_specs(row, col):
            current_row, current_col = start_row, start_col
            while True:
                next_row = current_row + drow
                next_col = current_col + dcol
                if not (0 <= next_row < height and 0 <= next_col < width):
                    stats["edge_stops"] += 1
                    break
                value = grid[next_row][next_col]
                if value != 0:
                    stats["red_stops" if value == 2 else "marker_stops"] += 1
                    break

                opposite_col = next_col - dcol
                opposite_is_2 = (
                    0 <= opposite_col < width
                    and grid[next_row][opposite_col] == 2
                )
                next1_row, next1_col = next_row + drow, next_col + dcol
                next2_row, next2_col = next_row + 2 * drow, next_col + 2 * dcol
                rem1 = (
                    0 <= next1_row < height
                    and 0 <= next1_col < width
                    and grid[next1_row][next1_col] == 0
                )
                rem2 = (
                    rem1
                    and 0 <= next2_row < height
                    and 0 <= next2_col < width
                    and grid[next2_row][next2_col] == 0
                )
                blocked = opposite_is_2 and rem1 and not rem2
                if blocked:
                    stats["blocked_skimmers"] += 1
                    break
                if opposite_is_2:
                    stats["open_skimmers"] += 1
                stats["painted_extension_cells"] += 1
                current_row, current_col = next_row, next_col
    return stats


def _interaction_from_stats(stats: dict[str, int]) -> str | None:
    if stats["marker_stops"]:
        return None
    if stats["blocked_skimmers"]:
        return "blocked_skimmer"
    if stats["red_stops"]:
        return "red_stop"
    if stats["open_skimmers"]:
        return "open_skimmer"
    return "edge"


def _palette_name(colors: set[int]) -> str | None:
    for name, values in _PALETTE_VALUES.items():
        if colors == set(values):
            return name
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if converted is None:
        return result

    height, width = len(converted), len(converted[0])
    blocks = _find_blocks(converted)
    if not blocks:
        errors.append("no solid 2x2 color-2 block found")
    if len(blocks) > 3:
        errors.append(f"expected at most 3 color-2 blocks, found {len(blocks)}")

    block_role_count: dict[tuple[int, int], int] = {}
    marker_role_count: dict[tuple[int, int], int] = {}
    marker_values: list[int] = []
    marker_values_by_block: list[tuple[int, int, int, int]] = []

    for row, col in blocks:
        for cell in _block_cells(row, col):
            block_role_count[cell] = block_role_count.get(cell, 0) + 1
        corners = _corner_cells(row, col)
        if any(
            not (0 <= corner_row < height and 0 <= corner_col < width)
            for corner_row, corner_col in corners
        ):
            errors.append(f"block {(row, col)} lacks four in-bounds diagonal markers")
            continue
        values = tuple(converted[r][c] for r, c in corners)
        marker_values_by_block.append(values)
        if any(value in (0, 2) for value in values):
            errors.append(
                f"block {(row, col)} markers must all be nonzero and non-2"
            )
        if len(set(values)) != 4:
            errors.append(f"block {(row, col)} markers must be pairwise distinct")
        for cell, value in zip(corners, values):
            marker_role_count[cell] = marker_role_count.get(cell, 0) + 1
            marker_values.append(value)

    if any(count != 1 for count in block_role_count.values()):
        errors.append("color-2 blocks overlap or form a larger ambiguous red region")
    if any(count != 1 for count in marker_role_count.values()):
        errors.append("diagonal marker roles overlap between blocks")
    if set(block_role_count) & set(marker_role_count):
        errors.append("a cell cannot be both a red-block cell and a marker cell")

    actual_twos = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if converted[row][col] == 2
    }
    if actual_twos != set(block_role_count):
        errors.append("every color-2 cell must belong to exactly one isolated 2x2 block")

    expected_foreground = set(block_role_count) | set(marker_role_count)
    actual_foreground = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if converted[row][col] != 0
    }
    if actual_foreground != expected_foreground:
        errors.append("all nonzero cells must be red-block cells or diagonal markers")

    marker_colors = set(marker_values)
    if blocks and len(marker_colors) != 4:
        errors.append(
            f"expected exactly 4 global marker colors, observed {len(marker_colors)}"
        )

    stats = _ray_statistics(converted, blocks) if blocks else {
        "edge_stops": 0,
        "red_stops": 0,
        "marker_stops": 0,
        "blocked_skimmers": 0,
        "open_skimmers": 0,
        "painted_extension_cells": 0,
    }
    interaction = _interaction_from_stats(stats)
    facts = {
        "grid_h": height,
        "grid_w": width,
        "n_blocks": len(blocks),
        "blocks": tuple(blocks),
        "marker_colors": tuple(sorted(marker_colors)),
        "marker_palette": _palette_name(marker_colors),
        "interaction_mode": interaction,
        "ray_stats": stats,
        "marker_values_by_block": tuple(marker_values_by_block),
    }
    result["errors"] = list(errors)
    result["grid"] = converted
    result["facts"] = facts
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar, not just generated scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = sorted(set(overrides) - set(AXES))
        if unknown:
            errors.append(f"unknown override(s): {unknown}")
        if not errors:
            facts = analysis["facts"]
            for name, expected in overrides.items():
                if name in AXES and facts.get(name) != expected:
                    errors.append(
                        f"requested {name}={expected!r}, observed {facts.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Generated/canonical teaching manifold used by strict semantic gates."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    height, width = facts["grid_h"], facts["grid_w"]
    if not (8 <= height <= 15 and 8 <= width <= 15):
        errors.append("strict scenes must have dimensions in 8..15")
    if facts["marker_palette"] not in MARKER_PALETTES:
        errors.append("strict scenes must use the canonical or alternate marker palette")
    if facts["interaction_mode"] not in INTERACTION_MODES:
        errors.append("strict scenes must have a probeable interaction mode")
    if facts["ray_stats"]["painted_extension_cells"] <= 0:
        errors.append("strict scenes must visibly extend at least one rotated marker")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if facts["marker_palette"] not in MARKER_PALETTES:
        raise ValueError("marker palette is outside the advertised override domain")
    if facts["interaction_mode"] not in INTERACTION_MODES:
        raise ValueError("interaction mode is not uniquely observable")
    return {name: facts[name] for name in AXES}


def _place_layout(
    height: int,
    width: int,
    positions: tuple[tuple[int, int], ...],
    marker_values: tuple[int, int, int, int] = _CANONICAL_MARKERS,
) -> list[list[int]] | None:
    grid = full_grid(height, width, 0)
    for row, col in positions:
        role_cells = _block_cells(row, col) + _corner_cells(row, col)
        if any(
            not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0
            for r, c in role_cells
        ):
            return None
        for r, c in _block_cells(row, col):
            grid[r][c] = 2
        for (r, c), value in zip(_corner_cells(row, col), marker_values):
            grid[r][c] = value
    return grid


def _find_layouts(
    height: int, width: int, n_blocks: int, interaction_mode: str
) -> tuple[tuple[tuple[int, int], ...], ...]:
    key = (height, width, n_blocks, interaction_mode)
    if key in _LAYOUT_CACHE:
        return _LAYOUT_CACHE[key]

    candidates = [
        (row, col)
        for row in range(1, height - 2)
        for col in range(1, width - 2)
    ]
    found: list[tuple[tuple[int, int], ...]] = []
    # Eight geometries per key are enough for nuisance diversity while keeping
    # semantic construction cheap under the large override matrix.
    for positions in itertools.combinations(candidates, n_blocks):
        grid = _place_layout(height, width, positions)
        if grid is None:
            continue
        blocks = _find_blocks(grid)
        if len(blocks) != n_blocks or set(blocks) != set(positions):
            continue
        stats = _ray_statistics(grid, blocks)
        if _interaction_from_stats(stats) != interaction_mode:
            continue
        if stats["painted_extension_cells"] <= 0:
            continue
        found.append(tuple(positions))
        if len(found) >= 8:
            break

    result = tuple(found)
    _LAYOUT_CACHE[key] = result
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    scheduled_profile = schedule_profile(seed, sample_index, band)
    defaults = _scheduled_defaults(scheduled_profile, sample_index, band, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", 8, 15, int(defaults["grid_h"]))
    width = _draw_exact_int(ctx, "grid_w", 8, 15, int(defaults["grid_w"]))
    n_blocks = _draw_exact_int(ctx, "n_blocks", 1, 3, int(defaults["n_blocks"]))
    marker_palette = _draw_exact_choice(
        ctx,
        "marker_palette",
        MARKER_PALETTES,
        str(defaults["marker_palette"]),
    )
    interaction_mode = _draw_exact_choice(
        ctx,
        "interaction_mode",
        INTERACTION_MODES,
        str(defaults["interaction_mode"]),
    )

    if n_blocks == 1 and interaction_mode != "edge":
        raise _incompatible(
            "non-edge interaction modes require at least two blocks",
            "n_blocks",
            "interaction_mode",
        )

    layouts = _find_layouts(height, width, n_blocks, interaction_mode)
    if not layouts:
        raise _incompatible(
            f"no lawful layout for {height}x{width}, n_blocks={n_blocks}, "
            f"interaction_mode={interaction_mode!r}",
            "grid_h",
            "grid_w",
            "n_blocks",
            "interaction_mode",
        )
    positions = ctx.draw_rng("layout_variant").choice(layouts)

    palette_values = list(_PALETTE_VALUES[marker_palette])
    grid = full_grid(height, width, 0)
    for block_index, (row, col) in enumerate(positions):
        values = palette_values[:]
        # Draw order remains deterministic yet differs by block and sample.
        block_rng = ctx.draw_rng(f"corner_colors_{block_index}")
        block_rng.shuffle(values)
        for r, c in _block_cells(row, col):
            grid[r][c] = 2
        for (r, c), value in zip(_corner_cells(row, col), values):
            grid[r][c] = value

    expected: dict[str, int | str] = {
        "grid_h": height,
        "grid_w": width,
        "n_blocks": n_blocks,
        "marker_palette": marker_palette,
        "interaction_mode": interaction_mode,
    }
    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(
            f"internal construction mismatch: expected {expected}, observed {observed}"
        )
    return [row[:] for row in grid]


def _apply_rule(
    grid: list[list[int]],
    *,
    corner_map: tuple[int, int, int, int] = (2, 0, 3, 1),
    extend: bool = True,
    special_stop: bool = True,
) -> list[list[int]]:
    """Shared exact/rival implementation; canonical Racket remains authority.

    ``corner_map`` indexes old (TL,TR,BL,BR) values for new
    (TL,TR,BL,BR).  The authority mapping is (BL,TL,BR,TR).
    """
    source = [row[:] for row in grid]
    height, width = len(source), len(source[0])
    result = copy.deepcopy(source)
    blocks = _find_blocks(source)
    directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))

    for row, col in blocks:
        corners = _corner_cells(row, col)
        old_values = tuple(source[r][c] for r, c in corners)
        new_values = tuple(old_values[index] for index in corner_map)
        for (r, c), value in zip(corners, new_values):
            result[r][c] = value
        if not extend:
            continue

        for (start_row, start_col), (drow, dcol), value in zip(
            corners, directions, new_values
        ):
            current_row, current_col = start_row, start_col
            while True:
                next_row = current_row + drow
                next_col = current_col + dcol
                if not (0 <= next_row < height and 0 <= next_col < width):
                    break
                if source[next_row][next_col] != 0:
                    break

                blocked = False
                if special_stop:
                    opposite_col = next_col - dcol
                    opposite_is_2 = (
                        0 <= opposite_col < width
                        and source[next_row][opposite_col] == 2
                    )
                    next1_row, next1_col = next_row + drow, next_col + dcol
                    next2_row, next2_col = (
                        next_row + 2 * drow,
                        next_col + 2 * dcol,
                    )
                    rem1 = (
                        0 <= next1_row < height
                        and 0 <= next1_col < width
                        and source[next1_row][next1_col] == 0
                    )
                    rem2 = (
                        rem1
                        and 0 <= next2_row < height
                        and 0 <= next2_col < width
                        and source[next2_row][next2_col] == 0
                    )
                    blocked = opposite_is_2 and rem1 and not rem2
                if blocked:
                    break

                result[next_row][next_col] = value
                current_row, current_col = next_row, next_col
    return result


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python mirror used only for tests/teaching diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _apply_rule(analysis["grid"])


def _rival_opposite_swap(grid):
    # Stale-generator hypothesis: TL<->BR and TR<->BL.
    return _apply_rule(grid, corner_map=(3, 2, 1, 0))


def _rival_no_special_stop(grid):
    return _apply_rule(grid, special_stop=False)


def _rival_rotate_only(grid):
    return _apply_rule(grid, extend=False)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "opposite_corner_swap": _rival_opposite_swap,
    "no_special_skimmer_stop": _rival_no_special_stop,
    "rotate_only_no_rays": _rival_rotate_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _interaction_witness(mode: str):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return (
            not analysis["errors"]
            and analysis["facts"]["interaction_mode"] == mode
            and analysis["facts"]["ray_stats"]["painted_extension_cells"] > 0
        )

    return witness


SEMANTIC_WITNESSES = {
    "edge_extension": _interaction_witness("edge"),
    "direct_red_stop": _interaction_witness("red_stop"),
    "open_skimmer_negative_control": _interaction_witness("open_skimmer"),
    "blocked_skimmer_exception": _interaction_witness("blocked_skimmer"),
}
WITNESS_RIVALS = {
    "edge_extension": ["rotate_only_no_rays", "opposite_corner_swap"],
    "direct_red_stop": ["rotate_only_no_rays", "opposite_corner_swap"],
    "open_skimmer_negative_control": ["rotate_only_no_rays", "opposite_corner_swap"],
    "blocked_skimmer_exception": [
        "no_special_skimmer_stop",
        "rotate_only_no_rays",
        "opposite_corner_swap",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a declared counter-hypothesis still wins."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    normalized_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
            continue
        normalized_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
        return reasons
    truth_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != truth_query:
        reasons.append("query output disagrees with the canonical rule")

    if len(normalized_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            try:
                fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                rival_query = rival(query["input"])
            except Exception as exc:
                reasons.append(f"competitor {name} crashed: {exc!r}")
                continue
            if fits and rival_query != truth_query:
                reasons.append(
                    f"competitor {name!r} fits every demo but predicts a different query"
                )
    return reasons


def mutation_fixtures():
    base = generate(
        73013,
        3,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        n_blocks=2,
        marker_palette="canonical",
        interaction_mode="blocked_skimmer",
    )
    analysis = _analysis(base)
    first_row, first_col = analysis["facts"]["blocks"][0]
    first_corners = _corner_cells(first_row, first_col)

    blank = full_grid(9, 9, 0)

    missing_marker = copy.deepcopy(base)
    r, c = first_corners[0]
    missing_marker[r][c] = 0

    duplicate_marker = copy.deepcopy(base)
    (r0, c0), (r1, c1) = first_corners[:2]
    duplicate_marker[r1][c1] = duplicate_marker[r0][c0]

    broken_block = copy.deepcopy(base)
    broken_block[first_row][first_col] = 0

    stray_color = copy.deepcopy(base)
    for row in range(len(stray_color)):
        for col in range(len(stray_color[0])):
            if stray_color[row][col] == 0:
                stray_color[row][col] = 9
                break
        else:
            continue
        break

    stray_two = copy.deepcopy(base)
    for row in range(len(stray_two)):
        for col in range(len(stray_two[0])):
            if stray_two[row][col] == 0:
                stray_two[row][col] = 2
                break
        else:
            continue
        break

    return [
        ("blank_scene", blank),
        ("missing_diagonal_marker", missing_marker),
        ("duplicate_marker_color", duplicate_marker),
        ("broken_red_block", broken_block),
        ("stray_foreground", stray_color),
        ("stray_color2", stray_two),
    ]
