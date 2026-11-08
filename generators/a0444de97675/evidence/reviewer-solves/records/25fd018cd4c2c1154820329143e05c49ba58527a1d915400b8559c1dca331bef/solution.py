def solve(grid):
    """Select the body object whose area equals the number of blue header marks."""
    height = len(grid)
    width = len(grid[0])
    target_area = sum(value == 1 for value in grid[0])

    seen = set()
    objects = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (1 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            objects.append(cells)

    matches = [cells for cells in objects if len(cells) == target_area]
    if len(matches) != 1:
        raise ValueError(f"expected one area-{target_area} body object, found {len(matches)}")

    target = matches[0]
    r0 = min(r for r, _ in target)
    r1 = max(r for r, _ in target)
    c0 = min(c for _, c in target)
    c1 = max(c for _, c in target)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    output = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        output.extend([doubled[:], doubled[:]])
    return output
