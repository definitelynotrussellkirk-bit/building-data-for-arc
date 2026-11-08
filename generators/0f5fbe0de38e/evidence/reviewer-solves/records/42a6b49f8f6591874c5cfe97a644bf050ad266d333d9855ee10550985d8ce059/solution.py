from __future__ import annotations

from collections import Counter
from copy import deepcopy


DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = DIR4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components(grid, background, *, same_color, directions):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == background or (row, column) in seen:
                continue
            todo = [(row, column)]
            seen.add((row, column))
            cells = []
            while todo:
                current_row, current_column = todo.pop()
                cells.append((current_row, current_column))
                for dr, dc in directions:
                    nr, nc = current_row + dr, current_column + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] == background:
                        continue
                    if same_color and grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    todo.append((nr, nc))
            r1, c1, r2, c2 = _bbox(cells)
            result.append(
                {
                    "cells": tuple(cells),
                    "cell_set": frozenset(cells),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "h": r2 - r1 + 1,
                    "w": c2 - c1 + 1,
                    "size": len(cells),
                    "color": color if same_color else None,
                    "colors": {grid[r][c] for r, c in cells},
                }
            )
    return result


def _transform(position, transform):
    row, column = position
    if transform == 0:  # identity
        return row, column
    if transform == 1:  # rotate clockwise
        return column, 2 - row
    if transform == 2:
        return 2 - row, 2 - column
    if transform == 3:
        return 2 - column, row
    if transform == 4:  # reflect left/right
        return row, 2 - column
    if transform == 5:  # reflect top/bottom
        return 2 - row, column
    if transform == 6:  # transpose
        return column, row
    return 2 - column, 2 - row


def _gap_distance(first, second):
    row_gap = max(
        0,
        max(first["r1"], second["r1"])
        - min(first["r2"], second["r2"])
        - 1,
    )
    column_gap = max(
        0,
        max(first["c1"], second["c1"])
        - min(first["c2"], second["c2"])
        - 1,
    )
    return row_gap + column_gap


def _greedy_pairs(objects):
    ordered = sorted(objects, key=lambda item: 1000 * item["r1"] + item["c1"])
    candidates = []
    for first_index in range(len(ordered)):
        for second_index in range(first_index + 1, len(ordered)):
            if ordered[first_index]["color"] == ordered[second_index]["color"]:
                continue
            candidates.append(
                (
                    _gap_distance(ordered[first_index], ordered[second_index]),
                    first_index,
                    second_index,
                )
            )
    candidates.sort(key=lambda row: row[0])
    used = set()
    pairs = []
    for _distance, first_index, second_index in candidates:
        if first_index in used or second_index in used:
            continue
        used.update((first_index, second_index))
        pairs.append((ordered[first_index], ordered[second_index]))
    return pairs


def _placement(marker_positions, first, second):
    if first["h"] != first["w"] or (first["h"], first["w"]) != (
        second["h"],
        second["w"],
    ):
        return None
    scale = first["h"]
    for transform in range(8):
        transformed = tuple(_transform(position, transform) for position in marker_positions)
        for left, right in ((first, second), (second, first)):
            top_a = left["r1"] - transformed[0][0] * scale
            left_a = left["c1"] - transformed[0][1] * scale
            top_b = right["r1"] - transformed[1][0] * scale
            left_b = right["c1"] - transformed[1][1] * scale
            if (top_a, left_a) == (top_b, left_b):
                return top_a, left_a, transform, scale
    return None


def solve(grid):
    output = deepcopy(grid)
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    multicolor_components = _components(
        grid, background, same_color=False, directions=DIR8
    )
    template_candidates = [
        component
        for component in multicolor_components
        if len(component["colors"]) >= 3
        and component["h"] == 3
        and component["w"] == 3
    ]
    if not template_candidates:
        return output
    template = min(
        template_candidates,
        key=lambda component: (
            component["size"],
            component["r1"],
            component["c1"],
        ),
    )

    counts = Counter(grid[row][column] for row, column in template["cells"])
    fill_color = counts.most_common(1)[0][0]
    marker_cells = [
        (row, column)
        for row, column in template["cells"]
        if grid[row][column] != fill_color
    ]
    if len(marker_cells) != 2:
        return output
    marker_positions = tuple(
        (row - template["r1"], column - template["c1"])
        for row, column in marker_cells
    )
    marker_colors = {grid[row][column] for row, column in marker_cells}
    fill_positions = tuple(
        (row - template["r1"], column - template["c1"])
        for row, column in template["cells"]
        if grid[row][column] == fill_color
    )

    same_color_components = _components(
        grid, background, same_color=True, directions=DIR4
    )
    marker_objects = [
        component
        for component in same_color_components
        if component["color"] in marker_colors
        and template["cell_set"].isdisjoint(component["cell_set"])
    ]

    height, width = len(grid), len(grid[0])
    for first, second in _greedy_pairs(marker_objects):
        placement = _placement(marker_positions, first, second)
        if placement is None:
            continue
        top, left, transform, scale = placement
        for position in fill_positions:
            transformed_row, transformed_column = _transform(position, transform)
            for row in range(top + transformed_row * scale, top + (transformed_row + 1) * scale):
                for column in range(
                    left + transformed_column * scale,
                    left + (transformed_column + 1) * scale,
                ):
                    if 0 <= row < height and 0 <= column < width:
                        output[row][column] = fill_color
    return output
