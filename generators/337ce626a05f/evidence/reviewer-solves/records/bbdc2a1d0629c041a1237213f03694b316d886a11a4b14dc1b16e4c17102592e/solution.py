from collections import Counter


def _panel_signatures(grid):
    height = len(grid)
    width = len(grid[0])
    separators = [
        col for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    boundaries = [-1, *separators, width]
    signatures = []

    for left, right in zip(boundaries, boundaries[1:]):
        points = [
            (row, col)
            for row in range(height)
            for col in range(left + 1, right)
            if grid[row][col] not in (0, 5)
        ]
        if not points:
            continue
        top = min(row for row, _ in points)
        bottom = max(row for row, _ in points)
        signature = tuple(
            sum(grid[row][col] not in (0, 5) for col in range(left + 1, right))
            for row in range(top, bottom + 1)
        )
        signatures.append(signature)

    return signatures


def solve(grid):
    signatures = _panel_signatures(grid)
    if not signatures:
        return []

    frequencies = Counter(signatures)
    signature = max(signatures, key=lambda item: frequencies[item])
    output_width = max(signature)
    return [
        [8] * filled + [0] * (output_width - filled)
        for filled in signature
    ]
