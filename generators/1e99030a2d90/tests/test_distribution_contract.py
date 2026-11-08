"""Behavioral regressions for red-cardinal centers and their teaching data."""
from copy import deepcopy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "1e99030a2d90"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.exists():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("red_cardinal_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def expected_output(grid):
    """Independent set-intersection oracle; production labels remain Racket."""
    red = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    candidates = set.intersection(
        {(r + 1, c) for r, c in red}, {(r - 1, c) for r, c in red},
        {(r, c + 1) for r, c in red}, {(r, c - 1) for r, c in red},
    )
    result = deepcopy(grid)
    for r, c in candidates:
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == 0:
            result[r][c] = 4
    return result


def changes(grid):
    return {(r, c) for r, row in enumerate(expected_output(grid))
            for c, v in enumerate(row) if grid[r][c] != v}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_canonical_inputs_remain_accepted_in_every_band(band):
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert gen.self_check(pair["input"], difficulty=band) == []
        assert expected_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,count", [(5, 5, 1), (5, 24, 1), (24, 5, 1),
                                               (10, 11, 3), (24, 24, 12)])
def test_advertised_dimension_and_count_controls_are_exact(band, height, width, count):
    grid = gen.generate(17, 9, difficulty=band, grid_h=height, grid_w=width,
                        n_diamonds=count)
    assert (len(grid), len(grid[0]), len(changes(grid))) == (height, width, count)
    assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_single_count_override_can_select_a_sufficient_canvas(band):
    grid = gen.generate(42, 0, difficulty=band, n_diamonds=12)
    assert len(changes(grid)) == 12


@pytest.mark.parametrize("overrides", [
    {"typo": 1}, {"palette_kind": "warm"}, {"density": "dense"},
    {"grid_h": True}, {"grid_w": 9.5}, {"n_diamonds": "3"},
    {"grid_h": 4}, {"grid_w": 25}, {"n_diamonds": 0}, {"n_diamonds": 13},
])
def test_invalid_or_retired_controls_are_rejected(overrides):
    with pytest.raises((ValueError, TypeError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_impossible_joint_count_reports_the_incompatible_axes():
    with pytest.raises(ValueError) as failure:
        gen.generate(0, 0, grid_h=5, grid_w=5, n_diamonds=12)
    assert set(failure.value.incompatible_axes) == {"grid_h", "grid_w", "n_diamonds"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_inputs_refute_the_isolated_template_shortcut(band):
    for index in range(24):
        grid = gen.generate(8100 + index, index, difficulty=band)
        target_cells = changes(grid)
        assert any(grid[r + dr][c + dc] != 0 for r, c in target_cells
                   for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_declared_witness_is_a_real_counterexample(band):
    seen = set()
    for index in range(24):
        grid = gen.generate(9100 + index, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                seen.add(name)
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != expected_output(grid)
                           for rival in gen.WITNESS_RIVALS[name])
    assert seen == set(gen.SEMANTIC_WITNESSES)


def test_declared_canonical_shortcuts_fit_all_five_labeled_pairs():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_demo_lessons_remain_identifiable_at_every_query_position(band):
    for start in range(8):
        pairs = []
        for offset in range(5):
            grid = gen.generate(1200 + start, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": expected_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert not (all(rival(p["input"]) == p["output"] for p in demos)
                            and rival(query["input"]) != query["output"])


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 2]], [[False, 2]],
                                 [[0, 2.0]], [[0, 10]], [[0, 0], [0, 0]]])
def test_malformed_or_target_free_inputs_are_diagnostic(grid):
    assert gen.self_check(grid)


def test_replay_and_rival_scoring_do_not_mutate_inputs():
    for index in range(8):
        grid = gen.generate(73, index)
        saved = deepcopy(grid)
        assert gen.generate(73, index) == saved
        for rival in gen.LESSON_COMPETITORS.values():
            rival(grid)
            assert grid == saved


def test_query_cannot_introduce_an_unseen_foreign_arm_color():
    """v2.0 seed0/start1 let warm-color arms fit all demos and fail the query."""
    def warm_arms(grid):
        result = deepcopy(grid)
        for r in range(1, len(grid) - 1):
            for c in range(1, len(grid[0]) - 1):
                if grid[r][c] == 0 and all(grid[rr][cc] in (2, 4, 7, 9)
                    for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):
                    result[r][c] = 4
        return result

    grids = [gen.generate(0, i, difficulty="easy") for i in range(1, 6)]
    assert not (all(warm_arms(g) == expected_output(g) for g in grids[:4])
                and warm_arms(grids[4]) != expected_output(grids[4]))
    for seed in range(24):
        colors = [{v for row in gen.generate(seed, i, difficulty="easy") for v in row} - {0, 2}
                  for i in range(8)]
        assert len(set.union(*colors)) == 1
