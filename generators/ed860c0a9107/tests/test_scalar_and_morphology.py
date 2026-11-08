"""Regressions for literal sampler arguments and canonical connected payloads."""
from itertools import product
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


gen, _, _ = load_selected_generator("ed860c0a9107", root=find_root(__file__))


@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
@pytest.mark.parametrize("argument", ["seed", "sample_index"])
@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1"])
def test_sampler_arguments_require_literal_integers(difficulty, argument, bad):
    arguments = {"seed": 991, "sample_index": 0, "difficulty": difficulty}
    arguments[argument] = bad
    with pytest.raises(TypeError, match=argument):
        gen.generate(**arguments)


@pytest.mark.parametrize("difficulty", ["easy", None, "hard"])
def test_sample_index_must_be_nonnegative(difficulty):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(991, -1, difficulty=difficulty)


def singleton_count(grid):
    """Count 4-connected monochrome nonzero singletons directly from pixels."""
    seen = set()
    count = 0
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            size = 0
            while todo:
                rr, cc = todo.pop()
                size += 1
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            count += size == 1
    return count


@pytest.mark.parametrize("n_containers,box_h,box_w", list(product(range(2, 5), range(2, 6), range(2, 6))))
def test_four_color_lane_has_connected_payloads_for_every_box_shape(n_containers, box_h, box_w):
    grid = gen.generate(20261020, 0, grid_h=14, grid_w=14,
                        n_containers=n_containers, box_h=box_h, box_w=box_w)
    assert singleton_count(grid) == 0
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 14, "grid_w": 14, "n_containers": n_containers,
        "box_h": box_h, "box_w": box_w,
    }
    assert len({v for row in grid for v in row}) == 4
    assert gen.rule_mirror(grid) != gen.SEMANTIC_RIVALS["last_visible"](grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_color_lane_supports_canonical_morphology_in_each_band(difficulty):
    for index in (0, 4, 8, 12, 16):
        grid = gen.generate(index, index, difficulty=difficulty)
        assert singleton_count(grid) == 0
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("seed", [-1, 0, 2**80])
def test_integer_seeds_remain_supported_and_deterministic(seed):
    assert gen.generate(seed, 0) == gen.generate(seed, 0)
