from __future__ import annotations

import sys
from pathlib import Path

import pytest

TASK_ID = "5e619caf1f27"
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (  # noqa: E402
    canonical_pairs as load_canonical_pairs,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
GEN, _GENERATOR_SOURCE, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_pairs():
    return load_canonical_pairs(TASK_ID, root=ROOT)


def _episode(seed: int, start: int, difficulty: str):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_index = start + GEN.EXAMPLES_NEEDED
    query_grid = GEN.generate(seed, query_index, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_canonical_top_left_margin_shortcut_is_declared_and_fits_all_pairs():
    rival = GEN.CANONICAL_SHORTCUTS["top_left_margin_only_clipped"]
    pairs = _canonical_pairs()
    assert len(pairs) == 6
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_four_demo_window_refutes_top_left_margin_shortcut(difficulty):
    rival = GEN.LESSON_COMPETITORS["top_left_margin_only_clipped"]
    for seed in (7, 97, 997):
        for start in range(8):
            demos, query = _episode(seed, start, difficulty)
            assert not all(
                rival(pair["input"]) == pair["output"] for pair in demos
            ), (difficulty, seed, start)
            assert GEN.lesson_identifiable(demos, query) == []


def test_far_edge_witness_is_bound_to_the_top_left_margin_shortcut():
    witness_name = "bottom_or_right_margin_caps_frame"
    rival_name = "top_left_margin_only_clipped"
    witness = GEN.SEMANTIC_WITNESSES[witness_name]
    assert rival_name in GEN.WITNESS_RIVALS[witness_name]
    rival = GEN.SEMANTIC_RIVALS[rival_name]

    for difficulty in ("easy", "medium", "hard"):
        for seed in (7, 97, 997):
            for sample_index in (3, 7, 11):
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                assert GEN.schedule_profile(seed, sample_index, difficulty) == "edge_limited_two"
                assert witness(grid), (difficulty, seed, sample_index)
                assert rival(grid) != GEN.rule_mirror(grid)


def test_canonical_shortcut_registry_contains_exactly_the_rivals_that_fit_all_pairs():
    pairs = _canonical_pairs()
    fitting = {
        name
        for name, rival in GEN.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    expected = {
        "top_left_margin_only_clipped",
        "maximum_inner_dimension",
        "inner_height_only",
        "inner_width_only",
    }
    assert fitting == expected
    assert set(GEN.CANONICAL_SHORTCUTS) == fitting
