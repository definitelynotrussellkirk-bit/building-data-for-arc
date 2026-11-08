"""Visible-example solution for ARC task 531905d00c4b."""
from __future__ import annotations


def _components(grid):
    """Return same-color four-connected nonzero components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append((color, cells))
    return found


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def solve(grid):
    # The first completely blank row splits the prototype library from the
    # lower color-index matrix.
    separator = next(
        row for row, values in enumerate(grid) if all(value == 0 for value in values)
    )
    library = [list(row) for row in grid[:separator]]

    # Crop each colored prototype independently.  Their absolute row/column
    # placement is layout only, not part of the tile.
    crops = {}
    for color, cells in _components(library):
        r0, c0, r1, c1 = _bbox(cells)
        crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
        for row, col in cells:
            crop[row - r0][col - c0] = color
        crops[color] = crop

    tile_height = max(len(crop) for crop in crops.values())
    tile_width = max(len(crop[0]) for crop in crops.values())
    tiles = {}
    for color, crop in crops.items():
        tile = [[0] * tile_width for _ in range(tile_height)]
        for row, values in enumerate(crop):
            tile[row][: len(values)] = values
        tiles[color] = tile

    # Blank rows/columns around the lower matrix are also layout padding.
    index_cells = [
        (row, col)
        for row in range(separator + 1, len(grid))
        for col, value in enumerate(grid[row])
        if value != 0
    ]
    r0, c0, r1, c1 = _bbox(index_cells)
    index = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    # Substitute each index color by its common-sized, top-left-padded tile.
    output = [
        [0] * (len(index[0]) * tile_width)
        for _ in range(len(index) * tile_height)
    ]
    for index_row, values in enumerate(index):
        for index_col, color in enumerate(values):
            tile = tiles[color]
            out_row = index_row * tile_height
            out_col = index_col * tile_width
            for row in range(tile_height):
                output[out_row + row][out_col : out_col + tile_width] = tile[row]
    return output
