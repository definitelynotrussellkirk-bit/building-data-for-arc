from collections import Counter


def _split_panels(grid):
    """Split at full-height gray (5) separator columns."""
    height = len(grid)
    width = len(grid[0])
    separators = {
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    }

    panels = []
    start = 0
    for col in range(width + 1):
        if col == width or col in separators:
            if start < col:
                panels.append([row[start:col] for row in grid])
            start = col + 1
    return panels


def _object_color(panel):
    colors = Counter(value for row in panel for value in row if value != 0)
    return colors.most_common(1)[0][0]


def _trim(mask):
    rows = [r for r, row in enumerate(mask) if any(row)]
    cols = [c for c in range(len(mask[0])) if any(row[c] for row in mask)]
    if not rows or not cols:
        return []
    return [[mask[r][c] for c in cols] for r in rows]


def _rotate_ccw(mask):
    if not mask:
        return []
    height, width = len(mask), len(mask[0])
    return [[mask[r][width - 1 - c] for r in range(height)]
            for c in range(width)]


def _dihedral_equivalent(left, right):
    # The examples include both rotations and a reflected orientation.
    for base in (left, [list(reversed(row)) for row in left]):
        candidate = base
        for _ in range(4):
            if candidate == right:
                return True
            candidate = _rotate_ccw(candidate)
    return False


def solve(grid):
    panels = _split_panels(grid)
    colors = [_object_color(panel) for panel in panels]

    # The final panel is the marker object. Find which preceding shape is the
    # same object under rotation, retain that panel's placement, and recolor it
    # with the final panel's color.
    marker_index = len(panels) - 1
    marker_color = colors[marker_index]
    marker_shape = _trim([
        [value != 0 for value in row]
        for row in panels[marker_index]
    ])

    for index, panel in enumerate(panels):
        if index == marker_index:
            continue
        shape = _trim([[value != 0 for value in row] for row in panel])
        if _dihedral_equivalent(shape, marker_shape):
            return [
                [marker_color if value != 0 else 0 for value in row]
                for row in panel
            ]

    raise ValueError("No shared-color panel matches the marker shape by rotation/reflection")
