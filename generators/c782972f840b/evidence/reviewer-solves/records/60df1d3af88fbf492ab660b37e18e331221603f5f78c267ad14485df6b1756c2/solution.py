def _components(grid):
    """Return same-colour 4-connected objects in row-major discovery order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_r = min(r for r, _ in cells)
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)
            shape = [
                [0 for _ in range(max_c - min_c + 1)]
                for _ in range(max_r - min_r + 1)
            ]
            for r, c in cells:
                shape[r - min_r][c - min_c] = 1
            objects.append((colour, shape))

    return objects


def _rotate_clockwise(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _rotation_equivalent(first, second):
    candidate = first
    for _ in range(4):
        if candidate == second:
            return True
        candidate = _rotate_clockwise(candidate)
    return False


def solve(grid):
    objects = _components(grid)
    size = len(objects)
    answer = [[0 for _ in range(size)] for _ in range(size)]

    for i, (colour_i, shape_i) in enumerate(objects):
        for j, (colour_j, shape_j) in enumerate(objects):
            if i == j:
                answer[i][j] = 9
            else:
                answer[i][j] = (
                    (2 if colour_i == colour_j else 0)
                    + (4 if _rotation_equivalent(shape_i, shape_j) else 0)
                )

    return answer
