"""Focused regressions for the review hardening of generator 72416068b0cf."""
from __future__ import annotations

import importlib

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "72416068b0cf"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(bad_seed):
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_sample_index(bad_index):
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(991, bad_index, difficulty="hard")


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index must be non-negative"):
        GEN.generate(991, -1)


def test_partial_rivals_are_not_declared_as_canonical_shortcuts():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert GEN.CANONICAL_SHORTCUTS == {}
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


def test_reverse_transform_order_is_scored_as_a_lesson_competitor():
    assert GEN.LESSON_COMPETITORS["reverse_transform_order"] is GEN._rival_reverse_order


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_four_demo_window_refutes_every_declared_lesson_competitor(difficulty):
    for seed in range(4):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": GEN._solve(grid)})
            query_grid = GEN.generate(
                seed,
                start + GEN.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": GEN._solve(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                fits_all_demos = all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                )
                if fits_all_demos:
                    assert rival(query["input"]) == query["output"], (
                        difficulty,
                        seed,
                        start,
                        name,
                    )


def test_every_semantic_witness_is_backed_by_a_named_rival_disagreement():
    """Strict after checks must not contain presence-only weak witnesses."""
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        assert rival_names, witness_name
        assert set(rival_names) <= set(GEN.SEMANTIC_RIVALS), witness_name
