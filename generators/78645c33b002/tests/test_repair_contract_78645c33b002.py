from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "78645c33b002"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def pair(grid):
    return {"input": grid, "output": MODULE.rule_mirror(grid)}


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, "1"])
def test_seed_must_be_a_literal_integer(bad_seed):
    with pytest.raises(ValueError):
        MODULE.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, "1", -1])
def test_sample_index_must_be_a_nonnegative_literal_integer(bad_index):
    with pytest.raises(ValueError):
        MODULE.generate(1, bad_index)


def test_declared_diagonal_shortcut_fits_every_labeled_canonical_pair():
    shortcut = MODULE.CANONICAL_SHORTCUTS["main_diagonal_run_compression"]
    labeled = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(labeled) == 8
    assert all(shortcut(item["input"]) == item["output"] for item in labeled)


def test_retained_offcenter_case_is_a_real_shortcut_counterexample():
    grid = MODULE.generate(93, 93, difficulty="medium", scene_profile="tall_offcenter")
    shortcut = MODULE.CANONICAL_SHORTCUTS["main_diagonal_run_compression"]

    assert MODULE.strict_canonical_like(grid) == []
    assert MODULE.SEMANTIC_WITNESSES["refutes_main_diagonal_run_compression"](grid)
    assert MODULE.rule_mirror(grid) != shortcut(grid)
    assert len(MODULE.rule_mirror(grid)) == 9
    assert len(shortcut(grid)) == 7


def test_lesson_contract_rejects_surviving_shortcut_and_accepts_a_witness():
    shortcut_query = pair(
        MODULE.generate(93, 93, difficulty="medium", scene_profile="tall_offcenter")
    )
    canon = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    unwitnessed = canon[: MODULE.EXAMPLES_NEEDED]

    findings = MODULE.lesson_identifiable(unwitnessed, shortcut_query)
    assert any("main_diagonal_run_compression" in finding for finding in findings)

    witnessed = [*canon[: MODULE.EXAMPLES_NEEDED - 1], shortcut_query]
    assert MODULE.lesson_identifiable(witnessed, canon[-1]) == []


def test_semantic_registry_connects_witness_to_named_rival():
    name = "main_diagonal_run_compression"
    witness = "refutes_main_diagonal_run_compression"
    assert MODULE.LESSON_COMPETITORS[name] is MODULE.SEMANTIC_RIVALS[name]
    assert MODULE.CANONICAL_SHORTCUTS[name] is MODULE.SEMANTIC_RIVALS[name]
    assert MODULE.WITNESS_RIVALS[witness] == [name]


def test_default_schedule_guarantees_rotatable_shortcut_evidence():
    period = MODULE.LESSON_SCHEDULE_PERIOD
    scheduled = [MODULE._scheduled_profile(index) for index in range(period)]
    assert sum(profile in MODULE.PUBLIC_PROFILES for profile in scheduled) >= period * 3 // 8
    assert set(scheduled) == set(MODULE.SCENE_PROFILES)

    for difficulty in ("easy", "medium", "hard"):
        for start in range(period):
            grids = [
                MODULE.generate(700_000 + start, start + offset, difficulty=difficulty)
                for offset in range(4)
            ]
            assert sum(
                MODULE.SEMANTIC_WITNESSES["refutes_main_diagonal_run_compression"](grid)
                for grid in grids
            ) >= 2
