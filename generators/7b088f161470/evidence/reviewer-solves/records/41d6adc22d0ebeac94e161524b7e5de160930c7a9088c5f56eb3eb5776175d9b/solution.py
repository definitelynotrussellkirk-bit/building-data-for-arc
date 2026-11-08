from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Summarize the three colored ladder rows and flag the farthest ladder.

    A non-zero monochrome row is a baseline.  The three baselines other than
    color 9 become output rows in top-to-bottom order.  The odd-height,
    three-column ladder made from the same color encodes a bar of
    ``(height - 1) // 2`` cells.  The horizontal 9 baseline becomes the
    vertical separator.  Color 5 marks the row whose non-empty ladder center
    is farthest from the input 5; an all-empty tie falls back to the first row.
    """
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    full_rows: list[tuple[int, int]] = []
    marker: tuple[int, int] | None = None

    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for c, value in enumerate(row):
            if value == 5:
                marker = (r, c)
        if row[0] != 0 and all(value == row[0] for value in row):
            full_rows.append((r, row[0]))

    baselines = [(r, color) for r, color in full_rows if color != 9]
    full_row_indices = {r for r, _ in full_rows}

    ladders: list[list[tuple[int, int]]] = []
    lengths: list[int] = []
    for baseline_row, color in baselines:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            if r not in full_row_indices
            for c, value in enumerate(row)
            if value == color
        ]
        ladders.append(cells)
        if not cells:
            lengths.append(0)
        else:
            rows = [r for r, _ in cells]
            ladder_height = max(rows) - min(rows) + 1
            lengths.append(max(0, (ladder_height - 1) // 2))

    marked_index = 0
    if marker is not None:
        mr, mc = marker
        best_distance = -1.0
        for index, cells in enumerate(ladders):
            if not cells:
                continue
            center_r = sum(r for r, _ in cells) / len(cells)
            center_c = sum(c for _, c in cells) / len(cells)
            distance = (center_r - mr) ** 2 + (center_c - mc) ** 2
            if distance > best_distance:
                best_distance = distance
                marked_index = index

    result: list[list[int]] = []
    for index, ((_, color), length) in enumerate(zip(baselines, lengths)):
        bar = [color] * min(length, 3)
        row = bar + [0] * (3 - len(bar)) + [9, 5 if index == marked_index else 0]
        result.append(row)
    return result
