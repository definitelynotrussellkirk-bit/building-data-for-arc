from collections import deque


def solve(grid):
    """Crop monochrome components, sort by bbox perimeter, and pack them."""
    height, width = len(grid), len(grid[0])
    seen = set()
    pieces = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
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
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [source[left : right + 1] for source in grid[top : bottom + 1]]
            crop_height = bottom - top + 1
            crop_width = right - left + 1
            pieces.append(
                (
                    2 * (crop_height + crop_width),
                    left,
                    top,
                    crop,
                )
            )

    pieces.sort(key=lambda item: item[:3])
    crops = [item[3] for item in pieces]
    out_height = max(len(crop) for crop in crops)
    out_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for crop in crops:
        for r, source in enumerate(crop):
            output[r][offset : offset + len(source)] = source
        offset += len(crop[0]) + 1

    return output
