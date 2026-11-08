from collections import Counter, defaultdict


_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid, background):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != background
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)

    return result


def solve(grid):
    """Move each compound's upper colour left and lower colour right by one."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    output = [[background for _ in range(width)] for _ in range(height)]

    for component in _components(grid, background):
        by_colour = defaultdict(list)
        for row, col in component:
            by_colour[grid[row][col]].append((row, col))

        # Visible examples contain exactly two vertically stacked colours per compound.
        ordered = sorted(
            by_colour.items(),
            key=lambda item: min(row for row, _ in item[1]),
        )
        if len(ordered) != 2:
            raise ValueError("expected each foreground compound to contain two colours")

        for (_, cells), delta_col in zip(ordered, (-1, 1)):
            for row, col in cells:
                new_col = col + delta_col
                if not 0 <= new_col < width:
                    raise ValueError("visible rule would shift a cell outside the grid")
                output[row][new_col] = grid[row][col]

    return output
