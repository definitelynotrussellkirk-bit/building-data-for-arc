from collections import Counter


def _objects(grid):
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, color in enumerate(row) if color == 3}
    result = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        cells = {seed}
        pending = [seed]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    pending.append(neighbor)
        result.append(cells)
    return result


def _shape(cells):
    forms = []
    for swap in (False, True):
        for a in (-1, 1):
            for b in (-1, 1):
                points = [(a * (c if swap else r), b * (r if swap else c))
                          for r, c in cells]
                top = min(r for r, c in points)
                left = min(c for r, c in points)
                forms.append(tuple(sorted((r - top, c - left) for r, c in points)))
    return min(forms)


def solve(grid):
    objects = _objects(grid)
    shapes = [_shape(cells) for cells in objects]
    frequency = Counter(shapes)
    unique = [cells for cells, shape in zip(objects, shapes) if frequency[shape] == 1]
    if len(unique) != 1:
        raise ValueError("The visible rule requires exactly one singleton shape class")
    answer = [row[:] for row in grid]
    for r, c in unique[0]:
        answer[r][c] = 8
    return answer
