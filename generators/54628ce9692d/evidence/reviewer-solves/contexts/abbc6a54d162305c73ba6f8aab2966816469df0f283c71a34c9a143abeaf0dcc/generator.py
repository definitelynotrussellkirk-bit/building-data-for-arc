"""Generator for ARC task e9fc42f2 / rule family 54628ce9692d.

The input contains two to four separated multicolor pieces.  Color 1 is
the body color.  A marker color occurring on exactly two different pieces
defines a docking edge: assemble those pieces with the equal markers
cardinally adjacent, then crop the completed assembly.  The paired marker
colors form a tree; at most one additional marker is unmatched.

The five published lessons demonstrate five different irregular piece
families and docking trees.  This generator preserves those answer-bearing
profiles while varying scatter, all global D4 symmetries, the modal
background, and marker-color names.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "54628ce9692d"
TASK_ID = "54628ce9692d"
VERSION = "3.0.0"
RULE_HASH = "9b6d1153ebca"

SUMMARY = (
    "A modal-background 13x13 grid contains 2..4 separated irregular "
    "color-1 pieces. Marker colors that occur exactly twice, on different "
    "pieces, form a connected docking tree. For each pair, infer the "
    "outward direction of the first marker and place the other marker one "
    "cell beyond it. Assemble every piece without overlap and crop to the "
    "completed multicolor object. One extra unmatched marker may remain."
)

INVARIANTS = [
    "the input is 13x13 with a unique modal background in colors 2..9",
    "there are exactly 2..4 separated irregular multicolor pieces",
    "piece bodies use color 1 and every piece has at least one marker",
    "exactly n_pieces-1 marker colors are paired across different pieces",
    "paired marker edges form a connected tree; at most one marker is unmatched",
    "the inferred docking placement preserves every cell without overlap",
    "the piece shapes and marker-equality topology match a published profile",
]

AXES = {
    "n_pieces": {
        "type": "int",
        "default": "uniform 2..4",
        "valid": "2..4",
    },
    "background_color": {
        "type": "int",
        "default": "uniform 2..9",
        "valid": "2..9",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_KING = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

# Each entry is (original_top, original_left, local_nonbackground_cells).
# These are the five unique published input profiles.  The augmented
# canonical row intentionally repeats the same five lessons.
_PROFILE_PIECES = (
    (
        (
            0,
            2,
            (
                (0, 2, 1),
                (1, 2, 1),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 1),
                (2, 3, 1),
                (2, 4, 1),
                (3, 2, 1),
                (4, 2, 3),
            ),
        ),
        (
            7,
            7,
            (
                (0, 0, 1),
                (0, 1, 3),
                (0, 2, 1),
                (0, 3, 1),
                (1, 0, 1),
                (1, 3, 8),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 1),
                (2, 3, 1),
            ),
        ),
    ),
    (
        (
            1,
            1,
            (
                (0, 1, 1),
                (0, 2, 3),
                (0, 3, 1),
                (1, 0, 1),
                (1, 1, 1),
                (1, 3, 1),
                (1, 4, 1),
                (2, 0, 1),
                (2, 4, 1),
                (3, 0, 1),
                (3, 1, 1),
                (3, 3, 1),
                (3, 4, 1),
                (4, 1, 1),
                (4, 2, 1),
                (4, 3, 1),
            ),
        ),
        (
            3,
            7,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (1, 0, 8),
                (1, 2, 1),
                (2, 0, 1),
                (2, 1, 3),
                (2, 2, 1),
            ),
        ),
        (
            7,
            4,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (0, 3, 1),
                (0, 4, 1),
                (0, 5, 1),
                (1, 5, 8),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 1),
                (2, 3, 1),
                (2, 4, 1),
                (2, 5, 1),
            ),
        ),
    ),
    (
        (
            1,
            1,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (1, 0, 1),
                (1, 2, 4),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 1),
            ),
        ),
        (
            1,
            8,
            (
                (0, 0, 1),
                (0, 1, 8),
                (0, 2, 1),
                (1, 0, 1),
                (1, 2, 1),
                (2, 0, 1),
                (2, 2, 1),
                (3, 0, 1),
                (3, 2, 1),
                (4, 0, 1),
                (4, 1, 3),
                (4, 2, 1),
            ),
        ),
        (
            5,
            3,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (1, 0, 4),
                (1, 2, 1),
                (2, 0, 1),
                (2, 1, 8),
                (2, 2, 1),
            ),
        ),
    ),
    (
        (
            1,
            1,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (0, 3, 1),
                (1, 1, 1),
                (2, 0, 1),
                (2, 1, 3),
                (2, 2, 1),
                (2, 3, 1),
            ),
        ),
        (
            3,
            9,
            (
                (0, 0, 1),
                (0, 1, 3),
                (0, 2, 1),
                (1, 0, 1),
                (1, 2, 1),
                (2, 0, 8),
                (2, 2, 1),
                (3, 0, 1),
                (3, 2, 1),
                (4, 0, 1),
                (4, 2, 1),
                (5, 0, 1),
                (5, 2, 1),
                (6, 0, 1),
                (6, 2, 4),
                (7, 0, 1),
                (7, 1, 1),
                (7, 2, 1),
            ),
        ),
        (
            5,
            4,
            (
                (0, 0, 1),
                (0, 2, 1),
                (1, 0, 1),
                (1, 2, 8),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 1),
                (3, 1, 1),
            ),
        ),
    ),
    (
        (
            1,
            0,
            (
                (0, 1, 1),
                (0, 3, 1),
                (0, 4, 1),
                (1, 1, 1),
                (1, 2, 1),
                (1, 3, 1),
                (1, 4, 4),
                (2, 0, 1),
                (2, 1, 3),
                (2, 2, 1),
                (2, 3, 1),
                (2, 4, 1),
            ),
        ),
        (
            2,
            8,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 8),
                (0, 3, 1),
                (1, 1, 1),
                (1, 2, 1),
                (2, 1, 1),
                (2, 2, 1),
            ),
        ),
        (
            5,
            2,
            (
                (0, 0, 1),
                (0, 1, 1),
                (0, 2, 1),
                (0, 3, 1),
                (0, 4, 1),
                (1, 0, 4),
                (1, 4, 1),
                (2, 0, 1),
                (2, 1, 1),
                (2, 2, 8),
                (2, 3, 1),
                (2, 4, 1),
            ),
        ),
        (
            7,
            8,
            (
                (0, 1, 1),
                (0, 2, 3),
                (0, 3, 1),
                (1, 0, 1),
                (1, 1, 1),
                (1, 2, 1),
                (1, 3, 1),
                (2, 0, 1),
                (2, 3, 1),
                (3, 0, 1),
                (3, 3, 1),
                (4, 0, 1),
                (4, 3, 1),
            ),
        ),
    ),
)

_PROFILE_INDEXES_BY_COUNT = {
    2: (0,),
    3: (1, 2, 3),
    4: (4,),
}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    bounds = {
        "n_pieces": (2, 4),
        "background_color": (2, 9),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be a literal integer (not bool)")
        lower, upper = bounds[name]
        if not lower <= value <= upper:
            raise ValueError(f"{name} must be in {lower}..{upper}")


def _coerce_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or len(grid) != 13:
        return None, ["grid must have exactly 13 rows"]
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != 13:
            errors.append(f"row {row_index} must have exactly 13 cells")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _components8(grid, background):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current = stack.pop()
                component.append(current)
                for delta_row, delta_col in _KING:
                    neighbor = (
                        current[0] + delta_row,
                        current[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] != background
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(component)))
    return tuple(sorted(components, key=_component_sort_key))


def _component_sort_key(component):
    top = min(row for row, _col in component)
    left = min(col for _row, col in component)
    return top, left


def _bbox(component):
    rows = [row for row, _col in component]
    cols = [col for _row, col in component]
    return min(rows), min(cols), max(rows), max(cols)


def _transform_point(row, col, height, width, transform):
    if transform >= 4:
        col = width - 1 - col
    for _turn in range(transform % 4):
        row, col = col, height - 1 - row
        height, width = width, height
    return row, col, height, width


def _transform_cells(cells, transform):
    height = 1 + max(row for row, _col, _value in cells)
    width = 1 + max(col for _row, col, _value in cells)
    transformed = []
    out_height = height
    out_width = width
    for row, col, value in cells:
        row, col, out_height, out_width = _transform_point(
            row,
            col,
            height,
            width,
            transform,
        )
        transformed.append((row, col, value))
    top = min(row for row, _col, _value in transformed)
    left = min(col for _row, col, _value in transformed)
    return tuple(sorted(
        (row - top, col - left, value)
        for row, col, value in transformed
    ))


def _profile_signature(components, grid, background):
    marker_colors = sorted({
        grid[row][col]
        for component in components
        for row, col in component
        if grid[row][col] not in (background, 1)
    })
    if not marker_colors:
        return None

    component_cells = []
    for component in components:
        top, left, _bottom, _right = _bbox(component)
        component_cells.append(tuple(
            (row - top, col - left, grid[row][col])
            for row, col in component
        ))

    candidates = []
    for transform in range(8):
        transformed_components = [
            _transform_cells(cells, transform)
            for cells in component_cells
        ]
        for role_order in permutations(range(len(marker_colors))):
            role_by_color = {
                color: role_order[index] + 2
                for index, color in enumerate(marker_colors)
            }
            piece_signatures = []
            for cells in transformed_components:
                height = 1 + max(row for row, _col, _value in cells)
                width = 1 + max(col for _row, col, _value in cells)
                values = {
                    (row, col): (
                        1 if value == 1 else role_by_color[value]
                    )
                    for row, col, value in cells
                }
                flat = tuple(
                    values.get((row, col), 0)
                    for row in range(height)
                    for col in range(width)
                )
                piece_signatures.append((height, width, flat))
            candidates.append((
                len(components),
                len(marker_colors),
                tuple(sorted(piece_signatures)),
            ))
    return min(candidates)


def _port_direction(component, local_row, local_col):
    top, left, bottom, right = _bbox(component)
    local_cells = {
        (row - top, col - left) for row, col in component
    }
    height = bottom - top + 1
    width = right - left + 1
    best_score, best_row, best_col = -1, 0, 0
    for delta_row, delta_col in _CARDINAL:
        neighbor = (
            local_row + delta_row,
            local_col + delta_col,
        )
        if neighbor in local_cells:
            continue
        score = 0
        if (
            local_row - delta_row,
            local_col - delta_col,
        ) in local_cells:
            score += 10
        if delta_row == -1 and local_row == 0:
            score += 5
        if delta_row == 1 and local_row == height - 1:
            score += 5
        if delta_col == -1 and local_col == 0:
            score += 5
        if delta_col == 1 and local_col == width - 1:
            score += 5
        if score > best_score:
            best_score, best_row, best_col = (
                score,
                delta_row,
                delta_col,
            )
    return best_score, best_row, best_col


def _marker_records(grid, background, components):
    records = []
    for component_index, component in enumerate(components):
        top, left, _bottom, _right = _bbox(component)
        for row, col in component:
            value = grid[row][col]
            if value == 1:
                continue
            score, delta_row, delta_col = _port_direction(
                component,
                row - top,
                col - left,
            )
            records.append({
                "color": value,
                "component": component_index,
                "local_row": row - top,
                "local_col": col - left,
                "delta_row": delta_row,
                "delta_col": delta_col,
                "score": score,
            })
    return tuple(records)


def _paired_edges(marker_records):
    by_color = defaultdict(list)
    for marker in marker_records:
        by_color[marker["color"]].append(marker)
    return tuple(
        (color, markers[0], markers[1])
        for color, markers in sorted(by_color.items())
        if len(markers) == 2
    )


def _placements(component_count, edges, marker_step=1):
    placements = {0: (0, 0)} if component_count else {}
    for _step in range(3 * max(1, component_count)):
        for _color, first, second in edges:
            first_id = first["component"]
            second_id = second["component"]
            if first_id in placements and second_id not in placements:
                from_row, from_col = placements[first_id]
                placements[second_id] = (
                    from_row
                    + first["local_row"]
                    + marker_step * first["delta_row"]
                    - second["local_row"],
                    from_col
                    + first["local_col"]
                    + marker_step * first["delta_col"]
                    - second["local_col"],
                )
            if second_id in placements and first_id not in placements:
                from_row, from_col = placements[second_id]
                placements[first_id] = (
                    from_row
                    + second["local_row"]
                    + marker_step * second["delta_row"]
                    - first["local_row"],
                    from_col
                    + second["local_col"]
                    + marker_step * second["delta_col"]
                    - first["local_col"],
                )
    return placements


def _placed_cells(grid, components, placements):
    placed = []
    for component_index, component in enumerate(components):
        origin_row, origin_col = placements[component_index]
        top, left, _bottom, _right = _bbox(component)
        for row, col in component:
            placed.append((
                origin_row + row - top,
                origin_col + col - left,
                grid[row][col],
            ))
    return tuple(placed)


def _render_crop(placed_cells, background):
    top = min(row for row, _col, _value in placed_cells)
    left = min(col for _row, col, _value in placed_cells)
    bottom = max(row for row, _col, _value in placed_cells)
    right = max(col for _row, col, _value in placed_cells)
    output = full_grid(
        bottom - top + 1,
        right - left + 1,
        background,
    )
    for row, col, value in placed_cells:
        output[row - top][col - left] = value
    return output


def _scene_analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        return None, {}, errors

    counts = Counter(value for row in coerced for value in row)
    max_count = max(counts.values())
    modes = [color for color, count in counts.items() if count == max_count]
    if len(modes) != 1:
        return coerced, {}, ["background color must be a unique mode"]
    background = modes[0]
    if background not in range(2, 10):
        errors.append("background color must be in 2..9")

    components = _components8(coerced, background)
    if not 2 <= len(components) <= 4:
        errors.append("scene must contain exactly 2..4 pieces")

    marker_records = _marker_records(coerced, background, components)
    markers_by_color = defaultdict(list)
    component_marker_counts = Counter()
    for marker in marker_records:
        markers_by_color[marker["color"]].append(marker)
        component_marker_counts[marker["component"]] += 1
        if marker["color"] not in range(2, 10):
            errors.append("marker colors must be in 2..9")
        if marker["score"] < 5:
            errors.append("every marker must have a supported outward port")

    for component_index, component in enumerate(components):
        values = Counter(coerced[row][col] for row, col in component)
        if not 8 <= len(component) <= 18:
            errors.append("each piece must contain 8..18 cells")
        if values[1] <= len(component) // 2:
            errors.append("color 1 must be the majority body of every piece")
        if component_marker_counts[component_index] < 1:
            errors.append("every piece must contain at least one marker")

    paired_colors = [
        color
        for color, markers in markers_by_color.items()
        if len(markers) == 2
    ]
    unmatched_colors = [
        color
        for color, markers in markers_by_color.items()
        if len(markers) == 1
    ]
    invalid_counts = [
        color
        for color, markers in markers_by_color.items()
        if len(markers) not in (1, 2)
    ]
    if invalid_counts:
        errors.append("marker colors may occur only once or twice")
    if len(paired_colors) != max(0, len(components) - 1):
        errors.append("paired marker colors must define exactly n-1 edges")
    if len(unmatched_colors) > 1:
        errors.append("at most one marker color may be unmatched")
    for color in paired_colors:
        first, second = markers_by_color[color]
        if first["component"] == second["component"]:
            errors.append("paired markers must lie on different pieces")

    graph = {index: set() for index in range(len(components))}
    for color in paired_colors:
        first, second = markers_by_color[color]
        graph[first["component"]].add(second["component"])
        graph[second["component"]].add(first["component"])
    reached = set()
    stack = [0] if components else []
    while stack:
        current = stack.pop()
        if current in reached:
            continue
        reached.add(current)
        stack.extend(graph[current] - reached)
    if len(reached) != len(components):
        errors.append("paired marker graph must connect every piece")

    signature = _profile_signature(components, coerced, background)
    profile_index = _PROFILE_SIGNATURE_TO_INDEX.get(signature)
    if profile_index is None:
        errors.append("piece morphology/topology is not a published profile")

    edges = _paired_edges(marker_records)
    placements = _placements(len(components), edges)
    placed_cells = ()
    if len(placements) != len(components):
        errors.append("docking edges failed to place every piece")
    else:
        placed_cells = _placed_cells(coerced, components, placements)
        coordinates = [
            (row, col) for row, col, _value in placed_cells
        ]
        if len(coordinates) != len(set(coordinates)):
            errors.append("docking placements must not overlap")

    features = {
        "background_color": background,
        "n_pieces": len(components),
        "components": components,
        "markers": marker_records,
        "edges": edges,
        "placements": placements,
        "placed_cells": placed_cells,
        "profile_index": profile_index,
        "signature": signature,
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Return structural/semantic errors for a proposed training lesson."""
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    """Recover every declared exact axis from a returned grid."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "n_pieces": features["n_pieces"],
        "background_color": features["background_color"],
    }


def rule_mirror(grid):
    """Apply an independent Python mirror of the canonical Racket rule."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid docking lesson: " + "; ".join(errors))
    return _render_crop(
        features["placed_cells"],
        features["background_color"],
    )


