"""Independent authoring oracle; exported labels still come from Racket.

No generator or object-library helper is imported. Canonical labels validate
the four-neighbor color-3 selection and signed 2-to-1 displacement.
"""
from collections import deque


def components(grid, *, colors=None, diagonal=False):
    cells = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row)
             if color != 0 and (colors is None or color in colors)}
    groups = []
    while cells:
        start = min(cells)
        cells.remove(start)
        todo, group = deque([start]), {start}
        color = grid[start[0]][start[1]]
        while todo:
            r, c = todo.popleft()
            neighbors = ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
            if diagonal:
                neighbors += ((r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1))
            for point in neighbors:
                if point in cells and grid[point[0]][point[1]] == color:
                    cells.remove(point)
                    group.add(point)
                    todo.append(point)
        groups.append(group)
    return groups


def facts(grid):
    green = components(grid, colors={3})
    main = max(green, key=len)
    one = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1)
    two = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    dr, dc = one[0]-two[0], one[1]-two[1]
    h, w = len(grid), len(grid[0])
    moved = {(r+dr, c+dc) for r, c in main}
    visible = {(r, c) for r, c in moved if 0 <= r < h and 0 <= c < w}
    return dict(h=h, w=w, main=main, green=green, one=one, two=two,
                delta=(dr, dc), moved=moved, visible=visible)


def predict(grid, *, selection="main", vector="signed"):
    scene = facts(grid)
    cells = scene["main"]
    if selection == "all_green":
        cells = set().union(*scene["green"])
    elif selection == "eight_connected_green":
        cells = max(components(grid, colors={3}, diagonal=True), key=len)
    elif selection == "first_green":
        cells = scene["green"][0]
    elif selection == "last_green":
        cells = scene["green"][-1]
    elif selection == "largest_nonmarker":
        cells = max(components(grid, colors=set(range(3, 10))), key=len)
    elif selection == "all_nonmarker":
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if 3 <= v <= 9}
    elif selection != "main":
        raise ValueError(selection)
    dr, dc = scene["delta"]
    if vector == "absolute":
        dr, dc = abs(dr), abs(dc)
    elif vector == "fixed_absolute_3_4":
        dr, dc = 3, 4
    elif vector == "swapped":
        dr, dc = dc, dr
    elif vector != "signed":
        raise ValueError(vector)
    output = [[0] * scene["w"] for _ in range(scene["h"])]
    for r, c in cells:
        rr, cc = r+dr, c+dc
        if 0 <= rr < scene["h"] and 0 <= cc < scene["w"]:
            output[rr][cc] = 8
    return output


def solve(grid):
    return predict(grid)
