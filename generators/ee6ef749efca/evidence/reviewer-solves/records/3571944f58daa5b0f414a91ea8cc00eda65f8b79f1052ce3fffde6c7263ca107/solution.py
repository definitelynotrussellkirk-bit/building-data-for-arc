def solve(grid):
    """Stamp the largest color-6 component at each color-2 marker."""
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] == 6}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    output = [[0] * width for _ in range(height)]
    if not components:
        return output
    template = max(components, key=len)
    top = min(r for r, _ in template)
    left = min(c for _, c in template)
    offsets = [(r - top, c - left) for r, c in template]
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 2:
                for dr, dc in offsets:
                    if r + dr < height and c + dc < width:
                        output[r + dr][c + dc] = 6
    return output
