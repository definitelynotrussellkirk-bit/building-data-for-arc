def solve(grid):
    """Rotate each row's payload right by the row's leading value."""
    out = []
    for row in grid:
        if not row:
            out.append([])
            continue
        head = row[0]
        payload = list(row[1:])
        if payload:
            shift = int(head) % len(payload)
            if shift:
                payload = payload[-shift:] + payload[:-shift]
        out.append([head] + payload)
    return out
