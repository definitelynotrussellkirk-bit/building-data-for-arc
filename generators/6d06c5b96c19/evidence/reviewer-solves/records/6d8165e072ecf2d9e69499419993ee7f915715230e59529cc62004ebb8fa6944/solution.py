"""Blind solution for task 6d06c5b96c19."""


def solve(grid):
    """Remove the left control column and cyclically shift rows down.

    The row containing color 2 in the leftmost column encodes the downward
    cyclic row offset. The remaining columns are the payload.
    """
    marker_rows = [r for r, row in enumerate(grid) if row and row[0] == 2]
    if len(marker_rows) != 1:
        raise ValueError(f"expected exactly one left-edge marker 2, got {marker_rows}")

    offset = marker_rows[0]
    payload = [list(row[1:]) for row in grid]
    if not payload:
        return []
    offset %= len(payload)
    if offset == 0:
        return payload
    return payload[-offset:] + payload[:-offset]
