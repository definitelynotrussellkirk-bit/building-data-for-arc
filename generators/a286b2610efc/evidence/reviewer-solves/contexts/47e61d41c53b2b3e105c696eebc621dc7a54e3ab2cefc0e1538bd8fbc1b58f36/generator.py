"""Generator for ARC task a286b2610efc: complete straight segments.

The authoritative rule scans every horizontal and vertical length-three window
in the *input* grid.  ``0,v,v`` fills its leading zero and ``v,v,0`` fills its
trailing zero.  A boundary domino therefore grows to length three; an interior
``0,v,v,0`` domino participates in two windows and grows to length four.

Generated lessons deliberately alternate boundary and interior scenes.  This
makes the curriculum distinguish the real sliding-window rule from the strongest
canonical shortcut: "extend each domino once toward the grid interior".
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a286b2610efc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2e117d692607"

SUMMARY = (
    "Place exactly two isolated, differently colored straight dominoes on a "
    "0-background: one horizontal and one vertical.  The rule scans all "
    "length-three row and column windows in the original input; 0,v,v fills "
    "the leading zero and v,v,0 fills the trailing zero.  Boundary dominoes "
    "therefore become length-three segments, while interior 0,v,v,0 motifs "
    "extend on both sides and become length-four segments.  Lessons alternate "
    "boundary and interior layouts so a one-extension shortcut is refuted."
)

INVARIANTS = [
    "the background is 0 and every cell is an integer ARC color 0..9",
    "exactly two distinct nonzero colors occur, each in one adjacent pair",
    "one pair is horizontal and the other is vertical",
    "both pairs are either boundary motifs with one in-grid extension cell or interior motifs with two",
    "all extension cells are empty and the two complete output footprints are separated",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_HEIGHTS = (7, 8, 9)
_WIDTHS = (8, 9, 10)
_LAYOUTS = ("edge", "interior")
_BAND_COLOR_OFFSETS = {"easy": 0, "medium": 3, "hard": 6}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-height 7",
        "valid": "7|8|9",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-width 8|9",
        "valid": "8|9|10",
    },
    "layout": {
        "type": "str",
        "default": "alternates edge|interior by sample_index",
        "valid": "edge|interior",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    grid_h = overrides.get("grid_h")
    if grid_h is not None and (type(grid_h) is not int or grid_h not in _HEIGHTS):
        raise ValueError(f"grid_h must be one of {_HEIGHTS}")

    grid_w = overrides.get("grid_w")
    if grid_w is not None and (type(grid_w) is not int or grid_w not in _WIDTHS):
        raise ValueError(f"grid_w must be one of {_WIDTHS}")

    layout = overrides.get("layout")
    if layout is not None and (type(layout) is not str or layout not in _LAYOUTS):
        raise ValueError(f"layout must be one of {_LAYOUTS}")


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]

    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [
                    "cells must be literal ARC integers 0..9; "
                    f"got {value!r} at {row_index},{col_index}"
                ]
    return []


def _motif_from_cells(
    color: int,
    cells: list[tuple[int, int]],
    height: int,
    width: int,
) -> tuple[dict[str, Any] | None, str | None]:
    cells = sorted(cells)
    (row0, col0), (row1, col1) = cells

    if row0 == row1 and col1 == col0 + 1:
        orientation = "horizontal"
        before = (row0, col0 - 1) if col0 > 0 else None
        after = (row0, col1 + 1) if col1 + 1 < width else None
    elif col0 == col1 and row1 == row0 + 1:
        orientation = "vertical"
        before = (row0 - 1, col0) if row0 > 0 else None
        after = (row1 + 1, col0) if row1 + 1 < height else None
    else:
        return None, (
            f"color {color} must form one orthogonally adjacent straight pair, "
            f"got cells {cells}"
        )

    extensions = tuple(pos for pos in (before, after) if pos is not None)
    if len(extensions) == 1:
        layout = "edge"
    elif len(extensions) == 2:
        layout = "interior"
    else:  # Defensive: impossible for the supported dimensions.
        return None, f"color {color} has no in-grid extension window"

    footprint = frozenset(cells) | frozenset(extensions)
    return {
        "color": color,
        "orientation": orientation,
        "cells": tuple(cells),
        "before": before,
        "after": after,
        "extensions": extensions,
        "layout": layout,
        "footprint": footprint,
    }, None


def _analyze_grid(grid) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return None, errors

    height, width = len(grid), len(grid[0])
    if height not in _HEIGHTS:
        errors.append(f"grid height must be one of {_HEIGHTS}, got {height}")
    if width not in _WIDTHS:
        errors.append(f"grid width must be one of {_WIDTHS}, got {width}")
    if errors:
        return None, errors

    by_color: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((row_index, col_index))

    if len(by_color) != 2:
        return None, [
            "expected exactly two distinct nonzero colors, "
            f"found {sorted(by_color)}"
        ]

    motifs: list[dict[str, Any]] = []
    for color in sorted(by_color):
        cells = by_color[color]
        if len(cells) != 2:
            errors.append(
                f"color {color} must occur exactly twice, found {len(cells)} cells"
            )
            continue
        motif, error = _motif_from_cells(color, cells, height, width)
        if error is not None:
            errors.append(error)
        else:
            assert motif is not None
            motifs.append(motif)
    if errors:
        return None, errors

    orientations = {motif["orientation"] for motif in motifs}
    if orientations != {"horizontal", "vertical"}:
        errors.append(
            "expected one horizontal and one vertical domino, "
            f"found {sorted(orientations)}"
        )

    layouts = {motif["layout"] for motif in motifs}
    if len(layouts) != 1:
        errors.append(
            "both dominoes must share one layout class (edge or interior), "
            f"found {sorted(layouts)}"
        )

    for motif in motifs:
        for row_index, col_index in motif["extensions"]:
            if grid[row_index][col_index] != 0:
                errors.append(
                    f"extension cell {row_index},{col_index} for color "
                    f"{motif['color']} must be background 0"
                )

    if len(motifs) == 2:
        first, second = motifs
        if first["footprint"] & second["footprint"]:
            errors.append("the two complete output footprints must not overlap")
        else:
            minimum_chebyshev = min(
                max(abs(row0 - row1), abs(col0 - col1))
                for row0, col0 in first["footprint"]
                for row1, col1 in second["footprint"]
            )
            if minimum_chebyshev <= 1:
                errors.append(
                    "the two complete output footprints must be separated by "
                    "at least one full background cell"
                )

    if errors:
        return None, errors

    layout = next(iter(layouts))
    return {
        "height": height,
        "width": width,
        "layout": layout,
        "motifs": tuple(motifs),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full, linked teaching grammar."""
    del difficulty, meta
    _analysis, errors = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted grid is a clean instance of the exact local rule."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the generated grid."""
    analysis, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    assert analysis is not None
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "layout": analysis["layout"],
    }


