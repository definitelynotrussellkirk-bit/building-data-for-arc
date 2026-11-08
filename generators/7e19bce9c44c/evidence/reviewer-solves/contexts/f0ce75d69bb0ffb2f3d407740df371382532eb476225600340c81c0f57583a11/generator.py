"""Generator for ``arc_additional_puzzles_21_set5:E35``.

The input contains a small multicolour pattern surrounded by black padding.
The output is the tight bounding-box crop of every non-background cell.  The
nonzero cells do not need to form one connected or one-colour object; that is
an important part of the canonical task.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e19bce9c44c"
TASK_ID = "7e19bce9c44c"
VERSION = "3.1.0"
RULE_HASH = "36e37e8e3020"

SUMMARY = (
    "A 7-10 by 9-12 black canvas contains 7 or 8 nonzero cells in a "
    "3-4 by 3-4 tight bounding box. The content uses 2 or 3 nonzero "
    "colors, may contain multiple same-color components, and always leaves "
    "at least one black hole inside its bounding box. Crop away every all-"
    "black outer row and column, preserving the complete multicolor pattern."
)

INVARIANTS = [
    "background color is 0",
    "all nonzero content is strictly inside the canvas",
    "the tight content bbox is 3-4 rows by 3-4 columns",
    "the bbox contains exactly 7 or 8 nonzero cells and at least one black hole",
    "the nonzero content uses 2 or 3 colors; connectivity is not required",
    "default medium/hard draws reserve one sample in five for an exact "
    "canonical canvas/palette profile; caller overrides always take priority",
    "even sample_index draws are single-scene refutations: the modal colour's "
    "bbox and every same-colour component's bbox are strictly inside the "
    "content bbox, so colour- or object-limited crops give a different answer",
    "on even three-colour draws, the least-frequent colour alone reaches the "
    "top crop boundary, refuting rules that use only the two most frequent "
    "colours to choose crop bounds",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 7..10",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 9..12",
        "valid": "9..12",
    },
    "bbox_h": {
        "type": "int",
        "default": "difficulty-weighted 3..4",
        "valid": "3..4",
    },
    "bbox_w": {
        "type": "int",
        "default": "difficulty-weighted 3..4",
        "valid": "3..4",
    },
    "occupied_cells": {
        "type": "int",
        "default": "difficulty-weighted 7..8",
        "valid": "7..8",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-weighted 2..3",
        "valid": "2..3",
    },
}


_CANONICAL_PROFILE_ANCHORS = {
    "medium": {
        "grid_h": 9,
        "grid_w": 10,
        "bbox_h": 3,
        "bbox_w": 4,
        "occupied_cells": 7,
        "n_colors": 2,
    },
    "hard": {
        "grid_h": 10,
        "grid_w": 10,
        "bbox_h": 4,
        "bbox_w": 3,
        "occupied_cells": 8,
        "n_colors": 2,
    },
}


def _validate_request(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _effective_overrides(difficulty, sample_index, overrides):
    """Return caller controls plus a sparse, default-only canonical anchor.

    The branch is deliberately disabled by ANY explicit override: overrides
    describe the caller's requested experiment and must never be silently
    coupled to an internal profile.  Consecutive default draws nevertheless
    receive 20% exact-profile support in both extrapolative bands.
    """
    if overrides:
        return dict(overrides)
    # Keep exact-profile anchors on odd residues.  Every three consecutive
    # sample indexes then contains an even, non-anchor draw that can carry the
    # three-colour rival refutation below.
    if (
        difficulty in _CANONICAL_PROFILE_ANCHORS
        and sample_index % 10 in (5, 9)
    ):
        return dict(_CANONICAL_PROFILE_ANCHORS[difficulty])
    if difficulty in ("easy", "medium", "hard") and sample_index % 2 == 0:
        return {"n_colors": 3}
    return {}


def _content_mask(rng, height: int, width: int, count: int) -> list[tuple[int, int]]:
    """Return exactly ``count`` cells whose bbox is the requested rectangle."""
    anchors = {
        (0, rng.randrange(width)),
        (height - 1, rng.randrange(width)),
        (rng.randrange(height), 0),
        (rng.randrange(height), width - 1),
    }
    remaining = [
        cell
        for cell in product(range(height), range(width))
        if cell not in anchors
    ]
    rng.shuffle(remaining)
    cells = set(anchors)
    cells.update(remaining[: count - len(cells)])
    return sorted(cells)


def _discriminative_content(layout_rng, color_rng, height, width, count, palette):
    """Cell->colour map whose single scene refutes the colour/object shortcuts.

    Two-colour construction: the rightmost bbox column carries k cells of a
    less-frequent boundary colour and NOTHING else, while the other colour
    stays strictly left of it.

    Three-colour construction: a uniquely least-frequent colour is the only
    colour on the top bbox row.  The other two colours occupy only lower rows,
    with one owning the left edge and the other owning the right edge.  Thus a
    rule that computes crop bounds from only the two most frequent colours
    loses the top row.  Except for the mathematically saturated 3x3/8-cell
    profile, all three colours also own a distinct bbox side.

    Consequences, guaranteed per draw:

    - the modal colour's bbox is strictly narrower than the content bbox, so
      "crop the modal colour's cells only" answers differently;
    - every same-colour 4-connected component's bbox is strictly inside the
      content bbox, so "crop the largest single-colour object only" answers
      differently.

    Scheduled on even sample_index values, so every EXAMPLES_NEEDED=3 demo
    window (consecutive sample indices from 0) contains at least two such
    refutation demos. Raises loudly when the requested profile cannot host
    the construction (unreachable for the declared 3..4 x 3..4 / 7..8 / 2..3
    envelope; proven by the exhaustive boundary sweep in the focused test).
    """
    n_colors = len(palette)
    if n_colors == 3:
        # Keep the top boundary exclusive to the rare colour.  A saturated
        # 3x3/8-cell scene needs two top cells because the two lower rows hold
        # only six cells; all other declared profiles need one.
        rare_count = max(1, count - (height - 1) * width)
        lower_count = count - rare_count
        boundary_count = lower_count // 2
        modal_count = lower_count - boundary_count
        if not (rare_count < boundary_count <= modal_count):
            raise RuntimeError(
                f"three-colour refutation infeasible for bbox {height}x{width}, "
                f"{count} cells"
            )

        # For the ordinary one-cell rare branch, keep that cell away from the
        # left/right corners so the other colours each retain an exclusive
        # side.  The saturated rare_count=2 branch may use top corners, but the
        # ignored-colour shortcut is still refuted by the exclusive top row.
        if rare_count == 1:
            rare_cols = [layout_rng.randrange(1, width - 1)]
        else:
            rare_cols = layout_rng.sample(range(width), rare_count)

        modal_cells = {(1, 0), (height - 1, 0)}
        boundary_cells = {(1, width - 1), (height - 1, width - 1)}
        middle = [
            (row, col)
            for row in range(1, height)
            for col in range(1, width - 1)
        ]
        layout_rng.shuffle(middle)
        modal_needed = modal_count - len(modal_cells)
        boundary_needed = boundary_count - len(boundary_cells)
        if modal_needed < 0 or boundary_needed < 0:
            raise RuntimeError(
                f"three-colour side ownership infeasible for bbox "
                f"{height}x{width}, {count} cells"
            )
        modal_cells.update(middle[:modal_needed])
        boundary_cells.update(
            middle[modal_needed:modal_needed + boundary_needed]
        )
        if (
            len(modal_cells) != modal_count
            or len(boundary_cells) != boundary_count
            or modal_cells & boundary_cells
        ):
            raise RuntimeError(
                f"three-colour allocation failed for bbox {height}x{width}, "
                f"{count} cells"
            )

        modal_color, boundary_color, rare_color = palette
        assignments = {cell: modal_color for cell in modal_cells}
        assignments.update({cell: boundary_color for cell in boundary_cells})
        assignments.update({(0, col): rare_color for col in rare_cols})
        if len(assignments) != count:
            raise RuntimeError(
                f"three-colour construction produced {len(assignments)} "
                f"rather than {count} cells"
            )
        return assignments

    extras = 0
    left_capacity = height * (width - 1)
    k_min = max(1, count - left_capacity)
    # Strict modality: modal count = count - k - extras must EXCEED k.
    k_max = min(height, (count - extras - 1) // 2)
    if k_min > k_max:
        raise RuntimeError(
            f"discriminative schedule infeasible for bbox {height}x{width}, "
            f"{count} cells, {n_colors} colors"
        )
    k = layout_rng.randint(k_min, k_max)
    right_rows = layout_rng.sample(range(height), k)

    # The bbox must stay tight: rows 0 / height-1 and column 0 need occupied
    # cells; the rightmost column is anchored by the boundary cells.
    required = set()
    if 0 not in right_rows:
        required.add((0, layout_rng.randrange(width - 1)))
    if height - 1 not in right_rows:
        required.add((height - 1, layout_rng.randrange(width - 1)))
    if not any(col == 0 for _row, col in required):
        required.add((layout_rng.randrange(height), 0))
    left_cells = [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
        if (row, col) not in required
    ]
    layout_rng.shuffle(left_cells)
    chosen = set(required)
    chosen.update(left_cells[: count - k - len(required)])

    modal_color, boundary_color = palette[0], palette[1]
    assignments = {(row, width - 1): boundary_color for row in right_rows}
    left_sorted = sorted(chosen)
    if extras:
        assignments[color_rng.choice(left_sorted)] = palette[2]
    for cell in left_sorted:
        if cell not in assignments:
            assignments[cell] = modal_color
    return assignments


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    effective_overrides = _effective_overrides(
        difficulty, sample_index, overrides
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    height = ctx.draw_int_diff("grid_h", 7, 10)
    width = ctx.draw_int_diff("grid_w", 9, 12)
    bbox_h = ctx.draw_int_diff("bbox_h", 3, 4)
    bbox_w = ctx.draw_int_diff("bbox_w", 3, 4)
    occupied = ctx.draw_int_diff("occupied_cells", 7, 8)
    n_colors = ctx.draw_int_diff("n_colors", 2, 3)

    # Every declared single-axis boundary and every pairwise boundary remains
    # feasible: the smallest bbox has area 9, while occupied <= 8.
    if occupied >= bbox_h * bbox_w:
        raise ValueError("occupied_cells must leave at least one black bbox cell")

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    palette = list(
        ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})
    )

    if sample_index % 2 == 0:
        # Scheduled single-scene refutation of the modal-colour-crop and
        # largest-component-crop shortcuts (see _discriminative_content).
        assignments = _discriminative_content(
            layout_rng, color_rng, bbox_h, bbox_w, occupied, palette
        )
    else:
        cells = _content_mask(layout_rng, bbox_h, bbox_w, occupied)
        shuffled_cells = list(cells)
        color_rng.shuffle(shuffled_cells)
        assignments = {
            cell: palette[index]
            for index, cell in enumerate(shuffled_cells[:n_colors])
        }
        for cell in shuffled_cells[n_colors:]:
            assignments[cell] = color_rng.choice(palette)

    top = layout_rng.randint(1, height - bbox_h - 1)
    left = layout_rng.randint(1, width - bbox_w - 1)
    grid = full_grid(height, width, 0)
    for (row, col), color in assignments.items():
        grid[top + row][left + col] = color
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return {}, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer color 0..9"
                )
    if errors:
        return {}, errors

    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not points:
        return {}, ["grid has no nonzero content to crop"]

    top = min(row for row, _col in points)
    bottom = max(row for row, _col in points)
    left = min(col for _row, col in points)
    right = max(col for _row, col in points)
    colors = {
        grid[row][col]
        for row, col in points
    }
    analysis = {
        "grid_h": len(grid),
        "grid_w": width,
        "bbox_h": bottom - top + 1,
        "bbox_w": right - left + 1,
        "occupied_cells": len(points),
        "n_colors": len(colors),
        "top": top,
        "left": left,
        "bottom_padding": len(grid) - bottom - 1,
        "right_padding": width - right - 1,
        "bbox_area": (bottom - top + 1) * (right - left + 1),
    }
    return analysis, []


def observe_overrides(grid) -> dict[str, int]:
    analysis, errors = _analyze(grid)
    if errors:
        return {}
    return {axis: analysis[axis] for axis in AXES}


def rule_mirror(grid):
    """Pure Python mirror of the canonical ``crop-to-content`` rule."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    top = analysis["top"]
    left = analysis["left"]
    bottom = len(grid) - analysis["bottom_padding"]
    right = len(grid[0]) - analysis["right_padding"]
    return [row[left:right] for row in grid[top:bottom]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis, errors = _analyze(grid)
    if errors:
        return errors

    if not 7 <= analysis["grid_h"] <= 10:
        errors.append("canvas height must be 7..10")
    if not 9 <= analysis["grid_w"] <= 12:
        errors.append("canvas width must be 9..12")
    if not 3 <= analysis["bbox_h"] <= 4:
        errors.append("tight content bbox height must be 3..4")
    if not 3 <= analysis["bbox_w"] <= 4:
        errors.append("tight content bbox width must be 3..4")
    if not 7 <= analysis["occupied_cells"] <= 8:
        errors.append("content must contain exactly 7 or 8 nonzero cells")
    if not 2 <= analysis["n_colors"] <= 3:
        errors.append("content must use 2 or 3 nonzero colors")
    if min(
        analysis["top"],
        analysis["left"],
        analysis["bottom_padding"],
        analysis["right_padding"],
    ) < 1:
        errors.append("content must have at least one black row/column on every side")
    if analysis["occupied_cells"] >= analysis["bbox_area"]:
        errors.append("content bbox must contain at least one black hole")
    return errors


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md, v1)
# ---------------------------------------------------------------------------

