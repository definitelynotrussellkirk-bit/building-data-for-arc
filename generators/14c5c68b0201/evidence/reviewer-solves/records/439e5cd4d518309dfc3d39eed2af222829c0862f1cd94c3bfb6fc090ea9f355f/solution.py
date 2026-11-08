from collections import Counter, deque


def _frame_color(grid):
    """Return the dominant color on the outer border."""
    height = len(grid)
    width = len(grid[0])
    border = list(grid[0]) + list(grid[-1])
    border.extend(grid[r][0] for r in range(1, height - 1))
    border.extend(grid[r][-1] for r in range(1, height - 1))
    return Counter(border).most_common(1)[0][0]


def _non_frame_components(grid, frame):
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == frame or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == frame:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            yield component


def solve(grid):
    """Tile each colored seed through the zero canvas that contains it."""
    output = [row[:] for row in grid]
    frame = _frame_color(grid)

    for component in _non_frame_components(grid, frame):
        colored = [
            (row, col, grid[row][col])
            for row, col in component
            if grid[row][col] not in (0, frame)
        ]
        if not colored:
            continue

        seed_top = min(row for row, _, _ in colored)
        seed_bottom = max(row for row, _, _ in colored)
        seed_left = min(col for _, col, _ in colored)
        seed_right = max(col for _, col, _ in colored)
        period_height = seed_bottom - seed_top + 1
        period_width = seed_right - seed_left + 1

        residues = {}
        for row, col, color in colored:
            key = ((row - seed_top) % period_height, (col - seed_left) % period_width)
            residues[key] = color

        for row, col in component:
            key = ((row - seed_top) % period_height, (col - seed_left) % period_width)
            output[row][col] = residues.get(key, 0)

    return output
