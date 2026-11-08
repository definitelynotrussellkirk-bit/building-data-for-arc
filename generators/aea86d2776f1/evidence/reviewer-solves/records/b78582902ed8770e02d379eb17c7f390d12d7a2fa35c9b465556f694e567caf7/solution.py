"""Visible-example solution for Commanded Template Mosaic."""
from __future__ import annotations


def _rotate_cw(tile):
    return [list(row) for row in zip(*tile[::-1])]


def _flip_lr(tile):
    return [row[::-1] for row in tile]


def _rotate_180(tile):
    return [row[::-1] for row in tile[::-1]]


def _transform(tile, residue):
    if residue == 0:
        return [row[:] for row in tile]
    if residue == 1:
        return _rotate_cw(tile)
    if residue == 2:
        return _flip_lr(tile)
    return _rotate_180(tile)


def solve(grid):
    left = [row[1:4] for row in grid[2:5]]
    right = [row[7:10] for row in grid[2:5]]
    templates = (left, right)

    tiles = []
    for column in (1, 3, 7, 9):
        command = grid[0][column]
        source = 0 if command <= 4 else 1
        residue = (command - 1) % 4
        tiles.append(_transform(templates[source], residue))

    return (
        [tiles[0][row] + tiles[1][row] for row in range(3)]
        + [tiles[2][row] + tiles[3][row] for row in range(3)]
    )
