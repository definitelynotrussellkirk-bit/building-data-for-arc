"""Reproduce the largest hollow rectangular frame around matching empty areas."""


def solve(grid):
    """Return a copy of grid with borders added to congruent zero interiors."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [list(row) for row in grid]
    if height < 3 or width < 3:
        return output

    # Discover full monochrome frames directly from the current input.
    frames = []
    for top in range(height - 2):
        for left in range(width - 2):
            color = grid[top][left]
            if color == 0:
                continue
            for bottom in range(top + 2, height):
                if any(grid[r][left] != color for r in range(top, bottom + 1)):
                    break
                for right in range(left + 2, width):
                    if any(grid[top][c] != color for c in range(left, right + 1)):
                        break
                    if any(grid[bottom][c] != color for c in range(left, right + 1)):
                        continue
                    if any(grid[r][right] != color for r in range(top, bottom + 1)):
                        continue
                    if any(
                        grid[r][c] != 0
                        for r in range(top + 1, bottom)
                        for c in range(left + 1, right)
                    ):
                        continue
                    frames.append((top, left, bottom, right, color))

    if not frames:
        return output
    top, left, bottom, right, color = max(
        frames,
        key=lambda frame: (frame[2] - frame[0] + 1) * (frame[3] - frame[1] + 1),
    )
    inner_height = bottom - top - 1
    inner_width = right - left - 1

    # Only inspect the original grid, so newly drawn borders never affect matching.
    for inner_top in range(1, height - inner_height):
        for inner_left in range(1, width - inner_width):
            if not all(
                grid[r][c] == 0
                for r in range(inner_top, inner_top + inner_height)
                for c in range(inner_left, inner_left + inner_width)
            ):
                continue
            frame_top = inner_top - 1
            frame_bottom = inner_top + inner_height
            frame_left = inner_left - 1
            frame_right = inner_left + inner_width
            for c in range(frame_left, frame_right + 1):
                output[frame_top][c] = color
                output[frame_bottom][c] = color
            for r in range(frame_top + 1, frame_bottom):
                output[r][frame_left] = color
                output[r][frame_right] = color
    return output
