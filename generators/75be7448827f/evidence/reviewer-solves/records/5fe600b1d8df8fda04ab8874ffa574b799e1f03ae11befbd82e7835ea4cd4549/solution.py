from collections import deque


def _one_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield component


def solve(grid):
    """Return the interior of the frame containing the most colored cells."""
    candidates = []

    for component in _one_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top < 2 or right - left < 2:
            continue

        border = (
            [(top, col) for col in range(left, right + 1)]
            + [(bottom, col) for col in range(left, right + 1)]
            + [(row, left) for row in range(top + 1, bottom)]
            + [(row, right) for row in range(top + 1, bottom)]
        )
        if not all(grid[row][col] == 1 for row, col in border):
            continue

        interior = [
            grid[row][left + 1 : right]
            for row in range(top + 1, bottom)
        ]
        colored_count = sum(
            value not in (0, 1)
            for row in interior
            for value in row
        )
        candidates.append((colored_count, interior))

    if not candidates:
        raise ValueError("no rectangular color-1 frames found")

    return max(candidates, key=lambda candidate: candidate[0])[1]
