"""Construct ten downward nozzle scenes without retries or original-example data.

input_templates(seed=0) returns six demonstration grids and four query grids.
Roles are background0, wall1, dye2, blockers3/4 and outside distractors5.
The native family owns palette permutations and global D4 presentation.
"""
from collections import Counter
import hashlib
import random


# name, (height,width), stride, cap, bend, throat, phase lengths, flare steps, clip left
PROFILES = (
    ("core_stride1", (25, 24), 1, (3, 18), (6, 18), (8, 13), (3, 5), 3, False),
    ("core_stride2_clipped_large", (30, 30), 2, (1, 17), (4, 14), (2, 8), (3, 6), 4, True),
    ("compact_stride1", (22, 21), 1, (3, 16), (6, 15), (7, 11), (3, 4), 2, False),
    ("stride3_reservoir", (27, 24), 3, (3, 18), (6, 17), (8, 12), (3, 5), 2, False),
    ("stride2_bent", (26, 25), 2, (4, 19), (7, 18), (9, 13), (3, 5), 3, False),
    ("stride3_long", (29, 27), 3, (3, 20), (6, 19), (8, 14), (3, 5), 3, False),
    ("query_stride1", (23, 22), 1, (2, 16), (5, 15), (7, 11), (3, 4), 3, False),
    ("query_stride2_clipped", (28, 26), 2, (1, 14), (3, 12), (2, 7), (2, 5), 5, True),
    ("query_stride3_large", (30, 30), 3, (4, 21), (7, 20), (9, 15), (3, 5), 3, False),
    ("query_stride1_long", (28, 27), 1, (3, 20), (6, 19), (9, 14), (3, 5), 4, False),
)


def _integer(value, name):
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError(name + " must be an exact integer in 0..2**63-1")


def _rng(seed, index):
    value = hashlib.sha256(f"b9e38dc0:constructive:{seed}:profile:{index}".encode()).digest()
    return random.Random(int.from_bytes(value, "big"))


def _scene(spec, rng):
    name, shape, stride, cap, bend, throat, phases, steps, clipped = spec
    height, width = shape
    shift = rng.randrange(2) if clipped else rng.randrange(-1, 2)
    cap = tuple(c + shift for c in cap)
    bend = (bend[0] + shift - rng.randrange(2), bend[1] + shift)
    throat = tuple(c + shift for c in throat)
    cap_row = 3 + rng.randrange(2)
    throat_rows = 1 + rng.randrange(2)
    board = [[0] * width for _ in range(height)]
    wall = {(cap_row, c) for c in range(cap[0], cap[1] + 1)}
    rails = [{}, {}]
    row, previous = cap_row, cap
    for target, length in zip((bend, throat), phases):
        assert all(abs(b - a) <= length for a, b in zip(previous, target))
        for offset in range(1, length + 1):
            columns = tuple(a + (b - a) * offset // length for a, b in zip(previous, target))
            assert 0 <= columns[0] < columns[1] < width and columns[1] - columns[0] >= 4
            row += 1
            for rail, col in zip(rails, columns):
                rail[row] = col
                wall.add((row, col))
        previous = target
    for _ in range(throat_rows):
        row += 1
        for rail, col in zip(rails, throat):
            rail[row] = col
            wall.add((row, col))
    throat_row = row
    ends = []
    for side, start_col, rail in zip((-1, 1), throat, rails):
        count = min(steps, start_col) if clipped and side == -1 else steps
        assert count >= 2
        for step in range(1, count + 1):
            col = start_col + side * step
            assert 0 <= col < width
            for offset in range(1, stride + 1):
                r = throat_row + (step - 1) * stride + offset
                assert r < height
                rail[r] = col
                wall.add((r, col))
        ends.append((throat_row + count * stride, start_col + side * count))
    final_tip = max(r for r, c in ends)
    assert height - final_tip - 1 >= 4
    for r, c in wall:
        board[r][c] = 1

    def edge(r, side_index):
        if r in rails[side_index]:
            return rails[side_index][r]
        end_r, end_c = ends[side_index]
        side = (-1, 1)[side_index]
        assert r > end_r
        return end_c + side * ((r - end_r + stride - 1) // stride)

    inside = {(r, c) for r in range(cap_row + 1, height)
              for c in range(max(0, edge(r, 0) + 1), min(width, edge(r, 1)))}

    def put(r, c, color, interior):
        assert 0 <= r < height and 0 <= c < width and board[r][c] == 0
        assert ((r, c) in inside) is interior
        board[r][c] = color

    # The first in-band marker is a short multi-cell dye patch. Its color is
    # neither the most frequent nonwall color nor necessarily the first global marker.
    dye_row = cap_row + 1
    dye_start = (edge(dye_row, 0) + edge(dye_row, 1)) // 2 - rng.randrange(2)
    dye_cells = [(dye_row, dye_start + i) for i in range(2 + rng.randrange(2))]
    for r, c in dye_cells:
        put(r, c, 2, True)

    # The five-cell throat blocker is larger than the dye and lies before both
    # tips. A second color lies beyond both tips in separate, unshadowed columns.
    first_depth, second_depth = throat_row, final_tip + 2
    first_col = throat[0] + 1
    lo2 = max(0, edge(second_depth, 0) + 1)
    hi2 = min(width - 1, edge(second_depth, 1) - 1)
    second_col = min(hi2 - 1, max(first_col + 4, lo2 + 3 * (hi2 - lo2 + 1) // 4))
    blockers = [(first_depth - 1, first_col + i, 3) for i in range(2)]
    blockers += [(first_depth, first_col + i, 3) for i in range(3)]
    blockers += [(second_depth, second_col + i, 4) for i in range(2)]
    for r, c, color in blockers:
        put(r, c, color, True)

    # Larger decoy behind the closed cap, aligned with columns of the later band.
    behind = [(r, dye_start - 1 + c) for r in (0, 1) for c in range(3)]
    for r, c in behind:
        put(r, c, 5, False)
    # This outside-band point's ray enters the cone farther forward. It must
    # never cast a shadow, unlike either in-band blocker color.
    side_decoy = (throat_row, throat[0] - 2)
    put(*side_decoy, 5, False)
    assert any(r > side_decoy[0] and c == side_decoy[1] for r, c in inside)
    counts = Counter(v for line in board for v in line)
    assert counts[0] > counts[1] > max(count for color, count in counts.items() if color not in (0, 1))
    return board, {"name": name, "stride": stride, "cap_row": cap_row,
        "endpoints": ends, "interior": inside, "wall": wall, "dye_cells": dye_cells,
        "blockers": blockers, "behind_cap_decoy": behind, "side_decoy": side_decoy,
        "continuation_rows": height - final_tip - 1, "clipped_left": clipped}


def input_templates(seed=0):
    """Fresh deterministic geometry/marker grids; no retries, palettes or labels."""
    _integer(seed, "seed")
    grids = [_scene(spec, _rng(seed, index))[0] for index, spec in enumerate(PROFILES)]
    return grids[:6], grids[6:]


