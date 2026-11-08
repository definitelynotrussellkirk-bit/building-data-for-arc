from collections import Counter


def _runs(indices):
    if not indices:
        return []
    out = []
    start = prev = indices[0]
    for value in indices[1:]:
        if value != prev + 1:
            out.append((start, prev + 1))
            start = value
        prev = value
    out.append((start, prev + 1))
    return out


def _mode_nonzero(values):
    counts = Counter(v for v in values if v != 0)
    if not counts:
        return 0
    return max(counts, key=lambda value: (counts[value], -value))


def solve(grid):
    """Compress the colored block matrix to colors, mirrored left-to-right."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])

    active_rows = [r for r in range(height) if any(grid[r][c] != 0 for c in range(width))]
    bands = _runs(active_rows)
    if not bands:
        return []

    active_cols = [c for c in range(width) if any(grid[r][c] != 0 for r in range(height))]
    left, right = active_cols[0], active_cols[-1] + 1

    # Each physical block is mostly one color.  Take a nonzero column mode in
    # every horizontal band; the tuple across bands is stable within a slot.
    signatures = []
    for c in range(left, right):
        signatures.append(tuple(
            _mode_nonzero(grid[r][c] for r in range(r0, r1))
            for r0, r1 in bands
        ))

    slots = []
    slot_start = left
    previous = signatures[0]
    for offset, signature in enumerate(signatures[1:], start=1):
        if signature != previous:
            slots.append((slot_start, left + offset))
            slot_start = left + offset
            previous = signature
    slots.append((slot_start, right))

    result = []
    for r0, r1 in bands:
        row = []
        for c0, c1 in slots:
            row.append(_mode_nonzero(
                grid[r][c]
                for r in range(r0, r1)
                for c in range(c0, c1)
            ))
        result.append(list(reversed(row)))
    return result
