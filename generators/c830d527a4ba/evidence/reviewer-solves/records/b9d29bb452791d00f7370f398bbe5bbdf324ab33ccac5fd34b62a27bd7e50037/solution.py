"""Visible-example-only solution for blind task c830d527a4ba."""


def _bbox(grid, predicate):
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if predicate(value)
    ]
    if not points:
        raise ValueError("required object is missing")
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return min(rows), max(rows), min(cols), max(cols)


def _crop(grid, box):
    r0, r1, c0, c1 = box
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_clockwise(tile):
    return [list(row) for row in zip(*tile[::-1])]


def _rotate_180(tile):
    return [row[::-1] for row in tile[::-1]]


def _flip_horizontal(tile):
    return [row[::-1] for row in tile]


def _paint(mask, color):
    return [[color if value else 0 for value in row] for row in mask]


def _tile_for(mask, color):
    # A zero template cell keeps the identity tile's footprint but paints nothing.
    if color == 0:
        return [[0 for _ in row] for row in mask]
    if color == 2:
        transformed = mask
    elif color == 3:
        transformed = _rotate_clockwise(mask)
    elif color == 4:
        transformed = _rotate_180(mask)
    elif color == 5:
        transformed = _flip_horizontal(mask)
    else:
        raise ValueError(f"unexpected template color {color}")
    return _paint(transformed, color)


def solve(grid):
    """Expand the 2–5 template using transformed copies of the color-1 shape."""
    shape_box = _bbox(grid, lambda value: value == 1)
    template_box = _bbox(grid, lambda value: value not in (0, 1))

    shape = _crop(grid, shape_box)
    shape = [[1 if value == 1 else 0 for value in row] for row in shape]
    template = _crop(grid, template_box)

    packed_rows = []
    for template_row in template:
        tiles = [_tile_for(shape, color) for color in template_row]
        row_height = max(len(tile) for tile in tiles)
        row_width = sum(len(tile[0]) for tile in tiles) + len(tiles) - 1
        packed = [[0] * row_width for _ in range(row_height)]

        left = 0
        for tile in tiles:
            for r, tile_row in enumerate(tile):
                packed[r][left : left + len(tile_row)] = tile_row
            left += len(tile[0]) + 1
        packed_rows.append(packed)

    output_width = max(len(row[0]) for row in packed_rows)
    centered_rows = []
    for packed in packed_rows:
        difference = output_width - len(packed[0])
        left_padding = difference // 2
        centered_rows.append(
            [[0] * left_padding + row + [0] * (difference - left_padding) for row in packed]
        )

    output = []
    for index, packed in enumerate(centered_rows):
        if index:
            output.append([0] * output_width)
        output.extend(packed)
    return output
