"""Visible-example solution for the periodic-hole task."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    for period_r in range(1, min(5, height) + 1):
        for period_c in range(1, min(5, width) + 1):
            buckets = [[set() for _ in range(period_c)] for _ in range(period_r)]
            for row, values in enumerate(grid):
                for column, value in enumerate(values):
                    if value != 0:
                        buckets[row % period_r][column % period_c].add(value)
            if all(len(bucket) == 1 for line in buckets for bucket in line):
                tile = [[next(iter(bucket)) for bucket in line] for line in buckets]
                return [
                    [
                        value if value != 0 else tile[row % period_r][column % period_c]
                        for column, value in enumerate(values)
                    ]
                    for row, values in enumerate(grid)
                ]
    raise ValueError("no complete periodic pattern can be inferred")
