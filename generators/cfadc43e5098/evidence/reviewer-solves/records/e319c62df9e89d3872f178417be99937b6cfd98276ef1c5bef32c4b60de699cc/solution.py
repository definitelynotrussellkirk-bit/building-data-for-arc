"""Visible-example-only solution for the assigned blind ARC task."""

from __future__ import annotations


def _objects(grid: list[list[int]]) -> list[dict[str, int]]:
    """Return 4-connected, single-colour objects as bounding rectangles."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict[str, int]] = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != colour:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            rows = [cell_row for cell_row, _ in cells]
            cols = [cell_col for _, cell_col in cells]
            objects.append(
                {
                    "colour": colour,
                    "top": min(rows),
                    "bottom": max(rows),
                    "left": min(cols),
                    "right": max(cols),
                }
            )

    return objects


def _overlap(first_start: int, first_end: int, second_start: int, second_end: int) -> int:
    return min(first_end, second_end) - max(first_start, second_start) + 1


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Join nearest aligned same-colour rectangles with inset colour-8 bridges."""
    output = [row[:] for row in grid]
    objects = _objects(grid)
    edges: set[tuple[int, int]] = set()

    # Each rectangle selects the nearest compatible same-colour rectangle in
    # each cardinal direction.  A compatible pair overlaps by at least three
    # cells on the perpendicular axis, allowing an inset bridge one cell away
    # from each outer edge.
    for index, source in enumerate(objects):
        for direction in ("left", "right", "up", "down"):
            candidates: list[tuple[int, int]] = []
            for other_index, target in enumerate(objects):
                if index == other_index or source["colour"] != target["colour"]:
                    continue

                if direction == "left" and target["right"] < source["left"]:
                    overlap = _overlap(
                        source["top"], source["bottom"], target["top"], target["bottom"]
                    )
                    if overlap >= 3:
                        candidates.append((source["left"] - target["right"] - 1, other_index))
                elif direction == "right" and target["left"] > source["right"]:
                    overlap = _overlap(
                        source["top"], source["bottom"], target["top"], target["bottom"]
                    )
                    if overlap >= 3:
                        candidates.append((target["left"] - source["right"] - 1, other_index))
                elif direction == "up" and target["bottom"] < source["top"]:
                    overlap = _overlap(
                        source["left"], source["right"], target["left"], target["right"]
                    )
                    if overlap >= 3:
                        candidates.append((source["top"] - target["bottom"] - 1, other_index))
                elif direction == "down" and target["top"] > source["bottom"]:
                    overlap = _overlap(
                        source["left"], source["right"], target["left"], target["right"]
                    )
                    if overlap >= 3:
                        candidates.append((target["top"] - source["bottom"] - 1, other_index))

            if candidates:
                nearest_distance = min(distance for distance, _ in candidates)
                for distance, other_index in candidates:
                    if distance == nearest_distance:
                        edges.add(tuple(sorted((index, other_index))))

    for first_index, second_index in edges:
        first = objects[first_index]
        second = objects[second_index]

        # Horizontal bridge.
        if first["right"] < second["left"] or second["right"] < first["left"]:
            top = max(first["top"], second["top"])
            bottom = min(first["bottom"], second["bottom"])
            if first["right"] < second["left"]:
                left_edge, right_edge = first["right"], second["left"]
            else:
                left_edge, right_edge = second["right"], first["left"]
            for row in range(top + 1, bottom):
                for col in range(left_edge + 1, right_edge):
                    if output[row][col] == 0:
                        output[row][col] = 8

        # Vertical bridge.
        if first["bottom"] < second["top"] or second["bottom"] < first["top"]:
            left = max(first["left"], second["left"])
            right = min(first["right"], second["right"])
            if first["bottom"] < second["top"]:
                top_edge, bottom_edge = first["bottom"], second["top"]
            else:
                top_edge, bottom_edge = second["bottom"], first["top"]
            for row in range(top_edge + 1, bottom_edge):
                for col in range(left + 1, right):
                    if output[row][col] == 0:
                        output[row][col] = 8

    return output