def _nonzero_cells(grid):
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _components_of(cells) -> list[set]:
    """4-connected components of a cell set (pure, deterministic)."""
    remaining = set(cells)
    components = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.discard(start)
        component = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.discard((nr, nc))
                    component.add((nr, nc))
                    stack.append((nr, nc))
        components.append(component)
    return components


def strict_canonical_like(grid) -> list[str]:
    """[] when grid is a lawful instance of the canonical crop-to-content
    family for THIS task.

    All five canonical inputs use exactly 2 nonzero colours and a 3x3 / 3x4 /
    4x3 tight bbox (never 4x4). The 3-colour and 4x4 branches are deliberate
    hard-band extrapolations — lawful teaching grammar (self_check) but not
    canonical-like.
    """
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis, _ = _analyze(grid)
    if analysis["n_colors"] != 2:
        reasons.append(
            f"content uses {analysis['n_colors']} colours; every canonical "
            "input uses exactly 2"
        )
    if analysis["bbox_h"] == 4 and analysis["bbox_w"] == 4:
        reasons.append(
            "4x4 content bbox is a hard-band extrapolation; canonical bboxes "
            "are 3x3, 3x4, or 4x3"
        )
    return reasons


def _witness_multicolour_content(grid) -> bool:
    """The crop spans MULTIPLE colours — the pre-repair generator taught a
    single-colour rule, so multicolour participation is the point."""
    cells = _nonzero_cells(grid)
    return len({grid[r][c] for r, c in cells}) >= 2


