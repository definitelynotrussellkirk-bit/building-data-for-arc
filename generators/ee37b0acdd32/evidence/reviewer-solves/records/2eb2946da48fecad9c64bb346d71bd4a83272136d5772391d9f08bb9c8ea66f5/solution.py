from collections import deque


def solve(grid):
    """Keep the chain of colored components joining marker 1 to marker 2.

    Nonzero cells are partitioned into 4-connected, same-color components.
    Components that touch orthogonally form a graph.  The examples show one
    intended route from the component containing 1 to the component containing
    2; all cells on that shortest route become 8 and everything else becomes 0.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    component_at = [[-1] * width for _ in range(height)]
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or component_at[row][col] != -1:
                continue

            component_id = len(components)
            cells = []
            queue = deque([(row, col)])
            component_at[row][col] = component_id

            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if component_at[next_row][next_col] != -1:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    component_at[next_row][next_col] = component_id
                    queue.append((next_row, next_col))

            components.append({"color": color, "cells": cells})

    adjacency = [set() for _ in components]
    for row in range(height):
        for col in range(width):
            first = component_at[row][col]
            if first == -1:
                continue
            for delta_row, delta_col in ((1, 0), (0, 1)):
                next_row = row + delta_row
                next_col = col + delta_col
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                second = component_at[next_row][next_col]
                if second == -1 or second == first:
                    continue
                adjacency[first].add(second)
                adjacency[second].add(first)

    starts = [index for index, component in enumerate(components) if component["color"] == 1]
    goals = {index for index, component in enumerate(components) if component["color"] == 2}
    if not starts or not goals:
        return [[0] * width for _ in range(height)]

    parent = {}
    queue = deque(starts)
    for start in starts:
        parent[start] = None

    goal = None
    while queue:
        current = queue.popleft()
        if current in goals:
            goal = current
            break
        for neighbor in sorted(adjacency[current]):
            if neighbor in parent:
                continue
            parent[neighbor] = current
            queue.append(neighbor)

    if goal is None:
        return [[0] * width for _ in range(height)]

    path = set()
    current = goal
    while current is not None:
        path.add(current)
        current = parent[current]

    output = [[0] * width for _ in range(height)]
    for component_id in path:
        for row, col in components[component_id]["cells"]:
            output[row][col] = 8
    return output
