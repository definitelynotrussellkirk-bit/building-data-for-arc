from __future__ import annotations

from typing import Sequence

# Each non-background object is a solid 3x3 tile.  The non-5 cells form one
# of eight directional glyphs; the all-5 tile belongs in the center.
_MASK_TO_SLOT = {
    frozenset({(0, 0), (0, 1), (1, 0)}): (0, 0),          # upper-left
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}): (0, 1),  # up
    frozenset({(0, 1), (0, 2), (1, 2)}): (0, 2),          # upper-right
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}): (1, 0),  # left
    frozenset({(0, 2), (1, 1), (1, 2), (2, 2)}): (1, 2),  # right
    frozenset({(1, 0), (2, 0), (2, 1)}): (2, 0),          # lower-left
    frozenset({(1, 1), (2, 0), (2, 1), (2, 2)}): (2, 1),  # down
    frozenset({(1, 2), (2, 1), (2, 2)}): (2, 2),          # lower-right
}


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height < 3 or width < 3 or any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid at least 3x3")

    found: dict[tuple[int, int], list[list[int]]] = {}

    # Exact 3x3 glyph matching disambiguates tiles even when neighboring tiles
    # touch and therefore form one larger connected component.
    for row in range(height - 2):
        for col in range(width - 2):
            tile = [list(input_row[col : col + 3]) for input_row in grid[row : row + 3]]
            if any(value == 0 for tile_row in tile for value in tile_row):
                continue

            accent = frozenset(
                (r, c)
                for r in range(3)
                for c in range(3)
                if tile[r][c] != 5
            )
            accent_colors = {tile[r][c] for r, c in accent}

            if not accent:
                slot = (1, 1)
            elif len(accent_colors) == 1 and accent in _MASK_TO_SLOT:
                slot = _MASK_TO_SLOT[accent]
            else:
                continue

            previous = found.get(slot)
            if previous is not None and previous != tile:
                raise ValueError(f"multiple candidate tiles for output slot {slot}")
            found[slot] = tile

    expected_slots = {(r, c) for r in range(3) for c in range(3)}
    if set(found) != expected_slots:
        missing = sorted(expected_slots - set(found))
        raise ValueError(f"could not locate every directional tile; missing {missing}")

    output = [[5 for _ in range(9)] for _ in range(9)]
    for (slot_row, slot_col), tile in found.items():
        for r in range(3):
            for c in range(3):
                output[3 * slot_row + r][3 * slot_col + c] = tile[r][c]
    return output
