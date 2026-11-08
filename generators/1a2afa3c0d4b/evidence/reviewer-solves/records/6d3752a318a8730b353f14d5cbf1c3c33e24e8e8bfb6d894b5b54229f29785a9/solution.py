"""Native Python solution inferred from the visible three-panel examples."""


def _rotate(panel):
    return [list(row) for row in zip(*panel[::-1])]


def _orient(panel, reflected, turns):
    value = [row[::-1] if reflected else row[:] for row in panel]
    for _ in range(turns):
        value = _rotate(value)
    return value


def solve(grid):
    if len(grid) < 2 or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a rectangular grid with a header and panels")
    width = len(grid[0])
    body = grid[1:]
    cuts = [column for column in range(width) if all(row[column] == 8 for row in body)]
    if len(cuts) != 2:
        raise ValueError("Expected two full separator columns")
    left, right = cuts
    a = [row[:left] for row in body]
    b = [row[left + 1:right] for row in body]
    c = [row[right + 1:] for row in body]
    target = next((value for value in grid[0] if value != 0), None)
    if target is None:
        raise ValueError("Missing output-color marker")
    candidates = []
    for reflected in (False, True):
        for turns in range(4):
            if _orient(a, reflected, turns) == b:
                transformed = _orient(c, reflected, turns)
                answer = [[target if value else 0 for value in row] for row in transformed]
                if answer not in candidates:
                    candidates.append(answer)
    if len(candidates) != 1:
        raise ValueError("The example panels do not determine one query transformation")
    return candidates[0]
