from __future__ import annotations

import copy
import os
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_components_output,
    authority_output,
    canonical_profile,
    component_sizes_by_panel,
    load_generator,
    zero_shift_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
TASK_ID = "b44c4c938f42"
BANDS = ("easy", "medium", "hard")


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": authority_output(grid)})
    return pairs[: gen.EXAMPLES_NEEDED], pairs[-1]


def test_rule_pin_and_canonical_pairs_match_independent_oracle():
    assert gen.RULE_HASH == "10339930cb51"
    assert gen.VERSION == "3.2.0"
    pairs = _pairs()
    assert len(pairs) == 12  # two canonical variants, six labeled pairs each
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert authority_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_generated_panel_teaches_largest_component_and_conflict_shift(difficulty):
    for index in range(48):
        grid = gen.generate(7300 + index, index, difficulty=difficulty)
        sizes = component_sizes_by_panel(grid)
        assert all(len(panel_sizes) == 2 for panel_sizes in sizes)
        assert all(panel_sizes[0] > panel_sizes[1] for panel_sizes in sizes)
        official = authority_output(grid)
        assert official != all_components_output(grid)
        assert official != zero_shift_output(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("difficulty", BANDS)
def test_exact_overrides_are_observable_in_every_band(difficulty):
    exact = {
        "grid_h": 8,
        "panel_w": 7,
        "panel_count": 3,
        "distractor_size": 2,
        "size_order": "ascending",
        "rotation": 3,
    }
    grid = gen.generate(20261012, 19, difficulty=difficulty, **exact)
    assert gen.observe_overrides(grid) == exact
    assert len(grid) == 8
    assert len(grid[0]) == 3 * 7 + 2


@pytest.mark.parametrize("axis,value", [
    ("bogus", 1),
    ("grid_h", 4), ("grid_h", 9), ("grid_h", True), ("grid_h", 5.0),
    ("panel_w", 4), ("panel_w", 8), ("panel_w", "5"),
    ("panel_count", 1), ("panel_count", 4),
    ("distractor_size", 0), ("distractor_size", 3),
    ("size_order", "sideways"), ("rotation", -1), ("rotation", 4),
])
def test_invalid_overrides_reject(axis, value):
    with pytest.raises((TypeError, ValueError), match="override|unknown|must"):
        gen.generate(1, 2, **{axis: value})


@pytest.mark.parametrize("difficulty", BANDS)
def test_canonical_profile_occurs_in_each_twenty_draw_band(difficulty):
    profiles = {
        canonical_profile(gen.generate(99173, index, difficulty=difficulty))
        for index in range(20)
    }
    assert (5, 17, 5) in profiles


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_query_rotation_refutes_fixed_absolute_size_thresholds(difficulty):
    """Any three demonstrations must show both sides of the relative-size decision.

    A size>1 rival fits singleton-distractor examples; a size>2 rival fits
    size-two-distractor examples.  Every rotated three-demo view therefore needs
    at least one panel whose winner has size 2 and at least one size-2 distractor.
    """
    for start in range(12):
        grids = [gen.generate(51000 + start, start + offset, difficulty=difficulty)
                 for offset in range(gen.EXAMPLES_NEEDED + 1)]
        for query_position in range(len(grids)):
            demos = [grid for index, grid in enumerate(grids) if index != query_position]
            facts = [component_sizes_by_panel(grid) for grid in demos]
            assert any(any(panel_sizes[0] == 2 for panel_sizes in sample) for sample in facts)
            assert any(any(panel_sizes[1] == 2 for panel_sizes in sample) for sample in facts)


@pytest.mark.parametrize("difficulty", BANDS)
def test_each_short_lesson_refutes_declared_competitors(difficulty):
    for start in range(12):
        demos, query = _lesson(60000 + start, start, difficulty)
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(copy.deepcopy(pair["input"])) != pair["output"] for pair in demos), name


def test_declared_witnesses_are_real_counterexamples():
    grid = gen.generate(44, 7, difficulty="medium")
    official = authority_output(grid)
    for name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert predicate(copy.deepcopy(grid)), name
        for rival_name in gen.WITNESS_RIVALS[name]:
            assert gen.SEMANTIC_RIVALS[rival_name](copy.deepcopy(grid)) != official


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 67, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_malformed_and_targeted_impostors_are_rejected():
    malformed = (None, [], [[]], [[8], [8, 8]], [[True] * 5 for _ in range(5)])
    for grid in malformed:
        assert gen.self_check(grid)

    valid = gen.generate(77, 5, panel_count=3, distractor_size=2)
    no_separator = [row[:] for row in valid]
    sep = 5
    for row in no_separator:
        row[sep] = 8
    assert gen.self_check(no_separator)

    one_component = gen.generate(77, 5, panel_count=3, distractor_size=1)
    # Erase the first panel's single-cell distractor while preserving its main object.
    panel_sizes = component_sizes_by_panel(one_component)
    assert panel_sizes[0][1] == 1
    from reference_probe import components, split_panels
    panels = split_panels(one_component)
    small = min(components(panels[0]), key=lambda obj: obj["size"])
    r, c = small["cells"][0]
    one_component[r][c] = 8
    assert gen.self_check(one_component)

@pytest.mark.parametrize("kwargs", [
    {"seed": True, "sample_index": 0},
    {"seed": 1.0, "sample_index": 0},
    {"seed": "1", "sample_index": 0},
    {"seed": 1, "sample_index": True},
    {"seed": 1, "sample_index": 1.0},
    {"seed": 1, "sample_index": "1"},
    {"seed": 1, "sample_index": -1},
    {"seed": 1, "sample_index": 0, "difficulty": True},
    {"seed": 1, "sample_index": 0, "difficulty": 0},
    {"seed": 1, "sample_index": 0, "difficulty": "impossible"},
])
def test_call_arguments_are_strict(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(**kwargs)


def test_difficulty_bands_enter_the_sampler_without_breaking_canonical_slots():
    # The same seed/index must not collapse to byte-identical easy/medium/hard
    # curricula, while index 0 still carries the canonical (5,17,5) profile.
    for index in range(1, 12):
        grids = [gen.generate(44001, index, difficulty=band) for band in BANDS]
        assert len({repr(grid) for grid in grids}) > 1
    for band in BANDS:
        assert canonical_profile(gen.generate(44001, 0, difficulty=band)) == (5, 17, 5)
