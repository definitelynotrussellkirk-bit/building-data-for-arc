from collections import Counter, deque


def _duplicated_diagonal_marker(grid):
    """Return the non-background/non-red color used by the diagonal marker pair."""
    counts = Counter(value for row in grid for value in row)
    candidates = []
    for color, count in counts.items():
        if color in (0, 2) or count != 2:
            continue
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        dr = abs(cells[0][0] - cells[1][0])
        dc = abs(cells[0][1] - cells[1][1])
        # The demonstrations distinguish the marker from singleton distractors
        # by using two equal cells on a diagonal.
        candidates.append((dr == 1 and dc == 1, color, cells))

    if not candidates:
        raise ValueError("expected a duplicated non-red marker color")
    candidates.sort(reverse=True)
    _, color, cells = candidates[0]
    return color, cells


def _marked_component(grid, marker_color, marker_cells):
    """Find the 8-connected component made of red cells and marker cells."""
    height = len(grid)
    width = len(grid[0])
    allowed = {2, marker_color}
    seen = set(marker_cells)
    queue = deque(marker_cells)

    while queue:
        r, c = queue.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if not (0 <= rr < height and 0 <= cc < width):
                    continue
                if (rr, cc) in seen or grid[rr][cc] not in allowed:
                    continue
                seen.add((rr, cc))
                queue.append((rr, cc))
    return seen


def solve(grid):
    marker_color, marker_cells = _duplicated_diagonal_marker(grid)
    excluded = _marked_component(grid, marker_color, marker_cells)

    height = len(grid)
    width = len(grid[0])
    result = [row[:] for row in grid]
    orthogonal = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0:
                continue
            red_neighbors = [
                (r + dr, c + dc)
                for dr, dc in orthogonal
                if 0 <= r + dr < height
                and 0 <= c + dc < width
                and grid[r + dr][c + dc] == 2
            ]
            if len(red_neighbors) >= 2 and all(
                cell not in excluded for cell in red_neighbors
            ):
                result[r][c] = 3

    return result
