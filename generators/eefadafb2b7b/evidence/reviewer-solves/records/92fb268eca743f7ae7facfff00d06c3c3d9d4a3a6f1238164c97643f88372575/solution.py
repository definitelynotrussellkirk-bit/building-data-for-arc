from collections import deque


def solve(grid):
    """Return 8 iff one 8-connected cyan component touches both red blocks."""
    height = len(grid)
    width = len(grid[0])

    blocks = []
    for row in range(height - 1):
        for col in range(width - 1):
            if all(
                grid[row + dr][col + dc] == 2
                for dr in (0, 1)
                for dc in (0, 1)
            ):
                blocks.append((row, col))

    if len(blocks) < 2:
        return [[0]]
    blocks = blocks[:2]

    def touches_block(cell, block):
        row, col = cell
        top, left = block
        return (
            top - 1 <= row <= top + 2
            and left - 1 <= col <= left + 2
            and not (top <= row <= top + 1 and left <= col <= left + 1)
        )

    seen = set()
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if grid[start_row][start_col] != 8 or start in seen:
                continue

            component = []
            queue = deque([start])
            seen.add(start)
            while queue:
                row, col = queue.popleft()
                component.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        nxt = (nr, nc)
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] == 8
                            and nxt not in seen
                        ):
                            seen.add(nxt)
                            queue.append(nxt)

            if all(
                any(touches_block(cell, block) for cell in component)
                for block in blocks
            ):
                return [[8]]

    return [[0]]
