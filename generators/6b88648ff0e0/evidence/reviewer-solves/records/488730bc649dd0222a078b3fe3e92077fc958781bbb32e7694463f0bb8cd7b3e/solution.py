from collections.abc import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Extract the strips framed by each horizontal pair of 2x2 azure blocks."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result: list[list[int]] = []

    for row in range(height - 1):
        starts: list[int] = []
        col = 0
        while col < width - 1:
            if (
                grid[row][col] == 8
                and grid[row][col + 1] == 8
                and grid[row + 1][col] == 8
                and grid[row + 1][col + 1] == 8
            ):
                starts.append(col)
                # A marker is two cells wide; skipping its second column also
                # avoids counting the same 2x2 block twice.
                col += 2
            else:
                col += 1

        for left, right in zip(starts[0::2], starts[1::2]):
            if right > left + 2:
                result.append(list(grid[row][left + 2 : right]))
                result.append(list(grid[row + 1][left + 2 : right]))

    return result
