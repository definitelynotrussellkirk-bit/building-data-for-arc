"""Source-bound semantic contract tests for dafb4f819b93."""
from __future__ import annotations

import copy

from reviewer_support import find_root, load_selected_generator


TASK_ID = "dafb4f819b93"
ROOT = find_root(__file__)
generator, _PATH, _SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": generator.rule_mirror(grid)}


def _lesson():
    grids = [
        generator.generate(
            91 + index,
            701 + index,
            difficulty=("easy", "medium", "hard", "medium")[index],
            grid_n=8 + index,
            n_colors=4 + (index % 2),
            border_relation=("matched", "different", "matched", "different")[index],
        )
        for index in range(4)
    ]
    return [_pair(grid) for grid in grids[:3]], _pair(grids[3])


def test_semantic_contract_declarations_exist():
    assert callable(generator.strict_canonical_like)
    assert callable(generator.lesson_identifiable)
    assert generator.EXAMPLES_NEEDED == 3
    assert set(generator.SEMANTIC_WITNESSES) == {
        "matched_partitions",
        "asymmetric_partitions",
    }
    assert set(generator.BRANCH_WITNESSES) == set(generator.SEMANTIC_WITNESSES)
    assert set(generator.WITNESS_RIVALS) == {"asymmetric_partitions"}
    assert generator.LESSON_COMPETITORS


def test_strict_hook_accepts_generated_grammar_and_rejects_impostor():
    grid = generator.generate(
        19,
        31,
        difficulty="hard",
        grid_n=14,
        n_colors=6,
        border_relation="different",
    )
    assert generator.strict_canonical_like(grid) == []
    bad = copy.deepcopy(grid)
    bad[0][0] = 5
    assert generator.strict_canonical_like(bad)


def test_branch_witnesses_and_asymmetry_rivals_are_real_counterexamples():
    matched = generator.generate(
        7,
        11,
        grid_n=10,
        n_colors=4,
        border_relation="matched",
    )
    asymmetric = generator.generate(
        7,
        11,
        grid_n=10,
        n_colors=4,
        border_relation="different",
    )
    witnesses = generator.SEMANTIC_WITNESSES
    assert witnesses["matched_partitions"](matched) is True
    assert witnesses["asymmetric_partitions"](matched) is False
    assert witnesses["matched_partitions"](asymmetric) is False
    assert witnesses["asymmetric_partitions"](asymmetric) is True

    expected = generator.rule_mirror(asymmetric)
    rival_names = generator.WITNESS_RIVALS["asymmetric_partitions"]
    assert rival_names
    assert all(
        generator.SEMANTIC_RIVALS[name](asymmetric) != expected
        for name in rival_names
    )


def test_every_declared_lesson_competitor_is_refuted_by_each_lawful_demo():
    demos, _query = _lesson()
    for name, rival in generator.LESSON_COMPETITORS.items():
        assert all(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_lesson_identifiable_accepts_valid_labels_and_rejects_tampering():
    demos, query = _lesson()
    assert generator.lesson_identifiable(demos, query) == []

    bad_demo = copy.deepcopy(demos)
    bad_demo[0]["output"][0][0] = 9
    reasons = generator.lesson_identifiable(bad_demo, query)
    assert any("output" in reason for reason in reasons)

    assert generator.lesson_identifiable(demos[:2], query) == [
        "lesson needs at least 3 demonstrations"
    ]
