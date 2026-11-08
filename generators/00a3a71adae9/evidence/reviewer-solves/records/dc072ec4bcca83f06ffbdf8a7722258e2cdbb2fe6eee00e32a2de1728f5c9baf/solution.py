from collections import deque


def _components(grid, color):
    """Return 4-connected components of ``color`` in top-left order."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(tuple(sorted(cells)))
    return result


def solve(grid):
    """Select the blue motif favored by the light-blue mask and recolor it 8."""
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    mask = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    motifs = _components(grid, 2)
    if not motifs:
        return []

    ranked = []
    for index, cells in enumerate(motifs):
        grown = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if 0 <= r + dr < h and 0 <= c + dc < w
        }
        overlap = len(grown & mask)
        if mask:
            distance = min(
                abs(r - mr) + abs(c - mc)
                for r, c in grown
                for mr, mc in mask
            )
        else:
            distance = h + w
        ranked.append((-overlap, distance, index, cells))

    cells = min(ranked)[:-1]  # rank only; retained below for clarity
    del cells
    chosen = min(ranked)[-1]
    r0 = min(r for r, _ in chosen)
    r1 = max(r for r, _ in chosen)
    c0 = min(c for _, c in chosen)
    c1 = max(c for _, c in chosen)
    occupied = set(chosen)
    return [
        [8 if (r, c) in occupied else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
