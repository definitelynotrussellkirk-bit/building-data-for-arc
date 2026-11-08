from __future__ import annotations

import copy
import importlib
import random

import pytest

from puzzle_generators import base as gen_base
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "8b2e01e4176b"
BANDS = ("easy", "medium", "hard")


def _load():
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def _pair(module, seed: int, sample_index: int, band: str) -> dict:
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": module.rule_mirror(grid)}


def test_rule_hash_all_canonical_pairs_and_selected_rule_mirror() -> None:
    module = _load()
    assert module.RULE_HASH == canonical_rule_hash(TASK_ID) == "1e68480e5183"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert module.self_check(pair["input"]) == []
        assert module.strict_canonical_like(pair["input"]) == []
        assert module.rule_mirror(pair["input"]) == pair["output"]


def test_declared_override_boundaries_are_exact_and_unknowns_reject() -> None:
    module = _load()
    cases = (
        {
            "grid_h": 7,
            "grid_w": 8,
            "n_seeds": 2,
            "edge_mode": "interior",
            "color_pattern": "distinct",
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "n_seeds": 6,
            "edge_mode": "clipped",
            "color_pattern": "reused",
        },
    )
    for band in BANDS:
        for index, requested in enumerate(cases):
            grid = module.generate(
                9100 + index, index, difficulty=band, **requested
            )
            assert module.self_check(grid) == []
            assert module.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        module.generate(0, 0, unknown_axis=1)
    with pytest.raises(ValueError):
        module.generate(0, 0, grid_h=6)
    with pytest.raises(ValueError):
        module.generate(0, 0, color_pattern="monochrome_only")


def test_default_keyed_draws_round_trip_through_observer() -> None:
    module = _load()
    captured = []
    gen_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(BANDS):
            for sample_index in range(12):
                grid = module.generate(
                    9200 + band_index, sample_index, difficulty=band
                )
                ctx = captured[-1]
                observed = module.observe_overrides(grid)
                recorded = ctx.recorded_draws()
                assert {axis: recorded[axis] for axis in module.AXES} == observed
    finally:
        gen_base.set_ctx_observer(None)


def test_self_check_rejects_targeted_impostors_and_accepts_reuse() -> None:
    module = _load()
    blank = [[0] * 8 for _ in range(7)]
    singleton = copy.deepcopy(blank)
    singleton[3][3] = 4
    adjacent_blob = copy.deepcopy(blank)
    adjacent_blob[3][3] = 4
    adjacent_blob[3][4] = 4
    invalid_color = copy.deepcopy(blank)
    invalid_color[2][2] = 10
    invalid_color[5][5] = 3
    ragged = [[0] * 8 for _ in range(6)] + [[0] * 7]

    for name, grid in {
        "blank": blank,
        "singleton": singleton,
        "adjacent_blob": adjacent_blob,
        "invalid_color": invalid_color,
        "ragged": ragged,
    }.items():
        assert module.self_check(grid), name

    reused = module.generate(
        9300,
        1,
        difficulty="medium",
        n_seeds=5,
        edge_mode="clipped",
        color_pattern="reused",
    )
    assert module.self_check(reused) == []
    assert module.observe_overrides(reused)["color_pattern"] == "reused"

    # Negative recombination: add a new-color adjacent cell.  The replacement
    # color is absent from every remaining scene part; the oracle mirror still
    # executes, but the teaching grammar rejects the multi-cell blob.
    canonical = copy.deepcopy(canonical_pairs(TASK_ID)[0]["input"])
    palette = {value for row in canonical for value in row}
    new_color = next(color for color in range(1, 10) if color not in palette)
    seed_row, seed_col = next(
        (row, col)
        for row, values in enumerate(canonical)
        for col, value in enumerate(values)
        if value != 0
    )
    neighbor = next(
        (seed_row + dr, seed_col + dc)
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
        if 0 <= seed_row + dr < len(canonical)
        and 0 <= seed_col + dc < len(canonical[0])
        and canonical[seed_row + dr][seed_col + dc] == 0
    )
    canonical[neighbor[0]][neighbor[1]] = new_color
    assert new_color not in palette
    assert module.self_check(canonical)
    assert module.rule_mirror(canonical)


def test_schedule_makes_every_three_demo_window_identifiable() -> None:
    module = _load()
    assert module.EXAMPLES_NEEDED == 3
    assert set(module.SCHEDULE_PROFILES) == {"anchor", "both_controls"}
    for band_index, band in enumerate(BANDS):
        for start in range(8):
            lesson = [
                _pair(module, 9400 + band_index * 100 + start, start + offset, band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            assert module.lesson_identifiable(lesson[:3], lesson[3]) == []
            profiles = {
                module.schedule_profile(
                    9400 + band_index * 100 + start,
                    start + offset,
                    difficulty=band,
                )
                for offset in range(3)
            }
            assert profiles == {"anchor", "both_controls"}


def test_named_witnesses_kill_their_named_rivals_and_shortcut() -> None:
    module = _load()
    candidates = [
        module.generate(9500, 0, difficulty="medium"),
        module.generate(9500, 1, difficulty="medium"),
    ]
    for witness_name, rival_names in module.WITNESS_RIVALS.items():
        firing = next(
            grid
            for grid in candidates
            if module.SEMANTIC_WITNESSES[witness_name](grid)
        )
        expected = module.rule_mirror(firing)
        for rival_name in rival_names:
            assert module.SEMANTIC_RIVALS[rival_name](firing) != expected

    shortcut = module.CANONICAL_SHORTCUTS["one_diamond_per_color"]
    for pair in canonical_pairs(TASK_ID):
        assert shortcut(pair["input"]) == pair["output"]
    reuse_grid = candidates[1]
    assert shortcut(reuse_grid) != module.rule_mirror(reuse_grid)


def test_strict_linked_census_and_disjoint_seed_stability() -> None:
    module = _load()
    for band_index, band in enumerate(BANDS):
        for seed_base in (9600, 19600):
            profile_counts = {"anchor": 0, "both_controls": 0}
            witness_counts = {name: 0 for name in module.SEMANTIC_WITNESSES}
            strict = 0
            rendered = set()
            outputs = set()
            for sample_index in range(200):
                grid = module.generate(
                    seed_base + band_index, sample_index, difficulty=band
                )
                assert module.self_check(grid) == []
                profile_counts[
                    module.schedule_profile(
                        seed_base + band_index,
                        sample_index,
                        difficulty=band,
                    )
                ] += 1
                strict += not bool(module.strict_canonical_like(grid))
                for name, predicate in module.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(predicate(grid))
                rendered.add(repr(grid))
                outputs.add(repr(module.rule_mirror(grid)))
            assert profile_counts == {"anchor": 100, "both_controls": 100}
            assert strict >= 90
            assert all(count >= 100 for count in witness_counts.values())
            assert len(rendered) >= 190
            assert len(outputs) >= 190


def test_replay_is_fresh_deterministic_and_global_rng_neutral() -> None:
    module = _load()
    random.seed(20260816)
    state = random.getstate()
    first = module.generate(9700, 7, difficulty="hard")
    assert random.getstate() == state
    second = module.generate(9700, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_invalid_difficulty_is_rejected_instead_of_silently_using_medium() -> None:
    module = _load()
    with pytest.raises(ValueError, match="difficulty"):
        module.generate(9800, 0, difficulty="impossible")
