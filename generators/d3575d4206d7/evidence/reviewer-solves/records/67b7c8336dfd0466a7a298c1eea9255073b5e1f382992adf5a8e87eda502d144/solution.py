"""Visible-only solution for the assigned ARC puzzle."""

from collections import Counter, defaultdict


def _axis_bands(grid, background, axis):
    """Return maximal non-separator runs along rows (axis 0) or columns."""
    outer = len(grid) if axis == 0 else len(grid[0])
    inner = len(grid[0]) if axis == 0 else len(grid)

    separators = set()
    for i in range(outer):
        values = (
            [grid[i][j] for j in range(inner)]
            if axis == 0
            else [grid[j][i] for j in range(inner)]
        )
        if all(value == background for value in values):
            separators.add(i)

    bands = []
    start = None
    for i in range(outer + 1):
        active = i < outer and i not in separators
        if active and start is None:
            start = i
        elif not active and start is not None:
            bands.append((start, i - 1))
            start = None
    return bands


def _components(block, color):
    """Eight-connected components of one color, in block-local coordinates."""
    height = len(block)
    width = len(block[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if block[row][col] == color
    }
    result = []

    while unseen:
        seed = unseen.pop()
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for drow in (-1, 0, 1):
                for dcol in (-1, 0, 1):
                    if drow == 0 and dcol == 0:
                        continue
                    neighbor = (row + drow, col + dcol)
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
        result.append(component)

    return result


def _shape(component):
    """Translation-invariant binary shape of a component."""
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    return frozenset((row - top, col - left) for row, col in component)


def solve(grid):
    # The dominant color forms the full separator rows/columns between 3x3
    # symbol cells.  Azure components are examples of symbol shapes.  For each
    # example, mark same-colored copies lying in its symbol-row or symbol-column,
    # and the fourth corners of rectangles induced by one row copy and one
    # column copy.
    output = [row[:] for row in grid]
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    row_bands = _axis_bands(grid, background, axis=0)
    col_bands = _axis_bands(grid, background, axis=1)

    entries = []
    markers = []
    for row_index, (row_start, row_end) in enumerate(row_bands):
        for col_index, (col_start, col_end) in enumerate(col_bands):
            block = [
                row[col_start : col_end + 1]
                for row in grid[row_start : row_end + 1]
            ]
            for color in counts:
                for component in _components(block, color):
                    entry = {
                        "row_index": row_index,
                        "col_index": col_index,
                        "color": color,
                        "shape": _shape(component),
                        "cells": {
                            (row_start + row, col_start + col)
                            for row, col in component
                        },
                    }
                    entries.append(entry)
                    if color == 8:
                        markers.append(entry)

    if not markers:
        return output

    # Infer which color the azure examples replace.  A valid source supplies
    # aligned copies for as many marker shapes as possible.  The puzzle uses a
    # sparse annotation color when several base colors accidentally make the
    # same tiny shape, so rarity is the tie-breaker before raw match count.
    source_scores = {}
    for color, frequency in counts.items():
        if color == 8:
            continue
        covered = 0
        direct_matches = 0
        for marker in markers:
            aligned = [
                entry
                for entry in entries
                if entry["color"] == color
                and entry["shape"] == marker["shape"]
                and (
                    entry["row_index"] == marker["row_index"]
                    or entry["col_index"] == marker["col_index"]
                )
            ]
            if aligned:
                covered += 1
                direct_matches += len(aligned)
        source_scores[color] = (covered, -frequency, direct_matches)

    source = max(source_scores, key=source_scores.get)
    if source_scores[source][0] == 0:
        return output

    for marker in markers:
        candidates = [
            entry
            for entry in entries
            if entry["color"] == source and entry["shape"] == marker["shape"]
        ]
        same_row = [
            entry
            for entry in candidates
            if entry["row_index"] == marker["row_index"]
        ]
        same_col = [
            entry
            for entry in candidates
            if entry["col_index"] == marker["col_index"]
        ]

        selected = {id(entry): entry for entry in same_row + same_col}
        by_cell = defaultdict(list)
        for entry in candidates:
            by_cell[(entry["row_index"], entry["col_index"])].append(entry)

        # If aligned row and column copies exist, include matching fourth
        # corners.  Deliberately do not iterate from newly marked corners:
        # dangling copies outside the marker-defined rectangle stay unchanged.
        for row_copy in same_row:
            for col_copy in same_col:
                corner = (col_copy["row_index"], row_copy["col_index"])
                for entry in by_cell.get(corner, ()):
                    selected[id(entry)] = entry

        for entry in selected.values():
            for row, col in entry["cells"]:
                output[row][col] = 8

    return output