def _candidate(
    orientation: str,
    cells: tuple[tuple[int, int], tuple[int, int]],
    before: tuple[int, int] | None,
    after: tuple[int, int] | None,
) -> dict[str, Any]:
    extensions = tuple(pos for pos in (before, after) if pos is not None)
    return {
        "orientation": orientation,
        "cells": cells,
        "before": before,
        "after": after,
        "extensions": extensions,
        "footprint": frozenset(cells) | frozenset(extensions),
    }


def _horizontal_candidates(height: int, width: int, layout: str):
    candidates = []
    for row in range(height):
        starts = (0, width - 2) if layout == "edge" else range(1, width - 2)
        for col in starts:
            before = (row, col - 1) if col > 0 else None
            after = (row, col + 2) if col + 2 < width else None
            candidates.append(
                _candidate(
                    "horizontal",
                    ((row, col), (row, col + 1)),
                    before,
                    after,
                )
            )
    return candidates


def _vertical_candidates(height: int, width: int, layout: str):
    candidates = []
    for col in range(width):
        starts = (0, height - 2) if layout == "edge" else range(1, height - 2)
        for row in starts:
            before = (row - 1, col) if row > 0 else None
            after = (row + 2, col) if row + 2 < height else None
            candidates.append(
                _candidate(
                    "vertical",
                    ((row, col), (row + 1, col)),
                    before,
                    after,
                )
            )
    return candidates


