"""Generator for ARC task ``1229e88ae0e6`` — center the nonzero motif.

The canonical rule crops the unique 4-connected nonzero motif to its bounding
box and pastes that crop at the floor-centered origin of a same-sized blank
grid.  Colors, holes, and internal geometry are preserved exactly.

The eight-direction schedule interleaves diagonal and single-axis moves.
Every four-demo window contains an interior source, odd-slack floor tie,
long translation, exact hole-position evidence, and cell-bound multicolor
evidence. Canvases and connected supports vary within each difficulty; no
Racket authority or safety label is changed.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1229e88ae0e6"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "5e5cb5402934"

SUMMARY = (
    "Translate the unique 4-connected nonzero motif so its bounding-box crop "
    "is floor-centered in the unchanged grid; preserve every color, hole, and "
    "relative cell position."
)

INVARIANTS = [
    "background is 0 and the nonzero cells form one 4-connected motif",
    "the motif bbox has height and width at least two and contains a zero hole",
    "the input motif bbox is not already centered",
    "the output keeps the input dimensions, colors, holes, and motif geometry",
]

# Source locations are measured relative to the floor-centered bbox origin.
# A consecutive quartet has two diagonal and two single-axis translations.
_ZONES = ("northwest", "east", "southeast", "north",
          "northeast", "west", "southwest", "south")
_ZONE_SIGNS = {
    "northwest": (-1, -1), "north": (-1, 0), "northeast": (-1, 1),
    "west": (0, -1), "east": (0, 1),
    "southwest": (1, -1), "south": (1, 0), "southeast": (1, 1),
}
_COLOR_MODES = ("mono", "multi")
_CANONICAL_SHAPES = {(5, 5), (5, 6), (6, 6), (6, 7)}

AXES = {
    "source_zone": {
        "type": "str",
        "default": "eight-slot diagonal and single-axis source schedule",
        "valid": "|".join(_ZONES),
    },
    "color_mode": {
        "type": "str",
        "default": "seed-phased mono|multi|multi|mono schedule",
        "valid": "|".join(_COLOR_MODES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

# Repeated counts are explicit sampling weights, not repeated templates.
# Each band retains small canonical motifs; higher bands favor larger supports.
# Canvas size is intentionally NOT determined by difficulty.
_BAND_SPECS = {
    "easy": {"cell_counts": (3, 3, 3, 4, 4), "max_colors": 2},
    "medium": {"cell_counts": (3, 3, 4, 4, 5, 5, 6), "max_colors": 3},
    "hard": {"cell_counts": (3, 4, 5, 6, 6, 7, 7, 8), "max_colors": 3},
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _scheduled_zone(sample_index: int, seed: int = 0) -> str:
    # Actual episodes start at index 0, so vary the direction at query index 4
    # across seeds, not only across sliding windows of a long census.
    return _ZONES[(int(sample_index) + int(seed)) % len(_ZONES)]


def _color_schedule_slot(seed: int, sample_index: int) -> int:
    """Return the independently phased four-example palette curriculum slot."""
    phase = (int(seed) // 8 + int(seed) // 32) % 4
    return (int(sample_index) + phase) % 4


def _scheduled_color_mode(seed: int, sample_index: int) -> str:
    # Two multicolor examples in every consecutive quartet. Unlike strict
    # alternation, this does not couple color mode to diagonal/cardinal moves.
    # Separate seed digits phase directions, witness roles, and palettes.
    # The sum gives all direction/color pairs within 32 seeds, while the
    # higher digit decouples palette from witness role over the 128-seed cycle.
    return ("mono", "multi", "multi", "mono")[
        _color_schedule_slot(seed, sample_index)
    ]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic joint curriculum slot for semantic-gate audits."""
    del difficulty
    return (
        f"{_scheduled_zone(sample_index, seed)}:"
        f"{_scheduled_color_mode(seed, sample_index)}"
    )


