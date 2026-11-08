from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                component.add(current)
                r, c = current
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def _near_rectangular_frame(component):
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    height = bottom - top + 1
    width = right - left + 1
    if height < 3 or width < 3:
        return None

    boundary = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    missing_boundary = len(boundary - component)
    interior_noise = len(component - boundary)

    # The visible tasks use exact frames or a frame with one displaced wall cell.
    if missing_boundary > 1 or interior_noise > 1:
        return None
    return top, bottom, left, right


def solve(grid):
    output = [row[:] for row in grid]

    marker_colors = [
        value
        for row in grid
        for value in row
        if value not in (0, 8)
    ]
    if not marker_colors:
        return output

    frames = []
    for component in _components(grid, 8):
        bounds = _near_rectangular_frame(component)
        if bounds is not None:
            frames.append(bounds)
    if not frames:
        return output

    outer = max(frames, key=lambda b: (b[1] - b[0] + 1) * (b[3] - b[2] + 1))
    center = (outer[0] + outer[1], outer[2] + outer[3])
    chain = [
        bounds
        for bounds in frames
        if (bounds[0] + bounds[1], bounds[2] + bounds[3]) == center
        and outer[0] <= bounds[0] <= bounds[1] <= outer[1]
        and outer[2] <= bounds[2] <= bounds[3] <= outer[3]
    ]
    chain.sort(key=lambda b: (b[1] - b[0] + 1) * (b[3] - b[2] + 1), reverse=True)

    for index, bounds in enumerate(chain):
        if index >= len(marker_colors):
            break
        top, bottom, left, right = bounds
        child = chain[index + 1] if index + 1 < len(chain) else None
        color = marker_colors[index]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                if child is not None:
                    ctop, cbottom, cleft, cright = child
                    if ctop < row < cbottom and cleft < col < cright:
                        continue
                if grid[row][col] == 0:
                    output[row][col] = color

    return output
