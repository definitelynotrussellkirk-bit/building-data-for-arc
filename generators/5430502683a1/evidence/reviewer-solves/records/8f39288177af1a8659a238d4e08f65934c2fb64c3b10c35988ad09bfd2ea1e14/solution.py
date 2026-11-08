"""Fresh visible-example solution; earlier task exposure is declared in notes."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    points = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color:
                points.setdefault(color, []).append((row, column))

    spans = []
    for color, ends in points.items():
        if len(ends) != 2:
            continue
        first, last = ends
        dr, dc = last[0] - first[0], last[1] - first[1]
        if dr and dc and abs(dr) != abs(dc):
            continue
        spans.append((max(abs(dr), abs(dc)) + 1, first, last))
    if not spans:
        raise ValueError("No aligned endpoint pair in the visible input")
    spans.sort(reverse=True)
    if len(spans) > 1 and spans[0][0] == spans[1][0]:
        raise ValueError("Visible examples do not define a longest-span tie")

    length, first, last = spans[0]
    step_row = (last[0] > first[0]) - (last[0] < first[0])
    step_column = (last[1] > first[1]) - (last[1] < first[1])
    output = [[0] * width for _ in range(height)]
    for offset in range(length):
        output[first[0] + offset * step_row][first[1] + offset * step_column] = 8
    return output
