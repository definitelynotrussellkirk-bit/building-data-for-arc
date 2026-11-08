from collections import Counter, deque


def solve(grid):
    """Recolor every repeated blue (1) object green (3).

    Objects are 4-connected components.  Shapes are compared after translation
    only, so rotations/reflections remain distinct.
    """
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    seen = set()
    components = []
    signatures = []

    for r in range(height):
        for c in range(width):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            min_r = min(r0 for r0, _ in cells)
            min_c = min(c0 for _, c0 in cells)
            signature = tuple(sorted((r0 - min_r, c0 - min_c) for r0, c0 in cells))
            components.append(cells)
            signatures.append(signature)

    multiplicity = Counter(signatures)
    output = [row[:] for row in grid]
    for cells, signature in zip(components, signatures):
        if multiplicity[signature] > 1:
            for r, c in cells:
                output[r][c] = 3
    return output
