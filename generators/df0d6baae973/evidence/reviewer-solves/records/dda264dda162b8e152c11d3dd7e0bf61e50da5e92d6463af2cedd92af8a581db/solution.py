from collections import Counter


def solve(grid):
    """Build a symmetric pairwise size-comparison table for nonzero colors.

    Rows and columns are ordered by ascending color value.  For each pair, the
    cell contains the color occupying more input cells; equal counts produce 0.
    """
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    colors = sorted(counts)
    output = [[0 for _ in colors] for _ in colors]

    for i, left in enumerate(colors):
        for j in range(i + 1, len(colors)):
            right = colors[j]
            if counts[left] > counts[right]:
                winner = left
            elif counts[right] > counts[left]:
                winner = right
            else:
                winner = 0
            output[i][j] = winner
            output[j][i] = winner

    return output
