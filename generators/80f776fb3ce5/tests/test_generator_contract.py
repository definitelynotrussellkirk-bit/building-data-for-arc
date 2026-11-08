"""Regression cases for canonical support, exact controls and lesson witnesses."""
import importlib.util
from copy import deepcopy

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "80f776fb3ce5"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("plus_generator_contract", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK, root=ROOT, labeled_only=True)


def targets(grid):
    """Independent pixel observation of the advertised exact pattern count."""
    return {(r, c) for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 0 and
            (grid[r - 1][c], grid[r + 1][c], grid[r][c - 1], grid[r][c + 1]) == (1, 1, 1, 1)}


def python_expectation(grid):
    """Test oracle only; production labels are separately checked in Racket."""
    out = deepcopy(grid)
    for r, c in targets(grid):
        out[r][c] = 8
    return out


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda pair: f"{pair['split']}-{pair['pair_index']}")
def test_all_canonical_inputs_are_in_the_validator_domain(pair):
    assert GEN.self_check(pair["input"]) == []
    assert python_expectation(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,count", [(6, 6, 4), (6, 14, 1), (14, 6, 4), (7, 8, 2), (14, 14, 3)])
def test_exact_dimensions_and_pattern_count_in_every_band(band, height, width, count):
    grid = GEN.generate(17, 3, difficulty=band, grid_h=height, grid_w=width, n_patterns=count)
    assert len(grid) == height
    assert all(len(row) == width for row in grid)
    assert len(targets(grid)) == count
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("overrides", [{"typo_axis": 7}, {"texture": "spread"}, {"n_patterns": 99},
                                       {"grid_h": True}, {"grid_w": "9"}, {"n_patterns": 2.5}])
def test_invalid_or_retired_controls_fail_visibly(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("grid", [[], [[0], [0, 1]], [[True, 1, 0], [1, 0, 1], [0, 1, 0]],
                                  [[0, 1, 0], [1, 0.0, 1], [0, 1, 0]],
                                  [[0, 1, 0], [1, "0", 1], [0, 1, 0]], [[0] * 3 for _ in range(3)]])
def test_malformed_or_target_free_inputs_return_reasons_without_crashing(grid):
    assert GEN.self_check(grid)


def test_canonical_shortcuts_fit_every_labeled_pair():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "the task needs executable canonical shortcut claims"
    for name, rival in rivals.items():
        for pair in CANONICAL:
            assert rival(deepcopy(pair["input"])) == pair["output"], name


def test_every_canonical_shortcut_has_an_executable_generated_witness():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        matching = [witness for witness, names in GEN.WITNESS_RIVALS.items() if name in names]
        assert matching, f"{name} has no declared generated counterexample witness"
        assert any(GEN.SEMANTIC_WITNESSES[witness](grid) and rival(grid) != python_expectation(grid)
                   for witness in matching
                   for grid in (GEN.generate(5, index) for index in range(4))), name


def test_rich_examples_avoid_more_than_threefold_canonical_fragmentation():
    def objects(grid):
        remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
        count = 0
        while remaining:
            todo = [remaining.pop()]
            count += 1
            while todo:
                r, c = todo.pop()
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if point in remaining:
                        remaining.remove(point)
                        todo.append(point)
        return count
    for seed in range(12):
        assert objects(GEN.generate(seed, 1)) <= 24


def test_connecting_rims_does_not_remove_one_or_two_diagonal_positive_cases():
    observed = set()
    for seed in range(24):
        grid = GEN.generate(seed, 1)
        for r, c in targets(grid):
            observed.add(sum(grid[r + dr][c + dc] == 1
                             for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))))
    assert observed == {0, 1, 2, 3, 4}


def test_all_finite_axis_values_have_joint_support():
    for band in (None, "easy", "medium", "hard"):
        for height in range(6, 15):
            for width in range(6, 15):
                for count in range(1, 5):
                    for index in (0, 1):
                        grid = GEN.generate(29, index, difficulty=band, grid_h=height,
                                            grid_w=width, n_patterns=count)
                        assert len(grid) == height and all(len(row) == width for row in grid)
                        assert len(targets(grid)) == count
                        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_lessons_and_every_query_rotation_refute_declared_rivals(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "a reported lesson guarantee needs executable competitors"
    for seed in (0, 19):
        for start in range(4):
            pairs = [{"input": GEN.generate(seed, start + i, difficulty=band)} for i in range(4)]
            for pair in pairs:
                pair["output"] = python_expectation(pair["input"])
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in rivals.items():
                    if rival(query["input"]) != query["output"]:
                        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_canonical_profile_and_rich_counterexamples_both_have_support(band):
    grids = [GEN.generate(31, index, difficulty=band) for index in range(12)]
    profiles = {(len(pair["input"]), len(pair["input"][0]),
                 tuple(sorted({v for row in pair["input"] for v in row}))) for pair in CANONICAL}
    assert any((len(grid), len(grid[0]), tuple(sorted({v for row in grid for v in row})))
               in profiles for grid in grids)
    assert any(any(grid[r + dr][c + dc] == 1 for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))
               for grid in grids for r, c in targets(grid)), "valid pluses with diagonal clutter must be emitted"
    assert any(any(v not in (0, 1) for row in grid for v in row) for grid in grids), "fixed blue semantics need colored negatives"


def test_observer_recovers_exact_values_from_pixels():
    assert callable(getattr(GEN, "observe_overrides", None)), "semantic controls need pixel observations"
    grid = GEN.generate(73, 1, grid_h=11, grid_w=13, n_patterns=4)
    assert GEN.observe_overrides(grid) == {"grid_h": 11, "grid_w": 13, "n_patterns": 4}


def test_determinism_has_no_caller_input_or_global_rng_side_effects():
    import random
    state = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    assert GEN.generate(42, 7, difficulty="hard") == first
    assert random.getstate() == state
    original = deepcopy(first)
    GEN.self_check(first)
    assert first == original
