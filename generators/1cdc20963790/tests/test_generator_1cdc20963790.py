from __future__ import annotations

import copy
import json
import importlib.util
import os
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "1cdc20963790"
TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SHAPES = ("6x6", "7x7", "7x8")
BANDS = ("easy", "medium", "hard")
COUNTEREXAMPLES = json.loads((TASK_HOME / "counterexamples" / "baseline-impostors.json").read_text())


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _labeled(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_identity_and_public_contract_are_pinned():
    assert gen.RULE_HASH == "2d0911ecb918"
    assert set(gen.AXES) == {"shape_profile", "row_markers", "column_markers"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "balanced",
        "row_heavy",
        "column_heavy",
        "edge_mix",
    )


def test_all_canonical_inputs_and_outputs_are_owned():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("row_markers", [2, 6])
@pytest.mark.parametrize("column_markers", [2, 6])
def test_all_declared_override_boundaries_are_exact_and_observable(
    band, shape, row_markers, column_markers
):
    grid = gen.generate(
        941,
        7,
        difficulty=band,
        shape_profile=shape,
        row_markers=row_markers,
        column_markers=column_markers,
    )
    assert gen.observe_overrides(grid) == {
        "shape_profile": shape,
        "row_markers": row_markers,
        "column_markers": column_markers,
    }
    assert gen.self_check(grid) == []


def test_invalid_requests_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 1, row_markers=True)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 1, row_markers=1)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 1, shape_profile="8x8")


def test_every_default_draw_is_strict_and_carries_all_named_witnesses():
    for band in BANDS:
        for sample_index in range(16):
            grid = gen.generate(707, sample_index, difficulty=band)
            assert gen.self_check(grid) == [], (band, sample_index)
            assert gen.strict_canonical_like(grid) == []
            assert set(gen.observe_overrides(grid)) == set(gen.AXES)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, sample_index, name)


def test_self_check_rejects_structural_impostors():
    grid = gen.generate(
        203,
        0,
        difficulty="medium",
        shape_profile="7x7",
        row_markers=4,
        column_markers=4,
    )

    bad_corner = copy.deepcopy(grid)
    bad_corner[0][0] = 2
    assert any("top-left" in reason for reason in gen.self_check(bad_corner))

    duplicate_top = copy.deepcopy(grid)
    duplicate_top[0][2] = duplicate_top[0][1]
    assert any("top header" in reason for reason in gen.self_check(duplicate_top))

    bad_interior = copy.deepcopy(grid)
    bad_interior[1][1] = 9
    assert any("interior" in reason for reason in gen.self_check(bad_interior))

    only_one_branch = copy.deepcopy(grid)
    for r in range(1, len(only_one_branch)):
        for c in range(1, len(only_one_branch[0])):
            if only_one_branch[r][c] == 2:
                only_one_branch[r][c] = 0
    assert any("column markers" in reason for reason in gen.self_check(only_one_branch))

    minimal = next(case for case in COUNTEREXAMPLES["cases"] if case["id"] == "solid-2x2-minimal-impostor")
    assert gen.self_check(minimal["input"])


def test_deterministic_fresh_and_global_rng_pure():
    random.seed(811)
    state = random.getstate()
    first = gen.generate(8, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(8, 3, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second == gen.generate(8, 3, difficulty="hard")


def test_each_generated_input_refutes_every_declared_rival():
    for band in BANDS:
        for sample_index in range(8):
            grid = gen.generate(509, sample_index, difficulty=band)
            truth = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (band, sample_index, name)


def test_every_schedule_window_and_query_rotation_identifies_the_rule():
    for band in BANDS:
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = [
                _labeled(gen.generate(613, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for held_out in range(len(pairs)):
                query = pairs[held_out]
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    held_out,
                )


def test_schedule_profiles_are_exhaustive_and_stable():
    for band in BANDS:
        observed = {
            gen.schedule_profile(11, index, difficulty=band)
            for index in range(gen.LESSON_SCHEDULE_PERIOD)
        }
        assert observed == set(gen.SCHEDULE_PROFILES)
