"""Independent component-based oracle for the proposed stack-side behavior.

This implementation never calls the generator's lattice reader or rule mirror.
It counts complete eight-cell ring components and aligns their origins.
"""
from collections import Counter, defaultdict


def independent_output(grid, stack_side="toward_main"):
    if stack_side not in ("toward_main", "toward_small"):
        raise ValueError("unknown stack_side")
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("a nonempty rectangular grid is required")
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value not in (0, 1)}
    components = defaultdict(list)
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        cells, todo = set(), [start]
        pending.remove(start)
        while todo:
            r, c = todo.pop()
            cells.add((r, c))
            for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if (nr, nc) in pending and grid[nr][nc] == color:
                    pending.remove((nr, nc))
                    todo.append((nr, nc))
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        ring = {(top+r, left+c) for r in range(3) for c in range(3)
                if (r, c) != (1, 1)}
        if cells != ring or grid[top+1][left+1] != 0:
            raise ValueError("expected disjoint complete hollow 3x3 rings")
        components[color].append((top, left))
    if 8 not in components or len(components) != 3:
        raise ValueError("expected cyan and exactly two small colors")
    main = components[8]
    wide = max(c for _, c in main)-min(c for _, c in main) > max(r for r, _ in main)-min(r for r, _ in main)
    long_axis, short_axis = (1, 0) if wide else (0, 1)
    origin = min(point[long_axis] for point in main)
    small_colors = [color for color in components if color != 8]
    main_side = min(point[short_axis] for point in main)
    small_sides = [min(point[short_axis] for point in components[color]) for color in small_colors]
    if not (all(main_side > side for side in small_sides) or
            all(main_side < side for side in small_sides)):
        raise ValueError("small pictures must share one short-axis side")
    main_at_end = all(main_side > side for side in small_sides)
    if stack_side == "toward_small":
        main_at_end = not main_at_end
    counts = defaultdict(Counter)
    for color, origins in components.items():
        for point in origins:
            delta = point[long_axis] - origin
            if delta < 0 or delta % 4:
                raise ValueError("ring origins must align on the main stride")
            counts[delta // 4][color] += 1
    if set(counts) != set(range(7)) or any(counts[i][8] == 0 for i in range(7)):
        raise ValueError("expected seven nonempty main slices")
    if any(len(set(counts[i]) - {8}) > 1 for i in range(7)):
        raise ValueError("small pictures cannot overlap a long-axis slice")
    extent = max(sum(counts[i].values()) for i in range(7))
    stacks = []
    for i in range(7):
        cyan = [8] * counts[i][8]
        other = [color for color, count in sorted(counts[i].items()) if color != 8
                 for _ in range(count)]
        empty = [0] * (extent-len(cyan)-len(other))
        stacks.append(empty + other + cyan if main_at_end else cyan + other + empty)
    return [list(row) for row in zip(*stacks)] if wide else stacks
