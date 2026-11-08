from collections import Counter


def solve(grid):
    """Fill each zero component with its unique cardinal-boundary plurality."""
    height = len(grid)
    width = len(grid[0])
    result = [list(row) for row in grid]
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    }

    while remaining:
        start = remaining.pop()
        stack = [start]
        component = []
        votes = []
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            for other_row, other_col in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if not (0 <= other_row < height and 0 <= other_col < width):
                    continue
                neighbor = (other_row, other_col)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                elif 1 <= grid[other_row][other_col] <= 4:
                    # Count an incidence, not merely a distinct marker cell.
                    votes.append(grid[other_row][other_col])

        counts = Counter(votes)
        if counts:
            best = max(counts.values())
            winners = [color for color, count in counts.items() if count == best]
            if len(winners) == 1:
                for row, col in component:
                    result[row][col] = winners[0]

    return result