SCHEDULE_PROFILES = tuple(
    f"{zone}:{mode}" for zone in _ZONES for mode in _COLOR_MODES
)


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 4 <= len(grid) <= 12 or not 4 <= width <= 12:
        return [f"grid dimensions must be in 4..12, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    if not cells:
        return False
    body = set(cells)
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in body and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(body)


def _basic_analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    colors = sorted({grid[r][c] for r, c in cells})
    if not 3 <= len(cells) <= 9:
        errors.append(f"expected 3-9 motif cells, found {len(cells)}")
    if not 1 <= len(colors) <= 3:
        errors.append(f"expected 1-3 nonzero colors, found {len(colors)}")
    if cells and not _connected(cells):
        errors.append("nonzero motif is not 4-connected")
    if not cells:
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "cells": cells,
            "colors": colors,
        }

    row0, col0, row1, col1 = _bbox(cells)
    bbox_h = row1 - row0 + 1
    bbox_w = col1 - col0 + 1
    if bbox_h < 2 or bbox_w < 2:
        errors.append("motif bbox must have height and width at least two")
    if len(cells) >= bbox_h * bbox_w:
        errors.append("motif bbox must contain at least one background hole")

    target_row = (height - bbox_h) // 2
    target_col = (width - bbox_w) // 2
    row_delta = row0 - target_row
    col_delta = col0 - target_col
    if row_delta == 0 and col_delta == 0:
        errors.append("motif bbox is already centered")

    signs = (_sign(row_delta), _sign(col_delta))
    zone = next((name for name, pair in _ZONE_SIGNS.items() if pair == signs), None)

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "cells": cells,
        "colors": colors,
        "bbox": (row0, col0, row1, col1),
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "target_origin": (target_row, target_col),
        "row_delta": row_delta,
        "col_delta": col_delta,
        "source_zone": zone,
        "touches_border": (
            row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1
        ),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover both declared controls from the returned input grid."""
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "source_zone": analysis["source_zone"],
        "color_mode": "mono" if len(analysis["colors"]) == 1 else "multi",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding motifs."""
    del difficulty
    analysis = _basic_analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the task's small sparse connected-motif canonical manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _basic_analysis(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_SHAPES:
        errors.append(
            "grid shape is outside the canonical 5x5/5x6/6x6/6x7 envelope"
        )
    if analysis["bbox_h"] > 3 or analysis["bbox_w"] > 3:
        errors.append("motif bbox exceeds the canonical-like 3x3 envelope")
    return errors


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


@lru_cache(maxsize=24)
def _motifs(height: int, width: int, count: int):
    """All connected, bbox-spanning, non-solid supports in a <=3x3 box.

    Enumeration is bounded by 2**9 and returns immutable, sorted coordinates.
    Sampling by bbox and count prevents the many 3x3 masks from swamping the
    small motifs. No color or original canonical answer enters this catalog.
    """
    if count >= height * width:
        return ()
    positions = tuple((r, c) for r in range(height) for c in range(width))
    return tuple(cells for cells in combinations(positions, count)
                 if _bbox(cells) == (0, 0, height-1, width-1) and _connected(cells))


def _origins(zone: str, height: int, width: int, motif_h: int, motif_w: int,
             *, interior: bool, long_move: bool):
    slack_r, slack_c = height-motif_h, width-motif_w
    tr, tc = slack_r//2, slack_c//2
    wanted = _ZONE_SIGNS[zone]
    return tuple((r, c) for r in range(slack_r+1) for c in range(slack_c+1)
                 if (_sign(r-tr), _sign(c-tc)) == wanted
                 and (not interior or (0 < r < slack_r and 0 < c < slack_c))
                 and (not long_move or max(abs(r-tr), abs(c-tc)) >= 2))


def _is_row_major_prefix(
    support: Sequence[tuple[int, int]], height: int, width: int
) -> bool:
    """Whether support merely fills the first N cells of its bbox."""
    prefix = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
    )[:len(support)]
    return tuple(sorted(support)) == prefix


@lru_cache(maxsize=128)
def _supports_for_slot(height: int, width: int, count: int, slot: int):
    """Return supports admitted by a curriculum slot's geometry witness."""
    supports = _motifs(height, width, count)
    if slot == 1:
        # A row-major-prefix support does not identify the positions of holes:
        # a learner can center the bbox, preserve cell count/colors, and pack
        # all nonzeros into its first N cells. Reserve one slot to refute that.
        supports = tuple(
            support for support in supports
            if not _is_row_major_prefix(support, height, width)
        )
    return supports


