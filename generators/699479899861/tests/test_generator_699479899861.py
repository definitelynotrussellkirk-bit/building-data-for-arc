from __future__ import annotations

import copy
import json
import random

import pytest

from arcpuzzles import Catalog
from puzzle_generators import runner
from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "699479899861"
MODULE, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CATALOG = Catalog(ROOT)
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def test_metadata_rule_hash_and_selected_authorities_match() -> None:
    description = CATALOG.describe(TASK_ID)
    assert MODULE.VERSION == "2.0.0"
    assert MODULE.RULE_HASH == "ac41730bf8e3"
    assert MODULE.RULE_HASH == description["rule_hash"]
    assert GENERATOR_SHA256 == description["generator_sha256"]
    assert GENERATOR_PATH.is_file()


def test_all_canonical_pairs_are_accepted_and_racket_exact_reentrant() -> None:
    pairs = CANONICAL_PAIRS
    assert len(pairs) == 5
    inputs = [copy.deepcopy(pair["input"]) for pair in pairs]
    before = copy.deepcopy(inputs)

    result = CATALOG.apply(TASK_ID, inputs + [copy.deepcopy(inputs[0])], timeout=180)
    assert result["rule_hash_matches_catalog"] is True
    assert result["executed_rule_hash"] == MODULE.RULE_HASH
    assert [row["error"] for row in result["results"]] == [None] * (len(pairs) + 1)
    assert [row["output"] for row in result["results"][:-1]] == [
        pair["output"] for pair in pairs
    ]
    assert result["results"][-1]["output"] == pairs[0]["output"]
    assert inputs == before

    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_determinism_fresh_returns_and_process_rng_state() -> None:
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("bad_sample_index", [True, False, -1])
def test_sample_index_requires_a_nonnegative_plain_integer(bad_sample_index) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        MODULE.generate(901, bad_sample_index, difficulty="medium")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_axis_boundaries_are_observable(difficulty: str) -> None:
    for index, (height, width, count) in enumerate(
        ((9, 10, 2), (9, 17, 4), (16, 10, 3), (16, 17, 4))
    ):
        grid = MODULE.generate(
            1800 + index,
            index,
            difficulty=difficulty,
            grid_h=height,
            grid_w=width,
            n_blobs=count,
        )
        assert MODULE.self_check(grid) == []
        assert (len(grid), len(grid[0])) == (height, width)
        assert MODULE.observe_overrides(grid) == {"n_blobs": count}

    with pytest.raises((ValueError, TypeError)):
        MODULE.generate(1, 1, difficulty=difficulty, grid_h=8)
    with pytest.raises((ValueError, TypeError)):
        MODULE.generate(1, 1, difficulty=difficulty, grid_w=18)
    with pytest.raises((ValueError, TypeError)):
        MODULE.generate(1, 1, difficulty=difficulty, n_blobs=5)
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 1, difficulty=difficulty, palette_kind="warm")


def test_four_step_schedule_covers_profiles_witnesses_and_identifiable_lesson() -> None:
    seed = 77331
    grids = [MODULE.generate(seed, index, difficulty="medium") for index in range(4)]
    assert [MODULE.schedule_profile(seed, index, "medium") for index in range(4)] == list(
        MODULE.SCHEDULE_PROFILES
    )
    assert [len(MODULE._analysis(grid)["components"]) for grid in grids] == [2, 2, 3, 4]
    assert MODULE.SEMANTIC_WITNESSES["canonical_anchor"](grids[0])
    assert MODULE.SEMANTIC_WITNESSES["noncanonical_blob_extent"](grids[1])
    for grid in grids:
        assert MODULE.SEMANTIC_WITNESSES[
            "separate_components_not_one_global_box"
        ](grid)
        assert MODULE.SEMANTIC_WITNESSES["decorations_are_preserved"](grid)
        assert MODULE.SEMANTIC_WITNESSES["original_red_cells_are_recolored"](grid)

    episode = runner.run_one(TASK_ID, seed=seed, sample_index=0, n_train=3, n_test=1)
    assert MODULE.lesson_identifiable(episode["train"], episode["test"][0]) == []
    for rival in MODULE.LESSON_COMPETITORS.values():
        assert not (
            all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
            and rival(episode["test"][0]["input"]) != episode["test"][0]["output"]
        )


def test_self_check_rejects_task_linked_impostors() -> None:
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert MODULE.self_check(grid), name

    valid = MODULE.generate(909, 2, difficulty="medium")
    assert MODULE.self_check(valid) == []

    missing_decoration = copy.deepcopy(valid)
    for row in missing_decoration:
        for col, value in enumerate(row):
            if value not in (0, 2):
                row[col] = 0
    assert any("decorative" in reason for reason in MODULE.self_check(missing_decoration))

    solid_component = copy.deepcopy(valid)
    first_component = MODULE._components(solid_component, 2)[0]
    for row, col in MODULE._bbox_cells(MODULE._bbox(first_component)):
        solid_component[row][col] = 2
    assert any(
        "non-rectangular" in reason
        for reason in MODULE.self_check(solid_component)
    )


def test_negative_recombinations_are_rejected_but_racket_remains_executable() -> None:
    valid = MODULE.generate(101, 2, difficulty="hard", grid_h=16, grid_w=17, n_blobs=3)

    no_red = copy.deepcopy(valid)
    for row in no_red:
        for col, value in enumerate(row):
            if value == 2:
                row[col] = 0
    assert MODULE.self_check(no_red)

    one_component = copy.deepcopy(valid)
    components = MODULE._components(one_component, 2)
    for component in components[1:]:
        for row, col in component:
            one_component[row][col] = 0
    assert MODULE.self_check(one_component)

    result = CATALOG.apply(TASK_ID, [no_red, one_component], timeout=180)
    assert result["rule_hash_matches_catalog"] is True
    assert [row["error"] for row in result["results"]] == [None, None]
    assert result["results"][0]["output"] == no_red
    assert result["results"][1]["output"] == MODULE.rule_mirror(one_component)


def test_recorded_fixed_size_shortcut_counterexample_is_reproducible() -> None:
    record_path = (
        ROOT
        / "generators"
        / TASK_ID
        / "counterexamples"
        / "fixed_canonical_3x2_boxes.json"
    )
    record = json.loads(record_path.read_text(encoding="utf-8"))

    assert record["generator_sha256"] == GENERATOR_SHA256
    assert record["rule_hash"] == MODULE.RULE_HASH
    assert record["rival_fits_all_canonical_pairs"] is True
    rival = MODULE.CANONICAL_SHORTCUTS[record["rival"]]
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL_PAIRS)

    recipe = record["generation"]
    generated = MODULE.generate(
        recipe["seed"],
        recipe["sample_index"],
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    assert generated == record["input"]
    assert MODULE.self_check(generated) == []
    assert rival(generated) == record["rival_output"]
    assert rival(generated) != record["intended_output"]

    result = CATALOG.apply(TASK_ID, [generated], timeout=180)
    assert result["generator_sha256"] == GENERATOR_SHA256
    assert result["results"][0]["error"] is None
    assert result["results"][0]["output"] == record["intended_output"]

