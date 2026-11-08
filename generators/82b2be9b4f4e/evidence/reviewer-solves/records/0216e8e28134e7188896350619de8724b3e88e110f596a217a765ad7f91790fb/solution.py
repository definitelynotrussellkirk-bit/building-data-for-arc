from collections import Counter, deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    parts = []
    while unseen:
        start = unseen.pop()
        part = {start}
        todo = deque([start])
        while todo:
            row, col = todo.popleft()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    part.add(neighbor)
                    todo.append(neighbor)
        parts.append(part)
    return parts


def solve(grid):
    """Extract the marked object's largest component and enlarge it 2x."""
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]

    marked = []
    for color in {cell for row in grid for cell in row if cell != background}:
        parts = _components(grid, color)
        if any(len(part) == 1 for part in parts) and any(len(part) > 1 for part in parts):
            marked.append((max(map(len, parts)), color, parts))

    if not marked:
        return [row[:] for row in grid]

    _, color, parts = max(marked)
    shape = max(parts, key=len)
    top = min(row for row, _ in shape)
    bottom = max(row for row, _ in shape)
    left = min(col for _, col in shape)
    right = max(col for _, col in shape)

    result = []
    for row in range(top, bottom + 1):
        expanded_row = []
        for col in range(left, right + 1):
            value = color if (row, col) in shape else background
            expanded_row.extend((value, value))
        result.extend((expanded_row[:], expanded_row[:]))
    return result
