"""Task-local regression tests for the enclosure-fill curriculum."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as read_canonical_pairs
from reviewer_support import canonical_path, find_root


def _load_generator():
    default = Path(__file__).resolve().parents[1] / "generator.py"
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", default))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
TASK_HOME = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = find_root(__file__)
CANONICAL_LEDGER = canonical_path(RUNTIME_ROOT)


def _canonical_pairs():
    assert CANONICAL_LEDGER.is_file()
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in read_canonical_pairs(
            gen.TASK_ID, root=RUNTIME_ROOT, variant=0, labeled_only=True
        )
    ]


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_contract_pins_authority_and_exposes_only_observable_profile_axis():
    assert gen.RULE_HASH == "92650211204a"
    assert set(gen.AXES) == {"profile"}
    assert set(gen.SCHEDULE_PROFILES) == {
        "canonical_rectangle",
        "irregular_enclosure",
        "shared_color_pair",
        "closure_contrast",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", gen.SCHEDULE_PROFILES)
def test_each_profile_override_is_exact_and_lawful(profile, band):
    grid = gen.generate(71, 9, difficulty=band, profile=profile)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.profile_signature(grid) == profile
    assert gen.observe_overrides(grid) == {"profile": profile}


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_profile="rectangle")


@pytest.mark.parametrize("bad", [1, True, 2.5, [], {}])
def test_profile_override_type_is_rejected(bad):
    with pytest.raises(ValueError, match="profile override must be a string"):
        gen.generate(0, 0, profile=bad)


@pytest.mark.parametrize("grid", [None, [], [[]], [1, 2], ["000", "000"], [[0], [0, 0]]])
def test_self_check_is_total_on_malformed_grids(grid):
    assert gen.self_check(grid)


def test_canonical_inputs_are_accepted_and_diagnostic_mirror_matches_outputs():
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_global_bbox_shortcut_fits_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {"global_color_bbox"}
    rival = gen.CANONICAL_SHORTCUTS["global_color_bbox"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())


def test_exact_same_color_pair_is_a_checked_bbox_counterexample():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 1, 1, 1, 0],
        [0, 1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    expected = copy.deepcopy(grid)
    expected[2][2] = 1
    expected[2][6] = 1
    assert gen.self_check(grid) == []
    assert gen.profile_signature(grid) == gen.PROFILE_SHARED
    assert gen.rule_mirror(grid) == expected
    assert gen.global_color_bbox(grid) != expected
    assert gen.SEMANTIC_WITNESSES["bbox_counterexample"](grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_three_demo_window_refutes_declared_shortcut(band):
    assert gen.EXAMPLES_NEEDED == 3
    for seed in range(6):
        grids = [gen.generate(seed, index, difficulty=band) for index in range(16)]
        for start in range(13):
            demos = [_pair(grid) for grid in grids[start:start + gen.EXAMPLES_NEEDED]]
            query = _pair(grids[start + gen.EXAMPLES_NEEDED])
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    name, band, seed, start
                )


def test_schedule_covers_each_profile_once_per_four_consecutive_draws():
    for band in (None, "easy", "medium", "hard"):
        for seed in range(8):
            for start in range(12):
                profiles = {
                    gen.profile_signature(gen.generate(seed, index, difficulty=band))
                    for index in range(start, start + 4)
                }
                assert profiles == set(gen.SCHEDULE_PROFILES)


def test_generated_inputs_use_canonical_canvas_profiles_and_preserve_inputs():
    canonical_shapes = {(6, 10), (7, 8), (8, 9), (8, 10), (9, 9)}
    seen = set()
    for seed in range(10):
        for index in range(12):
            grid = gen.generate(seed, index, difficulty="hard")
            saved = copy.deepcopy(grid)
            seen.add((len(grid), len(grid[0])))
            gen.rule_mirror(grid)
            gen.global_color_bbox(grid)
            assert grid == saved
            assert (len(grid), len(grid[0])) in canonical_shapes
            assert grid == gen.generate(seed, index, difficulty="hard")
    assert seen == canonical_shapes


def test_difficulty_bands_affect_the_deterministic_scene_stream():
    comparisons = []
    for seed in range(8):
        for index in range(8):
            grids = [gen.generate(seed, index, difficulty=band)
                     for band in ("easy", "medium", "hard")]
            comparisons.append(len({json.dumps(grid) for grid in grids}))
    assert max(comparisons) > 1


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_ordinary_example_visibly_demonstrates_the_fill(band):
    for seed in range(12):
        for index in range(12):
            grid = gen.generate(seed, index, difficulty=band)
            output = gen.rule_mirror(grid)
            changed = sum(
                before != after
                for row_before, row_after in zip(grid, output)
                for before, after in zip(row_before, row_after)
            )
            assert changed / (len(grid) * len(grid[0])) >= 0.03, (
                band, seed, index, gen.profile_signature(grid), changed,
                len(grid), len(grid[0])
            )
