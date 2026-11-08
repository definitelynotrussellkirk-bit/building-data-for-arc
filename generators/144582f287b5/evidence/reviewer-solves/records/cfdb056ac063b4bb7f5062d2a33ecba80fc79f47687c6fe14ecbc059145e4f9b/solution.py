from collections import Counter


def solve(grid):
    """Move the unique solid 2x2 payload to the four grid corners."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]

    blocks = []
    for row in range(height - 1):
        for column in range(width - 1):
            block = (
                grid[row][column],
                grid[row][column + 1],
                grid[row + 1][column],
                grid[row + 1][column + 1],
            )
            if all(value != background for value in block):
                blocks.append(block)

    if len(blocks) != 1:
        raise ValueError(f"expected one solid 2x2 payload, found {len(blocks)}")

    top_left, top_right, bottom_left, bottom_right = blocks[0]
    output = [[background for _ in range(width)] for _ in range(height)]
    output[0][0] = top_left
    output[0][-1] = top_right
    output[-1][0] = bottom_left
    output[-1][-1] = bottom_right
    return output
