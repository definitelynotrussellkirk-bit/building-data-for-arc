"""Panel matching inferred from the visible lesson; exposed post-repair attempt."""
def solve(grid):
    if not grid or len(grid) < 2 or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a rectangular header-plus-body grid')
    target = next((v for v in grid[0] if v), None)
    if target is None:
        raise ValueError('No target color in header')
    body = [list(row) for row in grid[1:]]
    cuts = [c for c in range(len(body[0])) if all(row[c] == 8 for row in body)]
    panels = []
    start = 0
    for end in cuts + [len(body[0])]:
        if end <= start:
            raise ValueError('Empty panel')
        panels.append([row[start:end] for row in body])
        start = end + 1

    def signature(panel):
        cells = [(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v]
        if not cells:
            return frozenset()
        top = min(r for r,c in cells)
        left = min(c for r,c in cells)
        return frozenset((r-top,c-left) for r,c in cells)

    def clockwise(panel):
        return [list(row) for row in zip(*panel[::-1])]

    goal = signature(panels[0])
    for candidate in panels[1:]:
        r90 = clockwise(candidate)
        r180 = clockwise(r90)
        r270 = clockwise(r180)
        transpose = [list(row) for row in zip(*candidate)]
        variants = [candidate, r90, r180, r270,
                    [row[::-1] for row in candidate],candidate[::-1],
                    transpose,clockwise(clockwise(transpose))]
        for transformed in variants:
            if signature(transformed) == goal:
                return [[target if value else 0 for value in row] for row in transformed]
    return [[0]]
