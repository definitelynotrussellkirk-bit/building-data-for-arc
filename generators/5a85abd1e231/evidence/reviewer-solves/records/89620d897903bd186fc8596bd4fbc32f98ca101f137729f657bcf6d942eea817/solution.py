"""Visible-only solution for the reviewer blind task.

The input contains nine disjoint 3x3 tiles on a zero background.  The shape of
an accent color inside each tile names the tile's destination in a 3x3 mosaic.
Tiles may touch and accent colors may repeat, so the implementation finds a
non-overlapping exact cover rather than splitting connected components.
"""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height < 3 or width < 3 or any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid at least 3x3")

    base = 5
    empty = 0
    mask_to_slot = {
        frozenset({(0, 0), (0, 1), (1, 0)}): (0, 0),
        frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}): (0, 1),
        frozenset({(0, 1), (0, 2), (1, 2)}): (0, 2),
        frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}): (1, 0),
        frozenset(): (1, 1),
        frozenset({(0, 2), (1, 1), (1, 2), (2, 2)}): (1, 2),
        frozenset({(1, 0), (2, 0), (2, 1)}): (2, 0),
        frozenset({(1, 1), (2, 0), (2, 1), (2, 2)}): (2, 1),
        frozenset({(1, 2), (2, 1), (2, 2)}): (2, 2),
    }

    all_nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != empty
    }

    candidates = {slot: [] for slot in mask_to_slot.values()}
    for top in range(height - 2):
        for left in range(width - 2):
            tile = tuple(
                tuple(grid[top + dr][left + dc] for dc in range(3))
                for dr in range(3)
            )
            if any(value == empty for row in tile for value in row):
                continue

            accent_positions = frozenset(
                (dr, dc)
                for dr in range(3)
                for dc in range(3)
                if tile[dr][dc] != base
            )
            slot = mask_to_slot.get(accent_positions)
            if slot is None:
                continue

            accent_values = {
                tile[dr][dc] for dr, dc in accent_positions
            }
            if len(accent_values) > 1:
                continue

            cells = frozenset(
                (top + dr, left + dc)
                for dr in range(3)
                for dc in range(3)
            )
            candidates[slot].append((cells, tile, top, left))

    if any(not options for options in candidates.values()):
        raise ValueError("could not find every motif tile")

    # Constrained slots first; leave the often-ambiguous all-5 center for later.
    slots = sorted(
        candidates,
        key=lambda slot: (slot == (1, 1), len(candidates[slot])),
    )
    chosen = {}

    def search(index, used):
        if index == len(slots):
            return used == all_nonzero

        slot = slots[index]
        for cells, tile, top, left in candidates[slot]:
            if cells & used:
                continue
            # Every selected window must belong to the observed nonzero support.
            if not cells <= all_nonzero:
                continue
            chosen[slot] = tile
            if search(index + 1, used | cells):
                return True
            del chosen[slot]
        return False

    if not search(0, frozenset()):
        raise ValueError("motif windows do not form a nine-tile exact cover")

    output = [[base for _ in range(9)] for _ in range(9)]
    for (tile_row, tile_col), tile in chosen.items():
        for dr in range(3):
            for dc in range(3):
                output[3 * tile_row + dr][3 * tile_col + dc] = tile[dr][dc]
    return output
