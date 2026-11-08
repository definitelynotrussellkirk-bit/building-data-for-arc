"""Solver inferred only from the visible train examples."""

from collections import deque


_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components_of_value(grid, value):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen = set()
    components = []

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != value or (r, c) in seen:
                continue
            component = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and grid[nr][nc] == value
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def _count_zero_regions_in_box(grid, r0, r1, c0, c1):
    """Count 4-connected zero regions in an inclusive rectangle."""

    seen = set()
    count = 0
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            count += 1
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in _NEIGHBORS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        r0 <= nr <= r1
                        and c0 <= nc <= c1
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return count


def solve(grid):
    """Recolor each 4-connected 8-object by its boxed zero-region count.

    The visible examples use color 7 as the display code for a count of four.
    All zero cells remain unchanged.
    """

    if not grid:
        return []
    output = [row[:] for row in grid]

    for component in _components_of_value(grid, 8):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        region_count = _count_zero_regions_in_box(
            grid, min(rows), max(rows), min(cols), max(cols)
        )
        replacement = 7 if region_count == 4 else region_count
        for r, c in component:
            output[r][c] = replacement

    return output
