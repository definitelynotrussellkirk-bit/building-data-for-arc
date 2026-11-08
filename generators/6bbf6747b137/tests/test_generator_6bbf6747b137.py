"""Focused header-count controls; portable in the library and staged runtime."""
import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("6bbf6747b137", root=ROOT)


def body_components(grid):
    """Independent orthogonal component observations, ignoring row zero."""
    remaining = {(r, c) for r in range(1, len(grid))
                 for c in range(len(grid[0])) if grid[r][c] != 0}
    result = []
    while remaining:
        start = remaining.pop()
        cells, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    cells.add(p)
                    frontier.append(p)
        result.append(cells)
    return result


@pytest.mark.parametrize("k", range(1, 7))
def test_header_count_override_matches_exactly_one_body_component(k):
    grid = GEN.generate(17, 0, K=k)
    assert grid[0].count(1) == k
    sizes = [len(cells) for cells in body_components(grid)]
    assert len(sizes) == len(set(sizes)) == 3
    assert sizes.count(k) == 1
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("k", [0, 7, True, 2.5, "3"])
def test_invalid_header_count_override_rejected(k):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 0, K=k)


def test_distractor_areas_are_not_the_fixed_two_smallest_alternatives():
    areas = {tuple(sorted(len(cells) for cells in body_components(
        GEN.generate(seed, 0, K=3)))) for seed in range(12)}
    assert len(areas) > 1
    assert any(3 not in (min(sizes), max(sizes)) for sizes in areas)
    assert any(3 == min(sizes) for sizes in areas)
    assert any(3 == max(sizes) for sizes in areas)
