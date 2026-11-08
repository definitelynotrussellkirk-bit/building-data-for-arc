from __future__ import annotations


def _complete_frames(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    """Return (top, left, bottom, right) for every complete nonzero frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    frames: list[tuple[int, int, int, int]] = []

    for top in range(height - 2):
        for bottom in range(top + 2, height):
            for left in range(width - 2):
                color = grid[top][left]
                if color == 0:
                    continue
                for right in range(left + 2, width):
                    if (
                        grid[top][right] != color
                        or grid[bottom][left] != color
                        or grid[bottom][right] != color
                    ):
                        continue
                    if not all(
                        grid[top][column] == color
                        and grid[bottom][column] == color
                        for column in range(left, right + 1)
                    ):
                        continue
                    if not all(
                        grid[row][left] == color
                        and grid[row][right] == color
                        for row in range(top, bottom + 1)
                    ):
                        continue
                    frames.append((top, left, bottom, right))

    # The examples read the surviving boxes from left to right.  Top is a
    # deterministic tie-breaker for vertically stacked boxes.
    frames.sort(key=lambda frame: (frame[1], frame[0], frame[3], frame[2]))
    return frames


def solve(grid: list[list[int]]) -> list[list[int]]:
    frames = _complete_frames(grid)
    if not frames:
        return []

    interiors = [
        [row[left + 1 : right] for row in grid[top + 1 : bottom]]
        for top, left, bottom, right in frames
    ]
    out_height = max(len(interior) for interior in interiors)
    out_width = sum(len(interior[0]) for interior in interiors) + len(interiors) - 1
    output = [[0] * out_width for _ in range(out_height)]

    out_column = 0
    for interior in interiors:
        interior_width = len(interior[0])
        for row_index, row in enumerate(interior):
            output[row_index][out_column : out_column + interior_width] = row
        out_column += interior_width + 1

    return output
