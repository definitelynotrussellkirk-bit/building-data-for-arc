"""Self-contained grid reconstruction for native source closure.

Pure functions reused from this task's reviewed workspace/reference_probe.py.
Racket remains the independent authority; this module has no filesystem imports.
"""

def _components(grid):
    """Return same-color 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop_component(grid, color, cells):
    r0, c0, r1, c1 = _bbox(cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = color
    return out


def _pad(grid, height, width):
    out = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r][c] = value
    return out


def _separator(grid):
    for r, row in enumerate(grid):
        if all(v == 0 for v in row):
            return r
    raise ValueError("no all-zero separator row")


def _index_bbox(grid, sep):
    points = [
        (r, c)
        for r in range(sep + 1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    ]
    if not points:
        raise ValueError("empty index area")
    return _bbox(points)


def parse(grid):
    sep = _separator(grid)
    library = [list(row) for row in grid[:sep]]
    components = sorted(_components(library), key=lambda item: (_bbox(item[1])[1], _bbox(item[1])[0]))
    if not components:
        raise ValueError("empty prototype library")
    crops = [(color, _crop_component(library, color, cells)) for color, cells in components]
    ph = max(len(tile) for _, tile in crops)
    pw = max(len(tile[0]) for _, tile in crops)
    tiles = {color: _pad(tile, ph, pw) for color, tile in crops}
    r0, c0, r1, c1 = _index_bbox(grid, sep)
    index = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    return {
        "sep": sep,
        "library": library,
        "components": components,
        "tiles": tiles,
        "tile_h": ph,
        "tile_w": pw,
        "index_bbox": (r0, c0, r1, c1),
        "index": index,
    }


def _mosaic(index, tiles, tile_h, tile_w):
    out = [[0] * (len(index[0]) * tile_w) for _ in range(len(index) * tile_h)]
    for ir, row in enumerate(index):
        for ic, token in enumerate(row):
            tile = tiles.get(token, [[0] * tile_w for _ in range(tile_h)])
            for r in range(tile_h):
                for c in range(tile_w):
                    value = tile[r][c]
                    if value:
                        out[ir * tile_h + r][ic * tile_w + c] = value
    return out


def intended_output(grid):
    parts = parse(grid)
    return _mosaic(parts["index"], parts["tiles"], parts["tile_h"], parts["tile_w"])


def absolute_row_rival(grid):
    """Wrong rule: preserve each prototype's absolute library row offset."""
    parts = parse(grid)
    lib_h = parts["sep"]
    pw = parts["tile_w"]
    tiles = {}
    for color, cells in parts["components"]:
        _, c0, _, c1 = _bbox(cells)
        tile = [[0] * (c1 - c0 + 1) for _ in range(lib_h)]
        for r, c in cells:
            tile[r][c - c0] = color
        tiles[color] = _pad(tile, lib_h, pw)
    return _mosaic(parts["index"], tiles, lib_h, pw)


def uncropped_index_rival(grid):
    """Wrong rule: tile the lower rectangle without cropping top/left zero padding."""
    parts = parse(grid)
    _, _, r1, c1 = parts["index_bbox"]
    raw = [row[:c1 + 1] for row in grid[parts["sep"] + 1:r1 + 1]]
    return _mosaic(raw, parts["tiles"], parts["tile_h"], parts["tile_w"])


def fixed_3x3_rival(grid):
    """Wrong rule: always normalize prototype tiles to the canonical 3x3 size."""
    parts = parse(grid)
    tiles = {}
    for color, tile in parts["tiles"].items():
        fixed = [[0] * 3 for _ in range(3)]
        for r in range(min(3, len(tile))):
            for c in range(min(3, len(tile[0]))):
                fixed[r][c] = tile[r][c]
        tiles[color] = fixed
    return _mosaic(parts["index"], tiles, 3, 3)
