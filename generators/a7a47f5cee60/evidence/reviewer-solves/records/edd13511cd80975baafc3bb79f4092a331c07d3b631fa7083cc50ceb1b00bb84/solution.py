"""Visible-example solution for the reviewer solve episode."""

MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    h, w = len(grid), len(grid[0])

    # Each nonzero monochromatic four-connected region is one graph vertex.
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    regions = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in MOVES:
                point = (r + dr, c + dc)
                if point in pending and grid[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    stack.append(point)
        regions.append(cells)

    owner = {cell: index for index, cells in enumerate(regions) for cell in cells}
    edges = [set() for _ in regions]
    for (r, c), index in owner.items():
        for dr, dc in MOVES:
            neighbor = owner.get((r + dr, c + dc))
            if neighbor is not None and neighbor != index:
                edges[index].add(neighbor)
                edges[neighbor].add(index)

    def component_count(skip=None):
        remaining = set(range(len(edges)))
        if skip is not None:
            remaining.discard(skip)
        count = 0
        while remaining:
            count += 1
            stack = [remaining.pop()]
            while stack:
                index = stack.pop()
                for neighbor in edges[index]:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        return count

    baseline = component_count()
    articulation_regions = [
        index for index in range(len(regions))
        if component_count(index) > baseline
    ]

    output = [[0 for _ in range(w)] for _ in range(h)]
    for index in articulation_regions:
        for r, c in regions[index]:
            output[r][c] = 8
    return output
