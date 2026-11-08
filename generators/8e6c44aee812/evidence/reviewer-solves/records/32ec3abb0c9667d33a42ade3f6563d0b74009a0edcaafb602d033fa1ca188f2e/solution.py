"""Continue the diagonal band sequence inferred from the visible examples."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    sequence = [grid[i][i] for i in range(min(height, width))]
    while sequence and sequence[-1] == 0:
        sequence.pop()
    if not sequence:
        raise ValueError("The examples require a nonempty active band sequence")
    return [[sequence[max(row, col) % len(sequence)]
             for col in range(2 * width)] for row in range(2 * height)]
