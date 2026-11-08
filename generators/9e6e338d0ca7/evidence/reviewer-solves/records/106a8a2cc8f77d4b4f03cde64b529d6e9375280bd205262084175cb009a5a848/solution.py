from collections import deque


def solve(grid):
    """Fill every least-populated nonempty room with its marker color.

    Color 5 is the wall network.  Each 4-connected component of non-wall cells
    is a room.  Count its nonzero markers, ignore empty rooms, and fill all rooms
    tied for the smallest positive marker count.  The generated lessons use a
    single marker color in each selected room; for robustness, a selected room
    is filled only when that color is unambiguous.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    rooms = []

    for row in range(height):
        for col in range(width):
            if seen[row][col] or grid[row][col] == 5:
                continue
            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []
            markers = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                if grid[r][c] != 0:
                    markers.append(grid[r][c])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != 5
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            rooms.append((cells, markers))

    positive_counts = [len(markers) for _, markers in rooms if markers]
    if not positive_counts:
        return out
    minimum = min(positive_counts)

    for cells, markers in rooms:
        if len(markers) != minimum:
            continue
        colors = set(markers)
        if len(colors) != 1:
            continue
        fill = markers[0]
        for r, c in cells:
            out[r][c] = fill

    return out
