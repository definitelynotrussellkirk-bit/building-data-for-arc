from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base as generator_base
from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.8230189d9b9e.generator"
)


def _episode(start: int, difficulty: str):
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        source = GEN.generate(91_000 + start, start + offset, difficulty=difficulty)
        pairs.append({"input": source, "output": GEN.rule_mirror(source)})
    return pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]


def _missing_color(grid):
    used = {value for row in grid for value in row}
    return next(value for value in range(1, 10) if value not in used)


def test_rule_hash_version_and_semantic_contract_are_pinned():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "b313e3795954"
    assert GEN.strict_canonical_like
    assert GEN.SEMANTIC_WITNESSES
    assert GEN.lesson_identifiable
    assert set(GEN.AXES) == {
        "grid_h",
        "n_keys",
        "query_len",
        "prototype_color_mode",
    }


def test_all_canonical_pairs_are_accepted_and_mirror_exactly():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_four_sample_window_identifies_the_rule(difficulty):
    for start in range(8):
        demos, query = _episode(start, difficulty)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_exact_override_boundaries_are_observable():
    cases = (
        {
            "grid_h": 6,
            "n_keys": 2,
            "query_len": 2,
            "prototype_color_mode": "matched",
        },
        {
            "grid_h": 8,
            "n_keys": 5,
            "query_len": 5,
            "prototype_color_mode": "decoupled",
        },
    )
    for index, overrides in enumerate(cases):
        source = GEN.generate(700 + index, 50 + index, difficulty="hard", **overrides)
        assert GEN.self_check(source) == []
        assert GEN.observe_overrides(source) == overrides


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 1, texture="warm")
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 1, grid_h=5)
    with pytest.raises(ValueError, match="n_keys"):
        GEN.generate(1, 1, n_keys=6)
    with pytest.raises(ValueError, match="prototype_color_mode"):
        GEN.generate(1, 1, prototype_color_mode="varied")


def test_default_keyed_axes_equal_returned_observables():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            captured = []
            generator_base.set_ctx_observer(captured.append)
            try:
                source = GEN.generate(80_000 + sample_index, sample_index, difficulty=difficulty)
            finally:
                generator_base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == GEN.observe_overrides(source)
            assert set(captured[0].recorded_draws()) == set(GEN.AXES)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(55, 7, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(55, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert GEN.generate(55, 7, difficulty="hard") == second


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(42, 1, difficulty="medium")
    analysis = GEN._analysis(valid)
    first = analysis["prototypes"][0]
    second = analysis["prototypes"][1]

    duplicate_key = copy.deepcopy(valid)
    duplicate_key[0][second["column"]] = first["key"]
    assert any("distinct" in reason for reason in GEN.self_check(duplicate_key))

    unknown_query = copy.deepcopy(valid)
    query_column = next(c for c, value in enumerate(unknown_query[-1]) if value)
    unknown_query[-1][query_column] = _missing_color(unknown_query)
    assert any("absent" in reason for reason in GEN.self_check(unknown_query))

    stray_library_cell = copy.deepcopy(valid)
    occupied_columns = {
        col
        for prototype in analysis["prototypes"]
        for col in range(prototype["column"] - 1, prototype["column"] + 2)
    }
    stray_column = next(col for col in range(len(valid[0])) if col not in occupied_columns)
    stray_library_cell[1][stray_column] = _missing_color(stray_library_cell)
    assert any("outside" in reason for reason in GEN.self_check(stray_library_cell))

    sparse_prototype = copy.deepcopy(valid)
    occupied = [
        (r, c)
        for r in range(1, 4)
        for c in range(first["column"] - 1, first["column"] + 2)
        if sparse_prototype[r][c]
    ]
    for r, c in occupied[2:]:
        sparse_prototype[r][c] = 0
    assert any("3..7" in reason for reason in GEN.self_check(sparse_prototype))

    multicolor_prototype = copy.deepcopy(valid)
    r, c = occupied[0]
    multicolor_prototype[r][c] = _missing_color(multicolor_prototype)
    assert any("monochrome" in reason for reason in GEN.self_check(multicolor_prototype))

    nonblank_separator = copy.deepcopy(valid)
    nonblank_separator[4][0] = _missing_color(nonblank_separator)
    assert any("blank" in reason for reason in GEN.self_check(nonblank_separator))


def test_schedule_supplies_each_named_rival_killer_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(4000, index, difficulty=difficulty) for index in range(4)]
        for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
            candidates = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
            assert candidates, witness_name
            for rival_name in rival_names:
                rival = GEN.SEMANTIC_RIVALS[rival_name]
                assert any(rival(grid) != GEN.rule_mirror(grid) for grid in candidates), (
                    witness_name,
                    rival_name,
                )