@lru_cache(maxsize=96)
def _layouts(band: str, zone: str, slot: int):
    """Finite feasibility filter; generation never relies on rejection loops.

    Slot 0 proves odd-slack floor tie-breaking AND multi-cell translation.
    Slot 1 proves exact hole positions rather than row-major hole packing.
    Slot 2 proves that interior objects move. Slot 3 is unrestricted.
    These constraints also remain feasible for all explicit source-zone axes.
    """
    choices = []
    for height, width in sorted(_CANONICAL_SHAPES):
        for motif_h in (2, 3):
            for motif_w in (2, 3):
                counts = tuple(
                    n for n in _BAND_SPECS[band]["cell_counts"]
                    if _supports_for_slot(motif_h, motif_w, n, slot)
                )
                if not counts:
                    continue
                if slot == 0 and (height-motif_h) % 2 == (width-motif_w) % 2 == 0:
                    continue
                origins = _origins(zone, height, width, motif_h, motif_w,
                                   interior=slot == 2, long_move=slot == 0)
                if origins:
                    choices.append((height, width, motif_h, motif_w, counts, origins))
    return tuple(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    requested_zone = overrides.get("source_zone")
    requested_mode = overrides.get("color_mode")
    if requested_zone is not None and requested_zone not in _ZONES:
        raise ValueError(f"unknown source_zone: {requested_zone!r}")
    if requested_mode is not None and requested_mode not in _COLOR_MODES:
        raise ValueError(f"unknown color_mode: {requested_mode!r}")

    selected_zone = requested_zone or _scheduled_zone(sample_index, seed)
    selected_mode = requested_mode or _scheduled_color_mode(seed, sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    source_zone = ctx.draw_choice("source_zone", [selected_zone])
    color_mode = ctx.draw_choice("color_mode", [selected_mode])

    spec = _BAND_SPECS[band]
    # Do not phase witness roles with directions: that would make northwest
    # sources permanently long/border-only even after query direction varied.
    slot = (int(sample_index) + (int(seed) // 8)) % 4
    layouts = _layouts(band, source_zone, slot)
    if not layouts:
        raise ValueError(f"no feasible layout for {band}/{source_zone}")
    # Equal choice among feasible canvases, then bbox shapes, rather than a
    # flat draw over supports (which would heavily favor 3x3 dense motifs).
    canvases = tuple(sorted({layout[:2] for layout in layouts}))
    canvas = ctx.draw_choice("canvas", canvases)
    layout_rng = ctx.draw_rng("layout")
    height, width, motif_h, motif_w, counts, origins = layout_rng.choice(
        tuple(layout for layout in layouts if layout[:2] == canvas)
    )
    count = ctx.draw_choice("motif_cell_count", counts)
    support = ctx.draw_rng("shape").choice(
        _supports_for_slot(motif_h, motif_w, count, slot)
    )
    row0, col0 = ctx.draw_rng("origin").choice(origins)

    palette_rng = ctx.draw_rng("palette")
    if color_mode == "mono":
        palette = [palette_rng.choice(range(1, 10))]
    else:
        n_colors = 2
        if spec["max_colors"] >= 3 and palette_rng.randrange(2) == 1:
            n_colors = 3
        palette = palette_rng.sample(range(1, 10), n_colors)

    cells = list(support)
    palette_rng.shuffle(cells)
    # Realize every requested palette color, then color the remaining cells
    # independently. Do not force the per-color frequencies to be balanced.
    color_by_cell = {
        cell: palette[index] if index < len(palette) else palette_rng.choice(palette)
        for index, cell in enumerate(cells)
    }
    if color_mode == "multi" and _color_schedule_slot(seed, sample_index) == 1:
        # Palette presence alone does not bind colors to motif cells. If this
        # designated witness happens to be monotone in row-major order, a wrong
        # learner can center the support and sort the colors. Reorder the same
        # multiset only when needed so the sequence has both an ascent and a
        # descent; color identities and frequencies remain unchanged.
        ordered_cells = sorted(support)
        values = [color_by_cell[cell] for cell in ordered_cells]
        if values == sorted(values) or values == sorted(values, reverse=True):
            remaining = sorted(values)
            low = remaining.pop(0)
            high = remaining.pop(-1)
            if low in remaining:
                remaining.remove(low)
                values = [low, high, low, *remaining]
            else:
                middle = remaining.pop(0)
                values = [high, low, middle, *remaining]
            color_by_cell = dict(zip(ordered_cells, values))
    grid = full_grid(height, width, 0)
    for row, col in support:
        grid[row0 + row][col0 + col] = color_by_cell[(row, col)]
    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; the synchronized Racket remains authority."""
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    row0, col0, _, _ = analysis["bbox"]
    target_row, target_col = analysis["target_origin"]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row, col in analysis["cells"]:
        output[target_row + row - row0][target_col + col - col0] = grid[row][col]
    return output


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _paste_with_origin(
    grid: Sequence[Sequence[int]], target_row: int, target_col: int
) -> list[list[int]]:
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    row0, col0, _, _ = analysis["bbox"]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row, col in analysis["cells"]:
        new_row = target_row + row - row0
        new_col = target_col + col - col0
        if 0 <= new_row < analysis["height"] and 0 <= new_col < analysis["width"]:
            output[new_row][new_col] = grid[row][col]
    return output


def _rival_ceil_center(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    target_row = (analysis["height"] - analysis["bbox_h"] + 1) // 2
    target_col = (analysis["width"] - analysis["bbox_w"] + 1) // 2
    return _paste_with_origin(grid, target_row, target_col)


def _rival_border_only(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    return rule_mirror(grid) if analysis["touches_border"] else _copy_grid(grid)


def _rival_solid_bbox(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    target_row, target_col = analysis["target_origin"]
    color = grid[analysis["cells"][0][0]][analysis["cells"][0][1]]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row in range(target_row, target_row + analysis["bbox_h"]):
        for col in range(target_col, target_col + analysis["bbox_w"]):
            output[row][col] = color
    return output


def _rival_recolor_first(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    first_color = grid[analysis["cells"][0][0]][analysis["cells"][0][1]]
    output = rule_mirror(grid)
    return [
        [first_color if value != 0 else 0 for value in row]
        for row in output
    ]


def _rival_sort_colors(grid, *, reverse: bool):
    """Center the right support but sort its colors by row-major cell order."""
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    output = rule_mirror(grid)
    cells = [
        (row, col)
        for row, values in enumerate(output)
        for col, value in enumerate(values)
        if value != 0
    ]
    colors = sorted(
        (output[row][col] for row, col in cells), reverse=reverse
    )
    for (row, col), color in zip(cells, colors):
        output[row][col] = color
    return output


def _rival_sort_colors_ascending(grid):
    return _rival_sort_colors(grid, reverse=False)


def _rival_sort_colors_descending(grid):
    return _rival_sort_colors(grid, reverse=True)


def _rival_pack_nonzeros(grid):
    """Center the bbox but pack its colors into the first N bbox cells."""
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    target_row, target_col = analysis["target_origin"]
    colors = [grid[row][col] for row, col in analysis["cells"]]
    positions = [
        (row, col)
        for row in range(analysis["bbox_h"])
        for col in range(analysis["bbox_w"])
    ][:len(colors)]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for (row, col), color in zip(positions, colors):
        output[target_row + row][target_col + col] = color
    return output


def _rival_center_rows_only(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    row0, col0, _, _ = analysis["bbox"]
    target_row, _ = analysis["target_origin"]
    return _paste_with_origin(grid, target_row, col0)


def _rival_center_columns_only(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    row0, _, _, _ = analysis["bbox"]
    _, target_col = analysis["target_origin"]
    return _paste_with_origin(grid, row0, target_col)


def _rival_diagonal_only(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    return (rule_mirror(grid) if analysis["row_delta"] and analysis["col_delta"]
            else _copy_grid(grid))


def _rival_one_step(grid):
    analysis = _basic_analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    row0, col0, _, _ = analysis["bbox"]
    return _paste_with_origin(grid, row0-_sign(analysis["row_delta"]),
                              col0-_sign(analysis["col_delta"]))


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "ceil_centering": _rival_ceil_center,
    "center_only_border_sources": _rival_border_only,
    "fill_centered_bbox": _rival_solid_bbox,
    "recolor_to_first_nonzero": _rival_recolor_first,
    "sort_colors_ascending": _rival_sort_colors_ascending,
    "sort_colors_descending": _rival_sort_colors_descending,
    "pack_nonzeros_in_centered_bbox": _rival_pack_nonzeros,
    "center_rows_only": _rival_center_rows_only,
    "center_columns_only": _rival_center_columns_only,
    "center_only_diagonal_sources": _rival_diagonal_only,
    "move_one_step_toward_center": _rival_one_step,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _basic_analysis(grid)
    return None if analysis["errors"] else analysis


def _interior_source_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and not analysis["touches_border"]
        and _rival_border_only(grid) != rule_mirror(grid)
    )


def _odd_slack_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and (
            (analysis["height"] - analysis["bbox_h"]) % 2 == 1
            or (analysis["width"] - analysis["bbox_w"]) % 2 == 1
        )
        and _rival_ceil_center(grid) != rule_mirror(grid)
    )


def _hole_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _rival_solid_bbox(grid) != rule_mirror(grid))


def _multicolor_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and len(analysis["colors"]) > 1
        and _rival_recolor_first(grid) != rule_mirror(grid)
    )


def _color_binding_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and len(analysis["colors"]) > 1
        and _rival_sort_colors_ascending(grid) != rule_mirror(grid)
        and _rival_sort_colors_descending(grid) != rule_mirror(grid)
    )


def _hole_position_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _rival_pack_nonzeros(grid) != rule_mirror(grid))


def _both_axes_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["row_delta"] != 0
        and analysis["col_delta"] != 0
        and _rival_center_rows_only(grid) != rule_mirror(grid)
    )


def _single_axis_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and (analysis["row_delta"] == 0) != (analysis["col_delta"] == 0)
                and _rival_diagonal_only(grid) != rule_mirror(grid))


def _long_translation_witness(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and max(abs(analysis["row_delta"]), abs(analysis["col_delta"])) >= 2
                and _rival_one_step(grid) != rule_mirror(grid))


SEMANTIC_WITNESSES = {
    "interior_source_refutes_border_shortcut": _interior_source_witness,
    "odd_slack_selects_floor_center": _odd_slack_witness,
    "bbox_hole_is_preserved": _hole_witness,
    "multicolor_pattern_is_preserved": _multicolor_witness,
    "colors_are_bound_to_exact_cells": _color_binding_witness,
    "exact_hole_positions_are_preserved": _hole_position_witness,
    "both_axes_translate": _both_axes_witness,
    "single_axis_translate": _single_axis_witness,
    "multi_cell_translation": _long_translation_witness,
}
WITNESS_RIVALS = {
    "interior_source_refutes_border_shortcut": ["center_only_border_sources"],
    "odd_slack_selects_floor_center": ["ceil_centering"],
    "bbox_hole_is_preserved": ["fill_centered_bbox"],
    "multicolor_pattern_is_preserved": ["recolor_to_first_nonzero"],
    "colors_are_bound_to_exact_cells": [
        "sort_colors_ascending", "sort_colors_descending"
    ],
    "exact_hole_positions_are_preserved": [
        "pack_nonzeros_in_centered_bbox"
    ],
    "both_axes_translate": ["center_rows_only", "center_columns_only"],
    "single_axis_translate": ["center_only_diagonal_sources"],
    "multi_cell_translation": ["move_one_step_toward_center"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named task-plausible rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            official = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is invalid: {exc}")
            continue
        if official != pair["output"]:
            reasons.append(f"demo {index} disagrees with the centering rule")

    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query disagrees with the centering rule")
    except Exception as exc:
        reasons.append(f"query is invalid: {exc}")

    if reasons:
        return reasons

    # Require the actual discriminating evidence, not four particular source
    # quadrants. The old quadrant requirement excluded canonical axis moves.
    for name, witness in SEMANTIC_WITNESSES.items():
        if not any(witness(pair["input"]) for pair in demos):
            reasons.append(f"demonstrations lack semantic witness: {name}")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
