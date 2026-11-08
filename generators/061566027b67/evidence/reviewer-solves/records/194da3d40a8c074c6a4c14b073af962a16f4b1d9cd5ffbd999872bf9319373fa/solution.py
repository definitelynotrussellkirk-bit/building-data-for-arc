from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep the largest solid non-background rectangle and erase all noise."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    # (area, min_side, height, width, -top, -left, color, top, left)
    # The planted rectangle is unique in the visible examples.  The remaining
    # fields make tie-breaking deterministic without changing the main rule.
    best: tuple[int, int, int, int, int, int, int, int, int] | None = None

    for top in range(height):
        common: list[int | None] = [
            value if value != 0 else None for value in grid[top]
        ]
        for bottom in range(top, height):
            if bottom > top:
                for col in range(width):
                    value = common[col]
                    if value is not None and grid[bottom][col] != value:
                        common[col] = None

            rect_height = bottom - top + 1
            col = 0
            while col < width:
                color = common[col]
                if color is None:
                    col += 1
                    continue

                left = col
                while col < width and common[col] == color:
                    col += 1
                rect_width = col - left

                # Ignore accidental monochrome lines in the random noise.  All
                # demonstrated target objects are genuine 2-D rectangles.
                if rect_height < 2 or rect_width < 2:
                    continue

                candidate = (
                    rect_height * rect_width,
                    min(rect_height, rect_width),
                    rect_height,
                    rect_width,
                    -top,
                    -left,
                    color,
                    top,
                    left,
                )
                if best is None or candidate[:6] > best[:6]:
                    best = candidate

    output = [[0 for _ in range(width)] for _ in range(height)]
    if best is None:
        return output

    _, _, rect_height, rect_width, _, _, color, top, left = best
    for row in range(top, top + rect_height):
        for col in range(left, left + rect_width):
            output[row][col] = color
    return output
