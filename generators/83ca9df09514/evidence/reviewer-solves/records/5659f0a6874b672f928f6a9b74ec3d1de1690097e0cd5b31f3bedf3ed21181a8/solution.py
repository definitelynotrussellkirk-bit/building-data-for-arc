from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand each sparse key row according to the densest template row.

    The uniquely densest row assigns a template color to every column.  A
    nonempty sparse row reveals a replacement color for each template-color
    group at one or more columns; apply that mapping across the full row.
    Empty rows and the template row are preserved.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    nonzero_counts = [sum(value != 0 for value in row) for row in grid]
    template_row = max(range(len(grid)), key=nonzero_counts.__getitem__)
    template = grid[template_row]

    output: list[list[int]] = []
    for row_index, row in enumerate(grid):
        if row_index == template_row or not any(row):
            output.append(row[:])
            continue

        mapping: dict[int, int] = {}
        for column, value in enumerate(row):
            if value != 0:
                mapping[template[column]] = value
        output.append([mapping.get(template_color, 0) for template_color in template])

    return output
