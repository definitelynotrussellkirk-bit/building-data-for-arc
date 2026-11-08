"""Exposed solve written from this episode's visible panel examples."""
from collections import Counter


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('ragged input')
    separators = [col for col in range(width)
                  if all(row[col] == 5 for row in grid)]
    if len(separators) != 2:
        raise ValueError('expected two divider columns')
    panel_width = separators[0]
    if separators != [panel_width, 2 * panel_width + 1] or width != 3 * panel_width + 2:
        raise ValueError('expected three equal panels')
    starts = (0, panel_width + 1, 2 * panel_width + 2)
    answer = []
    for row in range(height):
        output_row = []
        for col in range(panel_width):
            present = [grid[row][start + col] for start in starts
                       if grid[row][start + col] != 0]
            if len(present) < 2:
                output_row.append(0)
            else:
                frequencies = Counter(present)
                output_row.append(max(frequencies, key=lambda color: (frequencies[color], color)))
        answer.append(output_row)
    return answer
