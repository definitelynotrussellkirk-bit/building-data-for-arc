from collections import Counter, deque


def _components(grid):
    height = len(grid)
    width = len(grid[0]) if grid else 0
    seen = set()
    parts = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + delta_row, current_col + delta_col)
                    neighbor_row, neighbor_col = neighbor
                    if (
                        0 <= neighbor_row < height
                        and 0 <= neighbor_col < width
                        and neighbor not in seen
                        and grid[neighbor_row][neighbor_col] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            parts.append(cells)
    return parts


def solve(grid):
    """Encode the largest colored object as a cyan column-count histogram."""
    parts = _components(grid)
    if not parts:
        return []
    target = max(parts, key=len)
    left = min(col for _, col in target)
    right = max(col for _, col in target)
    counts_by_column = Counter(col for _, col in target)
    counts = [counts_by_column[col] for col in range(left, right + 1)]
    output_height = max(counts)
    return [
        [8 if row < count else 0 for count in counts]
        for row in range(output_height)
    ]
