from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK = "a88fd33fba06"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _episode(seed: int, start: int, band: str = "medium"):
    demos = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, sample_index, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed + 1, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid}


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_solved():
    assert gen.RULE_HASH == canonical_rule_hash(TASK)
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_shortcuts_and_nonframe_counterexample_are_real():
    pairs = canonical_pairs(TASK)
    assert all(
        gen.SEMANTIC_RIVALS["second_largest_object"](pair["input"]) == pair["output"]
        for pair in pairs
    )
    assert all(
        gen.SEMANTIC_RIVALS["recenter_innermost_frame"](pair["input"]) == pair["output"]
        for pair in pairs
    )
    # Canonical train[1] and test contain a smaller non-frame domino/singleton.
    assert sum(
        gen.SEMANTIC_RIVALS["innermost_nonzero_object"](pair["input"]) != pair["output"]
        for pair in pairs
    ) == 2


def test_unknown_override_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="medium", typo_axis=7)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_round_trip_in_every_band(band):
    cases = [
        {
            "frame_count": 2,
            "inner_decoy": "none",
            "layout_style": "canonical",
            "outer_margin": "edge",
        },
        {
            "frame_count": 5,
            "inner_decoy": "domino",
            "layout_style": "offset",
            "outer_margin": "inset",
        },
        {
            "frame_count": 3,
            "inner_decoy": "singleton",
            "layout_style": "offset",
            "outer_margin": "edge",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(1000 + index, 100 + index, difficulty=band, **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
        assert len(grid) <= 30 and len(grid[0]) <= 30


def test_every_three_sample_window_is_identifiable_and_kills_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos, query = _episode(4242, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            analyses = [gen._analyze(demo["input"]) for demo in demos]
            assert any(a["decoy_kind"] != "none" for a in analyses)
            assert any(a["frame_count"] >= 3 for a in analyses)
            assert any(a["layout_style"] == "offset" for a in analyses)
            assert {a["outer_margin"] for a in analyses} == {"edge", "inset"}
            for rival_name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), rival_name


def test_scheduled_semantic_witnesses_are_positive_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(8080, sample_index, difficulty=band) for sample_index in range(4)]
        assert any(gen.SEMANTIC_WITNESSES["nonframe_decoy_kills_object_depth"](g) for g in grids)
        assert any(gen.SEMANTIC_WITNESSES["deep_chain_kills_second_largest"](g) for g in grids)
        assert any(gen.SEMANTIC_WITNESSES["offset_recenter_killer"](g) for g in grids)


def test_targeted_mutation_fixtures_are_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_nonframe_moved_outside_deepest_frame_is_rejected():
    grid = gen.generate(99, 1, difficulty="medium")
    analysis = gen._analyze(grid)
    assert analysis["decoy_kind"] == "domino"
    moved = copy.deepcopy(grid)
    decoy = analysis["nonframes"][0]
    for r, c in decoy["cells"]:
        moved[r][c] = 0
    used = {value for row in moved for value in row}
    color = next(value for value in range(1, 10) if value not in used)
    outer = analysis["frames"][0]["bbox"]
    target = next(
        (r, c)
        for r in range(len(moved))
        for c in range(len(moved[0]))
        if moved[r][c] == 0
        and not (outer[0] < r < outer[2] and outer[1] < c < outer[3])
    )
    moved[target[0]][target[1]] = color
    assert gen.self_check(moved)


def test_replay_is_fresh_deterministic_and_preserves_global_rng_state():
    random.seed(1234567)
    state = random.getstate()
    first = gen.generate(2026, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(2026, 3, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
