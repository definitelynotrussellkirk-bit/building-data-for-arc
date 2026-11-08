"""Fill the interiors of blue rectangular frames containing red markers."""

def solve(grid):
    result = [list(row) for row in grid]
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    while pending:
        first = min(pending)
        pending.remove(first)
        component, frontier = {first}, [first]
        while frontier:
            r, c = frontier.pop()
            for point in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if point in pending:
                    pending.remove(point)
                    component.add(point)
                    frontier.append(point)
        top, bottom = min(r for r, c in component), max(r for r, c in component)
        left, right = min(c for r, c in component), max(c for r, c in component)
        if bottom-top < 2 or right-left < 2:
            continue
        perimeter = {(r, c) for r in range(top, bottom+1) for c in range(left, right+1)
                     if r in (top, bottom) or c in (left, right)}
        if component != perimeter:
            continue
        inside = [(r, c) for r in range(top+1, bottom) for c in range(left+1, right)]
        if any(grid[r][c] == 2 for r, c in inside):
            for r, c in inside:
                result[r][c] = 4
    return result
