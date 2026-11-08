from collections import Counter, defaultdict, deque


def _components(grid):
    """Return 4-connected non-background monochrome objects."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                current_row, current_col = todo.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    todo.append((next_row, next_col))

            min_row = min(row for row, _ in cells)
            max_row = max(row for row, _ in cells)
            min_col = min(col for _, col in cells)
            max_col = max(col for _, col in cells)
            mask = [
                [0 for _ in range(max_col - min_col + 1)]
                for _ in range(max_row - min_row + 1)
            ]
            for cell_row, cell_col in cells:
                mask[cell_row - min_row][cell_col - min_col] = 1

            objects.append({"color": color, "cells": cells, "mask": mask})

    return objects


def _hole_count(mask):
    """Count zero regions enclosed by the object inside its bounding box."""
    height = len(mask)
    width = len(mask[0])
    seen = set()
    holes = 0

    for row in range(height):
        for col in range(width):
            if mask[row][col] != 0 or (row, col) in seen:
                continue

            todo = deque([(row, col)])
            seen.add((row, col))
            touches_boundary = False
            while todo:
                current_row, current_col = todo.popleft()
                if current_row in (0, height - 1) or current_col in (0, width - 1):
                    touches_boundary = True
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if mask[next_row][next_col] != 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    todo.append((next_row, next_col))

            if not touches_boundary:
                holes += 1

    return holes


def _symmetry_signature(mask):
    """Describe intrinsic mirror/half-turn symmetry without fixing orientation."""
    height = len(mask)
    width = len(mask[0])

    horizontal = mask == list(reversed(mask))
    vertical = all(row == list(reversed(row)) for row in mask)
    reflection_count = int(horizontal) + int(vertical)

    if height == width:
        main_diagonal = all(mask[row][col] == mask[col][row]
                            for row in range(height) for col in range(width))
        anti_diagonal = all(
            mask[row][col] == mask[width - 1 - col][height - 1 - row]
            for row in range(height)
            for col in range(width)
        )
        reflection_count += int(main_diagonal) + int(anti_diagonal)

    half_turn = all(
        mask[row][col] == mask[height - 1 - row][width - 1 - col]
        for row in range(height)
        for col in range(width)
    )
    return reflection_count, half_turn


def _class_signature(obj):
    reflections, half_turn = _symmetry_signature(obj["mask"])
    return _hole_count(obj["mask"]), reflections, half_turn


def solve(grid):
    """
    Recolor the duplicated structural class among the four large objects.

    The visible examples distinguish objects by enclosed holes and intrinsic
    symmetry, rather than by exact outline.  A small four-cell object is a
    distractor; the four equal-size larger objects contain exactly one repeated
    (holes, mirror-axis count, half-turn) class.  Both members become azure (8).
    """
    objects = _components(grid)
    size_counts = Counter(len(obj["cells"]) for obj in objects)
    large_size = max(size_counts, key=lambda size: (size_counts[size], size))
    candidates = [obj for obj in objects if len(obj["cells"]) == large_size]

    by_signature = defaultdict(list)
    for obj in candidates:
        by_signature[_class_signature(obj)].append(obj)

    repeated_pairs = [group for group in by_signature.values() if len(group) == 2]
    if len(repeated_pairs) != 1:
        # The demonstrated task has one repeated class.  Refuse to invent a
        # positional tie-breaker if a malformed input violates that contract.
        return [row[:] for row in grid]

    result = [row[:] for row in grid]
    for obj in repeated_pairs[0]:
        for row, col in obj["cells"]:
            result[row][col] = 8
    return result
