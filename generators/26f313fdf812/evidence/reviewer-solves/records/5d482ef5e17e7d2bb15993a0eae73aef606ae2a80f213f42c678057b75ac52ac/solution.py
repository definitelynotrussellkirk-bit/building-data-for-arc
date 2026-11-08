from collections import defaultdict, deque


def solve(grid):
    """Return the pairwise area-comparison matrix for the colored objects."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            by_color = defaultdict(list)
            for r, c in cells:
                by_color[grid[r][c]].append((r, c))

            component_key = min(cells)
            objects = []
            for color, color_cells in by_color.items():
                objects.append(
                    {
                        "area": len(color_cells),
                        "first": min(color_cells),
                        "color": color,
                    }
                )
            # A touching minority color is an attached marker, so the main/larger
            # monochrome object is listed first inside a multi-color component.
            objects.sort(key=lambda obj: (-obj["area"], obj["first"], obj["color"]))
            components.append((component_key, objects))

    components.sort(key=lambda item: item[0])
    ordered = [obj for _, objects in components for obj in objects]

    output = []
    for left in ordered:
        row = []
        for right in ordered:
            if left["area"] == right["area"]:
                row.append(1)
            elif left["area"] > right["area"]:
                row.append(2)
            else:
                row.append(3)
        output.append(row)
    return output
