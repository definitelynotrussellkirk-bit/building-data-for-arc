"""Visible-example solution for the assigned blind ARC task."""


def _rotate_clockwise(square):
    return [list(row) for row in zip(*square[::-1])]


def _nonzero_bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return r0, r1, c0, c1


def _rotations(square):
    result = []
    current = [row[:] for row in square]
    for _ in range(4):
        if current not in result:
            result.append([row[:] for row in current])
        current = _rotate_clockwise(current)
    return result


def _complete_if_two_missing(block, targets):
    """Return a completed rotational target, or the original block.

    A block is repairable when every visible nonzero cell already agrees with
    one rotation of the left-hand template and exactly two nonzero template
    cells are absent.  Reflections and one-/three-cell defects are left alone.
    """
    for target in targets:
        missing = 0
        compatible = True
        for r in range(len(target)):
            for c in range(len(target[0])):
                seen = block[r][c]
                wanted = target[r][c]
                if seen != 0 and seen != wanted:
                    compatible = False
                    break
                if seen == 0 and wanted != 0:
                    missing += 1
            if not compatible:
                break
        if compatible and missing == 2:
            return [row[:] for row in target]
    return [row[:] for row in block]


def solve(grid):
    # The monochrome vertical bar separates the 3-column example/template panel
    # from the larger panel containing four damaged corner copies.
    separator = None
    for c in range(len(grid[0])):
        column = [row[c] for row in grid]
        nonzero = {value for value in column if value != 0}
        if len(nonzero) == 1 and all(value != 0 for value in column):
            separator = c
            break
    if separator is None:
        raise ValueError("no full-height separator column found")

    left = [row[:separator] for row in grid]
    right = [row[separator + 1 :] for row in grid]

    bbox = _nonzero_bbox(left)
    if bbox is None:
        return right
    r0, r1, c0, c1 = bbox
    template = [row[c0 : c1 + 1] for row in left[r0 : r1 + 1]]
    if len(template) != len(template[0]):
        raise ValueError("template is expected to be square")

    size = len(template)
    targets = _rotations(template)
    result = [row[:] for row in right]

    # The candidate copies occupy the four corners of the right panel, with a
    # blank corridor between their row and column bands.
    row_starts = sorted({0, len(right) - size})
    col_starts = sorted({0, len(right[0]) - size})
    for top in row_starts:
        for left_col in col_starts:
            block = [
                row[left_col : left_col + size]
                for row in result[top : top + size]
            ]
            completed = _complete_if_two_missing(block, targets)
            for r in range(size):
                result[top + r][left_col : left_col + size] = completed[r]

    return result
