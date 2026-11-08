def solve(grid):
    """Infer rotated copies from the visible episode's four marker colors."""
    height = len(grid)
    width = len(grid[0])
    marker_turns = {2: 0, 3: 1, 4: 2, 5: 3}
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or color in marker_turns or (row, col) in seen:
                continue
            cells = []
            todo = [(row, col)]
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            objects.append((len(cells), color, cells))
    if not objects:
        raise ValueError("No prototype in input")
    _, color, cells = max(objects, key=lambda item: item[0])
    top = min(r for r, c in cells)
    left = min(c for r, c in cells)
    shape = {(r-top, c-left) for r, c in cells}
    rotations = [shape]
    for _ in range(3):
        previous = rotations[-1]
        previous_height = max(r for r, c in previous) + 1
        rotations.append({(c, previous_height-1-r) for r, c in previous})
    result = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            turns = marker_turns.get(grid[row][col])
            if turns is None:
                continue
            for dr, dc in rotations[turns]:
                nr, nc = row+dr, col+dc
                if 0 <= nr < height and 0 <= nc < width:
                    result[nr][nc] = color
    return result
