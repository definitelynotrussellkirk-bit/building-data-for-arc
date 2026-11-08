"""Visible-example hypothesis for connecting colored endpoint pairs."""


def solve(grid):
    out = [row[:] for row in grid]
    colors = sorted({value for row in grid for value in row} - {0, 8}, reverse=True)

    for color in colors:
        endpoints = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(endpoints) != 2:
            continue
        (r0, c0), (r1, c1) = endpoints
        if abs(c1 - c0) > abs(r1 - r0):
            corner = (r0, c1)
        else:
            corner = (r1, c0)

        for (ra, ca), (rb, cb) in [(endpoints[0], corner), (corner, endpoints[1])]:
            dr = (rb > ra) - (rb < ra)
            dc = (cb > ca) - (cb < ca)
            length = max(abs(rb - ra), abs(cb - ca))
            for offset in range(length + 1):
                r = ra + offset * dr
                c = ca + offset * dc
                if grid[r][c] != 8:
                    out[r][c] = color

    return out
