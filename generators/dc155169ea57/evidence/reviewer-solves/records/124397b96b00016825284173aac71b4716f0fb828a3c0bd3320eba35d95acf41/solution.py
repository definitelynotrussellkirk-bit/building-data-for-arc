from collections import Counter, deque


def solve(grid):
    """Drop color-1 components through a one-cell-wide horizontal sieve."""
    height = len(grid)
    width = len(grid[0])

    # The separator is the row containing color 2; generated examples use one
    # complete horizontal row.  The most common remaining color is background.
    sieve_row = next(r for r, row in enumerate(grid) if 2 in row)
    background = Counter(cell for row in grid for cell in row if cell not in (1, 2)).most_common(1)[0][0]

    cells = {(r, c) for r in range(sieve_row) for c in range(width) if grid[r][c] == 1}
    components = []
    unseen = set(cells)
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    component.add((nr, nc))
                    queue.append((nr, nc))
        components.append(component)

    result = [row[:] for row in grid]
    for r, c in cells:
        result[r][c] = background

    # Lower objects settle first.  The examples keep paths disjoint, but the
    # occupancy check also makes stacked components behave like gravity.
    components.sort(key=lambda comp: max(r for r, _ in comp), reverse=True)
    settled = set()

    for component in components:
        position = set(component)
        while True:
            proposed = {(r + 1, c) for r, c in position}
            if any(r >= height for r, _ in proposed):
                break
            if proposed & settled:
                break

            # A single-cell horizontal slice may occupy/cross the sieve;
            # a wider slice is caught even if a thinner part of this same
            # object previously opened one of those columns.
            sieve_slice = [(r, c) for r, c in proposed if r == sieve_row]
            if len(sieve_slice) >= 2:
                break

            for r, c in position:
                if r == sieve_row:
                    result[r][c] = background
            position = proposed

            for r, c in position:
                if r == sieve_row:
                    result[r][c] = 1

        for r, c in position:
            result[r][c] = 1
        settled.update(position)

    return result
