from collections import defaultdict


def solve(grid):
    """Stack the non-background objects from widest to narrowest.

    Each nonzero color denotes one object.  The object is cropped to its
    bounding box, objects are ordered by decreasing bounding-box width, and
    their crops are left-aligned in an output as wide as the widest crop.
    Consecutive objects are separated by one all-zero row.
    """
    cells_by_color = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                cells_by_color[color].append((row_index, column_index))

    objects = []
    for color, cells in cells_by_color.items():
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(column for _, column in cells)
        right = max(column for _, column in cells)
        height = bottom - top + 1
        width = right - left + 1
        crop = [[0] * width for _ in range(height)]
        for row, column in cells:
            crop[row - top][column - left] = color
        objects.append((width, top, left, color, crop))

    if not objects:
        return []

    # Width is the demonstrated ordering key.  The remaining fields provide
    # deterministic behavior only if a future input contains equal widths.
    objects.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
    output_width = objects[0][0]
    output = []
    for index, (_, _, _, _, crop) in enumerate(objects):
        if index:
            output.append([0] * output_width)
        for row in crop:
            output.append(row + [0] * (output_width - len(row)))
    return output
