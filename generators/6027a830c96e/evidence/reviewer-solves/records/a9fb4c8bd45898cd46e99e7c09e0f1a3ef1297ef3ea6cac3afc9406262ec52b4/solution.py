from typing import List, Sequence, Tuple

Grid = List[List[int]]
Box = Tuple[int, int, int, int, int]  # top, left, bottom, right, color


def _rectangular_frames(grid: Sequence[Sequence[int]]) -> List[Box]:
    """Find colored rectangular borders, allowing arbitrary interior contents."""
    height, width = len(grid), len(grid[0])
    frames: List[Box] = []
    colors = {value for row in grid for value in row if value != 0}

    for color in colors:
        for top in range(height - 3):
            for bottom in range(top + 3, height):
                candidate_cols = [
                    col
                    for col in range(width)
                    if grid[top][col] == color and grid[bottom][col] == color
                ]
                for i, left in enumerate(candidate_cols):
                    for right in candidate_cols[i + 1 :]:
                        if right - left < 3:
                            continue
                        if not all(grid[top][col] == color for col in range(left, right + 1)):
                            continue
                        if not all(grid[bottom][col] == color for col in range(left, right + 1)):
                            continue
                        if not all(grid[row][left] == color for row in range(top, bottom + 1)):
                            continue
                        if not all(grid[row][right] == color for row in range(top, bottom + 1)):
                            continue
                        frames.append((top, left, bottom, right, color))

    # Solid borders can create duplicate nested detections only in degenerate data.
    # Retain maximal boxes; the examples consistently use separated panel frames.
    maximal: List[Box] = []
    for frame in frames:
        t, l, b, r, color = frame
        contained = any(
            other != frame
            and other[4] == color
            and other[0] <= t
            and other[1] <= l
            and other[2] >= b
            and other[3] >= r
            for other in frames
        )
        if not contained:
            maximal.append(frame)
    return maximal


def solve(grid: Grid) -> Grid:
    frames = _rectangular_frames(grid)
    if not frames:
        raise ValueError("no rectangular panels found")

    def inside_any_frame(row: int, col: int) -> bool:
        return any(top <= row <= bottom and left <= col <= right
                   for top, left, bottom, right, _ in frames)

    selector = None
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and not inside_any_frame(row, col):
                selector = value
                break
        if selector is not None:
            break
    if selector is None:
        raise ValueError("no external selector found")

    matches = [frame for frame in frames if frame[4] == selector]
    if len(matches) != 1:
        raise ValueError(f"expected one panel with selector color {selector}, found {len(matches)}")

    top, left, bottom, right, _ = matches[0]
    return [row[left + 1 : right] for row in grid[top + 1 : bottom]]
