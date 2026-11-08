def solve(grid):
    """Reflect the dense template; marker positions select color replacements."""
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    component = max(components, key=len)
    top = min(r for r, _ in component)
    left = min(c for _, c in component)
    tile_h = max(r for r, _ in component) - top + 1
    tile_w = max(c for _, c in component) - left + 1
    template = [row[left:left + tile_w] for row in grid[top:top + tile_h]]
    result = [[0] * width for _ in range(height)]
    for quadrant_r in range(2):
        for quadrant_c in range(2):
            row0 = top + quadrant_r * tile_h
            col0 = left + quadrant_c * tile_w
            def source_color(r, c):
                sr = tile_h - 1 - r if quadrant_r else r
                sc = tile_w - 1 - c if quadrant_c else c
                return template[sr][sc]
            mapping = {}
            if quadrant_r == quadrant_c == 0:
                mapping = {color: color for row in template for color in row}
            else:
                for r in range(tile_h):
                    for c in range(tile_w):
                        if row0 + r < height and col0 + c < width:
                            marker = grid[row0 + r][col0 + c]
                            if marker:
                                mapping.setdefault(source_color(r, c), marker)
            for r in range(tile_h):
                for c in range(tile_w):
                    if row0 + r < height and col0 + c < width:
                        result[row0 + r][col0 + c] = mapping.get(source_color(r, c), 0)
    return result
