from copy import deepcopy


def _between(a, b):
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def _path(a, b, first):
    r1, c1 = a
    r2, c2 = b
    if first == "h":
        return [(r1, c) for c in _between(c1, c2)] + [
            (r, c2) for r in _between(r1, r2)[1:]
        ]
    return [(r, c1) for r in _between(r1, r2)] + [
        (r2, c) for c in _between(c1, c2)[1:]
    ]


def solve(grid):
    original = deepcopy(grid)
    output = deepcopy(grid)

    colors = []
    seen = set()
    for row in original:
        for value in row:
            if value not in (0, 8) and value not in seen:
                seen.add(value)
                colors.append(value)

    for color in colors:
        endpoints = [
            (r, c)
            for r, row in enumerate(original)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(endpoints) != 2:
            continue
        horizontal = _path(endpoints[0], endpoints[1], "h")
        vertical = _path(endpoints[0], endpoints[1], "v")
        endpoint_set = set(endpoints)
        horizontal_clear = all(
            original[r][c] == 0 or (r, c) in endpoint_set
            for r, c in horizontal
        )
        chosen = horizontal if horizontal_clear else vertical
        for r, c in chosen:
            if output[r][c] != 8:
                output[r][c] = color
    return output
