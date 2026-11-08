"""Visible-example solution for reviewer task 5a85abd1e231."""


def _tiles(grid):
    """Partition all non-zero cells into filled 3x3 tiles."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    nonzero = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }

    candidates = []
    for top in range(height - 2):
        for left in range(width - 2):
            cells = frozenset(
                (row, col)
                for row in range(top, top + 3)
                for col in range(left, left + 3)
            )
            if cells <= nonzero:
                candidates.append((top, left, cells))

    by_cell = {cell: [] for cell in nonzero}
    for index, (_, _, cells) in enumerate(candidates):
        for cell in cells:
            by_cell[cell].append(index)

    chosen = []

    def cover(remaining):
        if not remaining:
            return True
        cell = min(
            remaining,
            key=lambda item: sum(candidates[index][2] <= remaining for index in by_cell[item]),
        )
        for index in by_cell[cell]:
            top, left, cells = candidates[index]
            if not cells <= remaining:
                continue
            chosen.append((top, left))
            if cover(remaining - cells):
                return True
            chosen.pop()
        return False

    if len(nonzero) != 81 or not cover(nonzero) or len(chosen) != 9:
        raise ValueError("expected nine non-overlapping filled 3x3 tiles")
    return chosen


def _direction(value):
    """Map a signed displacement to the corresponding 0/1/2 output band."""
    if value < 0:
        return 0
    if value > 0:
        return 2
    return 1


def solve(grid):
    """Arrange the nine 3x3 tiles according to each tile's accent direction."""
    output = [[0 for _ in range(9)] for _ in range(9)]
    occupied = set()

    for top, left in _tiles(grid):
        tile = [source_row[left : left + 3] for source_row in grid[top : top + 3]]
        accent = [
            (row, col)
            for row in range(3)
            for col in range(3)
            if tile[row][col] != 5
        ]

        if accent:
            row_displacement = sum(row - 1 for row, _ in accent)
            col_displacement = sum(col - 1 for _, col in accent)
            target_row = _direction(row_displacement)
            target_col = _direction(col_displacement)
        else:
            target_row = target_col = 1

        target = (target_row, target_col)
        if target in occupied:
            raise ValueError(f"two tiles map to output position {target}")
        occupied.add(target)

        for row in range(3):
            for col in range(3):
                output[3 * target_row + row][3 * target_col + col] = tile[row][col]

    if occupied != {(row, col) for row in range(3) for col in range(3)}:
        raise ValueError("input must provide exactly one tile for each output position")
    return output
