from collections import Counter


def solve(grid):
    """Stamp the colored motif at every 9 marker, clipping at the border."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=counts.get)
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    motif = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (background, 9)
    ]

    if not markers or not motif:
        return [row[:] for row in grid]

    # The template marker is the 9 most tightly surrounded by the motif.
    # The max-distance term identifies the smallest enclosing stamp; the
    # remaining terms make the choice deterministic if two markers tie.
    def anchor_score(marker):
        mr, mc = marker
        chebyshev = [max(abs(r - mr), abs(c - mc)) for r, c, _ in motif]
        manhattan = [abs(r - mr) + abs(c - mc) for r, c, _ in motif]
        adjacent = sum(distance <= 1 for distance in chebyshev)
        return (max(chebyshev), sum(manhattan), -adjacent, mr, mc)

    anchor_r, anchor_c = min(markers, key=anchor_score)
    offsets = [(r - anchor_r, c - anchor_c, value) for r, c, value in motif]

    result = [[background for _ in range(width)] for _ in range(height)]
    for marker_r, marker_c in markers:
        for dr, dc, value in offsets:
            r = marker_r + dr
            c = marker_c + dc
            if 0 <= r < height and 0 <= c < width:
                result[r][c] = value
    return result
