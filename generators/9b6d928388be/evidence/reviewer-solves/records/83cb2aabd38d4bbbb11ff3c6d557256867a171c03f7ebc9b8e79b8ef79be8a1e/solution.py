"""Visible-only solution for the assigned ARC puzzle."""


def _components(grid):
    """Return 4-connected, same-color non-background components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_step, col_step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + row_step
                    next_col = current_col + col_step
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            rows = [cell_row for cell_row, _ in cells]
            cols = [cell_col for _, cell_col in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )

    return result


def _is_frame(component):
    """Recognize a complete rectangular outline made from color 5."""
    if component["color"] != 5:
        return False

    top, left, bottom, right = component["bbox"]
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        return False

    border = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    return set(component["cells"]) == border


def solve(grid):
    """Move size-ranked shapes into the numbered rectangular frames."""
    output = [row[:] for row in grid]
    components = _components(grid)

    frames = [component for component in components if _is_frame(component)]
    markers = {
        component["color"]: component
        for component in components
        if component["color"] in (1, 2, 3) and len(component["cells"]) == 1
    }
    marker_ids = {id(component) for component in markers.values()}
    frame_ids = {id(component) for component in frames}

    objects = [
        component
        for component in components
        if id(component) not in frame_ids and id(component) not in marker_ids
    ]
    # The labels 1, 2, 3 denote increasing pixel count.  Equal-size objects
    # use ordinary reading order, as demonstrated by the first training pair.
    objects.sort(
        key=lambda component: (
            len(component["cells"]),
            component["bbox"][0],
            component["bbox"][1],
        )
    )

    # Remove the three loose shapes from their original locations.
    for component in objects:
        for row, col in component["cells"]:
            output[row][col] = 0

    for rank, marker in markers.items():
        marker_row, marker_col = marker["cells"][0]
        matching_frames = [
            frame
            for frame in frames
            if frame["bbox"][0] == marker_row + 1
            and frame["bbox"][1] <= marker_col <= frame["bbox"][3]
        ]
        if len(matching_frames) != 1 or not (1 <= rank <= len(objects)):
            continue

        frame = matching_frames[0]
        obj = objects[rank - 1]
        object_top, object_left, object_bottom, object_right = obj["bbox"]
        frame_top, frame_left, frame_bottom, frame_right = frame["bbox"]

        object_height = object_bottom - object_top + 1
        object_width = object_right - object_left + 1
        frame_height = frame_bottom - frame_top + 1
        frame_width = frame_right - frame_left + 1

        # Center the object's bounding box in the frame.  For an odd amount of
        # slack, the examples choose the upper/left placement.
        target_top = frame_top + (frame_height - object_height) // 2
        target_left = frame_left + (frame_width - object_width) // 2

        for row, col in obj["cells"]:
            output[target_top + row - object_top][target_left + col - object_left] = obj[
                "color"
            ]

    return output
