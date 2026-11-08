"""One candidate inferred from this episode's five visible demonstrations."""


def solve(grid):
    separators = [r for r, row in enumerate(grid) if all(v == 8 for v in row)]
    bands = [(a + 1, b) for a, b in zip(separators, separators[1:])]
    size = bands[0][1] - bands[0][0]
    result = [[] for _ in range(size)]
    for column, left in enumerate(range(1, len(grid[0]), size + 1)):
        frame = fill = motif = None
        for top, bottom in bands:
            tile = [row[left:left + size] for row in grid[top:bottom]]
            inside = {v for row in tile[1:-1] for v in row[1:-1]}
            if len(inside) == 1 and not inside.intersection({1, 2, 8}):
                frame, fill = grid[top][0], next(iter(inside))
            elif inside == {2, 8}:
                motif = tile
        if motif is None or frame is None or fill is None:
            raise ValueError("Missing solid tile or repeated pattern")
        for r, row in enumerate(motif):
            if column:
                result[r].append(8)
            result[r].extend(frame if v == 1 else fill if v == 2 else v for v in row)
    return result
