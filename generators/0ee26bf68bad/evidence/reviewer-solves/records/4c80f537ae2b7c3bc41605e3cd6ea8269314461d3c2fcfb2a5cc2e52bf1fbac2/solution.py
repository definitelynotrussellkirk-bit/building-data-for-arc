"""Extract the largest monochromatic component and clear its surrounded cells."""


def solve(grid):
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    visited = set()
    largest = set()
    largest_color = 0

    for row in range(height):
        for column in range(width):
            start = (row, column)
            color = grid[row][column]
            if color == 0 or start in visited:
                continue

            component = {start}
            visited.add(start)
            pending = [start]
            while pending:
                r, c = pending.pop()
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    neighbor = (nr, nc)
                    if (0 <= nr < height and 0 <= nc < width
                            and neighbor not in visited
                            and grid[nr][nc] == color):
                        component.add(neighbor)
                        visited.add(neighbor)
                        pending.append(neighbor)

            if len(component) > len(largest):
                largest = component
                largest_color = color

    if not largest:
        return []

    top = min(r for r, c in largest)
    bottom = max(r for r, c in largest)
    left = min(c for r, c in largest)
    right = max(c for r, c in largest)

    # Determine all removals from the original component simultaneously.
    interior = {
        (r, c)
        for r, c in largest
        if all((r + dr, c + dc) in largest for dr, dc in directions)
    }
    remaining = largest - interior

    return [
        [largest_color if (r, c) in remaining else 0
         for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]
