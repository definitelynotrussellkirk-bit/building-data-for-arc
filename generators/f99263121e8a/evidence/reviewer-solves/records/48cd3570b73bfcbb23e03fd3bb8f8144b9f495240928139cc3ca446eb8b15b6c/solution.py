from collections import deque


def solve(grid):
    """Stack monochromatic 4-connected components from left to right.

    Each component contributes the rectangular crop of the *original* grid over
    its bounding box, so another color enclosed by or touching that rectangle is
    retained.  Crops are horizontally centered in the widest crop (an odd spare
    column goes on the right) and separated by one blank row.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    boxes = []

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

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            boxes.append((min(cols), min(rows), max(cols), max(rows)))

    if not boxes:
        return []

    boxes.sort(key=lambda box: (box[0], box[1], box[2], box[3]))
    output_width = max(right - left + 1 for left, _, right, _ in boxes)
    blank = [0] * output_width
    output = []

    for index, (left, top, right, bottom) in enumerate(boxes):
        if index:
            output.append(blank.copy())
        for row in range(top, bottom + 1):
            crop_row = grid[row][left : right + 1]
            spare = output_width - len(crop_row)
            left_pad = spare // 2
            output.append([0] * left_pad + crop_row + [0] * (spare - left_pad))

    return output
