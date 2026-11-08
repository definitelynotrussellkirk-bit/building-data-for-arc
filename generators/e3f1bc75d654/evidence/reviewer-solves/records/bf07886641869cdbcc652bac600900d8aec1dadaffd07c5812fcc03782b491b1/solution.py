from collections import deque


def _same_color_components(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or seen[row][col]:
                continue

            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            yield color, cells


def _framed_objects(grid):
    """Return colored objects whose bounding-box border is a full rectangle."""
    objects = []
    for color, cells in _same_color_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        height = bottom - top + 1
        width = right - left + 1
        if height < 3 or width < 3:
            continue

        border = (
            [(top, c) for c in range(left, right + 1)]
            + [(bottom, c) for c in range(left, right + 1)]
            + [(r, left) for r in range(top + 1, bottom)]
            + [(r, right) for r in range(top + 1, bottom)]
        )
        if not all(grid[r][c] == color for r, c in border):
            continue

        mask = [
            [grid[top + r][left + c] == color for c in range(width)]
            for r in range(height)
        ]
        interior_count = sum(
            mask[r][c]
            for r in range(1, height - 1)
            for c in range(1, width - 1)
        )
        objects.append(
            {
                "color": color,
                "top": top,
                "left": left,
                "height": height,
                "width": width,
                "mask": mask,
                "interior_count": interior_count,
            }
        )
    return objects


def solve(grid):
    """Copy the one patterned frame into every same-sized colored frame."""
    if not grid:
        return []

    objects = _framed_objects(grid)
    patterned = [obj for obj in objects if obj["interior_count"] > 0]
    if not patterned:
        return [row[:] for row in grid]

    # The examples contain one patterned template; the tie-break is defensive.
    source = max(patterned, key=lambda obj: obj["interior_count"])
    target_size = (source["height"], source["width"])
    template = source["mask"]

    output = [[0 for _ in row] for row in grid]
    for obj in objects:
        if (obj["height"], obj["width"]) != target_size:
            continue
        for r in range(obj["height"]):
            for c in range(obj["width"]):
                if template[r][c]:
                    output[obj["top"] + r][obj["left"] + c] = obj["color"]
    return output
