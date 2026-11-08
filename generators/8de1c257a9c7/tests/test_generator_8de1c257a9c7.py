"""Focused regression tests for exact cyan-template transplantation."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import random
from pathlib import Path

import numpy as np
import pytest

from puzzle_generators import base as generator_base
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root

TASK_ID = "8de1c257a9c7"
ROOT = find_root(__file__)
_RUNTIME_GENERATOR = ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
_LIBRARY_GENERATOR = ROOT / f"generators/{TASK_ID}/generator.py"
GENERATOR_PATH = Path(
    os.environ.get(
        "GENERATOR_UNDER_TEST",
        _RUNTIME_GENERATOR if _RUNTIME_GENERATOR.is_file() else _LIBRARY_GENERATOR,
    )
)
COUNTEREXAMPLE_PATH = ROOT / (
    f"generators/{TASK_ID}/counterexamples/horizontal_mirror_seed29_slot1.json"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_8de1c257a9c7", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return load_generator()


def canonical_pairs():
    rows = load_canonical_pairs(TASK_ID, root=ROOT)
    assert len(rows) == 8  # two source rows, four pairs each
    return rows


def test_all_canonical_source_rows_are_accepted_and_exact(gen):
    signatures = []
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        signatures.append(gen.canonical_profile_signature(pair["input"]))
    assert set(signatures) == gen._CANONICAL_SIGNATURES
    assert len(set(signatures)) == 4


def test_default_prior_reaches_every_linked_profile_in_every_band(gen):
    for band in ("easy", "medium", "hard"):
        counts = {signature: 0 for signature in gen._CANONICAL_SIGNATURES}
        strict = 0
        for seed in range(200):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            signature = gen.canonical_profile_signature(grid)
            if signature is not None:
                counts[signature] += 1
                strict += 1
        assert strict >= 80, (band, strict, counts)
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_every_four_slot_window_is_identifiable(gen):
    for start in range(8):
        demos = []
        for offset in range(4):
            grid = gen.generate(104729, (start + offset) % 8, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(104729, (start + 4) % 8, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == [], start


def test_every_five_pair_window_survives_any_query_rotation(gen):
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = []
            for offset in range(5):
                grid = gen.generate(
                    104729,
                    (start + offset) % len(gen.SCHEDULE_PROFILES),
                    difficulty=difficulty,
                )
                lesson.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(lesson):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                )


def test_exact_override_observation_boundaries_and_unknown_rejection(gen):
    cases = [
        {"grid_h": 10, "grid_w": 10, "template": "canonical_cross", "n_reds": 1},
        {"grid_h": 22, "grid_w": 22, "template": "canonical_arch", "n_reds": 5},
        {"grid_h": 13, "grid_w": 17, "template": "asymmetric_hook", "n_reds": 3},
        {"grid_h": 17, "grid_w": 13, "template": "asymmetric_stair", "n_reds": 4},
    ]
    for index, overrides in enumerate(cases):
        captured = []
        generator_base.set_ctx_observer(captured.append)
        try:
            grid = gen.generate(700 + index, 20 + index, difficulty="hard", **overrides)
        finally:
            generator_base.set_ctx_observer(None)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides
        assert captured[0].recorded_draws() == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, nonexistent_axis=1)


def test_self_check_rejects_targeted_impostors(gen):
    base = gen.generate(13, 0)
    facts = gen._grid_facts(base)

    extra_green = copy.deepcopy(base)
    for r, row in enumerate(extra_green):
        for c, value in enumerate(row):
            if value == 0:
                extra_green[r][c] = 3
                break
        else:
            continue
        break
    assert any("exactly one green" in reason for reason in gen.self_check(extra_green))

    missing_reds = [[0 if value == 2 else value for value in row] for row in base]
    assert any("1-5 red" in reason for reason in gen.self_check(missing_reds))

    unknown_shape = copy.deepcopy(base)
    cr, cc = facts["cyans"][0]
    unknown_shape[cr][cc] = 0
    assert any("declared template" in reason for reason in gen.self_check(unknown_shape))

    clipped_copy = [[0 if value == 2 else value for value in row] for row in base]
    clipped_copy[0][0] = 2
    assert any("fit at every red" in reason for reason in gen.self_check(clipped_copy))

    bad_color = copy.deepcopy(base)
    bad_color[0][0] = 7
    assert any("only colors" in reason for reason in gen.self_check(bad_color))


def test_negative_recombination_is_lawful_but_not_canonical(gen):
    grid = gen.generate(
        23,
        17,
        grid_h=13,
        grid_w=13,
        template="canonical_diamond",
        n_reds=4,
    )
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid)
    assert gen.canonical_profile_signature(grid) is None
    output = gen.rule_mirror(grid)
    assert len(output) == 13 and len(output[0]) == 13


def test_asymmetry_and_overlap_refute_named_shortcuts(gen):
    asymmetric = gen.generate(29, 1)
    overlap = gen.generate(31, 3)
    assert gen.rule_mirror(asymmetric) != gen.SEMANTIC_RIVALS["mirror_shape_horizontally"](asymmetric)
    assert gen.semantic_observables(overlap)["overlap_cells"] > 0
    assert gen.rule_mirror(overlap) != gen.SEMANTIC_RIVALS["xor_overlapping_copies"](overlap)


def test_determinism_fresh_returns_and_global_rng_purity(gen):
    py_state = random.getstate()
    np_state = np.random.get_state()
    first = gen.generate(99991, 6, difficulty="hard")
    second = gen.generate(99991, 6, difficulty="hard")
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9
    assert random.getstate() == py_state
    np_after = np.random.get_state()
    assert np_after[0] == np_state[0]
    assert np.array_equal(np_after[1], np_state[1])
    assert np_after[2:] == np_state[2:]


def test_none_overrides_are_true_noops(gen):
    for sample_index in range(len(gen.SCHEDULE_PROFILES)):
        baseline = gen.generate(3109, sample_index, difficulty="medium")
        for axis in gen.AXES:
            assert gen.generate(3109, sample_index, difficulty="medium", **{axis: None}) == baseline
        assert gen.generate(
            3109,
            sample_index,
            difficulty="medium",
            **{axis: None for axis in gen.AXES},
        ) == baseline


@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 13.9),
        ("grid_h", "13"),
        ("grid_w", 13.9),
        ("grid_w", "13"),
        ("n_reds", True),
        ("n_reds", 3.5),
        ("n_reds", "3"),
    ],
)
def test_integer_overrides_reject_coercion(gen, axis, value):
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(17, 1, **{axis: value})


def test_equal_partial_override_does_not_change_the_scheduled_instance(gen):
    for sample_index in range(len(gen.SCHEDULE_PROFILES)):
        baseline = gen.generate(2027, sample_index, difficulty="hard")
        observed = gen.observe_overrides(baseline)
        for axis, value in observed.items():
            assert gen.generate(
                2027, sample_index, difficulty="hard", **{axis: value}
            ) == baseline


def test_dimension_override_preserves_unpinned_semantic_axes(gen):
    for sample_index in range(len(gen.SCHEDULE_PROFILES)):
        baseline = gen.generate(421, sample_index, difficulty="medium")
        before = gen.observe_overrides(baseline)
        requested_h = 22 if before["grid_h"] != 22 else 21
        changed = gen.generate(
            421, sample_index, difficulty="medium", grid_h=requested_h
        )
        after = gen.observe_overrides(changed)
        assert after["grid_h"] == requested_h
        assert after["template"] == before["template"]
        assert after["n_reds"] == before["n_reds"]


def test_retained_horizontal_mirror_counterexample(gen):
    case = json.loads(COUNTEREXAMPLE_PATH.read_text(encoding="utf-8"))
    assert case["task_id"] == TASK_ID
    assert case["seed"] == 29
    assert case["sample_index"] == 1
    assert case["input"] == gen.generate(29, 1, difficulty="medium")
    assert case["intended_output"] == gen.rule_mirror(case["input"])
    assert case["horizontal_mirror_output"] == (
        gen.SEMANTIC_RIVALS["mirror_shape_horizontally"](case["input"])
    )
    assert case["intended_output"] != case["horizontal_mirror_output"]


def test_feature_only_witness_is_declared_as_branch_coverage(gen):
    assert set(gen.BRANCH_WITNESSES) == {"single_destination_branch"}
    assert set(gen.SEMANTIC_WITNESSES) == (
        set(gen.WITNESS_RIVALS) | set(gen.BRANCH_WITNESSES)
    )
