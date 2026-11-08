"""Constructive input-only banks for local transpose followed by ranking.

The first three demonstrations teach changed component rankings, all ties,
same-color four-connectivity, occupied area, and blank-canvas rendering. Each
bank is built in full before slicing. Settings and labels never enter sampling;
there are no retries, reference-runtime calls, or process-global RNG changes.
"""
from __future__ import annotations

import hashlib
from random import Random


_ORTHOGONAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
_J4 = frozenset({(0, 0), (0, 1), (1, 1), (2, 1)})
_U8 = frozenset({(0, 0), (1, 0), (2, 0), (3, 0),
                 (3, 1), (3, 2), (2, 2), (1, 2)})
_L3 = frozenset({(0, 0), (1, 0), (1, 1)})
_SIXES = (
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)}),
)


def _rng(seed: int, stream: str) -> Random:
    material = f"7071285d78ce/native-input-v1/{stream}/{seed}".encode("ascii")
    return Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _vertical(size):
    return frozenset((row, 0) for row in range(size))


def _branched_four(branch):
    return frozenset({(0, 0), (1, 0), (2, 0), (branch, 1)})


def _place(shape, row, col):
    return frozenset((row + dr, col + dc) for dr, dc in shape)


def _destination(cells):
    top = min(row for row, col in cells)
    left = min(col for row, col in cells)
    return frozenset((top + col - left, left + row - top) for row, col in cells)


def _scene(rng, height, width, objects, *, shift=True, transpose=None):
    """Embed known connected pieces, checking the independent geometry gate.

    Destination-source intersections are allowed. Only distinct sources must
    have orthogonal clearance, and only distinct destinations must be disjoint.
    Whole-canvas transposition commutes with this anchored local transpose and
    preserves these restrictions; arbitrary canvas reflections need not do so.
    """
    occupied = set().union(*(cells | _destination(cells) for color, cells in objects))
    used_height = max(row for row, col in occupied) + 1
    used_width = max(col for row, col in occupied) + 1
    assert used_height <= height and used_width <= width, "internal canvas mismatch"
    top = rng.randrange(height - used_height + 1) if shift else 0
    left = rng.randrange(width - used_width + 1) if shift else 0
    grid = [[0] * width for _ in range(height)]
    blocked_sources, used_destinations = set(), set()
    for color, relative in objects:
        cells = _place(relative, top, left)
        target = _destination(cells)
        assert not cells & blocked_sources, "internal source clearance failure"
        assert not target & used_destinations, "internal destination collision"
        assert all(0 <= row < height and 0 <= col < width for row, col in cells | target)
        for row, col in cells:
            grid[row][col] = color
        blocked_sources.update(cells)
        blocked_sources.update((row + dr, col + dc) for row, col in cells for dr, dc in _ORTHOGONAL)
        used_destinations.update(target)
    if transpose is None:
        transpose = bool(rng.randrange(2))
    return [list(row) for row in zip(*grid)] if transpose else grid


def _small_lesson(rng, height, width, *, shift=True, transpose=None):
    """Source areas 2,3,4,4 become 5,4,4; one area4 touches only diagonally.

    The two four-cell components have bbox area6, while the merged line has
    bbox area5. Both extrema therefore differ from bbox ranking and from
    selecting before transposition. The same color still has two components.
    """
    merge_color, other_color = rng.sample(range(1, 10), 2)
    objects = [
        (merge_color, _vertical(2)),
        (merge_color, _place(_vertical(3), 0, 2)),
        (merge_color, _place(_J4, 1, 5)),
        (other_color, _place(_J4, 4, 0)),
    ]
    return _scene(rng, height, width, objects, shift=shift, transpose=transpose)


def _ties_lesson(rng, height, width):
    """Both extrema tie: post areas8,4,8,4; unlike colors also touch.

    The first two L4s merge. A third L4 touches their result orthogonally but
    has another color, distinguishing color-blind grouping for BOTH extrema.
    The global transpose makes selected components wide in every seed.
    """
    merge_color, small_color, large_color = rng.sample(range(1, 10), 3)
    objects = [
        (merge_color, _branched_four(rng.randrange(3))),
        (merge_color, _place(_branched_four(rng.randrange(3)), 0, 3)),
        (small_color, _place(_branched_four(rng.randrange(3)), 0, 6)),
        (large_color, _place(_U8, 5, 0)),
        (small_color, _place(_J4, 5, 6)),
    ]
    return _scene(rng, height, width, objects, transpose=True)


