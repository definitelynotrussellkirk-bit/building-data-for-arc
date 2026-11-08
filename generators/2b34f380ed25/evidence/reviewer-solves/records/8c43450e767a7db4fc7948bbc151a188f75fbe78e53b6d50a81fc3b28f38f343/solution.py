"""Visible-example solution for the exposed post-repair episode.

Standalone Python: no task generator, reference runtime, or answer imports.
"""
from collections import Counter


def _three_runs(lines):
    starts = set()
    for line in lines:
        begin = 0
        while begin < len(line):
            end = begin + 1
            while end < len(line) and line[end] == line[begin]:
                end += 1
            if line[begin] != 0 and end - begin == 3:
                starts.add(begin)
            begin = end
    return sorted(starts)


def _partition(starts, separators):
    groups = []
    current = []
    for index, start in enumerate(starts):
        if current and any(starts[current[-1]] + 2 < line < start for line in separators):
            groups.append(current)
            current = []
        current.append(index)
    if current:
        groups.append(current)
    return groups


def solve(grid):
    height, width = len(grid), len(grid[0])
    rows = _three_runs(list(zip(*grid)))
    cols = _three_runs(grid)
    if not rows or not cols:
        return [list(row) for row in grid]
    row_lines = [r for r in range(height)
                 if grid[r][0] not in (0, 4) and len(set(grid[r])) == 1]
    col_lines = [c for c in range(width)
                 if grid[0][c] not in (0, 4) and len({grid[r][c] for r in range(height)}) == 1]
    row_groups = _partition(rows, row_lines)
    col_groups = _partition(cols, col_lines)
    macro = []
    for top in rows:
        row = []
        for left in cols:
            colors = Counter(grid[r][c] for r in range(top, top + 3)
                             for c in range(left, left + 3) if grid[r][c] != 0)
            row.append(colors.most_common(1)[0][0] if colors else 0)
        macro.append(row)
    changed = [row[:] for row in macro]
    for rr in row_groups:
        for cc in col_groups:
            vertical = []
            horizontal = []
            for offset in range(len(cc) - 1):
                gap = range(cols[cc[offset]] + 3, cols[cc[offset + 1]])
                if any(all(grid[r][c] == 4 for r in range(rows[rr[0]], rows[rr[-1]] + 3)) for c in gap):
                    vertical.append(offset + 1)
            for offset in range(len(rr) - 1):
                gap = range(rows[rr[offset]] + 3, rows[rr[offset + 1]])
                if any(all(grid[r][c] == 4 for c in range(cols[cc[0]], cols[cc[-1]] + 3)) for r in gap):
                    horizontal.append(offset + 1)
            if not vertical and not horizontal:
                targets = {macro[r][c] for r in rr for c in cc} - {0, 1}
                if len(targets) == 1:
                    target = next(iter(targets))
                    for r in rr:
                        for c in cc:
                            if macro[r][c] == 1:
                                changed[r][c] = target
                continue
            for cut in vertical:
                if cut * 2 == len(cc):
                    order = cc[cut:] + cc[:cut]
                    for r in rr:
                        for destination, source in zip(cc, order):
                            changed[r][destination] = macro[r][source]
            for cut in horizontal:
                if cut * 2 == len(rr):
                    order = rr[cut:] + rr[:cut]
                    for destination, source in zip(rr, order):
                        for c in cc:
                            changed[destination][c] = macro[source][c]
    output = [list(row) for row in grid]
    for ri, top in enumerate(rows):
        for ci, left in enumerate(cols):
            for r in range(top, top + 3):
                for c in range(left, left + 3):
                    output[r][c] = changed[ri][ci]
    return output
