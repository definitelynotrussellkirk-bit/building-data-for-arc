from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop monochromatic 4-components and stack them left-to-right."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            pending = [(row, col)]
            cells: list[tuple[int, int]] = []
            while pending:
                current_row, current_col = pending.pop()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        pending.append((next_row, next_col))
            components.append(cells)

    def bounds(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
        return (
            min(row for row, _ in cells),
            min(col for _, col in cells),
            max(row for row, _ in cells),
            max(col for _, col in cells),
        )

    ordered = sorted(components, key=lambda cells: (bounds(cells)[1], bounds(cells)[0]))
    crops: list[list[list[int]]] = []
    for cells in ordered:
        top, left, bottom, right = bounds(cells)
        # Keep the complete source rectangle, including any other-colored cells.
        crops.append([source_row[left : right + 1] for source_row in grid[top : bottom + 1]])

    if not crops:
        return [[]]

    output_width = max(len(crop[0]) for crop in crops)
    output: list[list[int]] = []
    for index, crop in enumerate(crops):
        if index:
            output.append([0] * output_width)
        left_padding = (output_width - len(crop[0])) // 2
        right_padding = output_width - len(crop[0]) - left_padding
        output.extend(
            [([0] * left_padding) + row + ([0] * right_padding) for row in crop]
        )
    return output
