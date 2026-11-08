from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])

    blocks = []
    for row in range(height - 1):
        for column in range(width - 1):
            if all(
                grid[row + dr][column + dc] == 2
                for dr in (0, 1)
                for dc in (0, 1)
            ):
                blocks.append((row, column))

    if len(blocks) != 2:
        return [[0]]

    def touches_ring(cell, block):
        row, column = cell
        block_row, block_column = block
        return (
            block_row - 1 <= row <= block_row + 2
            and block_column - 1 <= column <= block_column + 2
            and not (
                block_row <= row <= block_row + 1
                and block_column <= column <= block_column + 1
            )
        )

    neighbors = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    ]
    seen = set()
    for row in range(height):
        for column in range(width):
            start = (row, column)
            if grid[row][column] != 8 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            component = []
            while queue:
                current = queue.popleft()
                component.append(current)
                for dr, dc in neighbors:
                    nxt = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == 8
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            if all(
                any(touches_ring(cell, block) for cell in component)
                for block in blocks
            ):
                return [[8]]
    return [[0]]
