"""Visible-example solution: complete grids of congruent colored marks."""

from collections import Counter, defaultdict


def _components(grid, color):
    """Return 8-connected components of one marker color."""
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        pending = [first]
        cells = [first]
        while pending:
            r, c = pending.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    neighbor = (r + dr, c + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        pending.append(neighbor)
                        cells.append(neighbor)
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        shape = tuple(sorted((r - top, c - left) for r, c in cells))
        result.append((shape, (top, left), cells))
    return result


def _largest_complete_grid(positions, seed):
    """Find a complete row-by-column product containing the seed position."""
    by_row = defaultdict(set)
    for row, column in positions:
        by_row[row].add(column)

    seed_row, seed_column = seed
    other_rows = sorted(
        row
        for row, columns in by_row.items()
        if row != seed_row and seed_column in columns
    )

    best_key = None
    best_positions = set()
    for mask in range(1 << len(other_rows)):
        rows = [seed_row] + [
            row for i, row in enumerate(other_rows) if mask & (1 << i)
        ]
        columns = set(by_row[seed_row])
        for row in rows[1:]:
            columns.intersection_update(by_row[row])

        candidate = {(row, column) for row in rows for column in columns}
        # The visible examples have a unique largest set. Prefer a genuinely
        # two-dimensional set if an unseen example ties a rectangle and a line;
        # then use sorted coordinates only to make the choice deterministic.
        key = (
            len(candidate),
            min(len(rows), len(columns)),
            tuple(sorted(candidate)),
        )
        if best_key is None or key > best_key:
            best_key = key
            best_positions = candidate
    return best_positions


def solve(grid):
    result = [list(row) for row in grid]
    if not grid or not grid[0]:
        return result

    colors = Counter(value for row in grid for value in row)
    target = 8
    if target not in colors:
        return result

    # Across every visible example the background and the unchanged pattern
    # ink are the two most frequent non-blue colors. The remaining color is
    # the source marker color. This inference avoids fixing its numeric value.
    non_target = sorted(
        (color for color in colors if color != target),
        key=lambda color: (-colors[color], color),
    )
    if len(non_target) < 3:
        return result
    source = non_target[-1]

    source_by_shape = defaultdict(dict)
    for shape, position, cells in _components(grid, source):
        source_by_shape[shape][position] = cells

    seeds_by_shape = defaultdict(list)
    for shape, position, cells in _components(grid, target):
        seeds_by_shape[shape].append(position)

    for shape, seeds in seeds_by_shape.items():
        candidates = source_by_shape[shape]
        positions = set(candidates) | set(seeds)
        chosen = set()
        for seed in seeds:
            chosen.update(_largest_complete_grid(positions, seed))
        for position in chosen:
            for r, c in candidates.get(position, ()):
                result[r][c] = target
    return result
