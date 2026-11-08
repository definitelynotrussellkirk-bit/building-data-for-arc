from collections import defaultdict


def solve(grid):
    """Collapse noisy color regions to their spatially ordered color sequence.

    The examples contain one broad region per color.  Their centroids are nearly
    aligned either top-to-bottom or left-to-right; the output is one cell per
    color along that same dominant axis.  A diagonal/tied layout is rendered as
    a row, which is the deterministic horizontal default.
    """
    if not grid or not grid[0]:
        return []

    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            positions[color].append((r, c))

    centroids = {}
    for color, cells in positions.items():
        n = len(cells)
        centroids[color] = (
            sum(r for r, _ in cells) / n,
            sum(c for _, c in cells) / n,
        )

    row_values = [rc[0] for rc in centroids.values()]
    col_values = [rc[1] for rc in centroids.values()]
    row_span = max(row_values) - min(row_values)
    col_span = max(col_values) - min(col_values)

    if row_span > col_span:
        ordered = sorted(centroids, key=lambda color: (centroids[color][0], centroids[color][1], color))
        return [[color] for color in ordered]

    ordered = sorted(centroids, key=lambda color: (centroids[color][1], centroids[color][0], color))
    return [ordered]
