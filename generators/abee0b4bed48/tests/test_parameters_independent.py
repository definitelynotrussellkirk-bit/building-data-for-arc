"""Portable independent classifier, composition and finite teaching checks."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bank():
    return _load(HOME / "tests/parameter_rivals.py", "_abee0b4bed48_independent_bank")


@pytest.fixture(scope="module")
def adapter():
    return _load(HOME / "workspace/parametric/adapter.py", "_abee0b4bed48_independent_adapter")


def test_every_binary_zone_pattern_and_all_classifier_branches(adapter, bank):
    histogram = Counter()
    for pattern in range(512):
        grid = bank.mask_grid([pattern])
        label = bank.classify(pattern)
        histogram[label] += 1
        assert adapter.decode(grid) == [label]
        for order in ("input", "frequency"):
            settings = {"order": order}
            assert adapter.first_stage(grid, settings) == [label]
            assert adapter.mirror(grid, settings) == bank.paint([label])
    assert histogram == {0: 410, 1: 1, 3: 9, 4: 9, 6: 1, 9: 82}


def test_all_patterns_in_multizone_strips_have_independent_intermediates(adapter, bank):
    for start in range(0, 512, 10):
        grid = bank.mask_grid(range(start, min(start+10, 512)))
        original = [row[:] for row in grid]
        for order in ("input", "frequency"):
            expected = bank.analyze(grid, {"order": order})
            actual = adapter.analyze(grid, {"order": order})
            for key in ("labels", "frequencies", "permutation", "ordered_labels", "output"):
                assert actual[key] == expected[key], (start, order, key)
        assert grid == original


def test_frozen_38_rule_bank_has_no_query_changing_demo_survivor(adapter, bank):
    assert len(bank.RIVALS) == 38
    unresolved = []
    for seed in range(32):
        for order in ("input", "frequency"):
            settings = {"order": order}
            episode = adapter.generate(seed, settings, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == bank.model(pair["input"], settings)
            fitted = bank.fit_demos(episode["train"], settings)
            assert not fitted["execution_errors"]
            queried = bank.assess_queries(episode["test"], settings, fitted)
            assert not queried["execution_errors"]
            if queried["query_disagreeing_survivors"]:
                unresolved.append((seed, order, queried["query_disagreeing_survivors"]))
    assert not unresolved, unresolved


@pytest.mark.parametrize("seed", (2, 3, 5, 8, 12, 21, 25, 26, 27, 28, 31))
def test_unequal_top_bottom_demonstrations_refute_recorded_swap_ambiguity(adapter, bank, seed):
    settings = {"order": "frequency"}
    episode = adapter.generate(seed, settings, demos=3, queries=4)
    fitted = bank.fit_demos(episode["train"], settings)
    predict = bank.RIVAL_BY_NAME["top_bottom_swapped"].predict
    assert any(predict(pair["input"], "frequency") != pair["output"]
               for pair in episode["test"]), "the original difficult query must remain"
    assert "top_bottom_swapped" not in fitted["survivors"], (seed, fitted["survivors"])


@pytest.mark.parametrize("order", ("input", "frequency"))
def test_minimum_three_demos_teach_required_relational_distinctions(adapter, bank, order):
    # These mechanisms motivated the constructive core, and each is distinct
    # from the selected rule on lawful inputs. Queries are not used in fitting.
    names = ["minimum_two_zones", "top_bottom_swapped", "one_center_only", "ring_only"]
    if order == "frequency":
        names += ["skip_order_if_all_unique", "stable_frequency", "gray_count_frequency", "weighted_gray_mass"]
    for seed in range(32):
        episode = adapter.generate(seed, {"order": order}, demos=3, queries=4)
        fitted = bank.fit_demos(episode["train"], {"order": order})
        assert not set(names) & set(fitted["survivors"]), (seed, order, fitted["survivors"])


def test_frequency_is_invariant_to_zone_permutation_but_input_order_is_observable(adapter, bank):
    values = [56, 16, 0, 495, 448, 16, 56, 448, 0, 495]
    permutation = [8, 1, 6, 4, 7, 0, 3, 9, 5, 2]
    first = bank.mask_grid(values)
    second = bank.mask_grid([values[i] for i in permutation])
    assert adapter.mirror(first, {"order": "frequency"}) == adapter.mirror(second, {"order": "frequency"})
    assert adapter.mirror(first, {"order": "input"}) != adapter.mirror(second, {"order": "input"})
    result = adapter.analyze(first, {"order": "frequency"})
    for label in set(result["labels"]):
        occurrences = [i for i in result["permutation"] if result["labels"][i] == label]
        assert occurrences == sorted(occurrences)


def test_nonzero_fallbacks_and_all_unique_ties(adapter, bank):
    inactive = bank.mask_grid([(1 << count)-1 for count in (0, 2, 4, 5, 6, 7, 9)])
    assert adapter.decode(inactive) == [0]*7
    assert adapter.mirror(inactive, {"order": "frequency"}) == [[0]*21 for _ in range(3)]
    distinct = bank.mask_grid([56, 7, 16, 495, 448, 0])
    assert adapter.analyze(distinct, {"order": "frequency"})["ordered_labels"] == [0, 1, 3, 4, 6, 9]
