"""Independent oracle and distribution probes for task 2636c90a673a.

This module deliberately does not call production generator helpers when deriving
outputs or morphology.  The selected Racket rule remains label authority; this
is focused reviewer tooling for regression tests and retained evidence.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter, deque


def intended_output(grid):
    """Drop row 0 and retain exactly columns whose header cell is blue (1)."""
    keep = [c for c, value in enumerate(grid[0]) if value == 1]
    return [[row[c] for c in keep] for row in grid[1:]]


def nonzero_header_rival(grid):
    """Canonical-fitting shortcut: keep every column with nonzero header."""
    keep = [c for c, value in enumerate(grid[0]) if value != 0]
    return [[row[c] for c in keep] for row in grid[1:]]


def odd_header_rival(grid):
    """Canonical-fitting shortcut: keep every column with an odd header value."""
    keep = [c for c, value in enumerate(grid[0]) if value % 2 == 1]
    return [[row[c] for c in keep] for row in grid[1:]]


def drop_header_only_rival(grid):
    """Wrong rule: remove the mask row but retain every body column."""
    return deepcopy(grid[1:])


def observed_numeric_axes(grid):
    """Recover exact pixel-observable numeric controls."""
    header = grid[0]
    return {
        "grid_h": len(grid),
        "grid_w": len(header),
        "n_keep": sum(value == 1 for value in header),
        "palette_size": len({value for row in grid for value in row}),
    }


def nonzero_component_count(grid):
    """Count 4-connected components formed by all nonzero cells."""
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
    return count


def max_same_color_component_size(grid):
    """Largest 4-connected component whose cells share one non-modal color."""
    from collections import Counter

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    seen = set()
    biggest = 0
    for start_row in range(height):
        for start_col in range(width):
            if (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            if color == background:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            size = 0
            while queue:
                row, col = queue.popleft()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (row + dr, col + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            biggest = max(biggest, size)
    return biggest


def repeated_nonzero_header_rival(grid):
    """Keep columns whose nonzero header color occurs more than once."""
    counts = Counter(grid[0])
    keep = [
        c for c, value in enumerate(grid[0])
        if value != 0 and counts[value] > 1
    ]
    return [[row[c] for c in keep] for row in grid[1:]]


def modal_nonzero_header_rival(grid):
    """Keep the most frequent nonzero header color, breaking ties by color."""
    counts = Counter(value for value in grid[0] if value != 0)
    if not counts:
        return [[] for _ in grid[1:]]
    marker = min(counts, key=lambda value: (-counts[value], value))
    keep = [c for c, value in enumerate(grid[0]) if value == marker]
    return [[row[c] for c in keep] for row in grid[1:]]
