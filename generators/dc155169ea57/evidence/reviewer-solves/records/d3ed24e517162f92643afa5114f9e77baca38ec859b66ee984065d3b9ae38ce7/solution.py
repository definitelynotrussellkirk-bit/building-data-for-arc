from collections import deque


def solve(grid):
    """Drop color-1 components through the horizontal color-2 sieve."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or not w:
        return [row[:] for row in grid]

    # The visible tasks use a complete horizontal separator of color 2.
    sieve_rows = [r for r, row in enumerate(grid) if row and all(v == 2 for v in row)]
    if len(sieve_rows) != 1:
        return [row[:] for row in grid]
    sieve = sieve_rows[0]

    seen = set()
    components = []
    for r in range(sieve):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < sieve
                        and 0 <= nc < w
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            components.append(comp)

    result = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if result[r][c] == 1:
                result[r][c] = 8

    for comp in components:
        shift = 0
        traversed_columns = set()
        blocked = False
        while True:
            next_shift = shift + 1
            if any(r + next_shift >= h for r, _ in comp):
                break
            on_sieve = [(r, c) for r, c in comp if r + next_shift == sieve]
            if len(on_sieve) > 1:
                blocked = True
                break
            if on_sieve:
                traversed_columns.add(on_sieve[0][1])
            shift = next_shift

        # Passage removes the corresponding sieve material.  A lodged object is
        # overlaid afterwards, so its final one-cell contact remains color 1.
        for c in traversed_columns:
            result[sieve][c] = 8

        for r, c in comp:
            nr = r + shift
            if not blocked and nr == sieve:
                continue
            result[nr][c] = 1

    return result