def _witness_all_nonzero_disconnected(grid) -> bool:
    """The full nonzero content is NOT one 4-connected component, so
    connectivity cannot define what is cropped."""
    cells = _nonzero_cells(grid)
    return len(_components_of(cells)) >= 2 if cells else False


def _witness_split_same_colour(grid) -> bool:
    """Some single colour occurs in >=2 separate 4-connected components (the
    canonical inputs the pre-repair generator rejected as 'two objects')."""
    cells = _nonzero_cells(grid)
    by_color: dict[int, list] = {}
    for r, c in cells:
        by_color.setdefault(grid[r][c], []).append((r, c))
    return any(len(_components_of(group)) >= 2 for group in by_color.values())


def _witness_internal_hole(grid) -> bool:
    """The tight bbox keeps at least one zero cell — internal holes survive
    the crop instead of being dropped."""
    cells = _nonzero_cells(grid)
    if not cells:
        return False
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return any(
        grid[r][c] == 0
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
    )


def _two_most_frequent_cells(grid):
    """Cells belonging to the two most frequent nonzero colours.

    Ties are resolved by the smaller ARC colour value, making the rival fully
    deterministic and independently replayable.
    """
    cells = _nonzero_cells(grid)
    counts: dict[int, int] = {}
    for row, col in cells:
        color = grid[row][col]
        counts[color] = counts.get(color, 0) + 1
    kept = {
        color
        for color, _count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )[:2]
    }
    return [(row, col) for row, col in cells if grid[row][col] in kept]