def _overlap_lesson(rng, height, width):
    """A new area10 merger, singleton ties, and cross-source overwrite.

    The bar's destination covers another component's original top cell.
    That second component's bbox top-left is empty. Its destinations remain
    disjoint from the bar and connect to it, so fresh rendering retains all10.
    """
    merge_color, second_color, third_color, fourth_color = rng.sample(range(1, 10), 4)
    offset_l = {(row, 1) for row in range(4)} | {(rng.choice((2, 3)), 0)}
    wide_five = {(0, col) for col in range(4)} | {(1, rng.randrange(4))}
    objects = [
        (merge_color, _vertical(5)),
        (merge_color, _place(offset_l, 0, 3)),
        (merge_color, _place(wide_five, 6, 0)),
        (second_color, frozenset({(6, 7)})),
        (third_color, frozenset({(9, 7)})),
        (third_color, _place(_L3, 6, 11)),
        (fourth_color, frozenset({(10, 2), (10, 3)})),
    ]
    return _scene(rng, height, width, objects)


def _tile_scene(rng, height, width, origins):
    """Each substantive tile changes areas4,4,6 into8,6 after transposition.

    Every tile contributes a real merger and two competing sizes. Eight tiles
    use24 source components and112 cells on30x30, including all four borders.
    Varying branch positions and six-cell topology changes the actual shapes.
    """
    palette = rng.sample(range(1, 10), rng.choice((3, 4, 5)))
    objects = []
    for index, (top, left) in enumerate(origins):
        merge_color = palette[index % len(palette)]
        other_color = rng.choice(palette)
        first = _branched_four(rng.randrange(3))
        second = _branched_four(rng.randrange(3))
        six = rng.choice(_SIXES)
        objects.extend([
            (merge_color, _place(first, top, left)),
            (merge_color, _place(second, top, left + 3)),
            (other_color, _place(six, top + 4, left + 3)),
        ])
    return _scene(rng, height, width, objects, shift=False)


def _demo_bank(seed):
    first_rng = _rng(seed, "demos/0")
    first_dims = first_rng.choice(((9, 11), (10, 12)))
    demos = [_small_lesson(first_rng, *first_dims, transpose=False)]
    second_rng = _rng(seed, "demos/1")
    demos.append(_ties_lesson(second_rng, *second_rng.choice(((12, 14), (13, 15)))))
    third_rng = _rng(seed, "demos/2")
    demos.append(_overlap_lesson(third_rng, *third_rng.choice(((16, 18), (17, 19)))))
    demos.append(_small_lesson(_rng(seed, "demos/3"), 11, 16))
    demos.append(_tile_scene(_rng(seed, "demos/4"), 21, 23,
                             [(row, col) for row in (0, 14) for col in (0, 17)]))
    demos.append(_tile_scene(_rng(seed, "demos/5"), 26, 28,
                             [(row, col) for row in (0, 9, 19) for col in (0, 22)]))
    return demos


def _query_bank(seed):
    queries = [
        _small_lesson(_rng(seed, "queries/8x8"), 8, 8, shift=False),
        _tile_scene(_rng(seed, "queries/20x24"), 20, 24,
                    [(row, col) for row in (0, 13) for col in (0, 18)]),
        _tile_scene(_rng(seed, "queries/24x26"), 24, 26,
                    [(row, col) for row in (0, 8, 17) for col in (0, 20)]),
        _tile_scene(_rng(seed, "queries/30x30"), 30, 30,
                    [(row, col) for row in (0, 11, 23) for col in (0, 12, 24)
                     if (row, col) != (11, 12)]),
    ]
    _rng(seed, "query-order").shuffle(queries)
    return queries


def inputs(seed: int, demos: int = 3, queries: int = 4) -> dict:
    """Return fresh independent input banks with a three-demo teaching floor."""
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 3, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    train = _demo_bank(seed)
    test = _query_bank(seed)
    return {"train": train[:demos], "test": test[:queries]}
