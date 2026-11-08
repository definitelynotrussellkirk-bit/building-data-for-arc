"""Section-frequency hypothesis, written from the visible solve challenge."""
from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    if not grid or any(len(row) != width for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    divider_rows = [-1] + [r for r in range(height) if not any(grid[r])] + [height]
    divider_columns = [-1] + [c for c in range(width)
                               if all(grid[r][c] == 0 for r in range(height))] + [width]
    result = []
    for top, bottom in zip(divider_rows, divider_rows[1:]):
        if bottom == top + 1:
            continue
        output_row = []
        for left, right in zip(divider_columns, divider_columns[1:]):
            if right == left + 1:
                continue
            counts = Counter(grid[r][c] for r in range(top + 1, bottom)
                             for c in range(left + 1, right) if grid[r][c] != 0)
            if not counts:
                raise ValueError("Empty section")
            frequency = max(counts.values())
            winners = [color for color, count in counts.items() if count == frequency]
            if len(winners) != 1:
                raise ValueError("Visible examples do not specify a frequency tie")
            output_row.append(winners[0])
        result.append(output_row)
    return result
