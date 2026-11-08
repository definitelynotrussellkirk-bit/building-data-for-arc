"""Finite executable shortcut inventory for the 17b0 parametric lesson."""
from __future__ import annotations

NAMES = (
    "all_horizontal_triples",
    "all_three_cell_objects",
    "all_vertical_lines",
    "selectors_and_selected_candidates",
    "nearest_to_first_selector_only",
    "nearest_to_last_selector_only",
    "first_n_horizontal_candidates",
    "last_n_horizontal_candidates",
    "center_nearest_horizontal_candidate",
)

DESCRIPTIONS = {
    "all_horizontal_triples": "paint every exact horizontal triple",
    "all_three_cell_objects": "paint every exact vertical or horizontal three-cell line",
    "all_vertical_lines": "paint every vertical line regardless of exact length",
    "selectors_and_selected_candidates": "paint both selector triples and their selected horizontal targets",
    "nearest_to_first_selector_only": "use only the first exact vertical selector",
    "nearest_to_last_selector_only": "use only the last exact vertical selector",
    "first_n_horizontal_candidates": "paint the first N horizontal triples for N selectors",
    "last_n_horizontal_candidates": "paint the last N horizontal triples for N selectors",
    "center_nearest_horizontal_candidate": "paint the one horizontal triple nearest the grid center",
}


def _paint(grid, targets):
    output = [list(row) for row in grid]
    for cells in targets:
        for row, col in cells:
            output[row][col] = 2
    return output


def _is_vertical_line(cells):
    rows = sorted(row for row, _ in cells)
    cols = {col for _, col in cells}
    return len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1))


def _selected(prototype, selectors, candidates):
    result = []
    for selector in selectors:
        distances = [prototype._object_distance(selector, candidate) for candidate in candidates]
        result.append(candidates[distances.index(min(distances))])
    return result


def output(prototype, grid, name):
    if name not in NAMES:
        raise KeyError(name)
    objects, selectors, candidates = prototype._scene_objects(grid)
    selected = _selected(prototype, selectors, candidates)
    if name == "all_horizontal_triples":
        targets = candidates
    elif name == "all_three_cell_objects":
        targets = selectors + candidates
    elif name == "all_vertical_lines":
        targets = [cells for cells in objects if _is_vertical_line(cells)]
    elif name == "selectors_and_selected_candidates":
        targets = selectors + selected
    elif name == "nearest_to_first_selector_only":
        targets = selected[:1]
    elif name == "nearest_to_last_selector_only":
        targets = selected[-1:]
    elif name == "first_n_horizontal_candidates":
        targets = candidates[: len(selectors)]
    elif name == "last_n_horizontal_candidates":
        targets = candidates[-len(selectors) :]
    else:
        center = ((len(grid) - 1) / 2, (len(grid[0]) - 1) / 2)
        target = min(
            candidates,
            key=lambda cells: min(
                abs(row - center[0]) + abs(col - center[1]) for row, col in cells
            ),
        )
        targets = [target]
    return _paint(grid, targets)
