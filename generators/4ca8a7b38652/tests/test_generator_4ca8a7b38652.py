from __future__ import annotations

import copy
from collections import Counter
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "4ca8a7b38652"
def _load_generator():
    selected = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(selected) if selected else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test_4ca8a7b38652", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _colors(grid):
    return {value for row in grid for value in row}


def _nonzero_count(grid):
    return len(_colors(grid) - {0})


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_default_draws_stay_on_the_declared_three_by_three_profiles() -> None:
    allowed_profiles = {
        (True, 2): {(1, 3, 5), (2, 2, 5)},
        (True, 3): {(1, 1, 2, 5), (1, 2, 2, 4)},
        (True, 4): {(1, 1, 1, 2, 4)},
        (False, 2): {(4, 5)},
        (False, 3): {(3, 3, 3)},
        (False, 4): {(2, 2, 2, 3)},
    }
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for sample_index in range(10):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                assert (len(grid), len(grid[0])) == (3, 3)
                observed = GEN.observe_overrides(grid)
                key = (observed["zero_present"], observed["color_count"])
                profile = tuple(sorted(Counter(v for row in grid for v in row).values()))
                assert profile in allowed_profiles[key], (band, seed, sample_index, grid)
                assert GEN.self_check(grid) == []
                assert GEN.strict_canonical_like(grid) == []


def test_every_five_window_has_redundant_zero_and_no_zero_witnesses() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(10):
            for start in range(5):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(5)
                ]
                zeros = [0 in _colors(grid) for grid in grids]
                counts = [_nonzero_count(grid) for grid in grids]
                assert sum(zeros) >= 3
                assert sum(not flag for flag in zeros) >= 2
                assert counts.count(2) >= 2
                assert counts.count(4) >= 2


def test_exact_overrides_are_observable_and_bad_overrides_reject() -> None:
    for band in ("easy", "medium", "hard"):
        for color_count in (2, 3, 4):
            for zero_present in (False, True):
                grid = GEN.generate(
                    77,
                    11,
                    difficulty=band,
                    color_count=color_count,
                    zero_present=zero_present,
                )
                assert GEN.observe_overrides(grid) == {
                    "color_count": color_count,
                    "zero_present": zero_present,
                }
                assert GEN.self_check(grid) == []

    with pytest.raises((TypeError, ValueError), match="color_count"):
        GEN.generate(1, 0, color_count=True)
    with pytest.raises((TypeError, ValueError), match="zero_present"):
        GEN.generate(1, 0, zero_present=1)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_rule_hash_and_schedule_contract_are_pinned() -> None:
    assert GEN.RULE_HASH == "2e2cb8677499"
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.LESSON_SCHEDULE_PERIOD == 5
    assert GEN.MIN_STRICT_FRAC == 1.0


def test_every_six_pair_window_is_identifiable_under_all_query_rotations() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(5):
                pairs = []
                for offset in range(6):
                    grid = GEN.generate(seed, start + offset, difficulty=band)
                    pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                for query_index, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        band,
                        seed,
                        start,
                        query_index,
                        GEN.lesson_identifiable(demos, query),
                    )


def test_declared_rivals_are_refuted_after_any_single_pair_holdout() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(6):
            pairs = []
            for sample_index in range(6):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index in range(6):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        seed,
                        query_index,
                        name,
                    )


def test_self_check_rejects_targeted_distribution_impostors() -> None:
    impostors = {
        "empty": [],
        "wrong_shape": [[1, 2], [2, 1]],
        "one_nonzero_color": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        "five_nonzero_colors": [[1, 2, 3], [4, 5, 1], [2, 3, 4]],
        "zero_profile_too_dense": [[0, 1, 1], [1, 1, 1], [2, 2, 2]],
        "zero_free_singleton": [[1, 1, 1], [1, 1, 1], [1, 1, 2]],
        "row_only": [[1, 1, 1], [2, 2, 2], [1, 1, 1]],
        "solid_two_by_two_partition": [[1, 1, 2], [1, 1, 2], [2, 2, 2]],
        "bad_cell": [[1, 1, 1], [2, 11, 2], [1, 2, 1]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_every_declared_semantic_witness_names_a_rival_claim() -> None:
    assert set(GEN.SEMANTIC_WITNESSES) <= set(GEN.WITNESS_RIVALS)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(9917)
    before = random.getstate()
    first = GEN.generate(2026, 19, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(2026, 19, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    changed = copy.deepcopy(first)
    changed[0][0] = (changed[0][0] + 1) % 10
    assert second != changed


def test_seed_and_sample_index_reject_bool_and_negative_values() -> None:
    for bad_seed in (True, False):
        with pytest.raises(TypeError, match="seed"):
            GEN.generate(bad_seed, 0)
    for bad_index in (True, False):
        with pytest.raises(TypeError, match="sample_index"):
            GEN.generate(1, bad_index)
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(1, -1)
