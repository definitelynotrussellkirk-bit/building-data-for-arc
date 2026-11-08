"""Visible-example solver; no generator, reference or private-label imports."""


def _normalize(points):
    top = min(r for r, c in points)
    left = min(c for r, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def _rotation_signature(points):
    variants = []
    current = _normalize(points)
    for _ in range(4):
        variants.append(current)
        current = _normalize([(c, -r) for r, c in current])
    return min(variants)


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        points = [start]
        while stack:
            r, c = stack.pop()
            for adjacent in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if adjacent in unseen and grid[adjacent[0]][adjacent[1]] == color:
                    unseen.remove(adjacent)
                    stack.append(adjacent)
                    points.append(adjacent)
        result.append({"top": min(r for r, c in points),
                       "left": min(c for r, c in points),
                       "color": color, "cells": _normalize(points)})
    return sorted(result, key=lambda item: (item["top"], item["left"]))


def solve(grid):
    signatures = [_rotation_signature(item["cells"]) for item in _components(grid)]
    return [[5 if row == col else 8 if a == b else 0
             for col, b in enumerate(signatures)]
            for row, a in enumerate(signatures)]