def _compatible_pairs(height: int, width: int, layout: str):
    pairs = []
    for horizontal in _horizontal_candidates(height, width, layout):
        for vertical in _vertical_candidates(height, width, layout):
            if horizontal["footprint"] & vertical["footprint"]:
                continue
            minimum_chebyshev = min(
                max(abs(row0 - row1), abs(col0 - col1))
                for row0, col0 in horizontal["footprint"]
                for row1, col1 in vertical["footprint"]
            )
            if minimum_chebyshev > 1:
                pairs.append((horizontal, vertical))
    return pairs


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Alternate the two rule-identifying layout profiles."""
    del seed, difficulty
    return "edge" if sample_index % 2 == 0 else "interior"


SCHEDULE_PROFILES = _LAYOUTS


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

    scheduled_height = 7
    scheduled_width = 8 + ((sample_index // 2) % 2)
    scheduled_layout = schedule_profile(seed, sample_index, difficulty)

    height_options = _HEIGHTS if overrides.get("grid_h") is not None else (scheduled_height,)
    width_options = _WIDTHS if overrides.get("grid_w") is not None else (scheduled_width,)
    layout_options = _LAYOUTS if overrides.get("layout") is not None else (scheduled_layout,)

    height = int(ctx.draw_choice("grid_h", height_options))
    width = int(ctx.draw_choice("grid_w", width_options))
    layout = str(ctx.draw_choice("layout", layout_options))
    base_colors = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    band = difficulty or "medium"
    offset = _BAND_COLOR_OFFSETS[band]
    colors = tuple(1 + ((color - 1 + offset) % 9) for color in base_colors)

    placements = _compatible_pairs(height, width, layout)
    if not placements:
        raise AssertionError(
            f"no compatible placements for {height}x{width} layout={layout}"
        )
    horizontal, vertical = ctx.draw_rng("placement").choice(placements)

    grid = full_grid(height, width, 0)
    for motif, color in zip((horizontal, vertical), colors):
        for row, col in motif["cells"]:
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid task instance: " + "; ".join(errors))
    return grid


def rule_mirror(grid):
    """Python mirror of the pinned Racket rule; never output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid complete-segment instance: " + "; ".join(errors))

    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])

    for row in range(height):
        for col in range(width - 2):
            first, middle, last = source[row][col : col + 3]
            if first == 0 and middle != 0 and middle == last:
                output[row][col] = middle
            elif first != 0 and first == middle and last == 0:
                output[row][col + 2] = first

    for row in range(height - 2):
        for col in range(width):
            first = source[row][col]
            middle = source[row + 1][col]
            last = source[row + 2][col]
            if first == 0 and middle != 0 and middle == last:
                output[row][col] = middle
            elif first != 0 and first == middle and last == 0:
                output[row + 2][col] = first

    return output


def one_sided_triplet_completion(grid):
    """Strong canonical shortcut: extend every domino exactly once inward.

    On every canonical example each domino is boundary-flush, so it has only
    one in-grid extension and this rival is answer-equivalent.  On an interior
    ``0,v,v,0`` motif it selects the positive-direction extension only, whereas
    the authoritative sliding-window rule fills both sides.
    """
    analysis, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("invalid complete-segment instance: " + "; ".join(errors))
    assert analysis is not None

    output = [list(row) for row in grid]
    for motif in analysis["motifs"]:
        chosen = motif["after"] if motif["after"] is not None else motif["before"]
        assert chosen is not None
        row, col = chosen
        output[row][col] = motif["color"]
    return output


def _two_sided_completion_witness(grid) -> bool:
    analysis, errors = _analyze_grid(grid)
    if errors or analysis is None or analysis["layout"] != "interior":
        return False
    return one_sided_triplet_completion(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "two_sided_completion": _two_sided_completion_witness,
}
SEMANTIC_RIVALS = {
    "one_sided_triplet_completion": one_sided_triplet_completion,
}
WITNESS_RIVALS = {
    "two_sided_completion": ["one_sided_triplet_completion"],
}
LESSON_COMPETITORS = {
    "one_sided_triplet_completion": one_sided_triplet_completion,
}
CANONICAL_SHORTCUTS = {
    "one_sided_triplet_completion": one_sided_triplet_completion,
}


def _normalized_grid(grid):
    return tuple(tuple(row) for row in grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require a valid edge example and a rival-refuting interior example."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    layouts: set[str] = set()
    rival_refuted = False

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue

        analysis, errors = _analyze_grid(demo["input"])
        if errors or analysis is None:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        layouts.add(analysis["layout"])

        expected = rule_mirror(demo["input"])
        if _normalized_grid(demo["output"]) != _normalized_grid(expected):
            reasons.append(f"demo {index} output does not match the pinned rule")
            continue
        if _normalized_grid(one_sided_triplet_completion(demo["input"])) != _normalized_grid(expected):
            rival_refuted = True

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")

    if layouts != {"edge", "interior"}:
        reasons.append(
            "demonstrations must include both edge and interior layouts; "
            f"found {sorted(layouts)}"
        )
    if not rival_refuted:
        reasons.append(
            "demonstrations do not refute one_sided_triplet_completion"
        )
    return reasons