def strict_canonical_like(grid):
    """Accept exactly the task-local canonical morphology/topology manifold."""
    return self_check(grid)


def _crop_scattered_pieces(grid):
    """Plausible shortcut: crop the scattered scene without assembling it."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid docking lesson: " + "; ".join(errors))
    cells = tuple(
        (row, col, coerced[row][col])
        for component in features["components"]
        for row, col in component
    )
    return _render_crop(cells, features["background_color"])


def _one_cell_gap_docking(grid):
    """Nearby rival: preserve the docking tree but leave one blank cell."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid docking lesson: " + "; ".join(errors))
    placements = _placements(
        len(features["components"]),
        features["edges"],
        marker_step=2,
    )
    cells = _placed_cells(coerced, features["components"], placements)
    return _render_crop(cells, features["background_color"])


def _pieces_require_assembly(grid):
    try:
        return _crop_scattered_pieces(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _paired_markers_touch(grid):
    try:
        return _one_cell_gap_docking(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _labeled_pair_errors(pair, label):
    if not isinstance(pair, dict):
        return [f"{label} must be a labeled pair"]
    if "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output"]
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError) as exc:
        return [f"{label} input is not canonical-like: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output differs from the selected rule"]
    return []


def lesson_identifiable(demos, query):
    """Check labels and reject declared alternatives that survive demos."""
    reasons = []
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a sequence"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"at least {EXAMPLES_NEEDED} demonstrations are required"
        )
    for index, pair in enumerate(demos):
        reasons.extend(_labeled_pair_errors(pair, f"demo {index}"))
    reasons.extend(_labeled_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except (TypeError, ValueError) as exc:
            reasons.append(f"competitor {name} failed: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons


EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SEMANTIC_RIVALS = {
    "crop_scattered_pieces": _crop_scattered_pieces,
    "one_cell_gap_docking": _one_cell_gap_docking,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {}
SEMANTIC_WITNESSES = {
    "pieces_require_assembly": _pieces_require_assembly,
    "paired_markers_touch": _paired_markers_touch,
}
WITNESS_RIVALS = {
    "pieces_require_assembly": ["crop_scattered_pieces"],
    "paired_markers_touch": ["one_cell_gap_docking"],
}


def canonical_profile_index(grid):
    """Return the published profile index after nuisance normalization."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return features["profile_index"]


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _profile_grid(profile_index):
    grid = full_grid(13, 13, 2)
    for top, left, cells in _PROFILE_PIECES[profile_index]:
        for row, col, value in cells:
            grid[top + row][left + col] = value
    return grid


def _fallback_origins(profile_index, transform):
    origins = []
    for top, left, cells in _PROFILE_PIECES[profile_index]:
        global_cells = []
        for local_row, local_col, _value in cells:
            row, col, _height, _width = _transform_point(
                top + local_row,
                left + local_col,
                13,
                13,
                transform,
            )
            global_cells.append((row, col))
        origins.append((
            min(row for row, _col in global_cells),
            min(col for _row, col in global_cells),
        ))
    return tuple(origins)


def _pieces_are_separate(first, second):
    for first_row, first_col in first:
        for second_row, second_col in second:
            if (
                abs(first_row - second_row) <= 1
                and abs(first_col - second_col) <= 1
            ):
                return False
    return True


def _scatter_origins(pieces, rng):
    """Place every piece; return None instead of silently dropping one."""
    indexes = list(range(len(pieces)))
    indexes.sort(
        key=lambda index: (
            -len(pieces[index]),
            -(
                (1 + max(row for row, _col, _value in pieces[index]))
                * (1 + max(col for _row, col, _value in pieces[index]))
            ),
        )
    )
    candidates = {}
    for index, cells in enumerate(pieces):
        height = 1 + max(row for row, _col, _value in cells)
        width = 1 + max(col for _row, col, _value in cells)
        choices = [
            (top, left)
            for top in range(14 - height)
            for left in range(14 - width)
        ]
        rng.shuffle(choices)
        candidates[index] = choices

    origins = [None] * len(pieces)
    placed_sets = []
    node_budget = 40_000

    def search(depth):
        nonlocal node_budget
        if depth == len(indexes):
            return True
        index = indexes[depth]
        cells = pieces[index]
        for top, left in candidates[index]:
            node_budget -= 1
            if node_budget < 0:
                return False
            absolute = {
                (top + row, left + col)
                for row, col, _value in cells
            }
            if all(
                _pieces_are_separate(absolute, previous)
                for previous in placed_sets
            ):
                origins[index] = (top, left)
                placed_sets.append(absolute)
                if search(depth + 1):
                    return True
                placed_sets.pop()
                origins[index] = None
        return False

    if not search(0):
        return None
    return tuple(origins)


def _draw_profile(profile_index, background, transform, rng):
    pieces = tuple(
        _transform_cells(cells, transform)
        for _top, _left, cells in _PROFILE_PIECES[profile_index]
    )
    origins = _scatter_origins(pieces, rng)
    if origins is None:
        origins = _fallback_origins(profile_index, transform)

    old_marker_colors = sorted({
        value
        for cells in pieces
        for _row, _col, value in cells
        if value != 1
    })
    palette = [
        color
        for color in range(2, 10)
        if color != background
    ]
    replacement_colors = rng.sample(palette, len(old_marker_colors))
    color_map = dict(zip(old_marker_colors, replacement_colors))

    grid = full_grid(13, 13, background)
    for (top, left), cells in zip(origins, pieces):
        for row, col, value in cells:
            grid[top + row][left + col] = (
                1 if value == 1 else color_map[value]
            )
    return grid


# Build role-normalized profile signatures only after all helpers exist.
_PROFILE_SIGNATURE_TO_INDEX = {}
for _profile_index in range(len(_PROFILE_PIECES)):
    _grid = _profile_grid(_profile_index)
    _components = _components8(_grid, 2)
    _signature = _profile_signature(_components, _grid, 2)
    _previous = _PROFILE_SIGNATURE_TO_INDEX.setdefault(
        _signature,
        _profile_index,
    )
    if _previous != _profile_index:
        raise AssertionError("published docking profile signatures overlap")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, fresh, semantically validated input."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_pieces = ctx.draw_int("n_pieces", 2, 4)
    background = ctx.draw_int("background_color", 2, 9)

    profile_options = _PROFILE_INDEXES_BY_COUNT[n_pieces]
    profile_index = ctx.draw_rng(
        f"profile|{difficulty or 'medium'}"
    ).choice(profile_options)
    transform = ctx.draw_rng("global_d4").randrange(8)
    grid = _draw_profile(
        profile_index,
        background,
        transform,
        ctx.draw_rng("scatter_and_palette"),
    )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "n_pieces": n_pieces,
        "background_color": background,
    }
    if observed != expected:
        raise AssertionError(
            f"returned axes {observed!r} do not match {expected!r}"
        )
    return grid
