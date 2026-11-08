from __future__ import annotations

import copy
import importlib
import random

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "766e2ddcc3d3"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.766e2ddcc3d3.generator"
)


def _pair(seed: int, sample_index: int, band: str = "medium") -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_selected_rule_hash_and_all_canonical_pairs() -> None:
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    signatures = set()
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        signatures.add(GEN.canonical_profile_signature(pair["input"]))
    assert signatures == {
        "public_ctrl2_l3_7x7",
        "public_ctrl3_l3_7x7",
        "public_ctrl4_l4_7x8",
        "public_ctrl5_l4_8x8",
    }


def test_every_schedule_window_identifies_the_rule() -> None:
    strict_profiles = set()
    for start in range(16):
        demos = [_pair(28001 + start, start + offset) for offset in range(4)]
        query = _pair(28001 + start, start + 4)
        controls = {
            GEN.observe_overrides(pair["input"])["ctrl"] for pair in demos
        }
        assert controls == {2, 3, 4, 5}
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert not all(
                rival(pair["input"]) == pair["output"] for pair in demos
            ), f"schedule window {start} failed to refute {name}"
        for pair in demos:
            signature = GEN.canonical_profile_signature(pair["input"])
            if signature:
                strict_profiles.add(signature)
    assert strict_profiles == {
        "public_ctrl2_l3_7x7",
        "public_ctrl3_l3_7x7",
        "public_ctrl4_l4_7x8",
        "public_ctrl5_l4_8x8",
    }


def test_exact_overrides_round_trip_at_boundaries() -> None:
    cases = [
        {"grid_h": 7, "grid_w": 7, "ctrl": 2, "shape_size": 3,
         "marker_location": "top_left"},
        {"grid_h": 14, "grid_w": 16, "ctrl": 5, "shape_size": 8,
         "marker_location": "interior"},
        {"grid_h": 7, "grid_w": 16, "ctrl": 3, "shape_size": 8,
         "marker_location": "other_corner"},
        {"grid_h": 14, "grid_w": 7, "ctrl": 4, "shape_size": 3,
         "marker_location": "edge"},
    ]
    for seed, expected in enumerate(cases, 901):
        grid = GEN.generate(seed, 5, difficulty="easy", **expected)
        assert GEN.observe_overrides(grid) == expected
        assert GEN.self_check(grid, meta=expected) == []
    try:
        GEN.generate(1, 1, difficulty="easy", misspelled_axis=1)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override key was accepted")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    before_state = random.getstate()
    first = GEN.generate(711, 13, difficulty="hard")
    after_state = random.getstate()
    second = GEN.generate(711, 13, difficulty="hard")
    assert before_state == after_state == random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    pristine = copy.deepcopy(second)
    first[0][0] = 9
    assert GEN.generate(711, 13, difficulty="hard") == pristine


def test_targeted_mutation_fixtures_are_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), f"fixture {name!r} was accepted"
