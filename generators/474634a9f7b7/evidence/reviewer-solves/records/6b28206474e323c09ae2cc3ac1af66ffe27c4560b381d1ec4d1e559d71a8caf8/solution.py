from collections import Counter


def _quadrant(cells, height, width):
    mean_r = sum(r for r, _ in cells) / len(cells)
    mean_c = sum(c for _, c in cells) / len(cells)
    return ("T" if mean_r < height / 2 else "B") + (
        "L" if mean_c < width / 2 else "R"
    )


def _to_local(cell, quadrant):
    r, c = cell
    if quadrant == "TL":
        return c, r
    if quadrant == "TR":
        return r, -c
    if quadrant == "BR":
        return -c, -r
    if quadrant == "BL":
        return -r, c
    raise ValueError(f"unknown quadrant: {quadrant}")


def _from_local(cell, quadrant):
    x, y = cell
    if quadrant == "TL":
        return y, x
    if quadrant == "TR":
        return x, -y
    if quadrant == "BR":
        return -y, -x
    if quadrant == "BL":
        return -x, y
    raise ValueError(f"unknown quadrant: {quadrant}")


def solve(grid):
    """Move one inward-tip cell from each smaller object to the largest object.

    Each quadrant has the same local orientation after rotation: +x points toward
    the centre and +y follows the visible object's progression.  Smaller objects
    lose their local (max x, max y) tip.  The largest object gains a three-cell
    segment just outside its local min-x edge at y=max_y-1..max_y+1.
    """
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    colors = [color for color in counts if color != background]

    objects = {}
    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        quadrant = _quadrant(cells, height, width)
        local = {_to_local(cell, quadrant) for cell in cells}
        objects[color] = (cells, quadrant, local)

    largest = max(colors, key=lambda color: len(objects[color][0]))

    for color, (cells, quadrant, local) in objects.items():
        if color == largest:
            min_x = min(x for x, _ in local)
            max_y = max(y for _, y in local)
            additions = {
                _from_local((min_x - 1, y), quadrant)
                for y in range(max_y - 1, max_y + 2)
            }
            for r, c in additions:
                if 0 <= r < height and 0 <= c < width:
                    out[r][c] = color
        else:
            max_x = max(x for x, _ in local)
            max_y = max(y for _, y in local)
            removal = _from_local((max_x, max_y), quadrant)
            if removal not in cells:
                # The visible examples make this distinguished corner occupied.
                # Keep a deterministic fallback for malformed variants.
                removal = max(cells, key=lambda p: _to_local(p, quadrant))
            r, c = removal
            out[r][c] = background

    return out
