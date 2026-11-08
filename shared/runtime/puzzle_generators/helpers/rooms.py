"""Helpers for rectangular wall-bounded room layouts."""
from __future__ import annotations

Grid = list[list[int]]


def rectangular_rooms(rows: int, cols: int, room_h: int, room_w: int, wall: int = 1):
    """Build a regular grid of rooms separated by one-cell walls."""
    h = rows * room_h + rows + 1
    w = cols * room_w + cols + 1
    grid = [[wall] * w for _ in range(h)]
    rooms = []
    for rr in range(rows):
        row = []
        r0 = 1 + rr * (room_h + 1)
        for cc in range(cols):
            c0 = 1 + cc * (room_w + 1)
            cells = []
            for r in range(r0, r0 + room_h):
                for c in range(c0, c0 + room_w):
                    grid[r][c] = 0
                    cells.append((r, c))
            row.append({"bbox": (r0, c0, room_h, room_w), "cells": cells})
        rooms.append(row)
    return grid, rooms


def center_cell(room) -> tuple[int, int]:
    """Center cell of a rectangular room."""
    r0, c0, h, w = room["bbox"]
    return r0 + h // 2, c0 + w // 2


def add_door_between(grid: Grid, rooms, a: tuple[int, int], b: tuple[int, int], door: int = 7) -> None:
    """Open a marked door in the wall between adjacent rooms."""
    ar, ac = a
    br, bc = b
    if abs(ar - br) + abs(ac - bc) != 1:
        raise ValueError("rooms must be cardinal-adjacent")
    r0, c0, h, w = rooms[ar][ac]["bbox"]
    r1, c1, _h2, _w2 = rooms[br][bc]["bbox"]
    if ar == br:
        wall_c = c0 + w if bc > ac else c1 + _w2
        grid[r0 + h // 2][wall_c] = door
    else:
        wall_r = r0 + h if br > ar else r1 + _h2
        grid[wall_r][c0 + w // 2] = door
