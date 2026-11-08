from collections import Counter, deque


def _components(grid, background):
    """Return same-colour 4-connected components as (colour, cells)."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            colour = grid[r][c]
            if colour == background or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            result.append((colour, cells))
    return result


def _shape(cells):
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    occupied = {(r - min_r, c - min_c) for r, c in cells}
    mask = tuple(
        tuple(1 if (r, c) in occupied else 0 for c in range(max_c - min_c + 1))
        for r in range(max_r - min_r + 1)
    )
    return mask


def solve(grid):
    # The scene contains repeated examples of the intended object and one
    # malformed object.  Return the repeated shape painted with the malformed
    # object's colour.
    colours = Counter(value for row in grid for value in row)
    background = colours.most_common(1)[0][0]

    objects = []
    for colour, cells in _components(grid, background):
        objects.append((colour, _shape(cells)))

    if not objects:
        return []

    shape_counts = Counter(shape for _, shape in objects)
    intended_shape = max(
        shape_counts,
        key=lambda shape: (shape_counts[shape], sum(map(sum, shape))),
    )

    malformed = [(colour, shape) for colour, shape in objects if shape != intended_shape]
    paint = malformed[0][0] if malformed else objects[0][0]

    return [
        [paint if cell else background for cell in row]
        for row in intended_shape
    ]
