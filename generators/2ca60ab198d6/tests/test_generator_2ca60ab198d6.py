"""Source-bound regressions for the left-guide row crop generator."""
from __future__ import annotations

import copy
import importlib.util
import random
from itertools import product
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "2ca60ab198d6"
TASK_ROOT = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", TASK_ROOT / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_all_canonical_pairs_match_python_mirror() -> None:
    assert GEN.RULE_HASH == "a6ff93ed49cd"
    assert len(PAIRS) == 3
    for pair in PAIRS:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_exact_override_boundaries_are_constructive_and_observable() -> None:
    expected_axes = {
        "grid_h",
        "grid_w",
        "n_keep",
        "selector_style",
        "payload_density",
        "n_payload_colors",
    }
    assert set(GEN.AXES) == expected_axes
    index = 0
    for difficulty, values in product(
        BANDS,
        product(
            (6, 10),
            (7, 11),
            (2, 4),
            ("zero_only", "nonzero_only", "mixed"),
            ("sparse", "medium", "dense"),
            (2, 8),
        ),
    ):
        grid_h, grid_w, n_keep, selector_style, payload_density, n_payload_colors = values
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_keep": n_keep,
            "selector_style": selector_style,
            "payload_density": payload_density,
            "n_payload_colors": n_payload_colors,
        }
        grid = GEN.generate(
            71000 + index,
            2000 + index,
            difficulty=difficulty,
            **requested,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested
        index += 1


def test_unknown_invalid_overrides_and_difficulty_fail_closed() -> None:
    with pytest.raises((TypeError, ValueError), match="unknown"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")
    for bad in (
        {"grid_h": 5},
        {"grid_w": 12},
        {"n_keep": 1},
        {"n_payload_colors": 9},
        {"selector_style": "alternating"},
        {"payload_density": "random"},
        {"grid_h": True},
        {"n_keep": 2.0},
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 0, **bad)


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    random.seed(20261004)
    state_before = random.getstate()
    first = GEN.generate(91, 7, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(91, 7, difficulty="medium")
    assert state_before == state_after
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != GEN.generate(92, 7, difficulty="medium")
    assert second != GEN.generate(91, 8, difficulty="medium")


def test_every_four_consecutive_defaults_cover_the_teaching_schedule() -> None:
    assert GEN.EXAMPLES_NEEDED == len(GEN.SCHEDULE_PROFILES) == 4
    expected = set(GEN.SCHEDULE_PROFILES)
    for difficulty in BANDS:
        for seed in range(4):
            for start in range(8):
                profiles = {
                    GEN.schedule_profile(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                }
                assert profiles == expected

                demos = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(seed, start + GEN.EXAMPLES_NEEDED, difficulty)
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert not all(
                        rival(pair["input"]) == pair["output"] for pair in demos
                    ), name


def test_canonical_shortcuts_fit_canonical_and_schedule_refutes_them() -> None:
    assert set(GEN.CANONICAL_SHORTCUTS) == {
        "nonzero_selector",
        "alternate_from_first_keep",
        "first_three_selected",
    }
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name

    for difficulty in BANDS:
        demos = [_pair(33, offset, difficulty) for offset in range(GEN.EXAMPLES_NEEDED)]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_all_semantic_witnesses_fire_and_refute_claimed_rivals() -> None:
    fired: set[str] = set()
    for difficulty in BANDS:
        for sample_index in range(12):
            grid = GEN.generate(17, sample_index, difficulty=difficulty)
            expected = GEN.rule_mirror(grid)
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    fired.add(name)
                    rivals = GEN.WITNESS_RIVALS[name]
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival](grid) != expected for rival in rivals
                    ), name
    assert fired == set(GEN.SEMANTIC_WITNESSES)


def test_each_band_has_canonical_profile_support_in_every_schedule_window() -> None:
    canonical_profiles = {_profile(pair["input"]) for pair in PAIRS}
    for difficulty in BANDS:
        for seed in range(5):
            for start in range(4):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                assert any(_profile(grid) in canonical_profiles for grid in grids)


def test_self_check_rejects_structural_impostors() -> None:
    assert GEN.self_check([])
    assert GEN.self_check([[]])
    assert GEN.self_check([[0], [0, 0]])
    assert GEN.self_check([[0] * 7 for _ in range(6)])

    grid = GEN.generate(5, 1)
    only_one_keeper = copy.deepcopy(grid)
    seen = 0
    for row in only_one_keeper:
        if row[0] == 7:
            seen += 1
            if seen > 1:
                row[0] = 0
    assert GEN.self_check(only_one_keeper)

    empty_payload_row = copy.deepcopy(grid)
    empty_payload_row[0][1:] = [0] * (len(grid[0]) - 1)
    assert GEN.self_check(empty_payload_row)


def test_every_five_example_window_survives_all_query_rotations() -> None:
    """No single held-out pair may be the only fixed-three counterexample."""
    for difficulty in BANDS:
        for seed in range(4):
            for start in range(8):
                pairs = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(GEN.EXAMPLES_NEEDED + 1)
                ]
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        difficulty,
                        seed,
                        start,
                        query_index,
                    )
