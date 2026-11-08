from __future__ import annotations


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            points: list[tuple[int, int]] = []

            while stack:
                current_row, current_col = stack.pop()
                points.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            result.append(
                {
                    "color": color,
                    "points": points,
                    "left": min(point_col for _, point_col in points),
                    "right": max(point_col for _, point_col in points),
                    "top": min(point_row for point_row, _ in points),
                }
            )

    return result


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    components = _components(grid)
    color_one = [component for component in components if component["color"] == 1]

    moving: list[dict[str, object]] = []
    standing: list[dict[str, object]] = []

    for component in components:
        if component["color"] == 1:
            moving.append(component)
            continue

        enclosed_by_matching_ones = any(
            left_one["right"] < component["left"]
            and component["right"] < right_one["left"]
            and left_one["top"] == right_one["top"]
            for left_one in color_one
            for right_one in color_one
        )
        (moving if enclosed_by_matching_ones else standing).append(component)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for component in standing:
        for row, col in component["points"]:  # type: ignore[assignment]
            output[row][col] = int(component["color"])

    standing_columns = sorted(
        {
            col
            for component in standing
            for _, col in component["points"]  # type: ignore[assignment]
        }
    )
    occupied: set[int] = set()

    for component in sorted(moving, key=lambda item: (item["left"], item["top"]), reverse=True):
        projected = sorted(
            {
                col + (height - 1 - row)
                for row, col in component["points"]  # type: ignore[assignment]
                if row >= height - 3 and col + (height - 1 - row) < width
            }
        )
        if not projected:
            continue

        barriers = [col for col in standing_columns if col > component["right"]]
        if barriers:
            right_limit = min(barriers) - 2
            projected = [col for col in projected if col <= right_limit]
        if not projected:
            continue

        while any(col in occupied for col in projected) and min(projected) > 0:
            projected = [col - 1 for col in projected]

        for col in projected:
            if 0 <= col < width and col not in occupied:
                output[height - 1][col] = int(component["color"])
                occupied.add(col)

    return output
