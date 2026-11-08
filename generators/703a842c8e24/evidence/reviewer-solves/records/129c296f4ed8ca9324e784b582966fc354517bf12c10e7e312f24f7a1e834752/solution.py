from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep each row header; cyclically rotate its remaining cells right."""
    output: list[list[int]] = []
    for row in grid:
        header = row[0]
        body = row[1:]
        if not body:
            output.append(row[:])
            continue
        shift = header % len(body)
        shifted = body[:] if shift == 0 else body[-shift:] + body[:-shift]
        output.append([header, *shifted])
    return output