def _bbox(cells):
    if not cells:
        return None
    return (
        min(row for row, _col in cells),
        max(row for row, _col in cells),
        min(col for _row, col in cells),
        max(col for _row, col in cells),
    )


def _witness_least_frequent_colour_bbox_essential(grid) -> bool:
    """Ignoring the least-frequent colour changes the crop geometry."""
    cells = _nonzero_cells(grid)
    colors = {grid[row][col] for row, col in cells}
    if len(colors) < 3:
        return False
    selected = _two_most_frequent_cells(grid)
    return _bbox(selected) != _bbox(cells)


SEMANTIC_WITNESSES = {
    "multicolour_content": _witness_multicolour_content,
    "all_nonzero_disconnected": _witness_all_nonzero_disconnected,
    "split_same_colour_component": _witness_split_same_colour,
    "internal_hole_in_bbox": _witness_internal_hole,
    "least_frequent_colour_bbox_essential":
        _witness_least_frequent_colour_bbox_essential,
}

BRANCH_WITNESSES = {
    "multicolour_content",
    "all_nonzero_disconnected",
    "split_same_colour_component",
    "internal_hole_in_bbox",
}


def _crop_to_cells(grid, cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def _competitor_largest_component_crop(grid):
    """Competing rule: crop to the LARGEST single-colour 4-connected
    component's bbox (the pre-repair single-object prior). Deterministic
    tie-break: larger size first, then topmost-leftmost cell."""
    cells = _nonzero_cells(grid)
    if not cells:
        return None
    by_color: dict[int, list] = {}
    for r, c in cells:
        by_color.setdefault(grid[r][c], []).append((r, c))
    components = [
        component
        for group in by_color.values()
        for component in _components_of(group)
    ]
    best = max(components, key=lambda comp: (len(comp), [-x for x in min(comp)]))
    return _crop_to_cells(grid, sorted(best))


def _competitor_modal_colour_crop(grid):
    """Competing rule: crop to the bbox of ONE colour only — the most
    frequent nonzero colour (ties to the smallest colour value)."""
    cells = _nonzero_cells(grid)
    if not cells:
        return None
    counts: dict[int, int] = {}
    for r, c in cells:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    top_count = max(counts.values())
    modal = min(color for color, count in counts.items() if count == top_count)
    return _crop_to_cells(
        grid, [(r, c) for r, c in cells if grid[r][c] == modal])


def _competitor_fill_holes(grid):
    """Competing rule: crop to content but FILL internal zero holes with the
    modal nonzero colour instead of preserving them."""
    cells = _nonzero_cells(grid)
    if not cells:
        return None
    counts: dict[int, int] = {}
    for r, c in cells:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    top_count = max(counts.values())
    modal = min(color for color, count in counts.items() if count == top_count)
    cropped = _crop_to_cells(grid, cells)
    return [
        [modal if value == 0 else value for value in row] for row in cropped
    ]


def _competitor_two_most_frequent_colours(grid):
    """Competing rule: use only the two most frequent colours for bounds.

    The returned crop still preserves every original cell inside those bounds,
    so this differs from simply deleting the ignored colour.  It exactly fits
    all canonical demonstrations because each has only two nonzero colours.
    """
    cells = _two_most_frequent_cells(grid)
    if not cells:
        return None
    return _crop_to_cells(grid, cells)


_TWO_MOST_FREQUENT_RIVAL = "two_most_frequent_colours_only"

SEMANTIC_RIVALS = {
    _TWO_MOST_FREQUENT_RIVAL: _competitor_two_most_frequent_colours,
}

WITNESS_RIVALS = {
    "least_frequent_colour_bbox_essential": [
        _TWO_MOST_FREQUENT_RIVAL
    ],
}

CANONICAL_SHORTCUTS = {
    _TWO_MOST_FREQUENT_RIVAL: _competitor_two_most_frequent_colours,
}

LESSON_COMPETITORS = {
    "crop the largest single-colour connected object only":
        _competitor_largest_component_crop,
    "crop the modal colour's cells only":
        _competitor_modal_colour_crop,
    "drop internal holes (fill zeros inside the crop)":
        _competitor_fill_holes,
    _TWO_MOST_FREQUENT_RIVAL: _competitor_two_most_frequent_colours,
}

# Backward-compatible private name used by the original implementation.
_LESSON_COMPETITORS = LESSON_COMPETITORS


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos uniquely determine the query answer.

    A competing rule consistent with EVERY demo that answers the query
    differently makes the lesson ambiguous. Pure: no mutation, no RNG."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            mirrored = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if mirrored != demo["output"]:
            reasons.append(
                f"demo {index} output does not match crop-to-content"
            )
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' is consistent with every demo but "
                "answers the query differently"
            )
    return reasons
