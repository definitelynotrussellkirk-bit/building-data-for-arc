from collections import deque


def _components(cells):
    remaining = set(cells)
    out = []
    while remaining:
        start = remaining.pop()
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        out.append(comp)
    return out


def solve(grid):
    """Complete partial copies of the left-hand reference object."""
    height = len(grid)
    width = len(grid[0])

    # The solid 9 column separates a complete reference from the work area.
    separators = [
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    if not separators:
        return [row[:] for row in grid]
    sep = separators[0]

    reference_cells = [
        (r, c)
        for r in range(height)
        for c in range(sep)
        if grid[r][c] not in (0, 9)
    ]
    if not reference_cells:
        return [row[sep + 1:] for row in grid]

    # The reference object uses one repair color in all visible examples.
    counts = {}
    for r, c in reference_cells:
        counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    color = max(counts, key=counts.get)
    prototype = {(r, c) for r, c in reference_cells if grid[r][c] == color}

    work = [row[sep + 1:] for row in grid]
    work_width = len(work[0]) if work else 0
    colored = {
        (r, c)
        for r in range(height)
        for c in range(work_width)
        if work[r][c] == color
    }

    for comp in _components(colored):
        candidates = set()
        for cr, cc in comp:
            for pr, pc in prototype:
                candidates.add((cr - pr, cc - pc))

        valid = []
        for dr, dc in candidates:
            placed = {(pr + dr, pc + dc) for pr, pc in prototype}
            if not comp <= placed:
                continue
            if not all(0 <= r < height and 0 <= c < work_width for r, c in placed):
                continue
            # Completing a copy may fill blanks, but must not overwrite a distractor.
            if any(work[r][c] not in (0, color) for r, c in placed):
                continue
            # Prefer the placement that explains the most currently visible target cells.
            overlap = len(placed & colored)
            valid.append((overlap, -sum(abs(r - cr) + abs(c - cc) for r, c in placed for cr, cc in comp), dr, dc, placed))

        if valid:
            placed = max(valid, key=lambda item: item[:4])[4]
            for r, c in placed:
                if work[r][c] == 0:
                    work[r][c] = color

    return work
