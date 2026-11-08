from collections import deque


def _two_blocks(grid):
    """Return bounding boxes for 4-connected components of color 2."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    blocks = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 2 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            blocks.append((min(rows), max(rows), min(cols), max(cols)))

    return blocks


def solve(grid):
    """Pull each block's one or three nearest aligned blue markers inward."""
    result = [row[:] for row in grid]
    blocks = _two_blocks(grid)
    assigned = [[] for _ in blocks]

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 1:
                continue

            candidates = []
            for block_index, (top, bottom, left, right) in enumerate(blocks):
                if top <= row <= bottom:
                    if col < left:
                        candidates.append((left - col, block_index, row, left - 1))
                    elif col > right:
                        candidates.append((col - right, block_index, row, right + 1))

                if left <= col <= right:
                    if row < top:
                        candidates.append((top - row, block_index, top - 1, col))
                    elif row > bottom:
                        candidates.append((row - bottom, block_index, bottom + 1, col))

            if candidates:
                distance, block_index, destination_row, destination_col = min(candidates)
                assigned[block_index].append(
                    (distance, row, col, destination_row, destination_col)
                )

    moves = []
    for candidates in assigned:
        candidates.sort()
        keep = 1 if len(candidates) < 3 else 3
        for _, row, col, destination_row, destination_col in candidates[:keep]:
            moves.append(((row, col), (destination_row, destination_col)))

    for source, destination in moves:
        if source != destination:
            result[source[0]][source[1]] = 0
    for _, destination in moves:
        result[destination[0]][destination[1]] = 1

    return result
