from __future__ import annotations

from collections import deque

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "ce40117f40f9"


def load_generator():
    module, _path, _sha256 = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


def non_marker_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def marker_position(grid):
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    assert len(markers) == 1
    return markers[0]


def bbox(cells):
    rows = [r for r, c, value in cells]
    cols = [c for r, c, value in cells]
    return min(rows), min(cols), max(rows), max(cols)


@pytest.mark.parametrize(
    "grid",
    [
        [[0] * 8 for _ in range(8)],
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 4, 4, 0, 0, 0, 0, 0, 0],
            [0, 4, 0, 0, 0, 0, 0, 0, 0],
            *([[0] * 9] * 5),
        ],
        [*([[0] * 9] * 5), [0, 0, 0, 0, 0, 0, 9, 0, 0], *([[0] * 9] * 2)],
        [[True, 0, 0], [0, 4, 9], [0, 4, 0]],
    ],
)
def test_self_check_rejects_reproduced_invalid_domains(grid):
    mod = load_generator()
    assert mod.self_check(grid), grid


def test_generate_rejects_unknown_axes_and_honors_exact_blob_size():
    mod = load_generator()
    with pytest.raises((TypeError, ValueError), match="unknown"):
        mod.generate(0, 0, not_an_axis=123)

    grid = mod.generate(
        0,
        0,
        grid_h=12,
        grid_w=12,
        blob_size=6,
        position_bias="marker_southeast",
    )
    assert len(non_marker_cells(grid)) == 6
    assert mod.self_check(grid) == []


@pytest.mark.parametrize(
    ("position_bias", "relation"),
    [
        ("marker_southeast", "se"),
        ("marker_northwest", "nw"),
        ("marker_northeast", "ne"),
        ("marker_southwest", "sw"),
    ],
)
def test_generate_constructs_requested_marker_direction(position_bias, relation):
    mod = load_generator()
    grid = mod.generate(
        20261024,
        3,
        grid_h=12,
        grid_w=13,
        blob_size=5,
        position_bias=position_bias,
    )
    cells = non_marker_cells(grid)
    top, left, bottom, right = bbox(cells)
    mr, mc = marker_position(grid)
    observed = {
        "se": mr > bottom and mc > right,
        "nw": mr < top and mc < left,
        "ne": mr < top and mc > right,
        "sw": mr > bottom and mc < left,
    }
    assert observed[relation], (position_bias, (top, left, bottom, right), (mr, mc))
    assert sum(observed.values()) == 1
    assert mod.self_check(grid) == []


def test_generate_supports_literal_minimum_and_30x30_boundaries():
    mod = load_generator()
    small = mod.generate(
        11,
        0,
        grid_h=6,
        grid_w=6,
        blob_size=2,
        position_bias="marker_northwest",
    )
    large = mod.generate(
        12,
        1,
        grid_h=30,
        grid_w=30,
        blob_size=6,
        position_bias="marker_southwest",
    )
    assert (len(small), len(small[0])) == (6, 6)
    assert (len(large), len(large[0])) == (30, 30)
    assert mod.self_check(small) == []
    assert mod.self_check(large) == []


def test_generated_blob_is_monochrome_and_four_connected():
    mod = load_generator()
    for index in range(24):
        grid = mod.generate(314159, index)
        cells = non_marker_cells(grid)
        points = {(r, c) for r, c, _ in cells}
        assert len({value for _, _, value in cells}) == 1
        seen = {next(iter(points))}
        queue = deque(seen)
        while queue:
            r, c = queue.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in points and point not in seen:
                    seen.add(point)
                    queue.append(point)
        assert seen == points
        assert mod.self_check(grid) == []
