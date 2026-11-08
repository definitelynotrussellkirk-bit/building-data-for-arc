"""Generator for ``Grow One More Onion Layer`` (task b883fcd81438).

The input contains exactly three square panels separated by full-height color-9
columns.  The third/rightmost panel is the query.  Treat its color-1 cells as a
binary shape, add one *cardinal* (4-neighbor) layer, and crop the grown mask to
its occupied bounding box.  The answer is always rendered in color 1.

The public examples accidentally admit two strong selection shortcuts: the
third panel is also the sparsest panel in every canonical pair, and (with a
rightmost tie break) the panel with the smallest occupied bounding box.  This
generator therefore makes the first panel deliberately smaller than the query
while keeping all three panels otherwise canonical-like.  The generated
curriculum teaches the positional rule rather than those count/size shortcuts.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b883fcd81438"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d15657f62bc6"

SUMMARY = (
    "Split the input at the two full-height color-9 divider columns. Use the "
    "THIRD/rightmost panel as the query, convert its color-1 shape to a binary "
    "mask, add one cardinal (up/down/left/right) boundary layer, then crop to "
    "the grown mask's occupied bounding box. Output the cropped mask in color 1."
)

INVARIANTS = [
    "background is color 0; foreground shapes are color 1; dividers are color 9",
    "exactly three equal square panels are separated by two one-column full-height 9 dividers",
    "each panel contains one nonempty 4-connected color-1 shape with a visible background margin",
    "the third/rightmost panel is always the query regardless of relative object count or bbox size",
    "the query is grown by one 4-neighbor layer and the result is cropped to the grown bbox",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

# One exact, finite, output-observable curriculum axis.  The panel size and
# query cell count uniquely identify the profile in a returned grid.
PROFILE_SPECS: dict[str, tuple[int, int]] = {
    "compact_five": (7, 5),
    "compact_seven": (7, 7),
    "large_nine": (9, 9),
    "large_thirteen": (9, 13),
}
SCENE_PROFILES = tuple(PROFILE_SPECS)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile sample-index cycle",
        "valid": "compact_five|compact_seven|large_nine|large_thirteen",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if not (dr == 0 and dc == 0)
)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _divider_columns(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[int]:
    height = len(grid)
    width = len(grid[0])
    return [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]


def _split_panels(grid: Any) -> list[list[list[int]]]:
    """Return panels split on full-height 9 columns; malformed input -> []."""
    if _grid_errors(grid):
        return []
    dividers = _divider_columns(grid)
    if len(dividers) != 2:
        return []
    left, right = dividers
    if left <= 0 or right <= left + 1 or right >= len(grid[0]) - 1:
        return []
    spans = ((0, left), (left + 1, right), (right + 1, len(grid[0])))
    return [[list(row[start:end]) for row in grid] for start, end in spans]


def _cells(panel: Any) -> set[tuple[int, int]]:
    return {
        (row, column)
        for row, values in enumerate(panel)
        for column, value in enumerate(values)
        if value not in (0, 9)
    }


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    cells = tuple(cells)
    if not cells:
        return None
    rows = [row for row, _ in cells]
    cols = [column for _, column in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    box = _bbox(cells)
    if box is None:
        return 0
    r0, c0, r1, c1 = box
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    box = _bbox(cells)
    if box is None:
        return ()
    r0, c0, _, _ = box
    return tuple(sorted((row - r0, column - c0) for row, column in cells))


def _connected4(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = {pending[0]}
    while pending:
        row, column = pending.pop()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, column + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _grow_cells(
    cells: set[tuple[int, int]],
    height: int,
    width: int,
    deltas: tuple[tuple[int, int], ...] = _CARDINAL,
) -> set[tuple[int, int]]:
    grown = set(cells)
    for row, column in cells:
        for dr, dc in deltas:
            rr, cc = row + dr, column + dc
            if 0 <= rr < height and 0 <= cc < width:
                grown.add((rr, cc))
    return grown


def _crop_mask(cells: set[tuple[int, int]]) -> list[list[int]]:
    box = _bbox(cells)
    if box is None:
        return [[0]]
    r0, c0, r1, c1 = box
    return [
        [1 if (row, column) in cells else 0 for column in range(c0, c1 + 1)]
        for row in range(r0, r1 + 1)
    ]


def _panel_output(panel: Any, *, diagonal: bool = False) -> list[list[int]]:
    cells = _cells(panel)
    deltas = _DIAGONAL_8 if diagonal else _CARDINAL
    return _crop_mask(_grow_cells(cells, len(panel), len(panel[0]), deltas))


def _raw_panel_output(panel: Any) -> list[list[int]]:
    return _crop_mask(_cells(panel))


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket rule."""
    panels = _split_panels(grid)
    if len(panels) != 3:
        raise ValueError("expected exactly three panels separated by two full-height 9 columns")
    if not _cells(panels[2]):
        raise ValueError("third/query panel is empty")
    return _panel_output(panels[2])


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height = len(grid)
    width = len(grid[0])
    dividers = _divider_columns(grid)
    stray_nines = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 9 and column not in dividers
    ]
    panels = _split_panels(grid)
    panel_cells = [_cells(panel) for panel in panels]
    panel_boxes = [_bbox(cells) for cells in panel_cells]
    palette = {value for row in grid for value in row}
    return {
        "errors": [],
        "height": height,
        "width": width,
        "dividers": dividers,
        "stray_nines": stray_nines,
        "panels": panels,
        "panel_cells": panel_cells,
        "panel_boxes": panel_boxes,
        "palette": palette,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid structural grammar, not curriculum extras."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors

    if len(analysis["dividers"]) != 2:
        errors.append("expected exactly two full-height color-9 divider columns")
        return errors
    if analysis["stray_nines"]:
        errors.append("color 9 may appear only in the two full-height divider columns")

    panels = analysis["panels"]
    if len(panels) != 3:
        errors.append("expected exactly three nonempty panels")
        return errors

    height = analysis["height"]
    widths = [len(panel[0]) for panel in panels]
    if widths != [height, height, height]:
        errors.append(f"panels must be equal squares matching grid height; got widths {widths} at height {height}")

    if analysis["palette"] - {0, 1, 9}:
        errors.append("task grammar uses only colors 0, 1, and divider color 9")

    for index, (panel, cells) in enumerate(zip(panels, analysis["panel_cells"]), start=1):
        if not cells:
            errors.append(f"panel {index} must contain a nonempty color-1 shape")
            continue
        if any(panel[row][column] != 1 for row, column in cells):
            errors.append(f"panel {index} foreground must be color 1")
        if not _connected4(cells):
            errors.append(f"panel {index} foreground must form one 4-connected component")
        panel_h, panel_w = len(panel), len(panel[0])
        if any(row in (0, panel_h - 1) or column in (0, panel_w - 1) for row, column in cells):
            errors.append(f"panel {index} shape must retain at least one background cell of border margin")

    query_cells = analysis["panel_cells"][2]
    if query_cells and len(query_cells) < 3:
        errors.append("query shape must contain at least three cells")

    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None:
        observed = _profile_of(grid)
        if observed != requested:
            errors.append(f"scene profile drifted from {requested!r} to {observed!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical three-square-panel, {0,1,9}-palette manifold."""
    errors = list(self_check(grid))
    if errors:
        return errors
    height = len(grid)
    width = len(grid[0])
    if height not in (7, 9):
        errors.append(f"canonical panel height is 7 or 9, got {height}")
    if width != 3 * height + 2:
        errors.append(f"canonical width must equal 3*h+2, got {(height, width)}")
    if {value for row in grid for value in row} != {0, 1, 9}:
        errors.append("canonical-like scenes use exactly palette {0,1,9}")
    return errors


def _profile_of(grid: Any) -> str | None:
    analysis = _analysis(grid)
    if analysis.get("errors") or len(analysis.get("panels", [])) != 3:
        return None
    signature = (analysis["height"], len(analysis["panel_cells"][2]))
    for name, spec in PROFILE_SPECS.items():
        if signature == spec:
            return name
    return None


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact declared profile from returned dimensions/query count."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid does not encode one of the declared scene profiles")
    return {"scene_profile": profile}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive examples cover all declared profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _orient_shape(
    cells: Iterable[tuple[int, int]], rng
) -> tuple[tuple[int, int], ...]:
    """Apply a deterministic random dihedral transform and normalize."""
    points = tuple(cells)
    turns = rng.randrange(4)
    reflect = bool(rng.randrange(2))
    transformed = []
    for row, column in points:
        rr, cc = row, -column if reflect else column
        for _ in range(turns):
            rr, cc = cc, -rr
        transformed.append((rr, cc))
    return _normalize_shape(transformed)


def _shape_is_discriminative(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = set(_normalize_shape(cells))
    if len(normalized) < 3 or not _connected4(normalized):
        return False
    box = _bbox(normalized)
    if box is None:
        return False
    r0, c0, r1, c1 = box
    shape_h, shape_w = r1 - r0 + 1, c1 - c0 + 1
    if shape_h < 3 or shape_w < 3:
        return False
    # Evaluate with one cell of margin so no intended dilation is clipped.
    shifted = {(row + 1, column + 1) for row, column in normalized}
    h, w = shape_h + 2, shape_w + 2
    cardinal = _crop_mask(_grow_cells(shifted, h, w, _CARDINAL))
    diagonal = _crop_mask(_grow_cells(shifted, h, w, _DIAGONAL_8))
    if cardinal == diagonal:
        return False
    if all(value == 1 for row in cardinal for value in row):
        return False
    return True


_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    7: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
    9: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
    13: (
        (0, 2),
        (1, 1), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
        (3, 1), (3, 2), (3, 3),
        (4, 2),
    ),
}


def _random_query_shape(rng, cell_count: int, max_span: int) -> tuple[tuple[int, int], ...]:
    """Grow a random connected polyomino with two operation-discriminating cues."""
    for _ in range(512):
        cells = {(0, 0)}
        while len(cells) < cell_count:
            row, column = rng.choice(tuple(sorted(cells)))
            dr, dc = rng.choice(_CARDINAL)
            cells.add((row + dr, column + dc))
        normalized = _normalize_shape(cells)
        box = _bbox(normalized)
        assert box is not None
        r0, c0, r1, c1 = box
        if r1 - r0 + 1 > max_span or c1 - c0 + 1 > max_span:
            continue
        if _shape_is_discriminative(normalized):
            return normalized
    fallback = _FALLBACK_SHAPES[cell_count]
    if not _shape_is_discriminative(fallback):
        raise RuntimeError(f"fallback query shape for {cell_count} cells is not discriminative")
    return fallback


def _paint_shape(panel: list[list[int]], cells: Iterable[tuple[int, int]], rng) -> None:
    normalized = _normalize_shape(cells)
    box = _bbox(normalized)
    if box is None:
        raise ValueError("cannot paint an empty shape")
    _, _, r1, c1 = box
    shape_h, shape_w = r1 + 1, c1 + 1
    # Keep one-cell border clearance on every side; the canonical examples have
    # even more margin, and this keeps the one-layer operation fully visible.
    top = rng.randint(1, len(panel) - shape_h - 1)
    left = rng.randint(1, len(panel[0]) - shape_w - 1)
    for row, column in normalized:
        panel[top + row][left + column] = 1


def _assemble(panels: list[list[list[int]]]) -> list[list[int]]:
    height = len(panels[0])
    rows: list[list[int]] = []
    for row in range(height):
        out: list[int] = []
        for index, panel in enumerate(panels):
            if index:
                out.append(9)
            out.extend(panel[row])
        rows.append(out)
    return rows


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    panel_size, query_count = PROFILE_SPECS[profile]
    rng = ctx.draw_rng(f"layout:{profile}:{difficulty or 'medium'}")

    # Smaller distractors are intentional negative evidence against the
    # canonical-only "grow the sparsest/smallest panel" shortcuts.
    first_shape = _orient_shape(((0, 0), (1, 0), (1, 1)), rng)  # L triomino
    if panel_size == 7:
        # Canonical 7x7 scenes contain 3x3 distractors (9 cells).
        second_shape = tuple((row, column) for row in range(3) for column in range(3))
    else:
        # Canonical 9x9 scenes reach 21-cell distractors.  A 5x5 block with
        # the four corners removed matches that scale while remaining visibly
        # different from the third-panel query after one cardinal growth.
        second_shape = tuple(
            (row, column)
            for row in range(5)
            for column in range(5)
            if (row, column) not in {(0, 0), (0, 4), (4, 0), (4, 4)}
        )
    second_shape = _orient_shape(second_shape, rng)
    query_shape = _orient_shape(
        _random_query_shape(rng, query_count, panel_size - 2),
        rng,
    )

    panels = [full_grid(panel_size, panel_size, 0) for _ in range(3)]
    for panel, shape in zip(panels, (first_shape, second_shape, query_shape)):
        _paint_shape(panel, shape, rng)
    grid = _assemble(panels)

    errors = self_check(grid, meta={"overrides": {"scene_profile": profile}})
    if errors:
        raise RuntimeError("generator produced an invalid scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Named plausible wrong rules and generated counterexamples
# ---------------------------------------------------------------------------


def _rival_raw_third(grid: Any) -> list[list[int]]:
    return _raw_panel_output(_split_panels(grid)[2])


def _rival_grow_first(grid: Any) -> list[list[int]]:
    return _panel_output(_split_panels(grid)[0])


def _rival_grow_second(grid: Any) -> list[list[int]]:
    return _panel_output(_split_panels(grid)[1])


def _rival_grow_sparsest(grid: Any) -> list[list[int]]:
    panels = _split_panels(grid)
    index = min(range(3), key=lambda i: (len(_cells(panels[i])), -i))
    return _panel_output(panels[index])


def _rival_grow_smallest_bbox(grid: Any) -> list[list[int]]:
    panels = _split_panels(grid)
    index = min(range(3), key=lambda i: (_bbox_area(_cells(panels[i])), -i))
    return _panel_output(panels[index])


def _rival_eight_neighbor_growth(grid: Any) -> list[list[int]]:
    return _panel_output(_split_panels(grid)[2], diagonal=True)


def _rival_fill_grown_bbox(grid: Any) -> list[list[int]]:
    true = rule_mirror(grid)
    return [[1] * len(true[0]) for _ in range(len(true))]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "raw_third_without_growth": _rival_raw_third,
    "grow_first_panel": _rival_grow_first,
    "grow_second_panel": _rival_grow_second,
    "grow_sparsest_panel": _rival_grow_sparsest,
    "grow_smallest_bbox_panel": _rival_grow_smallest_bbox,
    "eight_neighbor_growth": _rival_eight_neighbor_growth,
    "fill_grown_bbox": _rival_fill_grown_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "grow_sparsest_panel": _rival_grow_sparsest,
    "grow_smallest_bbox_panel": _rival_grow_smallest_bbox,
}


def _witness_visible_growth(grid: Any) -> bool:
    panels = _split_panels(grid)
    return len(panels) == 3 and _raw_panel_output(panels[2]) != rule_mirror(grid)


def _witness_first_is_wrong(grid: Any) -> bool:
    panels = _split_panels(grid)
    return len(panels) == 3 and _panel_output(panels[0]) != rule_mirror(grid)


def _witness_second_is_wrong(grid: Any) -> bool:
    panels = _split_panels(grid)
    return len(panels) == 3 and _panel_output(panels[1]) != rule_mirror(grid)


def _witness_query_not_sparsest(grid: Any) -> bool:
    panels = _split_panels(grid)
    if len(panels) != 3:
        return False
    counts = [len(_cells(panel)) for panel in panels]
    return counts[2] > min(counts[:2]) and _rival_grow_sparsest(grid) != rule_mirror(grid)


def _witness_query_not_smallest_bbox(grid: Any) -> bool:
    panels = _split_panels(grid)
    if len(panels) != 3:
        return False
    areas = [_bbox_area(_cells(panel)) for panel in panels]
    return areas[2] > min(areas[:2]) and _rival_grow_smallest_bbox(grid) != rule_mirror(grid)


def _witness_cardinal_not_diagonal(grid: Any) -> bool:
    return _rival_eight_neighbor_growth(grid) != rule_mirror(grid)


def _witness_growth_not_bbox_fill(grid: Any) -> bool:
    return _rival_fill_grown_bbox(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "growth_is_visible": _witness_visible_growth,
    "first_panel_is_not_query": _witness_first_is_wrong,
    "second_panel_is_not_query": _witness_second_is_wrong,
    "query_is_not_sparsest": _witness_query_not_sparsest,
    "query_is_not_smallest_bbox": _witness_query_not_smallest_bbox,
    "cardinal_growth_not_diagonal": _witness_cardinal_not_diagonal,
    "grown_shape_preserves_bbox_gaps": _witness_growth_not_bbox_fill,
}

WITNESS_RIVALS = {
    "growth_is_visible": ["raw_third_without_growth"],
    "first_panel_is_not_query": ["grow_first_panel"],
    "second_panel_is_not_query": ["grow_second_panel"],
    "query_is_not_sparsest": ["grow_sparsest_panel"],
    "query_is_not_smallest_bbox": ["grow_smallest_bbox_panel"],
    "cardinal_growth_not_diagonal": ["eight_neighbor_growth"],
    "grown_shape_preserves_bbox_gaps": ["fill_grown_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which any named plausible wrong rule survives demos."""
    reasons: list[str] = []
    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the rule domain: {exc}")
            continue
        if expected != pair.get("output"):
            reasons.append(f"pair {index} output disagrees with the third-panel cardinal-growth rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_all_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:  # contract violation must be surfaced, never hidden
            reasons.append(f"competitor {name} crashed: {exc}")
            continue
        if fits_all_demos:
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons
