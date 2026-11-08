from collections import Counter


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(1, h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def solve(grid):
    """Select by the row-0 frequency legend, crop the largest key object, scale 2x."""
    counts = Counter(value for value in grid[0] if value != 0)
    key = min(counts, key=lambda color: (-counts[color], color))

    components = _components(grid, key)
    chosen = min(
        components,
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )
    r0 = min(r for r, _ in chosen)
    r1 = max(r for r, _ in chosen)
    c0 = min(c for _, c in chosen)
    c1 = max(c for _, c in chosen)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    output = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        output.append(doubled[:])
        output.append(doubled[:])
    return output
