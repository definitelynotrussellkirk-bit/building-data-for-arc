from collections import Counter
from copy import deepcopy


def _background(grid):
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    first = {value: flat.index(value) for value in counts}
    return max(counts, key=lambda value: (counts[value], -first[value]))


def _components(grid, background):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == background:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(columns), max(columns)
            part = {
                "index": len(result),
                "color": color,
                "cells": cells,
                "size": len(cells),
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            }
            part["solid"] = part["size"] == part["h"] * part["w"]
            result.append(part)
    return result


def _overlap(a1, a2, b1, b2):
    return a1 <= b2 and b1 <= a2


def _candidates(parts):
    candidates = []
    for mover in parts:
        for wall in parts:
            if mover is wall or not wall["solid"]:
                continue
            direction = None
            gap = None
            if (
                wall["r1"] > mover["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "down"
                gap = wall["r1"] - mover["r2"] - 1
            elif (
                mover["r1"] > wall["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "up"
                gap = mover["r1"] - wall["r2"] - 1
            elif (
                wall["c1"] > mover["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "right"
                gap = wall["c1"] - mover["c2"] - 1
            elif (
                mover["c1"] > wall["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "left"
                gap = mover["c1"] - wall["c2"] - 1
            if direction is not None:
                candidates.append(
                    {
                        "order": len(candidates),
                        "gap": gap,
                        "direction": direction,
                        "mover": mover,
                        "wall": wall,
                    }
                )
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["gap"],
            -candidate["wall"]["size"],
            candidate["order"],
        ),
    )


def _put(grid, row, column, value):
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = value


def solve(grid):
    """Move the nearest small object through its larger facing rectangle."""
    if not grid or not grid[0]:
        return deepcopy(grid)
    background = _background(grid)
    candidates = _candidates(_components(grid, background))
    if not candidates:
        return deepcopy(grid)

    selected = candidates[0]
    mover = selected["mover"]
    wall = selected["wall"]
    direction = selected["direction"]
    output = deepcopy(grid)
    mover_cells = [
        (row, column, grid[row][column]) for row, column in mover["cells"]
    ]
    for row, column, _ in mover_cells:
        output[row][column] = background

    if direction in ("down", "up"):
        for row in range(wall["r1"], wall["r2"] + 1):
            for column in range(mover["c1"], mover["c2"] + 1):
                _put(output, row, column, background)
        padding = max(1, mover["w"] // 2)
        for row in range(wall["r1"], wall["r2"] + 1):
            for distance in range(1, padding + 1):
                _put(output, row, wall["c1"] - distance, wall["color"])
                _put(output, row, wall["c2"] + distance, wall["color"])
        destination_row = (
            max(0, wall["r1"] - mover["h"])
            if direction == "up"
            else (
                wall["r2"] - mover["h"] + 1
                if wall["r2"] == len(grid) - 1
                else wall["r2"] + 1
            )
        )
        destination_column = mover["c1"]
    else:
        for row in range(mover["r1"], mover["r2"] + 1):
            for column in range(wall["c1"], wall["c2"] + 1):
                _put(output, row, column, background)
        padding = max(1, mover["h"] // 2)
        for column in range(wall["c1"], wall["c2"] + 1):
            for distance in range(1, padding + 1):
                _put(output, wall["r1"] - distance, column, wall["color"])
                _put(output, wall["r2"] + distance, column, wall["color"])
        destination_column = (
            max(0, wall["c1"] - mover["w"])
            if direction == "left"
            else (
                wall["c2"] - mover["w"] + 1
                if wall["c2"] == len(grid[0]) - 1
                else wall["c2"] + 1
            )
        )
        destination_row = mover["r1"]

    for row, column, color in mover_cells:
        _put(
            output,
            destination_row + row - mover["r1"],
            destination_column + column - mover["c1"],
            color,
        )
    return output
