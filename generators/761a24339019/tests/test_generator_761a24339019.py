from __future__ import annotations

from collections import deque

import pytest

from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("761a24339019", root=ROOT)


CLIPPED_WITNESS = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 3, 3, 0, 0, 0, 0, 0, 0],
    [3, 3, 3, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def _nonzero_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            component = {(row, col)}
            seen.add((row, col))
            frontier = deque([(row, col)])
            while frontier:
                current_row, current_col = frontier.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbour = current_row + dr, current_col + dc
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in seen
                        and grid[neighbour[0]][neighbour[1]] != 0
                    ):
                        seen.add(neighbour)
                        component.add(neighbour)
                        frontier.append(neighbour)
            components.append(component)
    return components


def _complete_stamp_errors(grid: list[list[int]]) -> list[str]:
    height, width = len(grid), len(grid[0])
    components = _nonzero_components(grid)
    exemplars = [
        component
        for component in components
        if {grid[row][col] for row, col in component} == {1, 3}
    ]
    if len(exemplars) != 1:
        return [f"expected one mixed exemplar, got {len(exemplars)}"]
    exemplar = exemplars[0]
    anchors = [(row, col) for row, col in exemplar if grid[row][col] == 1]
    if len(anchors) != 1:
        return [f"expected one exemplar anchor, got {len(anchors)}"]
    anchor_row, anchor_col = anchors[0]
    offsets = {
        (row - anchor_row, col - anchor_col)
        for row, col in exemplar
        if grid[row][col] == 3
    }
    targets = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1 and (row, col) != (anchor_row, anchor_col)
    ]
    errors: list[str] = []
    footprints: list[set[tuple[int, int]]] = []
    for target_row, target_col in targets:
        footprint = {(target_row + dr, target_col + dc) for dr, dc in offsets}
        if any(not (0 <= row < height and 0 <= col < width) for row, col in footprint):
            errors.append(f"target {(target_row, target_col)} clips its stamp")
        in_bounds = {
            (row, col)
            for row, col in footprint
            if 0 <= row < height and 0 <= col < width
        }
        if any(grid[row][col] != 0 for row, col in in_bounds):
            errors.append(f"target {(target_row, target_col)} overwrites input content")
        footprints.append(footprint)
    for left in range(len(footprints)):
        for right in range(left + 1, len(footprints)):
            if footprints[left] & footprints[right]:
                errors.append(f"target stamps {left} and {right} overlap")
    return errors


def test_retained_seed_has_only_complete_nonoverlapping_stamps():
    grid = gen.generate(6, 6, difficulty="easy")
    assert gen.self_check(grid) == []
    assert _complete_stamp_errors(grid) == []


def test_self_check_rejects_saved_partial_stamp_domain():
    errors = gen.self_check(CLIPPED_WITNESS)
    assert errors
    assert any("complete" in error or "bounds" in error or "clip" in error for error in errors)


@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
def test_bounded_generation_stays_in_complete_stamp_domain(difficulty):
    for seed in range(30):
        grid = gen.generate(seed, seed * 17 + 3, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert _complete_stamp_errors(grid) == []
