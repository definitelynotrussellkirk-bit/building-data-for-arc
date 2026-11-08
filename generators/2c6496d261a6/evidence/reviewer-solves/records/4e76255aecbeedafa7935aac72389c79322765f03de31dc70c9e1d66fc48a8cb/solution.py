from collections import Counter, defaultdict


def solve(grid):
    """Keep the horizontal signal color and the unique marker; erase noise."""
    positions = defaultdict(list)
    counts = Counter()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))
                counts[value] += 1

    singleton_colors = {color for color, count in counts.items() if count == 1}

    # The signal is the non-background color whose cells all occupy one row.
    # Prefer the longest such row if malformed input supplies more than one.
    horizontal_candidates = [
        color
        for color, cells in positions.items()
        if len(cells) >= 2 and len({r for r, _ in cells}) == 1
    ]
    horizontal_color = max(
        horizontal_candidates,
        key=lambda color: len(positions[color]),
        default=None,
    )

    keep = set(singleton_colors)
    if horizontal_color is not None:
        keep.add(horizontal_color)

    return [
        [value if value in keep else 0 for value in row]
        for row in grid
    ]
